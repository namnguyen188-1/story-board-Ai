"""
FFmpeg & FFprobe utilities for Recap Engine.
Provides path resolution, hardware acceleration detection, and safe execution.
"""

import os
import shutil
import subprocess
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

WIN_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0

# Known default locations on Windows
RECAP_DIR = Path(__file__).resolve().parent.parent
FALLBACK_FFMPEG_PATHS = [
    RECAP_DIR / "runtime" / "ffmpeg" / "bin" / "ffmpeg.exe",
    RECAP_DIR / "runtime" / "ffmpeg" / "ffmpeg.exe",
    RECAP_DIR.parent / "runtime" / "ffmpeg" / "bin" / "ffmpeg.exe",
    RECAP_DIR / "ffmpeg.exe",
    Path(r"C:\ffmpeg-8.0-full_build-shared\bin\ffmpeg.exe"),
    Path(r"C:\ffmpeg\bin\ffmpeg.exe"),
]

FALLBACK_FFPROBE_PATHS = [
    RECAP_DIR / "runtime" / "ffmpeg" / "bin" / "ffprobe.exe",
    RECAP_DIR / "runtime" / "ffmpeg" / "ffprobe.exe",
    RECAP_DIR.parent / "runtime" / "ffmpeg" / "bin" / "ffprobe.exe",
    RECAP_DIR / "ffprobe.exe",
    Path(r"C:\ffmpeg-8.0-full_build-shared\bin\ffprobe.exe"),
    Path(r"C:\ffmpeg\bin\ffprobe.exe"),
]


def get_ffmpeg_path() -> str:
    """Finds ffmpeg executable path."""
    which_path = shutil.which("ffmpeg")
    if which_path:
        return which_path
    for p in FALLBACK_FFMPEG_PATHS:
        if p.is_file():
            return str(p)
    return "ffmpeg"


def get_ffprobe_path() -> str:
    """Finds ffprobe executable path."""
    which_path = shutil.which("ffprobe")
    if which_path:
        return which_path
    for p in FALLBACK_FFPROBE_PATHS:
        if p.is_file():
            return str(p)
    return "ffprobe"


def check_nvenc_available() -> bool:
    """Check if NVIDIA NVENC hardware encoder is available."""
    ffmpeg = get_ffmpeg_path()
    try:
        proc = subprocess.run(
            [ffmpeg, "-encoders"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            creationflags=WIN_NO_WINDOW
        )
        return "h264_nvenc" in proc.stdout
    except Exception:
        return False


def run_ffprobe_json(args: List[str]) -> Dict[str, Any]:
    """Execute ffprobe and parse output as JSON."""
    ffprobe = get_ffprobe_path()
    cmd = [ffprobe, "-v", "quiet", "-print_format", "json"] + args
    res = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=WIN_NO_WINDOW
    )
    if res.returncode != 0:
        raise RuntimeError(f"FFprobe failed (code {res.returncode}): {res.stderr}")
    return json.loads(res.stdout)
