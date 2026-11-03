"""Preserve real Muse still, place 3:2 scenes into a verified 16:9 frame.
No face/object crop. Never pretend the underlying Muse generation was 16:9.
"""
from pathlib import Path
import os
from PIL import Image,ImageOps,ImageFilter
from cinematic_engine.drama_asset_first import sha,atomic_write

def frame_to_widescreen(scene_file:Path)->dict:
 p=Path(scene_file)
 if not p.is_file():raise FileNotFoundError(p)
 original=p.with_name("scene_master_original_3to2.png")
 proof=p.with_name("scene_master_aspect_proof.json")
 if proof.is_file():
  import json
  rec=json.loads(proof.read_text(encoding="utf-8"))
  if p.is_file() and original.is_file() and sha(p)==rec["adapted_sha256"] and sha(original)==rec["original_sha256"]:
   return rec
  raise RuntimeError("ASPECT_PROOF_CHANGED_NEEDS_REVIEW")
 with Image.open(p) as im:
  im.load();im=im.convert("RGB")
  w,h=im.size
  aspect=w/h
  if abs(aspect-16/9)<.02:
   return {"adapted":False,"native_dimensions":[w,h],"output_dimensions":[w,h]}
  if not 1.33<=aspect<=1.72:
   raise RuntimeError(f"UNEXPECTED_SCENE_ASPECT_{w}x{h}")
  th=round(w*9/16)
  if th%2:th+=1
  background=ImageOps.fit(im,(w,th),method=Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(radius=max(18,w//70)))
  fg=ImageOps.contain(im,(w,th),method=Image.Resampling.LANCZOS)
  background.paste(fg,((w-fg.width)//2,(th-fg.height)//2))
  tmp=p.with_name("scene_master_aspect_convert.part.png")
  background.save(tmp,format="PNG")
 original_sha=sha(p)
 os.replace(p,original)
 os.replace(tmp,p)
 result={"adapted":True,"method":"No-crop 16:9 blurred side-extension",
         "native_dimensions":[w,h],"output_dimensions":[w,th],
         "original_sha256":original_sha,"adapted_sha256":sha(p),
         "original_file":str(original),"output_file":str(p),
         "publish_allowed":False,"human_scene_review_required":True}
 atomic_write(proof,result)
 return result
