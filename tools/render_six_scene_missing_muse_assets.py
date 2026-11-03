import sys,json,concurrent.futures,time
from pathlib import Path
sys.path.insert(0,r"D:\STORYBOARD_AI\studio")
from muse_asset_images import generate_sheet
from cinematic_engine.drama_asset_first import validate_assets
ep=Path(r"D:\STORYBOARD_AI\studio\scratch\multi_role_asset_first_e2e\episode_006")
m=json.loads((ep/"00_ASSET_PACK"/"asset_bible.json").read_text(encoding="utf-8"))
task=[]
for kind in ("characters","locations","props"):
 for key,item in m[kind].items():
  if (ep/"00_ASSET_PACK"/item["folder"]/"muse_original_4views.png").is_file():continue
  task.append((kind,key,item))
def job(arg):
 kind,key,item=arg
 print("MUSE_REAL_ASSET_STARTED",kind,key,flush=True)
 try:
  a=generate_sheet(item,kind,ep,timeout_s=240)
  print("MUSE_REAL_ASSET_DONE",kind,key,a["status"],flush=True)
  return {"kind":kind,"id":key,"status":a["status"]}
 except Exception as e:
  print("MUSE_REAL_ASSET_UNFINISHED",kind,key,str(e),flush=True)
  return {"kind":kind,"id":key,"status":"INCOMPLETE","error":str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 result=list(pool.map(job,task))
print("FOUR_ASSETS_GENERATION_RESULTS",json.dumps(result,ensure_ascii=False),flush=True)
print("PREPRODUCTION_QC",json.dumps(validate_assets(ep,m),ensure_ascii=False),flush=True)
