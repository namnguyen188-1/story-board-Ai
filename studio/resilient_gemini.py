"""Bounded resilience and Multi-API-Key Failover pool for Gemini requests.
Supports:
1. Multi-API-Key pool with automatic failover on HTTP 429 / Quota Exceeded.
2. Cross-model fallback (e.g., gemini-3.8-flash -> gemini-3.6-flash -> gemini-2.5-flash -> gemini-3.5-flash-lite)
   when all keys exhaust quota for the primary model.
3. Cooldown tracking and round-robin key management.
4. Bounded exponential backoff retry for transient network / 503 capacity errors.
5. Strict privacy: never logs full API keys or sensitive prompts.
"""
from __future__ import annotations

import os
import sys
import re
import time
import random
import socket
from pathlib import Path

# Enforce a 75-second hard ceiling on all underlying TCP/HTTP sockets so calls cannot hang indefinitely
try:
    socket.setdefaulttimeout(75.0)
except Exception:
    pass

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

FALLBACKS = {
    "gemini-3.5-flash": ("gemini-flash-lite-latest", "gemini-3.5-flash-lite", "gemini-3.8-flash"),
    "gemini-3.5-flash": ("gemini-flash-lite-latest", "gemini-3.8-flash"),
    "gemini-3.8-flash": ("gemini-3.5-flash", "gemini-flash-lite-latest"),
    "gemini-flash-lite-latest": ("gemini-3.5-flash", "gemini-3.8-flash"),
    "gemini-3.6-flash": ("gemini-3.5-flash", "gemini-flash-lite-latest", "gemini-3.8-flash"),
    "gemini-3.7-flash": ("gemini-3.5-flash", "gemini-flash-lite-latest", "gemini-3.8-flash"),
    "gemini-2.5-flash": ("gemini-3.5-flash", "gemini-flash-lite-latest", "gemini-3.8-flash"),
    "gemini-3.5-flash-lite": ("gemini-3.5-flash", "gemini-flash-lite-latest", "gemini-3.8-flash"),
    "gemini-3.1-flash-lite": ("gemini-3.5-flash", "gemini-flash-lite-latest", "gemini-3.8-flash"),
    "gemini-3.1-flash-lite-preview": ("gemini-3.5-flash", "gemini-flash-lite-latest", "gemini-3.8-flash"),
    "gemini-flash-latest": ("gemini-3.5-flash", "gemini-flash-lite-latest"),
    "gemini-nano-banana-2.1": ("gemini-3.1-flash-image", "gemini-3.1-flash-lite-image"),
    "gemini-3.8-flash-tts": ("gemini-2.5-flash-preview-tts",),
    "gemini-2.5-flash-preview-tts": ("gemini-3.8-flash-tts",),
}
RETRY_CODE = re.compile(r"(?:^|\D)(429|500|502|503|504)(?:\D|$)")


def parse_api_keys_text(text: str) -> list[str]:
    """Extract clean API keys from a string (supports comma, semicolon, newline, or key=val)."""
    keys = []
    for line in str(text or "").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            var_name, val = line.split("=", 1)
            var_name = var_name.strip()
            # Only parse keys from GEMINI-related variables
            if not (var_name.startswith("GEMINI_KEY") or var_name in ("GEMINI_API_KEY", "GEMINI_API_KEYS")):
                continue
        else:
            val = line
        val = val.strip().strip('"').strip("'")
        for part in re.split(r"[,;\s]+", val):
            k = part.strip().strip('"').strip("'")
            # Strip non-ASCII characters that might come from Vietnamese Telex/VNI typing
            k = re.sub(r"[^\x20-\x7E]", "", k).strip()
            if k and len(k) >= 15 and not k.startswith("http") and not k.startswith("sk-") and k not in keys:
                keys.append(k)
    return keys


def get_all_api_keys() -> list[str]:
    """Return all configured Gemini API keys in priority order."""
    keys = []
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        try:
            for k in parse_api_keys_text(env_path.read_text(encoding="utf-8-sig")):
                if k not in keys:
                    keys.append(k)
        except Exception:
            pass
    for env_var in ("GEMINI_API_KEYS", "GEMINI_API_KEY"):
        v = os.environ.get(env_var, "")
        if v:
            for k in parse_api_keys_text(v):
                if k not in keys:
                    keys.append(k)
    return keys


def mask_key(key: str) -> str:
    """Safely mask key for logs without leaking secrets."""
    if not key or len(key) < 8:
        return "***"
    return f"...{key[-4:]}"


def status_code(exc):
    for attr in ("code", "status_code"):
        raw = getattr(exc, attr, None)
        if raw is not None:
            try:
                return int(raw)
            except (ValueError, TypeError):
                pass
    match = RETRY_CODE.search(str(exc))
    return int(match.group(1)) if match else None


def is_quota_error(exc, status=None) -> bool:
    code = status or status_code(exc)
    if code == 429:
        return True
    msg = str(exc).lower()
    return any(
        x in msg
        for x in (
            "quota exceeded",
            "exceeded your current quota",
            "quota metric",
            "resource exhausted",
            "billing required",
            "free tier limit",
            "rate limit",
            "too many requests",
        )
    )


def is_temporary(exc):
    code = status_code(exc)
    if code in (429, 500, 502, 503, 504):
        return True
    if code is not None:
        return False
    name = exc.__class__.__name__.lower()
    msg = str(exc).lower()
    return any(k in name for k in ("timeout", "connecterror", "readerror", "networkerror")) or any(
        k in msg for k in ("high demand", "temporarily unavailable", "connection timed out", "read timed out")
    )


class TransientGeminiFailure(RuntimeError):
    pass


class ApiKeyPool:
    """Manages rotation, cooldowns, and failover across multiple Gemini API keys."""

    def __init__(self, keys: list[str] | None = None):
        self._keys = list(keys) if keys else []
        self._exhausted_until: dict[str, float] = {}
        self._active_idx = 0

    def refresh(self):
        if not self._keys:
            self._keys = get_all_api_keys()

    @property
    def keys(self) -> list[str]:
        if not self._keys:
            self.refresh()
        return self._keys

    def mark_exhausted(self, key: str, cooldown_seconds: float = 60.0):
        self._exhausted_until[key] = time.time() + cooldown_seconds

    def is_available(self, key: str) -> bool:
        return time.time() >= self._exhausted_until.get(key, 0)

    def get_ordered_keys(self) -> list[str]:
        all_k = self.keys
        if not all_k:
            return [""]
        available = [k for k in all_k if self.is_available(k)]
        if not available:
            # All keys are in cooldown; reset cooldown so we can retry the pool
            self._exhausted_until.clear()
            available = list(all_k)

        ordered = []
        start = self._active_idx % len(all_k)
        for i in range(len(all_k)):
            k = all_k[(start + i) % len(all_k)]
            if k in available and k not in ordered:
                ordered.append(k)
        for k in all_k:
            if k not in ordered:
                ordered.append(k)
        return ordered

    def set_active_key(self, key: str):
        if key in self._keys:
            self._active_idx = self._keys.index(key)


def call_with_retry(
    fn,
    model,
    *args,
    sleeper=time.sleep,
    max_primary=2,
    max_fallback=1,
    base_delay=2.0,
    **kwargs,
):
    """Traditional single-fn retry & fallback across model list."""
    models = [model]
    if os.getenv("STORYBOARD_DISABLE_MODEL_FALLBACK", "0") != "1":
        models.extend(FALLBACKS.get(model, ()))
    last = None
    for model_i, candidate in enumerate(models):
        attempts = max_primary if model_i == 0 else max_fallback
        for attempt in range(1, attempts + 1):
            try:
                result = fn(*args, model=candidate, **kwargs)
                if model_i:
                    print(f"[GEMINI_FALLBACK_SUCCESS] selected={candidate}", flush=True)
                return result
            except Exception as exc:
                last = exc
                status = status_code(exc)
                if not is_temporary(exc):
                    print(
                        f"[GEMINI_NON_RETRYABLE] model={candidate} status={status or 'unknown'}",
                        flush=True,
                    )
                    raise
                hard_quota = is_quota_error(exc, status)
                other = (not hard_quota and attempt < attempts) or model_i < len(models) - 1
                print(
                    f"[GEMINI_RETRY] model={candidate} attempt={attempt}/{attempts} "
                    f"status={status or 'transient'}",
                    flush=True,
                )
                if other:
                    delay = (
                        0.5
                        if hard_quota
                        else min(18.0, base_delay * (2 ** (attempt - 1)) + random.uniform(0, 0.4))
                    )
                    sleeper(delay)
                if hard_quota:
                    print(f"[GEMINI_QUOTA] model={candidate} status=429", flush=True)
                    break
    code = status_code(last)
    label = "429 QUOTA_OR_RATE_LIMIT" if code == 429 else "503 CAPACITY" if code == 503 else f"{code or 'NETWORK'}"
    print(f"[GEMINI_EXHAUSTED] status={label}", flush=True)
    raise TransientGeminiFailure(
        f"Gemini request failed after bounded retries: {label}. "
        "Existing story bible, screenplay and finished scenes are preserved. "
        "For 429, check the model's rate/quota limits in Google AI Studio; "
        "otherwise retry later."
    ) from last


def is_text_only_contents(contents):
    # Reject silent loss of multimodal data during gateway fallback.
    if isinstance(contents, str): return True
    if hasattr(contents, "parts"): contents = contents.parts
    if not isinstance(contents, (list, tuple)) or not contents: return False
    for item in contents:
        if isinstance(item, str): continue
        if getattr(item, "inline_data", None) is not None: return False
        if getattr(item, "file_data", None) is not None: return False
        if getattr(item, "text", None) is None: return False
    return True


class ResilientModels:
    """Wrapper around models namespace that executes multi-key failover and multi-model fallback."""

    def __init__(self, client_parent: ResilientClient):
        self._parent = client_parent

    def generate_content(self, *, model, **kwargs):
        models = [model]
        if os.getenv("STORYBOARD_DISABLE_MODEL_FALLBACK", "0") != "1":
            models.extend(FALLBACKS.get(model, ()))

        last_exc = None
        pool = self._parent.pool

        for model_i, candidate_model in enumerate(models):
            ordered_keys = pool.get_ordered_keys()
            consecutive_quota_fails = 0
            for key_i, key in enumerate(ordered_keys):
                # Retrieve client instance for this key
                client_inst = self._parent.get_client_for_key(key)
                target_fn = getattr(client_inst.models, "generate_content", None)
                if not target_fn:
                    continue

                # Maximum retry attempts per key: 2 for primary, 1 for fallback
                max_key_attempts = 2 if model_i == 0 else 1
                for attempt in range(1, max_key_attempts + 1):
                    try:
                        res = target_fn(model=candidate_model, **kwargs)
                        pool.set_active_key(key)
                        self._parent.last_successful_model = candidate_model
                        if model_i > 0:
                            print(
                                f"[GEMINI_FALLBACK_SUCCESS] Đã tiếp tục thành công với model={candidate_model} (Khóa {mask_key(key)})!",
                                flush=True,
                            )
                        elif key_i > 0:
                            print(
                                f"[GEMINI_KEY_FAILOVER_SUCCESS] Đã tiếp tục thành công với Khóa {mask_key(key)} (model={candidate_model})!",
                                flush=True,
                            )
                        return res
                    except Exception as exc:
                        last_exc = exc
                        status = status_code(exc)

                        if status == 404 or "not found" in str(exc).lower() or "no longer available" in str(exc).lower():
                            print(f"[GEMINI_MODEL_UNAVAILABLE] model={candidate_model} không khả dụng (404). Chuyển sang model dự phòng tiếp theo...", flush=True)
                            break
                        if not is_temporary(exc):
                            print(
                                f"[GEMINI_NON_RETRYABLE] model={candidate_model} status={status or 'unknown'}",
                                flush=True,
                            )
                            raise

                        if is_quota_error(exc, status):
                            pool.mark_exhausted(key)
                            consecutive_quota_fails += 1
                            print(
                                f"[GEMINI_QUOTA_KEY_FAILOVER] Khóa #{key_i + 1} ({mask_key(key)}) chạm hạn mức Quota ({status or 429}).",
                                flush=True,
                            )
                            is_tts_req = "tts" in str(candidate_model).lower() or bool(
                                kwargs.get("config") and "AUDIO" in getattr(kwargs.get("config"), "response_modalities", [])
                            )
                            if consecutive_quota_fails >= 3 and is_tts_req:
                                print(
                                    f"[GEMINI_TTS_FAST_FALLBACK] 3 khóa liên tiếp chạm hạn mức Quota ({status or 429}). Ngắt quét sớm để chuyển ngay sang Edge-TTS trong 1s!",
                                    flush=True,
                                )
                                break
                            elif consecutive_quota_fails >= 5:
                                print(
                                    f"[GEMINI_QUOTA_FAST_FAILOVER] 5 khóa liên tiếp chạm hạn mức Quota ({status or 429}). Ngắt quét khóa để chuyển nhanh sang engine dự phòng!",
                                    flush=True,
                                )
                                break
                            if key_i < len(ordered_keys) - 1:
                                next_k = ordered_keys[key_i + 1]
                                print(
                                    f"  -> Tự động chuyển sang Khóa #{key_i + 2} ({mask_key(next_k)}) để tiếp tục...",
                                    flush=True,
                                )
                            break  # Move immediately to next key

                        # For transient 500/503/network
                        print(
                            f"[GEMINI_RETRY] model={candidate_model} key={mask_key(key)} attempt={attempt}/{max_key_attempts} status={status or 'transient'}",
                            flush=True,
                        )
                        if attempt < max_key_attempts:
                            time.sleep(min(8.0, 1.5 * (2 ** (attempt - 1)) + random.uniform(0, 0.3)))

            # If all keys exhausted for this candidate model, let's inform and try next candidate model
            if model_i < len(models) - 1:
                next_mod = models[model_i + 1]
                if "tts" in str(candidate_model).lower() and "tts" in str(next_mod).lower() and consecutive_quota_fails >= 3:
                    print(
                        f"[GEMINI_TTS_FAST_FALLBACK] Cả pool khóa đều hết Quota TTS ({candidate_model}). Ngắt chuyển đổi sang Edge-TTS ngay lập tức!",
                        flush=True,
                    )
                    break
                print(
                    f"[GEMINI_MODEL_FALLBACK] Tất cả khóa API đều bận/hết quota model={candidate_model}. Tự động chuyển sang model dự phòng: {next_mod}...",
                    flush=True,
                )

        # Check if caller requested AUDIO modality
        req_cfg = kwargs.get("config", None)
        is_audio = False
        if req_cfg:
            mods = getattr(req_cfg, "response_modalities", None) or []
            if "AUDIO" in mods:
                is_audio = True
        if "AUDIO" in kwargs.get("response_modalities", []):
            is_audio = True

        if is_audio:
            if last_exc:
                raise last_exc
            raise RuntimeError("Gemini TTS audio generation failed across all available keys.")

        # Tier-2 Failover: Check 3rd-party Gateway (Tuấn Stor - https://tuansuapi.store/v1)
        try:
            from . import tuansuapi_provider
        except (ImportError, ValueError):
            try:
                import tuansuapi_provider
            except ImportError:
                tuansuapi_provider = None

        if tuansuapi_provider and is_text_only_contents(kwargs.get("contents")):
            gw_cfg = tuansuapi_provider.get_gateway_config()
            if gw_cfg.get("enabled") == "1" and gw_cfg.get("api_key"):
                print(
                    "[FAILOVER_GATEWAY] Các khóa Gemini Google trực tiếp đã hết quota / bận. "
                    "Tự động chuyển tiếp sang API Bên Thứ Ba (Tuấn Stor - https://tuansuapi.store/v1)...",
                    flush=True,
                )
                try:
                    contents = kwargs.get("contents")
                    prompt_text = ""
                    if isinstance(contents, str):
                        prompt_text = contents
                    elif isinstance(contents, list):
                        prompt_text = "\n".join(str(c) for c in contents)
                    elif hasattr(contents, "parts"):
                        prompt_text = "\n".join(str(getattr(p, "text", p)) for p in contents.parts)
                    else:
                        prompt_text = str(contents or "")

                    messages = [
                        {"role": "system", "content": "You are a professional screenwriter and story designer. Return strictly valid JSON or formatted content as requested. Do not wrap in extra prose."},
                        {"role": "user", "content": prompt_text}
                    ]
                    reply_text = tuansuapi_provider.generate_chat_completion(
                        messages=messages,
                        model=gw_cfg.get("text_model")
                    )
                    # Clean markdown code block if present
                    clean_reply = reply_text.strip()
                    if clean_reply.startswith("```json"):
                        clean_reply = clean_reply[7:].strip()
                    elif clean_reply.startswith("```"):
                        clean_reply = clean_reply[3:].strip()
                    if clean_reply.endswith("```"):
                        clean_reply = clean_reply[:-3].strip()

                    print(
                        f"[FAILOVER_GATEWAY_SUCCESS] API Bên Thứ Ba (Tuấn Stor) đã tạo kịch bản thành công ({len(clean_reply)} chars)!",
                        flush=True,
                    )
                    from types import SimpleNamespace
                    return SimpleNamespace(text=clean_reply)
                except Exception as gw_exc:
                    print(f"[FAILOVER_GATEWAY_ERROR] API Bên Thứ Ba thất bại: {gw_exc}", flush=True)

        # If everything exhausted, raise TransientGeminiFailure
        code = status_code(last_exc)
        label = "429 QUOTA_OR_RATE_LIMIT" if code == 429 else "503 CAPACITY" if code == 503 else f"{code or 'NETWORK'}"
        print(f"[GEMINI_EXHAUSTED] status={label}", flush=True)
        raise TransientGeminiFailure(
            f"Gemini request failed after bounded multi-key retries: {label}. "
            "Existing story bible, screenplay and finished scenes are preserved. "
            "Add additional API keys to .env to increase capacity."
        ) from last_exc

    def __getattr__(self, name):
        active_client = self._parent.get_active_client()
        return getattr(active_client.models, name)


class ResilientClient:
    """Drop-in replacement for google.genai.Client with multi-key pooling and automatic model fallback."""

    def __init__(self, core_client=None, api_keys: list[str] | None = None):
        self._core = core_client
        self._client_cache: dict[str, any] = {}
        self.pool = ApiKeyPool(api_keys)
        self.models = ResilientModels(self)

    def get_client_for_key(self, key: str):
        if key in self._client_cache:
            return self._client_cache[key]
        if not key and self._core:
            return self._core

        try:
            from google import genai
            client = genai.Client(api_key=key)
            self._client_cache[key] = client
            return client
        except Exception:
            if self._core:
                return self._core
            raise

    def get_active_client(self):
        keys = self.pool.get_ordered_keys()
        if keys and keys[0]:
            return self.get_client_for_key(keys[0])
        return self._core

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __getattr__(self, name):
        active = self.get_active_client()
        if active is not None:
            return getattr(active, name)
        raise AttributeError(f"'ResilientClient' object has no attribute '{name}'")
