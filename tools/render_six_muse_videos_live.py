import concurrent.futures,json,sys,time,hashlib
from pathlib import Path
sys.path.insert(0,"D:/STORYBOARD_AI/studio")
from cinematic_engine.drama_asset_first import validate_assets,bind_scene
from cinematic_engine.drama_skill9 import export_episode
from cinematic_engine.drama_video_engine import DramaVideoEngine
from cinematic_engine.drama_schema import CharacterProfile
ep=Path("D:/STORYBOARD_AI/studio/scratch/multi_role_asset_first_e2e/episode_006")
p=json.loads((ep/"drama_plan.json").read_text(encoding="utf-8"))
assert validate_assets(ep)["status"]=="READY","ASSET_GATE_FAILED"
skill=export_episode(p,ep,genre="family_drama",visual_style="color_cinematic",language="Vietnamese",aspect="16:9",seconds=10)
assert skill["pass"],skill
print("SIX_VIDEO_SKILL_PASS",skill["scene_count"],flush=True)
for sc in p["scenes"]:
 bind_scene(ep,sc,verify_scene_image=True)
print("SIX_SCENE_IMAGE_APPROVAL_PASS",flush=True)
cast={
 "Lan":CharacterProfile(name="Lan",gender="female",voice_id="Aoede",
                         appearance_lock=p["cast"]["Lan"]["appearance_lock"],
                         attire=p["cast"]["Lan"]["attire"]),
 "Minh":CharacterProfile(name="Minh",gender="male",voice_id="Charon",
                         appearance_lock=p["cast"]["Minh"]["appearance_lock"],
                         attire=p["cast"]["Minh"]["attire"])
}
def run_scene(sc):
 n=sc["scene_number"]
 folder=ep/"scenes"/("scene_%04d"%n)
 focal="Lan" if n in (1,3,5) else "Minh"
 anchor=ep/"00_ASSET_PACK"/"characters"/focal.lower()/"front.png"
 start=time.time()
 try:
  print("MUSE_I2V_REAL_STARTED",n,flush=True)
  res=DramaVideoEngine(fps=24).render_scene(
      sc,folder,aspect_ratio="16:9",cast_map=cast,
      reference_image_path=anchor,image_provider="muse_video",
      bible={"language":"Vietnamese","cast":p["cast"]},
      width=1280,height=720,subtitle_style="karaoke_viral",
      subtitle_size=58,no_subtitles=False)
  path=Path(res["final_video_path"])
  result={"scene":n,"status":"VIDEO_FILE_CREATED_NEEDS_VISUAL_QC",
          "bytes":path.stat().st_size,"path":str(path),
          "raw_muse":str(folder/"muse_clip.mp4"),"elapsed":round(time.time()-start,1)}
  print("MUSE_I2V_REAL_COMPLETED",n,path.stat().st_size,flush=True)
  return result
 except Exception as e:
  result={"scene":n,"status":"BLOCKED_OR_FAILED","error":str(e),"elapsed":round(time.time()-start,1)}
  print("MUSE_I2V_REAL_BLOCKED",n,str(e)[:500],flush=True)
  return result
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 results=list(pool.map(run_scene,p["scenes"]))
(ep/"six_scene_video_report.json").write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding="utf-8")
print("SIX_SCENE_MUSE_VIDEO_RESULTS",json.dumps(results,ensure_ascii=False),flush=True)
