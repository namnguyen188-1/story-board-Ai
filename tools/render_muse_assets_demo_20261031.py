from pathlib import Path
import json,sys,traceback
sys.path.insert(0,r"D:\STORYBOARD_AI\studio")
from muse_asset_images import generate_sheet
from cinematic_engine.drama_asset_first import validate_assets
ep=Path(r"D:\STORYBOARD_AI\studio\scratch\multi_role_asset_first_e2e\episode_001")
m=json.loads((ep/"00_ASSET_PACK"/"asset_bible.json").read_text(encoding="utf-8"))
for kind in ("locations","props"):
 for key,asset in m[kind].items():
  try:
   print("MUSE_ASSET_GENERATE",kind,key,flush=True)
   res=generate_sheet(asset,kind,ep,timeout_s=150)
   print("MUSE_ASSET_GENERATED",kind,key,res["status"],flush=True)
  except Exception as exc:
   print("MUSE_ASSET_BLOCKED",kind,key,str(exc),flush=True)
print("ASSET_QC",json.dumps(validate_assets(ep,m),ensure_ascii=False),flush=True)
