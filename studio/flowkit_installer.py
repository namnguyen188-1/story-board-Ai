"""FlowKit Engine Automated Installer & Verifier for Secondary Machines.

Ensures full self-contained Google Flow WebTool & Muse engine capability on any machine.
Supports automated download, extraction, path resolution, configuration, and launch.
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import sys
import time
import urllib.request
import zipfile
from pathlib import Path
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger("flowkit_installer")

GITHUB_RELEASE_DOWNLOAD_URL = (
    "https://github.com/anma8802-create/AI-tool/releases/download/v1.3.18/FlowKit_Engine_Standalone.zip"
)
GITHUB_FALLBACK_DOWNLOAD_URL = (
    "https://github.com/namnguyen188-1/story-board-Ai/releases/download/v1.3.18/FlowKit_Engine_Standalone.zip"
)

_INSTALL_STATUS = {
    "active": False,
    "percent": 0,
    "message": "Sẵn sàng",
    "success": False,
    "error": ""
}


def get_install_status() -> Dict[str, Any]:
    return dict(_INSTALL_STATUS)


def set_install_status(percent: int, message: str, active: bool = True, success: bool = False, error: str = ""):
    _INSTALL_STATUS["percent"] = percent
    _INSTALL_STATUS["message"] = message
    _INSTALL_STATUS["active"] = active
    _INSTALL_STATUS["success"] = success
    _INSTALL_STATUS["error"] = error


def find_existing_flowkit() -> Optional[Path]:
    """Locate an existing valid FlowKit engine installation."""
    from studio.flowkit_client import _resolve_flowkit_root
    try:
        cand = _resolve_flowkit_root()
        if cand and cand.is_dir() and (cand / "app" / "gateway.py").is_file():
            return cand
    except Exception:
        pass

    candidates = [
        Path(os.environ.get("FLOWKIT_ROOT", "").strip()) if os.environ.get("FLOWKIT_ROOT") else None,
        Path("D:/FLOWKIT"),
        Path(__file__).resolve().parent.parent / "FLOWKIT",
        Path("C:/FLOWKIT"),
    ]
    for c in candidates:
        if c and c.is_dir() and (c / "app" / "gateway.py").is_file():
            return c
    return None


def is_flowkit_installed() -> bool:
    return find_existing_flowkit() is not None


def determine_best_target_dir() -> Path:
    """Select the most optimal directory to install FlowKit."""
    # 1. If D:\ exists and is writable, D:\FLOWKIT is the primary standard
    if os.path.exists("D:\\"):
        try:
            test_file = Path("D:/_test_write.tmp")
            test_file.write_text("ok")
            test_file.unlink(missing_ok=True)
            return Path("D:/FLOWKIT")
        except Exception:
            pass

    # 2. Project root FLOWKIT
    proj_root = Path(__file__).resolve().parent.parent / "FLOWKIT"
    try:
        proj_root.parent.mkdir(parents=True, exist_ok=True)
        return proj_root
    except Exception:
        pass

    # 3. Fallback to C:\FLOWKIT
    return Path("C:/FLOWKIT")


def find_local_zip() -> Optional[Path]:
    """Search for existing FlowKit_Engine_Standalone.zip on disk."""
    candidates = [
        Path("D:/STORYBOARD_AI/FlowKit_Engine_Standalone.zip"),
        Path(__file__).resolve().parent.parent / "FlowKit_Engine_Standalone.zip",
        Path(__file__).resolve().parent.parent / "dist" / "FlowKit_Engine_Standalone.zip",
        Path.home() / "Downloads" / "FlowKit_Engine_Standalone.zip",
        Path("C:/FlowKit_Engine_Standalone.zip"),
    ]
    for c in candidates:
        if c.is_file() and c.stat().st_size > 100_000_000:
            return c
    return None


def download_flowkit_engine(target_zip: Path, progress_cb: Optional[Callable[[int, str], None]] = None) -> bool:
    """Download FlowKit standalone archive with progress reporting."""
    target_zip.parent.mkdir(parents=True, exist_ok=True)
    urls = [GITHUB_RELEASE_DOWNLOAD_URL, GITHUB_FALLBACK_DOWNLOAD_URL]

    for url in urls:
        try:
            logger.info(f"Downloading FlowKit engine from {url}...")
            if progress_cb:
                progress_cb(5, "Đang kết nối tới máy chủ cập nhật để tải Động cơ FlowKit...")

            req = urllib.request.Request(url, headers={"User-Agent": "StoryboardAI-Updater"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                total_bytes = int(resp.headers.get("Content-Length", 563_879_227))
                downloaded = 0
                chunk_size = 1024 * 512  # 512 KB

                with open(target_zip, "wb") as f_out:
                    while True:
                        chunk = resp.read(chunk_size)
                        if not chunk:
                            break
                        f_out.write(chunk)
                        downloaded += len(chunk)
                        pct = int((downloaded / total_bytes) * 60) + 5
                        pct = min(pct, 65)
                        mb_done = downloaded / (1024 * 1024)
                        mb_total = total_bytes / (1024 * 1024)
                        if progress_cb and downloaded % (1024 * 1024 * 5) < chunk_size:
                            progress_cb(pct, f"Đang tải động cơ FlowKit ({mb_done:.1f} MB / {mb_total:.1f} MB)...")

            if target_zip.is_file() and target_zip.stat().st_size > 100_000_000:
                logger.info("FlowKit download completed successfully.")
                return True
        except Exception as exc:
            logger.warning(f"Download failed from {url}: {exc}")
            if target_zip.is_file():
                try:
                    target_zip.unlink(missing_ok=True)
                except Exception:
                    pass

    return False


def install_flowkit_engine(progress_cb: Optional[Callable[[int, str], None]] = None) -> Dict[str, Any]:
    """Execute complete installation & validation of FlowKit Engine."""
    set_install_status(0, "Bắt đầu kiểm tra và cài đặt động cơ FlowKit...")

    def _notify(pct: int, msg: str):
        set_install_status(pct, msg)
        if progress_cb:
            progress_cb(pct, msg)

    # 1. Check if already installed
    existing = find_existing_flowkit()
    if existing:
        _notify(90, "Động cơ FlowKit đã có sẵn. Đang khởi động dịch vụ...")
        from studio.flowkit_client import ensure_flowkit_running, is_flowkit_alive
        ensure_flowkit_running(max_wait_seconds=10)
        alive = is_flowkit_alive()
        set_install_status(100, f"Động cơ FlowKit đã sẵn sàng tại {existing}", active=False, success=True)
        return {"ok": True, "path": str(existing), "alive": alive, "message": "Đã có sẵn và đang chạy."}

    # 2. Determine target directory
    target_dir = determine_best_target_dir()
    _notify(5, f"Thư mục cài đặt tối ưu: {target_dir}")

    # 3. Locate or download ZIP
    zip_path = find_local_zip()
    if not zip_path:
        _notify(10, "Không thấy gói cục bộ. Đang tải FlowKit_Engine_Standalone.zip từ GitHub...")
        temp_zip = Path(os.environ.get("TEMP", "C:/Windows/Temp")) / "FlowKit_Engine_Standalone.zip"
        ok = download_flowkit_engine(temp_zip, progress_cb=_notify)
        if not ok or not temp_zip.is_file():
            set_install_status(0, "Tải động cơ FlowKit thất bại. Vui lòng kiểm tra kết nối mạng.", active=False, error="DOWNLOAD_FAILED")
            return {"ok": False, "error": "Không thể tải động cơ FlowKit từ máy chủ phát hành."}
        zip_path = temp_zip

    # 4. Extract
    _notify(68, f"Đang giải nén động cơ FlowKit vào {target_dir} (khoảng 30 giây)...")
    seven_z = Path("C:/Program Files/7-Zip/7z.exe")
    extract_parent = target_dir.parent
    extract_parent.mkdir(parents=True, exist_ok=True)

    extracted_ok = False
    if seven_z.is_file():
        try:
            cmd = [str(seven_z), "x", "-y", f"-o{extract_parent}", str(zip_path)]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            if res.returncode == 0:
                extracted_ok = True
        except Exception as exc:
            logger.warning(f"7-Zip extraction failed: {exc}")

    if not extracted_ok:
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(extract_parent)
            extracted_ok = True
        except Exception as exc:
            set_install_status(0, f"Giải nén thất bại: {exc}", active=False, error=str(exc))
            return {"ok": False, "error": f"Lỗi giải nén: {exc}"}

    # Verify extracted structure
    actual_root = target_dir
    if not (actual_root / "app" / "gateway.py").is_file():
        cand_sub = target_dir / "FLOWKIT"
        if (cand_sub / "app" / "gateway.py").is_file():
            actual_root = cand_sub

    if not (actual_root / "app" / "gateway.py").is_file():
        set_install_status(0, "Cấu trúc thư mục giải nén không hợp lệ.", active=False, error="INVALID_STRUCTURE")
        return {"ok": False, "error": "Cấu trúc FlowKit không đầy đủ sau giải nén."}

    # 5. Configure machine.json
    _notify(88, "Đang khởi tạo cấu hình Google Flow WebTool...")
    state_dir = actual_root / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    machine_json = state_dir / "machine.json"
    m_data = {
        "debug_port": 9461,
        "flow_profile": str(actual_root / "state" / "flow_profile").replace("/", "\\"),
        "installed_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    machine_json.write_text(json.dumps(m_data, indent=2), encoding="utf-8")

    # Set environment variable permanently for session
    os.environ["FLOWKIT_ROOT"] = str(actual_root).replace("/", "\\")

    # 6. Launch FlowKit
    _notify(92, "Đang khởi động dịch vụ động cơ FlowKit cổng 18110...")
    from studio.flowkit_client import ensure_flowkit_running, is_flowkit_alive
    ensure_flowkit_running(max_wait_seconds=15)
    alive = is_flowkit_alive(timeout=4.0)

    _notify(100, f"Đã cài đặt thành công động cơ FlowKit tại {actual_root}!")
    set_install_status(100, f"Hoàn tất! Động cơ FlowKit sẵn sàng ({actual_root}).", active=False, success=True)

    return {
        "ok": True,
        "path": str(actual_root),
        "alive": alive,
        "message": f"Cài đặt hoàn tất thành công tại {actual_root}."
    }
