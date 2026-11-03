"""Storyboard AI Studio Pro - Multi-Channel YouTube Management & 1-Click Video Uploader.
Handles Google OAuth 2.0 flow, multi-channel registry, token refresh, resumable video upload,
and automatic 1280x720 thumbnail publishing via YouTube Data API v3.
"""
from __future__ import annotations

import json
import logging
import math
import os
import re
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
import urllib.parse
import sys
import requests

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

logger = logging.getLogger("studio.youtube_manager")

STUDIO_DIR = Path(__file__).resolve().parent
CHANNELS_FILE = STUDIO_DIR / "youtube_channels.json"

# Default OAuth Client ID / Secret template
DEFAULT_OAUTH_CONFIG = {
    "client_id": "",
    "client_secret": "",
    "active_channel_id": "",
    "channels": []
}

# In-memory upload job tracker
_upload_lock = threading.Lock()
_upload_state: Dict[str, Any] = {
    "status": "idle",  # idle, uploading, setting_thumbnail, done, error
    "percent": 0,
    "bytes_sent": 0,
    "total_bytes": 0,
    "message": "",
    "video_id": "",
    "video_url": "",
    "studio_url": "",
    "error": None,
    "start_time": 0,
    "completed_at": 0
}


def load_youtube_config() -> Dict[str, Any]:
    """Load the YouTube configuration file safely."""
    if not CHANNELS_FILE.exists():
        return dict(DEFAULT_OAUTH_CONFIG)
    try:
        data = json.loads(CHANNELS_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return dict(DEFAULT_OAUTH_CONFIG)
        if "channels" not in data or not isinstance(data["channels"], list):
            data["channels"] = []
        return data
    except Exception as exc:
        logger.error(f"Failed to read {CHANNELS_FILE}: {exc}")
        return dict(DEFAULT_OAUTH_CONFIG)


def save_youtube_config(config: Dict[str, Any]) -> bool:
    """Save the YouTube configuration file atomically."""
    try:
        tmp_file = CHANNELS_FILE.with_suffix(".tmp")
        tmp_file.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp_file.replace(CHANNELS_FILE)
        return True
    except Exception as exc:
        logger.error(f"Failed to write {CHANNELS_FILE}: {exc}")
        return False


def set_oauth_credentials(client_id: str = "", client_secret: str = "", raw_json: Optional[str] = None) -> Dict[str, Any]:
    """Save or update Google OAuth Client ID and Secret, supporting raw JSON files directly."""
    if raw_json:
        try:
            data = json.loads(raw_json)
            creds = data.get("installed") or data.get("web") or data
            client_id = creds.get("client_id", client_id)
            client_secret = creds.get("client_secret", client_secret)
        except Exception as exc:
            return {"ok": False, "error": f"Tệp JSON không hợp lệ: {exc}"}

    client_id = (client_id or "").strip()
    client_secret = (client_secret or "").strip()

    if not client_id or not client_secret:
        return {"ok": False, "error": "Thiếu Client ID hoặc Client Secret hợp lệ."}

    config = load_youtube_config()
    config["client_id"] = client_id
    config["client_secret"] = client_secret
    save_youtube_config(config)
    return {
        "ok": True,
        "client_id_configured": bool(config["client_id"]),
        "has_client_secret": bool(config["client_secret"])
    }


def get_channels_summary() -> Dict[str, Any]:
    """Return channel list with sensitive tokens masked for frontend display."""
    config = load_youtube_config()
    active_id = config.get("active_channel_id", "")
    channels = []
    
    for ch in config.get("channels", []):
        is_active = (ch.get("id") == active_id) or (len(channels) == 0 and not active_id)
        saved_settings = ch.get("publish_settings") or {}
        channels.append({
            "id": ch.get("id", ""),
            "name": ch.get("name", "Kênh YouTube"),
            "custom_url": ch.get("custom_url", ""),
            "avatar_url": ch.get("avatar_url", ""),
            "subscriber_count": ch.get("subscriber_count", "0"),
            "default_privacy": ch.get("default_privacy", "private"),
            "publish_settings": {
                "category_id": saved_settings.get("category_id", "1"),
                "contains_synthetic_media": saved_settings.get("contains_synthetic_media", True),
                "made_for_kids": saved_settings.get("made_for_kids", False),
                "license": saved_settings.get("license", "youtube"),
                "embeddable": saved_settings.get("embeddable", True),
                "public_stats_viewable": saved_settings.get("public_stats_viewable", True),
                "default_privacy": saved_settings.get("default_privacy", ch.get("default_privacy", "unlisted")),
                "default_language": saved_settings.get("default_language", ""),
                "default_audio_language": saved_settings.get("default_audio_language", ""),
                "default_playlist_id": saved_settings.get("default_playlist_id", "auto"),
                "shorts_remix": saved_settings.get("shorts_remix", "none")
            },
            "is_active": is_active,
            "connected_at": ch.get("added_at", ""),
            "has_token": bool(ch.get("refresh_token") or ch.get("access_token")),
            "token_expired": bool(ch.get("token_expired", False))
        })

    # Auto select first channel as active if none set
    if channels and not any(c["is_active"] for c in channels):
        channels[0]["is_active"] = True
        config["active_channel_id"] = channels[0]["id"]
        save_youtube_config(config)

    return {
        "ok": True,
        "client_id_configured": bool(config.get("client_id")),
        "active_channel_id": config.get("active_channel_id", ""),
        "series_channel_mapping": config.get("series_channel_mapping", {}),
        "channels": channels,
        "count": len(channels)
    }


def set_active_channel(channel_id: str) -> Dict[str, Any]:
    """Set the active default channel for 1-click publishing."""
    config = load_youtube_config()
    found = False
    for ch in config.get("channels", []):
        if ch.get("id") == channel_id:
            found = True
            break
    if not found and channel_id:
        return {"ok": False, "error": f"Không tìm thấy kênh với ID: {channel_id}"}

    config["active_channel_id"] = channel_id
    save_youtube_config(config)
    return {"ok": True, "active_channel_id": channel_id}


def delete_channel(channel_id: str) -> Dict[str, Any]:
    """Remove a channel from the registry."""
    config = load_youtube_config()
    before_count = len(config.get("channels", []))
    config["channels"] = [ch for ch in config.get("channels", []) if ch.get("id") != channel_id]
    
    if config.get("active_channel_id") == channel_id:
        config["active_channel_id"] = config["channels"][0]["id"] if config["channels"] else ""

    save_youtube_config(config)
    return {
        "ok": True,
        "deleted": before_count > len(config["channels"]),
        "active_channel_id": config.get("active_channel_id", "")
    }


def update_channel_privacy(channel_id: str, default_privacy: str) -> Dict[str, Any]:
    """Update default privacy (private/unlisted/public) for a channel."""
    if default_privacy not in ("private", "unlisted", "public"):
        default_privacy = "private"
    config = load_youtube_config()
    for ch in config.get("channels", []):
        if ch.get("id") == channel_id:
            ch["default_privacy"] = default_privacy
            ch.setdefault("publish_settings", {})["default_privacy"] = default_privacy
            save_youtube_config(config)
            return {"ok": True, "id": channel_id, "default_privacy": default_privacy}
    return {"ok": False, "error": "Kênh không tồn tại"}


def get_channel_publish_settings(channel_id: str) -> Dict[str, Any]:
    """Get the saved publish settings for a given channel with production defaults."""
    config = load_youtube_config()
    for ch in config.get("channels", []):
        if ch.get("id") == channel_id:
            saved = ch.get("publish_settings") or {}
            return {
                "category_id": saved.get("category_id", "1"),
                "contains_synthetic_media": saved.get("contains_synthetic_media", True),
                "made_for_kids": saved.get("made_for_kids", False),
                "license": saved.get("license", "youtube"),
                "embeddable": saved.get("embeddable", True),
                "public_stats_viewable": saved.get("public_stats_viewable", True),
                "default_privacy": saved.get("default_privacy", ch.get("default_privacy", "unlisted")),
                "default_language": saved.get("default_language", ""),
                "default_audio_language": saved.get("default_audio_language", ""),
                "default_playlist_id": saved.get("default_playlist_id", "auto")
            }
    return {
        "category_id": "1",
        "contains_synthetic_media": True,
        "made_for_kids": False,
        "license": "youtube",
        "embeddable": True,
        "public_stats_viewable": True,
        "default_privacy": "unlisted",
        "default_language": "",
        "default_audio_language": "",
        "default_playlist_id": "auto"
    }


def update_channel_publish_settings(channel_id: str, settings: Dict[str, Any]) -> Dict[str, Any]:
    """Persist publish settings for a given channel permanently in youtube_channels.json."""
    config = load_youtube_config()
    for ch in config.get("channels", []):
        if ch.get("id") == channel_id:
            current = ch.setdefault("publish_settings", {})
            for k in (
                "category_id", "contains_synthetic_media", "made_for_kids",
                "license", "embeddable", "public_stats_viewable",
                "default_language", "default_audio_language", "default_privacy",
                "default_playlist_id"
            ):
                if k in settings:
                    current[k] = settings[k]
            if "default_privacy" in settings:
                ch["default_privacy"] = settings["default_privacy"]
            save_youtube_config(config)
            return {"ok": True, "channel_id": channel_id, "publish_settings": current}
    return {"ok": False, "error": f"Không tìm thấy kênh: {channel_id}"}


def set_series_channel_mapping(series_name: str, channel_id: str) -> Dict[str, Any]:
    """Remember that a series belongs to a specific channel so it auto-selects next time."""
    s = str(series_name or "").strip()
    if not s or not channel_id or s.lower() in ("auto", "vẽ tranh", "whiteboard chronicles", "tập phim mới"):
        # Do not save generic workspace defaults as global series mappings
        return {"ok": False, "error": "Bỏ qua lưu ánh xạ cho series mặc định"}
    config = load_youtube_config()
    mapping = config.setdefault("series_channel_mapping", {})
    mapping[s] = str(channel_id).strip()
    save_youtube_config(config)
    return {"ok": True, "series": s, "channel_id": channel_id}


def format_rfc3339(ts_str: Optional[str]) -> str:
    """Convert an ISO string or datetime-local to valid RFC 3339 for YouTube Data API v3."""
    if not ts_str or not str(ts_str).strip():
        return ""
    s = str(ts_str).strip()
    try:
        from datetime import datetime
        if s.endswith("Z") or (len(s) >= 19 and s[-6] in ("+", "-") and s[-3] == ":"):
            return s
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            local_tz = datetime.now().astimezone().tzinfo
            dt = dt.replace(tzinfo=local_tz)
        return dt.isoformat()
    except Exception as exc:
        logger.warning(f"Không thể chuẩn hóa RFC 3339 cho publish_at '{ts_str}': {exc}")
        return s


def to_youtube_bcp47(lang: Optional[str]) -> str:
    """Convert any human or legacy language tag to a strict YouTube Data API v3 BCP-47 language code."""
    if not lang:
        return ""
    l = str(lang).strip().lower()

    # English variants (US prioritized as requested)
    if l in ("en-gb", "uk", "british", "british english", "tiếng anh (vương quốc anh)", "tiếng anh (anh)"):
        return "en-GB"
    if l in ("en-ca", "canadian english", "tiếng anh (canada)"):
        return "en-CA"
    if l in ("en-au", "australian english", "tiếng anh (úc)"):
        return "en-AU"
    if l in ("en-in", "indian english", "tiếng anh (ấn độ)"):
        return "en-IN"
    if l in ("en-us", "us", "american", "american english", "tiếng anh (hoa kỳ)", "hoa kỳ", "en", "eng", "english", "tiếng anh", "anh"):
        return "en-US"

    # Spanish variants
    if l in ("es-419", "spanish (latin america)", "mỹ latinh", "latin america"):
        return "es-419"
    if l in ("es", "es-es", "spa", "spanish", "tiếng tây ban nha", "tây ban nha", "español", "espanol"):
        return "es"

    # Portuguese
    if l in ("pt-br", "brazilian", "brazilian portuguese", "tiếng bồ đào nha (brazil)", "brazil", "bồ đào nha"):
        return "pt-BR"
    if l in ("pt-pt", "portuguese (portugal)"):
        return "pt-PT"
    if l in ("pt", "por", "portuguese"):
        return "pt-BR"

    # Chinese
    if l in ("zh-cn", "zh-hans", "chinese (simplified)", "tiếng trung (giản thể)", "giản thể"):
        return "zh-CN"
    if l in ("zh-tw", "zh-hant", "chinese (traditional)", "tiếng trung (phồn thể)", "phồn thể"):
        return "zh-TW"
    if l in ("zh", "chinese", "tiếng trung", "trung"):
        return "zh-CN"

    # Other common YouTube Studio languages
    mapping = {
        "ru": "ru", "rus": "ru", "russian": "ru", "tiếng nga": "ru", "nga": "ru",
        "vi": "vi", "vie": "vi", "vietnamese": "vi", "tiếng việt": "vi", "việt": "vi",
        "ja": "ja", "jpn": "ja", "japanese": "ja", "tiếng nhật": "ja", "nhật": "ja",
        "ko": "ko", "kor": "ko", "korean": "ko", "tiếng hàn": "ko", "hàn": "ko",
        "de": "de", "deu": "de", "german": "de", "tiếng đức": "de", "đức": "de",
        "fr": "fr", "fra": "fr", "french": "fr", "tiếng pháp": "fr", "pháp": "fr",
        "it": "it", "ita": "it", "italian": "it", "tiếng ý": "it", "ý": "it",
        "hi": "hi", "hin": "hi", "hindi": "hi", "tiếng hindi": "hi", "ấn độ": "hi",
        "id": "id", "ind": "id", "indonesian": "id", "tiếng indonesia": "id",
        "th": "th", "tha": "th", "thai": "th", "tiếng thái": "th", "thái": "th",
        "fil": "fil", "filipino": "fil", "tagalog": "fil", "tiếng filipino": "fil",
        "ms": "ms", "may": "ms", "malay": "ms", "malaysia": "ms", "tiếng malaysia": "ms",
        "ar": "ar", "ara": "ar", "arabic": "ar", "tiếng ả rập": "ar", "ả rập": "ar",
        "tr": "tr", "tur": "tr", "turkish": "tr", "tiếng thổ nhĩ kỳ": "tr", "thổ nhĩ kỳ": "tr",
        "pl": "pl", "pol": "pl", "polish": "pl", "tiếng ba lan": "pl", "ba lan": "pl",
        "nl": "nl", "nld": "nl", "dutch": "nl", "tiếng hà lan": "nl", "hà lan": "nl",
        "uk": "uk", "ukr": "uk", "ukrainian": "uk", "tiếng ukraina": "uk", "ukraina": "uk",
    }
    for k, v in mapping.items():
        if l == k or l.startswith(k + "-") or k in l:
            return v

    if "-" in str(lang):
        parts = str(lang).split("-")
        return f"{parts[0].lower()}-{parts[1].upper()}"
    return str(lang).strip()


def normalize_language_code(lang: str) -> str:
    """Normalize any language string (Russian, Tiếng Nga, ru, English, en-US, en, Spanish, es, Vietnamese, vi) to ISO 639-1 code."""
    if not lang:
        return ""
    l = str(lang).strip().lower()
    if "tiếng anh" in l or "english" in l or "hoa kỳ" in l or "american" in l or "british" in l or l.startswith("en"):
        return "en"
    if "tây ban nha" in l or "spanish" in l or "español" in l or "latin" in l or l.startswith("es"):
        return "es"
    if "nga" in l or "russian" in l or l.startswith("ru"):
        return "ru"
    if "việt" in l or "vietnamese" in l or l.startswith("vi"):
        return "vi"
    if "bồ đào nha" in l or "portuguese" in l or l.startswith("pt"):
        return "pt"
    if "trung" in l or "chinese" in l or l.startswith("zh"):
        return "zh"
    if "nhật" in l or "japanese" in l or l.startswith("ja"):
        return "ja"
    if "hàn" in l or "korean" in l or l.startswith("ko"):
        return "ko"
    if "pháp" in l or "french" in l or l.startswith("fr"):
        return "fr"
    if "đức" in l or "german" in l or l.startswith("de"):
        return "de"
    return l[:2] if len(l) >= 2 else l


def get_series_channel(series_name: str, episode_language: str = "") -> str:
    """
    Strict Channel Auto-Detection matching channel pre-configured settings:
    1. Video/SEO Language is FIRST PRIORITY:
       - Match channels whose publish_settings.default_language or default_language matches episode_language.
       - If exactly 1 channel matches the language, pick it immediately.
       - If multiple channels match the language (e.g. English), use series keywords / themes to pick the exact channel:
         * "stoic" / "philosophy" -> "Stoic Sovereign"
         * "frontier" / "wild" / "western" -> "Wild Frontier Chronicles"
         * "history" / "veiled" -> "Veiled History"
         * "hoa" / "drama" / "fallout" -> "The HOA Fallout"
    2. Check explicit series_channel_mapping ONLY if the mapped channel's language DOES NOT conflict with the video's language!
    3. Keyword / Substring heuristics on series name if no language provided.
    4. Fall back to active_channel_id or first channel.
    """
    config = load_youtube_config()
    channels = config.get("channels", [])
    if not channels:
        return ""

    s_clean = str(series_name or "").strip().lower()
    norm_lang = normalize_language_code(episode_language)

    # If episode_language wasn't explicitly given, check if series_name has language hints
    if not norm_lang:
        if "nga" in s_clean or "russian" in s_clean or "правд" in s_clean:
            norm_lang = "ru"
        elif "tây ban nha" in s_clean or "spanish" in s_clean or "estoic" in s_clean:
            norm_lang = "es"
        elif "việt" in s_clean or "vietnamese" in s_clean:
            norm_lang = "vi"

    # Helper to get normalized configured language for a channel
    def channel_lang(ch: Dict[str, Any]) -> str:
        ps = ch.get("publish_settings", {})
        return normalize_language_code(ps.get("default_language") or ps.get("default_audio_language") or "")

    mapping = config.get("series_channel_mapping", {})

    # Step 1: If language is known, filter matching channels
    if norm_lang:
        lang_matches = [ch for ch in channels if channel_lang(ch) == norm_lang]
        if len(lang_matches) == 1:
            return lang_matches[0].get("id", "")
        elif len(lang_matches) > 1:
            # Check explicit mapping FIRST among matching language channels!
            if series_name and series_name in mapping:
                mapped_id = mapping[series_name]
                if any(c.get("id") == mapped_id for c in lang_matches):
                    return mapped_id

            # Disambiguate among channels with the same language using series/keyword matching
            for ch in lang_matches:
                c_name = ch.get("name", "").lower()
                # HOA / Drama / Revenge
                if ("hoa" in s_clean or "fallout" in s_clean) and ("hoa" in c_name or "fallout" in c_name):
                    return ch.get("id", "")
                # Stoic / Philosophy (Exclude Spanish Notas Estoicas)
                if ("stoic" in s_clean or "triết" in s_clean or "sovereign" in s_clean) and ("sovereign" in c_name or ("stoic" in c_name and "notas" not in c_name)):
                    return ch.get("id", "")
                # Frontier / Western
                if ("frontier" in s_clean or "wild" in s_clean or "viễn tây" in s_clean) and ("frontier" in c_name or "wild" in c_name):
                    return ch.get("id", "")
                # History / Veiled
                if ("history" in s_clean or "lịch sử" in s_clean or "veiled" in s_clean) and ("history" in c_name or "veiled" in c_name):
                    return ch.get("id", "")
                # Direct substring match
                if s_clean and (s_clean in c_name or c_name in s_clean):
                    return ch.get("id", "")

            # If no keyword matched, return the active one if it's in lang_matches, else the first
            active_id = config.get("active_channel_id", "")
            for ch in lang_matches:
                if ch.get("id") == active_id:
                    return active_id
            return lang_matches[0].get("id", "")

    # Step 2: Check explicit series mapping, BUT verify it doesn't violate language if known
    if series_name and series_name in mapping:
        mapped_id = mapping[series_name]
        mapped_ch = next((c for c in channels if c.get("id") == mapped_id), None)
        if mapped_ch:
            if not norm_lang or channel_lang(mapped_ch) == norm_lang:
                return mapped_id

    # Step 3: Heuristics based on series name
    if "hoa" in s_clean or "fallout" in s_clean:
        for ch in channels:
            if "hoa" in ch.get("name", "").lower():
                return ch.get("id", "")

    if "estoic" in s_clean or "notas" in s_clean or s_clean == "stoi":
        for ch in channels:
            if "notas" in ch.get("name", "").lower() or "estoic" in ch.get("name", "").lower():
                return ch.get("id", "")

    if "sovereign" in s_clean or s_clean == "stoic" or ("stoic" in s_clean and "estoic" not in s_clean):
        for ch in channels:
            if "sovereign" in ch.get("name", "").lower() or ("stoic" in ch.get("name", "").lower() and "notas" not in ch.get("name", "").lower()):
                return ch.get("id", "")

    if "frontier" in s_clean or "wild" in s_clean or "viễn tây" in s_clean:
        for ch in channels:
            if "frontier" in ch.get("name", "").lower():
                return ch.get("id", "")

    if "history" in s_clean or "lịch sử" in s_clean or "veiled" in s_clean:
        for ch in channels:
            if "history" in ch.get("name", "").lower() or "veiled" in ch.get("name", "").lower():
                return ch.get("id", "")

    if "правд" in s_clean or "nga" in s_clean:
        for ch in channels:
            if "правд" in ch.get("name", "").lower() or "по ту сторону" in ch.get("name", "").lower():
                return ch.get("id", "")

    # Step 4: Substring name match
    if s_clean:
        for ch in channels:
            c_name = ch.get("name", "").lower()
            if s_clean in c_name or c_name in s_clean:
                return ch.get("id", "")

    # Step 5: Fall back to active channel or first channel
    active_id = config.get("active_channel_id", "")
    if active_id and any(c.get("id") == active_id for c in channels):
        return active_id

    return channels[0].get("id", "")


# ---------------------------------------------------------------------------
# GOOGLE OAUTH 2.0 FLOW & TOKEN MANAGEMENT
# ---------------------------------------------------------------------------

YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]


def build_auth_url(redirect_uri: str, client_id: Optional[str] = None, channel_id: Optional[str] = None) -> str:
    """Generate the Google OAuth consent URL with full YouTube scopes (Video + Playlists)."""
    config = load_youtube_config()
    cid = client_id
    if not cid and channel_id:
        for ch in config.get("channels", []):
            if ch.get("id") == channel_id:
                cid = ch.get("client_id")
                break
    if not cid:
        cid = config.get("client_id", "")
    if not cid:
        raise ValueError("Vui lòng nhập Google OAuth Client ID trước khi kết nối kênh.")

    params = {
        "client_id": cid,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(YOUTUBE_SCOPES),
        "access_type": "offline",
        "prompt": "select_account consent",
        "include_granted_scopes": "true"
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"


def exchange_code_and_add_channel(code: str, redirect_uri: str) -> Dict[str, Any]:
    """Exchange authorization code for tokens and fetch channel profile to store."""
    config = load_youtube_config()
    client_id = config.get("client_id", "")
    client_secret = config.get("client_secret", "")
    if not client_id or not client_secret:
        raise ValueError("Chưa thiết lập Google OAuth Client ID hoặc Client Secret.")

    token_url = "https://oauth2.googleapis.com/token"
    token_payload = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }
    resp = requests.post(token_url, data=token_payload, timeout=20)
    if resp.status_code != 200:
        error_msg = resp.text
        try:
            error_data = resp.json()
            error_msg = error_data.get("error_description", error_data.get("error", resp.text))
        except Exception:
            pass
        raise RuntimeError(f"Lỗi trao đổi mã OAuth với Google: {error_msg}")

    token_data = resp.json()
    access_token = token_data.get("access_token", "")
    refresh_token = token_data.get("refresh_token", "")
    expires_in = token_data.get("expires_in", 3600)
    token_expiry = int(time.time() + expires_in)

    # Fetch channel profile
    profile = fetch_channel_profile(access_token)
    channel_id = profile["id"]

    # Check if channel exists in registry
    channel_entry = None
    for ch in config.get("channels", []):
        if ch.get("id") == channel_id:
            channel_entry = ch
            break

    if not channel_entry:
        channel_entry = {
            "id": channel_id,
            "name": profile.get("name", "Kênh YouTube"),
            "custom_url": profile.get("custom_url", ""),
            "avatar_url": profile.get("avatar_url", ""),
            "subscriber_count": profile.get("subscriber_count", "0"),
            "default_privacy": "private",
            "added_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        config["channels"].append(channel_entry)
    else:
        channel_entry["name"] = profile.get("name", channel_entry.get("name"))
        channel_entry["custom_url"] = profile.get("custom_url", channel_entry.get("custom_url"))
        channel_entry["avatar_url"] = profile.get("avatar_url", channel_entry.get("avatar_url"))
        channel_entry["subscriber_count"] = profile.get("subscriber_count", channel_entry.get("subscriber_count"))

    channel_entry["access_token"] = access_token
    if refresh_token:
        channel_entry["refresh_token"] = refresh_token
    channel_entry["token_expiry"] = token_expiry
    if client_id:
        channel_entry["client_id"] = client_id
    if client_secret:
        channel_entry["client_secret"] = client_secret

    config["active_channel_id"] = channel_id

    save_youtube_config(config)
    return {
        "ok": True,
        "channel_id": channel_id,
        "name": channel_entry["name"],
        "custom_url": channel_entry["custom_url"],
        "avatar_url": channel_entry["avatar_url"],
        "subscriber_count": channel_entry["subscriber_count"]
    }


def fetch_channel_profile(access_token: str) -> Dict[str, Any]:
    """Query YouTube Data API v3 for the authenticated channel's profile & statistics."""
    url = "https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics&mine=true"
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(url, headers=headers, timeout=15)
    if resp.status_code != 200:
        raise RuntimeError(f"Không thể lấy thông tin kênh YouTube: HTTP {resp.status_code} {resp.text}")

    data = resp.json()
    items = data.get("items", [])
    if not items:
        raise RuntimeError("Không tìm thấy thông tin kênh YouTube cho tài khoản này.")

    item = items[0]
    ch_id = item.get("id", "")
    snippet = item.get("snippet", {})
    stats = item.get("statistics", {})

    # Avatar selection
    thumbs = snippet.get("thumbnails", {})
    avatar_url = (thumbs.get("medium") or thumbs.get("default") or {}).get("url", "")

    return {
        "id": ch_id,
        "name": snippet.get("title", "Kênh YouTube"),
        "custom_url": snippet.get("customUrl", ""),
        "avatar_url": avatar_url,
        "subscriber_count": stats.get("subscriberCount", "0")
    }


def get_fresh_access_token(channel_id: str) -> str:
    """Ensure access token is valid, refreshing it if expired."""
    config = load_youtube_config()
    target_ch = None
    for ch in config.get("channels", []):
        if ch.get("id") == channel_id:
            target_ch = ch
            break
    if not target_ch:
        raise ValueError(f"Không tìm thấy cấu hình cho kênh ID: {channel_id}")

    access_token = target_ch.get("access_token", "")
    token_expiry = target_ch.get("token_expiry", 0)
    refresh_token = target_ch.get("refresh_token", "")

    # Token is valid if expiration is at least 300 seconds away
    if access_token and (token_expiry - time.time() > 300):
        return access_token

    if not refresh_token:
        raise RuntimeError(f"Kênh '{target_ch.get('name')}' chưa có refresh token. Vui lòng cấp quyền lại.")

    client_id = target_ch.get("client_id") or config.get("client_id", "")
    client_secret = target_ch.get("client_secret") or config.get("client_secret", "")

    token_url = "https://oauth2.googleapis.com/token"
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }

    resp = None
    if client_id and client_secret:
        resp = requests.post(token_url, data=payload, timeout=20)

    if resp is None or resp.status_code != 200:
        # Auto-heal: Scan kênh/*.json to find matching credentials for this refresh_token
        import glob
        kenh_dir = Path(__file__).resolve().parent.parent / "kênh"
        for kf in glob.glob(str(kenh_dir / "*.json")):
            try:
                kd = json.loads(Path(kf).read_text(encoding="utf-8"))
                pi = kd.get("installed") or kd.get("web") or kd
                cid, cs = pi.get("client_id"), pi.get("client_secret")
                if cid and cs and cid != client_id:
                    r = requests.post(token_url, data={
                        "client_id": cid, "client_secret": cs,
                        "refresh_token": refresh_token, "grant_type": "refresh_token"
                    }, timeout=10)
                    if r.status_code == 200:
                        resp = r
                        client_id, client_secret = cid, cs
                        target_ch["client_id"] = cid
                        target_ch["client_secret"] = cs
                        target_ch["credential_file"] = str(Path(kf).relative_to(kenh_dir.parent))
                        break
            except Exception:
                pass

    if resp is None or resp.status_code != 200:
        err_msg = resp.text if resp is not None else "Không tìm thấy client_id/client_secret phù hợp."
        if "invalid_grant" in err_msg.lower():
            target_ch["token_expired"] = True
            save_youtube_config(config)
            raise RuntimeError(f"Phiên xác thực Google của kênh '{target_ch.get('name')}' đã hết hạn (Google quy định 7 ngày đối với App thử nghiệm). Vui lòng nhấn Kết nối lại để tiếp tục đăng tự động.")
        raise RuntimeError(f"Lỗi làm mới token: HTTP {resp.status_code if resp is not None else 401} {err_msg}")

    data = resp.json()
    new_access_token = data.get("access_token", "")
    expires_in = data.get("expires_in", 3600)

    target_ch["access_token"] = new_access_token
    target_ch["token_expiry"] = int(time.time() + expires_in)
    target_ch["token_expired"] = False
    save_youtube_config(config)

    return new_access_token


# ---------------------------------------------------------------------------
# YOUTUBE PLAYLIST AUTOMATION API
# ---------------------------------------------------------------------------

def fetch_channel_playlists(channel_id: str) -> List[Dict[str, Any]]:
    """Fetch all playlists for the given channel using its access token."""
    try:
        access_token = get_fresh_access_token(channel_id)
        url = "https://www.googleapis.com/youtube/v3/playlists?part=snippet,contentDetails&mine=true&maxResults=50"
        headers = {"Authorization": f"Bearer {access_token}"}
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            logger.warning(f"Lỗi lấy danh sách playlist: HTTP {resp.status_code} {resp.text}")
            return []
        items = resp.json().get("items", [])
        playlists = []
        for it in items:
            snippet = it.get("snippet", {})
            content_details = it.get("contentDetails", {})
            playlists.append({
                "id": it.get("id"),
                "title": snippet.get("title", ""),
                "description": snippet.get("description", ""),
                "item_count": content_details.get("itemCount", 0)
            })
        return playlists
    except Exception as exc:
        logger.error(f"Lỗi truy vấn playlist: {exc}")
        return []


def create_playlist(channel_id: str, title: str, description: str = "", privacy_status: str = "public") -> Dict[str, Any]:
    """Create a new playlist on the channel."""
    try:
        access_token = get_fresh_access_token(channel_id)
        url = "https://www.googleapis.com/youtube/v3/playlists?part=snippet,status"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8"
        }
        body = {
            "snippet": {
                "title": title[:150],
                "description": description[:5000]
            },
            "status": {
                "privacyStatus": privacy_status if privacy_status in ("public", "private", "unlisted") else "public"
            }
        }
        resp = requests.post(url, headers=headers, json=body, timeout=20)
        if resp.status_code in (200, 201):
            data = resp.json()
            return {"ok": True, "id": data.get("id"), "title": title}
        else:
            return {"ok": False, "error": resp.text, "status_code": resp.status_code}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def add_video_to_playlist(channel_id: str, video_id: str, playlist_id: str) -> Dict[str, Any]:
    """Add an uploaded video to a specific playlist on YouTube with auto-retry for processing latency."""
    if not playlist_id or playlist_id in ("none", "auto", ""):
        return {"ok": False, "skipped": True, "error": "Không có playlist hợp lệ."}

    last_err = ""
    for attempt in range(1, 4):
        try:
            access_token = get_fresh_access_token(channel_id)
            url = "https://www.googleapis.com/youtube/v3/playlistItems?part=snippet"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json; charset=UTF-8"
            }
            body = {
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id
                    }
                }
            }
            resp = requests.post(url, headers=headers, json=body, timeout=20)
            if resp.status_code in (200, 201):
                data = resp.json()
                logger.info(f"Đã thêm video {video_id} vào playlist {playlist_id} thành công (lần thử {attempt}).")
                return {"ok": True, "playlist_item_id": data.get("id"), "playlist_id": playlist_id}

            err_msg = resp.text
            try:
                err_json = resp.json()
                err_msg = err_json.get("error", {}).get("message", resp.text)
            except Exception:
                pass

            if "insufficient authentication scopes" in err_msg.lower():
                friendly_msg = "Kênh này được kết nối trước đây với quyền rút gọn (thiếu scope youtube.force-ssl). Vui lòng vào Cài đặt Kênh YouTube và bấm biểu tượng 🔑 'Cấp quyền Google' để kích hoạt tính năng tự động thêm Playlist."
                logger.warning(f"Kênh {channel_id} thiếu quyền playlist: {friendly_msg}")
                return {"ok": False, "error": friendly_msg, "needs_reauth": True, "playlist_id": playlist_id}

            last_err = f"HTTP {resp.status_code}: {err_msg}"
            logger.warning(f"Lần thử {attempt}/3 thêm video {video_id} vào playlist {playlist_id} thất bại: {last_err}")
            if attempt < 3:
                time.sleep(2.0)
        except Exception as exc:
            last_err = str(exc)
            logger.warning(f"Lỗi kết nối thêm playlist (lần thử {attempt}): {last_err}")
            if attempt < 3:
                time.sleep(2.0)

    return {"ok": False, "error": last_err, "playlist_id": playlist_id}


def post_pinned_comment(channel_id: str, video_id: str, comment_text: str) -> Dict[str, Any]:
    """Posts a top-level author comment to an uploaded YouTube video."""
    if not comment_text or not str(comment_text).strip():
        return {"ok": False, "error": "Nội dung bình luận rỗng."}
    try:
        access_token = get_fresh_access_token(channel_id)
        url = "https://www.googleapis.com/youtube/v3/commentThreads?part=snippet"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8"
        }
        body = {
            "snippet": {
                "videoId": video_id,
                "topLevelComment": {
                    "snippet": {
                        "textOriginal": str(comment_text).strip()
                    }
                }
            }
        }
        resp = requests.post(url, headers=headers, json=body, timeout=20)
        if resp.status_code in (200, 201):
            data = resp.json()
            return {"ok": True, "comment_id": data.get("id")}
        err_msg = resp.text
        try:
            err_msg = resp.json().get("error", {}).get("message", resp.text)
        except Exception:
            pass
        logger.warning(f"Không thể đăng bình luận cho video {video_id}: HTTP {resp.status_code} {err_msg}")
        return {"ok": False, "error": err_msg, "status_code": resp.status_code}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def sanitize_youtube_tags(tags: List[str], max_yt_chars: int = 485) -> List[str]:
    """Sanitize tags and ensure total length in YouTube's internal quoted format stays under 500 chars (safe default 485).

    YouTube internally wraps tags containing spaces in quotation marks ("tag name") and counts
    those quotes plus commas towards its strict 500-character barrier. Exceeding it returns HTTP 400 invalidTags.
    """
    clean_tags: List[str] = []
    current_cost = 0
    for t in (tags or []):
        cleaned = re.sub(r'[,<>\"\'\\/]+', ' ', str(t)).strip()
        cleaned = re.sub(r'\s+', ' ', cleaned)[:80]
        if not cleaned:
            continue
        tag_cost = (len(cleaned) + 2) if " " in cleaned else len(cleaned)
        delimiter_cost = 1 if clean_tags else 0
        if current_cost + tag_cost + delimiter_cost > max_yt_chars:
            continue
        if cleaned.lower() not in [ct.lower() for ct in clean_tags]:
            clean_tags.append(cleaned)
            current_cost += tag_cost + delimiter_cost
    return clean_tags


# ---------------------------------------------------------------------------
# RESUMABLE VIDEO UPLOAD & THUMBNAIL PUBLISHING
# ---------------------------------------------------------------------------

def upload_video_to_youtube(
    video_path: Path,
    channel_id: str,
    title: str,
    description: str,
    tags: List[str],
    privacy_status: str = "private",
    category_id: str = "1",  # 1 = Film & Animation
    thumbnail_path: Optional[Path] = None,
    progress_callback: Optional[Callable[[int, int, int], None]] = None,
    playlist_id: Optional[str] = "auto",
    contains_synthetic_media: bool = True,
    publish_at: Optional[str] = None,
    made_for_kids: bool = False,
    license_type: str = "youtube",
    embeddable: bool = True,
    public_stats_viewable: bool = True,
    default_language: Optional[str] = None,
    default_audio_language: Optional[str] = None,
    pinned_comment: Optional[str] = None,
    new_playlist_title: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Perform YouTube Resumable Video Upload with real-time byte chunk progress tracking,
    full YouTube Studio settings (AI disclosure, scheduling, COPPA, license, category),
    and automatic custom thumbnail, playlist assignment, and pinned comment.
    """
    if not video_path.exists():
        raise FileNotFoundError(f"Tệp video không tồn tại: {video_path}")

    file_size = video_path.stat().st_size
    if file_size == 0:
        raise ValueError("Tệp video rỗng (0 bytes).")

    access_token = get_fresh_access_token(channel_id)

    # 1. Initiate Resumable Upload Session
    init_url = "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=UTF-8",
        "X-Upload-Content-Type": "video/mp4",
        "X-Upload-Content-Length": str(file_size)
    }

    # Ensure constraints & sanitize tags (Strict YouTube 500-char quoted barrier compliance)
    clean_t = str(title or "").strip()
    if clean_t.lower() in ("none", "null", "undefined", ""):
        clean_t = video_path.stem.replace("_", " ").title()
    safe_title = clean_t[:100]

    clean_d = str(description or "").strip()
    if clean_d.lower() in ("none", "null", "undefined"):
        clean_d = ""
    safe_desc = clean_d[:5000]
    safe_tags = sanitize_youtube_tags(tags, max_yt_chars=485)
    if privacy_status not in ("private", "unlisted", "public"):
        privacy_status = "private"

    # BCP-47 Language Standardization (e.g. en-US for American English, es, ru, vi)
    bcp47_lang = to_youtube_bcp47(default_language)
    bcp47_audio = to_youtube_bcp47(default_audio_language or default_language)

    snippet_dict = {
        "title": safe_title,
        "description": safe_desc,
        "tags": safe_tags,
        "categoryId": str(category_id or "1")
    }
    if bcp47_lang:
        snippet_dict["defaultLanguage"] = bcp47_lang
    if bcp47_audio:
        snippet_dict["defaultAudioLanguage"] = bcp47_audio

    status_dict = {
        "privacyStatus": privacy_status,
        "selfDeclaredMadeForKids": bool(made_for_kids),
        "containsSyntheticMedia": bool(contains_synthetic_media),
        "license": "creativeCommon" if license_type == "creativeCommon" else "youtube",
        "embeddable": bool(embeddable),
        "publicStatsViewable": bool(public_stats_viewable)
    }

    if publish_at and str(publish_at).strip():
        formatted_pub = format_rfc3339(publish_at)
        if formatted_pub:
            status_dict["privacyStatus"] = "private"
            status_dict["publishAt"] = formatted_pub
            logger.info(f"Lên lịch đăng YouTube: {formatted_pub} (Chế độ chờ Riêng tư, YouTube tự động Công khai khi đến giờ)")

    metadata = {
        "snippet": snippet_dict,
        "status": status_dict
    }

    init_resp = requests.post(init_url, headers=headers, json=metadata, timeout=30)
    if init_resp.status_code not in (200, 201):
        raise RuntimeError(f"Khởi tạo phiên tải video thất bại: HTTP {init_resp.status_code} {init_resp.text}")

    session_url = init_resp.headers.get("Location")
    if not session_url:
        raise RuntimeError("YouTube API không trả về URL tải lên resumable (Location header thiếu).")

    # 2. Upload Video in Chunks (e.g. 5MB chunks, multiple of 256KB)
    chunk_size = 5 * 1024 * 1024  # 5MB
    video_id = None

    with open(video_path, "rb") as vf:
        bytes_uploaded = 0
        while bytes_uploaded < file_size:
            chunk = vf.read(chunk_size)
            if not chunk:
                break
            chunk_len = len(chunk)
            range_end = bytes_uploaded + chunk_len - 1
            chunk_headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Range": f"bytes {bytes_uploaded}-{range_end}/{file_size}",
                "Content-Length": str(chunk_len),
                "Content-Type": "video/mp4"
            }

            chunk_resp = requests.put(session_url, headers=chunk_headers, data=chunk, timeout=60)
            bytes_uploaded += chunk_len
            pct = int((bytes_uploaded / file_size) * 90)  # Reserve last 10% for thumbnail
            if progress_callback:
                progress_callback(pct, bytes_uploaded, file_size)

            if chunk_resp.status_code in (200, 201):
                res_data = chunk_resp.json()
                video_id = res_data.get("id")
                break
            elif chunk_resp.status_code == 308:
                # Incomplete, continue uploading next chunk
                continue
            else:
                raise RuntimeError(f"Lỗi tải dữ liệu video: HTTP {chunk_resp.status_code} {chunk_resp.text}")

    if not video_id:
        raise RuntimeError("Video đã tải lên nhưng không nhận được video ID từ YouTube.")

    # 2.5 Ensure YouTube strictly locks AI Disclosure & exact Language via videos.update
    try:
        update_url = "https://www.googleapis.com/youtube/v3/videos?part=snippet,status"
        update_headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8"
        }
        update_payload = {
            "id": video_id,
            "snippet": snippet_dict,
            "status": status_dict
        }
        up_resp = requests.put(update_url, headers=update_headers, json=update_payload, timeout=25)
        if up_resp.status_code == 200:
            logger.info(f"Đã xác nhận & lưu cài đặt AI Disclosure ({contains_synthetic_media}) và ngôn ngữ ({bcp47_lang}) cho video {video_id}.")
        else:
            logger.warning(f"Lỗi xác nhận videos.update video {video_id}: HTTP {up_resp.status_code} {up_resp.text}")
    except Exception as up_err:
        logger.warning(f"Không thể gọi xác nhận videos.update: {up_err}")

    # 3. Set Custom Thumbnail if provided
    thumb_uploaded = False
    if thumbnail_path and thumbnail_path.exists():
        if progress_callback:
            progress_callback(95, bytes_uploaded, file_size)
        try:
            thumb_uploaded = set_video_thumbnail(video_id, thumbnail_path, access_token)
        except Exception as tex:
            logger.warning(f"Không thể gắn ảnh thumbnail: {tex}")

    # 4. Auto Assign to Playlist (or create new if requested)
    playlist_result = {"ok": False, "skipped": True}
    if new_playlist_title and str(new_playlist_title).strip():
        new_title_clean = str(new_playlist_title).strip()
        try:
            # Check existing playlists first to avoid creating duplicate playlists!
            existing_pls = fetch_channel_playlists(channel_id)
            matching_pl = next((p for p in existing_pls if p.get("title", "").strip().lower() == new_title_clean.lower()), None)
            if matching_pl:
                logger.info(f"Đã tìm thấy playlist trùng tên '{new_title_clean}' (ID: {matching_pl['id']}), tái sử dụng thay vì tạo mới trùng lặp!")
                playlist_id = matching_pl["id"]
            else:
                c_pl = create_playlist(channel_id, new_title_clean)
                if c_pl.get("ok"):
                    playlist_id = c_pl.get("id")
                    logger.info(f"Đã tạo playlist mới '{new_title_clean}' trên YouTube: {playlist_id}")
        except Exception as pl_create_err:
            logger.warning(f"Không thể kiểm tra/tạo playlist mới: {pl_create_err}")

    if playlist_id and playlist_id != "none":
        target_pl_id = playlist_id
        if target_pl_id == "auto":
            try:
                pls = fetch_channel_playlists(channel_id)
                if pls:
                    keywords = [safe_title.lower(), "stoic", "philosophy", "series", "tập", "full"]
                    matched = None
                    for pl in pls:
                        pl_title_low = pl.get("title", "").lower()
                        for kw in keywords:
                            if kw and kw in pl_title_low:
                                matched = pl["id"]
                                break
                        if matched:
                            break
                    target_pl_id = matched or pls[0]["id"]
            except Exception as pe:
                logger.warning(f"Lỗi tự động dò playlist: {pe}")

        if target_pl_id and target_pl_id not in ("none", "auto"):
            # Sleep 1.5s for YouTube internal video propagation across playlist shards
            time.sleep(1.5)
            try:
                pl_res = add_video_to_playlist(channel_id, video_id, target_pl_id)
                playlist_result = pl_res
                if pl_res.get("ok"):
                    logger.info(f"Đã tự động thêm video {video_id} vào playlist {target_pl_id}")
                else:
                    logger.warning(f"Thêm video vào playlist: {pl_res.get('error')}")
            except Exception as pl_exc:
                playlist_result = {"ok": False, "error": str(pl_exc)}

    # 5. Auto Post Pinned Comment
    pinned_comment_res = {"ok": False, "skipped": True}
    if pinned_comment and str(pinned_comment).strip():
        try:
            pinned_comment_res = post_pinned_comment(channel_id, video_id, str(pinned_comment).strip())
            if pinned_comment_res.get("ok"):
                logger.info(f"Đã tự động đăng bình luận ghim cho video {video_id}")
        except Exception as c_exc:
            pinned_comment_res = {"ok": False, "error": str(c_exc)}

    if progress_callback:
        progress_callback(100, file_size, file_size)

    return {
        "ok": True,
        "video_id": video_id,
        "video_url": f"https://youtu.be/{video_id}",
        "studio_url": f"https://studio.youtube.com/video/{video_id}/edit",
        "title": safe_title,
        "privacy": privacy_status,
        "publish_at": status_dict.get("publishAt"),
        "thumbnail_uploaded": thumb_uploaded,
        "playlist_added": playlist_result.get("ok", False),
        "playlist_id": playlist_result.get("playlist_id", ""),
        "playlist_error": playlist_result.get("error", None),
        "pinned_comment_posted": pinned_comment_res.get("ok", False),
        "pinned_comment_id": pinned_comment_res.get("comment_id", ""),
        "channel_id": channel_id
    }


def set_video_thumbnail(video_id: str, thumbnail_path: Path, access_token: str) -> bool:
    """Upload custom 1280x720 thumbnail for the published video."""
    thumb_url = f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={video_id}"
    mime = "image/jpeg"
    if thumbnail_path.suffix.lower() == ".png":
        mime = "image/png"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": mime
    }
    with open(thumbnail_path, "rb") as tf:
        thumb_bytes = tf.read()

    resp = requests.post(thumb_url, headers=headers, data=thumb_bytes, timeout=30)
    return resp.status_code in (200, 201)


def fetch_live_video_details(video_id: str, channel_id: Optional[str] = None) -> Dict[str, Any]:
    """Fetch live video snippet and statistics directly via YouTube Data API v3."""
    cfg = load_youtube_config()
    target_ch_id = channel_id or cfg.get("active_channel_id")
    if not target_ch_id and cfg.get("channels"):
        target_ch_id = cfg["channels"][0].get("id")
    if not target_ch_id:
        raise ValueError("Chưa cấu hình kênh YouTube nào.")
    access_token = get_fresh_access_token(target_ch_id)
    headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
    url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails,status,statistics&id={video_id}"
    resp = requests.get(url, headers=headers, timeout=15)
    if resp.status_code != 200:
        raise RuntimeError(f"YouTube API trả về lỗi: {resp.status_code} {resp.text}")
    items = resp.json().get("items", [])
    if not items:
        raise ValueError(f"Không tìm thấy video với ID {video_id} trên YouTube.")
    return items[0]


def update_live_video_metadata(
    video_id: str,
    title: str,
    description: str,
    tags: List[str],
    channel_id: Optional[str] = None,
    category_id: str = "1",
) -> Dict[str, Any]:
    """Update title, description, and tags on an existing live YouTube video via official API."""
    cfg = load_youtube_config()
    target_ch_id = channel_id or cfg.get("active_channel_id")
    if not target_ch_id and cfg.get("channels"):
        target_ch_id = cfg["channels"][0].get("id")
    if not target_ch_id:
        raise ValueError("Chưa cấu hình kênh YouTube nào.")
    access_token = get_fresh_access_token(target_ch_id)
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

    clean_tags = sanitize_youtube_tags(tags, max_yt_chars=485)

    payload = {
        "id": video_id,
        "snippet": {
            "title": (title or "")[:100],
            "description": (description or "")[:5000],
            "tags": clean_tags,
            "categoryId": category_id or "1",
        }
    }
    url = "https://www.googleapis.com/youtube/v3/videos?part=snippet"
    resp = requests.put(url, headers=headers, json=payload, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"Lỗi cập nhật video YouTube: {resp.status_code} {resp.text}")
    return resp.json()


# ---------------------------------------------------------------------------
# ASYNCHRONOUS BACKGROUND UPLOADER THREAD
# ---------------------------------------------------------------------------

def start_background_upload(
    video_path: Path,
    channel_id: str,
    title: str,
    description: str,
    tags: List[str],
    privacy_status: str = "private",
    thumbnail_path: Optional[Path] = None,
    playlist_id: Optional[str] = "auto",
    contains_synthetic_media: bool = True,
    publish_at: Optional[str] = None,
    made_for_kids: bool = False,
    category_id: str = "1",
    license_type: str = "youtube",
    embeddable: bool = True,
    public_stats_viewable: bool = True,
    default_language: Optional[str] = None,
    default_audio_language: Optional[str] = None,
    pinned_comment: Optional[str] = None,
    new_playlist_title: Optional[str] = None,
) -> Dict[str, Any]:
    """Start asynchronous upload thread and return immediately."""
    global _upload_state
    with _upload_lock:
        if _upload_state["status"] in ("uploading", "setting_thumbnail"):
            return {
                "ok": False,
                "error": "Hiện đang có một video khác đang được tải lên YouTube. Vui lòng chờ hoàn tất."
            }

        _upload_state = {
            "status": "uploading",
            "percent": 0,
            "bytes_sent": 0,
            "total_bytes": video_path.stat().st_size if video_path.exists() else 0,
            "message": "Đang kết nối tới máy chủ YouTube...",
            "video_id": "",
            "video_url": "",
            "studio_url": "",
            "error": None,
            "playlist_added": False,
            "playlist_error": None,
            "pinned_comment_posted": False,
            "contains_synthetic_media": bool(contains_synthetic_media),
            "start_time": time.time(),
            "completed_at": 0
        }

    def _worker():
        global _upload_state
        try:
            def _progress(pct, sent, total):
                with _upload_lock:
                    _upload_state["percent"] = pct
                    _upload_state["bytes_sent"] = sent
                    _upload_state["total_bytes"] = total
                    mb_sent = sent / (1024 * 1024)
                    mb_total = total / (1024 * 1024)
                    if pct < 90:
                        _upload_state["message"] = f"Đang tải lên: {pct}% ({mb_sent:.1f}/{mb_total:.1f} MB)"
                    elif pct < 98:
                        _upload_state["message"] = "Đang đồng bộ ảnh Thumbnail HD 1280x720..."
                    else:
                        _upload_state["message"] = "Đang gán Playlist & Bình luận ghim..."

            result = upload_video_to_youtube(
                video_path=video_path,
                channel_id=channel_id,
                title=title,
                description=description,
                tags=tags,
                privacy_status=privacy_status,
                category_id=category_id,
                thumbnail_path=thumbnail_path,
                progress_callback=_progress,
                playlist_id=playlist_id,
                contains_synthetic_media=contains_synthetic_media,
                publish_at=publish_at,
                made_for_kids=made_for_kids,
                license_type=license_type,
                embeddable=embeddable,
                public_stats_viewable=public_stats_viewable,
                default_language=default_language,
                default_audio_language=default_audio_language,
                pinned_comment=pinned_comment,
                new_playlist_title=new_playlist_title,
            )

            with _upload_lock:
                _upload_state["status"] = "done"
                _upload_state["percent"] = 100
                _upload_state["video_id"] = result.get("video_id", "")
                _upload_state["video_url"] = result.get("video_url", "")
                _upload_state["studio_url"] = result.get("studio_url", "")
                _upload_state["playlist_added"] = result.get("playlist_added", False)
                _upload_state["playlist_error"] = result.get("playlist_error", None)

                pl_msg = ""
                if result.get("playlist_added"):
                    pl_msg = " & đã thêm vào Danh sách phát!"
                elif result.get("playlist_error"):
                    pl_msg = f" (Danh sách phát: {result.get('playlist_error')})"

                sched_msg = ""
                if result.get("publish_at"):
                    sched_msg = f" ⏰ Đã lên lịch tự động công khai: {result.get('publish_at')}"
                    _upload_state["publish_at"] = result.get("publish_at")

                _upload_state["message"] = f"Đã đăng tải thành công lên YouTube ({result.get('privacy')}){pl_msg}!{sched_msg}"
                _upload_state["completed_at"] = time.time()

        except Exception as exc:
            logger.exception("Upload failed")
            with _upload_lock:
                _upload_state["status"] = "error"
                _upload_state["error"] = str(exc)
                _upload_state["message"] = f"Lỗi tải lên: {exc}"
                _upload_state["completed_at"] = time.time()

    t = threading.Thread(target=_worker, name="YouTubeUploaderThread", daemon=True)
    t.start()
    return {"ok": True, "message": "Tiến trình tải lên YouTube đã bắt đầu trong nền."}


def start_background_batch_upload(
    tasks: List[Dict[str, Any]],
    series_name: str = "",
    episode_num: int = 1
) -> Dict[str, Any]:
    """Upload multiple video formats in sequence (e.g. Long Video 16:9 first, followed by Shorts 9:16)."""
    global _upload_state
    with _upload_lock:
        if _upload_state["status"] in ("uploading", "setting_thumbnail"):
            return {
                "ok": False,
                "error": "Hiện đang có một video khác đang được tải lên YouTube. Vui lòng chờ hoàn tất."
            }

        valid_tasks = [t for t in tasks if t.get("video_path") and Path(t["video_path"]).exists()]
        if not valid_tasks:
            return {"ok": False, "error": "Không tìm thấy tệp video hợp lệ để tải lên."}

        total_bytes_sum = sum(Path(t["video_path"]).stat().st_size for t in valid_tasks)
        _upload_state = {
            "status": "uploading",
            "percent": 0,
            "bytes_sent": 0,
            "total_bytes": total_bytes_sum,
            "message": f"Bắt đầu chuỗi xuất bản 2 thể loại ({len(valid_tasks)} video)...",
            "video_id": "",
            "video_url": "",
            "studio_url": "",
            "error": None,
            "playlist_added": False,
            "playlist_error": None,
            "pinned_comment_posted": False,
            "contains_synthetic_media": True,
            "start_time": time.time(),
            "completed_at": 0,
            "results": []
        }

    def _worker():
        global _upload_state
        try:
            total_tasks = len(valid_tasks)
            uploaded_results = []
            long_video_url = ""

            for i, task in enumerate(valid_tasks):
                task_desc = task.get("label", f"Video {i+1}")
                v_path = Path(task["video_path"])

                def _progress(pct, sent, total):
                    with _upload_lock:
                        overall_pct = int(((i * 100) + pct) / total_tasks)
                        _upload_state["percent"] = overall_pct
                        _upload_state["bytes_sent"] = sent
                        _upload_state["total_bytes"] = total
                        mb_sent = sent / (1024 * 1024)
                        mb_total = total / (1024 * 1024)
                        if pct < 90:
                            _upload_state["message"] = f"[{i+1}/{total_tasks}] Đang tải {task_desc}: {pct}% ({mb_sent:.1f}/{mb_total:.1f} MB)"
                        elif pct < 98:
                            _upload_state["message"] = f"[{i+1}/{total_tasks}] Đang đồng bộ ảnh Thumbnail & Thiết lập {task_desc}..."
                        else:
                            _upload_state["message"] = f"[{i+1}/{total_tasks}] Đang gán Playlist & Ghim bình luận {task_desc}..."

                # If this is Shorts (the second item) and we already have long_video_url, inject it into pinned comment
                p_comment = task.get("pinned_comment")
                if i > 0 and long_video_url and p_comment:
                    if long_video_url not in p_comment:
                        task_lang = str(task.get("language") or "").lower()
                        if any(k in task_lang for k in ("vi", "viet", "tiếng việt")):
                            prefix_link = f"👉 Xem trọn bộ tập phim dài 16:9 tại đây: {long_video_url}"
                        elif any(k in task_lang for k in ("es", "span", "español")):
                            prefix_link = f"👉 Mira el episodio completo en 16:9 aquí: {long_video_url}"
                        elif any(k in task_lang for k in ("ru", "rus", "рус")):
                            prefix_link = f"👉 Смотрите полную серию 16:9 здесь: {long_video_url}"
                        elif any(k in task_lang for k in ("de", "german", "deutsch")):
                            prefix_link = f"👉 Die ganze Folge in 16:9 hier ansehen: {long_video_url}"
                        elif any(k in task_lang for k in ("fr", "french", "français")):
                            prefix_link = f"👉 Regardez l'épisode complet en 16:9 ici: {long_video_url}"
                        else:
                            prefix_link = f"👉 Watch the full 16:9 episode here: {long_video_url}"
                        p_comment = f"{prefix_link}\n\n{p_comment}"

                res = upload_video_to_youtube(
                    video_path=v_path,
                    channel_id=task["channel_id"],
                    title=task["title"],
                    description=task["description"],
                    tags=task["tags"],
                    privacy_status=task.get("privacy_status", "unlisted"),
                    category_id=task.get("category_id", "1"),
                    thumbnail_path=task.get("thumbnail_path"),
                    progress_callback=_progress,
                    playlist_id=task.get("playlist_id", "auto"),
                    contains_synthetic_media=task.get("contains_synthetic_media", True),
                    publish_at=task.get("publish_at"),
                    made_for_kids=task.get("made_for_kids", False),
                    license_type=task.get("license_type", "youtube"),
                    embeddable=task.get("embeddable", True),
                    public_stats_viewable=task.get("public_stats_viewable", True),
                    default_language=task.get("default_language"),
                    default_audio_language=task.get("default_audio_language"),
                    pinned_comment=p_comment,
                    new_playlist_title=task.get("new_playlist_title"),
                )
                uploaded_results.append(res)
                if i == 0:
                    long_video_url = res.get("video_url", "")

            with _upload_lock:
                _upload_state["status"] = "done"
                _upload_state["percent"] = 100
                _upload_state["results"] = uploaded_results
                _upload_state["video_id"] = uploaded_results[-1].get("video_id", "")
                _upload_state["video_url"] = uploaded_results[-1].get("video_url", "")
                _upload_state["studio_url"] = uploaded_results[-1].get("studio_url", "")
                _upload_state["message"] = f"🎉 Đã đăng thành công CẢ 2 THỂ LOẠI (Video Dài 16:9 & Shorts 9:16) lên kênh YouTube!"
                _upload_state["completed_at"] = time.time()

        except Exception as exc:
            logger.exception("Batch upload failed")
            with _upload_lock:
                _upload_state["status"] = "error"
                _upload_state["error"] = str(exc)
                _upload_state["message"] = f"Lỗi tải lên: {exc}"
                _upload_state["completed_at"] = time.time()

    t = threading.Thread(target=_worker, name="YouTubeBatchUploaderThread", daemon=True)
    t.start()
    return {"ok": True, "message": "Chuỗi đăng tải 2 thể loại (Video dài + Shorts) đã bắt đầu trong nền."}


def get_current_upload_status() -> Dict[str, Any]:
    """Return live status of the upload process."""
    with _upload_lock:
        return dict(_upload_state)


def resolve_episode_media(ep_dir: Path, media_type: str = "long") -> Dict[str, Any]:
    """Find the best video MP4, thumbnail JPEG, and SEO metadata pack in an episode folder.
    Supports media_type='long' (16:9 full episode) or media_type='short' (9:16 Shorts highlight).
    """
    if not ep_dir or not ep_dir.exists():
        return {
            "video_path": None,
            "thumbnail_path": None,
            "title": "",
            "description": "",
            "tags": [],
            "vidiq_score": 0,
            "is_short": (media_type == "short")
        }

    is_short = (str(media_type).lower() == "short")
    video_path = None

    if is_short:
        # 1. Check episode_short.mp4
        if (ep_dir / "episode_short.mp4").is_file():
            video_path = ep_dir / "episode_short.mp4"
        elif (ep_dir / "00_DANG_BAI_YOUTUBE" / "02_VIDEO_SHORTS_9x16.mp4").is_file():
            video_path = ep_dir / "00_DANG_BAI_YOUTUBE" / "02_VIDEO_SHORTS_9x16.mp4"
        elif (ep_dir / "00_DANG_BAI_YOUTUBE").is_dir():
            for mp4 in (ep_dir / "00_DANG_BAI_YOUTUBE").glob("*short*.mp4"):
                video_path = mp4
                break
        # Auto generate on the fly if not yet created!
        if not video_path:
            try:
                import shorts_extractor
                res_gen = shorts_extractor.generate_episode_short(ep_dir)
                if res_gen.get("ok") and (ep_dir / "episode_short.mp4").is_file():
                    video_path = ep_dir / "episode_short.mp4"
            except Exception as e:
                logger.warning(f"Auto-generation of shorts failed: {e}")
    else:
        # Long video resolution
        if (ep_dir / "episode_final.mp4").is_file():
            video_path = ep_dir / "episode_final.mp4"
        elif (ep_dir / "00_DANG_BAI_YOUTUBE").is_dir():
            for mp4 in (ep_dir / "00_DANG_BAI_YOUTUBE").glob("*.mp4"):
                if "short" not in mp4.name.lower():
                    video_path = mp4
                    break
        if not video_path:
            for mp4 in sorted(ep_dir.glob("*.mp4"), key=lambda p: p.stat().st_size, reverse=True):
                if "raw" not in mp4.name and "temp" not in mp4.name and "short" not in mp4.name.lower():
                    video_path = mp4
                    break

    # Read SEO pack
    import json
    pack_data = {}
    pack_path = ep_dir / "youtube_publish_pack.json"
    if pack_path.is_file() and pack_path.stat().st_size >= 10:
        try:
            pack_data = json.loads(pack_path.read_text(encoding="utf-8"))
        except Exception as _p_err:
            logger.warning(f"Error parsing youtube_publish_pack.json: {_p_err}")
            pack_data = {}

    if not pack_data or not pack_data.get("best_title") or not pack_data.get("description"):
        # Fallback to reference_analysis.json if available
        ref_path = ep_dir / "reference_analysis.json"
        if ref_path.is_file():
            try:
                ref_d = json.loads(ref_path.read_text(encoding="utf-8"))
                if not pack_data.get("best_title") and ref_d.get("title"):
                    pack_data["best_title"] = ref_d.get("title")
                if not pack_data.get("description") and ref_d.get("description"):
                    pack_data["description"] = ref_d.get("description")
                if not pack_data.get("tags") and ref_d.get("keywords"):
                    pack_data["tags"] = ref_d.get("keywords")
                if not pack_data.get("language") and ref_d.get("language"):
                    pack_data["language"] = ref_d.get("language")
            except Exception:
                pass

    if not pack_data.get("language"):
        plan_p = ep_dir / "plan.json"
        if plan_p.is_file():
            try:
                p_data = json.loads(plan_p.read_text(encoding="utf-8"))
                pack_data["language"] = p_data.get("language") or p_data.get("config", {}).get("language") or ""
            except Exception:
                pass

    # Shorts specific SEO pack resolution
    if is_short:
        shorts_pack = pack_data.get("shorts_package")
        if not shorts_pack:
            shorts_json_p = ep_dir / "youtube_shorts_pack.json"
            if shorts_json_p.is_file():
                try:
                    shorts_pack = json.loads(shorts_json_p.read_text(encoding="utf-8"))
                except Exception:
                    pass
        if shorts_pack:
            return {
                "video_path": video_path,
                "thumbnail_path": None,  # Shorts use frame extraction on YouTube
                "title": shorts_pack.get("best_title") or f"{ep_dir.parent.name} #shorts",
                "description": shorts_pack.get("description", ""),
                "tags": shorts_pack.get("tags", ["shorts", "youtube shorts"]),
                "vidiq_score": 100,
                "language": pack_data.get("language", ""),
                "pinned_comment": shorts_pack.get("pinned_comment", ""),
                "is_short": True
            }

    # Video thumbnail resolution (honoring vertical Shorts vs 16:9)
    thumb_path = None
    if pack_data.get("thumbnail_file") and Path(pack_data["thumbnail_file"]).is_file():
        thumb_path = Path(pack_data["thumbnail_file"])
    elif (ep_dir / "thumbnail_shorts.jpg").is_file() and (pack_data.get("is_short") or pack_data.get("is_vertical_short")):
        thumb_path = ep_dir / "thumbnail_shorts.jpg"
    elif (ep_dir / "thumbnail_seo.jpg").is_file():
        thumb_path = ep_dir / "thumbnail_seo.jpg" 
    elif (ep_dir / "00_DANG_BAI_YOUTUBE").is_dir():
        for jpg in (ep_dir / "00_DANG_BAI_YOUTUBE").glob("*.jpg"):
            thumb_path = jpg
            break

    series_fallback = ep_dir.parent.name if ep_dir else "Tập Phim Mới"
    return {
        "video_path": video_path,
        "thumbnail_path": thumb_path,
        "title": pack_data.get("best_title") or series_fallback,
        "description": pack_data.get("description", ""),
        "tags": pack_data.get("tags", []),
        "vidiq_score": pack_data.get("vidiq_score", 100),
        "language": pack_data.get("language", ""),
        "pinned_comment": pack_data.get("pinned_comment", ""),
        "publish_pack": pack_data,
        "is_short": False
    }

def auto_upload_episode(
    episode_dir: Path,
    series_name: str,
    language: str = "",
    privacy_status: str = "unlisted"
) -> Dict[str, Any]:
    """Automatically upload an episode to YouTube after rendering finishes.
    Selects mapped channel for series, extracts metadata, thumbnails,
    and uploads in unlisted mode so creator can review while YouTube processes HD/4K.
    """
    config = load_youtube_config()
    channels = config.get("channels", [])
    if not channels:
        return {"ok": False, "skipped": True, "reason": "Chưa có kênh YouTube nào được kết nối trong hệ thống."}

    channel_id = get_series_channel(series_name, language)
    if not channel_id:
        channel_id = config.get("active_channel_id") or channels[0].get("id")

    target_ch = next((c for c in channels if c.get("id") == channel_id), None)
    if not target_ch or not (target_ch.get("refresh_token") or target_ch.get("access_token")):
        return {"ok": False, "skipped": True, "reason": f"Kênh {channel_id} chưa được cấp quyền OAuth hợp lệ."}
    if target_ch.get("token_expired"):
        return {"ok": False, "skipped": True, "token_expired": True, "reason": f"Phiên xác thực Google OAuth của kênh '{target_ch.get('name')}' đã hết hạn sau 7 ngày (Google OAuth chế độ Testing). Vui lòng vào '📺 Kênh YouTube' và bấm nút '🔑 Cấp quyền lại' để tiếp tục đăng tự động."}

    media_info = resolve_episode_media(episode_dir, media_type="long")
    video_path = media_info.get("video_path")
    if not video_path or not Path(video_path).is_file():
        return {"ok": False, "error": f"Không tìm thấy file video hoàn chỉnh trong {episode_dir}"}

    ch_settings = get_channel_publish_settings(channel_id)

    # Force unlisted as requested to allow YouTube to process HD without premature public release
    eff_privacy = "unlisted" if privacy_status in ("unlisted", "public", "") else privacy_status

    title = media_info.get("title") or video_path.stem
    desc = media_info.get("description", "")
    tags = media_info.get("tags", [])
    thumb = media_info.get("thumbnail_path")
    if thumb and not Path(thumb).is_file():
        thumb = None

    playlist_id = ch_settings.get("default_playlist_id", "auto")
    cat_id = ch_settings.get("category_id", "1")
    made_for_kids = ch_settings.get("made_for_kids", False)
    synthetic = ch_settings.get("contains_synthetic_media", True)
    license_type = ch_settings.get("license", "youtube")
    pinned_comment = media_info.get("pinned_comment")

    def _prog(pct, sent, total):
        if pct % 25 == 0 or pct == 100:
            print(f"   [YOUTUBE UPLOAD] {pct}% ({round(sent / (1024*1024), 1)} MB / {round(total / (1024*1024), 1)} MB)...", flush=True)

    try:
        ch_name = target_ch.get("name") or target_ch.get("title") or channel_id
        print(f"[YOUTUBE] Bắt đầu tự động tải video lên kênh '{ch_name}'...", flush=True)
        print(f"   Tiêu đề: {title[:75]}...", flush=True)
        print(f"   Trạng thái: Không công khai (Unlisted)", flush=True)
        res = upload_video_to_youtube(
            video_path=Path(video_path),
            channel_id=channel_id,
            title=title,
            description=desc,
            tags=tags,
            privacy_status=eff_privacy,
            category_id=cat_id,
            thumbnail_path=Path(thumb) if thumb else None,
            progress_callback=_prog,
            playlist_id=playlist_id,
            contains_synthetic_media=synthetic,
            made_for_kids=made_for_kids,
            license_type=license_type,
            pinned_comment=pinned_comment,
            new_playlist_title=None
        )
        if res.get("ok"):
            record = {
                "uploaded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "channel_id": channel_id,
                "channel_title": target_ch.get("name") or target_ch.get("title") or channel_id,
                "video_id": res.get("video_id"),
                "video_url": res.get("video_url"),
                "studio_url": res.get("studio_url"),
                "privacy_status": eff_privacy,
                "title": title
            }
            try:
                (episode_dir / "youtube_uploaded.json").write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
            except Exception:
                pass
        return res
    except Exception as exc:
        logger.error(f"Auto-upload failed: {exc}")
        return {"ok": False, "error": str(exc)}

