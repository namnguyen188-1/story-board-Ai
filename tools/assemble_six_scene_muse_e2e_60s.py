"""Six real Muse scene clips -> technical 60s review movie.
Preserves original raw Muse videos, unapproved for publishing until MOVING
continuity/lip-sync/subtitles have been checked. Explicitly tags 3 adapted.
"""
from pathlib import Path
import json,sys,subprocess
sys.path.insert(0,"D:/STORYBOARD_AI/studio")
from cinematic_engine.drama_aspect_repair import video_info
from cinematic_engine.drama_asset_first import validate_assets,atomic_write
base=Path("D:/STORYBOARD_AI/studio/scratch/multi_role_asset_first_e2e/episode_006")
scenes=base/"scenes"
results=[]
assert validate_assets(base)["status"]=="READY","MASTER_ASSETS_NOT_READY"
normalized=[]
for number in range(1,7):
 folder=scenes/("scene_%04d"%number)
 orig=folder/"scene_final.mp4"
 if not orig.is_file():raise RuntimeError("SCENE_FINAL_MISSING:"+str(number))
 w,h,t=video_info(orig)
 if abs(t-10)>.12:raise RuntimeError("SCENE_LENGTH_WRONG:"+str(number))
 proof=folder/"aspect_adaptation.json"
 adapted=proof.is_file()
 if adapted:
  j=json.loads(proof.read_text(encoding="utf-8"))
  if j["status"]!="ASPECT_ADAPTED_NEEDS_VISUAL_QC":
   raise RuntimeError("ASPECT_PROOF_BAD:"+str(number))
 # Check the same scene used an approved Muse scene still before video.
 pf=json.loads((folder/"scene_master.json").read_text(encoding="utf-8"))
 if not pf.get("approved"):raise RuntimeError("SCENE_IMAGE_UNAPPROVED:"+str(number))
 target=folder/"scene_normalized_1280x720.mp4"
 cmd=["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(orig),
      "-vf","scale=1280:720,setsar=1,fps=24","-r","24","-c:v","libx264","-preset","veryfast",
      "-crf","19","-pix_fmt","yuv420p","-c:a","aac","-b:a","160k",
      "-ar","48000","-ac","2","-movflags","+faststart",str(target)]
 r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=160)
 if r.returncode:raise RuntimeError("NORMALIZATION_FAILED:"+str(number)+":"+r.stderr[-400:])
 tw,th,tt=video_info(target)
 if (tw,th)!=(1280,720) or abs(tt-t)>.15:raise RuntimeError("NORMALIZATION_QC_FAILED")
 results.append({"scene":number,"native_muse_dimensions":[w,h],"duration_s":round(t,3),
                 "aspect_adapted":adapted,"normalized_file":str(target)})
 normalized.append(target)
 print("NORMALIZED_REAL_MUSE_SCENE",number,"adapted",adapted,flush=True)
inputs=base/"six_scene_concat_inputs.txt"
inputs.write_text("\n".join("file '"+p.as_posix()+"'" for p in normalized)+"\n",encoding="utf-8")
out=base/"SIX_SCENES_MUSE_E2E_REVIEW_60S.mp4"
cmd=["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0",
     "-i",str(inputs),"-c","copy","-movflags","+faststart",str(out)]
r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=120)
if r.returncode:raise RuntimeError("EPISODE_CONCAT_FAILED:"+r.stderr[-600:])
w,h,t=video_info(out)
if not(59.5<=t<=60.5) or (w,h)!=(1280,720):raise RuntimeError("EPISODE_DURATION_OR_SIZE_INVALID")
qc={"status":"E2E_SIX_REAL_MUSE_VIDEOS_ASSEMBLED_NEEDS_MOVING_VISUAL_QC",
 "publish_allowed":False,"episode":6,"scenes":results,"video":str(out),
 "actual_duration_seconds":round(t,3),"video_bytes":out.stat().st_size,
 "aspect_adapted_count":sum(x["aspect_adapted"] for x in results),
 "note":"60s real Muse videos stitched with native audio/subtitles. 3 scenes 3:2 adapted to 16:9 with side blur; original clips/receipts preserved. No auto-publish."}
atomic_write(base/"six_scene_episode_qc.json",qc)
print("SIX_SCENE_ASSEMBLY_TECHNICAL_QC",json.dumps({k:v for k,v in qc.items() if k!="scenes"},ensure_ascii=False),flush=True)
