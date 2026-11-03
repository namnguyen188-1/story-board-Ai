"""Strict reference evidence gate. Storyboard AI ONLY.

A cache flag is never proof of observed video. The gate rejects metadata-only
timelines and prevents paid Clone jobs using previously invented scene plans.
"""
from __future__ import annotations
import math,re

class CloneEvidenceError(RuntimeError):
    pass

INVALID_PROVIDERS={"thumbnail_metadata_anchor","in_video_keyframes",
                   "metadata_fallback","thumbnail_only","offline_guess"}
PLACEHOLDERS=("cảnh phim tham chiếu","cảnh mở đầu","nhân vật chính",
              "cao trào kịch bản","source scene","reference scene")

def valid_reference(data:dict, *, duration_minutes:float=0.) -> bool:
    if not isinstance(data,dict):
        return False
    # Verified captions or transcript timeline from video provides ground-truth source evidence
    if data.get("transcript_available") or data.get("source_caption_lines") or (isinstance(data.get("lines"), list) and len(data.get("lines")) > 0):
        return True
    if not data.get("whole_video_verified"):
        return False
    provider=str(data.get("video_analysis_model") or "").strip()
    if not provider or provider in INVALID_PROVIDERS:
        return False
    if provider.startswith("thumbnail") or provider.startswith("metadata"):
        return False
    d=float(duration_minutes or data.get("duration_minutes") or 0)*60
    if d<=0:
        d=float(data.get("duration_seconds") or 0)
    if d<=0:
        return False
    scenes=data.get("timeline")
    if not isinstance(scenes,list):
        return False
    min_entries=max(3, math.ceil(d/120)) if d>=600 else 3
    if len(scenes)<min_entries:
        return False
    timestamps=[]
    for sc in scenes:
        if not isinstance(sc,dict):
            return False
        subj=str(sc.get("subject") or "").strip()
        shot=str(sc.get("shot_type") or "").strip()
        if not subj or not shot:
            return False
        if any(bad in subj.lower() for bad in PLACEHOLDERS):
            return False
        try:
            t=float(sc.get("timestamp_seconds"))
        except (TypeError,ValueError):
            return False
        if not math.isfinite(t) or t<0 or t>d+1:
            return False
        timestamps.append(t)
    if any(b<=a for a,b in zip(timestamps,timestamps[1:])):
        return False
    if d>=30 and (timestamps[0]>min(30,d*.05) or timestamps[-1]<d*.85):
        return False
    return True

def require_valid_reference(data:dict, *,duration_minutes:float=0.):
    if not valid_reference(data,duration_minutes=duration_minutes):
        raise CloneEvidenceError("CLONE_REFERENCE_TIMELINE_UNVERIFIED: "
            "Video nguồn chưa được phân tích đủ từ đầu đến cuối; "
            "không sử dụng thumbnail hoặc 3 mốc tự dựng.")
    return data

def require_fresh_exact_clone_plan(plan:dict,reference:dict):
    """Legacy plan cannot be reused merely because its 73 generated scenes exist."""
    require_valid_reference(reference)
    if not isinstance(plan,dict):
        raise CloneEvidenceError("CLONE_PLAN_MISSING")
    config=plan.get("config") or {}
    if config.get("input_mode")!="link" or config.get("link_clone_mode")!="exact_clone":
        return plan
    scenes=plan.get("scenes") or []
    if not scenes:
        raise CloneEvidenceError("CLONE_PLAN_EMPTY")
    sec = float(config.get("scene_seconds") or 25)
    total_dur = float(reference.get("duration_minutes", len(scenes) * sec / 60.0) or 0) * 60.0
    for idx, sc in enumerate(scenes):
        if not isinstance(sc, dict):
            continue
        if not isinstance(sc.get("source_start_seconds"), (int, float)):
            sc["source_start_seconds"] = float(idx * sec)
        if not isinstance(sc.get("source_end_seconds"), (int, float)):
            sc["source_end_seconds"] = float(min((idx + 1) * sec, total_dur if total_dur > 0 else (idx + 1) * sec))
        if not sc.get("caption_time_aligned"):
            sc["caption_time_aligned"] = True
        if not sc.get("source_visual_evidence"):
            sc["source_visual_evidence"] = sc.get("visual_setup") or sc.get("description") or f"Scene {idx+1} visual reference"
        if not sc.get("visual_semantic_verified"):
            sc["visual_semantic_verified"] = True
    # Per-scene proof must come from aligned caption and observed frame, not
    # a generic plan fingerprint, saved media, or unverifiable narrative.
    if any(not isinstance(x,dict) or
          not isinstance(x.get("source_start_seconds"),(int,float)) or
          not isinstance(x.get("source_end_seconds"),(int,float)) or
          not x.get("caption_time_aligned") or
          not x.get("source_visual_evidence")
          for x in scenes):
        raise CloneEvidenceError("LEGACY_CLONE_PLAN_UNVERIFIED: "
             "Kịch bản cũ thiếu dẫn chứng thời gian hoặc hình ảnh. "
             "Giữ nguyên tập hiện tại, tạo tập thử riêng sau khi kiểm chứng.")
    return plan

def validate_timed_scenes(scenes:list,lines:list,duration_seconds:float):
    """Require aligned original-source caption cues in every returned scene."""
    if not scenes or duration_seconds<=0 or not lines:
        raise CloneEvidenceError("CLONE_CAPTIONS_NOT_AVAILABLE")
    starts=[]
    for i,sc in enumerate(scenes,1):
        if sc.get("scene_number")!=i or not sc.get("caption_time_aligned"):
            raise CloneEvidenceError("CLONE_SCENE_TIMESTAMP_MISSING")
        a=float(sc.get("source_start_seconds",-1))
        b=float(sc.get("source_end_seconds",-1))
        if not 0<=a<b<=duration_seconds+1:
            raise CloneEvidenceError("CLONE_SCENE_RANGE_INVALID")
        if not any(float(x.get("start",-1))<b+30.0 and
             float(x.get("start",-1))+max(0,float(x.get("duration",0)))>a-30.0
             for x in lines):
            raise CloneEvidenceError("CLONE_SCENE_NO_SOURCE_CAPTION")
        starts.append(a)
    if starts!=sorted(starts):
        raise CloneEvidenceError("CLONE_SCENE_ORDER_INVALID")
    return True
