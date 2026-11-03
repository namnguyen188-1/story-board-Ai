"""Promote only visually verified six Muse repair sheets into canonical assets.
Original wrong images and receipts archived under same scene in _rejected_review_20261031.
No scene generation/publish in this script.
"""
import json,sys,shutil
from pathlib import Path
sys.path.insert(0,r"D:\STORYBOARD_AI\studio")
from drama_asset_review_api import review
from cinematic_engine.drama_asset_first import validate_assets,atomic_write
ep=Path(r"D:\STORYBOARD_AI\studio\productions\THI-N-S-HUY-N-PH-TR-N-QU\episode_001")
m=json.loads((ep/"00_ASSET_PACK"/"asset_bible.json").read_text(encoding="utf-8"))
target={"locations":["thanh_van_mountain_pass","hong_dang_village_gate","hong_dang_old_street"],
        "props":["tui_phu_pouch","huyen_phu_talisman","bamboo_walking_staff"]}
for kind,ids in target.items():
 for id in ids:
  a=m[kind][id];base=ep/"00_ASSET_PACK"/a["folder"]
  repaired=base.with_name(base.name+"_repair_20261031")
  backup=base/"_rejected_review_20261031"
  assert repaired.is_dir(),repaired
  for fn in ["muse_original_4views.png","muse_sheet_receipt.json","generation_proof.json",*[name+".png" for name in a["views"]]]:
   assert (repaired/fn).is_file(),repaired/fn
  if backup.exists():raise RuntimeError("REPAIR_ALREADY_APPLIED_STOP_"+id)
  backup.mkdir()
  for fn in ["muse_original_4views.png","muse_sheet_receipt.json","generation_proof.json",*[name+".png" for name in a["views"]]]:
   old=base/fn
   if old.exists():shutil.move(str(old),str(backup/fn))
   shutil.copy2(repaired/fn,base/fn)
  result=review(ep,kind,id,True)
  if not result["approved"]:raise RuntimeError("REPAIR_IMAGE_NOT_APPROVED_"+id)
  print("MASTER_REPAIRED_AND_APPROVED",kind,id,flush=True)
qc=validate_assets(ep)
print("THIEN_SU_17_REAL_ASSETS_QC",json.dumps({"status":qc["status"],"counts":qc["asset_counts"],
        "blocked":qc["blocked"],"continuity":qc.get("story_continuity")},ensure_ascii=False)[:2400],flush=True)
if qc["status"]!="READY":raise RuntimeError("NOT_READY_AFTER_MASTER_REVIEW")
atomic_write(ep/"master_visual_review_final_20261031.json",
 {"status":"APPROVED_17_REAL_MUSE_SHEETS","approved":17,
  "six_targeted_regenerations_used":True,
  "location_empty_environment":["thanh_van_mountain_pass","hong_dang_village_gate","hong_dang_old_street"],
  "item_only_prop":["tui_phu_pouch","huyen_phu_talisman","bamboo_walking_staff"],
  "all_rejected_originals_archived":True,"proceed_to_scene_images":True})
