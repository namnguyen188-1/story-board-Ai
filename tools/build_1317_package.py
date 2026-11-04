"""Build and verify Storyboard_AI_Studio_Pro_v1.3.17.zip from 1.3.16 baseline.

Includes:
- Fix script mode (Kịch bản có sẵn) failure: support flexible scene headers (CẢNH, SHOT, SCENE, PHẦN, ĐOẠN, 1., 2...) and intelligent auto-segmentation when raw unformatted text is provided.
- Fix fixed 20-image lock: dynamically synchronize Số Ảnh (inMcpMaxImages) with Cảnh (Giây) (e.g. 7s) and Thời Lượng (inMinutes), eliminating the frozen 20-image issue.
- Prevent incomplete episode auto-resume from hijacking and overwriting fresh custom scripts.
- Retain built-in 1-click cleanup and auto-pruning.
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
BASE = DIST / "Storyboard_AI_Studio_Pro_v1.3.16.zip"
OUT = DIST / "Storyboard_AI_Studio_Pro_v1.3.17.zip"
STAGE = DIST / "_stage_v1317"
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

# Core studio files updated in 1.3.17
studio_updates = [
    "studio/version.json",
    "studio/studio_input_modes.py",
    "studio/series_studio.py",
    "studio/web_server.py",
    "studio/web/app.js",
    "studio/web/index.html",
    "studio/flow_account_manager.py",
    "studio/mcp_v2_batch.py",
    "studio/youtube_channels.json",
    "tools/Clean-OldVersions.ps1",
    "tools/Update-StoryboardAI.ps1",
]

for p in studio_updates:
    if (ROOT / p).is_file():
        files_to_overlay.append(p)

files_to_overlay = sorted(list(set(files_to_overlay)))
print(f"Staging {len(files_to_overlay)} files for v1.3.17 overlay...")

for rel_str in files_to_overlay:
    src = ROOT / rel_str
    dst = STAGE / rel_str
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

print("Copying baseline v1.3.16 -> v1.3.17...")
if OUT.exists():
    OUT.unlink()
shutil.copyfile(BASE, OUT)

print("Injecting staged files into v1.3.17 via 7-Zip...")
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
        "studio/studio_input_modes.py",
        "studio/series_studio.py",
        "studio/web_server.py",
        "studio/web/app.js",
        "tools/Clean-OldVersions.ps1"
    ]:
        assert check_file in namelist, f"Missing {check_file} in zip!"
        print(f" Verified in zip: {check_file}")

# Write latest.json and latest_v1.3.17.json
latest_manifest = {
    "version": "1.3.17",
    "app_name": "Storyboard AI Studio Pro",
    "release_date": "2026-11-04",
    "download_url": "https://github.com/anma8802-create/AI-tool/releases/download/v1.3.17/Storyboard_AI_Studio_Pro_v1.3.17.zip",
    "installer": "https://github.com/anma8802-create/AI-tool/releases/download/v1.3.17/Storyboard_AI_Studio_Pro_v1.3.17.zip",
    "sha256": sha256,
    "size_bytes": size,
    "bytes": size,
    "changelog": [
        "Sua triet de loi Che do kich ban khong chay duoc: Mo rong nhan dien linh hoat tat ca cac kieu phan canh (CANH, SHOT, SCENE, PHAN, DOAN, 1., 2...), tu dong phan tach doan van thanh cac canh hoan chinh khop voi thoi luong (7s) neu dan van ban tu do.",
        "Khac phuc loi co dinh 20 anh: Dong bo dong thoi luong va so canh theo thoi gian moi canh (7s/canh), So Anh (inMcpMaxImages) tu dong tinh toan chinh xac khong con bi dong bang o so 20.",
        "Ngan chan co che tu dong resume de len kich ban moi: Dam bao tap moi hoac kich ban moi luon chay dung tu canh 1.",
        "Tich hop nut 1-Click Don dep ban cu va bo nho tam ngay trong cai dat giup giai phong dung luong o cung tren ca may chinh va may phu."
    ]
}

(DIST / "latest.json").write_text(json.dumps(latest_manifest, indent=2, ensure_ascii=False), encoding="utf-8")
(DIST / "latest_v1.3.17.json").write_text(json.dumps(latest_manifest, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Generated {DIST / 'latest.json'}")

# Generate RELEASE_NOTES_v1.3.17.md
release_notes = """# Storyboard AI Studio Pro - Phiên bản v1.3.17

### 🎬 Bản vá: Khắc phục Chế độ Kịch Bản & Đồng bộ động Số Lượng Ảnh (7s/cảnh)

1. **Khắc phục lỗi Chế độ Kịch bản (🔒 Kịch bản có sẵn) không chạy**:
   - **Nhận diện phân cảnh linh hoạt**: Tự động nhận diện mọi cách viết phân cảnh (`CẢNH 1`, `Cảnh 01:`, `SHOT 1`, `SCENE 1`, `PHẦN 1`, `ĐOẠN 1`, `1.`, `2.`...).
   - **Tự động phân tách kịch bản thông minh (Auto-segmentation)**: Nếu người dùng dán văn bản tự do, truyện ngắn hay lời thoại không có từ khóa `CẢNH`, hệ thống tự động phân tách các đoạn văn thành từng phân cảnh hoàn chỉnh khớp với thời lượng (mặc định 7s/cảnh), không bao giờ văng lỗi `ValueError` hay dừng chạy.
   - **Xóa bỏ bẫy tự động Resume**: Ngăn chặn tình trạng tập cũ dở dang tự động đè lên kịch bản mới của người dùng.

2. **Khắc phục lỗi "Cố định 20 ảnh"**:
   - Cập nhật hàm tính toán `syncAutoImageBudget` & `estimatedImageScenes`: Khi thay đổi `Thời Lượng` hoặc `Cảnh (Giây)` (ví dụ chọn 7s), ô **Số Ảnh** sẽ tự động nhảy số theo đúng công thức phân cảnh thực tế.
   - Không bị đóng băng ở con số 20 khi chuyển chế độ hoặc khi dán kịch bản mới.

3. **Tích hợp tính năng Dọn dẹp bản cũ & Bộ nhớ tạm 1-Click**:
   - Nút bấm `🧹 Dọn Dẹp Bản Cũ & Bộ Nhớ Tạm` trong phần Cài Đặt và script `Clean-OldVersions.ps1` sẵn sàng trên cả máy chính và máy phụ.
"""

(DIST / "RELEASE_NOTES_v1.3.17.md").write_text(release_notes, encoding="utf-8")
print(f"Generated {DIST / 'RELEASE_NOTES_v1.3.17.md'}")
