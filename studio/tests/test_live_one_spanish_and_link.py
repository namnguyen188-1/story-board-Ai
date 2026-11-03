"""Bounded provider smoke: one public YouTube analysis and one short ES TTS,
without image/video jobs. No keys/cookies in logs; local Studio key only.
"""
from pathlib import Path
import sys,os,json,wave,traceback,time
r=Path(r"D:\STORYBOARD_AI\studio");sys.path.insert(0,str(r))
from series_studio import own_api_key
from studio_input_modes import analyze_reference
key=own_api_key()
if not key:
    print("BLOCKED_STUDIO_KEY_NOT_CONFIGURED",flush=True)
    raise SystemExit(3)
os.environ["STORYBOARD_DISABLE_MODEL_FALLBACK"]="1"
from google import genai
from google.genai import types
from resilient_gemini import status_code
client=genai.Client(api_key=key,http_options=types.HttpOptions(timeout=35000))
try:
    started=time.monotonic()
    analysis=analyze_reference(client,"gemini-3.8-flash","https://youtu.be/0ArKOVnNgio")
    safe={k:analysis.get(k) for k in ("genre","primary_language","hook_technique","visual_style")}
    print("REAL_YOUTUBE_REFERENCE_ANALYSIS_PASS",json.dumps(safe,ensure_ascii=True)[:500],
          "elapsed",round(time.monotonic()-started,1),flush=True)
except Exception as exc:
    print("REAL_YOUTUBE_REFERENCE_ANALYSIS_FAILED",type(exc).__name__,
          "HTTP",status_code(exc),"elapsed",round(time.monotonic()-started,1),flush=True)
try:
    sys.path.insert(0,str(r/"engine"))
    from tools import tts,utils
    utils.client=client
    tts_dir=r/"diagnostics"/"spanish_voice_one_probe"
    tts_dir.mkdir(parents=True,exist_ok=True)
    utils.GLOBAL_OUTPUT_DIR=str(tts_dir)
    started=time.monotonic()
    result=tts.generate_tts_audio_tool_fn(
        "La serenidad comienza cuando distinguimos lo que depende de nosotros.",
        language="Spanish",voice_name="Charon",
        voice_style="Native Spain Spanish; calm stoic philosophical narration, natural cadence and controlled emphasis.")
    path=Path(result)
    if not path.is_file():raise RuntimeError("TTS returned no file")
    with wave.open(str(path),"rb") as wf:
        duration=wf.getnframes()/max(1,wf.getframerate())
        rate=wf.getframerate()
    if not 1.0<duration<25:raise RuntimeError("TTS audio invalid duration")
    print("REAL_ES_TTS_PASS voice=Charon duration_s",round(duration,2),
          "rate",rate,"bytes",path.stat().st_size,"elapsed",round(time.monotonic()-started,1),
          "path",str(path),flush=True)
except Exception as exc:
    print("REAL_ES_TTS_FAILED",type(exc).__name__,"HTTP",status_code(exc),
          "elapsed",round(time.monotonic()-started,1),flush=True)
