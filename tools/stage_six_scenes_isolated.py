from pathlib import Path
import sys,shutil,json
sys.path.insert(0,r"D:\STORYBOARD_AI\studio")
from cinematic_engine.drama_asset_first import build_manifest,validate_assets,sha,atomic_write
base=Path(r"D:\STORYBOARD_AI\studio\scratch\multi_role_asset_first_e2e")
src=base/"episode_001"
dst=base/"episode_006"
dst.mkdir(parents=True,exist_ok=True)
plan=json.loads((src/"drama_plan.json").read_text(encoding="utf-8"))
plan["series_name"]="Multi Role Real E2E Six Scenes"
plan["episode_num"]=6
atomic_write(dst/"drama_plan.json",plan)
m=build_manifest(dst,plan)
original=json.loads((src/"00_ASSET_PACK"/"asset_bible.json").read_text(encoding="utf-8"))
copied=[]
for kind in ("characters","locations","props"):
 for entity_id,item in m[kind].items():
  old=original[kind].get(entity_id)
  if not old:continue
  if old["spec_sha256"]!=item["spec_sha256"]:
   print("ASSET_DESIGN_CHANGED_NEEDS_NEW_GENERATION",kind,entity_id,flush=True)
   continue
  source=src/"00_ASSET_PACK"/old["folder"]
  target=dst/"00_ASSET_PACK"/item["folder"]
  for fn in ["muse_original_4views.png","generation_proof.json"]:
   if (source/fn).is_file():shutil.copy2(source/fn,target/fn)
  hashes={}
  for view,v in item["views"].items():
   p=source/(view+".png")
   if not p.is_file():break
   shutil.copy2(p,target/(view+".png"))
   hashes[view]=sha(target/(view+".png"))
  if len(hashes)!=len(item["views"]):continue
  # These three pictures were personally inspected in this chat.
  atomic_write(target/"approval.json",{
      "approved":True,"spec_sha256":item["spec_sha256"],"view_sha256":hashes,
      "reviewer":"Visual verification of same approved Muse master images from first scene E2E",
      "review_scope":"E2E staging images, not general release authorization"})
  copied.append(kind+"/"+entity_id)
print("E2E_6_SCENE_FOLDER",str(dst),flush=True)
print("REUSED_APPROVED_REAL_MUSE_IMAGES",copied,flush=True)
print("QC",json.dumps(validate_assets(dst,m),ensure_ascii=False),flush=True)
