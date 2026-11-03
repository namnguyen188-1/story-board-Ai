"""One bounded fallback video-analysis probe; no repeated calls, no account secrets printed."""
import sys,os,time
from pathlib import Path
root=Path(r"D:\STORYBOARD_AI\studio")
sys.path.insert(0,str(root))
from series_studio import own_api_key
from studio_input_modes import analyze_reference
from google import genai
from google.genai import types
from resilient_gemini import status_code
key=own_api_key()
if not key:raise SystemExit("STUDIO_KEY_MISSING")
client=genai.Client(api_key=key,http_options=types.HttpOptions(timeout=30000))
start=time.monotonic()
try:
    data=analyze_reference(client,"gemini-3.6-flash","https://youtu.be/9hE5-98ZeCg")
    print("ALTERNATE_SHORT_YOUTUBE_ANALYSIS_PASS",
          str(data.get("genre"))[:30],
          str(data.get("primary_language"))[:30],flush=True)
except Exception as exc:
    print("ALTERNATE_SHORT_YOUTUBE_ANALYSIS_FAILED",
          type(exc).__name__,status_code(exc),flush=True)
print("ELAPSED",round(time.monotonic()-start,2),flush=True)
