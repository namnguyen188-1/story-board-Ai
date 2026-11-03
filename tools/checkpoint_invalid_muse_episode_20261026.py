# -*- coding: utf-8 -*-
"""Checkpoint damaged published master and mark verified missing Muse scenes."""
from pathlib import Path
import json, shutil, hashlib
ROOT=Path(r"D:\STORYBOARD_AI\studio")
EP=ROOT/"productions"/"ho-t-h-nh-3d"/"episode_001"
CHECK=ROOT/"diagnostics"/"E2E_REPAIR_20261026"
CHECK.mkdir(parents=True,exist_ok=True)
FINAL=EP/"episode_001_final.mp4"
TARGET=CHECK/"episode_001_final_BEFORE_REPAIR.mp4"
if FINAL.exists() and not TARGET.exists():
 shutil.copy2(FINAL,TARGET)
for number in (11,63,67):
 src=EP/"scenes"/f"scene_{number:04d}"
 dest=CHECK/f"scene_{number:04d}_BEFORE"
 dest.mkdir(exist_ok=True)
 for fn in ("scene_final.mp4","final.mp4","result.json","muse_job.json","job.json","image.png"):
  if (src/fn).exists() and not (dest/fn).exists():shutil.copy2(src/fn,dest/fn)
 result=src/"result.json"
 result.write_text(json.dumps({"status":"FAILED","qc":{"duration_seconds":3.0,"expected_seconds":10.0},
                               "error_code":"MUSE_CLIP_MISSING_FAKE_3S_PLACEHOLDER"},
                              ensure_ascii=False,indent=2),encoding="utf-8")
report={"status":"FAILED_INCOMPLETE","expected_scenes":90,"verified_real_muse_scenes":87,
        "issues":[{"scene":i,"reason":"NO_REAL_MUSE_CLIP; 3 second silent placeholder"} for i in (11,63,67)],
        "publish_allowed":False,"requested_repair":"resume only scenes 11, 63, 67; do not reset other scenes",
        "original_master_backed_up":TARGET.exists(),"original_master":str(FINAL)}
(EP/"episode_qc.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print("BACKUP_MASTER",TARGET.exists(),"BYTES",TARGET.stat().st_size if TARGET.exists() else 0)
print("INVALID_SCENES_MARKED",3)
print("PUBLISH_BLOCKED",not report["publish_allowed"])
