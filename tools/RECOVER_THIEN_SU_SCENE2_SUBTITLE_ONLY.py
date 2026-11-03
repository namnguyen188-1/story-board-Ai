"""Recover scene2 subtitles from existing Muse audio/video. NO Muse resubmit."""
import sys,json,traceback,hashlib
from pathlib import Path
sys.path.insert(0,r"D:\STORYBOARD_AI\studio")
from cinematic_engine.drama_asset_first import bind_scene,validate_assets,atomic_write
from cinematic_engine.drama_video_engine import DramaVideoEngine
from cinematic_engine.drama_schema import CharacterProfile
ep=Path(r"D:\STORYBOARD_AI\studio\productions\THI-N-S-HUY-N-PH-TR-N-QU\episode_001")
folder=ep/"scenes"/"scene_0002"
report=folder/"subtitle_recovery_no_new_muse_video.json"
if report.exists():raise RuntimeError("ALREADY_TRIED_NO_DUPLICATE")
job_file=folder/"muse_job.json"
job=json.loads(job_file.read_text(encoding="utf-8"))
assert job.get("state")=="complete","NO_REPLAY_UNLESS_PROVEN_COMPLETE"
video=folder/"muse_clip.mp4"
assert video.is_file() and video.stat().st_size>100000
before=hashlib.sha256(video.read_bytes()).hexdigest()
plan=json.loads((ep/"drama_plan.json").read_text(encoding="utf-8"))
scene=plan["scenes"][1]
bind_scene(ep,scene,verify_scene_image=True)
cast={}
for name,d in plan["cast"].items():
 if name=="Narrator":continue
 cast[name]=CharacterProfile(name=name,gender=d.get("gender","female"),
   voice_id=d.get("voice_id","Aoede"),voice_label=d.get("voice_label",""),
   appearance_lock=d.get("appearance_lock") or d.get("appearance",""))
result={"state":"STARTED_LOCAL_SUBTITLE_REPAIR", "prior_muse_video_sha256":before,
        "muse_video_receipt_state":"complete","muse_job_id":job.get("task_id")}
atomic_write(report,result)
try:
 print("SCENE2_REUSE_ORIGINAL_MUSE_MP4_BEGIN",flush=True)
 made=DramaVideoEngine(fps=24).render_scene(
   scene,folder,aspect_ratio="16:9",cast_map=cast,
   reference_image_path=ep/"00_ASSET_PACK"/"characters"/"luc_thanh_y"/"front.png",
   image_provider="muse_video",bible={"language":"Vietnamese","cast":plan["cast"]},
   width=1280,height=720,subtitle_style="karaoke_viral",subtitle_size=58,no_subtitles=False)
 out=Path(made["final_video_path"])
 after=hashlib.sha256(video.read_bytes()).hexdigest()
 assert after==before,"MUSE_VIDEO_SOURCE_CHANGED"
 rec=json.loads(job_file.read_text(encoding="utf-8"))
 assert rec.get("state")=="complete" and rec.get("video_remote")==job["video_remote"]
 result.update(state="LOCAL_SUBTITLE_REPAIR_PASS_ORIGINAL_MUSE_REUSED",
               output=str(out),bytes=out.stat().st_size,
               original_muse_sha256=before)
 print("SCENE2_SUBTITLES_RECOVERED_NO_MUSE_RESUBMIT",json.dumps(result,ensure_ascii=False),flush=True)
except Exception as e:
 result.update(state="BLOCKED_NO_RESUBMIT",error=str(e),trace=traceback.format_exc()[-1800:])
 print("SCENE2_SUBTITLE_RECOVERY_BLOCKED",type(e).__name__,str(e),flush=True)
finally: atomic_write(report,result)
