"""Versioned derived-media cache: rebuild old stripe clips but never image or audio."""
from pathlib import Path
import json,hashlib,time,sys
root=Path(r"D:\STORYBOARD_AI\studio")
sys.path.insert(0,str(root))
from series_studio import read_json,render_one
scene=root/"productions"/"Hand-Color-Contours-V2-E2E-Oct13-2026"/"episode_001"/"scenes"/"scene_0001"
job=scene/"job.json"
old=read_json(scene/"render_style.json")
assert old.get("visual_style")=="hand_color" and not old.get("hand_color_engine"),old
before={x:hashlib.sha256((scene/x).read_bytes()).hexdigest() for x in ("image.png","audio.wav")}
orig_hash=hashlib.sha256((scene/"silent.mp4").read_bytes()).hexdigest()
render_one(job)
state=read_json(scene/"render_style.json")
assert state["hand_color_engine"]=="contour_fill_v2_20261013",state
assert before=={x:hashlib.sha256((scene/x).read_bytes()).hexdigest() for x in before}
first_mtime=(scene/"silent.mp4").stat().st_mtime_ns
first_hash=hashlib.sha256((scene/"silent.mp4").read_bytes()).hexdigest()
render_one(job)
second_mtime=(scene/"silent.mp4").stat().st_mtime_ns
second_hash=hashlib.sha256((scene/"silent.mp4").read_bytes()).hexdigest()
assert first_mtime==second_mtime and first_hash==second_hash
assert before=={x:hashlib.sha256((scene/x).read_bytes()).hexdigest() for x in before}
print("OLD_STRIPE_CACHE_REBUILT_ONCE_PASS",flush=True)
print("SECOND_RUN_USES_CACHE_NO_EXTRA_RENDER_PASS",flush=True)
print("PAID_MCP_IMAGE_AND_SAVED_AUDIO_UNTOUCHED_PASS",flush=True)
