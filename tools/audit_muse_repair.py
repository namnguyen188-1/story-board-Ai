from pathlib import Path
import json, zipfile, re, hashlib
root=Path(r"D:\STORYBOARD_AI")
p=root/"studio/version.json"; d=json.loads(p.read_text(encoding="utf-8-sig")); d["version"]="1.3.6"; p.write_text(json.dumps(d,indent=2),encoding="utf-8")
shutil_source=root/"make_secure_release.py"
s=shutil_source.read_text(encoding="utf-8")
s=s.replace('        shutil.copy2(ver_file, TARGET_DIR / "studio" / "version.json")','        version_data = json.loads(ver_file.read_text(encoding="utf-8-sig"))\n        version_data["version"] = VERSION\n        (TARGET_DIR / "studio" / "version.json").write_text(json.dumps(version_data, indent=2), encoding="utf-8")')
shutil_source.write_text(s,encoding="utf-8")
p=root/"dist/Muse_Runtime_Repair_v1.3.6.zip"
patterns=[re.compile(r"AIza[0-9A-Za-z_-]{35}"),re.compile(r"sk-[A-Za-z0-9]{32,}"),re.compile(r"ya29\.[0-9A-Za-z_-]{50,}"),re.compile(r"1//0[0-9A-Za-z_-]{40,}")]
with zipfile.ZipFile(p) as z:
 assert z.testzip() is None
 for e in z.infolist():
  if e.is_dir(): continue
  assert e.filename.startswith("studio/runtime/muse/") or e.filename in ("studio/muse_login.py","studio/muse_video_provider.py"), e.filename
  if Path(e.filename).suffix in (".py",".json",".js",".html",".txt"):
   t=z.read(e).decode("utf-8-sig",errors="replace")
   assert not any(pat.search(t) for pat in patterns),e.filename
   if e.filename.endswith(".py"): compile(t,e.filename,"exec")
print(json.dumps({"repair_audit":"PASS","bytes":p.stat().st_size,"sha256":hashlib.file_digest(p.open("rb"),"sha256").hexdigest().upper()}))
