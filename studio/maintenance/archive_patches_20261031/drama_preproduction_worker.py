"""On-demand Muse asset-first worker, launched ONLY by multi-role production.
Muse image jobs use their own receipt and never auto-resubmit.
"""
from pathlib import Path
import argparse,json,sys
from cinematic_engine.drama_asset_first import validate_assets

def main():
 p=argparse.ArgumentParser()
 p.add_argument("action",choices=["assets","scene"])
 p.add_argument("--episode-dir",required=True)
 p.add_argument("--scene-number",type=int)
 p.add_argument("--max-assets",type=int,default=20)
 a=p.parse_args()
 ep=Path(a.episode_dir)
 manifest=json.loads((ep/"00_ASSET_PACK"/"asset_bible.json").read_text(encoding="utf-8"))
 if a.action=="assets":
  from muse_asset_images import generate_sheet
  total=sum(len(manifest[k]) for k in ("characters","locations","props"))
  if total>a.max_assets:
   raise RuntimeError(f"DRAMA_TOO_MANY_ASSETS: {total}. Normalize duplicate locations/props before paid generation.")
  for kind in ("characters","locations","props"):
   for name,asset in manifest[kind].items():
    folder=ep/"00_ASSET_PACK"/asset["folder"]
    sheet=folder/"muse_original_4views.png"
    if sheet.exists() and all(Path(v["path"]).is_file() for v in asset["views"].values()):
     print("[ASSET_REUSE]",kind,name,flush=True);continue
    print("[MUSE_IMAGE] creating real master",kind,name,flush=True)
    x=generate_sheet(asset,kind,ep,timeout_s=210)
    print("[MUSE_IMAGE] generated",kind,name,x["status"],flush=True)
  qc=validate_assets(ep,manifest)
  print("ASSET_IMAGE_RESULT",json.dumps(qc,ensure_ascii=False),flush=True)
 elif a.action=="scene":
  if not a.scene_number:raise RuntimeError("SCENE_NUMBER_REQUIRED")
  from muse_scene_image import generate_scene
  plan=json.loads((ep/"drama_plan.json").read_text(encoding="utf-8"))
  scene=next((x for x in plan.get("scenes",[]) if int(x.get("scene_number",0))==a.scene_number),None)
  if not scene:raise RuntimeError("SCENE_NOT_IN_PLAN")
  print("[MUSE_SCENE_IMAGE] creating composed scene",a.scene_number,flush=True)
  res=generate_scene(ep,scene,timeout_s=210)
  print("MUSE_SCENE_IMAGE_RESULT",json.dumps({k:v for k,v in res.items() if k!="references_uploaded"},ensure_ascii=False),flush=True)

if __name__=="__main__":main()
