import concurrent.futures,json,sys,time
from pathlib import Path
sys.path.insert(0,"D:/STORYBOARD_AI/studio")
from cinematic_engine.drama_asset_first import bind_scene,validate_assets
from cinematic_engine.drama_video_engine import DramaVideoEngine
from cinematic_engine.drama_schema import CharacterProfile
ep=Path("D:/STORYBOARD_AI/studio/scratch/multi_role_asset_first_e2e/episode_006")
p=json.loads((ep/"drama_plan.json").read_text(encoding="utf-8"))
assert validate_assets(ep)["status"]=="READY"
cast={}
for name in ("Lan","Minh"):
 data=p["cast"][name]
 cast[name]=CharacterProfile(name=name,gender="female" if name=="Lan" else "male",
    appearance_lock=data["appearance_lock"],attire=data["attire"])
def one(n):
 sc=p["scenes"][n-1];folder=ep/"scenes"/("scene_%04d"%n)
 bind_scene(ep,sc,verify_scene_image=True)
 print("VIDEO_ASPECT_RECOVERY_RESUME",n,flush=True)
 anchor=ep/"00_ASSET_PACK"/"characters"/("lan" if n==3 else "minh")/"front.png"
 try:
  res=DramaVideoEngine(fps=24).render_scene(sc,folder,aspect_ratio="16:9",cast_map=cast,
    reference_image_path=anchor,image_provider="muse_video",bible={"language":"Vietnamese","cast":p["cast"]},
    width=1280,height=720,subtitle_style="karaoke_viral",subtitle_size=58,no_subtitles=False)
  file=Path(res["final_video_path"])
  print("ASPECT_RECOVERED_SCENE_COMPLETE",n,file.stat().st_size,flush=True)
  return {"scene":n,"status":"ADAPTED_MOVING_VIDEO_NEEDS_QC","path":str(file)}
 except Exception as e:
  print("ASPECT_RECOVERY_SCENE_FAILED",n,str(e),flush=True)
  return {"scene":n,"status":"BLOCKED","error":str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 results=list(pool.map(one,(3,4,6)))
(ep/"aspect_recovery_scene_report.json").write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding="utf-8")
print("ASPECT_RECOVERY_RESULT",json.dumps(results,ensure_ascii=False),flush=True)
