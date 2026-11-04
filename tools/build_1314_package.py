"""Build and verify Storyboard_AI_Studio_Pro_v1.3.14.zip from 1.3.13 baseline with YouTube Publishing Configuration, Language Binding, Thumbnail Watermark Cleaner, and Shorts Remixing Fixes."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import zipfile

ROOT = Path(r"D:\STORYBOARD_AI")
DIST = ROOT / "dist"
BASE = DIST / "Storyboard_AI_Studio_Pro_v1.3.13.zip"
OUT = DIST / "Storyboard_AI_Studio_Pro_v1.3.14.zip"
STAGE = DIST / "_stage_v1314"
SEVEN = Path(r"C:\Program Files\7-Zip\7z.exe")

assert BASE.is_file(), f"Baseline not found: {BASE}"
assert SEVEN.is_file(), f"7-Zip not found: {SEVEN}"

if STAGE.exists():
    shutil.rmtree(STAGE, ignore_errors=True)
STAGE.mkdir(parents=True, exist_ok=True)

# 1. Collect all target files to stage
files_to_overlay = []

# All skills
for skill_file in (ROOT / ".agents" / "skills").rglob("*"):
    if skill_file.is_file() and "__pycache__" not in skill_file.parts:
        rel = skill_file.relative_to(ROOT)
        files_to_overlay.append(str(rel).replace("\\", "/"))

# Core studio files updated in 1.3.14
studio_updates = [
    "studio/version.json",
    "studio/seo_packager.py",
    "studio/thumbnail_studio.py",
    "studio/youtube_manager.py",
    "studio/clean_watermark.py",
    "studio/series_studio.py",
    "studio/reference_scene_assembler.py",
    "studio/web_server.py",
    "studio/web/app.js",
    "studio/web/index.html",
    "studio/youtube_channels.json",
    "tools/Update-StoryboardAI.ps1",
]

for p in studio_updates:
    if (ROOT / p).is_file():
        files_to_overlay.append(p)

files_to_overlay = sorted(list(set(files_to_overlay)))
print(f"Staging {len(files_to_overlay)} files for v1.3.14 overlay...")

for rel_str in files_to_overlay:
    src = ROOT / rel_str
    dst = STAGE / rel_str
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

print("Copying baseline v1.3.13 -> v1.3.14...")
if OUT.exists():
    OUT.unlink()
shutil.copyfile(BASE, OUT)

print("Injecting staged files into v1.3.14 via 7-Zip...")
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
        "studio/clean_watermark.py",
        "studio/web_server.py",
        "studio/web/index.html",
        "tools/Update-StoryboardAI.ps1",
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
            v_content = json.loads(zf.read(matched[0]).decode("utf-8"))
            assert v_content.get("version") == "1.3.14", f"Expected version 1.3.14 inside zip, got {v_content.get('version')}"
            print(f"Verified version inside zip: {v_content.get('version')}")

# Generate latest_v1.3.14.json matching exact Update-StoryboardAI.ps1 requirements!
manifest = {
    "version": "1.3.14",
    "release_name": "Storyboard_AI_Studio_Pro_v1.3.14",
    "installer": f"https://github.com/anma8802-create/AI-tool/releases/latest/download/{OUT.name}",
    "download_url": f"https://github.com/anma8802-create/AI-tool/releases/latest/download/{OUT.name}",
    "bytes": size,
    "sha256": sha256.upper(),
    "release_notes": [
        "Sửa triệt để cấu hình xuất bản YouTube: chuẩn hóa mã ngôn ngữ BCP-47 (defaultLanguage/defaultAudioLanguage), video không còn bị lệch tiếng hay để trống.",
        "Xóa sạch 100% hình quả trám (logo ngôi sao watermark 4 cánh của Google Flow / Imagen) trên ảnh Thumbnail bằng thuật toán Inpainting Navier-Stokes đa tầng.",
        "Cơ chế tự động thử lại khi tải Thumbnail (Exponential Backoff Retry 4 lần), triệt tiêu lỗi ảnh thumbnail bị trống khi máy chủ YouTube xử lý chậm.",
        "Tự động lưu và hướng dẫn chi tiết cách tắt phối lại Shorts mặc định 1 lần duy nhất cho toàn kênh trên YouTube Studio."
    ]
}

manifest_path = DIST / "latest_v1.3.14.json"
manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Generated manifest: {manifest_path}")

# Also update root dist/latest.json
root_manifest = DIST / "latest.json"
root_manifest.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Generated root manifest: {root_manifest}")

# Generate RELEASE_NOTES_v1.3.14.md
release_notes_path = DIST / "RELEASE_NOTES_v1.3.14.md"
release_notes_content = f"""# Storyboard AI Studio Pro v1.3.14 - YouTube Publishing Alignment, Language Binding, Watermark Cleaner & Thumbnail Fixes

## 🚀 Tính năng & Sửa lỗi nổi bật

1. **Khắc phục lỗi ngôn ngữ YouTube (defaultLanguage & defaultAudioLanguage):**
   - Đã xử lý triệt để việc gắn mã chuẩn BCP-47 (`es` cho Tiếng Tây Ban Nha, `vi` cho Tiếng Việt, `en-US` cho Tiếng Anh, `ru` cho Tiếng Nga).
   - Truyền đầy đủ cả 2 trường `defaultLanguage` (ngôn ngữ tiêu đề/mô tả) và `defaultAudioLanguage` (ngôn ngữ giọng đọc) khi tải lên video tự động (`auto_upload_episode`), tải lên theo lô (`batch upload`) và cập nhật trực tiếp (`update_live_video_metadata`).
   - Khắc phục lỗi video tải lên bị mặc định thành tiếng Anh (`en-US`) hoặc để trống.

2. **Xóa sạch 100% logo quả trám (Google Flow Star Watermark) trên Thumbnail:**
   - Nâng cấp bộ khử watermark `clean_watermark.py` với thuật toán nhận diện màu xám trung tính động (Dynamic Grey Star Detector) tại góc dưới phải.
   - Tự động xóa sạch biểu tượng ngôi sao 4 cánh / quả trám của Google Flow / Imagen 3 mà không để lại bất kỳ vệt mờ nào.

3. **Khắc phục lỗi ảnh Thumbnail bị trống khi tải lên:**
   - Bổ sung cơ chế Exponential Backoff Retry (thử lại tối đa 4 lần, giãn cách 3s - 6s - 9s) khi gắn ảnh Thumbnail lên video qua YouTube API v3.
   - Tự động tạo ảnh Thumbnail trước khi tải lên nếu phát hiện tập phim chưa có sẵn.

4. **Cấu hình Quyền phối lại Shorts (Shorts Remixing):**
   - Lưu trữ lựa chọn `shorts_remix: none` vĩnh viễn trong cấu hình kênh (`publish_settings`).
   - Cung cấp hướng dẫn trực quan trên giao diện và tài liệu checklist xuất bản: hướng dẫn người dùng thiết lập 1 lần duy nhất trong *YouTube Studio &rarr; Cài đặt &rarr; Chế độ mặc định tải lên &rarr; Cài đặt nâng cao &rarr; Phối lại Shorts &rarr; Chọn "Không cho phép phối lại"*.

## 📦 Thông tin gói cập nhật
- **Tên tệp:** `{OUT.name}`
- **Kích thước:** `{size:,}` bytes
- **SHA256:** `{sha256.upper()}`
"""
release_notes_path.write_text(release_notes_content, encoding="utf-8")
print(f"Generated release notes: {release_notes_path}")
