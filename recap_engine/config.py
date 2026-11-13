"""
Configuration module for Standalone Movie Recap Engine.
Completely isolated from Storyboard AI.
"""

from pathlib import Path
import os
import re
import json
from typing import List, Optional

RECAP_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = RECAP_ROOT.parent

CONFIG_FILE = RECAP_ROOT / "recap_config.json"
EXAMPLE_CONFIG_FILE = RECAP_ROOT / "recap_config.example.json"
DEFAULT_EXPORT_DIR = PROJECT_ROOT / "recap_exports"
STUDIO_ENV_FILE = PROJECT_ROOT / "studio" / ".env"

DEFAULT_CONFIG = {
    "gemini_keys": [],
    "model_name": "gemini-3.5-flash",
    "fallback_models": ["gemini-flash-lite-latest", "gemini-3.8-flash"],
    "voice_engine": "edge_tts",  # "gemini_tts" or "edge_tts"
    "gemini_voice": "Fenrir",
    "edge_voice": "vi-VN-NamMinhNeural",
    "voice_speed": 1.15,
    "whisper_mode": "local",
    "export_dir": str(DEFAULT_EXPORT_DIR),
    "anti_content_id": {
        "max_clip_seconds": 4.0,
        "ken_burns_zoom": True,
        "speed_factor": 1.04,
        "selective_flip": False,
        "film_grain": True,
        "mute_orig_bgm": True,
        "auto_duck_db": -18
    }
}


def _is_valid_key(k: str) -> bool:
    if not k:
        return False
    clean = re.sub(r"[^\x20-\x7E]", "", k).strip()
    return len(clean) >= 25 and (clean.startswith("AIza") or clean.startswith("AQ.") or "." in clean)


def load_keys_from_env() -> List[str]:
    """Helper to discover clean API keys from existing .env if available."""
    keys = []
    # Check current environment first
    for var in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GEMINI_API_KEYS"):
        val = os.environ.get(var, "").strip()
        if val:
            for k in val.split(","):
                clean_k = re.sub(r"[^\x20-\x7E]", "", k).strip()
                if _is_valid_key(clean_k) and clean_k not in keys:
                    keys.append(clean_k)

    # Check studio .env as well
    if STUDIO_ENV_FILE.is_file():
        try:
            content = STUDIO_ENV_FILE.read_text(encoding="utf-8", errors="replace")
            for line in content.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k_name, k_val = line.split("=", 1)
                    k_name = k_name.strip()
                    if k_name in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GEMINI_API_KEYS"):
                        for item in k_val.strip("\"' ").split(","):
                            clean_k = re.sub(r"[^\x20-\x7E]", "", item).strip()
                            if _is_valid_key(clean_k) and clean_k not in keys:
                                keys.append(clean_k)
        except Exception:
            pass
    return keys


def load_config() -> dict:
    """Load config from recap_config.json, populated with defaults and discovered keys."""
    config = dict(DEFAULT_CONFIG)
    if not CONFIG_FILE.is_file() and EXAMPLE_CONFIG_FILE.is_file():
        try:
            data = json.loads(EXAMPLE_CONFIG_FILE.read_text(encoding="utf-8"))
            config.update(data)
        except Exception:
            pass

    if CONFIG_FILE.is_file():
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            config.update(data)
        except Exception:
            pass

    # Ensure keys are populated
    if not config.get("gemini_keys"):
        discovered = load_keys_from_env()
        if discovered:
            config["gemini_keys"] = discovered
            save_config(config)

    # Ensure export directory exists
    export_path = Path(config["export_dir"])
    export_path.mkdir(parents=True, exist_ok=True)

    return config


def save_config(config: dict) -> None:
    """Save config to recap_config.json."""
    CONFIG_FILE.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")


class KeyRotator:
    """Thread-safe key rotator for Google Gemini API."""
    def __init__(self, keys: List[str]):
        import threading
        self.keys = [re.sub(r"[^\x20-\x7E]", "", k).strip() for k in keys if k.strip()]
        self.index = 0
        self._lock = threading.Lock()

    def get_current_key(self) -> Optional[str]:
        with self._lock:
            if not self.keys:
                return None
            return self.keys[self.index % len(self.keys)]

    def rotate_next(self) -> Optional[str]:
        with self._lock:
            if not self.keys:
                return None
            self.index = (self.index + 1) % len(self.keys)
            return self.keys[self.index % len(self.keys)]

    def get_client(self, timeout_sec: float = 35.0):
        """Returns a google-genai Client initialized with current key and http timeout."""
        key = self.get_current_key()
        if not key:
            raise ValueError("Chưa cấu hình Gemini API Key nào trong recap_config.json!")
        from google import genai
        from google.genai import types
        timeout_ms = int(timeout_sec * 1000)
        return genai.Client(
            api_key=key,
            http_options=types.HttpOptions(
                timeout=timeout_ms,
                retry_options=types.HttpRetryOptions(attempts=1)
            )
        )


_SHARED_ROTATOR: Optional[KeyRotator] = None

def get_shared_rotator() -> KeyRotator:
    global _SHARED_ROTATOR
    if _SHARED_ROTATOR is None:
        cfg = load_config()
        keys = cfg.get("gemini_keys", [])
        _SHARED_ROTATOR = KeyRotator(keys)
    return _SHARED_ROTATOR
