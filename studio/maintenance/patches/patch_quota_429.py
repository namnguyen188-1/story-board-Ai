"""Bound transient Gemini failures without burning repeated image-quota attempts."""
from pathlib import Path
import shutil,py_compile
root=Path(r"D:\STORYBOARD_AI\studio")
files=[root/"resilient_gemini.py",root/"series_studio.py"]
checkpoint=root/"checkpoints"/"quota_429_20261011"
checkpoint.mkdir(parents=True,exist_ok=True)
for file in files: shutil.copy2(file,checkpoint/file.name)
p=root/"resilient_gemini.py"
s=p.read_text(encoding="utf-8")
s=s.replace('("gemini-3.1-flash-image",)', '("gemini-3.1-flash-image","gemini-3.1-flash-lite-image")')
s=s.replace('max_primary=3,','max_primary=2,').replace('max_fallback=2,','max_fallback=1,')
needle='''                # Retry only transient conditions; no unbounded loops.
                other = attempt < attempts or model_i < len(models)-1'''
assert needle in s
s=s.replace(needle,'''                # A hard quota error is not fixed by repeated calls to the same model.
                hard_quota = status == 429 and any(
                    x in str(exc).lower() for x in ("quota exceeded","exceeded your current quota",
                    "quota metric", "billing required", "free tier limit")
                )
                # Retry only transient conditions; no unbounded loops.
                other = (not hard_quota and attempt < attempts) or model_i < len(models)-1''',1)
needle='''                if other:
                    delay = min(18.0, base_delay * (2 ** (attempt-1)) + random.uniform(0, 0.4))
                    sleeper(delay)'''
assert needle in s
s=s.replace(needle,'''                if other:
                    delay = (0.5 if hard_quota else
                             min(18.0, base_delay * (2 ** (attempt-1)) + random.uniform(0, 0.4)))
                    sleeper(delay)
                if hard_quota:
                    print(f"[GEMINI_QUOTA] model={candidate} status=429",flush=True)
                    break''',1)
needle='''    raise TransientGeminiFailure("Gemini temporarily unavailable after bounded retries and fallback. "
                       "No completed scenes were discarded. Try the same episode again.") from last'''
assert needle in s
s=s.replace(needle,'''    code = status_code(last)
    label = "429 QUOTA_OR_RATE_LIMIT" if code == 429 else "503 CAPACITY" if code == 503 else f"{code or 'NETWORK'}"
    print(f"[GEMINI_EXHAUSTED] status={label}",flush=True)
    raise TransientGeminiFailure(
        f"Gemini request failed after bounded retries: {label}. "
        "Existing story bible, screenplay and finished scenes are preserved. "
        "For 429, check the model's rate/quota limits in Google AI Studio; "
        "otherwise retry later."
    ) from last''',1)
p.write_text(s,encoding="utf-8")
p=root/"series_studio.py"
s=p.read_text(encoding="utf-8")
needle='''            if any(x in last_error.lower() for x in ("401","403","invalid api key","permission_denied")):'''
assert needle in s
s=s.replace(needle,'''            if any(x in last_error.lower() for x in (
                    "401","403","invalid api key","permission_denied",
                    "gemini request failed after bounded retries",
                    "gemini temporarily unavailable after bounded retries",
                    "429 quota_or_rate_limit")):''',1)
p.write_text(s,encoding="utf-8")
for file in files: py_compile.compile(str(file),doraise=True)
print("QUOTA_HANDLING_PATCH_PASS")
print("BACKUP",str(checkpoint))
