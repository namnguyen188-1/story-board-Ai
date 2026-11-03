from pathlib import Path
import ast,hashlib,json,shutil
root=Path(r"D:\STORYBOARD_AI")
stage=root/"dist"/"Storyboard_AI_Studio_Pro_Transfer_Test_20261015"
f=stage/"studio"/"studio_mcp"/"auto_flow_manager.py"
iss=root/"dist"/"AutoSetup-TransferTest-Installer.iss"
release=root/"dist"/"StoryboardAI-AutoSetup-TransferTest-Setup.exe"
archive=root/"_ARCHIVE"/"OLDER_INSTALLERS_20261015"/"StoryboardAI-AutoSetup-TransferTest-v1.2.4-OLD.exe"
audit=stage/"CANDIDATE_AUDIT.json"
assert all(p.is_file() for p in (f,iss,release,audit))
assert not archive.exists(),"Old version archived already"
s=f.read_text(encoding="utf-8")
ast.parse(s)
for text in ('AUTO_FLOW_PINNED_TAB_NOT_OPEN','AUTO_FLOW_DUPLICATE_TABS_REQUIRE_REVIEW',
            'def _minimize_verified_browser_once','AUTO_FLOW_SELECTED_PROJECT_CHANGED',
            'def ensure_ready(genre="auto", *, allow_open=False'):
    assert text in s,text
spec=iss.read_text(encoding="utf-8")
assert spec.count('#define MyAppVersion "1.2.4"')==1
data=json.loads(audit.read_text(encoding="utf-8"))
key="studio/studio_mcp/auto_flow_manager.py"
data["sha256"][key]=hashlib.sha256(f.read_bytes()).hexdigest()
data["mcp_pinned_session_release"]="1.2.5: reuse selected verified Flow project only; never auto-open/clone"
data["mcp_visibility"]="Account-owned Chrome minimized after auth, explicit Login button restores, retains CDP"
data["mcp_status_guard"]="Read-only active project and exact tab count checked"
data["mcp_live_test"]="DESKTOP-2CP0L6S READY, selected unchanged, 1 Flow tab, Chrome minimized"
data["mcp_mock_tests"]="10/10 PASS after patch, no new tabs, manual login preserved"
audit.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
shutil.copy2(release,archive)
iss.write_text(spec.replace('#define MyAppVersion "1.2.4"','#define MyAppVersion "1.2.5"'),encoding="utf-8")
print("PREPARE_BUILD_1.2.5_PASS",flush=True)
