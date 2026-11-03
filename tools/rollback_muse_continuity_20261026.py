# -*- coding: utf-8 -*-
"""Restore the three files changed by the 2026-10-26 continuity experiment."""
from pathlib import Path
import hashlib, shutil, py_compile, datetime, os
root=Path(r"D:\STORYBOARD_AI")
studio=root/"studio"
before=root/"tools"/"backups"/"continuity_20261026_142646"
stamp=datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
out=root/"tools"/"backups"/("rollback_continuity_"+stamp)
files=["cinematic_engine/drama_orchestrator.py",
       "cinematic_engine/drama_video_engine.py","muse_video_provider.py"]
expected_markers={
files[0]:"MUSE_CONTINUITY_V1",
files[1]:"MUSE_CONTINUITY_V1",
files[2]:"MUSE_CONTINUITY_V1"
}
def sha(p):
 return hashlib.sha256(p.read_bytes()).hexdigest()
# Read and compile all sources before any change.
for relative in files:
 target=studio/relative
 orig=before/relative
 if not target.is_file() or not orig.is_file():
  raise RuntimeError(f"RECOVERY_SOURCE_MISSING {relative}")
 now=target.read_text(encoding="utf-8")
 old=orig.read_text(encoding="utf-8")
 if expected_markers[relative] not in now or expected_markers[relative] in old:
  raise RuntimeError(f"RECOVERY_VERSION_MISMATCH {relative}")
 compile(old,str(target),"exec")
out.mkdir(parents=True)
# Save patched files to rollback folder.
for relative in files:
 dest=out/"experiment_version"/relative
 dest.parent.mkdir(parents=True,exist_ok=True)
 shutil.copy2(studio/relative,dest)
# Restore each earlier verified good version atomically.
for relative in files:
 orig=before/relative
 target=studio/relative
 tmp=target.with_name(target.name+".restore_20261026_tmp")
 shutil.copy2(orig,tmp)
 os.replace(tmp,target)
 if sha(orig)!=sha(target):
  raise RuntimeError(f"RESTORE_HASH_MISMATCH {relative}")
 py_compile.compile(str(target),doraise=True)
 print("RESTORED_SHA256_MATCH",relative,sha(target)[:24])
# Archive only our experimental helper and tests to avoid stale failing test discovery.
for p in [studio/"cinematic_engine"/"scene_continuity.py",
          studio/"tests"/"test_scene_continuity_20261026.py",
          root/"tools"/"patch_continuity_20261026.py",
          root/"tools"/"test_continuity_live_20261026.py"]:
 if p.exists():
  dest=out/"experiment_only"/p.name
  if dest.exists(): raise RuntimeError("ARCHIVE_CONFLICT")
  shutil.move(str(p),str(dest))
  print("ARCHIVED_EXPERIMENT_ONLY",p.name)
print("ROLLBACK_COMPLETE")
print("ARCHIVE",out)
