"""Build and verify Storyboard_AI_Studio_Pro_v1.3.13.zip from 1.3.12 baseline with Tri-Chromatic Thumbnail (Gold+Red+White), Clean 5-Hashtags, and VidIQ 100/100."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import zipfile

ROOT = Path(r"D:\STORYBOARD_AI")
DIST = ROOT / "dist"
BASE = DIST / "Storyboard_AI_Studio_Pro_v1.3.12.zip"
OUT = DIST / "Storyboard_AI_Studio_Pro_v1.3.13.zip"
STAGE = DIST / "_stage_v1313"
SEVEN = Path(r"C:\Program Files\7-Zip\7z.exe")

assert BASE.is_file(), f"Baseline not found: {BASE}"
assert SEVEN.is_file(), f"7-Zip not found: {SEVEN}"

if STAGE.exists():
    shutil.rmtree(STAGE, ignore_errors=True)
STAGE.mkdir(parents=True, exist_ok=True)

# 1. Collect all target files to stage
files_to_overlay = []

# All 7 skills
for skill_file in (ROOT / ".agents" / "skills").rglob("*"):
    if skill_file.is_file() and "__pycache__" not in skill_file.parts:
        rel = skill_file.relative_to(ROOT)
        files_to_overlay.append(str(rel).replace("\\", "/"))

# Core studio files updated in 1.3.13
studio_updates = [
    "studio/version.json",
    "studio/seo_packager.py",
    "studio/thumbnail_studio.py",
    "studio/youtube_manager.py",
    "studio/series_studio.py",
    "studio/reference_scene_assembler.py",
    "studio/web_server.py",
    "studio/web/app.js",
    "studio/web/index.html",
]

for p in studio_updates:
    if (ROOT / p).is_file():
        files_to_overlay.append(p)

files_to_overlay = sorted(list(set(files_to_overlay)))
print(f"Staging {len(files_to_overlay)} files for v1.3.13 overlay...")

for rel_str in files_to_overlay:
    src = ROOT / rel_str
    dst = STAGE / rel_str
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

print("Copying baseline v1.3.12 -> v1.3.13...")
if OUT.exists():
    OUT.unlink()
shutil.copyfile(BASE, OUT)

print("Injecting staged files into v1.3.13 via 7-Zip...")
cmd = [str(SEVEN), "a", str(OUT), f"{STAGE}\\*"]
proc = subprocess.run(cmd, capture_output=True, text=True)
assert proc.returncode == 0, f"7z failed: {proc.stderr}\n{proc.stdout}"

# Verify zip
size = OUT.stat().st_size
hasher = hashlib.sha256()
with open(OUT, "rb") as f:
    while chunk := f.read(1024 * 1024):
        hasher.update(chunk)
sha256 = hasher.hexdigest()

print(f"\n=======================================================")
print(f"SUCCESS: {OUT.name}")
print(f"SIZE:    {size:,} bytes")
print(f"SHA256:  {sha256}")
print(f"=======================================================\n")

# Verify contents inside zip
with zipfile.ZipFile(OUT, "r") as zf:
    namelist = zf.namelist()
    for check_file in [
        "studio/version.json",
        "studio/seo_packager.py",
        "studio/thumbnail_studio.py",
        "studio/youtube_manager.py",
        ".agents/skills/create-youtube-thumbnail/SKILL.md",
        ".agents/skills/publish-youtube-narrative/SKILL.md",
        ".agents/skills/publish-youtube-shorts/SKILL.md",
        ".agents/skills/publish-youtube-drama/SKILL.md"
    ]:
        norm_name = check_file.replace("/", "\\")
        matched = [n for n in namelist if n == check_file or n == norm_name]
        assert matched, f"Missing {check_file} in zip!"
        # Verify version inside zip
        if check_file == "studio/version.json":
            v_data = json.loads(zf.read(matched[0]).decode("utf-8"))
            assert v_data.get("version") == "1.3.13", f"Wrong version in zip: {v_data}"

print("All package verifications passed 100%!")

# Write manifest snippet
manifest = {
    "version": "1.3.13",
    "release_date": "2026-11-04",
    "filename": "Storyboard_AI_Studio_Pro_v1.3.13.zip",
    "size": size,
    "sha256": sha256,
    "download_url": f"https://github.com/anma8802-create/AI-tool/releases/download/v1.3.13/Storyboard_AI_Studio_Pro_v1.3.13.zip",
    "notes": "v1.3.13: Cong thuc thumbnail 3 mau dinh cao Vang kim + Do tham + Trang titan (100/100 VidIQ), bo loc sach 5 hashtag, fix loi lang NameError, va cap nhat toan bo 7 skills."
}
(DIST / "latest_v1313.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Manifest written to: {DIST / 'latest_v1313.json'}")
