"""Build a private portable FlowKit release; exclude secrets, active profiles, jobs."""
from pathlib import Path
import hashlib,json,os,zipfile
ROOT=Path("D:/FLOWKIT")
# Fail closed: packaging is disabled until the full test matrix is approved.
# Creating a ZIP is NOT the same as proving portable production stability.
release_approval=ROOT/"state"/"RELEASE_APPROVED.json"
if not release_approval.is_file():
    raise SystemExit("RELEASE_BLOCKED: no signed-off full image/video E2E regression and cross-machine QA")
approval=json.loads(release_approval.read_text(encoding="utf-8"))
if approval.get("status")!="approved" or approval.get("image_video_e2e") is not True or approval.get("cross_machine_e2e") is not True:
    raise SystemExit("RELEASE_BLOCKED: required QA gates not passed")
OUT=Path("D:/FLOWKIT_RELEASES")
OUT.mkdir(exist_ok=True)
DEST=OUT/"FlowKit_ImageVideo_Standalone_20261028_PRIVATE.zip"
TMP=DEST.with_suffix(".part")
groups=["app","bin","docs","extensions/flow","engines/flowkit","engines/muse/runtime/muse/python"]
ignored_dirs={"__pycache__",".git",".venv","node_modules","scratch",".pytest_cache",".mypy_cache"}
ignored_names={".env","cookies.txt","api.key","credentials.json","token.json","session.json"}
files=[]
for group in groups:
 root=ROOT/group
 if not root.is_dir():raise RuntimeError("MISSING_DIR_"+group)
 for file in root.rglob("*"):
  if not file.is_file():continue
  rel=file.relative_to(ROOT)
  if any(p.lower() in ignored_dirs for p in rel.parts):continue
  if file.name.lower() in ignored_names or file.suffix.lower() in {".pyc",".pyo",".log",".sqlite",".db",".lock",".tmp"}:continue
  files.append((file,rel.as_posix()))
for file in (ROOT/"engines"/"muse").glob("*.py"):
 files.append((file,file.relative_to(ROOT).as_posix()))
for name in ["START.cmd","Start_API.vbs","SETUP_FLOW.cmd","SETUP_MUSE.cmd","LOCK_FLOW.cmd","NEW_PROJECT.cmd"]:
 file=ROOT/name
 if not file.is_file():raise RuntimeError("MISSING_START_SCRIPT_"+name)
 files.append((file,name))
for file,arc in [
 (ROOT/"outputs"/"21c859da-8a88-4b30-9a3f-42cd6e92927e"/"scene.png","examples/image_E2E_768x1376.png"),
 (ROOT/"outputs"/"70f37044-abc1-436e-8dd0-920414a9c17b"/"video.mp4","examples/video_E2E_8seconds.mp4")
]:
 if not file.is_file():raise RuntimeError("MISSING_TEST_MEDIA_"+arc)
 files.append((file,arc))
settings=json.loads((ROOT/"settings.json").read_text(encoding="utf-8-sig"))
settings={k:v for k,v in settings.items() if not any(x in k.lower() for x in ("password","secret","token","cookie","api_key"))}
settings["browser_mode"]="on_demand"
settings["browser_idle_close_seconds"]=90
guide="""FLOWKIT PRIVATE PORTABLE - 2026-10-28
===================================
This is the independent image/video engine, not Storyboard AI or MCP V2.
DO NOT integrate into Storyboard AI until further regression.

1. Extract all files to a writable Windows directory (e.g. D:\\FLOWKIT_PORTABLE).
2. Run START.cmd (bundled Python). It starts localhost API without opening Chrome.
3. Open http://127.0.0.1:18110/docs; read generated state/api.key for X-API-Key.
4. Run SETUP_FLOW.cmd and sign in to your authorized Google account.
5. Send POST /v1/jobs with provider=webtool, webtool_mode=hidden, kind=image/video.
6. Retrieve results by /v1/jobs/<id>/files/scene.png or video.mp4.
7. Muse requires independent authentication using SETUP_MUSE.cmd.

This PRIVATE package retains YOUR Flow project and Web Tool URLs in settings.json.
Never publish or sell the package with those URLs. No credentials, API keys,
cookies, browser profiles or Muse account sessions are included.
Google authorization DOES NOT transfer automatically to another PC.
Only one instance may bind to local ports 18110/18100/9232/9233 on a PC.

E2E image: PASS 768x1376 PNG (included in examples).
E2E video: PASS 8.043s 720x1280 MP4 (included).
Flow Direct image: separate test returned HTTP 502; use Web Tool image mode.
Cross-machine installation, Chrome crash during render: not yet E2E verified.
Do not automatically replay a job with an uncertain remote outcome.
"""
if TMP.exists():TMP.unlink()
print("START_ZIP",len(files),"FILES",flush=True)
with zipfile.ZipFile(TMP,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=5,allowZip64=True) as z:
 names=set()
 for i,(file,arc) in enumerate(files,1):
  if arc in names:raise RuntimeError("DUPLICATE_MEMBER_"+arc)
  names.add(arc)
  z.write(file,arc)
  if i%1500==0:print("PACKED",i,"/",len(files),flush=True)
 z.writestr("settings.json",json.dumps(settings,ensure_ascii=False,indent=2))
 z.writestr("state/machine.json",json.dumps({"debug_port":9233},indent=2))
 z.writestr("README_PORTABLE_PRIVATE.txt",guide)
 z.writestr("PACKAGE_STATUS.json",json.dumps({
  "type":"private_portable_zip","date":"2026-10-28","credentials_included":False,
  "image":{"state":"succeeded","dimensions":"768x1376"},
  "video":{"state":"succeeded","seconds":8.043,"dimensions":"720x1280"},
  "flow_direct_image":"HTTP_502_NEEDS_REVIEW","cross_machine_tested":False},indent=2))
os.replace(TMP,DEST)
with zipfile.ZipFile(DEST) as z:
 bad=z.testzip()
 if bad:raise RuntimeError("ZIP_CRC_FAILED_"+bad)
 names=set(z.namelist())
 required={"app/gateway.py","app/flow_webtool_jobs.py","app/flow_webtool_direct.py","app/flow_webtool_worker.py","engines/muse/runtime/muse/python/python.exe","engines/flowkit/agent/main.py","bin/ffmpeg.exe","extensions/flow/manifest.json","examples/image_E2E_768x1376.png","examples/video_E2E_8seconds.mp4"}
 if required-names:raise RuntimeError("MISSING_"+repr(required-names))
 banned=[n for n in names if n.startswith(("runtime/","outputs/","engines/muse/runtime/muse_profiles/")) or n.endswith(("api.key","cookies.txt","token.json"))]
 if banned:raise RuntimeError("SECRET_PATH_INCLUDED_"+str(banned[:3]))
 print("ZIP_CRC_AND_PRIVACY_PASS",len(names),flush=True)
with DEST.open("rb") as f:sha=hashlib.file_digest(f,"sha256").hexdigest()
(OUT/(DEST.name+".sha256")).write_text(sha+"  "+DEST.name+"\n",encoding="ascii")
print("RELEASE_PATH",str(DEST),flush=True)
print("RELEASE_BYTES",DEST.stat().st_size,"SHA256",sha,flush=True)
