import sys,json,copy
from pathlib import Path
sys.path.insert(0,r"D:\STORYBOARD_AI\studio")
from muse_asset_images import generate_sheet
ep=Path(r"D:\STORYBOARD_AI\studio\scratch\multi_role_asset_first_e2e\episode_006")
m=json.loads((ep/"00_ASSET_PACK"/"asset_bible.json").read_text(encoding="utf-8"))
item=copy.deepcopy(m["characters"]["minh"])
item["folder"]="characters/minh_repair_fullbody_01"
for key,obj in item["views"].items():
 obj["path"]=str(ep/"00_ASSET_PACK"/item["folder"]/(key+".png"))
try:
 r=generate_sheet(item,"characters",ep,timeout_s=240)
 print("MINH_SINGLE_TARGETED_REPAIR",json.dumps(r,ensure_ascii=False),flush=True)
except Exception as e:
 print("MINH_TARGETED_REPAIR_PENDING_OR_FAILED",str(e),flush=True)
