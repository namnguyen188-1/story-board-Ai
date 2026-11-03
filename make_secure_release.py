"""Storyboard AI Studio Pro - Secure Release Packaging & Audit Script.

Creates a 100% clean, commercial, production-ready release distribution:
- Strips all developer API keys, .env credentials, and private OAuth tokens.
- Resets YouTube channel credentials to a clean, unconfigured state.
- Excludes developer productions, character clone files, browser cookies, and caches.
- Verifies Python syntax and performs security leak scans.
- Produces a compressed release archive with SHA-256 hash and update manifest.
"""
from __future__ import annotations

import hashlib
import json
import os
import py_compile
import re
import shutil
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = Path("d:/STORYBOARD_AI").resolve()
STUDIO_DIR = ROOT_DIR / "studio"
DIST_DIR = ROOT_DIR / "dist"
VERSION = "1.3.7"
RELEASE_NAME = f"Storyboard_AI_Studio_Pro_v{VERSION}"
TARGET_DIR = DIST_DIR / RELEASE_NAME


def log(msg: str):
    print(f"[*] {msg}", flush=True)


def log_ok(msg: str):
    print(f"  [+] {msg}", flush=True)


def log_warn(msg: str):
    print(f"  [!] {msg}", flush=True)


def clean_target():
    log(f"Chuẩn bị thư mục xuất bản: {TARGET_DIR}...")
    if TARGET_DIR.exists():
        shutil.rmtree(TARGET_DIR, ignore_errors=True)
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    log_ok("Đã dọn sạch và tạo thư mục xuất bản mới.")


def copy_core_studio():
    log("Đang sao chép các module mã nguồn lõi Studio...")
    target_studio = TARGET_DIR / "studio"
    target_studio.mkdir(parents=True, exist_ok=True)

    # 1. Copy all valid Python modules from studio/
    copied_count = 0
    for p in STUDIO_DIR.glob("*.py"):
        if p.name.startswith(("test_", "scratch_test_")) or ".bak" in p.name:
            continue
        shutil.copy2(p, target_studio / p.name)
        copied_count += 1
    log_ok(f"Đã sao chép {copied_count} module Python lõi.")

    # 2. Copy Web UI directory (clean of backups and temporary files)
    log("Đang sao chép Web UI (Giao diện Studio)...")
    shutil.copytree(
        STUDIO_DIR / "web",
        target_studio / "web",
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("*.bak", "*.log", "__pycache__", ".git*")
    )
    log_ok("Đã sao chép thư mục Web UI hoàn chỉnh.")

    # 3. Copy Engine (FFmpeg and media binaries)
    if (STUDIO_DIR / "engine").is_dir():
        log("Đang sao chép Media Engine...")
        shutil.copytree(
            STUDIO_DIR / "engine",
            target_studio / "engine",
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.log", ".env", "test_scripts", "output")
        )
        log_ok("Đã sao chép Media Engine.")

    # 4. Copy studio_mcp (bridge & automation tools)
    if (STUDIO_DIR / "studio_mcp").is_dir():
        log("Đang sao chép studio_mcp...")
        shutil.copytree(
            STUDIO_DIR / "studio_mcp",
            target_studio / "studio_mcp",
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.log", ".env", "test_scripts")
        )
        log_ok("Đã sao chép studio_mcp.")

    # Preserve the production pipeline package; it is imported lazily by the router.
    cinematic = STUDIO_DIR / "cinematic_engine"
    if cinematic.is_dir():
        shutil.copytree(cinematic, target_studio / "cinematic_engine",
                        dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.bak", ".env",
                                                      "test_*", "run_e2e_*"))
        log_ok("Bundled cinematic production pipeline.")

    # 5. Create empty clean user folders
    (target_studio / "productions").mkdir(exist_ok=True)
    (target_studio / "character_clones").mkdir(exist_ok=True)
    (target_studio / "scratch").mkdir(exist_ok=True)
    (target_studio / "inbox").mkdir(exist_ok=True)
    log_ok("Đã tạo sẵn các thư mục rỗng sạch: productions/, character_clones/, scratch/, inbox/.")



def copy_muse_runtime():
    source = STUDIO_DIR / "runtime" / "muse"
    target = TARGET_DIR / "studio" / "runtime" / "muse"
    for required in ("python/python.exe", "python/python312.dll", "agent-browser.exe"):
        if not (source / required).is_file():
            raise RuntimeError("Missing Muse runtime: " + required)
    target.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source / "python", target / "python",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copy2(source / "agent-browser.exe", target / "agent-browser.exe")
    for license_file in source.glob("agent-browser-LICENSE*"):
        shutil.copy2(license_file, target / license_file.name)
    log_ok("Bundled isolated Muse runtime and login helper; no account profiles.")

def sanitize_and_inject_clean_templates():
    log("Đang áp dụng bộ lọc bảo mật & nạp cấu hình mẫu sạch...")
    target_studio = TARGET_DIR / "studio"

    # A. Clean .env.example (No developer API keys)
    env_example = target_studio / ".env.example"
    env_example.write_text(
        "# =====================================================================\n"
        "# STORYBOARD AI STUDIO PRO - CẤU HÌNH API NGUỒN\n"
        "# =====================================================================\n"
        "# Tùy chọn 1: Sử dụng Điện Toán Đám Mây Cloud AI Pro (Mặc định):\n"
        "TUANSU_BASE_URL=https://tuansuapi.store/v1\n"
        "TUANSU_API_KEY=\n"
        "TUANSU_TEXT_MODEL=gemini-flash-3.8-fast\n"
        "TUANSU_IMAGE_MODEL=gemini-3.1-flash-image-preview\n"
        "TUANSU_ENABLED=1\n\n"
        "# Tùy chọn 2: Sử dụng trực tiếp Google Gemini API Key của bạn:\n"
        "GEMINI_API_KEY=\n",
        encoding="utf-8"
    )
    # Also write a clean default .env with empty keys
    (target_studio / ".env").write_text(
        "# Khởi tạo cấu hình ban đầu\n"
        "TUANSU_BASE_URL=https://tuansuapi.store/v1\n"
        "TUANSU_API_KEY=\n"
        "TUANSU_TEXT_MODEL=gemini-flash-3.8-fast\n"
        "TUANSU_IMAGE_MODEL=gemini-3.1-flash-image-preview\n"
        "TUANSU_ENABLED=1\n"
        "GEMINI_API_KEY=\n",
        encoding="utf-8"
    )
    log_ok("Đã tạo file .env sạch (không chứa API key của lập trình viên).")

    # B. Clean youtube_channels.json (No private tokens or channel IDs)
    clean_yt = {
        "client_id": "",
        "client_secret": "",
        "active_channel_id": "",
        "channels": [],
        "series_channel_mapping": {}
    }
    (target_studio / "youtube_channels.json").write_text(
        json.dumps(clean_yt, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    log_ok("Đã tạo youtube_channels.json sạch (loại bỏ hoàn toàn token và kênh cá nhân).")

    # C. Requirements file
    req_src = STUDIO_DIR / "requirements.txt"
    if req_src.is_file():
        shutil.copy2(req_src, target_studio / "requirements.txt")
        log_ok("Đã sao chép requirements.txt.")


def copy_root_launchers():
    log("Đang sao chép các file thực thi và launcher...")

    # 1. Native C# compiled executable
    exe_src = ROOT_DIR / "Storyboard_AI_Studio.exe"
    if exe_src.is_file():
        shutil.copy2(exe_src, TARGET_DIR / "Storyboard_AI_Studio.exe")
        log_ok("Đã sao chép Storyboard_AI_Studio.exe.")

    # 2. Silent VBS launcher
    vbs_src = ROOT_DIR / "LAUNCH_STUDIO_SILENT.vbs"
    if vbs_src.is_file():
        shutil.copy2(vbs_src, TARGET_DIR / "LAUNCH_STUDIO_SILENT.vbs")
        log_ok("Đã sao chép LAUNCH_STUDIO_SILENT.vbs.")

    # 3. Standard BAT launcher
    bat_content = (
        "@echo off\n"
        "title Storyboard AI Studio Pro\n"
        "cd /d \"%~dp0\"\n"
        "if exist \"Storyboard_AI_Studio.exe\" (\n"
        "    start \"\" \"Storyboard_AI_Studio.exe\"\n"
        "    exit /b\n"
        ")\n"
        "if exist \"studio\\.venv\\Scripts\\pythonw.exe\" (\n"
        "    start \"\" \"studio\\.venv\\Scripts\\pythonw.exe\" \"studio\\desktop_app.py\"\n"
        ") else (\n"
        "    start \"\" python \"studio\\desktop_app.py\"\n"
        ")\n"
    )
    (TARGET_DIR / "KHOI_DONG_STUDIO.bat").write_text(bat_content, encoding="utf-8")
    log_ok("Đã tạo KHOI_DONG_STUDIO.bat.")

    # 4. User manual
    readme = (
        "======================================================================\n"
        f"   🎬 HƯỚNG DẪN SỬ DỤNG STORYBOARD AI STUDIO PRO v{VERSION}\n"
        "   Hệ Thống Tự Động Hóa Sản Xuất Phim Hoạt Ảnh & Xuất Bản Kép YouTube\n"
        "======================================================================\n\n"
        "1. KHỞI ĐỘNG ỨNG DỤNG:\n"
        "   - Nhấp đúp chuột vào file 'Storyboard_AI_Studio.exe' (hoặc KHOI_DONG_STUDIO.bat).\n"
        "   - Nếu là lần đầu chạy trên máy mới, hệ thống sẽ tự động kiểm tra môi trường\n"
        "     và chuẩn bị các thư viện hoàn toàn tự động 100%.\n\n"
        "2. TÍNH NĂNG MỚI NỔI BẬT TRONG BẢN v1.3.0:\n"
        "   - Xuất bản kép (🔥 Đăng Cả Hai): Tự động đẩy Video Dài 16:9 trước,\n"
        "     lấy link gắn vào bình luận ghim của Shorts 9:16 rồi đăng tiếp nối.\n"
        "   - Tự động nhận diện ngôn ngữ và khóa kênh chuẩn: Video tiếng nào tự động\n"
        "     nhảy đúng kênh cấu hình tiếng đó, tích hợp chốt chặn chống spam kênh.\n"
        "   - Tự động cắt Shorts 9:16: Tự nhận diện phân đoạn cao trào hay nhất để trích xuất.\n"
        "   - Cập nhật 1-Click: Tự động kiểm tra và nâng cấp phiên bản mới chỉ với 1 click.\n\n"
        "======================================================================\n"
    )
    (TARGET_DIR / "HUONG_DAN_SU_DUNG.txt").write_text(readme, encoding="utf-8")
    log_ok("Đã tạo HUONG_DAN_SU_DUNG.txt.")

    # 5. Tools directory with Update-StoryboardAI.ps1
    tools_src = ROOT_DIR / "tools"
    if tools_src.is_dir():
        log("Đang sao chép thư mục tools và công cụ cập nhật...")
        shutil.copytree(tools_src, TARGET_DIR / "tools", dirs_exist_ok=True)
        log_ok("Đã sao chép tools/Update-StoryboardAI.ps1.")

    # 6. Version file
    ver_file = STUDIO_DIR / "version.json"
    if ver_file.is_file():
        version_data = json.loads(ver_file.read_text(encoding="utf-8-sig"))
        version_data["version"] = VERSION
        (TARGET_DIR / "studio" / "version.json").write_text(json.dumps(version_data, indent=2), encoding="utf-8")
        log_ok("Đã sao chép studio/version.json.")


def perform_security_and_syntax_audit():
    log("Bắt đầu quy trình kiểm tra bảo mật (Security Audit) & cú pháp mã nguồn...")

    # 1. Syntax check on all packaged Python files
    error_count = 0
    for py_file in (TARGET_DIR / "studio").rglob("*.py"):
        try:
            py_compile.compile(str(py_file), doraise=True)
        except Exception as exc:
            log_warn(f"Lỗi cú pháp tại {py_file.name}: {exc}")
            error_count += 1
    if error_count > 0:
        raise RuntimeError(f"Phát hiện {error_count} file bị lỗi cú pháp Python!")
    log_ok("100% file Python vượt qua kiểm tra cú pháp thành công.")

    # 2. Strict credential and private data leak scan
    PATTERNS = [
        ("Google API Key", re.compile(r'AIza[0-9A-Za-z_-]{35}')),
        ("OpenAI / Generic Secret Key", re.compile(r'sk-[A-Za-z0-9]{32,}')),
        ("OAuth Access Token", re.compile(r'ya29\.[0-9A-Za-z_-]{50,}')),
        ("OAuth Refresh Token", re.compile(r'1//0[0-9A-Za-z_-]{40,}')),
    ]

    leaks = []
    for root, dirs, files in os.walk(TARGET_DIR):
        dirs[:] = [d for d in dirs if d not in ("node_modules", ".git", "__pycache__", "test_scripts")]
        for f in files:
            p = Path(root) / f
            if p.suffix.lower() in [".py", ".json", ".js", ".html", ".env", ".txt"]:
                try:
                    text = p.read_text(encoding="utf-8", errors="ignore")
                    for name, pat in PATTERNS:
                        matches = pat.findall(text)
                        if matches:
                            leaks.append((p.relative_to(TARGET_DIR).as_posix(), name, len(matches)))
                except Exception:
                    pass

    if leaks:
        for fpath, name, count in leaks:
            log_warn(f"PHÁT HIỆN RÒ RỈ: {fpath} chứa {count} {name}!")
        raise RuntimeError("Quy trình đóng gói bị dừng vì phát hiện khóa bí mật / token trong file đóng gói!")

    log_ok("Quy trình kiểm tra bảo mật hoàn tất: KHÔNG CÓ BẤT KỲ TOKEN HAY API KEY CÁ NHÂN NÀO!")


def create_release_archive():
    log(f"Đang nén toàn bộ bản phát hành thành file ZIP: {RELEASE_NAME}.zip...")
    zip_output = DIST_DIR / f"{RELEASE_NAME}.zip"
    if zip_output.exists():
        zip_output.unlink()

    seven_zip = r"C:\Program Files\7-Zip\7z.exe"
    if os.path.exists(seven_zip):
        log(f"Sử dụng 7-Zip Ultra Compression...")
        cmd = [seven_zip, "a", "-tzip", "-mx7", str(zip_output), str(TARGET_DIR / "*")]
        subprocess.run(cmd, capture_output=True, text=True)
    else:
        log("Sử dụng Python ZipFile...")
        shutil.make_archive(str(DIST_DIR / RELEASE_NAME), "zip", TARGET_DIR)

    file_size = zip_output.stat().st_size
    mb_size = file_size / (1024 * 1024)
    log_ok(f"File ZIP đã tạo thành công: {zip_output.name} ({mb_size:.2f} MB)")

    # Calculate SHA-256
    with open(zip_output, "rb") as f:
        sha256 = hashlib.file_digest(f, "sha256").hexdigest().upper()
    log_ok(f"Mã băm SHA-256: {sha256}")

    # Generate latest.json manifest for remote updates
    manifest = {
        "version": VERSION,
        "release_name": RELEASE_NAME,
        "installer": f"https://github.com/anma8802-create/AI-tool/releases/latest/download/{zip_output.name}",
        "bytes": file_size,
        "sha256": sha256,
        "release_notes": [
            "Include the isolated Muse core and login helper on every updated PC.",
            "Resolve Muse runtime paths independently of the developer computer.",
            "Preserve the existing interface, local accounts and projects."
        ]
    }
    manifest_path = DIST_DIR / "latest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    log_ok(f"Đã tạo manifest cập nhật: {manifest_path.name}")

    print("\n" + "=" * 70)
    print("🎉 ĐÓNG GÓI BẢO MẬT HOÀN TẤT THÀNH CÔNG 100%!")
    print(f"📁 Thư mục xuất bản sạch: {TARGET_DIR}")
    print(f"📦 File nén hoàn chỉnh: {zip_output} ({mb_size:.2f} MB)")
    print(f"🔑 Mã SHA-256: {sha256}")
    print(f"📜 File manifest cập nhật: {manifest_path}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    try:
        clean_target()
        copy_core_studio()
        copy_muse_runtime()
        sanitize_and_inject_clean_templates()
        copy_root_launchers()
        perform_security_and_syntax_audit()
        create_release_archive()
    except Exception as exc:
        print(f"\n[X] LỖI ĐÓNG GÓI: {exc}", file=sys.stderr)
        sys.exit(1)
