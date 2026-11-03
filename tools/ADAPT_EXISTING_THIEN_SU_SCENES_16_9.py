import sys,json
from pathlib import Path
sys.path.insert(0,r"D:\STORYBOARD_AI\studio")
from cinematic_engine.drama_scene_aspect import frame_to_widescreen
from cinematic_engine.drama_asset_first import atomic_write,sha
root=Path(r"D:\STORYBOARD_AI\studio\productions\THI-N-S-HUY-N-PH-TR-N-QU\episode_001\scenes")
for n in range(1,67):
 folder=root/("scene_%04d"%n)
 proof=folder/"scene_master.json"
 img=folder/"scene_master.png"
 if not (img.is_file() and proof.is_file()):
  print("IMAGE_NOT_FINISHED",n,flush=True)
  continue
 info=json.loads(proof.read_text(encoding="utf-8"))
 if info.get("aspect_adaptation"):
  print("ALREADY_ADAPTED",n,flush=True);continue
 aspect=frame_to_widescreen(img)
 info.update(aspect_adaptation=aspect,scene_image_sha256=sha(img))
 atomic_write(proof,info)
 print("SCENE_16_9_CORRECTED_AND_RESEALED",n,aspect["output_dimensions"],flush=True)
