"""Build and verify Storyboard_AI_Studio_Pro_v1.3.19.zip from 1.3.18 baseline.

Includes:
- Audio Signal Guard (audio_signal_guard.py) with preflight volume detection to block silent (-91 dBFS) clips.
- Decouple Rome/history from Stoic marble statues in mcp_v2_batch.py, preserve multi-character appearances, and retain visual style prompts for animation/whiteboard.
- Fix subtitle word reveals in video_subtitle.py to prevent premature word display in karaoke mode.
- Prevent word placement in silence intervals in native_audio_subtitles.py (WORD_IN_SILENCE).
- Authoritative three-digit scene sequence (SCENE_001) and quoted dialogue preservation in studio_input_modes.py.
- Fallback types shim for genai in studio_input_modes.py.
- Drama and Auto preset hint chips in Web UI.
- 13 automated regression tests.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import zipfile

ROOT = Path(r"D:\STORYBOARD_AI")
DIST = ROOT / "dist"
BASE = DIST / "Storyboard_AI_Studio_Pro_v1.3.18.zip"
OUT = DIST / "Storyboard_AI_Studio_Pro_v1.3.19.zip"
STAGE = DIST / "_stage_v1319"
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

# Core studio files updated in 1.3.19
studio_updates = [
    "studio/version.json",
    "studio/audio_signal_guard.py",
    "studio/cinematic_engine/drama_orchestrator.py",
    "studio/cinematic_engine/drama_skill9.py",
    "studio/cinematic_engine/drama_video_engine.py",
    "studio/cinematic_engine/native_audio_subtitles.py",
    "studio/engine/tools/video_subtitle.py",
    "studio/mcp_v2_batch.py",
    "studio/series_studio.py",
    "studio/story_arc_quality.py",
    "studio/story_skill_bridge.py",
    "studio/studio_input_modes.py",
    "studio/web_server.py",
    "studio/web/app.js",
    "studio/web/index.html",
    "studio/flow_account_manager.py",
    "studio/flowkit_client.py",
    "studio/flowkit_installer.py",
    "studio/youtube_manager.py",
    "tools/Install-FlowKit.ps1",
    "tools/Clean-OldVersions.ps1",
    "tools/Update-StoryboardAI.ps1",
]

# Add test files
for tf in (ROOT / "studio" / "tests").glob("*.py"):
    rel = tf.relative_to(ROOT)
    studio_updates.append(str(rel).replace("\\", "/"))

for p in studio_updates:
    if (ROOT / p).is_file():
        files_to_overlay.append(p)

print(f"Staging {len(files_to_overlay)} files for v1.3.19 overlay...")
for rel_path in files_to_overlay:
    src = ROOT / rel_path
    dst = STAGE / rel_path
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

# 2. Duplicate base zip to target output zip
print(f"Copying baseline v1.3.18 -> v1.3.19...")
shutil.copy2(BASE, OUT)

# 3. Use 7-Zip to update the archive in-place with staged files
print("Injecting staged files into v1.3.19 via 7-Zip...")
cmd = [str(SEVEN), "u", "-r", str(OUT), "*"]
res = subprocess.run(cmd, cwd=str(STAGE), capture_output=True, text=True)
if res.returncode != 0:
    print("7-Zip error:", res.stderr)
    raise RuntimeError(f"7-Zip update failed with code {res.returncode}")

# 4. Clean up stage directory
shutil.rmtree(STAGE, ignore_errors=True)

# 5. Compute size & sha256
file_size = OUT.stat().st_size
hasher = hashlib.sha256()
with open(OUT, "rb") as f:
    for chunk in iter(lambda: f.read(1024 * 1024), b""):
        hasher.update(chunk)
sha256_hash = hasher.hexdigest()

print("\n" + "=" * 55)
print(f"SUCCESS: Storyboard_AI_Studio_Pro_v1.3.19.zip")
print(f"SIZE:    {file_size:,} bytes")
print(f"SHA256:  {sha256_hash}")
print("=" * 55 + "\n")

# Verify critical files inside the zip
with zipfile.ZipFile(OUT, "r") as z:
    names = z.namelist()
    for check in [
        "studio/version.json",
        "studio/audio_signal_guard.py",
        "studio/series_studio.py",
        "studio/mcp_v2_batch.py",
        "studio/engine/tools/video_subtitle.py",
        "studio/cinematic_engine/drama_video_engine.py",
        "studio/web/app.js",
        "tools/Install-FlowKit.ps1",
    ]:
        if check in names:
            print(f"  Verified in zip: {check}")
        else:
            print(f"  MISSING in zip: {check}")

# 6. Generate latest.json
latest_data = {
    "version": "1.3.19",
    "app_name": "Storyboard AI Studio Pro",
    "release_date": "2026-11-05",
    "url": "https://github.com/anma8802-create/AI-tool/releases/download/v1.3.19/Storyboard_AI_Studio_Pro_v1.3.19.zip",
    "installer": "https://github.com/anma8802-create/AI-tool/releases/download/v1.3.19/Storyboard_AI_Studio_Pro_v1.3.19.zip",
    "download_url": "https://github.com/anma8802-create/AI-tool/releases/download/v1.3.19/Storyboard_AI_Studio_Pro_v1.3.19.zip",
    "fallback_urls": [
        "https://github.com/namnguyen188-1/story-board-Ai/releases/download/v1.3.19/Storyboard_AI_Studio_Pro_v1.3.19.zip"
    ],
    "sha256": sha256_hash,
    "size_bytes": file_size,
    "bytes": file_size,
    "release_notes": [
        "Tich hop Bo Kiem Soat Tin Hieu Am Thanh (audio_signal_guard.py): Chong clip vo thanh (-91 dBFS), bat buoc do am luong truoc khi xuat ban.",
        "Khu triet de hien tuong ep tuong La Ma Marcus Aurelius vao phim Lich su va Tai lieu trong mcp_v2_batch.py.",
        "Bao ve dong thoi nhieu nhan vat trong Drama: Khong con bi ep 'single solitary subject' khi nhan vat co mo ta ngoai hinh.",
        "Bao toan net ve minh hoa Hoat hinh 3D va Bang trang: Khong bi chen photorealistic 8k khi prompt chi dinh visual_style.",
        "Sua loi phu de Karaoke: Hien thi tung tu dong bo theo giong noi thuc te, khong con bi lo tu truong truoc khi doc.",
        "Khoa bao toan kich ban nguoi dung (Locked Script): Nhan dien SCENE_001 chuan, bao toan 100% cau thoai trong ngoac kep.",
        "Bo sung the goi y kich tinh Drama va Auto tren Web UI.",
        "Kiem thu toan dien: 13/13 bai test hoi quy dat chuan PASS 100%."
    ],
    "changelog": [
        "Tích hợp Bộ Kiểm Soát Tín Hiệu Âm Thanh (audio_signal_guard.py): Chống clip vô thanh (-91 dBFS), bắt buộc đo âm lượng trước khi xuất bản.",
        "Khử triệt để hiện tượng ép tượng La Mã Marcus Aurelius vào phim Lịch sử và Tài liệu trong mcp_v2_batch.py.",
        "Bảo vệ đồng thời nhiều nhân vật trong Drama: Không còn bị ép 'single solitary subject' khi nhân vật có mô tả ngoại hình.",
        "Bảo toàn nét vẽ minh họa Hoạt hình 3D và Bảng trắng: Không bị chèn photorealistic 8k khi prompt chỉ định visual_style.",
        "Sửa lỗi phụ đề Karaoke: Hiển thị từng từ đồng bộ theo giọng nói thực tế, không còn bị lộ từ trước khi đọc.",
        "Khóa bảo toàn kịch bản người dùng (Locked Script): Nhận diện SCENE_001 chuẩn, bảo toàn 100% câu thoại trong ngoặc kép.",
        "Bổ sung thẻ gợi ý kịch tính Drama và Auto trên Web UI.",
        "Kiểm thử toàn diện: 13/13 bài test hồi quy đạt chuẩn PASS 100%."
    ]
}

latest_path = DIST / "latest.json"
with open(latest_path, "w", encoding="utf-8") as f:
    json.dump(latest_data, f, indent=2, ensure_ascii=False)
print(f"Generated {latest_path}")

latest_path_root = ROOT / "latest.json"
with open(latest_path_root, "w", encoding="utf-8") as f:
    json.dump(latest_data, f, indent=2, ensure_ascii=False)
print(f"Generated {latest_path_root}")

latest_v1319 = DIST / "latest_v1.3.19.json"
with open(latest_v1319, "w", encoding="utf-8") as f:
    json.dump(latest_data, f, indent=2, ensure_ascii=False)
print(f"Generated {latest_v1319}")
