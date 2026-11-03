from pathlib import Path
import json, hashlib, shutil, subprocess, zipfile, re

root = Path(r"D:\STORYBOARD_AI")
dist = root / "dist"
old = dist / "Storyboard_AI_Studio_Pro_v1.3.7.zip"
new = dist / "Storyboard_AI_Studio_Pro_v1.3.8.zip"
stage = dist / "_patch_stage_v138"
seven = Path(r"C:\Program Files\7-Zip\7z.exe")
assert old.is_file() and seven.is_file()
assert not new.exists(), "Candidate already exists; refusing to overwrite"
patched = ["studio/muse_gateway_worker.py", "studio/muse_video_provider.py", "studio/web/app.js", "studio/version.json"]
for name in patched:
    dest = stage / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    if name == "studio/version.json":
        data = json.loads((root / name).read_text(encoding="utf-8-sig"))
        data["version"] = "1.3.8"
        data["release_date"] = "2026-10-22"
        dest.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    else:
        shutil.copy2(root / name, dest)
shutil.copyfile(old, new)
subprocess.run([str(seven), "u", "-tzip", str(new), *patched, "-y"], cwd=stage, check=True, capture_output=True)
patterns = [re.compile(r"AIza[0-9A-Za-z_-]{35}"), re.compile(r"sk-[A-Za-z0-9]{32,}"), re.compile(r"ya29\.[0-9A-Za-z_-]{50,}")]
with zipfile.ZipFile(old) as zo, zipfile.ZipFile(new) as zn:
    assert zn.testzip() is None, "Corrupt ZIP"
    a = {i.filename: i for i in zo.infolist() if not i.is_dir()}
    b = {i.filename: i for i in zn.infolist() if not i.is_dir()}
    assert len(b) == len([i for i in zn.infolist() if not i.is_dir()]), "Duplicate ZIP entry"
    assert set(a) == set(b), "Unexpected package file changes"
    for name in set(a) - set(patched):
        assert (a[name].CRC, a[name].file_size) == (b[name].CRC, b[name].file_size), name
    for name in patched:
        expected = (stage / name).read_bytes()
        assert zn.read(name) == expected, name
        text = expected.decode("utf-8-sig")
        assert not any(p.search(text) for p in patterns), name
        if name.endswith(".py"):
            compile(expected, name, "exec")
    assert b["studio/runtime/muse/python/python.exe"].file_size > 0
    assert b["studio/cinematic_engine/__init__.py"].file_size >= 0
    assert "Đăng nhập" in zn.read("studio/web/app.js").decode("utf-8")
    assert "math.gcd" in zn.read("studio/muse_gateway_worker.py").decode("utf-8")
digest = hashlib.file_digest(new.open("rb"), "sha256").hexdigest().upper()
print(json.dumps({"candidate":str(new),"bytes":new.stat().st_size,"sha256":digest,"file_count":len(b),"patched":patched,"audit":"PASS"},ensure_ascii=False),flush=True)
