"""Build and verify Storyboard_AI_Studio_Pro_v1.3.16.zip from 1.3.15 baseline.

Includes:
- Fix Stoic character consistency across ALL scenes (100% pure classical Carrara marble & antique bronze statue, eliminated living flesh/vascular veins).
- Strict isolation of Stoic rules: other genres (Drama, Animation, Whiteboard, Sci-Fi) remain completely clean and unaffected.
- Revert non-Stoic skills (publish-youtube-drama, publish-youtube-narrative, publish-youtube-shorts) to clean baseline.
- Fix Google Flow WebTool connection detection: Chrome active on 9461 is immediately recognized as 🟢 Sẵn sàng (never 🔴 Chưa kết nối / Offline).
- Auto-start FlowKit Gateway in background without blocking UI.
- Top bar and Settings section 3 status synchronization.
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
BASE = DIST / "Storyboard_AI_Studio_Pro_v1.3.15.zip"
OUT = DIST / "Storyboard_AI_Studio_Pro_v1.3.16.zip"
STAGE = DIST / "_stage_v1316"
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

# Core studio files updated in 1.3.16
studio_updates = [
    "studio/version.json",
    "studio/flow_account_manager.py",
    "studio/flowkit_client.py",
    "studio/mcp_v2_batch.py",
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
print(f"Staging {len(files_to_overlay)} files for v1.3.16 overlay...")

for rel_str in files_to_overlay:
    src = ROOT / rel_str
    dst = STAGE / rel_str
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

print("Copying baseline v1.3.15 -> v1.3.16...")
if OUT.exists():
    OUT.unlink()
shutil.copyfile(BASE, OUT)

print("Injecting staged files into v1.3.16 via 7-Zip...")
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
        "studio/flow_account_manager.py",
        "studio/mcp_v2_batch.py",
        "studio/web/app.js",
        ".agents/skills/write-video-scene-prompts/references/GENRES.md"
    ]:
        assert check_file in namelist, f"Missing {check_file} in zip!"
        print(f" Verified in zip: {check_file}")

# Write latest.json and latest_v1.3.16.json
latest_manifest = {
    "version": "1.3.16",
    "app_name": "Storyboard AI Studio Pro",
    "release_date": "2026-11-04",
    "download_url": "https://github.com/anma8802-create/AI-tool/releases/download/v1.3.16/Storyboard_AI_Studio_Pro_v1.3.16.zip",
    "installer": "https://github.com/anma8802-create/AI-tool/releases/download/v1.3.16/Storyboard_AI_Studio_Pro_v1.3.16.zip",
    "sha256": sha256,
    "size_bytes": size,
    "bytes": size,
    "changelog": [
        "Sua triet de loi nua tuong nua nguoi cho the loai Khac Ky (Stoic): Khoa 100% tat ca cac canh thanh Tuong da Carrara nguyen khoi va dong co dien, loai bo hoan toan cac thuoc tinh da nguoi/mach mau (vascular arms, real skin).",
        "Tach biet tuyet doi quy tac Khac Ky: Khong lam anh huong hay ap dat quy tac tuong da len cac the loai khac (Phim Kich Da Vai, Ke Chuyen, Bang Trang, Hoat Hinh).",
        "Sua loi hien thi ket noi WebTool Google Flow: Nhan dien tu dong Chrome Google Flow dang hoat dong tren cong 9461, chuyen ngay trang thai sang 🟢 San sang (thay vi bao do Chua ket noi / Offline).",
        "Tu dong kich hoat FlowKit Gateway ngam khi Chrome mo, dong bo nhan thanh cong cu va hop trang thai khong bi xung dot.",
        "Cap nhat dong bo toan bo prompt cac phan canh hien tai thanh tuong da Carrara chuan xac 100%."
    ]
}

(DIST / "latest.json").write_text(json.dumps(latest_manifest, indent=2, ensure_ascii=False), encoding="utf-8")
(DIST / "latest_v1.3.16.json").write_text(json.dumps(latest_manifest, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Generated {DIST / 'latest.json'}")

# Generate RELEASE_NOTES_v1.3.16.md
release_notes = """# Storyboard AI Studio Pro - Phiên bản v1.3.16

### 🏛️ Bản vá hoàn thiện: Đồng nhất 100% Tượng đá Khắc Kỷ & Nhận diện Kết nối Google Flow

1. **Khắc phục triệt để lỗi "Nửa tượng nửa người" cho thể loại Khắc Kỷ (Stoic)**:
   - Loại bỏ hoàn toàn các từ khóa da thịt/mạch máu người sống (`vascular arms`, `sun-kissed skin`, `muscular chest`) trong prompt tạo ảnh.
   - Khóa 100% mọi phân cảnh thành **Tượng điêu khắc đá cẩm thạch Carrara cổ điển nguyên khối kết hợp đồng cổ**, râu tóc nếp nhăn và áo choàng toga chạm khắc tinh xảo.
   - Thêm quy tắc ràng buộc âm bản (`negative constraints`): *100% pure carved classical stone sculpture throughout, never living human flesh, never real skin pores, never vascular veins, never modern clothes*.
   - Đảm bảo tính nhất quán tuyệt đối từ cảnh đầu đến cảnh cuối.

2. **Cách ly tuyệt đối nhánh Khắc Kỷ**:
   - Chỉ áp dụng quy tắc tượng đá cẩm thạch cho thể loại Khắc Kỷ (`stoic` / `philosophy`).
   - Các bộ skill khác (Phim Kịch Đa Vai, Kể Chuyện, Bảng Trắng, Hoạt Hình 2D) được bảo toàn nguyên vẹn 100%, không bị ảnh hưởng.

3. **Sửa lỗi hiển thị kết nối WebTool Google Flow**:
   - Khi trình duyệt Chrome đang mở và đã đăng nhập `flow.google.com` (cổng 9461), hệ thống tự động nhận diện và hiển thị huy hiệu `🟢 Sẵn sàng` (thay vì báo đỏ `🔴 Chưa kết nối` hoặc `Offline`).
   - Tự động chạy ngầm FlowKit Gateway (Cổng 18110) để sẵn sàng xử lý yêu cầu mà không bắt người dùng bấm nút thủ công.
   - Đồng bộ hóa trạng thái trên thanh điều hướng trên cùng và bảng cài đặt tài khoản.
"""

(DIST / "RELEASE_NOTES_v1.3.16.md").write_text(release_notes, encoding="utf-8")
print(f"Generated {DIST / 'RELEASE_NOTES_v1.3.16.md'}")
