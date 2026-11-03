"""Fallback timeline from actual local video frames, using Studio Gemini API.

Samples are spread across full duration; metadata, thumbnails, and synthetic
scene names never count as observed evidence. No local ML model/GPU required.
"""
from __future__ import annotations
import hashlib,json,math,subprocess,sys
from pathlib import Path
try:
    import silent_subprocess
except Exception:
    pass
from clone_integrity import CloneEvidenceError,valid_reference

def _get_silent_si_and_flags():
    si = subprocess.STARTUPINFO()
    si.dwFlags |= getattr(subprocess, "STARTF_USESHOWWINDOW", 1)
    si.wShowWindow = getattr(subprocess, "SW_HIDE", 0)
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
    return si, flags

def observed_frames(video_path:Path,cache_dir:Path, duration_seconds:float)->list[dict]:
    source=Path(video_path)
    if not source.is_file() or not 10<=duration_seconds<=43200:
        raise CloneEvidenceError("VIDEO_SAMPLE_UNAVAILABLE")

    # Probe real duration from video file using ffprobe
    real_dur = None
    si, flags = _get_silent_si_and_flags()
    try:
        cmd_p = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", str(source)]
        p_dur = subprocess.run(cmd_p, capture_output=True, text=True, timeout=10,
                               stdin=subprocess.DEVNULL, startupinfo=si, creationflags=flags)
        if p_dur.returncode == 0 and p_dur.stdout.strip():
            val = float(p_dur.stdout.strip())
            if 5.0 <= val <= 86400.0:
                real_dur = val
    except Exception:
        pass

    effective_dur = min(duration_seconds, real_dur) if real_dur is not None else duration_seconds
    n = max(3, math.ceil(duration_seconds / 120))
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    mark = hashlib.sha256((str(source.resolve()) + "|" + str(source.stat().st_size) +
          "|" + str(source.stat().st_mtime_ns)).encode()).hexdigest()[:14]

    start_t = 0.0
    min_end = duration_seconds * 0.86
    safe_eof = max(start_t + 1.0, effective_dur - 2.0)
    end_t = min(safe_eof, max(min_end, effective_dur * 0.95))
    if end_t <= start_t:
        end_t = max(start_t + 1.0, effective_dur - 0.5)

    result = []
    for index in range(n):
        target_at = round(start_t + (end_t - start_t) * index / max(1, n - 1), 2)
        if result and target_at <= result[-1]["timestamp_seconds"]:
            target_at = round(result[-1]["timestamp_seconds"] + 0.5, 2)
        jpg = cache_dir / f"observed_{mark}_{index+1:03d}.jpg"
        if not jpg.is_file() or jpg.stat().st_size < 1000:
            success = False
            candidates = [target_at]
            if target_at > 1.0:
                candidates.extend([
                    round(target_at - 1.0, 2),
                    round(target_at - 2.5, 2),
                    round(target_at - 5.0, 2),
                ])
            for try_at in candidates:
                if result and try_at <= result[-1]["timestamp_seconds"]:
                    continue
                if try_at < 0:
                    continue
                cmd = ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
                       "-ss", str(try_at), "-i", str(source),
                       "-frames:v", "1", "-vf", "scale=640:360", "-q:v", "3", str(jpg)]
                try:
                    p = subprocess.run(cmd, capture_output=True, timeout=90,
                                     stdin=subprocess.DEVNULL, startupinfo=si, creationflags=flags)
                    if p.returncode == 0 and jpg.is_file() and jpg.stat().st_size >= 1000:
                        target_at = try_at
                        success = True
                        break
                except (OSError, subprocess.TimeoutExpired):
                    pass
            if not success:
                raise CloneEvidenceError("SOURCE_SAMPLE_FRAME_DECODE_FAILED")
        result.append({"timestamp_seconds": target_at, "frame_path": str(jpg)})
    return result

def frame_timeline_batch(frames:list[dict],client,model="gemini-3.8-flash")->list[dict]:
    from google.genai import types
    if not 1<=len(frames)<=4:
        raise CloneEvidenceError("REFERENCE_TIMELINE_INVALID_BATCH")
    prompt=(
      "Analyze actual video frame images attached separately with their precise "
      "timestamps. Describe only what appears; never infer subject, scene, "
      "camera movement or time from titles or metadata. Reply JSON with "
      "timeline array in the same order, exactly one entry per timestamp. "
      "Each entry must contain timestamp_seconds(number), subject(detailed "
      "string), shot_type(one of wide/full_body/medium/closeup/object/environment), "
      "composition(string),palette(string),background(string),"
      "camera_movement(string; say unknown_from_still if not inferable). "
      "Static busts must remain statues if observed; no forced variation."
    )
    contents=[types.Part.from_text(text=prompt)]
    for f in frames:
        data=Path(f["frame_path"]).read_bytes()
        if not data.startswith(bytes.fromhex("ffd8ff")):
            raise CloneEvidenceError("INVALID_SOURCE_FRAME")
        contents += [types.Part.from_text(text=f"timestamp_seconds={f['timestamp_seconds']}"),
                     types.Part.from_bytes(data=data,mime_type="image/jpeg")]
    response=client.models.generate_content(
       model=model,contents=contents,
       config={"response_mime_type":"application/json",
               "temperature":0,"max_output_tokens":3200})
    try:
        decoded=json.loads(response.text)
        items=decoded if isinstance(decoded,list) else decoded["timeline"]
    except (TypeError,ValueError,KeyError) as ex:
        raise CloneEvidenceError("SOURCE_TIMELINE_MODEL_INVALID_JSON") from ex
    if not isinstance(items,list) or len(items)!=len(frames):
        raise CloneEvidenceError("SOURCE_TIMELINE_MODEL_COUNT_MISMATCH")
    allowed={"wide","full_body","medium","closeup","object","environment"}
    results=[]
    for source,item in zip(frames,items):
        if not isinstance(item,dict) or item.get("shot_type") not in allowed:
            raise CloneEvidenceError("SOURCE_TIMELINE_BAD_SHOT")
        if abs(float(item.get("timestamp_seconds",-999))-source["timestamp_seconds"])>2:
            raise CloneEvidenceError("SOURCE_TIMELINE_TIMESTAMP_DRIFT")
        for k in ("subject","composition","palette","background","camera_movement"):
            if not isinstance(item.get(k),str) or len(item[k].strip())<3:
                raise CloneEvidenceError("SOURCE_TIMELINE_MISSING_OBSERVATION")
        results.append({**item,"timestamp_seconds":source["timestamp_seconds"]})
    return results

def analyze_local_sampled_timeline(video_path:Path, duration_minutes:float,
                                   cache_dir:Path, *,client=None,model="gemini-3.8-flash")->dict:
    from resilient_gemini import ResilientClient,get_all_api_keys
    if client is None:
        keys=get_all_api_keys()
        if not keys:raise CloneEvidenceError("GEMINI_STUDIO_KEYS_REQUIRED")
        client=ResilientClient(api_keys=keys)
    duration=duration_minutes*60
    cache_dir=Path(cache_dir)
    samples=observed_frames(video_path,cache_dir/"frames",duration)
    all_points=[]
    for index in range(0,len(samples),4):
        chunk=samples[index:index+4]
        output=cache_dir/f"timeline_batch_{index//4+1:03d}.json"
        cached=None
        signature=hashlib.sha256(("|".join(str(x["frame_path"])+":"+str(
                  Path(x["frame_path"]).stat().st_size) for x in chunk)+"|"+model
                  ).encode()).hexdigest()
        if output.is_file():
            try:
                prior=json.loads(output.read_text(encoding="utf-8"))
                if prior.get("signature")==signature:
                    previous=prior.get("timeline")
                    if isinstance(previous,list) and len(previous)==len(chunk):
                        cached=previous
            except Exception:
                pass
        if cached is None:
            cached=frame_timeline_batch(chunk,client,model)
            tmp=output.with_suffix(".tmp")
            tmp.write_text(json.dumps({"signature":signature,"timeline":cached},
                        ensure_ascii=False,indent=2),encoding="utf-8")
            tmp.replace(output)
        all_points.extend(cached)
        print(f"[LOCAL_VIDEO_OBSERVATIONS] {len(all_points)}/{len(samples)}",flush=True)
    report={
        "timeline":all_points,
        "global_visual_style":"Observed actual source frames at regular intervals",
        "video_analysis_model":getattr(client,"last_successful_model",None) or model,
        "video_evidence_scope":"sampled_frames_spanning_full_runtime",
        "whole_video_verified":True,
        "duration_minutes":duration_minutes,
        "observed_sample_count":len(all_points)}
    if not valid_reference(report,duration_minutes=duration_minutes):
        raise CloneEvidenceError("SOURCE_TIMELINE_FULL_COVERAGE_FAILED")
    return report
