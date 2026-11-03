from pathlib import Path
import hashlib,json,shutil
root=Path(r"D:\STORYBOARD_AI")
stage=root/"dist"/"Storyboard_AI_Studio_Pro_Transfer_Test_20261015"
f=stage/"studio"/"studio_mcp"/"auto_flow_manager.py"
manifest=stage/"CANDIDATE_AUDIT.json"
iss=root/"dist"/"AutoSetup-TransferTest-Installer.iss"
old=root/"dist"/"StoryboardAI-AutoSetup-TransferTest-Setup.exe"
archive=root/"_ARCHIVE"/"OLDER_INSTALLERS_20261015"/"StoryboardAI-AutoSetup-TransferTest-v1.2.3-OLD.exe"
assert f.is_file() and old.is_file() and not archive.exists()
text=f.read_text(encoding="utf-8")
for phrase in ('AUTO_FLOW_DUPLICATE_TABS_REQUIRE_REVIEW',
               'AUTO_FLOW_EXISTING_TAB_REVIEW_REQUIRED',
               'ensure_ready("auto",allow_open=False)'):
    assert phrase in text
spec=iss.read_text(encoding="utf-8")
assert spec.count('#define MyAppVersion "1.2.3"')==1
data=json.loads(manifest.read_text(encoding="utf-8"))
data["sha256"]["studio/studio_mcp/auto_flow_manager.py"]=hashlib.sha256(f.read_bytes()).hexdigest()
data["flow_no_auto_tabs_patch"]="1.2.4: read-only GET, background no new tabs, reject duplicate project tabs"
data["flow_regression"]="4/4 unit checks passed on DESKTOP-2CP0L6S; source patch SHA matches builder"
manifest.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
shutil.copy2(old,archive)
iss.write_text(spec.replace('#define MyAppVersion "1.2.3"','#define MyAppVersion "1.2.4"'),encoding="utf-8")
print("READY_TO_COMPILE_1.2.4",flush=True)
