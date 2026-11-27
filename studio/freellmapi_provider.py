"""Local FreeLLMAPI Proxy Integration (https://github.com/tashfeenahmed/freellmapi).

Provides an OpenAI-compatible local AI router (default http://127.0.0.1:31415/v1)
that aggregates free-tier providers (Groq, Google AI Studio, Cerebras, OpenRouter,
NVIDIA NIM, Mistral, keyless models) with automatic 429 failover.
"""
from __future__ import annotations

import os
import re
import sqlite3
import subprocess
import time
import urllib.parse
from pathlib import Path
import requests

DEFAULT_BASE_URL = "http://127.0.0.1:31415/v1"
DEFAULT_MODEL = "auto"
DEFAULT_MODE = "fallback"  # "fallback" | "primary" | "off"

STUDIO_ENV = Path(__file__).resolve().parent / ".env"

_EXE_CANDIDATES = (
    Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "freellmapi-desktop" / "FreeLLMAPI.exe",
    Path.home() / "AppData" / "Local" / "Programs" / "freellmapi-desktop" / "FreeLLMAPI.exe",
)

_DB_CANDIDATES = (
    Path(os.environ.get("APPDATA", "")) / "FreeLLMAPI" / "freeapi.db",
    Path.home() / "AppData" / "Roaming" / "FreeLLMAPI" / "freeapi.db",
)

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)


def find_executable() -> Path | None:
    """Return path to FreeLLMAPI Desktop executable if installed."""
    for candidate in _EXE_CANDIDATES:
        try:
            if candidate.is_file():
                return candidate
        except OSError:
            pass
    return None


def _read_local_unified_key() -> str:
    """Read auto-generated unified_api_key from local FreeLLMAPI SQLite DB (read-only)."""
    for db_path in _DB_CANDIDATES:
        try:
            if not db_path.is_file():
                continue
            uri = f"file:{db_path.as_posix()}?mode=ro"
            conn = sqlite3.connect(uri, uri=True, timeout=1.5)
            try:
                row = conn.execute(
                    "SELECT value FROM settings WHERE key = 'unified_api_key'"
                ).fetchone()
                if row and isinstance(row[0], str) and row[0].strip():
                    return row[0].strip()
            finally:
                conn.close()
        except Exception:
            pass
    return ""


def _read_local_port() -> int | None:
    """Read configured desktop port from %APPDATA%\\FreeLLMAPI\\config.json if present."""
    import json
    cfg_path = Path(os.environ.get("APPDATA", "")) / "FreeLLMAPI" / "config.json"
    if not cfg_path.is_file():
        cfg_path = Path.home() / "AppData" / "Roaming" / "FreeLLMAPI" / "config.json"
    try:
        if cfg_path.is_file():
            data = json.loads(cfg_path.read_text(encoding="utf-8"))
            port = int(data.get("port") or 0)
            if 1024 <= port <= 65535:
                return port
    except Exception:
        pass
    return None


def get_config() -> dict[str, str]:
    """Retrieve FreeLLMAPI settings from Studio .env with local desktop auto-discovery."""
    detected_port = _read_local_port()
    default_url = f"http://127.0.0.1:{detected_port}/v1" if detected_port else DEFAULT_BASE_URL

    config = {
        "base_url": default_url,
        "api_key": "",
        "model": DEFAULT_MODEL,
        "mode": DEFAULT_MODE,
        "source": "auto_local",
    }

    if STUDIO_ENV.is_file():
        try:
            for line in STUDIO_ENV.read_text(encoding="utf-8-sig", errors="replace").splitlines():
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip().strip("'").strip('"')
                    if k == "FREELLMAPI_BASE_URL" and v:
                        config["base_url"] = v
                    elif k == "FREELLMAPI_API_KEY" and v:
                        config["api_key"] = v
                        config["source"] = "studio_env"
                    elif k == "FREELLMAPI_MODEL" and v:
                        config["model"] = v
                    elif k == "FREELLMAPI_MODE" and v.lower() in ("off", "fallback", "primary"):
                        config["mode"] = v.lower()
        except Exception:
            pass

    if not config["api_key"]:
        local_key = _read_local_unified_key()
        if local_key:
            config["api_key"] = local_key
            config["source"] = "local_db"

    config["base_url"] = config["base_url"].rstrip("/")
    return config


def save_config(
    api_key: str = "",
    base_url: str = DEFAULT_BASE_URL,
    model: str = DEFAULT_MODEL,
    mode: str = DEFAULT_MODE,
) -> bool:
    """Save FreeLLMAPI configuration to Studio .env without touching other keys."""
    clean_mode = str(mode or DEFAULT_MODE).strip().lower()
    if clean_mode not in ("off", "fallback", "primary"):
        clean_mode = DEFAULT_MODE

    lines: list[str] = []
    managed = {"FREELLMAPI_BASE_URL", "FREELLMAPI_API_KEY", "FREELLMAPI_MODEL", "FREELLMAPI_MODE"}
    if STUDIO_ENV.is_file():
        for raw in STUDIO_ENV.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            k = raw.split("=", 1)[0].strip() if "=" in raw else ""
            if k not in managed:
                lines.append(raw)

    clean_url = (base_url or DEFAULT_BASE_URL).strip().rstrip("/")
    if not clean_url.endswith("/v1") and not clean_url.endswith("/v1/"):
        # Keep custom paths if already explicit, only append /v1 for bare host:port
        parsed = urllib.parse.urlsplit(clean_url)
        if parsed.path in ("", "/"):
            clean_url = clean_url + "/v1"

    lines.append(f"FREELLMAPI_BASE_URL={clean_url}")
    if api_key.strip():
        lines.append(f"FREELLMAPI_API_KEY={api_key.strip()}")
    lines.append(f"FREELLMAPI_MODEL={(model or DEFAULT_MODEL).strip()}")
    lines.append(f"FREELLMAPI_MODE={clean_mode}")

    STUDIO_ENV.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return True


def dashboard_url_for(base_url: str | None = None) -> str:
    """Return the root dashboard URL for a FreeLLMAPI /v1 base_url."""
    url = (base_url or get_config()["base_url"]).rstrip("/")
    if url.endswith("/v1"):
        url = url[:-3]
    return url


def is_running(base_url: str | None = None, timeout: float = 1.5) -> bool:
    """Check whether the FreeLLMAPI server responds on its health/root URL."""
    root = dashboard_url_for(base_url)
    try:
        resp = requests.get(f"{root}/health", timeout=timeout)
        return resp.status_code < 500
    except Exception:
        return False


def start_desktop_app() -> dict:
    """Launch FreeLLMAPI Desktop detached so it keeps running in the system tray."""
    cfg = get_config()
    if is_running(cfg["base_url"]):
        return {"ok": True, "running": True, "already_running": True, "dashboard_url": dashboard_url_for(cfg["base_url"])}

    exe = find_executable()
    if not exe:
        return {"ok": False, "running": False, "error": "Chưa cài đặt FreeLLMAPI Desktop trên máy."}

    flags = (
        getattr(subprocess, "DETACHED_PROCESS", 0x00000008)
        | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)
        | getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
    )
    subprocess.Popen(
        [str(exe)],
        cwd=str(exe.parent),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        creationflags=flags,
        close_fds=True,
    )

    deadline = time.monotonic() + 10.0
    while time.monotonic() < deadline:
        if is_running(cfg["base_url"], timeout=1.0):
            return {"ok": True, "running": True, "started": True, "dashboard_url": dashboard_url_for(cfg["base_url"])}
        time.sleep(0.4)

    return {"ok": False, "running": False, "error": "Đã mở FreeLLMAPI nhưng cổng cục bộ chưa phản hồi kịp."}


def ensure_running() -> bool:
    """Ensure local FreeLLMAPI is running if configured on localhost."""
    cfg = get_config()
    if cfg.get("mode") == "off":
        return False
    if is_running(cfg["base_url"]):
        return True
    parsed = urllib.parse.urlsplit(cfg["base_url"])
    if parsed.hostname in ("127.0.0.1", "localhost") and find_executable():
        res = start_desktop_app()
        return bool(res.get("running"))
    return False


def test_connection(auto_start: bool = False, ping_chat: bool = True) -> dict:
    """Verify FreeLLMAPI proxy connectivity, authentication, and model availability."""
    cfg = get_config()
    installed = find_executable() is not None
    running = is_running(cfg["base_url"])

    if not running and auto_start and installed:
        start_res = start_desktop_app()
        running = bool(start_res.get("running"))

    if not running:
        return {
            "ok": False,
            "installed": installed,
            "running": False,
            "error": "FreeLLMAPI chưa chạy. Bấm 'Khởi Động' để bật proxy cục bộ."
            if installed
            else "Chưa cài đặt FreeLLMAPI.",
        }

    if not cfg.get("api_key"):
        return {
            "ok": False,
            "installed": installed,
            "running": True,
            "error": "Chưa có Unified API Key (freellmapi-...). Mở Bảng Keys để sao chép khóa.",
        }

    headers = {
        "Authorization": f"Bearer {cfg['api_key']}",
        "Content-Type": "application/json",
    }

    model_count = 0
    try:
        m_resp = requests.get(f"{cfg['base_url']}/models", headers=headers, timeout=5)
        if m_resp.status_code == 401:
            return {
                "ok": False,
                "installed": installed,
                "running": True,
                "error": "Unified API Key không hợp lệ (HTTP 401).",
            }
        if m_resp.status_code == 200:
            model_count = len(m_resp.json().get("data", []))
    except Exception as exc:
        return {"ok": False, "installed": installed, "running": True, "error": f"Lỗi kết nối /v1/models: {exc}"}

    if not ping_chat:
        return {
            "ok": True,
            "installed": installed,
            "running": True,
            "model_count": model_count,
            "base_url": cfg["base_url"],
            "model": cfg["model"],
        }

    try:
        payload = {
            "model": cfg["model"] or DEFAULT_MODEL,
            "messages": [{"role": "user", "content": "Reply with exactly: OK"}],
            "max_tokens": 16,
        }
        c_resp = requests.post(
            f"{cfg['base_url']}/chat/completions",
            headers=headers,
            json=payload,
            timeout=25,
        )
        if c_resp.status_code == 200:
            content = (
                c_resp.json()
                .get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
            return {
                "ok": True,
                "installed": installed,
                "running": True,
                "model_count": model_count,
                "base_url": cfg["base_url"],
                "model": cfg["model"],
                "response": _THINK_RE.sub("", content).strip()[:120],
            }
        return {
            "ok": False,
            "installed": installed,
            "running": True,
            "model_count": model_count,
            "error": f"FreeLLMAPI trả về HTTP {c_resp.status_code}: {c_resp.text[:160]}",
        }
    except Exception as exc:
        return {
            "ok": False,
            "installed": installed,
            "running": True,
            "model_count": model_count,
            "error": f"Không thể gọi /chat/completions: {exc}",
        }


def generate_chat_completion(
    messages: list[dict],
    model: str | None = None,
    temperature: float = 0.7,
    timeout: float = 90.0,
    max_tokens: int | None = None,
) -> str:
    """Generate text/JSON completion via local FreeLLMAPI OpenAI-compatible proxy."""
    cfg = get_config()
    if cfg.get("mode") == "off":
        raise RuntimeError("FreeLLMAPI is disabled")
    if not cfg.get("api_key"):
        raise RuntimeError("FreeLLMAPI unified API key is missing")
    if not ensure_running():
        raise RuntimeError("FreeLLMAPI local proxy is not running")

    url = f"{cfg['base_url']}/chat/completions"
    headers = {
        "Authorization": f"Bearer {cfg['api_key']}",
        "Content-Type": "application/json",
    }
    active_model = (model or cfg.get("model") or DEFAULT_MODEL).strip()
    payload: dict = {
        "model": active_model,
        "messages": messages,
        "temperature": float(temperature),
    }
    if max_tokens and int(max_tokens) > 0:
        payload["max_tokens"] = int(max_tokens)

    resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    if resp.status_code == 400 and "max_tokens" in payload:
        payload_retry = dict(payload)
        payload_retry.pop("max_tokens", None)
        resp = requests.post(url, headers=headers, json=payload_retry, timeout=timeout)
    if resp.status_code != 200:
        raise RuntimeError(f"FreeLLMAPI HTTP {resp.status_code}: {resp.text[:220]}")

    data = resp.json()
    choices = data.get("choices", [])
    if not choices:
        raise RuntimeError("FreeLLMAPI did not return any choices")

    raw_content = choices[0].get("message", {}).get("content") or ""
    cleaned = _THINK_RE.sub("", raw_content).strip()
    if not cleaned:
        raise RuntimeError("FreeLLMAPI returned empty response content")
    return cleaned
