from pathlib import Path
import shutil, os, subprocess, sys, json, zipfile
root=Path(r"D:\STORYBOARD_AI"); dest=root/"studio/runtime/muse"; py=dest/"python"
if py.exists(): raise RuntimeError("Refusing to overwrite existing bundle")
py.mkdir(parents=True)
for name in ("python.exe","pythonw.exe","python3.dll","python312.dll","vcruntime140.dll","vcruntime140_1.dll","LICENSE.txt"):
 p=Path("D:/")/name
 if p.is_file(): shutil.copy2(p,py/name)
ignore=shutil.ignore_patterns("__pycache__","*.pyc","site-packages","test","tests","idlelib","tkinter","turtledemo","ensurepip")
shutil.copytree(Path("D:/Lib"),py/"Lib",ignore=ignore)
shutil.copytree(Path("D:/DLLs"),py/"DLLs",ignore=shutil.ignore_patterns("*tk*","*tcl*"))
site=Path(os.environ["LOCALAPPDATA"])/"muse-cli-audit/venv/Lib/site-packages"
shutil.copytree(site,py/"Lib/site-packages",ignore=shutil.ignore_patterns("__pycache__","*.pyc","pip","pip-*.dist-info","examples"))
(py/"python312._pth").write_text('Lib\nDLLs\nLib/site-packages\n.\n..\\..\\..\\\nimport site\n', encoding="ascii")
helper=Path(os.environ["APPDATA"])/"npm/node_modules/agent-browser"
shutil.copy2(helper/"bin/agent-browser-win32-x64.exe",dest/"agent-browser.exe")
for name in ("LICENSE","LICENSE.md","LICENSE.txt"):
 if (helper/name).is_file(): shutil.copy2(helper/name,dest/("agent-browser-"+name))
check="import sys, json, muse_cli.cli, muse_cli.gateway, curl_cffi, cffi, noise, google.protobuf, av, PIL; print(json.dumps({'python':sys.version.split()[0],'prefix':sys.prefix,'base_prefix':sys.base_prefix,'muse_imports':'ok'}))"
subprocess.run([str(py/"python.exe"),"-I","-c",check],check=True)
subprocess.run([str(dest/"agent-browser.exe"),"--version"],check=True)
files=[p for p in dest.rglob("*") if p.is_file()]
print("BUNDLE_OK",len(files),sum(p.stat().st_size for p in files),flush=True)
for folder in (root/"studio/runtime/python",):
 fs=[p for p in folder.rglob("*") if p.is_file()]
 print("APP_RUNTIME_SIZE",len(fs),sum(p.stat().st_size for p in fs))
