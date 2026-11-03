"""One targeted real Muse image generation each for six rejected masters.
Preserves prior source photos/receipts; does not update asset registry or auto-approve.
Resume a receipt when pending; never duplicate Muse submissions.
"""
import json,sys,copy,concurrent.futures,time
from pathlib import Path
sys.path.insert(0,r"D:\STORYBOARD_AI\studio")
from muse_asset_images import generate_sheet
from cinematic_engine.drama_asset_first import atomic_write
ep=Path(r"D:\STORYBOARD_AI\studio\productions\THI-N-S-HUY-N-PH-TR-N-QU\episode_001")
manifest=json.loads((ep/"00_ASSET_PACK"/"asset_bible.json").read_text(encoding="utf-8"))
target={"locations":["thanh_van_mountain_pass","hong_dang_village_gate","hong_dang_old_street"],
        "props":["tui_phu_pouch","huyen_phu_talisman","bamboo_walking_staff"]}
tasks=[]
for kind,names in target.items():
 for id in names:
  asset=copy.deepcopy(manifest[kind][id])
  asset["folder"]+="_repair_20261031"
  for view,info in asset["views"].items():
   info["path"]=str(ep/"00_ASSET_PACK"/asset["folder"]/(view+".png"))
  # physical design stays stable; forbid distracting people in master sheets
  # without changing the asset bible's canonical specification.
  profile=dict(asset["profile"])
  if kind=="locations":
   profile["description"]=((profile.get("description") or profile.get("spec") or asset["name"])+
           " Crucial: architecture/terrain ONLY, zero people anywhere, zero modern visitors, zero extras, no humans, no character modeling; all 4 panels empty.")
  else:
   profile["description"]=((profile.get("description") or profile.get("spec") or asset["name"])+
           " Crucial: isolated SINGLE OBJECT only, show all 4 physical angles. Never show someone wearing/holding/carrying this. No models, clothes, props other than this exact item.")
  asset["profile"]=profile
  tasks.append((kind,id,asset))
def go(t):
 kind,id,asset=t
 print("REPAIR_MASTER_START",kind,id,flush=True)
 try:
  res=generate_sheet(asset,kind,ep,timeout_s=260)
  print("REPAIR_MASTER_DONE",kind,id,res["status"],flush=True)
  return {"kind":kind,"id":id,"status":res["status"],"folder":asset["folder"]}
 except Exception as e:
  print("REPAIR_MASTER_PENDING_OR_FAILED",kind,id,type(e).__name__,str(e)[:300],flush=True)
  return {"kind":kind,"id":id,"status":"UNFINISHED","error":str(e),"folder":asset["folder"]}
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
 out=list(ex.map(go,tasks))
atomic_write(ep/"master_six_repair_jobs_20261031.json",out)
print("SIX_REPAIR_SUMMARY",json.dumps(out,ensure_ascii=False),flush=True)
