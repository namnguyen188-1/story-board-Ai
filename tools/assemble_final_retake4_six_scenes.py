from pathlib import Path
import subprocess,json,sys
sys.path.insert(0,"D:/STORYBOARD_AI/studio")
from cinematic_engine.drama_aspect_repair import video_info
from cinematic_engine.drama_asset_first import atomic_write,sha
root=Path("D:/STORYBOARD_AI/studio/scratch/multi_role_asset_first_e2e/episode_006")
retake=root/"scenes"/"scene_0004_retake_no_phantom_key"/"scene_final.mp4"
assert retake.is_file()
norm=retake.with_name("scene_normalized_1280x720.mp4")
cmd=["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(retake),
     "-vf","scale=1280:720,setsar=1,fps=24","-r","24","-c:v","libx264",
     "-preset","veryfast","-crf","19","-pix_fmt","yuv420p",
     "-c:a","aac","-b:a","160k","-ar","48000","-ac","2","-movflags","+faststart",str(norm)]
p=subprocess.run(cmd,capture_output=True,text=True,timeout=130)
if p.returncode:raise RuntimeError("RETAKE_NORMALIZE_FAILED"+p.stderr[-400:])
sources=[root/"scenes"/("scene_%04d"%i)/"scene_normalized_1280x720.mp4" for i in range(1,7)]
sources[3]=norm
for i,s in enumerate(sources,1):
 if not s.is_file():raise RuntimeError("MISSING_NORMALIZED_SCENE"+str(i))
 w,h,t=video_info(s)
 if (w,h)!=(1280,720) or not 9.7<=t<=10.4:raise RuntimeError("SCENE_QC_FAILED"+str(i))
concat=root/"six_scene_concat_RETAKE4.txt"
concat.write_text("\n".join("file '"+p.as_posix()+"'" for p in sources)+"\n",encoding="utf-8")
out=root/"SIX_SCENES_MUSE_E2E_60S_RETAKE4.mp4"
cmd=["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0",
     "-i",str(concat),"-c","copy","-movflags","+faststart",str(out)]
p=subprocess.run(cmd,capture_output=True,text=True,timeout=120)
if p.returncode:raise RuntimeError("RETAKE_ASSEMBLY_FAILED"+p.stderr[-700:])
w,h,t=video_info(out)
if (w,h)!=(1280,720) or not 59.5<=t<=60.5:raise RuntimeError("BAD_FINAL_DURATION_ASPECT")
qc={"status":"SIX_REAL_MUSE_SCENES_E2E_TECHNICAL_COMPLETE_REVIEW_NEEDED",
"publish_allowed":False,"video":str(out),"duration_seconds":round(t,3),"bytes":out.stat().st_size,
"sha256":sha(out),"scene_count":6,"characters":2,"locations":2,"props":3,
"retake_scene_4":True,"retake_proof":str(root/"scenes"/"scene_0004_retake_no_phantom_key"/"aspect_adaptation.json"),
"aspect_adapted_scenes":[3,4,6],
"visual_review":"18 original frames + 3 retake frames examined; physical key handoff improved",
"speech_review":"all six native Vietnamese transcripts match respective script exact, word-timed captions",
"limitations":"3x original Muse videos 3:2 adapted with blurred side fill; human review before publish",
"preserve_old_scene_4":str(root/"scenes"/"scene_0004"/"scene_final.mp4")}
atomic_write(root/"six_scene_final_retaked_qc.json",qc)
print("SIX_SCENE_RETAKE_FINAL_TECHNICAL_PASS",json.dumps(qc,ensure_ascii=False),flush=True)
