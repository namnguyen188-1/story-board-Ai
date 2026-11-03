"""Storyboard AI Studio Pro - Gemini / Google Flow Watermark Cleaner.
High-speed inpainting using OpenCV Navier-Stokes (NS) with exact multi-model
support (Imagen 3 images, Veo / Omni 1.1 Flash videos, landscape 16:9 & vertical 9:16).
Completely eliminates the 4-pointed diamond star logo from images and video clips.
"""
from __future__ import annotations

import os
from pathlib import Path
import numpy as np

try:
    import cv2
except ImportError:
    cv2 = None


def create_gemini_star_mask(height: int, width: int) -> np.ndarray:
    """Generates a high-precision mask matching the 4-pointed Gemini / Google Flow star.
    Supports both Google Flow Video (Omni Flash / Veo) and Imagen 3 coordinates across all ratios.
    """
    mask = np.zeros((height, width), dtype=np.uint8)
    is_vertical = height > width

    if is_vertical:
        # 9:16 vertical ratio (e.g. 720x1280 or 1080x1920 or 864x1536)
        cx1 = int(round(width * 0.885))
        cy1 = int(round(height * 0.935))
        cx2 = int(round(width * 0.874))
        cy2 = int(round(height * 0.930))
        r = max(24, int(round(width * 0.055)))
        if cv2 is not None:
            cv2.circle(mask, (cx1, cy1), r, 255, -1)
            cv2.circle(mask, (cx2, cy2), r, 255, -1)
    else:
        # 16:9 landscape ratio (e.g. 1280x720 or 1536x864)
        # 1. Google Flow Video coordinate (Omni 1.1 Flash / Veo): ~90.6% W, ~83.3% H
        cx_vid = int(round(width * (1160.0 / 1280.0)))
        cy_vid = int(round(height * (600.0 / 720.0)))
        r_vid = max(24, int(round(width * 0.026)))

        # 2. Imagen 3 Image coordinate: ~93.0% W, ~86.8% H
        cx_img = int(round(width * (1428.0 / 1536.0)))
        cy_img = int(round(height * (750.0 / 864.0)))
        r_img = max(24, int(round(width * 0.026)))

        if cv2 is not None:
            cv2.circle(mask, (cx_vid, cy_vid), r_vid, 255, -1)
            cv2.circle(mask, (cx_img, cy_img), r_img, 255, -1)

    # 7x7 elliptical dilation with 2 iterations to seamlessly capture anti-aliased outer translucent glow
    if cv2 is not None:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        mask = cv2.dilate(mask, kernel, iterations=2)
    return mask


def remove_gemini_watermark(image_input: str | Path | np.ndarray,
                            output_path: str | Path | None = None,
                            inpaint_radius: int = 5) -> str | np.ndarray | None:
    """Removes the bottom-right Gemini/Google Flow diamond logo cleanly from an image with zero visible trace.

    - If image_input is a path, saves to output_path (or overwrites if output_path is None)
      and returns the string path.
    - If image_input is a numpy array (BGR), returns the cleaned numpy array.
    """
    if cv2 is None:
        return image_input

    is_array = isinstance(image_input, np.ndarray)
    if is_array:
        img = image_input
    else:
        in_path = Path(image_input)
        if not in_path.is_file():
            return None
        img = cv2.imread(str(in_path))
        if img is None:
            return str(in_path)

    h, w = img.shape[:2]
    mask = create_gemini_star_mask(h, w)

    # Inpaint using Navier-Stokes (cv2.INPAINT_NS) for smooth mathematical gradient preservation
    cleaned = cv2.inpaint(img, mask, inpaintRadius=inpaint_radius, flags=cv2.INPAINT_NS)

    if is_array:
        return cleaned

    target = Path(output_path) if output_path else Path(image_input)
    target.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(target), cleaned)
    return str(target)


def get_flow_watermark_delogo_box(width: int, height: int) -> tuple[int, int, int, int]:
    """Calculate the bounding box for FFmpeg delogo filter covering both Video and Image star positions."""
    is_vertical = height > width
    if is_vertical:
        cx = int(round(width * 0.885))
        cy = int(round(height * 0.935))
        rx = max(18, int(round(width * 0.05)))
        ry = max(18, int(round(height * 0.03)))
    else:
        # Bounding box enclosing both (cx_vid, cy_vid) and (cx_img, cy_img)
        cx_min = int(round(width * (1160.0 / 1280.0))) - 24
        cx_max = int(round(width * (1428.0 / 1536.0))) + 28
        cy_min = int(round(height * (600.0 / 720.0))) - 24
        cy_max = int(round(height * (750.0 / 864.0))) + 28
        x = max(0, cx_min - 8)
        y = max(0, cy_min - 8)
        w = min(width - x, (cx_max - cx_min) + 16)
        h = min(height - y, (cy_max - cy_min) + 16)
        return x, y, w, h

    x = max(0, cx - rx - 10)
    y = max(0, cy - ry - 10)
    w = min(width - x, (rx + 10) * 2)
    h = min(height - y, (ry + 10) * 2)
    return x, y, w, h


def _hardware_encoder_usable() -> bool:
    try:
        from studio_color_render import _hardware_encoder_usable as _chk
        return _chk()
    except Exception:
        return False


def remove_video_watermark(
    video_path: str | Path,
    output_path: str | Path | None = None,
    width: int | None = None,
    height: int | None = None,
) -> Path:
    """Removes the Google Flow / Gemini star watermark from a video clip using high-speed FFmpeg delogo.
    Overwrites the original video if output_path is None or equal to video_path.
    """
    v_in = Path(video_path)
    if not v_in.is_file():
        return v_in

    import subprocess, json
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

    if not width or not height:
        try:
            probe = subprocess.run(
                ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", str(v_in)],
                capture_output=True, text=True, check=True, creationflags=flags
            )
            data = json.loads(probe.stdout)
            for s in data.get("streams", []):
                if s.get("codec_type") == "video":
                    width = int(s.get("width", 1280))
                    height = int(s.get("height", 720))
                    break
        except Exception:
            width = width or 1280
            height = height or 720

    x, y, w, h = get_flow_watermark_delogo_box(width, height)
    target = Path(output_path) if output_path and Path(output_path) != v_in else v_in.with_name(f"delogo_temp_{v_in.name}")

    use_gpu = _hardware_encoder_usable()
    v_codec = ["-c:v", "h264_nvenc", "-preset", "p4", "-cq", "18"] if use_gpu else ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18"]
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(v_in),
        "-vf", f"delogo=x={x}:y={y}:w={w}:h={h}:show=0",
        *v_codec,
        "-c:a", "copy",
        str(target)
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, creationflags=flags)
        if res.returncode != 0 and use_gpu:
            cmd_fallback = [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-i", str(v_in),
                "-vf", f"delogo=x={x}:y={y}:w={w}:h={h}:show=0",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                "-c:a", "copy",
                str(target)
            ]
            subprocess.run(cmd_fallback, check=True, creationflags=flags)
        elif res.returncode != 0:
            res.check_returncode()
        if target != v_in and (output_path is None or Path(output_path) == v_in):
            v_in.unlink(missing_ok=True)
            target.rename(v_in)
            return v_in
        return target
    except Exception:
        if target.exists() and target != v_in:
            target.unlink(missing_ok=True)
        return v_in
