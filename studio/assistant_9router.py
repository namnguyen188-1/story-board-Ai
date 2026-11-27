"""Isolated Studio Chat AI Co-Pilot routed strictly through local 9router (127.0.0.1:20128).

Never reads Storyboard AI Gemini .env keys and never touches FreeLLMAPI (31415) or
active video rendering pipelines.
"""
from __future__ import annotations

import os
import re
import shutil
import sqlite3
import subprocess
import time
import webbrowser
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests

ROUTER_HOST = "127.0.0.1"
ROUTER_PORT = 20128
ROUTER_BASE_URL = f"http://{ROUTER_HOST}:{ROUTER_PORT}"
ROUTER_DASHBOARD_URL = f"{ROUTER_BASE_URL}/dashboard"

_NODE_CANDIDATES = (
    shutil.which("node"),
    r"C:\Program Files\nodejs\node.exe",
    r"C:\Program Files (x86)\nodejs\node.exe",
)


def _find_node_exe() -> Optional[str]:
    for cand in _NODE_CANDIDATES:
        if cand and os.path.isfile(cand):
            return cand
    return None


def _find_9router_cli() -> Optional[Path]:
    appdata = os.environ.get("APPDATA", "")
    candidates = [
        Path(appdata) / "npm" / "node_modules" / "9router" / "cli.js",
        Path.home() / "AppData" / "Roaming" / "npm" / "node_modules" / "9router" / "cli.js",
    ]
    for p in candidates:
        if p.is_file():
            return p
    return None


def _router_db_path() -> Optional[Path]:
    appdata = os.environ.get("APPDATA", "")
    p = Path(appdata) / "9router" / "db" / "data.sqlite"
    return p if p.is_file() else None


def _read_db_summary_and_key() -> tuple[Dict[str, Any], str]:
    """Reads non-secret provider metadata + optional loopback key purely in Python memory."""
    summary: Dict[str, Any] = {
        "active_providers": [],
        "total_connections": 0,
        "combos": [],
    }
    api_key = ""
    db_path = _router_db_path()
    if not db_path:
        return summary, api_key

    try:
        conn = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True, timeout=1.5)
        try:
            tables = {
                r[0]
                for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            }
            if "providerConnections" in tables:
                rows = conn.execute(
                    "SELECT provider, authType, name, isActive FROM providerConnections"
                ).fetchall()
                summary["total_connections"] = len(rows)
                summary["active_providers"] = [
                    {
                        "provider": str(r[0] or ""),
                        "auth_type": str(r[1] or ""),
                        "name": str(r[2] or r[0] or ""),
                    }
                    for r in rows
                    if r[3] in (1, True, "1", "true")
                ]
            if "combos" in tables:
                cols = {r[1] for r in conn.execute("PRAGMA table_info(combos)").fetchall()}
                if "isActive" in cols:
                    c_rows = conn.execute("SELECT name, isActive FROM combos").fetchall()
                    summary["combos"] = [str(r[0]) for r in c_rows if r[0] and r[1] in (1, True, "1")]
                elif "name" in cols:
                    c_rows = conn.execute("SELECT name FROM combos").fetchall()
                    summary["combos"] = [str(r[0]) for r in c_rows if r[0]]
            if "apiKeys" in tables:
                cols = [r[1] for r in conn.execute("PRAGMA table_info(apiKeys)").fetchall()]
                key_col = "key" if "key" in cols else ("apiKey" if "apiKey" in cols else "")
                if key_col:
                    k_row = conn.execute(f"SELECT {key_col} FROM apiKeys LIMIT 1").fetchone()
                    if k_row and isinstance(k_row[0], str):
                        api_key = k_row[0].strip()
        finally:
            conn.close()
    except Exception:
        pass
    return summary, api_key


def is_router_running(timeout: float = 1.2) -> bool:
    try:
        resp = requests.get(f"{ROUTER_BASE_URL}/v1/models", timeout=timeout)
        return resp.status_code in (200, 401, 403)
    except Exception:
        return False


def fetch_models(timeout: float = 3.0) -> List[str]:
    summary, api_key = _read_db_summary_and_key()
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    models: List[str] = list(summary.get("combos") or [])
    try:
        resp = requests.get(f"{ROUTER_BASE_URL}/v1/models", headers=headers, timeout=timeout)
        if resp.status_code == 200:
            payload = resp.json()
            for item in payload.get("data", []) if isinstance(payload, dict) else []:
                if isinstance(item, dict) and item.get("id"):
                    mid = str(item["id"])
                    if mid not in models:
                        models.append(mid)
    except Exception:
        pass
    return models[:80]


_FREELLMAPI_PREFERRED_MODELS = (
    "claude-sonnet-4-5",
    "claude-haiku-4-5",
    "claude-opus-4-5",
    "gpt-oss-120b",
    "qwen3.8-27b",
    "llama-3.3-70b",
    "auto",
)

_NOISY_MODEL_SUBSTRINGS = ("uncensored", "aggressive", "guard", "q4-k-", "heretic", "iq4", "impish")


def _is_valid_assistant_reply(text: str, user_prompt: str = "") -> bool:
    """Rejects classifier/guard stubs (e.g. 'Safety: Safe\\nCategories: None') or truncated noise."""
    s = str(text or "").strip()
    if not s:
        return False
    low = s.lower()
    if re.search(r"^\s*safety\s*:\s*(?:safe|unsafe)\b", low) or "categories:\s*none" in low.replace(" ", ""):
        return False
    if re.fullmatch(r"(?:safe|unsafe|none|ok|null|undefined)[.!]?", low):
        return False
    # If the user wrote a detailed script/chat prompt (>18 chars), ignore ultra-short 1-2 word glitches
    if len(str(user_prompt or "").strip()) > 18 and len(s) < 15:
        return False
    return True


def _clean_assistant_reply(text: str) -> str:
    """Normalize stray HTML breaks and markdown table pipes into crisp plain prose."""
    s = str(text or "").strip()
    if not s:
        return ""
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.IGNORECASE)
    s = re.sub(r"</?(?:p|div|span|b|strong|i|em)[^>]*>", "", s, flags=re.IGNORECASE)
    cleaned_lines: List[str] = []
    for line in s.splitlines():
        st = line.strip()
        # Drop pure markdown table divider lines like |---|---|
        if re.fullmatch(r"\|?(?:\s*:?-+:?\s*\|)+\s*:?-*:?\s*\|?", st):
            continue
        # Drop standalone horizontal rules --- / ===
        if re.fullmatch(r"[-=*_]{3,}", st):
            continue
        # Convert markdown table row "| Visual | Dialogue |" -> readable text
        if st.startswith("|") and st.endswith("|") and st.count("|") >= 2:
            cells = [c.strip() for c in st.strip("|").split("|") if c.strip()]
            if cells and not (len(cells) == 2 and cells[0].lower() in ("visual", "hình ảnh") and cells[1].lower() in ("dialogue", "diálogo", "lời thoại")):
                cleaned_lines.append(" — ".join(cells))
            continue
        cleaned_lines.append(line.rstrip())
    out = "\n".join(cleaned_lines)
    out = re.sub(r"\n{3,}", "\n\n", out).strip()
    return out


def _get_freellmapi_info(include_models: bool = True) -> Dict[str, Any]:
    """Inspect local FreeLLMAPI (:31415) availability & curated model list (never exposes API keys)."""
    info: Dict[str, Any] = {
        "installed": False,
        "running": False,
        "ready": False,
        "model_count": 0,
        "models": [],
    }
    try:
        import freellmapi_provider as fp

        cfg = fp.get_config()
        if str(cfg.get("mode") or "").lower() == "off":
            return info
        info["installed"] = fp.find_executable() is not None
        running = fp.is_running(cfg["base_url"])
        info["running"] = running
        api_key = str(cfg.get("api_key") or "").strip()
        if not running or not api_key:
            return info

        info["ready"] = True
        if include_models:
            try:
                resp = requests.get(
                    f"{cfg['base_url']}/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=2.5,
                )
                if resp.status_code == 200:
                    data = resp.json().get("data", []) if isinstance(resp.json(), dict) else []
                    ids = [str(m.get("id")) for m in data if isinstance(m, dict) and m.get("id")]
                    info["model_count"] = len(ids)
                    id_set = set(ids)
                    ordered: List[str] = [m for m in _FREELLMAPI_PREFERRED_MODELS if m in id_set and m != "auto"]
                    for mid in ids:
                        low = mid.lower()
                        if mid not in ordered and mid != "auto" and not any(bad in low for bad in _NOISY_MODEL_SUBSTRINGS):
                            ordered.append(mid)
                        if len(ordered) >= 24:
                            break
                    info["models"] = ordered
            except Exception:
                pass
    except Exception:
        pass
    return info


def _freellmapi_in_cooldown() -> bool:
    try:
        return time.time() < float(os.environ.get("STORYBOARD_FREELLMAPI_COOLDOWN_UNTIL", "0") or 0)
    except Exception:
        return False


def _mark_freellmapi_cooldown(seconds: float = 180.0) -> None:
    os.environ["STORYBOARD_FREELLMAPI_COOLDOWN_UNTIL"] = str(time.time() + float(seconds))


def _clear_freellmapi_cooldown() -> None:
    os.environ.pop("STORYBOARD_FREELLMAPI_COOLDOWN_UNTIL", None)


def _get_studio_ai_models() -> tuple[bool, bool, List[str]]:
    """Checks Studio built-in LLM gateways (Tuấn Stor & Gemini API Pool) for reliable failover."""
    has_tuansu = False
    has_gemini = False
    models: List[str] = []
    try:
        import tuansuapi_provider as tp
        cfg = tp.get_gateway_config()
        if str(cfg.get("enabled") or "1") == "1" and str(cfg.get("api_key") or "").strip():
            has_tuansu = True
            t_m = str(cfg.get("text_model") or tp.DEFAULT_TEXT_MODEL).strip()
            if t_m and t_m not in models:
                models.append(t_m)
    except Exception:
        pass
    try:
        import resilient_gemini
        keys = resilient_gemini.load_api_keys()
        if keys:
            has_gemini = True
            for gm in ("gemini-2.5-flash", "gemini-2.5-pro"):
                if gm not in models:
                    models.append(gm)
    except Exception:
        pass
    return has_tuansu, has_gemini, models


def get_status() -> Dict[str, Any]:
    cli_path = _find_9router_cli()
    node_exe = _find_node_exe()
    installed = bool(cli_path and node_exe)
    running = is_router_running()
    db_summary, _ = _read_db_summary_and_key()
    router_models = fetch_models() if running else []
    has_router_ai = bool(running and (db_summary["active_providers"] or router_models))

    f_info = _get_freellmapi_info(include_models=(not has_router_ai))
    has_tuansu, has_gemini, studio_models = _get_studio_ai_models()
    has_studio_ai = bool(has_tuansu or has_gemini)

    if has_router_ai:
        active_backend = "9router"
        models = list(router_models)
        for sm in studio_models:
            if sm not in models:
                models.append(sm)
    elif f_info["ready"] and not _freellmapi_in_cooldown():
        active_backend = "freellmapi"
        models = list(studio_models) + [m for m in f_info["models"] if m not in studio_models]
    elif has_studio_ai:
        active_backend = "studio_ai"
        models = list(studio_models) + ([m for m in f_info["models"] if m not in studio_models] if f_info["ready"] else [])
    elif f_info["ready"]:
        active_backend = "freellmapi"
        models = f_info["models"]
    else:
        active_backend = "none"
        models = []

    return {
        "ok": True,
        "installed": installed,
        "running": running,
        "base_url": ROUTER_BASE_URL,
        "dashboard_url": ROUTER_DASHBOARD_URL,
        "active_providers": db_summary["active_providers"],
        "provider_count": len(db_summary["active_providers"]),
        "total_connections": db_summary["total_connections"],
        "combos": db_summary["combos"],
        "freellmapi_installed": f_info["installed"],
        "freellmapi_running": f_info["running"],
        "freellmapi_model_count": f_info["model_count"],
        "freellmapi_cooldown": _freellmapi_in_cooldown(),
        "tuansu_ready": has_tuansu,
        "gemini_ready": has_gemini,
        "active_backend": active_backend,
        "ready": active_backend != "none",
        "models": models[:30],
    }


def start_router(timeout: float = 18.0) -> Dict[str, Any]:
    if is_router_running():
        st = get_status()
        st["already_running"] = True
        st["message"] = "9router (:20128) đang chạy sẵn."
        return st

    node_exe = _find_node_exe()
    cli_js = _find_9router_cli()
    if not node_exe or not cli_js:
        return {
            "ok": False,
            "running": False,
            "installed": False,
            "error": "Không tìm thấy 9router hoặc Node.js trên máy.",
        }

    cflags = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(subprocess, "DETACHED_PROCESS", 0)
    try:
        subprocess.Popen(
            [node_exe, str(cli_js), "-t", "-n", "--skip-update", "-H", ROUTER_HOST, "-p", str(ROUTER_PORT)],
            cwd=str(cli_js.parent),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=cflags,
        )
    except Exception as exc:
        return {"ok": False, "running": False, "installed": True, "error": f"Không thể bật 9router: {exc}"}

    deadline = time.time() + max(4.0, timeout)
    while time.time() < deadline:
        if is_router_running(timeout=0.8):
            st = get_status()
            st["already_running"] = False
            st["message"] = "Đã khởi động 9router tại cổng 20128."
            return st
        time.sleep(0.35)

    return {
        "ok": False,
        "running": False,
        "installed": True,
        "dashboard_url": ROUTER_DASHBOARD_URL,
        "error": "9router khởi động quá thời gian chờ tại 127.0.0.1:20128.",
    }


def open_dashboard() -> Dict[str, Any]:
    if not is_router_running():
        start_res = start_router(timeout=15.0)
        if not start_res.get("running"):
            return start_res
    try:
        webbrowser.open(ROUTER_DASHBOARD_URL)
    except Exception:
        pass
    st = get_status()
    st["message"] = f"Đã mở Dashboard 9router tại {ROUTER_DASHBOARD_URL}"
    return st


def _detect_long_script_request(messages: List[Dict[str, str]]) -> tuple[bool, Optional[float]]:
    """Detects whether the user asked for a multi-minute, detailed, or continued long script."""
    recent_user_txt = " ".join(
        str(m.get("content") or "")
        for m in messages[-4:]
        if isinstance(m, dict) and str(m.get("role") or "").lower() == "user"
    )
    low = recent_user_txt.lower()
    target_min: Optional[float] = None
    m_min = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:phút|phut|minutes?|mins?)\b", low)
    if m_min:
        try:
            target_min = float(m_min.group(1).replace(",", "."))
        except Exception:
            target_min = None

    m_words = re.search(r"(\d{3,5})\s*(?:từ|tu|chữ|chu|words?)\b", low)
    req_words = int(m_words.group(1)) if m_words else 0
    m_scenes = re.search(r"(\d{1,3})\s*(?:cảnh|canh|scenes?|phân đoạn)\b", low)
    req_scenes = int(m_scenes.group(1)) if m_scenes else 0

    long_keywords = (
        "kịch bản dài",
        "viết dài",
        "viết tiếp",
        "phần tiếp",
        "kéo dài",
        "mở rộng",
        "kể đầy đủ",
        "kể chi tiết",
        "từng cảnh chi tiết",
        "nối tiếp",
        "trọn vẹn",
        "phim dài",
        "long script",
        "full script",
    )
    is_long = bool(
        (target_min is not None and target_min >= 3.5)
        or req_words >= 500
        or req_scenes >= 8
        or any(k in low for k in long_keywords)
    )
    return is_long, target_min


_LANG_DISPLAY_MAP = {
    "vietnamese": "Tiếng Việt",
    "japanese": "Tiếng Nhật (日本語)",
    "korean": "Tiếng Hàn (한국어)",
    "english": "Tiếng Anh (English)",
    "english_uk": "Tiếng Anh - Anh (British English)",
    "chinese": "Tiếng Trung (中文)",
    "spanish": "Tiếng Tây Ban Nha (Español)",
    "french": "Tiếng Pháp (Français)",
    "german": "Tiếng Đức (Deutsch)",
    "russian": "Tiếng Nga (Русский)",
    "thai": "Tiếng Thái (ภาษาไทย)",
    "indonesian": "Tiếng Indonesia",
    "malay": "Tiếng Malaysia",
    "filipino": "Tiếng Philippines",
    "hindi": "Tiếng Hindi",
    "portuguese": "Tiếng Bồ Đào Nha",
}


def _resolve_target_script_language(language: str, messages: List[Dict[str, str]]) -> tuple[str, str]:
    """Resolves user's intended script language from explicit chat prompt or Studio dropdown."""
    recent_user_txt = " ".join(
        str(m.get("content") or "")
        for m in (messages or [])[-4:]
        if isinstance(m, dict) and str(m.get("role") or "").lower() == "user"
    )
    low = recent_user_txt.lower()

    prompt_lang_rules = (
        ("japanese", ("tiếng nhật", "tieng nhat", "bằng nhật", "japanese", "日本語")),
        ("korean", ("tiếng hàn", "tieng han", "bằng hàn", "korean", "한국어", "사연", "yadam")),
        ("english", ("tiếng anh", "tieng anh", "in english", "english script")),
        ("chinese", ("tiếng trung", "tieng trung", "tiếng hoa", "chinese", "中文")),
        ("spanish", ("tiếng tây ban nha", "spanish", "español")),
        ("french", ("tiếng pháp", "tieng phap", "french", "français")),
        ("german", ("tiếng đức", "tieng duc", "german", "deutsch")),
        ("russian", ("tiếng nga", "tieng nga", "russian", "русский")),
        ("thai", ("tiếng thái", "tieng thai", "thai")),
        ("vietnamese", ("chỉ tiếng việt", "bằng tiếng việt", "toàn tiếng việt", "tieng viet")),
    )
    for key, patterns in prompt_lang_rules:
        if any(p in low for p in patterns):
            return key, _LANG_DISPLAY_MAP[key]

    lang_norm = str(language or "").strip().lower()
    if lang_norm in _LANG_DISPLAY_MAP:
        return lang_norm, _LANG_DISPLAY_MAP[lang_norm]
    if lang_norm in ("auto", "studio", ""):
        # If user didn't pick a foreign language, follow Vietnamese unless user wrote predominantly in another language
        if any(tag in low for tag in ("nhật bản", "edo", "zen", "triết lý nhật")):
            return "japanese", _LANG_DISPLAY_MAP["japanese"]
        return "vietnamese", _LANG_DISPLAY_MAP["vietnamese"]
    return lang_norm, str(language).strip()


def _build_studio_system_prompt(
    genre: str = "auto",
    language: str = "auto",
    is_long: bool = False,
    target_minutes: Optional[float] = None,
    resolved_lang_key: str = "vietnamese",
    resolved_lang_display: str = "Tiếng Việt",
) -> str:
    g = str(genre or "auto").strip()
    l = str(language or "auto").strip()
    if resolved_lang_key == "vietnamese":
        lang_rule = (
            "- QUY TẮC NGÔN NGỮ: Người dùng đang chọn **Tiếng Việt** — viết toàn bộ Tiêu đề, Hook, mô tả hình ảnh, "
            "Lời kể và Lời thoại tự nhiên bằng Tiếng Việt."
        )
    else:
        lang_rule = (
            f"- QUY TẮC NGÔN NGỮ BẮT BUỘC THEO Ý NGƯỜI DÙNG ({resolved_lang_display}):\n"
            f"  • NGÔN NGỮ KỊCH BẢN MỤC TIÊU LÀ **{resolved_lang_display}**! TUYỆT ĐỐI KHÔNG viết phần Lời kể / Lời thoại thành toàn tiếng Việt khi người dùng đang làm video {resolved_lang_display}.\n"
            f"  • Toàn bộ **Tiêu đề phim, Hook mở đầu, Lời kể và Lời thoại nhân vật** PHẢI viết trực tiếp bằng **{resolved_lang_display}** chuẩn tự nhiên bản xứ để Tool đọc thẳng thành giọng thuyết minh / thoại phim.\n"
            f"  • Nếu người dùng KHÔNG yêu cầu '100% không kèm tiếng Việt', bạn có thể ghi nhãn `Cảnh X` + dòng `Hình ảnh minh họa` ngắn bằng tiếng Việt (hoặc thêm dòng `[Dịch ngắn: ...]` tách riêng dưới Lời kể) để người dùng dễ đọc hiểu; còn NỘI DUNG LỜI KỂ / THOẠI vẫn phải viết hoàn toàn bằng {resolved_lang_display}."
        )
    length_rule = (
        f"- QUY TẮC ĐỘ DÀI LINH HOẠT THEO Ý NGƯỜI DÙNG: "
        + (
            f"Người dùng đang yêu cầu kịch bản DÀI (mục tiêu khoảng {target_minutes:g} phút). "
            if target_minutes
            else "Khi người dùng yêu cầu kịch bản dài, nhiều cảnh, hoặc viết tiếp, "
        )
        + "TUYỆT ĐỐI KHÔNG tóm tắt lướt hay cắt ngắn giữa chừng! "
        "Hãy viết ĐẦY ĐỦ, CHI TIẾT từng cảnh (mật độ chuẩn ~135–150 từ tiếng Anh/Việt hoặc ~300–350 ký tự Nhật/Hàn mỗi phút video, tức khoảng 15–30+ cảnh cho kịch bản 5–15 phút). "
        "Luôn ghi rõ dòng 'Thời lượng ước tính: ~X phút' ngay dưới Tiêu đề để Studio tự đồng bộ thời lượng khi đẩy sang dựng phim. "
        "Nếu kịch bản quá dài (>10–12 phút), có thể trình bày sạch sẽ thành Phần 1 trọn vẹn các cảnh đầu rồi gợi ý bấm 'Viết tiếp / Kéo dài' cho phần sau; khi viết tiếp PHẢI giữ nguyên nhân vật, bối cảnh, NGÔN NGỮ ĐANG CHỌN và đánh số Cảnh nối tiếp liên tục."
        if is_long
        else "- QUY TẮC ĐỘ DÀI: Đáp ứng đúng thời lượng hoặc số cảnh người dùng yêu cầu; nếu không chỉ rõ thời lượng thì viết mạch lạc, đủ cao trào, không tóm tắt cộc lốc."
    )
    return (
        "Bạn là Biên Kịch & Trợ Lý Ý Tưởng chuyên nghiệp bên trong Storyboard AI Studio Pro.\n"
        f"- Thông tin tham khảo trên Studio: Thể loại đang chọn = '{g}', Ngôn ngữ đang chọn = '{resolved_lang_display}' (cài đặt gốc='{l}').\n"
        f"{lang_rule}\n"
        "- QUY TẮC TRÌNH BÀY SẠCH: TUYỆT ĐỐI KHÔNG dùng bảng Markdown (dấu `| ... |`), KHÔNG dùng thẻ HTML (`<br>`, `<b>`), "
        "KHÔNG dùng đường kẻ `---`, KHÔNG dùng icon số `1️⃣ 2️⃣` rườm rà.\n"
        f"{length_rule}\n"
        "- CẤU TRÚC KỊCH BẢN KHI VIẾT: Viết rõ ràng, giàu cảm xúc điện ảnh để bấm 'Đẩy & Tạo Video' là Studio tự phân tích & dựng phim ngay:\n"
        "  • Tiêu đề: (bằng ngôn ngữ kịch bản mục tiêu)\n"
        "  • Thời lượng ước tính: ~X phút\n"
        "  • Hook (3-5s đầu): (hình ảnh + câu mở đầu gây tò mò bằng ngôn ngữ mục tiêu)\n"
        "  • Cảnh 1, Cảnh 2, Cảnh 3...: (mỗi cảnh gồm Hình ảnh minh họa + Lời kể / Lời thoại viết bằng đúng ngôn ngữ mục tiêu)\n"
        "  • Kết: (cao trào / thông điệp đọng lại bằng ngôn ngữ mục tiêu)\n"
        "- Gợi ý theo thể loại: nếu 'jp_zen_story' thì ưu tiên câu chuyện chiêm nghiệm, hình minh họa nét mảnh nền trắng tối giản; "
        "nếu 'jp_edo_sleepless' / 'kr_yadam_joseon' giữ chất cổ trang sâu lắng; nếu Drama thì tập trung xung đột & cú twist cảm xúc."
    )


def _choose_model(requested: str, models: List[str], active_providers: List[Dict[str, str]]) -> str:
    req = str(requested or "").strip()
    if req and req.lower() != "auto":
        return req
    if models:
        return models[0]
    if active_providers:
        prov = active_providers[0].get("provider", "").lower()
        defaults = {
            "gemini": "gemini/gemini-2.5-flash",
            "gemini-cli": "gemini-cli/gemini-2.5-flash",
            "openai": "openai/gpt-4o-mini",
            "codex": "codex/gpt-5.4-mini",
            "qwen": "qwen/qwen3-coder-plus",
            "claude": "claude/claude-sonnet-4-5",
            "antigravity": "antigravity/gemini-2.5-flash",
        }
        if prov in defaults:
            return defaults[prov]
    return "auto"


def _chat_via_freellmapi(
    clean_msgs: List[Dict[str, str]],
    requested_model: str,
    timeout: float,
    max_tokens: int = 8192,
) -> Dict[str, Any]:
    import freellmapi_provider as fp

    cfg = fp.get_config()
    if str(cfg.get("mode") or "").lower() == "off":
        return {"ok": False, "code": "NO_PROVIDER", "error": "FreeLLMAPI đang ở chế độ tắt."}
    if not fp.is_running(cfg["base_url"], timeout=1.5):
        return {
            "ok": False,
            "code": "NO_PROVIDER",
            "error": "FreeLLMAPI (:31415) chưa sẵn sàng.",
        }
    if not str(cfg.get("api_key") or "").strip():
        return {"ok": False, "code": "NO_PROVIDER", "error": "Thiếu API Key FreeLLMAPI."}

    req_m = str(requested_model or "auto").strip()
    if req_m and req_m.lower() != "auto" and "/" not in req_m:
        candidates = [req_m]
    else:
        candidates = ["claude-sonnet-4-5", "llama-3.3-70b"]

    seen: set[str] = set()
    ordered_candidates = [m for m in candidates if not (m in seen or seen.add(m))]
    last_err = ""
    user_tail = next((m.get("content", "") for m in reversed(clean_msgs) if m.get("role") == "user"), "")
    total_budget = min(22.0, max(16.0, float(timeout) * 0.25))
    budget_deadline = time.time() + total_budget
    for cand in ordered_candidates:
        rem = budget_deadline - time.time()
        if rem < 4.0:
            break
        per_try_timeout = min(18.0, rem)
        try:
            raw_reply = fp.generate_chat_completion(
                clean_msgs,
                model=cand,
                temperature=0.68,
                timeout=per_try_timeout,
                max_tokens=max_tokens,
            )
            cleaned = _clean_assistant_reply(raw_reply)
            if cleaned and _is_valid_assistant_reply(cleaned, user_tail):
                _clear_freellmapi_cooldown()
                return {
                    "ok": True,
                    "reply": cleaned,
                    "backend": "freellmapi",
                    "model": cand,
                    "provider_count": 1,
                }
            last_err = f"Model {cand} trả về phản hồi nhiễu/bộ lọc ({cleaned[:60]})."
        except Exception as exc:
            last_err = str(exc)
            if "timed out" in last_err.lower() or "timeout" in last_err.lower():
                _mark_freellmapi_cooldown(180.0)
                break
            if "429" in last_err:
                _mark_freellmapi_cooldown(180.0)
            continue

    _mark_freellmapi_cooldown(180.0)
    return {
        "ok": False,
        "error": f"Các model miễn phí trên FreeLLMAPI (:31415) đang bận hoặc giới hạn tốc độ. Chi tiết: {last_err[:180]}",
    }


def _chat_via_tuansuapi(
    clean_msgs: List[Dict[str, str]],
    requested_model: str = "",
    timeout: float = 90.0,
    max_tokens: int = 8192,
) -> Dict[str, Any]:
    try:
        import tuansuapi_provider as tp
        cfg = tp.get_gateway_config()
        if str(cfg.get("enabled") or "1") != "1" or not str(cfg.get("api_key") or "").strip():
            return {"ok": False, "error": "Chưa cấu hình Tuấn Stor API Key."}
        req = str(requested_model or "").strip()
        model_to_use = req if (req and req.lower() not in ("auto",) and ("gemini" in req.lower() or "gpt" in req.lower())) else None
        raw_reply = tp.generate_chat_completion(
            clean_msgs,
            model=model_to_use,
            temperature=0.68,
            timeout=max(60.0, float(timeout)),
            max_tokens=max_tokens,
        )
        cleaned = _clean_assistant_reply(raw_reply)
        if cleaned:
            return {
                "ok": True,
                "reply": cleaned,
                "backend": "tuansuapi",
                "model": model_to_use or cfg.get("text_model") or tp.DEFAULT_TEXT_MODEL,
                "provider_count": 1,
            }
        return {"ok": False, "error": "Tuấn Stor API trả về nội dung rỗng."}
    except Exception as exc:
        return {"ok": False, "error": f"Lỗi Tuấn Stor API: {str(exc)[:180]}"}


def _chat_via_gemini_pool(
    clean_msgs: List[Dict[str, str]],
    requested_model: str = "",
    max_tokens: int = 8192,
) -> Dict[str, Any]:
    try:
        import resilient_gemini
        keys = resilient_gemini.load_api_keys()
        if not keys:
            return {"ok": False, "error": "Chưa cấu hình GEMINI_API_KEY trong studio/.env."}
        sys_txt = ""
        convo_parts: List[str] = []
        for m in clean_msgs:
            role = m.get("role", "user")
            content = m.get("content", "")
            if role == "system":
                sys_txt = content
            elif role == "assistant":
                convo_parts.append(f"Trợ lý:\n{content}")
            else:
                convo_parts.append(f"Người dùng:\n{content}")
        prompt_text = (f"{sys_txt}\n\n" if sys_txt else "") + "\n\n".join(convo_parts)
        req = str(requested_model or "").strip()
        gem_model = req if (req.startswith("gemini-") and "flash-3.8" not in req) else "gemini-2.5-flash"
        resp = resilient_gemini.ResilientClient().models.generate_content(
            model=gem_model,
            contents=prompt_text,
            config={"max_output_tokens": int(max_tokens)},
        )
        raw_reply = resp.text if hasattr(resp, "text") else str(resp)
        cleaned = _clean_assistant_reply(raw_reply)
        if cleaned:
            return {
                "ok": True,
                "reply": cleaned,
                "backend": "gemini",
                "model": gem_model,
                "provider_count": len(keys),
            }
        return {"ok": False, "error": "Gemini API trả về nội dung rỗng."}
    except Exception as exc:
        return {"ok": False, "error": f"Lỗi Gemini API: {str(exc)[:180]}"}


def _studio_ai_failover(
    clean_msgs: List[Dict[str, str]],
    requested_model: str,
    timeout: float,
    max_tokens: int = 8192,
) -> Dict[str, Any]:
    """Fail-safe chain: Tuấn Stor Gateway -> Gemini Multi-Key Pool -> fast FreeLLMAPI if not cooled down."""
    errors: List[str] = []
    req = str(requested_model or "auto").strip()
    is_explicit_gemini_pool = req in ("gemini-2.5-flash", "gemini-2.5-pro")

    if is_explicit_gemini_pool:
        g_res = _chat_via_gemini_pool(clean_msgs, req, max_tokens=max_tokens)
        if g_res.get("ok"):
            return g_res
        errors.append(g_res.get("error") or "Gemini failed")

    t_res = _chat_via_tuansuapi(clean_msgs, req, timeout=timeout, max_tokens=max_tokens)
    if t_res.get("ok"):
        return t_res
    if t_res.get("error"):
        errors.append(t_res["error"])

    if not is_explicit_gemini_pool:
        g_res = _chat_via_gemini_pool(clean_msgs, req, max_tokens=max_tokens)
        if g_res.get("ok"):
            return g_res
        if g_res.get("error"):
            errors.append(g_res["error"])

    return {"ok": False, "error": " | ".join(errors[:2])}


def chat_completion(
    messages: List[Dict[str, str]],
    model: str = "auto",
    genre: str = "auto",
    language: str = "auto",
    auto_start: bool = True,
    timeout: float = 150.0,
) -> Dict[str, Any]:
    if not isinstance(messages, list) or not messages:
        return {"ok": False, "error": "Tin nhắn trống."}

    is_long, target_minutes = _detect_long_script_request(messages)
    resolved_lang_key, resolved_lang_display = _resolve_target_script_language(language, messages)
    target_max_tokens = 8192 if is_long else 4096
    effective_timeout = max(float(timeout), 120.0 if is_long else 75.0)

    clean_msgs: List[Dict[str, str]] = [
        {
            "role": "system",
            "content": _build_studio_system_prompt(
                genre=genre,
                language=language,
                is_long=is_long,
                target_minutes=target_minutes,
                resolved_lang_key=resolved_lang_key,
                resolved_lang_display=resolved_lang_display,
            ),
        }
    ]
    total_chars = len(clean_msgs[0]["content"])
    history_slice: List[Dict[str, str]] = []
    for item in reversed(messages[-24:]):
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "user").strip().lower()
        content = str(item.get("content") or "").strip()[:24000]
        if role in ("user", "assistant") and content:
            if history_slice and total_chars + len(content) > 72000:
                break
            history_slice.append({"role": role, "content": content})
            total_chars += len(content)
    clean_msgs.extend(reversed(history_slice))

    req_model = str(model or "auto").strip()
    db_summary, api_key = _read_db_summary_and_key()
    has_router_providers = bool(db_summary["active_providers"] or db_summary["combos"])

    if has_router_providers and not is_router_running() and auto_start:
        start_router(timeout=15.0)

    models = fetch_models() if is_router_running() else []
    use_9router = is_router_running() and (has_router_providers or bool(models))

    # 1. If 9router has real logged-in providers, try it first
    router_err = ""
    if use_9router:
        chosen_model = _choose_model(req_model, models, db_summary["active_providers"])
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        payload = {
            "model": chosen_model,
            "messages": clean_msgs,
            "temperature": 0.7,
            "max_tokens": target_max_tokens,
            "stream": False,
        }
        try:
            resp = requests.post(
                f"{ROUTER_BASE_URL}/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=min(130.0, effective_timeout),
            )
            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices") or []
                reply = ""
                if choices and isinstance(choices[0], dict):
                    reply = str((choices[0].get("message") or {}).get("content") or "").strip()
                reply = _clean_assistant_reply(reply)
                if reply:
                    return {
                        "ok": True,
                        "reply": reply,
                        "backend": "9router",
                        "model": data.get("model") or chosen_model,
                        "provider_count": len(db_summary["active_providers"]),
                        "is_long": is_long,
                    }
            router_err = f"9router HTTP {resp.status_code}: {resp.text[:160]}"
        except Exception as exc:
            router_err = f"Lỗi 9router: {exc}"

    # 2. If user specifically requested a built-in Studio AI model (Tuấn Stor / Gemini), route directly
    is_studio_model = req_model in ("gemini-flash-3.8-fast", "gemini-2.5-flash", "gemini-2.5-pro")
    free_err = ""
    if (not is_studio_model) and (not _freellmapi_in_cooldown()):
        try:
            f_res = _chat_via_freellmapi(clean_msgs, req_model, effective_timeout, max_tokens=target_max_tokens)
            if f_res.get("ok"):
                f_res["is_long"] = is_long
                return f_res
            free_err = str(f_res.get("error") or "")
        except Exception as exc:
            _mark_freellmapi_cooldown(180.0)
            free_err = str(exc)

    # 3. Seamless automatic failover to Tuấn Stor Gateway -> Gemini API Pool (never leaves user stuck on 429/timeout!)
    st_res = _studio_ai_failover(clean_msgs, req_model, effective_timeout, max_tokens=target_max_tokens)
    if st_res.get("ok"):
        st_res["is_long"] = is_long
        return st_res

    combined_err = " | ".join(x for x in (router_err, free_err, st_res.get("error")) if x)
    return {
        "ok": False,
        "code": "NO_PROVIDER",
        "dashboard_url": ROUTER_DASHBOARD_URL,
        "error": combined_err or "Không có nguồn AI khả dụng. Hãy kiểm tra FreeLLMAPI, 9router hoặc API Key trong Cài đặt.",
    }
