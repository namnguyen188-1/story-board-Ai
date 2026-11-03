from pathlib import Path
import json, hashlib, shutil, subprocess, zipfile
root=Path(r"D:\STORYBOARD_AI"); dist=root/"dist"
old=dist/"Storyboard_AI_Studio_Pro_v1.3.8.zip"
new=dist/"Storyboard_AI_Studio_Pro_v1.3.9.zip"
stage=dist/"_patch_stage_v139"
seven=Path(r"C:\Program Files\7-Zip\7z.exe")
assert old.is_file() and seven.is_file()
assert not new.exists(), "Candidate already exists"
patched=["tools/Update-StoryboardAI.ps1","studio/version.json"]
for name in patched:
    dest=stage/name;dest.parent.mkdir(parents=True,exist_ok=True)
    if name=="studio/version.json":
        ver=json.loads((root/name).read_text(encoding="utf-8-sig"))
        ver["version"]="1.3.9";ver["release_date"]="2026-10-22"
        dest.write_text(json.dumps(ver,indent=2,ensure_ascii=False),encoding="utf-8")
    else: shutil.copy2(root/name,dest)
shutil.copyfile(old,new)
subprocess.run([str(seven),"u","-tzip",str(new),*patched,"-y"],cwd=stage,check=True,capture_output=True)
with zipfile.ZipFile(old) as oz,zipfile.ZipFile(new) as nz:
    assert nz.testzip() is None
    a={i.filename:i for i in oz.infolist() if not i.is_dir()}
    b={i.filename:i for i in nz.infolist() if not i.is_dir()}
    assert len(b)==len([i for i in nz.infolist() if not i.is_dir()])
    assert set(a)==set(b)
    for k in set(a)-set(patched): assert (a[k].CRC,a[k].file_size)==(b[k].CRC,b[k].file_size),k
    for k in patched: assert nz.read(k)==(stage/k).read_bytes(),k
    patch=nz.read("tools/Update-StoryboardAI.ps1").decode("utf-8-sig")
    assert "Select-Object -Unique" in patch and "refresh=" in patch
    assert "1.3.9"==json.loads(nz.read("studio/version.json"))["version"]
    assert "Đăng nhập" in nz.read("studio/web/app.js").decode("utf-8")
    assert "math.gcd" in nz.read("studio/muse_gateway_worker.py").decode("utf-8")
    assert b["studio/runtime/muse/python/python.exe"].file_size>0
hash=hashlib.file_digest(new.open("rb"),"sha256").hexdigest().upper()
print(json.dumps({"candidate":str(new),"bytes":new.stat().st_size,"sha256":hash,"files":len(b),"patched":patched,"audit":"PASS"},ensure_ascii=False),flush=True)
