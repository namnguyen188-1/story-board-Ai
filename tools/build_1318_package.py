"""Build and verify Storyboard_AI_Studio_Pro_v1.3.18.zip from 1.3.17 baseline.

Includes:
- Complete genre-alignment for Idea Mode (Scene 1 & Final scene isolation per genre, ART[genre] in make_bible).
- Strict Image Prompt genre branching in mcp_v2_batch.py (Whiteboard After Skool chisel markers on white background, 3D Pixar animation, 8k cinematic drama, Carrara marble statue).
- Dynamic Hint Chips + 1-Click "✨ Gợi Ý Ý Tưởng" button in Web UI.
- Strict YouTube Hashtag Guarantee: Ensure at least 3-5 high-ranking topic hashtags on both Long videos and Shorts.
- Automated FlowKit Engine Installer (flowkit_installer.py, Install-FlowKit.ps1, /api/flowkit/install_engine) for seamless 1-click engine setup on secondary machines.
- Portable launch_flow_9461.bat and removal of hardcoded username paths.
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
BASE = DIST / "Storyboard_AI_Studio_Pro_v1.3.17.zip"
OUT = DIST / "Storyboard_AI_Studio_Pro_v1.3.18.zip"
STAGE = DIST / "_stage_v1318"
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

# Core studio files updated in 1.3.18
studio_updates = [
    "studio/version.json",
    "studio/studio_input_modes.py",
    "studio/series_studio.py",
    "studio/web_server.py",
    "studio/web/app.js",
    "studio/web/index.html",
    "studio/flow_account_manager.py",
    "studio/flowkit_client.py",
    "studio/flowkit_installer.py",
    "studio/youtube_manager.py",
    "studio/flow_accounts/launch_flow_9461.bat",
    "studio/mcp_v2_batch.py",
    "studio/studio_modes.py",
    "studio/muse_video_provider.py",
    "tools/Install-FlowKit.ps1",
    "tools/Clean-OldVersions.ps1",
    "tools/Update-StoryboardAI.ps1",
]

for p in studio_updates:
    if (ROOT / p).is_file():
        files_to_overlay.append(p)

print(f"Staging {len(files_to_overlay)} files for v1.3.18 overlay...")
for rel_path in files_to_overlay:
    src = ROOT / rel_path
    dst = STAGE / rel_path
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

# 2. Duplicate base zip to target output zip
print(f"Copying baseline v1.3.17 -> v1.3.18...")
shutil.copy2(BASE, OUT)

# 3. Use 7-Zip to update the archive in-place with staged files
print("Injecting staged files into v1.3.18 via 7-Zip...")
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
print(f"SUCCESS: Storyboard_AI_Studio_Pro_v1.3.18.zip")
print(f"SIZE:    {file_size:,} bytes")
print(f"SHA256:  {sha256_hash}")
print("=" * 55 + "\n")

# Verify critical files inside the zip
with zipfile.ZipFile(OUT, "r") as z:
    names = z.namelist()
    for check in [
        "studio/version.json",
        "studio/series_studio.py",
        "studio/flowkit_installer.py",
        "studio/youtube_manager.py",
        "studio/flow_accounts/launch_flow_9461.bat",
        "studio/mcp_v2_batch.py",
        "studio/web/app.js",
        "studio/web/index.html",
        "tools/Install-FlowKit.ps1",
    ]:
        if check in names:
            print(f"  Verified in zip: {check}")
        else:
            print(f"  MISSING in zip: {check}")

# 6. Generate latest.json
latest_data = {
    "version": "1.3.18",
    "app_name": "Storyboard AI Studio Pro",
    "release_date": "2026-11-04",
    "url": "https://github.com/anma8802-create/AI-tool/releases/download/v1.3.18/Storyboard_AI_Studio_Pro_v1.3.18.zip",
    "installer": "https://github.com/anma8802-create/AI-tool/releases/download/v1.3.18/Storyboard_AI_Studio_Pro_v1.3.18.zip",
    "download_url": "https://github.com/anma8802-create/AI-tool/releases/download/v1.3.18/Storyboard_AI_Studio_Pro_v1.3.18.zip",
    "fallback_urls": [
        "https://github.com/namnguyen188-1/story-board-Ai/releases/download/v1.3.18/Storyboard_AI_Studio_Pro_v1.3.18.zip"
    ],
    "sha256": sha256_hash,
    "size_bytes": file_size,
    "bytes": file_size,
    "release_notes": [
        "Chuan hoa 100% Muc Y Tuong theo The Loai: Tach rieng logic Hook Mo Man Canh 1 & Canh Ket theo tung the loai (Family Drama, Romance, Whiteboard, Animation, Crime Mafia, Horror, Stoic).",
        "Khu triet de hien tuong ep vu khi dao sung mau me, danh dam vao Drama gia dinh va Ngon tinh lang man.",
        "Nap truc tiep dac ta chuan the loai (ART[genre]) vao ham make_bible() giup AI tao nhan vat va the gioi dong bo 100% tu Canh 1 den Canh cuoi.",
        "Phan luong prompt ve anh doc lap trong mcp_v2_batch.py: Whiteboard khoa net but da tren bang trang After Skool (khu anh chup nguoi that 8k), Animation khoa net 3D Pixar/Disney CGI.",
        "Tich hop Bo Cai Dat Dong Co FlowKit Tu Dong (flowkit_installer.py, Install-FlowKit.ps1) va nut 1-Click tren Web giup may phu setup dong co 100% tron goi khong bi thieu phu thuoc.",
        "Bao ve tuyet doi Hashtag YouTube: Luon tu dong day du 3-5 hashtag chu de chat luong cao vao noi dung mo ta cho ca video dai 16:9 va Shorts 9:16, khong con bi thieu hashtag khi dang.",
        "The goi y cot truyen dong (Dynamic Hint Chips) tren Web UI tu dong bien doi theo The Loai da chon.",
        "Tich hop nut 1-Click 'Goi Y Y Tuong' tu dong dien cot truyen trieu view chuan the loai vao o nhap lieu."
    ],
    "changelog": [
        "Chuẩn hóa 100% Mục Ý Tưởng theo Thể Loại: Tách riêng logic Hook Mở Màn Cảnh 1 & Cảnh Kết theo từng thể loại (Family Drama, Romance, Whiteboard, Animation, Crime Mafia, Horror, Stoic).",
        "Khử triệt để hiện tượng ép vũ khí dao súng máu me, đánh đấm vào Drama gia đình và Ngôn tình lãng mạn.",
        "Nạp trực tiếp đặc tả chuẩn thể loại (ART[genre]) vào hàm make_bible() giúp AI tạo nhân vật và thế giới đồng bộ 100% từ Cảnh 1 đến Cảnh cuối.",
        "Phân luồng prompt vẽ ảnh độc lập trong mcp_v2_batch.py: Whiteboard khóa nét bút dạ trên bảng trắng After Skool (khử ảnh chụp người thật 8k), Animation khóa nét 3D Pixar/Disney CGI.",
        "Tích hợp Bộ Cài Đặt Động Cơ FlowKit Tự Động (flowkit_installer.py, Install-FlowKit.ps1) và nút 1-Click trên Web giúp máy phụ setup động cơ 100% trọn gói không bị thiếu phụ thuộc.",
        "Bảo đảm tuyệt đối Hashtag YouTube: Luôn tự động đẩy đủ 3-5 hashtag chủ đề chất lượng cao vào nội dung mô tả cho cả video dài 16:9 và Shorts 9:16, không còn bị thiếu hashtag khi đăng.",
        "Thẻ gợi ý cốt truyện động (Dynamic Hint Chips) trên Web UI tự động biến đổi theo Thể Loại đã chọn.",
        "Tích hợp nút 1-Click '✨ Gợi Ý Ý Tưởng' tự động điền cốt truyện triệu view chuẩn thể loại vào ô nhập liệu."
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

latest_v1318 = DIST / "latest_v1.3.18.json"
with open(latest_v1318, "w", encoding="utf-8") as f:
    json.dump(latest_data, f, indent=2, ensure_ascii=False)
print(f"Generated {latest_v1318}")
