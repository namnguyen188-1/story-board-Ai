"""Build and verify Storyboard_AI_Studio_Pro_v1.3.15.zip from 1.3.14 baseline.

Includes:
- Fix for Chrome launch failure on secondary machine (direct interactive desktop Popen + ShellExecuteW SW_SHOWNORMAL).
- Removal of Session 0 isolation, schtasks, WinSta0\Default Access Denied.
- Dynamic Chrome detection (registry + ProgramFiles across drives + Edge fallback).
- Safe window enumeration and SW_RESTORE foregrounding.
- FlowKit Gateway autostart resilience (Start_API.vbs, launcher.py, multi-python search, uvicorn).
- Account DB and CDP port alignment (port 9461 / 9462) with email persistence upon login.
- Portability sanitization removing C:\\Users\\thean references.
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
BASE = DIST / "Storyboard_AI_Studio_Pro_v1.3.14.zip"
OUT = DIST / "Storyboard_AI_Studio_Pro_v1.3.15.zip"
STAGE = DIST / "_stage_v1315"
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

# Core studio files updated in 1.3.15
studio_updates = [
    "studio/version.json",
    "studio/flow_account_manager.py",
    "studio/flowkit_client.py",
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
print(f"Staging {len(files_to_overlay)} files for v1.3.15 overlay...")

for rel_str in files_to_overlay:
    src = ROOT / rel_str
    dst = STAGE / rel_str
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

print("Copying baseline v1.3.14 -> v1.3.15...")
if OUT.exists():
    OUT.unlink()
shutil.copyfile(BASE, OUT)

print("Injecting staged files into v1.3.15 via 7-Zip...")
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
        "studio/flowkit_client.py",
        "studio/youtube_manager.py",
        "studio/thumbnail_studio.py"
    ]:
        assert check_file in namelist, f"Missing {check_file} in zip!"
        print(f" Verified in zip: {check_file}")

# Write latest.json and latest_v1.3.15.json
latest_manifest = {
    "version": "1.3.15",
    "app_name": "Storyboard AI Studio Pro",
    "release_date": "2026-11-04",
    "download_url": "https://github.com/anma8802-create/AI-tool/releases/download/v1.3.15/Storyboard_AI_Studio_Pro_v1.3.15.zip",
    "installer": "https://github.com/anma8802-create/AI-tool/releases/download/v1.3.15/Storyboard_AI_Studio_Pro_v1.3.15.zip",
    "sha256": sha256,
    "size_bytes": size,
    "changelog": [
        "Sua loi may phu khong dang nhap duoc Google Flow (khac phuc triet de Session 0 isolation, WinSta0\\Default Access Denied).",
        "Trinh duyet Chrome mo truc tiep tren man hinh tuong tac cua nguoi dung qua ShellExecuteW va subprocess.Popen.",
        "Bo sung tham so --disable-blink-features=AutomationControlled chong Google chan dang nhap tren trinh duyet tu dong.",
        "Tu dong quet va tim kiem Chrome trong Registry HKLM/HKCU va tat ca o dia (fallback Edge neu chua cai Chrome).",
        "Nang cap khoi dong tu dong FlowKit Gateway qua Start_API.vbs, launcher.py va tim kiem Python da duong dan.",
        "Dong bo chinh xac cong CDP (9461/9462) va luu tru email tai khoan sau khi dang nhap thanh cong.",
        "Tu dong chuan hoa va xoa bo cac duong dan tuyet doi may chinh (C:\\Users\\thean) dam bao tinh tuong thich 100% tren may phu."
    ]
}

(DIST / "latest.json").write_text(json.dumps(latest_manifest, indent=2, ensure_ascii=False), encoding="utf-8")
(DIST / "latest_v1.3.15.json").write_text(json.dumps(latest_manifest, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Generated {DIST / 'latest.json'}")

# Generate RELEASE_NOTES_v1.3.15.md
release_notes = """# Storyboard AI Studio Pro - Phiên bản v1.3.15

### 🚀 Bản vá quan trọng: Khắc phục sự cố đăng nhập Google Flow & FlowKit trên Máy Phụ

1. **Mở trình duyệt tương tác trực tiếp trên màn hình vật lý**:
   - Loại bỏ hoàn toàn Task Scheduler (`schtasks`) và `WinSta0\\Default` - nguyên nhân gây lỗi *Session 0 isolation* và *Access Denied*, khiến cửa sổ Chrome chạy ngầm vô hình không thể hiện lên màn hình.
   - Sử dụng `ShellExecuteW` (`SW_SHOWNORMAL`) kết hợp `subprocess.Popen` giúp Chrome luôn xuất hiện ngay trước mắt người dùng để đăng nhập.
   - Thêm cờ `--disable-blink-features=AutomationControlled` ngăn Google hiển thị cảnh báo chặn đăng nhập trình duyệt bảo mật.

2. **Tự động quét Chrome trên toàn hệ thống**:
   - Tra cứu trực tiếp Windows Registry (`HKLM` & `HKCU\\...\\App Paths\\chrome.exe`), tìm kiếm trên mọi ổ đĩa (`C:`, `D:`, `%LOCALAPPDATA%`), và tự động fallback sang `msedge.exe` nếu máy phụ chưa cài Chrome.

3. **Tự động kích hoạt FlowKit Gateway**:
   - Cơ chế tự khởi động FlowKit đa tầng qua `Start_API.vbs`, `launcher.py`, dò tìm môi trường Python linh hoạt, giúp `FlowKit WebTool` kết nối trực tiếp (`🟢 Online 18110`).

4. **Đồng bộ đa tài khoản & Lưu email chính xác**:
   - Khớp chính xác cổng CDP (`9461`, `9462`) giữa Chrome và cơ sở dữ liệu `storyboard_accounts.json`.
   - Tự động bắt email và lưu vào danh sách tài khoản ngay khi người dùng đăng nhập thành công.
   - Cơ chế Portable tự động chuyển đổi các đường dẫn máy chính (`C:\\Users\\thean`) sang thư mục workspace của máy phụ mà không gây xung đột.
"""
(DIST / "RELEASE_NOTES_v1.3.15.md").write_text(release_notes, encoding="utf-8")
print(f"Generated {DIST / 'RELEASE_NOTES_v1.3.15.md'}")
