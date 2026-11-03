"""3rd-Party AI Gateway Integration (Tuấn Stor - https://tuansuapi.store/v1).

Provides high-speed, high-quota failover for:
1. LLM Screenplay, Story Bible, Narration and Scene Planning via gemini-flash-3.8-fast.
2. AI Image Generation via gemini-3.1-flash-image-preview or gpt-image-2.
3. Automatic sync with V2 configuration (D:\\YOUTUBE_SEO_PRO_V2\\.env).
"""
from __future__ import annotations

import os
import json
import base64
import io
import time
import uuid
import requests
from pathlib import Path
from PIL import Image, ImageOps

DEFAULT_BASE_URL = "https://tuansuapi.store/v1"
DEFAULT_TEXT_MODEL = "gemini-flash-3.8-fast"
DEFAULT_IMAGE_MODEL = "gemini-3.1-flash-image-preview"

STUDIO_ENV = Path(__file__).resolve().parent / ".env"
V2_ENV = Path(r"D:\YOUTUBE_SEO_PRO_V2\.env")


def get_gateway_config() -> dict[str, str]:
    """Retrieves 3rd-party gateway settings, checking Studio .env then V2 .env."""
    config = {
        "base_url": DEFAULT_BASE_URL,
        "api_key": "",
        "text_model": DEFAULT_TEXT_MODEL,
        "image_model": DEFAULT_IMAGE_MODEL,
        "enabled": "1",
        "source": "default"
    }

    # 1. Check Studio .env first
    if STUDIO_ENV.is_file():
        try:
            for line in STUDIO_ENV.read_text(encoding="utf-8-sig", errors="replace").splitlines():
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip().strip("'").strip('"')
                    if k in ("TUANSU_BASE_URL", "AI_TEAM_BASE_URL", "GEMINI_BASE_URL"):
                        config["base_url"] = v
                    elif k in ("TUANSU_API_KEY", "MODELAPI_API_KEY", "CLAUDE_GATEWAY_API_KEY"):
                        config["api_key"] = v
                        config["source"] = "studio"
                    elif k in ("TUANSU_TEXT_MODEL", "GEMINI_MODEL", "MODELAPI_MODEL"):
                        config["text_model"] = v
                    elif k in ("TUANSU_IMAGE_MODEL", "GEMINI_IMAGE_MODEL", "AI_TEAM_IMAGE_MODEL"):
                        config["image_model"] = v
                    elif k == "TUANSU_ENABLED":
                        config["enabled"] = v
        except Exception:
            pass

    # 2. If no key in Studio, inherit seamlessly from V2 .env
    if not config["api_key"] and V2_ENV.is_file():
        try:
            for line in V2_ENV.read_text(encoding="utf-8-sig", errors="replace").splitlines():
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip().strip("'").strip('"')
                    if k in ("GEMINI_BASE_URL", "AI_TEAM_BASE_URL") and not config["base_url"]:
                        config["base_url"] = v
                    elif k == "GEMINI_API_KEY" and not config["api_key"]:
                        config["api_key"] = v
                        config["source"] = "v2_inherited"
                    elif k == "GEMINI_IMAGE_MODEL" and v:
                        config["image_model"] = v
                    elif k == "GEMINI_MODEL" and v:
                        config["text_model"] = v
        except Exception:
            pass

    # Ensure clean base URL without trailing slash
    config["base_url"] = config["base_url"].rstrip("/")
    return config


def save_gateway_config(api_key: str, base_url: str = DEFAULT_BASE_URL, text_model: str = DEFAULT_TEXT_MODEL, image_model: str = DEFAULT_IMAGE_MODEL, enabled: bool = True) -> bool:
    """Saves 3rd-party gateway configuration to Studio .env."""
    lines = []
    if STUDIO_ENV.is_file():
        for l in STUDIO_ENV.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            k = l.split("=", 1)[0].strip() if "=" in l else ""
            if k not in ("TUANSU_BASE_URL", "TUANSU_API_KEY", "TUANSU_TEXT_MODEL", "TUANSU_IMAGE_MODEL", "TUANSU_ENABLED"):
                lines.append(l)

    lines.append(f"TUANSU_BASE_URL={base_url.strip().rstrip('/')}")
    lines.append(f"TUANSU_API_KEY={api_key.strip()}")
    lines.append(f"TUANSU_TEXT_MODEL={text_model.strip()}")
    lines.append(f"TUANSU_IMAGE_MODEL={image_model.strip()}")
    lines.append(f"TUANSU_ENABLED={'1' if enabled else '0'}")

    STUDIO_ENV.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return True


def test_gateway_connection() -> dict:
    """Verifies gateway availability and returns model test response."""
    cfg = get_gateway_config()
    if not cfg["api_key"]:
        return {"ok": False, "error": "Chưa có API Key bên thứ ba (Tuấn Stor)."}

    url = f"{cfg['base_url']}/chat/completions"
    headers = {
        "Authorization": f"Bearer {cfg['api_key']}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": cfg["text_model"] or DEFAULT_TEXT_MODEL,
        "messages": [
            {"role": "user", "content": "Ping test: Reply with OK"}
        ]
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=25)
        if resp.status_code == 200:
            data = resp.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return {
                "ok": True,
                "base_url": cfg["base_url"],
                "model": cfg["text_model"],
                "source": cfg["source"],
                "response": content[:120]
            }
        else:
            return {
                "ok": False,
                "error": f"Gateway trả về mã lỗi HTTP {resp.status_code}: {resp.text[:150]}"
            }
    except Exception as exc:
        return {"ok": False, "error": f"Không thể kết nối gateway: {exc}"}


def generate_chat_completion(messages: list[dict], model: str | None = None, temperature: float = 0.7, timeout: float = 60.0) -> str:
    """Generates text / JSON content using 3rd-party gateway."""
    cfg = get_gateway_config()
    if not cfg["api_key"]:
        raise RuntimeError("Tuấn Stor API Key is missing")

    url = f"{cfg['base_url']}/chat/completions"
    headers = {
        "Authorization": f"Bearer {cfg['api_key']}",
        "Content-Type": "application/json"
    }
    active_model = model or cfg["text_model"] or DEFAULT_TEXT_MODEL
    payload = {
        "model": active_model,
        "messages": messages,
        "temperature": float(temperature)
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    if resp.status_code != 200:
        raise RuntimeError(f"Gateway HTTP {resp.status_code}: {resp.text[:200]}")

    data = resp.json()
    choices = data.get("choices", [])
    if not choices:
        raise RuntimeError("Gateway did not return any choices")
    return choices[0].get("message", {}).get("content", "")


def generate_gateway_image(prompt: str, output_path: str | Path, model: str | None = None, timeout: float = 110.0) -> str:
    """Generates an image via 3rd-party gateway (OpenAI images format)."""
    cfg = get_gateway_config()
    if not cfg["api_key"]:
        raise RuntimeError("Tuấn Stor API Key is missing for image generation")

    url = f"{cfg['base_url']}/images/generations"
    headers = {
        "Authorization": f"Bearer {cfg['api_key']}",
        "Content-Type": "application/json"
    }
    active_model = model or cfg["image_model"] or DEFAULT_IMAGE_MODEL
    payload = {
        "model": active_model,
        "prompt": prompt.strip(),
        "n": 1,
        "size": "1024x1024"
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    if resp.status_code != 200:
        raise RuntimeError(f"Gateway Image HTTP {resp.status_code}: {resp.text[:200]}")

    data = resp.json()
    entries = data.get("data", [])
    if not entries:
        raise RuntimeError("No image returned from gateway")

    item = entries[0]
    binary = None
    if isinstance(item.get("b64_json"), str):
        binary = base64.b64decode(item["b64_json"])
    elif isinstance(item.get("url"), str):
        img_resp = requests.get(item["url"], timeout=30)
        if img_resp.status_code == 200:
            binary = img_resp.content

    if not binary:
        raise RuntimeError("Could not decode image from gateway response")

    target = Path(output_path).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(io.BytesIO(binary)) as img:
        img.load()
        rgb = img.convert("RGB")
        if abs(rgb.width / rgb.height - 16 / 9) > 0.01:
            rgb = ImageOps.pad(rgb, (1536, 864), color="white", method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        temp = target.with_name(f"{target.stem}.{uuid.uuid4().hex}.png")
        rgb.save(temp, format="PNG")
        temp.replace(target)

    return str(target)
