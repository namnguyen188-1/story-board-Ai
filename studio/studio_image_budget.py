"""MCP image credit budget: no auto-increase, optional explicit reusable key visuals."""
from __future__ import annotations
import math
from pathlib import Path

class ImageBudgetError(ValueError):
    pass

def required_images(minutes, scene_seconds, scripted_scenes=None):
    if scripted_scenes is not None:
        count = len(scripted_scenes)
    else:
        try:
            m = float(minutes) if minutes is not None else 1.0
            if not math.isfinite(m) or m <= 0:
                m = 1.0
        except (ValueError, TypeError):
            m = 1.0
        try:
            seconds = int(scene_seconds) if scene_seconds is not None else 25
            if seconds <= 0:
                seconds = 25
        except (ValueError, TypeError):
            seconds = 25
        m = max(0.1, min(m, 180.0))
        if m <= 1.05 and (seconds >= 15 or seconds <= 0):
            seconds = 7
        seconds = max(4, min(seconds, 60))
        count = max(1, math.ceil(m * 60 / seconds))
    count = max(1, min(count, 1000))
    return count

def inspect_budget(scene_count, limit, policy="unique"):
    if policy not in ("unique", "reuse"):
        raise ImageBudgetError("IMAGE_VISUAL_POLICY_INVALID")
    try:
        approved = int(limit)
    except (ValueError,TypeError):
        raise ImageBudgetError("IMAGE_BUDGET_INVALID")
    if not 1 <= approved <= 1000:
        raise ImageBudgetError("IMAGE_BUDGET_INVALID")
    if not 1 <= int(scene_count) <= 1000:
        raise ImageBudgetError("IMAGE_SCENE_COUNT_OUT_OF_RANGE")
    required = int(scene_count)
    if policy == "unique" and required > approved:
        raise ImageBudgetError(
            "IMAGE_BUDGET_TOO_SMALL: %d scenes require %d unique images, current approved limit %d. "
            "Increase the limit explicitly or choose Reuse key visuals before starting."
            % (required, required, approved))
    return {"scenes":required, "approved_max":approved,
            "image_jobs":min(required,approved) if policy == "reuse" else required,
            "policy":policy}

def select_keyframes(scene_count, image_jobs):
    """Deterministic temporal anchors: first/last included, evenly distributed."""
    count = int(scene_count)
    quota = int(image_jobs)
    if not 1 <= quota <= count <= 1000:
        raise ImageBudgetError("IMAGE_KEYFRAME_MAPPING_INVALID")
    if quota == 1:
        anchors=[1]
    else:
        anchors=[1 + (k*(count-1))//(quota-1) for k in range(quota)]
    if len(set(anchors)) != quota or anchors[0] != 1:
        raise ImageBudgetError("IMAGE_KEYFRAME_MAPPING_DUPLICATE")
    mapping={str(i):min(anchors,key=lambda a:(abs(a-i),a)) for i in range(1,count+1)}
    return anchors,mapping

def cached_plan_scene_count(path, *, minutes, scene_seconds, input_mode):
    """Never read the prompt itself or trust a plan for different timing settings."""
    import json
    p=Path(path)
    if not p.is_file():
        return None
    try:
        data=json.loads(p.read_text(encoding="utf-8"))
        cfg=data["config"]
        if (float(cfg.get("minutes"))!=float(minutes)
            or int(cfg.get("scene_seconds"))!=int(scene_seconds)
            or cfg.get("input_mode")!=input_mode):
            return None
        scenes=data["scenes"]
        if not isinstance(scenes,list) or len(scenes)<1:
            return None
        if len(scenes)>1000 or int(data.get("scene_count"))!=len(scenes):
            return None
        return len(scenes)
    except (ValueError,TypeError,KeyError,OSError):
        return None
