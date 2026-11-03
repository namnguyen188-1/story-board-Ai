"""Automated Packaging Tool for Storyboard AI Studio Pro Release Distribution.
Creates a clean, commercial, production-ready release folder and ZIP archive,
stripping all developer test files, temporary scratch files, private test productions,
and git traces.
"""
from __future__ import annotations

import os
import shutil
import sys
import zipfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = Path("d:/STORYBOARD_AI").resolve()
STUDIO_DIR = ROOT_DIR / "studio"
DIST_DIR = ROOT_DIR / "dist"
RELEASE_NAME = "Storyboard_AI_Studio_Pro_v1.0"
TARGET_DIR = DIST_DIR / RELEASE_NAME

# Essential Core Application Files
CORE_STUDIO_FILES = [
    "desktop_app.py",
    "web_server.py",
    "series_studio.py",
    "seo_packager.py",
    "comfyui_image_provider.py",
    "gpu_capabilities.py",
    "tuansuapi_provider.py",
    "v2_tuanstor_image.py",
    "resilient_gemini.py",
    "studio_color_render.py",
    "studio_hand_color.py",
    "studio_hand_color_strokes.py",
    "studio_modes.py",
    "studio_voices.py",
    "studio_input_modes.py",
    "studio_image_budget.py",
    "studio_flow_accounts.py",
    "production_gallery.py",
    "competitor_cloner.py",
    "config.py",
    "mcp_v2_batch.py",
    "mcp_v2_images.py",
    "studio_library.py",
    "requirements.txt",
    "flowkit_client.py",
    "flow_account_manager.py",
    "clean_watermark.py",
    "youtube_manager.py",
    "transcript_cloner.py",
    "reference_scene_assembler.py",
    "reference_video_timeline.py",
    "reference_local_timeline.py",
    "yunet.onnx",
]

CORE_STUDIO_DIRS = [
    "web",
    "engine",
    "studio_mcp",
    "cinematic_engine",
]

def clean_and_prepare():
    if TARGET_DIR.exists():
        print(f"[*] Dọn dẹp thư mục release cũ: {TARGET_DIR}...")
        shutil.rmtree(TARGET_DIR, ignore_errors=True)
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[+] Đã tạo thư mục đóng gói: {TARGET_DIR}")

def copy_application_files():
    studio_target = TARGET_DIR / "studio"
    studio_target.mkdir(parents=True, exist_ok=True)

    # 1. Copy core files
    for fname in CORE_STUDIO_FILES:
        src = STUDIO_DIR / fname
        if src.is_file():
            shutil.copy2(src, studio_target / fname)
            print(f"  + Sao chép: {fname}")

    # 2. Copy core directories (web UI, engine, studio_mcp)
    for dname in CORE_STUDIO_DIRS:
        src = STUDIO_DIR / dname
        if src.is_dir():
            shutil.copytree(src, studio_target / dname, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".git*", "test_scripts", "*.log"))
            print(f"  + Sao chép thư mục: {dname}")

    # Include only interpreter bytes, never private accounts, profiles, logs,
    # production receipts or other developer runtime data.
    runtime_python = STUDIO_DIR / "runtime" / "python"
    if runtime_python.is_dir():
        shutil.copytree(runtime_python, studio_target / "runtime" / "python",
                        dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.log", "*.jsonl", ".env"))
        print("  + Clean portable Python runtime (no developer profiles)")

    # 2.5 Copy FlowKit Engine (All-In-One Distribution)
    flowkit_src = Path("D:/FLOWKIT")
    if flowkit_src.is_dir():
        flowkit_dst = TARGET_DIR / "FLOWKIT"
        shutil.copytree(flowkit_src, flowkit_dst, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".git*", "outputs", "*.log", "checkpoint_*", "*.part"))
        (flowkit_dst / "outputs").mkdir(exist_ok=True)
        print(f"  + Sao chép FlowKit Engine trọn gói: {flowkit_dst}")

    # 3. Create empty clean productions and scratch folders
    (studio_target / "productions").mkdir(exist_ok=True)
    (studio_target / "scratch").mkdir(exist_ok=True)
    (studio_target / "inbox").mkdir(exist_ok=True)

    # 4. Compile and copy native Windows Executable (.exe)
    compile_native_exe()
    exe_src = ROOT_DIR / "Storyboard_AI_Studio.exe"
    if exe_src.is_file():
        shutil.copy2(exe_src, TARGET_DIR / "Storyboard_AI_Studio.exe")
        print(f"  + Sao chép ứng dụng thực thi: Storyboard_AI_Studio.exe")

    # 5. Copy root launch and setup scripts
    for launcher in ["LAUNCH_STUDIO.bat", "CAI_DAT_MOI_TRUONG.bat", "LAUNCH_STUDIO_SILENT.vbs"]:
        src = ROOT_DIR / launcher
        if src.is_file():
            shutil.copy2(src, TARGET_DIR / launcher)
            print(f"  + Sao chép script: {launcher}")

    # 6. Create default commercial .env.example
    env_example = studio_target / ".env.example"
    env_example.write_text(
        "# STORYBOARD AI STUDIO PRO - COMMERCIAL CONFIGURATION\n"
        "# Điền khóa API bên thứ ba (Cloud AI Pro) hoặc khóa Gemini của bạn:\n"
        "TUANSU_BASE_URL=https://tuansuapi.store/v1\n"
        "TUANSU_API_KEY=\n"
        "TUANSU_TEXT_MODEL=gemini-flash-3.8-fast\n"
        "TUANSU_IMAGE_MODEL=gemini-3.1-flash-image-preview\n"
        "TUANSU_ENABLED=1\n"
        "GEMINI_API_KEY=\n",
        encoding="utf-8"
    )

    # 7. Create clean user manual for customers
    readme_path = TARGET_DIR / "HUONG_DAN_SU_DUNG.txt"
    readme_path.write_text(
        "======================================================================\n"
        "   🎬 CHÀO MỪNG BẠN ĐẾN VỚI STORYBOARD AI STUDIO PRO v1.0\n"
        "   Phần mềm Tự Động Hóa Sản Xuất Phim Hoạt Ảnh AI Chuyên Nghiệp\n"
        "======================================================================\n\n"
        "I. YÊU CẦU HỆ THỐNG:\n"
        "   - Hệ điều hành: Windows 10 hoặc Windows 11 (64-bit).\n"
        "   - Đã cài đặt Python 3.11 hoặc 3.12 (Tải tại: https://www.python.org/downloads/)\n"
        "     * Lưu ý khi cài Python: Nhớ tích chọn 'Add python.exe to PATH'.\n"
        "   - Công cụ video FFmpeg (Khuyên dùng: mở CMD gõ 'winget install Gyan.FFmpeg').\n\n"
        "II. CÁCH KHỞI ĐỘNG VÀ SỬ DỤNG:\n"
        "   1. KHỞI ĐỘNG ỨNG DỤNG:\n"
        "      - Nhấp đúp chuột vào file: 'Storyboard_AI_Studio.exe'\n"
        "        (File có biểu tượng logo Studio chuyên nghiệp).\n"
        "      - Nếu là lần đầu tiên mở phần mềm, hệ thống sẽ tự động khởi tạo\n"
        "        môi trường ảo và tải các thư viện AI hoàn toàn tự động 100%.\n\n"
        "   2. CẤU HÌNH NGUỒN AI:\n"
        "      - Bấm nút 'Cài Đặt' trên thanh công cụ góc trên.\n"
        "      - Chọn nguồn tạo ảnh bạn muốn:\n"
        "        + Điện Toán Đám Mây (Cloud AI Pro): Nhập mã kích hoạt API.\n"
        "        + GPU Render Nội Bộ: Sử dụng card đồ họa máy tính (ComfyUI / SDXL).\n"
        "        + Họa Sĩ Studio AI: Sử dụng tài khoản Google Flow.\n\n"
        "   3. SẢN XUẤT PHIM:\n"
        "      - Nhập Tên Phim và Chọn Tập (Ví dụ: Series Bí Ẩn Rừng Sâu - Tập 1).\n"
        "      - Nhập nội dung kịch bản hoặc ý tưởng sơ lược.\n"
        "      - Chọn Thể Loại và Tỷ Lệ Khung Hình (16:9 ngang hoặc 9:16 dọc).\n"
        "      - Bấm 'Sản Xuất Tập ... Bằng AI'.\n"
        "      - Toàn bộ khâu phân cảnh, vẽ tranh hoạt ảnh, lồng tiếng và dựng phim\n"
        "        sẽ được tự động hóa hoàn toàn!\n"
        "      - Xem video xuất bản ngay trong phần mềm hoặc mở thư mục productions.\n\n"
        "======================================================================\n"
        "Chúc bạn gặt hái nhiều thành công và tạo ra các video triệu view xuất sắc!\n"
        "======================================================================\n",
        encoding="utf-8"
    )
    print("  + Tạo tài liệu hướng dẫn: HUONG_DAN_SU_DUNG.txt")

def compile_native_exe():
    csc_path = r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
    icon_path = ROOT_DIR / "studio" / "web" / "assets" / "storyboard_ai_icon.ico"
    cs_source = ROOT_DIR / "launcher_src" / "Storyboard_AI_Studio.cs"
    exe_output = ROOT_DIR / "Storyboard_AI_Studio.exe"
    if not os.path.exists(csc_path) or not cs_source.is_file():
        return
    import subprocess
    cmd = [
        csc_path,
        "/target:winexe",
        f"/win32icon:{icon_path}",
        f"/out:{exe_output}",
        "/r:System.Windows.Forms.dll",
        "/r:System.Drawing.dll",
        str(cs_source)
    ]
    print("[*] Đang biên dịch Storyboard_AI_Studio.exe với biểu tượng chính thức...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        print("  + Biên dịch thành công: Storyboard_AI_Studio.exe")
    else:
        print("  [!] Lỗi biên dịch csc:", res.stderr)

def create_zip_archive():
    zip_path = DIST_DIR / f"{RELEASE_NAME}.zip"
    seven_zip = r"C:\Program Files\7-Zip\7z.exe"
    print(f"\n[*] Đang nén thành file phân phối ZIP: {zip_path.name}...", flush=True)
    if zip_path.exists():
        zip_path.unlink()

    if os.path.exists(seven_zip):
        import subprocess
        cmd = [seven_zip, "a", "-tzip", "-mx5", str(zip_path), str(TARGET_DIR / "*")]
        subprocess.run(cmd, capture_output=True, text=True)
    else:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(TARGET_DIR):
                for file in files:
                    abs_file = Path(root) / file
                    rel_path = abs_file.relative_to(DIST_DIR)
                    zf.write(abs_file, rel_path)
    print(f"[+] Kích thước file ZIP: {zip_path.stat().st_size / (1024*1024):.2f} MB", flush=True)
    root_zip = ROOT_DIR / "dist.zip"
    try:
        shutil.copyfile(zip_path, root_zip)
        print(f"[+] Đã đồng bộ file root dist.zip ({root_zip.stat().st_size / (1024*1024):.2f} MB)", flush=True)
    except Exception as e:
        print(f"  [-] Không thể đồng bộ root dist.zip: {e}")
    return zip_path

def create_setup_installer():
    seven_zip = r"C:\Program Files\7-Zip\7z.exe"
    sfx_module = r"C:\Program Files\7-Zip\7z.sfx"
    installer_exe = DIST_DIR / "Setup_Storyboard_AI_Studio_Pro_v1.0.exe"

    if not os.path.exists(seven_zip) or not os.path.exists(sfx_module):
        print("  [-] Không tìm thấy 7-Zip để tạo bộ cài .exe tự động.")
        return None

    print(f"\n[*] Đang đóng gói Bộ Cài Đặt 1-Click .EXE: {installer_exe.name}...")
    import subprocess
    temp_7z = DIST_DIR / "temp_archive.7z"
    if temp_7z.exists():
        temp_7z.unlink()

    # 1. Archive release folder
    cmd_archive = [seven_zip, "a", "-mx7", str(temp_7z), str(TARGET_DIR / "*")]
    res = subprocess.run(cmd_archive, capture_output=True, text=True)
    if res.returncode != 0:
        print("  [!] Lỗi nén 7z:", res.stderr)
        return None

    # 2. Config block
    config_data = (
        ";!@Install@!UTF-8!\n"
        "Title=\"Storyboard AI Studio Pro v1.0 - Trình Cài Đặt\"\n"
        "BeginPrompt=\"Bạn có muốn giải nén và khởi động Storyboard AI Studio Pro v1.0 không?\"\n"
        "RunProgram=\"Storyboard_AI_Studio.exe\"\n"
        ";!@InstallEnd@!\n"
    ).encode("utf-8")

    # 3. Concatenate sfx + config + 7z
    with open(installer_exe, "wb") as out_f:
        with open(sfx_module, "rb") as sfx_f:
            out_f.write(sfx_f.read())
        out_f.write(config_data)
        with open(temp_7z, "rb") as arc_f:
            out_f.write(arc_f.read())

    if temp_7z.exists():
        temp_7z.unlink()

    print(f"[+] ĐÃ TẠO BỘ CÀI ĐẶT .EXE THÀNH CÔNG! Kích thước: {installer_exe.stat().st_size / (1024*1024):.2f} MB")
    return installer_exe

def compile_inno_setup():
    iscc_candidates = [
        r"C:\Users\thean\AppData\Local\Programs\Inno Setup 6\ISCC.exe",
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
    ]
    iscc_exe = next((p for p in iscc_candidates if os.path.exists(p)), None)
    if not iscc_exe:
        print("  [-] Không tìm thấy Inno Setup Compiler (ISCC.exe).")
        return None

    iss_file = ROOT_DIR / "installer.iss"
    if not iss_file.is_file():
        print("  [-] Không tìm thấy installer.iss.")
        return None

    print(f"\n[*] Đang biên dịch Trình Cài Đặt Tiêu Chuẩn Windows: StoryboardAI-Setup.exe...")
    import subprocess
    cmd = [iscc_exe, str(iss_file)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    setup_output = DIST_DIR / "StoryboardAI-Setup.exe"
    if res.returncode == 0 and setup_output.is_file():
        print(f"[+] ĐÃ TẠO THÀNH CÔNG BỘ CÀI ĐẶT WINDOWS (INNO SETUP): StoryboardAI-Setup.exe ({setup_output.stat().st_size / (1024*1024):.2f} MB)")
        return setup_output
    else:
        print("  [!] Lỗi biên dịch Inno Setup:", res.stderr or res.stdout)
        return None

if __name__ == "__main__":
    clean_and_prepare()
    copy_application_files()
    create_zip_archive()
    create_setup_installer()
    compile_inno_setup()

