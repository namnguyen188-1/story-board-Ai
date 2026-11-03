"""Explicit 3:2 Muse video adaptation to 16:9 WITHOUT CROPPING FACES/PROPS.
Aspect repair is marked as ADAPTED, never ORIGINAL_NATIVE_16_9; original
clip and original Muse receipt remain intact. Never submits paid Muse jobs.
"""
from __future__ import annotations
import json,os,subprocess,hashlib
from pathlib import Path
from cinematic_engine.drama_asset_first import atomic_write,sha

class UnsafeAspectRepair(ValueError):pass
def video_info(path):
 cmd=["ffprobe","-v","error","-show_entries",
      "stream=width,height,codec_type:format=duration","-of","json",str(path)]
 r=subprocess.run(cmd,capture_output=True,text=True,timeout=25)
 if r.returncode:raise UnsafeAspectRepair("FFPROBE_FAILED: "+r.stderr[:300])
 j=json.loads(r.stdout)
 video=next((s for s in j.get("streams",[]) if s.get("codec_type")=="video"),None)
 if not video:raise UnsafeAspectRepair("NO_VIDEO_STREAM")
 return int(video["width"]),int(video["height"]),float(j["format"]["duration"])

def normalize_3_2(episode_scene_dir,*,target_width=1280,target_height=720):
 scene=Path(episode_scene_dir)
 file=scene/"muse_clip.mp4"; original=scene/"muse_clip_3x2_original.mp4"
 proof=scene/"aspect_adaptation.json"
 if proof.exists() and file.is_file():
  data=json.loads(proof.read_text(encoding="utf-8"))
  if data.get("adapted_sha256")==sha(file) and original.is_file() and data.get("original_sha256")==sha(original):
   return data
  raise UnsafeAspectRepair("ASPECT_REPAIR_PROOF_CHANGED")
 source=original if original.is_file() else file
 if not source.is_file():raise FileNotFoundError(source)
 w,h,seconds=video_info(source)
 ratio=w/h
 expected=target_width/target_height
 if abs(ratio-1.5)>.04:
  raise UnsafeAspectRepair(f"ONLY_3_BY_2_REPAIR_SUPPORTED: {w}x{h}")
 if not 2<=seconds<=120:raise UnsafeAspectRepair("DURATION_INVALID")
 if target_width%2 or target_height%2:raise UnsafeAspectRepair("TARGET_NOT_EVEN")
 # Preserve *all* pixels in vertical direction; blurred side extension avoids
 # chopping heads, hands, props, or important floor/foot action.
 fw=round(target_height*ratio/2)*2
 if fw>=target_width:raise UnsafeAspectRepair("NOT_EXPECTED_PILLAR_FILL")
 filtergraph=(
  f"[0:v]split=2[bg][fg];"
  f"[bg]scale={target_width}:{target_height}:force_original_aspect_ratio=increase,"
  f"crop={target_width}:{target_height},boxblur=24:2[blur];"
  f"[fg]scale={fw}:{target_height}[main];"
  f"[blur][main]overlay=(W-w)/2:(H-h)/2:format=auto,format=yuv420p[v]")
 tmp=scene/"muse_clip_aspect_repair.part.mp4"
 cmd=["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(source),
      "-filter_complex",filtergraph,"-map","[v]","-map","0:a?",
      "-c:v","libx264","-preset","veryfast","-crf","18","-pix_fmt","yuv420p",
      "-c:a","copy","-movflags","+faststart",str(tmp)]
 r=subprocess.run(cmd,capture_output=True,text=True,timeout=210,
                  creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
 if r.returncode:
  tmp.unlink(missing_ok=True)
  raise UnsafeAspectRepair("FFMPEG_REPAIR_FAILED:"+r.stderr[-500:])
 tw,th,td=video_info(tmp)
 if (tw,th)!=(target_width,target_height) or abs(td-seconds)>.12:
  tmp.unlink(missing_ok=True)
  raise UnsafeAspectRepair("REPAIRED_VIDEO_INTEGRITY_FAILED")
 if not original.is_file():os.replace(file,original)
 os.replace(tmp,file)
 data={"status":"ASPECT_ADAPTED_NEEDS_VISUAL_QC","source":"Muse actual video",
       "method":"full-frame-preserving blurred side extension (not native widescreen)",
       "original_dimensions":[w,h],"adapted_dimensions":[tw,th],
       "duration_seconds":round(td,3),
       "original_sha256":sha(original),"adapted_sha256":sha(file),
       "original_file":str(original),"adapted_file":str(file),
       "publish_allowed":False}
 atomic_write(proof,data)
 return data
