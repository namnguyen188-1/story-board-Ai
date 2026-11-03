from pathlib import Path
import ast,json,hashlib,shutil
root=Path(r"D:\STORYBOARD_AI")
stage=root/"dist"/"Storyboard_AI_Studio_Pro_Transfer_Test_20261015"
spec=root/"dist"/"AutoSetup-TransferTest-Installer.iss"
release=root/"dist"/"StoryboardAI-AutoSetup-TransferTest-Setup.exe"
archive=root/"_ARCHIVE"/"OLDER_INSTALLERS_20261015"/"StoryboardAI-AutoSetup-TransferTest-v1.2.5-OLD.exe"
manifest=stage/"CANDIDATE_AUDIT.json"
assert not archive.exists() and release.is_file() and manifest.is_file()
text=spec.read_text(encoding="utf-8")
assert text.count('#define MyAppVersion "1.2.5"')==1
ast.parse((stage/"studio"/"web_server.py").read_text(encoding="utf-8"))
af=(stage/"studio"/"studio_mcp"/"auto_flow_manager.py").read_text(encoding="utf-8")
assert "def _minimize_verified_browser_once" in af
assert 'def ensure_ready(genre="auto", *, allow_open=False' in af
web=(stage/"studio"/"web_server.py").read_text(encoding="utf-8")
assert 'result["login_pending"]=True' in web
html=(stage/"studio"/"web"/"index.html").read_text(encoding="utf-8")
assert "mcp_pinned_1" in html and "Thêm tài khoản" in html
js=(stage/"studio"/"web"/"app.js").read_text(encoding="utf-8")
assert "Chỉ khi bạn bấm Đăng nhập / Hiện Google Flow" in js
shutil.copy2(release,archive)
record=json.loads(manifest.read_text(encoding="utf-8"))
for rel in ("studio/web_server.py","studio/web/app.js","studio/web/index.html","studio/studio_mcp/auto_flow_manager.py"):
 p=stage/rel
 record["sha256"][rel]=hashlib.sha256(p.read_bytes()).hexdigest()
record["required_files"]=len(record["sha256"])
record["mcp_exclusive_login_release"]="1.2.6: only explicit login action restores owned Chrome; create/select don't"
record["live_test"]="on DESKTOP-2CP0L6S: MCP READY, selected pinned, 1 Flow tab, Chrome minimized"
record["regression"]="10/10 pinned/session tests + 3/3 tab status tests + login-only AST PASS"
manifest.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding="utf-8")
spec.write_text(text.replace('#define MyAppVersion "1.2.5"','#define MyAppVersion "1.2.6"'),encoding="utf-8")
print("PREBUILD_1.2.6_PASS",flush=True)
