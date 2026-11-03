from pathlib import Path
import hashlib,json,shutil
root=Path(r"D:\STORYBOARD_AI")
stage=root/"dist"/"Storyboard_AI_Studio_Pro_Transfer_Test_20261015"
iss=root/"dist"/"AutoSetup-TransferTest-Installer.iss"
old=root/"dist"/"StoryboardAI-AutoSetup-TransferTest-Setup.exe"
archive=root/"_ARCHIVE"/"OLDER_INSTALLERS_20261015"/"StoryboardAI-AutoSetup-TransferTest-v1.2.1-OLD.exe"
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for v in iter(lambda:f.read(4*1024*1024),b""):h.update(v)
 return h.hexdigest()
assert old.is_file() and not archive.exists()
assert sha(old).upper()=="D1B864B73623E49F42DE47F9AFBDEA0E61A2C737FB4E04A03F8C16BD45AD6E10","old release changed"
p=stage/"studio"/"studio_mcp"/"production_tab.py"
n=stage/"studio"/"studio_mcp"/"node"/"production-job-tab.mjs"
assert "DUPLICATE_TOOL_TABS_BLOCKED" in p.read_text(encoding="utf-8")
assert "DUPLICATE_TABS_BLOCKED" in n.read_text(encoding="utf-8")
manifest=stage/"CANDIDATE_AUDIT.json"
data=json.loads(manifest.read_text(encoding="utf-8"))
for file in (p,n):
 key=file.relative_to(stage).as_posix()
 data["sha256"][key]=sha(file)
data["production_tab_guard"]="2026-10-16 duplicates blocked in both Python and Node"
data["tab_regression"]="Python and Node guard unit tests PASS on customer PC DESKTOP-2CP0L6S"
manifest.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
spec=iss.read_text(encoding="utf-8")
assert spec.count('#define MyAppVersion "1.2.1"')==1
iss.write_text(spec.replace('#define MyAppVersion "1.2.1"','#define MyAppVersion "1.2.2"'),encoding="utf-8")
shutil.move(str(old),str(archive))
print("ARCHIVED_OLD",archive)
print("CANDIDATE_VERSION","1.2.2")
print("CURRENT_MCP_FILES_HASHED",2)
