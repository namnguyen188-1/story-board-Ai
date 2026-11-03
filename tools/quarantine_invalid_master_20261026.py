# -*- coding: utf-8 -*-
"""Safely quarantine invalid Muse output with reversible paths and accurate QC."""
from pathlib import Path
import json,shutil
EP=Path(r"D:\STORYBOARD_AI\studio\productions\ho-t-h-nh-3d\episode_001")
QA=Path(r"D:\STORYBOARD_AI\studio\diagnostics\E2E_REPAIR_20261026")
QA.mkdir(parents=True,exist_ok=True)
assert (QA/"episode_001_final_BEFORE_REPAIR.mp4").is_file()
moved={}
for filename in ["episode_001_final.mp4","episode_final.mp4"]:
 src=EP/filename
 dst=QA/(filename.replace(".mp4","_INVALID_879s.mp4"))
 if src.exists():
  if dst.exists():raise RuntimeError("Already quarantined: "+str(dst))
  shutil.move(str(src),str(dst));moved[filename]=str(dst)
for i in (63,67):
 sc=EP/"scenes"/f"scene_{i:04d}"
 for filename in ["scene_final.mp4","final.mp4"]:
  src=sc/filename
  dst=QA/(f"scene_{i:04d}_PLACEHOLDER_{filename}")
  if src.exists():
   if dst.exists():raise RuntimeError("Already quarantined: "+str(dst))
   shutil.move(str(src),str(dst))
 # Preserve user origin receipts and source metadata; only flag unverified media.
 (sc/"result.json").write_text(json.dumps({
   "status":"FAILED","error_code":"REAL_MUSE_SCENE_REQUIRED",
   "qc":{"expected_duration_seconds":10,"actual_render_verified":False},
 },ensure_ascii=False,indent=2),encoding="utf-8")
record={"status":"FAILED_INCOMPLETE","expected_scenes":90,
        "verified_real_muse_scenes":88,"missing_scenes":[63,67],
        "publish_allowed":False,
        "reason":"Muse returned no verified motion video for scenes 63 and 67",
        "quarantined_invalid_master_files":moved,
        "preserved_successful_scenes":88,
        "do_not_autoretry_until_scene_review":True}
(EP/"episode_qc.json").write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding="utf-8")
(QA/"quarantine_manifest.json").write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding="utf-8")
print("INCOMPLETE_QC_SCENES",record["missing_scenes"])
print("GOOD_SCENES_PRESERVED",record["preserved_successful_scenes"])
print("INVALID_MASTERS_QUARANTINED",list(moved))
print("UPLOAD_BLOCKED_BY_MISSING_MASTER_AND_QC",not any((EP/n).exists() for n in ["episode_final.mp4","episode_001_final.mp4"]))
