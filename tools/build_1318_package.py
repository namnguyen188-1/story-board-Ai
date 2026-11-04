"""Build and verify Storyboard_AI_Studio_Pro_v1.3.18.zip from 1.3.17 baseline.

Includes:
- Complete genre-alignment for Idea Mode:
  1. Injected genre specification (ART[genre]) directly into make_bible() for authentic character and world generation.
  2. Isolated Scene 1 Cold Open and Final Scene rules per genre: Family Drama (domestic conflict/will/dinner confrontation, zero weapons/blood), Romance Melodrama (heartbreaking crossroads, longing, zero violence), Whiteboard (After Skool intellectual hook, witty voiceover, marker drawings), Animation (Pixar/Disney 3D adventure hook, family-friendly cartoon acting), Psychological Horror (atmospheric dread, chilling suspense, paranoia), Stoic (intact marble statue, philosophical reflection).
  3. Image prompt genre isolation in mcp_v2_batch.py: Whiteboard strictly renders colored markers on white background, Animation renders 3D stylized CGI, Drama renders authentic cinematic film stills.
  4. Web UI Dynamic Hint Chips: chips change dynamically based on inGenre dropdown.
  5. 1-Click AI Idea Generator button (btnSuggestIdea) to cycle viral high-retention premises per genre.
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
    "studio/mcp_v2_batch.py",
    "studio/studio_modes.py",
    "studio/muse_video_provider.py",
    "studio/youtube_channels.json",
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
        "studio/mcp_v2_batch.py",
        "studio/web/app.js",
        "studio/web/index.html",
    ]:
        if check in names:
            print(f" Verified in zip: {check}")
        else:
            print(f" MISSING in zip: {check}")

# 6. Generate latest.json
latest_data = {
    "version": "1.3.18",
    "release_date": "2026-11-04",
    "url": "https://github.com/anma8802-create/AI-tool/releases/download/v1.3.18/Storyboard_AI_Studio_Pro_v1.3.18.zip",
    "download_url": "https://github.com/anma8802-create/AI-tool/releases/download/v1.3.18/Storyboard_AI_Studio_Pro_v1.3.18.zip",
    "fallback_urls": [
        "https://github.com/namnguyen188-1/story-board-Ai/releases/download/v1.3.18/Storyboard_AI_Studio_Pro_v1.3.18.zip"
    ],
    "sha256": sha256_hash,
    "size_bytes": file_size,
    "bytes": file_size,
    "changelog": [
        "Chuẩn hóa 100% Mục Ý Tưởng theo Thể Loại: Tách riêng cấu trúc Hook Mở Màn Cảnh 1 và Kết Thúc cho Drama Gia Đình, Ngôn Tình, Bảng Trắng After Skool, Hoạt Hình, Trinh Thám Mafia, Kinh Dị, Khắc Kỷ.",
        "Khử triệt để hiện tượng ép dao súng máu me, la hét kinh hoàng vào Drama gia đình và Ngôn tình lãng mạn.",
        "Nạp trực tiếp bản đặc tả chuẩn thể loại (ART[genre]) vào hàm make_bible() để AI xây dựng nhân vật và thế giới câu chuyện đúng 100% phong cách thể loại.",
        "Phân luồng prompt vẽ ảnh trong mcp_v2_batch.py: Whiteboard khóa cứng nét vẽ bút dạ nét sketch trên nền trắng After Skool (loại bỏ ảnh chụp người thật 8k), Animation khóa chuẩn 3D Pixar/Disney.",
        "Thẻ gợi ý cốt truyện động (Dynamic Hint Chips) trên Web UI tự động biến đổi theo Thể Loại đã chọn.",
        "Tích hợp nút 1-Click '✨ Gợi Ý Ý Tưởng' tự động sinh cốt truyện triệu view chuẩn thể loại vào ô nhập liệu."
    ]
}

latest_path = DIST / "latest.json"
with open(latest_path, "w", encoding="utf-8") as f:
    json.dump(latest_data, f, indent=2, ensure_ascii=False)
print(f"Generated {latest_path}")
