import sys
import json
from pathlib import Path
from google import genai

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import load_config

cfg = load_config()
keys = cfg.get("gemini_keys", [])
print(f"Total keys to test: {len(keys)}", flush=True)

working_keys = []
for idx, k in enumerate(keys):
    prefix = k[:10] + "..."
    try:
        client = genai.Client(api_key=k)
        resp = client.models.generate_content(
            model="gemini-3.5-flash",
            contents="Hello! Reply with 1 word 'OK'."
        )
        ans = resp.text.strip()
        print(f"[{idx+1}/{len(keys)}] Key {prefix}: SUCCESS -> {ans}", flush=True)
        working_keys.append(k)
    except Exception as e:
        err = str(e)
        if "429" in err:
            status = "429 Quota Exceeded"
        elif "400" in err:
            status = "400 Bad Request / Invalid Key"
        elif "503" in err:
            status = "503 Unavailable"
        else:
            status = err[:60]
        print(f"[{idx+1}/{len(keys)}] Key {prefix}: FAILED -> {status}", flush=True)

print(f"\nSummary: {len(working_keys)}/{len(keys)} keys working.", flush=True)
