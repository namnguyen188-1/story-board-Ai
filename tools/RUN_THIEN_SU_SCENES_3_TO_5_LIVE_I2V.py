"""Three approved THIEN SU scenes, actual Muse I2V, max two parallel.
Never duplicate an already requested Muse job; no publishing.
"""
import sys,json,traceback,concurrent.futures
from pathlib import Path
sys.path.insert(0,r"D:\STORYBOARD_AI\studio")
from cinematic_engine.drama_asset_first import bind_scene,validate_assets,atomic_write
from cinematic_engine.drama_video_engine import DramaVideoEngine
from cinematic_engine.drama_schema import CharacterProfile
ep=Path(r"D:\STORYBOARD_AI\studio\productions\THI-N-S-HUY-N-PH-TR-N-QU\episode_001")
plan=json.loads((ep/"drama_plan.json").read_text(encoding="utf-8"))
assert len(plan["scenes"])==66 and validate_assets(ep)["status"]=="READY"
cast={}
for name,c in plan["cast"].items():
 if name=="Narrator":continue
 cast[name]=CharacterProfile(name=name,gender=c.get("gender","female"),
    voice_id=c.get("voice_id","Aoede"),voice_label=c.get("voice_label",""),
    appearance_lock=c.get("appearance_lock") or c.get("appearance",""),
    attire=c.get("attire",""))
def render(n):
 sc=plan["scenes"][n-1]
 folder=ep/"scenes"/f"scene_{n:04d}"
 receipt=folder/"manual_live_i2v_production_20261031.json"
 try:
  if receipt.exists():raise RuntimeError("SCENE_ALREADY_SUBMITTED_DO_NOT_DUPLICATE")
  bind_scene(ep,sc,verify_scene_image=True)
  r={"state":"IN_PROGRESS","scene":n,"provider":"muse_video",
     "auto_upload":False,"reference_preflight":True}
  atomic_write(receipt,r)
  print("LIVE_MUSE_I2V_SCENE_START",n,flush=True)
  engine=DramaVideoEngine(fps=24)
  result=engine.render_scene(sc,folder,aspect_ratio="16:9",cast_map=cast,
     reference_image_path=ep/"00_ASSET_PACK"/"characters"/"luc_thanh_y"/"front.png",
     image_provider="muse_video",bible={"language":"Vietnamese","cast":plan["cast"]},
     width=1280,height=720,subtitle_style="karaoke_viral",subtitle_size=58,no_subtitles=False)
  output=Path(result["final_video_path"])
  r.update(state="MOVING_VIDEO_CREATED_REVIEW_PENDING",file=str(output),
      bytes=output.stat().st_size)
  print("LIVE_MUSE_I2V_SCENE_FINISHED",n,output.stat().st_size,flush=True)
 except Exception as e:
  if "r" not in locals():r={"state":"BLOCKED","scene":n}
  r.update(state="BLOCKED_NO_DUPLICATE",error=str(e),trace=traceback.format_exc()[-1600:])
  print("LIVE_MUSE_I2V_SCENE_BLOCKED",n,type(e).__name__,str(e)[:400],flush=True)
 finally:
  if "r" in locals():atomic_write(receipt,r)
 return r
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 result=list(pool.map(render,(3,4,5)))
atomic_write(ep/"approved_scene_3_5_muse_i2v_run.json",result)
print("SCENES_3_5_VIDEO_BATCH_RESULT",json.dumps([{"scene":r["scene"],"state":r["state"]} for r in result],ensure_ascii=False),flush=True)
