"""Timestamped public YouTube reference study. Never substitutes a thumbnail for video evidence."""
from __future__ import annotations
import json
from studio_input_modes import youtube_url

class ReferenceVideoUnavailable(RuntimeError):
    pass

def validate_timeline(data, duration_minutes=0):
    if not isinstance(data,dict) or data.get("error"):
        raise ReferenceVideoUnavailable("REFERENCE_VIDEO_NOT_READABLE")
    points=data.get("timeline")
    if not isinstance(points,list) or len(points)<3:
        raise ReferenceVideoUnavailable("REFERENCE_TIMELINE_TOO_SPARSE")
    expected=float(duration_minutes or 0)*60
    if expected > 0:
        # Exclude points that hallucinate past the actual video runtime
        points = [p for p in points if isinstance(p, dict) and float(p.get("timestamp_seconds", 0)) <= expected + 1.0]
        data["timeline"] = points
        if len(points) < 3:
            raise ReferenceVideoUnavailable("REFERENCE_TIMELINE_TOO_SPARSE")

    times=[]
    for entry in points:
        if not isinstance(entry,dict) or not str(entry.get("subject","")).strip() or not str(entry.get("shot_type","")).strip():
            raise ReferenceVideoUnavailable("REFERENCE_TIMELINE_MISSING_OBSERVATION")
        try:
            t=float(entry.get("timestamp_seconds"))
        except (ValueError,TypeError):
            raise ReferenceVideoUnavailable("REFERENCE_TIMELINE_MISSING_TIMESTAMP")
        if not 0 <= t < 86400:
            raise ReferenceVideoUnavailable("REFERENCE_TIMELINE_INVALID_TIMESTAMP")
        times.append(t)
        import re
        bad_pat = r'(?i)\b(peripheral|subtle|vertical|edge)?\s*(mirroring|mirrored|mirror seam|mirror effect|mirrored border effects?|kaleidoscope(\s+edge\s+blur)?|diptych|split[- ]screen)\b'
        for field in ("subject", "composition", "background"):
            if field in entry and isinstance(entry[field], str):
                entry[field] = re.sub(bad_pat, '', entry[field]).strip(' ,;-')
    if any(a>=b for a,b in zip(times,times[1:])):
        raise ReferenceVideoUnavailable("REFERENCE_TIMELINE_NOT_CHRONOLOGICAL")
    if expected>=600 and len(times)<max(6,int(expected/120)):
        raise ReferenceVideoUnavailable("REFERENCE_TIMELINE_TOO_SPARSE_FOR_LONG_VIDEO")
    if expected>=30 and (times[0]>min(30,expected*0.05) or times[-1]<expected*0.85):
        raise ReferenceVideoUnavailable("REFERENCE_TIMELINE_NOT_FULL_COVERAGE")
    return data

def analyze_youtube_timeline(url, duration_minutes=0, client=None, models=None):
    """Ask Gemini about video from start to finish, without downloading large media.

    Any failure returns a clear error to the caller, not imagined timeline contents.
    """
    canonical=youtube_url(url)
    from google.genai import types
    if client is None:
        from resilient_gemini import ResilientClient, get_all_api_keys
        keys=get_all_api_keys()
        if not keys:
            raise ReferenceVideoUnavailable("REFERENCE_VIDEO_KEY_MISSING")
        # ResilientClient tries each available key, then its configured
        # multimodal-compatible model fallbacks (3.8 -> 3.5 -> ...).
        client=ResilientClient(api_keys=keys)
    # The resilient wrapper handles 3.5/3.1 fallbacks itself.
    # Injected test clients may override the model sequence explicitly.
    models=models or ("gemini-3.8-flash",)
    n=16 if float(duration_minutes or 0)>=10 else 10 if float(duration_minutes or 0)>=2 else 6
    expected_sec = float(duration_minutes or 0) * 60
    dur_note = f" The video is {duration_minutes:.1f} minutes long ({int(expected_sec)} seconds). All timestamp_seconds must strictly be between 0 and {int(expected_sec)}." if expected_sec > 0 else ""
    prompt=(
        "Inspect the ACTUAL video, observing the START, MIDDLE and END. "
        "Do not infer visuals from title, metadata, thumbnail or genre. "
        "Return JSON only: timeline (array) and global_visual_style (text). "
        f"Give about {n} observations spread throughout full video duration.{dur_note} "
        "or state error VIDEO_UNAVAILABLE if unable to inspect. "
        "Every timeline item must include timestamp_seconds (numeric), "
        "subject, shot_type (wide/full_body/medium/closeup/object/environment), "
        "composition, palette, background, camera_movement. "
        "Report actual repetition or static shots honestly. Describe whether "
        "subjects are statues/sculptures or live actors and whether the framing "
        "shows upper body or full body where visible. "
        "Only observational cinematography information for ORIGINAL adaptation. "
        "CRITICAL: Ignore video editing artifacts, mirror borders, kaleidoscope blur, split screens, captions/subtitles, or letterbox bars. Describe only the true physical subject and background. Never describe a single subject as mirrored, symmetrical, double, or split. "
        "Do not reproduce identifiable frames, dialogue or original story."
    )
    last=None
    for model in models:
        try:
            res=client.models.generate_content(
                model=model,
                # YouTube URLs are VIDEO REFERENCES, not uploaded MP4 file URIs.
                # Keep real video data in every key/model retry.
                contents=types.Content(parts=[
                    types.Part(file_data=types.FileData(file_uri=canonical)),
                    types.Part(text=prompt)
                ]),
                config={"response_mime_type":"application/json","temperature":0}
            )
            data=validate_timeline(json.loads(str(res.text)),duration_minutes)
            return {"timeline":data["timeline"][:32],
                    "global_visual_style":str(data.get("global_visual_style",""))[:1000],
                    "whole_video_verified":True,
                    "video_analysis_model":getattr(client,"last_successful_model",None) or model}
        except Exception as exc:
            last=exc
            print(f"[REFERENCE_VIDEO] provider={model} error={type(exc).__name__}",flush=True)
    raise ReferenceVideoUnavailable("REFERENCE_VIDEO_ANALYSIS_UNAVAILABLE") from last
