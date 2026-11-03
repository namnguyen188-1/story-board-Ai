"""Single-scene Muse canary, one revised prompt, no account cascade."""
import json,os,sys,subprocess
from pathlib import Path
ROOT=Path(r"D:\STORYBOARD_AI\studio")
EP=ROOT/"productions"/"ho-t-h-nh-3d"/"episode_001"
sys.path.insert(0,str(ROOT))
from cinematic_engine.drama_skill9 import build_scene
from cinematic_engine.drama_auto_repair import arm_one_repair,load_armed_repair
from muse_video_provider import make_scene_media
import muse_accounts
cmd="@((Get-CimInstance Win32_Process | Where-Object { $_.Name -like 'python*' -and $_.CommandLine -like '*pipeline_router.py*' })).Count"
count=int(subprocess.check_output(["powershell","-NoProfile","-Command",cmd],timeout=10).decode().strip())
assert count==0,"A separate user production job is active"
raw=json.loads((EP/"drama_plan.json").read_text(encoding="utf-8"))
n=63
scene=dict(raw["scenes"][n-1])
prev=raw["scenes"][n-2]
scene["raw_9_fields"]=build_scene(scene,raw.get("cast",{}),prev,
    genre="animation",visual_style="color_animation",language="Vietnamese",aspect="9:16",seconds=10,index=n)
sd=EP/"scenes"/"scene_0063"
assert not (sd/"muse_clip.mp4").exists()
if (sd/"muse_scene_repair.json").is_file():
    assert load_armed_repair(sd,scene)
else:
    receipt=json.loads((sd/"muse_job.json").read_text(encoding="utf-8"))
    assert receipt.get("state")=="failed" and receipt.get("terminal_reason")=="no_video_after_completion"
    assert arm_one_repair(sd,scene,"MUSE_SCENE_REVIEW_REQUIRED: no video on confirmed completed remote session")
print("REVISED_9_FIELDS_SAVED_SCENE_63",flush=True)
bible={"production_genre":"animation","visual_style":"color_animation",
       "world":raw.get("logline",""),
       "characters":[{"name":name,"appearance":(profile.get("appearance_lock") or profile.get("appearance") or "")}
                     for name,profile in raw.get("cast",{}).items() if isinstance(profile,dict)]}
request={"scene_number":n,"description":scene.get("summary",""),
         "visual_setup":scene.get("visual_setup",""),
         "prompt":scene.get("visual_setup",""),
         "camera":scene.get("camera_motion",""),
         "dialogue":"; ".join(f"{b.get('speaker')}: {b.get('text')}" for b in scene.get("dialogue_beats",[]) if isinstance(b,dict)),
         "raw_9_fields":scene["raw_9_fields"]}
print("SENDING_ONE_REVISED_SCENE_ONLY",flush=True)
output=make_scene_media(scene=request,bible=bible,output_image_path=sd/"scene_base.png",width=720,height=1280,duration=10)
print("MUSE_SCENE_63_CANARY_OK",bool((sd/"muse_clip.mp4").is_file()),flush=True)
