import json,sys,shutil,os
from pathlib import Path
sys.path.insert(0,"D:/STORYBOARD_AI/studio")
from cinematic_engine.drama_asset_first import atomic_write
ep=Path("D:/STORYBOARD_AI/studio/scratch/multi_role_asset_first_e2e/episode_006")
dir=ep/"scenes"/"scene_0001"
plan_file=ep/"drama_plan.json"
p=json.loads(plan_file.read_text(encoding="utf-8"))
p["scenes"][0]["visual_setup"]=(
"LOCK CAMERA COMPOSITION TO THE APPROVED LIVING-ROOM MASTER WIDE PHOTO. "
"EXACT ARCHITECTURE MUST NOT CHANGE: the GRAY FABRIC SOFA IS CENTERED DIRECTLY UNDER THE DOUBLE WINDOW ON THE FAR WALL; one WINDOW immediately BEHIND sofa, split in the middle, AIR CONDITIONER ABOVE WINDOW, tall BROWN DOOR ON FAR RIGHT WALL, floating SHELF right of window, RATTAN WALL HANGING on LEFT WALL, SMALL WOODEN COFFEE TABLE CENTERED directly IN FRONT OF sofa with plant and book. "
"DO NOT move sofa to the right wall or to side of window; do not add another sofa, door or window. "
"Lan stands LEFT SIDE of the centrally placed sofa, wearing SAME BEIGE COAT and DARK BURGUNDY SWEATER; she holds the SAME BLACK PHONE in LEFT HAND. "
"Full wide cinematic establishing shot, same room geometry as reference photo, photorealistic 16:9. "
"NOT a living-room redesign, not a generic alternative.")
atomic_write(plan_file,p)
for fname in ("muse_scene_image_receipt.json","scene_master.png","scene_master.json"):
 src=dir/fname
 if src.exists():
  archive=dir/("rejected_geometry_"+fname)
  if archive.exists():raise RuntimeError("Geometry repair already attempted: "+str(archive))
  os.replace(src,archive)
print("SCENE_01_TARGETED_REPAIR_STAGED",flush=True)
