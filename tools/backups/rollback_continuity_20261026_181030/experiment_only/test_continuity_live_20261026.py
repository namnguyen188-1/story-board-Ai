# -*- coding: utf-8 -*-
"""Real, isolated 2-scene Muse production E2E for continuity QA."""
from pathlib import Path
import sys, json, time, hashlib, traceback
S=Path(r"D:\STORYBOARD_AI\studio")
sys.path.insert(0,str(S))
O=S/"diagnostics"/"continuity_live_QA_20261026"
O.mkdir(parents=True,exist_ok=True)
REPORT=O/"report.json"
report={"test":"Real Muse Cinematic Drama continuity E2E","status":"STARTED","scenes":[],"timestamp":time.strftime("%Y-%m-%dT%H:%M:%S")}
def save():
 REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
def describe(path):
 p=Path(path)
 return {"path":str(p),"bytes":p.stat().st_size,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()[:20]}
def note(stage,**data):
 report["stage"]=stage
 report.update(data)
 save()
 print("E2E_STAGE",stage,flush=True)
def scene(num,summary,action,dialogue):
 return {
  "scene_number":num,
  "summary":summary,
  "setting":"Sunny coastal toy repair workshop, oak workbench by one big round window",
  "visual_setup":("Premium vibrant stylized 3D animated film. Same single small blue round-bodied "
    "robot with two amber round eyes, one scratch on the left cheek plate and a yellow fabric scarf. "
    "The same antique copper lantern with a star-shaped glass window is on the same oak workbench "
    "by the workshop's large round seaside window. Sunlight from frame-left, wooden shelf on frame-right. "
    +action),
  "camera_motion":"gentle medium-shot tracking from camera-left toward the workbench",
  "characters_present":["Robot Ti"],
  "dialogue_beats":[{"speaker":"Robot Ti","text":dialogue,"action":action,"tone":"warm"}],
  "bgm_mood":"hopeful",
  "sfx_cues":["tiny_clockwork_tick"]
 }
bible={
 "production_genre":"animation",
 "genre":"animation",
 "visual_style":"premium stylized cinematic 3D animation",
 "master_setting":"Same sunlit toy-repair workshop on a quiet coast, same oak workbench and copper lantern.",
 "characters":[{"name":"Robot Ti","appearance":"small stylized 3D blue round-bodied robot, two glowing amber round eyes, single scratch on left cheek plate, yellow fabric scarf, no legs or outfit changes"}]
}
a=scene(1,"Robot Ti places a small golden gear inside the open copper lantern and carefully presses it into its socket.",
        "The robot holds the antique copper lantern steady with its left hand, inserts one little golden gear with its right hand, then watches the stationary gear settle in the socket. The lantern remains dark at the end.",
        "Bánh răng đã vào đúng chỗ rồi!")
b=scene(2,"Robot Ti continues from the inserted gear, winds the same lantern's side crank and the star glass glows.",
        "At the start the same lantern still stands dark on the workbench with the golden gear in its socket. Without moving the lantern elsewhere, Robot Ti turns the tiny crank on the lantern clockwise and watches the same star-shaped window glow gently. The yellow scarf, background, and screen direction do not change.",
        "Tốt rồi! Chiếc đèn sáng trở lại.")
try:
 from cinematic_engine.scene_continuity import continuity_instruction,extract_last_frame
 from cinematic_engine.drama_video_engine import DramaVideoEngine, get_media_duration
 from cinematic_engine.drama_orchestrator import concatenate_scene_videos
 from muse_video_provider import test_muse_connection,format_real_acting_prompt
 import shutil
 b["continuity_context"]=continuity_instruction(a,b)
 prompt=format_real_acting_prompt(b,bible)
 assert "SCENE-TO-SCENE CONTINUITY:" in prompt and "PREVIOUS SCENE EVENT:" in prompt
 assert "same" in prompt.lower()
 report["continuity_prompt_valid"]=True
 note("MUSE_CONNECTION_PREFLIGHT")
 status=test_muse_connection()
 report["muse_connection_ok"]=bool(status.get("ok"))
 save()
 if not status.get("ok"):
  raise RuntimeError("MUSE_PREFLIGHT_FAILED:"+str(status.get("status") or "not ready"))
 engine=DramaVideoEngine(fps=24)
 video_paths=[]
 for sc in [a,b]:
  k=sc["scene_number"]
  d=O/"scenes"/f"scene_{k:04d}"
  d.mkdir(parents=True,exist_ok=True)
  out=d/"scene_final.mp4"
  if not (out.is_file() and (d/"muse_clip.mp4").is_file() and out.stat().st_size>100000):
   note(f"REAL_MUSE_RENDER_SCENE_{k}")
   result=engine.render_scene(scene=sc,scene_dir=d,aspect_ratio="16:9",
       image_provider="muse_video",bible=bible,width=1280,height=720,
       no_subtitles=True,subtitle_style="none",subtitle_size=0)
   out=Path(result["final_video_path"])
  actual=get_media_duration(out)
  if out.stat().st_size < 100000 or not 4 <= actual <= 30:
   raise RuntimeError(f"SCENE_{k}_INVALID_VIDEO duration={actual},bytes={out.stat().st_size}")
  extract_last_frame(out,d/"continuity_last_frame.jpg")
  video_paths.append(out)
  report["scenes"].append({"scene":k,"duration_s":actual,**describe(out)})
  save()
 note("REAL_FILM_ASSEMBLY")
 combined=O/"episode_2_scenes_real_muse.mp4"
 concatenate_scene_videos(video_paths,combined)
 all_seconds=get_media_duration(combined)
 if combined.stat().st_size<=100000 or all_seconds<8:
  raise RuntimeError("REAL_ASSEMBLY_FAILED")
 report["film"]={"duration_s":all_seconds,**describe(combined)}
 report["status"]="PASS_REAL_MUSE_2_SCENES"
 note("PASS")
except BaseException as e:
 report["status"]="FAIL_OR_BLOCKED"
 report["error_type"]=type(e).__name__
 report["error_code"]=str(e).split(":",1)[0][:160]
 save()
 print("E2E_FAILED",report["error_code"],flush=True)
 traceback.print_exc()
 sys.exit(1)
