from pathlib import Path
import json,hashlib,subprocess,zipfile,re
root=Path(r"D:\STORYBOARD_AI"); dist=root/"dist"
target=dist/"Storyboard_AI_Studio_Pro_v1.3.6"
(target/"studio/version.json").write_bytes((root/"studio/version.json").read_bytes())
package=dist/"Storyboard_AI_Studio_Pro_v1.3.6.zip"
subprocess.run([r"C:\Program Files\7-Zip\7z.exe","a","-tzip",str(package),"studio/version.json"],cwd=target,check=True,capture_output=True)
manifest=json.loads((dist/"latest.json").read_text(encoding="utf-8-sig"))
assert manifest["version"]=="1.3.6"
manifest["bytes"]=package.stat().st_size
manifest["sha256"]=hashlib.file_digest(package.open("rb"),"sha256").hexdigest().upper()
(dist/"latest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
patterns=[re.compile(r"AIza[0-9A-Za-z_-]{35}"),re.compile(r"sk-[A-Za-z0-9]{32,}"),re.compile(r"ya29\.[0-9A-Za-z_-]{50,}"),re.compile(r"1//0[0-9A-Za-z_-]{40,}")]
compiled=0
with zipfile.ZipFile(package) as z,zipfile.ZipFile(dist/"Storyboard_AI_Studio_Pro_v1.3.5.zip") as previous:
 assert z.testzip() is None
 for name in ("studio/web/app.js","studio/web/index.html"):
  assert z.read(name)==previous.read(name),"Existing interface changed"
 assert json.loads(z.read("studio/version.json"))["version"]=="1.3.6"
 for name in ("python/python.exe","python/python312.dll","agent-browser.exe"):
  assert z.getinfo("studio/runtime/muse/"+name).file_size>0
 for e in z.infolist():
  if e.is_dir(): continue
  if Path(e.filename).suffix in (".py",".json",".js",".html",".txt",".env"):
   raw=z.read(e);text=raw.decode("utf-8-sig",errors="replace")
   assert not any(p.search(text) for p in patterns),e.filename
   if e.filename.endswith(".py"):compile(raw,e.filename,"exec");compiled+=1
print(json.dumps({"audit":"PASS","ui":"byte-for-byte unchanged","python_files":compiled,"bytes":manifest["bytes"],"sha256":manifest["sha256"]}),flush=True)
ps=(dist/"publish-update-button-135.ps1").read_text(encoding="utf-8-sig").replace("1.3.5","1.3.6").replace("134","136")
ps=ps.replace("Update button fix","Portable Muse core")
ps=ps.replace("One-click updates without hidden dialogs, with persistent progress and duplicate-update protection. Preserve local accounts and projects. Use the official public GitHub update channel.","Bundle the isolated Muse runtime and login helper. Resolve runtime paths on secondary computers. Preserve the existing interface, local accounts and projects.")
ps=ps.replace("fix update button HTTP 500","bundle portable Muse runtime")
ps=ps.replace("$asset $manifestPath --repo","$asset $manifestPath (Join-Path $dir 'Muse_Runtime_Repair_v1.3.6.zip') --repo")
(dist/"publish-muse-136.ps1").write_text(ps,encoding="utf-8-sig")
