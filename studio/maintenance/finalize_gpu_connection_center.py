"""Finalize installer 1.2.3 with in-app GPU setup + cold-boot import check."""
from pathlib import Path
import hashlib,json,sys
root=Path(r"D:\STORYBOARD_AI")
stage=root/"dist"/"Storyboard_AI_Studio_Pro_Transfer_Test_20261015"
manifest=stage/"CANDIDATE_AUDIT.json"
spec=root/"dist"/"AutoSetup-TransferTest-Installer.iss"
record=json.loads(manifest.read_text(encoding="utf-8"))
names=["studio/gpu_setup_control.py","studio/web_server.py","studio/web/index.html",
       "studio/web/app.js","studio/customer_bootstrap.py"]
for name in names:
 p=stage/name
 assert p.is_file(),name
 record["sha256"][name]=hashlib.sha256(p.read_bytes()).hexdigest()
record["required_files"]=len(record["sha256"])
record["gpu_connection_center"]="1.2.3: install/check/cancel progress, local API origin guard; opt-in only"
record["cold_start_import_timeout"]="90-second preflight and per-module diagnostics"
manifest.write_text(json.dumps(record,indent=2,ensure_ascii=False),encoding="utf-8")
txt=spec.read_text(encoding="utf-8")
assert txt.count('#define MyAppVersion "1.2.2"')==1
spec.write_text(txt.replace('#define MyAppVersion "1.2.2"','#define MyAppVersion "1.2.3"'),encoding="utf-8")
print("BUILD_SPEC_UPDATED_1.2.3; FILES_SHA256_UPDATED=",len(names))
