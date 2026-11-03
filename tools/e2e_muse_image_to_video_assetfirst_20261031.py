import sys,json,time,traceback,subprocess
from pathlib import Path
sys.path.insert(0,r"D:\STORYBOARD_AI\studio")
sys.path.insert(0,r"D:\STORYBOARD_AI\studio\engine")
from cinematic_engine.drama_asset_first import bind_scene
from cinematic_engine.drama_skill9 import export_episode
from cinematic_engine.drama_video_engine import DramaVideoEngine
from cinematic_engine.drama_schema import CharacterProfile
ep=Path(r"D:\STORYBOARD_AI\studio\scratch\multi_role_asset_first_e2e\episode_001")
plan=json.loads((ep/"drama_plan.json").read_text(encoding="utf-8"))
scene=plan["scenes"][0]
sc_dir=ep/"scenes"/"scene_0001"
report=sc_dir/"e2e_muse_image_to_video_result.json"
start=time.time()
summary={"mode":"image_to_video","stage":"STAGING","status":"RUNNING",
 "scene_image":str(sc_dir/"scene_master.png"),"preprod_assets_ready":True}
try:
 from cinematic_engine.drama_asset_first import validate_assets
 assert validate_assets(ep)["status"]=="READY"
 binding=bind_scene(ep,scene,verify_scene_image=True)
 skill=export_episode(plan,ep,genre="family_drama",visual_style="color_cinematic",language="Vietnamese",aspect="16:9",seconds=10)
 print("SKILL9_PREFLIGHT",skill["pass"],skill["scene_count"],flush=True)
 cast={"Lan":CharacterProfile(name="Lan",gender="female",
        appearance_lock=plan["cast"]["Lan"]["appearance_lock"])}
 anchor=ep/"00_ASSET_PACK"/"characters"/"lan"/"front.png"
 result=DramaVideoEngine(fps=24).render_scene(
   scene,sc_dir,aspect_ratio="16:9",cast_map=cast,
   reference_image_path=anchor,image_provider="muse_video",
   bible={"language":"Vietnamese","cast":plan["cast"]},
   width=1280,height=720,subtitle_style="karaoke_viral",subtitle_size=58,no_subtitles=False)
 video=Path(result["final_video_path"])
 summary.update(status="VIDEO_FILE_CREATED_NEEDS_I2V_VISUAL_QC",path=str(video),
                bytes=video.stat().st_size,raw_clip_exists=(sc_dir/"muse_clip.mp4").is_file())
 print("MUSE_I2V_E2E_VIDEO_CREATED",json.dumps(summary,ensure_ascii=False),flush=True)
except Exception as e:
 summary.update(status="FAIL_OR_PROVIDER_PENDING",error=str(e),traceback=traceback.format_exc()[-2200:])
 print("MUSE_I2V_E2E_BLOCKED",type(e).__name__,str(e)[:600],flush=True)
finally:
 summary["elapsed_seconds"]=round(time.time()-start,1)
 report.write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
