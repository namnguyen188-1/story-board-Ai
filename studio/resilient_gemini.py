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

import hashlib
import os
import sys
import re
import time
import random
import socket
import json
import threading
from pathlib import Path

TTS_COOLDOWN_FILE = Path(__file__).resolve().parent / "runtime" / "gemini_tts_key_cooldowns.json"
_TTS_COOLDOWN_LOCK = threading.Lock()


def _key_digest(key: str) -> str:
    return hashlib.sha256(str(key or "").encode("utf-8")).hexdigest()[:12]


def _load_tts_cooldowns() -> dict[str, float]:
    now = time.time()
    try:
        if TTS_COOLDOWN_FILE.is_file():
            raw = json.loads(TTS_COOLDOWN_FILE.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                return {k: float(v) for k, v in raw.items() if float(v) > now}
    except Exception:
        pass
    return {}


def _mark_tts_key_cooldown(key: str, seconds: float) -> None:
    if not key:
        return
    until = time.time() + max(10.0, float(seconds))
    digest = _key_digest(key)
    with _TTS_COOLDOWN_LOCK:
        try:
            TTS_COOLDOWN_FILE.parent.mkdir(parents=True, exist_ok=True)
            data = _load_tts_cooldowns()
            data[digest] = max(float(data.get(digest, 0.0)), until)
            tmp = TTS_COOLDOWN_FILE.with_suffix(".tmp")
            tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
            tmp.replace(TTS_COOLDOWN_FILE)
        except Exception:
            pass


def _parse_tts_retry_cooldown(exc: Exception) -> float:
    msg = str(exc or "").lower()
    if "generate_content_free_tier_requests" in msg or "perday" in msg or "per day" in msg:
        return 3600.0 * 4.0
    m = re.search(r"retrydelay['\"]?\s*[:=]\s*['\"]?(\d+)", msg, re.I)
    if m:
        try:
            return min(14400.0, max(60.0, float(m.group(1))))
        except Exception:
            pass
    return 120.0

# Enforce a 45-second hard ceiling on all underlying TCP/HTTP sockets so calls cannot hang indefinitely
try:
    socket.setdefaulttimeout(45.0)
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
    "gemini-3.8-flash": ("gemini-3.5-flash-lite", "gemini-flash-lite-latest", "gemini-3-flash-preview", "gemini-3.5-flash"),
    "gemini-3.5-flash": ("gemini-3.5-flash-lite", "gemini-flash-lite-latest", "gemini-3-flash-preview", "gemini-3.8-flash"),
    "gemini-3.5-flash-lite": ("gemini-flash-lite-latest", "gemini-3-flash-preview", "gemini-3.8-flash", "gemini-3.5-flash"),
    "gemini-flash-lite-latest": ("gemini-3.5-flash-lite", "gemini-3-flash-preview", "gemini-3.8-flash", "gemini-3.5-flash"),
    "gemini-3-flash-preview": ("gemini-3.5-flash-lite", "gemini-flash-lite-latest", "gemini-3.8-flash", "gemini-3.5-flash"),
    "gemini-3.6-flash": ("gemini-3.5-flash-lite", "gemini-flash-lite-latest", "gemini-3.8-flash", "gemini-3.5-flash"),
    "gemini-3.7-flash": ("gemini-3.5-flash-lite", "gemini-flash-lite-latest", "gemini-3.8-flash", "gemini-3.5-flash"),
    "gemini-2.5-flash": ("gemini-3.5-flash-lite", "gemini-flash-lite-latest", "gemini-3.8-flash"),
    "gemini-3.1-flash-lite": ("gemini-3.5-flash-lite", "gemini-flash-lite-latest", "gemini-3.8-flash"),
    "gemini-3.1-flash-lite-preview": ("gemini-3.5-flash-lite", "gemini-flash-lite-latest", "gemini-3.8-flash"),
    "gemini-flash-latest": ("gemini-3.5-flash-lite", "gemini-flash-lite-latest", "gemini-3.8-flash"),
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
        self._lock = threading.Lock()

    def refresh(self):
        with self._lock:
            if not self._keys:
                self._keys = get_all_api_keys()

    @property
    def keys(self) -> list[str]:
        with self._lock:
            if not self._keys:
                self._keys = get_all_api_keys()
            return list(self._keys)

    def mark_exhausted(self, key: str, cooldown_seconds: float = 60.0):
        with self._lock:
            self._exhausted_until[key] = time.time() + cooldown_seconds

    def is_available(self, key: str) -> bool:
        with self._lock:
            return time.time() >= self._exhausted_until.get(key, 0)

    def get_ordered_keys(self) -> list[str]:
        with self._lock:
            all_k = list(self._keys) if self._keys else get_all_api_keys()
            if not self._keys:
                self._keys = list(all_k)
            if not all_k:
                return [""]
            available = [k for k in all_k if time.time() >= self._exhausted_until.get(k, 0)]
            if not available:
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
        with self._lock:
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


def _load_freellmapi_provider():
    """Import freellmapi_provider from package or top-level studio path."""
    try:
        from . import freellmapi_provider
        return freellmapi_provider
    except (ImportError, ValueError):
        try:
            import freellmapi_provider
            return freellmapi_provider
        except ImportError:
            return None


def _contents_to_messages(contents) -> list[dict]:
    """Convert Gemini SDK contents payload to OpenAI-compatible chat messages."""
    if isinstance(contents, str):
        prompt_text = contents
    elif isinstance(contents, list):
        prompt_text = "\n".join(str(c) for c in contents)
    elif hasattr(contents, "parts"):
        prompt_text = "\n".join(str(getattr(p, "text", p)) for p in contents.parts)
    else:
        prompt_text = str(contents or "")
    return [
        {
            "role": "system",
            "content": "You are a professional screenwriter and story designer. Return strictly valid JSON or formatted content as requested. Do not wrap in extra prose.",
        },
        {"role": "user", "content": prompt_text},
    ]


def _clean_markdown_reply(reply_text: str) -> str:
    """Strip outer markdown code fences from LLM text/JSON replies."""
    clean_reply = reply_text.strip()
    if clean_reply.startswith("```json"):
        clean_reply = clean_reply[7:].strip()
    elif clean_reply.startswith("```"):
        clean_reply = clean_reply[3:].strip()
    if clean_reply.endswith("```"):
        clean_reply = clean_reply[:-3].strip()
    return clean_reply


class ResilientModels:
    """Wrapper around models namespace that executes multi-key failover and multi-model fallback."""

    def __init__(self, client_parent: ResilientClient):
        self._parent = client_parent

    def _try_freellmapi(self, contents, stage_label: str):
        """Attempt text completion through local FreeLLMAPI proxy if enabled and ready."""
        provider = _load_freellmapi_provider()
        if not provider or not is_text_only_contents(contents):
            return None
        cfg = provider.get_config()
        if cfg.get("mode") == "off" or not cfg.get("api_key"):
            return None
        reply_text = provider.generate_chat_completion(
            messages=_contents_to_messages(contents),
            model=cfg.get("model") or "auto",
        )
        clean_reply = _clean_markdown_reply(reply_text)
        active_model = cfg.get("model") or "auto"
        print(
            f"[FREELLMAPI_{stage_label}_SUCCESS] FreeLLMAPI ({active_model}) đã tạo nội dung thành công ({len(clean_reply)} chars)!",
            flush=True,
        )
        from types import SimpleNamespace
        return SimpleNamespace(text=clean_reply)

    def generate_content(self, *, model, **kwargs):
        is_text_non_tts = is_text_only_contents(kwargs.get("contents")) and "tts" not in str(model).lower()
        freellm_tried = False

        # 0. Primary Preference (if user explicitly selected FreeLLMAPI as primary)
        if is_text_non_tts:
            fl_mod = _load_freellmapi_provider()
            if fl_mod and fl_mod.get_config().get("mode") == "primary":
                freellm_tried = True
                try:
                    res = self._try_freellmapi(kwargs.get("contents"), "PRIMARY")
                    if res is not None:
                        return res
                except Exception as e_fl:
                    print(f"[FREELLMAPI_NOTICE] FreeLLMAPI: {e_fl}. Tự động chuyển sang Cloud AI / Gemini...", flush=True)

        # 1. Primary Preference: If Tuấn Stor Gateway is configured and preferred, execute directly via Tuấn Stor!
        try:
            from . import tuansuapi_provider
        except (ImportError, ValueError):
            try:
                import tuansuapi_provider
            except ImportError:
                tuansuapi_provider = None

        if tuansuapi_provider and is_text_only_contents(kwargs.get("contents")):
            gw_cfg = tuansuapi_provider.get_gateway_config()
            prefer_tuan = os.getenv("PREFER_TUANSU", "1") == "1" and gw_cfg.get("enabled") == "1" and gw_cfg.get("api_key")
            if prefer_tuan and "tts" not in str(model).lower():
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
                    active_text_model = gw_cfg.get("text_model") or "gemini-flash-3.8-fast"
                    reply_text = tuansuapi_provider.generate_chat_completion(
                        messages=messages,
                        model=active_text_model
                    )
                    clean_reply = reply_text.strip()
                    if clean_reply.startswith("```json"):
                        clean_reply = clean_reply[7:].strip()
                    elif clean_reply.startswith("```"):
                        clean_reply = clean_reply[3:].strip()
                    if clean_reply.endswith("```"):
                        clean_reply = clean_reply[:-3].strip()

                    print(
                        f"[TUANSU_GATEWAY_SUCCESS] Đã tạo nội dung thành công qua Tuấn Stor ({active_text_model}) ({len(clean_reply)} chars)!",
                        flush=True,
                    )
                    from types import SimpleNamespace
                    return SimpleNamespace(text=clean_reply)
                except Exception as e_tuan:
                    print(f"[TUANSU_GATEWAY_NOTICE] Tuấn Stor: {e_tuan}. Tự động fallback sang Google Gemini pool...", flush=True)

        models = [model]
        if os.getenv("STORYBOARD_DISABLE_MODEL_FALLBACK", "0") != "1":
            models.extend(FALLBACKS.get(model, ()))

        last_exc = None
        pool = self._parent.pool

        for model_i, candidate_model in enumerate(models):
            is_tts_req = "tts" in str(candidate_model).lower() or bool(
                kwargs.get("config") and "AUDIO" in (getattr(kwargs.get("config"), "response_modalities", None) or [])
            )
            ordered_keys = pool.get_ordered_keys()
            if is_tts_req:
                tts_cooldowns = _load_tts_cooldowns()
                if tts_cooldowns:
                    fresh_keys = [k for k in ordered_keys if _key_digest(k) not in tts_cooldowns]
                    cooled_keys = [k for k in ordered_keys if _key_digest(k) in tts_cooldowns]
                    if fresh_keys:
                        ordered_keys = fresh_keys
                    else:
                        ordered_keys = cooled_keys[:3]
            consecutive_quota_fails = 0
            consecutive_server_fails = 0
            abandon_current_model = False
            for key_i, key in enumerate(ordered_keys):
                if abandon_current_model:
                    break
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
                            abandon_current_model = True
                            break
                        if not is_temporary(exc):
                            print(
                                f"[GEMINI_NON_RETRYABLE] model={candidate_model} status={status or 'unknown'}",
                                flush=True,
                            )
                            raise

                        if is_quota_error(exc, status):
                            pool.mark_exhausted(key)
                            if is_tts_req:
                                _mark_tts_key_cooldown(key, _parse_tts_retry_cooldown(exc))
                            consecutive_quota_fails += 1
                            print(
                                f"[GEMINI_QUOTA_KEY_FAILOVER] Khóa #{key_i + 1} ({mask_key(key)}) chạm hạn mức Quota ({status or 429}).",
                                flush=True,
                            )
                            tts_scan_limit = min(len(ordered_keys), 20)
                            if is_tts_req and consecutive_quota_fails >= tts_scan_limit:
                                print(
                                    f"[GEMINI_TTS_FAST_FALLBACK] {consecutive_quota_fails} khóa TTS chạm hạn mức Quota ({status or 429}). Ngắt quét để chuyển sang giọng Neural dự phòng!",
                                    flush=True,
                                )
                                abandon_current_model = True
                                break
                            elif (not is_tts_req) and consecutive_quota_fails >= 3:
                                print(
                                    f"[GEMINI_QUOTA_FAST_FAILOVER] 3 khóa cùng thuộc Project chạm hạn mức Quota ({status or 429}). Ngắt quét khóa để chuyển nhanh sang model dự phòng!",
                                    flush=True,
                                )
                                abandon_current_model = True
                                break
                            if key_i < len(ordered_keys) - 1:
                                next_k = ordered_keys[key_i + 1]
                                print(
                                    f"  -> Tự động chuyển sang Khóa #{key_i + 2} ({mask_key(next_k)}) để tiếp tục...",
                                    flush=True,
                                )
                            break  # Move immediately to next key

                        if status in (500, 502, 503, 504):
                            consecutive_server_fails += 1
                            if consecutive_server_fails >= 2:
                                print(
                                    f"[GEMINI_SERVER_FAST_FAILOVER] Model {candidate_model} gặp lỗi máy chủ ({status}) liên tiếp 2 lần. Tự động chuyển ngay sang model dự phòng!",
                                    flush=True,
                                )
                                abandon_current_model = True
                                break

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
                if "tts" in str(candidate_model).lower() and "tts" in str(next_mod).lower() and consecutive_quota_fails >= min(len(ordered_keys), 20):
                    print(
                        f"[GEMINI_TTS_FAST_FALLBACK] Cả pool khóa khả dụng đều hết Quota TTS ({candidate_model}). Chuyển sang giọng Neural dự phòng!",
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

        # Tier-3 Failover: FreeLLMAPI local OpenAI-compatible proxy
        if is_text_non_tts and not freellm_tried:
            try:
                res = self._try_freellmapi(kwargs.get("contents"), "FAILOVER")
                if res is not None:
                    return res
            except Exception as fl_exc:
                print(f"[FREELLMAPI_FAILOVER_ERROR] FreeLLMAPI thất bại: {fl_exc}", flush=True)

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
            client = genai.Client(api_key=key, http_options={"timeout": 60000})
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
