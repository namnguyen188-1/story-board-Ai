"""One actual Muse I2V for approved THIEN SU scene 1; no auto publish or extra scenes."""
import sys,json,traceback,time
from pathlib import Path
sys.path.insert(0,r"D:\STORYBOARD_AI\studio")
from cinematic_engine.drama_asset_first import bind_scene,validate_assets,atomic_write
from cinematic_engine.drama_video_engine import DramaVideoEngine
from cinematic_engine.drama_schema import CharacterProfile
ep=Path(r"D:\STORYBOARD_AI\studio\productions\THI-N-S-HUY-N-PH-TR-N-QU\episode_001")
folder=ep/"scenes"/"scene_0001"
report=folder/"video_i2v_smoke_20261031.json"
if report.is_file():raise RuntimeError("VIDEO_SMOKE_PREVIOUSLY_ATTEMPTED_DO_NOT_DUPLICATE")
plan=json.loads((ep/"drama_plan.json").read_text(encoding="utf-8"))
scene=plan["scenes"][0]
assert validate_assets(ep)["status"]=="READY"
bind_scene(ep,scene,verify_scene_image=True)
cast={}
for name,details in plan["cast"].items():
 if name=="Narrator":continue
 cast[name]=CharacterProfile(name=name,
   gender=details.get("gender","female"),role=details.get("role","supporting"),
   voice_id=details.get("voice_id","Aoede"),voice_label=details.get("voice_label",""),
   appearance_lock=details.get("appearance_lock") or details.get("appearance",""),
   attire=details.get("attire",""))
audit={"status":"VIDEO_ATTEMPT_IN_PROGRESS_NO_RESUBMIT","scene":1,"provider":"muse_video"}
atomic_write(report,audit)
try:
 print("MUSE_TRUE_I2V_SCENE_01_START",flush=True)
 result=DramaVideoEngine(fps=24).render_scene(
  scene,folder,aspect_ratio="16:9",cast_map=cast,
  reference_image_path=ep/"00_ASSET_PACK"/"characters"/"luc_thanh_y"/"front.png",
  image_provider="muse_video",bible={"language":"Vietnamese","cast":plan["cast"]},
  width=1280,height=720,subtitle_style="karaoke_viral",subtitle_size=58,no_subtitles=False)
 output=Path(result["final_video_path"])
 audit.update(status="REAL_VIDEO_CREATED_PENDING_VISUAL_QC",file=str(output),bytes=output.stat().st_size,
             raw_muse_file_exists=(folder/"muse_clip.mp4").is_file())
 print("MUSE_TRUE_I2V_SCENE01_COMPLETE",json.dumps(audit,ensure_ascii=False),flush=True)
except Exception as err:
 audit.update(status="FAILED_OR_PENDING_NO_AUTO_RESUBMIT",error=str(err),trace=traceback.format_exc()[-1600:])
 print("MUSE_TRUE_I2V_SCENE01_BLOCKED",type(err).__name__,str(err)[:450],flush=True)
finally:
 atomic_write(report,audit)
