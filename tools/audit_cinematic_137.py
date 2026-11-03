from pathlib import Path
import json,zipfile,re,hashlib
root=Path(r"D:\STORYBOARD_AI");dist=root/"dist"
package=dist/"Storyboard_AI_Studio_Pro_v1.3.7.zip";repair=dist/"Cinematic_Core_Repair_v1.3.7.zip"
patterns=[re.compile(r"AIza[0-9A-Za-z_-]{35}"),re.compile(r"sk-[A-Za-z0-9]{32,}"),re.compile(r"ya29\.[0-9A-Za-z_-]{50,}"),re.compile(r"1//0[0-9A-Za-z_-]{40,}")]
compiled=0
for path in (package,repair):
 with zipfile.ZipFile(path) as z:
  assert z.testzip() is None
  assert json.loads(z.read("studio/version.json"))["version"]=="1.3.7"
  assert z.getinfo("studio/cinematic_engine/drama_orchestrator.py").file_size>0
  for e in z.infolist():
   if e.is_dir():continue
   if Path(e.filename).suffix in (".py",".json",".js",".html",".txt",".env"):
    raw=z.read(e);t=raw.decode("utf-8-sig",errors="replace")
    assert not any(p.search(t) for p in patterns),e.filename
    if e.filename.endswith(".py"):compile(raw,e.filename,"exec");compiled+=1
with zipfile.ZipFile(package) as z,zipfile.ZipFile(dist/"Storyboard_AI_Studio_Pro_v1.3.6.zip") as old:
 for name in ("studio/web/app.js","studio/web/index.html"):assert z.read(name)==old.read(name)
m=json.loads((dist/"latest.json").read_text(encoding="utf-8-sig"));m.update(version="1.3.7",release_name="Storyboard_AI_Studio_Pro_v1.3.7",installer="https://github.com/anma8802-create/AI-tool/releases/latest/download/"+package.name,bytes=package.stat().st_size,sha256=hashlib.file_digest(package.open("rb"),"sha256").hexdigest().upper(),release_notes=["Include the cinematic production pipeline omitted from previous packages.","Fix ModuleNotFoundError before starting Muse scene production.","Preserve the existing interface, accounts and projects."])
(dist/"latest.json").write_text(json.dumps(m,indent=2),encoding="utf-8")
ps=(dist/"publish-muse-136.ps1").read_text(encoding="utf-8-sig").replace("1.3.6","1.3.7").replace("136","137").replace("Muse_Runtime_Repair","Cinematic_Core_Repair").replace("Portable Muse core","Restore cinematic production pipeline")
ps=ps.replace("Bundle the isolated Muse runtime and login helper. Resolve runtime paths on secondary computers. Preserve the existing interface, local accounts and projects.","Include the cinematic_engine production modules missing from earlier packages. Fix startup ModuleNotFoundError. Keep the existing interface, accounts and projects.")
ps=ps.replace("bundle portable Muse runtime","restore missing cinematic production pipeline")
(dist/"publish-cinematic-137.ps1").write_text(ps,encoding="utf-8-sig")
print(json.dumps({"audit":"PASS","python_files":compiled,"ui":"unchanged","full_bytes":m["bytes"],"repair_bytes":repair.stat().st_size,"repair_sha256":hashlib.file_digest(repair.open("rb"),"sha256").hexdigest().upper()}),flush=True)
