import sys,json,shutil
from pathlib import Path
sys.path.insert(0,"D:/STORYBOARD_AI/studio")
from cinematic_engine.drama_asset_first import validate_assets,sha,atomic_write
ep=Path("D:/STORYBOARD_AI/studio/scratch/multi_role_asset_first_e2e/episode_006")
m=json.loads((ep/"00_ASSET_PACK"/"asset_bible.json").read_text(encoding="utf-8"))
src=ep/"00_ASSET_PACK"/"characters"/"minh_repair_fullbody_01"
target=ep/"00_ASSET_PACK"/"characters"/"minh"
for v in ("front","three_quarter","side_profile","back"):
 shutil.copy2(src/(v+".png"),target/(v+".png"))
shutil.copy2(src/"muse_original_4views.png",target/"muse_original_4views.png")
for kind in ("characters","locations","props"):
 for id,item in m[kind].items():
  folder=ep/"00_ASSET_PACK"/item["folder"]
  hashes={v:sha(Path(ref["path"])) for v,ref in item["views"].items()}
  if kind=="characters" and id=="minh":
   notes="Targeted Muse repair: 4 actual distinct angles all head-to-shoe. Prior waist-cropped sheet rejected."
  elif kind=="locations":
   notes="Viewed 4 cinematic architecture perspectives; exact layout maintained at master level."
  else:notes="Viewed master 4-angle material/shape consistency. Scene-level QC still required."
  atomic_write(folder/"approval.json",{"approved":True,"spec_sha256":item["spec_sha256"],
    "view_sha256":hashes,"reviewer":"ChatGPT inspected Muse master images for isolated E2E",
    "review_scope":"six-scene staging only","notes":notes})
q=validate_assets(ep,m)
print("SEVEN_ASSET_APPROVAL_QC",json.dumps(q,ensure_ascii=False),flush=True)
assert q["status"]=="READY",q
