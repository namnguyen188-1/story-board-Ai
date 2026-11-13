"""
Movie Recap Studio Pro - Automated Distribution Packager.
Builds:
1. Clean Portable Release Directory & ZIP: D:\MOVIE_RECAP_STUDIO\dist\Movie_Recap_Studio_Pro_v1.0_Portable.zip
2. Standalone Self-Extracting Installer: D:\STORYBOARD_AI\dist_package\Movie_Recap_Studio_Pro_Setup.exe
"""
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

SRC_DIR = Path(r"D:\MOVIE_RECAP_STUDIO").resolve()
DIST_DIR = SRC_DIR / "dist"
DIST_DIR.mkdir(parents=True, exist_ok=True)

RELEASE_NAME = "Movie_Recap_Studio_Pro_v1.0"
STAGE_DIR = DIST_DIR / RELEASE_NAME
if STAGE_DIR.exists():
    shutil.rmtree(STAGE_DIR, ignore_errors=True)
STAGE_DIR.mkdir(parents=True, exist_ok=True)

print(f"📦 Staging files from {SRC_DIR} to {STAGE_DIR}...")

# 1. Essential Root Files
ESSENTIAL_ROOT_FILES = [
    "Movie_Recap_Studio.exe",
    "KHOI_DONG.bat",
    "KHOI_DONG_RECAP.bat",
    "config.py",
    "desktop_app.py",
    "pipeline.py",
    "server.py",
    "recap_config.example.json",
    "recap_config.json",
    "test_sample.mp4",
]

for fn in ESSENTIAL_ROOT_FILES:
    f_path = SRC_DIR / fn
    if f_path.is_file():
        shutil.copy2(f_path, STAGE_DIR / fn)
        print(f"  + {fn}")

# 2. Subdirectories: core, web, launcher_src, runtime
SUBDIRS = ["core", "web", "launcher_src", "runtime"]
for d_name in SUBDIRS:
    s_d = SRC_DIR / d_name
    t_d = STAGE_DIR / d_name
    if s_d.is_dir():
        def ignore_patterns(folder, items):
            return [i for i in items if i in ("__pycache__", ".git") or i.endswith(".pyc")]
        shutil.copytree(s_d, t_d, ignore=ignore_patterns, dirs_exist_ok=True)
        print(f"  + dir: {d_name}/")

seven_zip = Path(r"C:\Program Files\7-Zip\7z.exe")
sfx_module = Path(r"C:\Program Files\7-Zip\7z.sfx")

# 3. Create Portable ZIP via fast 7-Zip
zip_path = DIST_DIR / f"{RELEASE_NAME}_Portable.zip"
print(f"📦 Compressing into Portable ZIP: {zip_path}...")
cmd_zip = [
    str(seven_zip), "a", "-tzip", "-mx=5", "-r",
    str(zip_path),
    str(STAGE_DIR / "*")
]
subprocess.run(cmd_zip, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
zip_size_mb = zip_path.stat().st_size / (1024 * 1024)
print(f"✅ Portable ZIP created: {zip_path.name} ({zip_size_mb:.1f} MB)")

# 4. Create Standalone 7z SFX Setup Installer
if seven_zip.exists() and sfx_module.exists():
    dist_pkg_dir = Path(r"D:\STORYBOARD_AI\dist_package")
    dist_pkg_dir.mkdir(parents=True, exist_ok=True)

    payload_7z = dist_pkg_dir / "app_payload.7z"
    if payload_7z.exists():
        payload_7z.unlink(missing_ok=True)

    print(f"📦 Creating 7z archive for SFX installer...")
    cmd_7z = [
        str(seven_zip), "a", "-mx=5", "-r",
        str(payload_7z),
        str(STAGE_DIR / "*")
    ]
    subprocess.run(cmd_7z, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    sfx_config = dist_pkg_dir / "sfx_config.txt"
    sfx_config.write_text(
        ';!@Install@!UTF-8!\n'
        'Title="Movie Recap Studio Pro 2026 - Bản Cài Đặt Standalone"\n'
        'BeginPrompt="Bạn có muốn giải nén và mở Movie Recap Studio Pro (Bản Standalone độc lập 100%) không?"\n'
        'RunProgram="Movie_Recap_Studio.exe"\n'
        ';!@InstallEnd@!\n',
        encoding="utf-8"
    )

    setup_exe = dist_pkg_dir / "Movie_Recap_Studio_Pro_Setup.exe"
    print(f"🔨 Building SFX Setup Installer: {setup_exe}...")
    with open(setup_exe, "wb") as out_f:
        out_f.write(sfx_module.read_bytes())
        out_f.write(sfx_config.read_bytes())
        out_f.write(payload_7z.read_bytes())

    # Copy installer to Desktop for easy access
    desktop_setup = Path(r"C:\Users\thean\Desktop\Movie_Recap_Studio_Pro_Setup.exe")
    shutil.copy2(setup_exe, desktop_setup)
    setup_mb = setup_exe.stat().st_size / (1024 * 1024)
    print(f"✅ Setup Installer created: {setup_exe.name} ({setup_mb:.1f} MB)")
    print(f"✅ Copied to Desktop: {desktop_setup}")

print("🎉 Packaging complete!")
