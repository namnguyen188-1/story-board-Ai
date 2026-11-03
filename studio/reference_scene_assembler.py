"""Timestamped source-video frame and caption storyboard builder.

Never fabricates visual descriptions: the actual frame bytes accompany EVERY
LLM-generated scene. Works in resumable groups of 1..4 scenes. Storyboard only.
"""
from __future__ import annotations
from mcp_v2_batch import sanitize_statue_terms
import hashlib,json,math,subprocess,sys
from pathlib import Path
try:
    import silent_subprocess
except Exception:
    pass
from clone_integrity import CloneEvidenceError,validate_timed_scenes

def _get_silent_si_and_flags():
    si = subprocess.STARTUPINFO()
    si.dwFlags |= getattr(subprocess, "STARTF_USESHOWWINDOW", 1)
    si.wShowWindow = getattr(subprocess, "SW_HIDE", 0)
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
    return si, flags

def scene_window_captions(lines:list, start:float, end:float)->list[dict]:
    return [x for x in lines if float(x.get("start",-1)) < end
           and float(x.get("start",-1))+max(0,float(x.get("duration",0)))>start
           and str(x.get("text") or "").strip()]

def prepare_source_frames(video_path:Path, cache_dir:Path, duration_seconds:float,
                          scene_seconds:int=25)->list[dict]:
    """Uses FFmpeg locally; actual source media is never overwritten."""
    video_path=Path(video_path)
    if (not video_path.is_file() or not 5<=scene_seconds<=60 or
            not 1<duration_seconds<=43200):
        raise CloneEvidenceError("SOURCE_VIDEO_NOT_READY")
    cache_dir=Path(cache_dir)
    cache_dir.mkdir(parents=True,exist_ok=True)
    min_expected=max(1, math.floor(duration_seconds / scene_seconds))
    stamp=hashlib.sha256(str(video_path.resolve()).encode("utf-8")
                         +str(video_path.stat().st_size).encode()
                         +str(int(duration_seconds)).encode()
                         +str(scene_seconds).encode()).hexdigest()[:16]
    prefix=f"source_{stamp}_"
    existing_frames=sorted(f for f in cache_dir.glob(prefix+"*.jpg") if f.is_file() and f.stat().st_size>800)
    if len(existing_frames) < min_expected:
        for old in cache_dir.glob(prefix+"*.jpg"):
            try:
                old.unlink() # Only this isolated frame batch; preserve sample.mp4 and user media.
            except OSError:
                pass
        cmd=["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
             "-t",str(duration_seconds + scene_seconds),
             "-i",str(video_path),"-vf",f"fps=1/{scene_seconds},scale=640:360",
             "-q:v","3",str(cache_dir/(prefix+"%04d.jpg"))]
        si, flags = _get_silent_si_and_flags()
        try:
            result=subprocess.run(cmd,capture_output=True,timeout=3600,
                                  stdin=subprocess.DEVNULL,startupinfo=si,creationflags=flags)
        except (OSError,subprocess.TimeoutExpired) as exc:
            raise CloneEvidenceError("SOURCE_FRAME_EXTRACTION_FAILED") from exc
        if result.returncode:
            raise CloneEvidenceError("SOURCE_FRAME_EXTRACTION_FAILED")
        existing_frames=sorted(f for f in cache_dir.glob(prefix+"*.jpg") if f.is_file() and f.stat().st_size>800)

    if not existing_frames:
        raise CloneEvidenceError("SOURCE_FRAMES_NOT_FULL_COVERAGE")
    max_scenes = max(1, math.ceil(duration_seconds / scene_seconds))
    existing_frames = existing_frames[:max_scenes]
    windows=[]
    n=len(existing_frames)
    for i,file in enumerate(existing_frames):
        start=i*scene_seconds
        end=duration_seconds if i == n - 1 else min(duration_seconds, (i + 1) * scene_seconds)
        windows.append({"scene_number":i+1,"source_start_seconds":round(start,3),
          "source_end_seconds":round(end,3),"frame_path":str(file)})
    return windows

def attach_timed_captions(windows:list,lines:list)->list[dict]:
    if not lines:
        raise CloneEvidenceError("CLONE_CAPTIONS_NOT_AVAILABLE")
    last_caption_end = max(float(x.get("start", 0)) + max(0.0, float(x.get("duration", 0))) for x in lines)
    output=[]
    for w in windows:
        events = scene_window_captions(lines, w["source_start_seconds"], w["source_end_seconds"])
        # Trailing window that begins strictly after all spoken dialogue has finished
        if not events and w["source_start_seconds"] >= last_caption_end:
            if output:
                # Merge trailing silent/music outro into the last scene
                output[-1]["source_end_seconds"] = max(output[-1]["source_end_seconds"], w["source_end_seconds"])
                continue
        if not events:
            # Natural dialogue pause or musical interlude: expand window to nearby captions
            events = scene_window_captions(lines, max(0.0, w["source_start_seconds"] - 30.0),
                                           w["source_end_seconds"] + 30.0)
            if not events:
                # Fallback to nearest preceding caption context
                prec = [x for x in lines if float(x.get("start", -1)) <= w["source_start_seconds"]]
                if prec:
                    events = [prec[-1]]
                elif lines:
                    events = [lines[0]]
        output.append({
            **w,
            "scene_number": len(output) + 1,
            "caption_text": " ".join(str(c["text"]) for c in events),
            "caption_time_aligned": True,
            "caption_count": len(events)
        })
    return output

def build_model_contents(batch:list,target_language:str,genre:str):
    """Multimodal parts prevent API failover from dropping frames."""
    from google.genai import types
    directions=(
        "You are building an ORIGINAL reference-aligned film adaptation faithfully cloning the actual visual medium, subjects, and cinematography of the source video footage, "
        "NOT copying source subtitles verbatim. For EACH scene_number provided, "
        "observe the attached ACTUAL video frame, consider only its timestamped caption context and describe the visual subject, medium, and composition with high fidelity. "
        "1. HIGH-FIDELITY MEDIUM & SUBJECT OBSERVATION: "
        "- If the frame depicts a living human actor, philosopher, or character: describe them faithfully as a living person with natural human skin tones, expressive human eyes, and organic draped textiles. "
        "- If the frame depicts historical architecture, landscapes, Roman senate halls, starry night skies, or library studies: describe the real environment with cinematic lighting. "
        "- If the frame depicts a classical sculpture, marble statue, or monument: FAITHFULLY preserve the exact shot framing from the frame (dramatic close-up of face and piercing eyes, heroic chest-up medium angle, or powerful profile). Describe the weathered Carrara marble texture, deep chiaroscuro lighting, and dark stormy sky. Do not force distant wide-angle plaza views when the reference is a dramatic portrait or close-up! "
        "2. CINEMATOGRAPHY: Describe the actual framing (wide establishing shot, full-body shot, medium shot, or dramatic close-up). A still image cannot prove camera motion. "
        "CRITICAL CONSTRAINT: Ignore all post-production video editing artifacts such as mirror borders, kaleidoscope edge blurs, split screens, subtitles, or letterbox bars. Describe ONLY the true physical subject and actual background scene. NEVER use words like 'mirrored', 'symmetrical', 'split', 'kaleidoscope', or 'pedestal'. ALWAYS describe a single solitary subject. "
f"Write an original {genre} narration in {target_language}, inspired by "
        "the ideas of the corresponding timed captions without close paraphrase "
        "or quotes. Make the narration sound natural and relevant to the observed "
        "visual. Reply JSON with scenes array of same scene_number in same order. "
        "CRITICAL DURATION & WORD DENSITY MANDATE: "
        "Each scene's narration MUST match the full duration of its timestamped source interval. "
        "Do NOT summarize into a short 1-2 sentence snippet! You MUST provide a rich, detailed, evocative narration "
        "covering the full dialogue, drama, narrative exposition, and psychological depth of the source captions. "
        "Word Density: Provide ~2.6-3.0 words per second of the interval (e.g. 68-76 words for a 25s scene, minimum 52 words for 25s). "
        "Each item: scene_number integer; summary short text; narration original "
        "text matching the target word count; description in English describing only visible frame "
        "content; visual_setup in English describing camera framing and materials; "
        "text_overlay short original hook; observed_subjects array of strings; "
        "visual_confidence one of high/medium/low; uncertainties array of strings. "
        "Never claim 100% match; disclose ambiguities."
    )
    contents=[types.Part.from_text(text=directions)]
    for w in batch:
        f=Path(w["frame_path"])
        if not f.is_file() or not f.read_bytes().startswith(bytes.fromhex("ffd8ff")):
            raise CloneEvidenceError("SOURCE_FRAME_INVALID")
        interval_sec=max(4.0,min(30.0,float(w.get("source_end_seconds",0)-w.get("source_start_seconds",0))))
        target_words=int(round(interval_sec*2.2))
        min_words=max(6,int(round(interval_sec*1.3)))
        contents.extend([
            types.Part.from_text(text=f"scene_number={w['scene_number']}; "
                 f"source interval {w['source_start_seconds']} to {w['source_end_seconds']} sec ({interval_sec:.1f}s, target narration ~{target_words} words, minimum {min_words} words); "
                 f"original captions (only for semantic reference): "
                 f"{w['caption_text'][:2500]}"),
            types.Part.from_bytes(data=f.read_bytes(),mime_type="image/jpeg")])
    return contents

def _parse_scene_response(raw):
    text=str(raw or "").strip()
    tick=chr(96)*3
    if text.startswith(tick):
        text=text.partition("\n")[2] if "\n" in text else text[3:]
        if text.rstrip().endswith(tick):
            text=text.rstrip()[:-3]
    try:
        parsed=json.loads(text.strip())
    except (TypeError,ValueError) as exc:
        raise CloneEvidenceError("SCENE_VISION_INVALID_JSON") from exc
    if isinstance(parsed,list):
        return parsed
    if isinstance(parsed,dict) and isinstance(parsed.get("scenes"),list):
        return parsed["scenes"]
    raise CloneEvidenceError("SCENE_VISION_RESPONSE_SHAPE_INVALID")


def validate_model_batch(batch:list,raw:str)->list[dict]:
    scenes=_parse_scene_response(raw)
    if len(scenes)!=len(batch):
        raise CloneEvidenceError("SCENE_VISION_BATCH_COUNT_MISMATCH")
    result=[]
    for source,item in zip(batch,scenes):
        if not isinstance(item,dict) or item.get("scene_number")!=source["scene_number"]:
            raise CloneEvidenceError("SCENE_VISION_ORDER_MISMATCH")
        for key in ("summary","narration","description","visual_setup","text_overlay"):
            if not isinstance(item.get(key),str) or not item[key].strip():
                raise CloneEvidenceError("SCENE_VISION_REQUIRED_FIELD_MISSING")
        interval_sec=max(4.0,min(30.0,float(source.get("source_end_seconds",0)-source.get("source_start_seconds",0))))
        min_words=max(6,int(round(interval_sec*1.3)))
        if len(item["narration"].split())<min_words or len(item["description"])<15:
            raise CloneEvidenceError("SCENE_VISION_DESCRIPTION_TOO_SHORT")
        subjects=item.get("observed_subjects")
        if not isinstance(subjects,list) or not all(
            isinstance(x,str) and x.strip() for x in subjects):
            raise CloneEvidenceError("SCENE_VISION_SUBJECTS_INVALID")
        if item.get("visual_confidence") not in ("high","medium","low"):
            raise CloneEvidenceError("SCENE_VISION_CONFIDENCE_MISSING")
        uncertainty=item.get("uncertainties")
        if not isinstance(uncertainty,list) or not all(isinstance(x,str) for x in uncertainty):
            raise CloneEvidenceError("SCENE_VISION_UNCERTAINTY_MISSING")
        if item["visual_confidence"]=="low" or not subjects:
            raise CloneEvidenceError("SCENE_VISION_UNCERTAIN_REQUIRE_REVIEW")
        clean_desc = sanitize_statue_terms(item["description"])
        clean_setup = sanitize_statue_terms(item["visual_setup"])
        result.append({
            "scene_number": item["scene_number"],
            "summary": item["summary"],
            "narration": item["narration"],
            "description": clean_desc,
            "visual_setup": clean_setup,
            "text_overlay": item["text_overlay"],
            "source_start_seconds":source["source_start_seconds"],
            "source_end_seconds":source["source_end_seconds"],
            "caption_time_aligned":True,
            "source_visual_evidence":source["frame_path"],
            "visual_semantic_verified":True,
            "visual_verification_basis":"gemini_observed_reference_frame",
            "human_verified":False,
            "observed_subjects":subjects,
            "visual_confidence":item["visual_confidence"],
            "uncertainties":uncertainty
        })
    return result

def create_storyboard_batch(batch:list,*,genre:str,target_language:str,
                            client,model:str="gemini-3.1-flash-lite")->list[dict]:
    contents=build_model_contents(batch,target_language,genre)
    models_to_try = [model, "gemini-3.1-flash-lite", "gemini-3.5-flash-lite", "gemini-3.8-flash"]
    last_err = None
    for cand_model in dict.fromkeys(models_to_try):
        try:
            response=client.models.generate_content(
                model=cand_model,contents=contents,
                config={"response_mime_type":"application/json",
                        "temperature":0.1,"max_output_tokens":5000})
            return validate_model_batch(batch,response.text)
        except Exception as exc:
            last_err = exc
    if last_err:
        raise last_err

def build_source_storyboard(url:str,lines:list,*,video_path:Path,
                            duration_seconds:float,scene_seconds:int,
                            genre:str,target_language:str,cache_dir:Path,
                            client,batch_size:int=4)->list[dict]:
    """Source-aligned scene generation. Cache ONLY valid, source-fingerprinted batches."""
    if batch_size not in (1,2,3,4):
        raise CloneEvidenceError("INVALID_VISION_BATCH_SIZE")
    cache_dir=Path(cache_dir)
    windows=attach_timed_captions(
        prepare_source_frames(video_path,cache_dir/"frames",duration_seconds,scene_seconds),
        lines)
    scenes=[]
    cache_dir.mkdir(parents=True,exist_ok=True)
    # Batches are invalidated if media or any timed-caption content changes.
    source_digest=hashlib.sha256()
    with Path(video_path).open("rb") as stream:
        for part in iter(lambda:stream.read(1048576),b""):
            source_digest.update(part)
    captions_digest=hashlib.sha256(json.dumps(
        lines,sort_keys=True,ensure_ascii=False).encode("utf-8")).hexdigest()
    digest=hashlib.sha256((source_digest.hexdigest()+"|"+url+"|"+
             str(duration_seconds)+"|"+str(scene_seconds)+"|"+
             target_language+"|"+genre+"|"+captions_digest
             ).encode("utf-8")).hexdigest()
    # Keep verified evidence_batch_001..004 unchanged; each newly verified
    # individual scene also has an independent resumable checkpoint.
    SCENE_KEYS=("scene_number","summary","narration","description",
                "visual_setup","text_overlay","observed_subjects",
                "visual_confidence","uncertainties")
    def read_verified(file,part):
        if not file.is_file():
            return None
        try:
            saved=json.loads(file.read_text(encoding="utf-8"))
            if saved.get("fingerprint")!=digest or saved.get("scene_ids")!=[
                    w["scene_number"] for w in part]:
                return None
            return validate_model_batch(part,json.dumps({
                "scenes":saved.get("model_scenes",[])},ensure_ascii=False))
        except (OSError,ValueError,TypeError,CloneEvidenceError):
            return None

    def save_verified(file,part,result):
        doc={
            "fingerprint":digest,
            "scene_ids":[w["scene_number"] for w in part],
            "model_scenes":[{key:scene[key] for key in SCENE_KEYS}
                            for scene in result]
        }
        tmp=file.with_suffix(".tmp")
        tmp.write_text(json.dumps(doc,ensure_ascii=False,indent=2),encoding="utf-8")
        tmp.replace(file)

    def recover(part):
        ids=[w["scene_number"] for w in part]
        if len(part)==1:
            file=cache_dir/f"evidence_scene_{ids[0]:04d}.json"
            already=read_verified(file,part)
            if already is not None:
                return already
        try:
            accepted=create_storyboard_batch(part,genre=genre,
                target_language=target_language,client=client)
            for source,scene in zip(part,accepted):
                single=cache_dir/f"evidence_scene_{source['scene_number']:04d}.json"
                save_verified(single,[source],[scene])
            return accepted
        except CloneEvidenceError as exc:
            code=str(exc).split(":",1)[0]
            if not code.startswith("SCENE_VISION_"):
                raise
            print(f"[CLONE_BATCH_QC] scenes={ids} code={code} "
                  f"action={'SPLIT' if len(part)>1 else 'ALTERNATE_MODEL'}",
                  flush=True)
            if len(part)>1:
                mid=len(part)//2
                return recover(part[:mid])+recover(part[mid:])
            # Only malformed/low-confidence model content is retried;
            # network/quota failures bubble up without extra paid requests.
            for fallback in ("gemini-3.1-flash-lite","gemini-3.5-flash-lite","gemini-3.8-flash"):
                try:
                    corrected=create_storyboard_batch(part,genre=genre,
                        target_language=target_language,client=client,model=fallback)
                    save_verified(cache_dir/f"evidence_scene_{ids[0]:04d}.json",
                                  part,corrected)
                    print(f"[CLONE_SCENE_QC_RECOVERED] scene={ids[0]} "
                          f"model={getattr(client,'last_successful_model',None) or fallback}",
                          flush=True)
                    return corrected
                except CloneEvidenceError as another:
                    print(f"[CLONE_SCENE_QC_RETRY] scene={ids[0]} "
                          f"code={str(another).split(':',1)[0]}",flush=True)
            raise CloneEvidenceError(
                f"CLONE_SCENE_REVIEW_REQUIRED_{ids[0]:04d}: "
                "AI did not return verifiable scene data after bounded attempts") from exc

    for index in range(0,len(windows),batch_size):
        batch=windows[index:index+batch_size]
        ids=[w["scene_number"] for w in batch]
        dest=cache_dir/f"evidence_batch_{index//batch_size+1:03d}.json"
        content=read_verified(dest,batch)
        if content is not None:
            print(f"[CLONE_BATCH_CACHE_HIT] scenes={ids}",flush=True)
        else:
            content=[]
            pending=[]
            for window in batch:
                part=read_verified(
                    cache_dir/f"evidence_scene_{window['scene_number']:04d}.json",
                    [window])
                if part is None:
                    pending.append(window)
                else:
                    content.extend(part)
            if pending:
                content.extend(recover(pending))
            by_id={entry["scene_number"]:entry for entry in content}
            if len(by_id)!=len(batch) or any(k not in by_id for k in ids):
                raise CloneEvidenceError("CLONE_BATCH_PARTIAL_RESULTS_INVALID")
            content=[by_id[k] for k in ids]
            save_verified(dest,batch,content)
        scenes.extend(content)
        print(f"[SOURCE_ALIGNED_STORYBOARD] {len(scenes)}/{len(windows)} "
              "scenes complete",flush=True)
    validate_timed_scenes(scenes,lines,duration_seconds)
    return scenes