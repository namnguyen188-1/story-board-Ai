import json,sys,os
from pathlib import Path
sys.path.insert(0,"D:/STORYBOARD_AI/studio")
from cinematic_engine.drama_asset_first import atomic_write
ep=Path("D:/STORYBOARD_AI/studio/scratch/multi_role_asset_first_e2e/episode_006")
dir=ep/"scenes"/"scene_0004"
pfile=ep/"drama_plan.json";plan=json.loads(pfile.read_text(encoding="utf-8"))
plan["scenes"][3]["visual_setup"]=(
"EXACT SAME APPROVED COMPANY OFFICE MASTER geometry: black leather office chairs, dark oak desk facing a large bright north window, brown bookcase on LEFT wall, timber office door RIGHT wall, plain white walls. "
"Camera medium two-shot of the SAME Lan in beige trench coat and burgundy turtleneck and SAME Minh in navy vest, charcoal shirt and brown apron, standing on opposite sides of the oak desk. "
"A SINGLE red dossier with gold binder clip lies ON office desk; do not add a new folder. "
"The single small brass key is COMPLETELY HIDDEN INSIDE MINH TROUSER POCKET at opening of the shot; no visible key hanging from belt, no giant key, no jewelry. "
"Natural cinematic daylight, no changes to architecture, all faces and clothing matching reference plates, no extra people.")
atomic_write(pfile,plan)
for name in ("muse_scene_image_receipt.json","scene_master.png","scene_master.json"):
 src=dir/name
 if src.exists():
  target=dir/("rejected_key_state_"+name)
  if target.exists():raise RuntimeError("Scene4 repair already attempted")
  os.replace(src,target)
print("SCENE04_PROP_VISIBILITY_REPAIR_STAGED",flush=True)
