import sys,json
from pathlib import Path
sys.path.insert(0,r"D:\STORYBOARD_AI\studio")
from muse_scene_image import generate_scene
p=Path(r"D:\STORYBOARD_AI\studio\scratch\multi_role_asset_first_e2e\episode_001")
plan=json.loads((p/"drama_plan.json").read_text(encoding="utf-8"))
try:
 x=generate_scene(p,plan["scenes"][0],timeout_s=160)
 print("MUSE_SCENE_IMAGE_GENERATED",json.dumps({k:v for k,v in x.items() if k!="references_uploaded"},ensure_ascii=False),flush=True)
except Exception as e:
 print("MUSE_SCENE_IMAGE_FAILED_OR_PENDING",str(e),flush=True)
