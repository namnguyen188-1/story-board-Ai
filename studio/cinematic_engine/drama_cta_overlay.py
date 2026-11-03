"""Cinematic Drama Engine - Call-to-Action (CTA) Overlay Engine.
Generates ultra-crisp transparent CTA badges (Like, Subscribe, Bell / Thích, Đăng ký, Chuông)
and burns smooth animated overlays onto videos while preserving 100% native audio.
"""
from __future__ import annotations

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont

# Reconfigure stdout/stderr for clean utf-8 logging on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


_NVENC_AVAILABLE = None


def get_video_encoder_flags() -> list[str]:
    """Returns GPU NVENC encoding flags if available, otherwise fast CPU x264."""
    global _NVENC_AVAILABLE
    if _NVENC_AVAILABLE is None:
        try:
            r = subprocess.run(
                ["ffmpeg", "-hide_banner", "-f", "lavfi", "-i", "color=c=blue:s=1280x720:d=0.1", "-c:v", "h264_nvenc", "-f", "null", "-"],
                capture_output=True, timeout=5, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
            )
            _NVENC_AVAILABLE = (r.returncode == 0)
        except Exception:
            _NVENC_AVAILABLE = False

    if _NVENC_AVAILABLE:
        return ["-c:v", "h264_nvenc", "-preset", "p4", "-cq", "20"]
    return ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20"]


def get_video_duration(video_path: Path | str) -> float:
    """Probes exact duration in seconds of video file."""
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)
    ]
    try:
        res = subprocess.run(
            cmd, capture_output=True, text=True, check=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
        )
        return float(res.stdout.strip())
    except Exception:
        return 5.0


def draw_thumbs_up_vector(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    size: int = 28,
    color: Tuple[int, int, int, int] = (255, 255, 255, 255)
):
    """Draws a clean, stylized thumbs-up vector icon."""
    # Cuff / wrist
    draw.rounded_rectangle([(x, y + 10), (x + 6, y + size)], radius=2, fill=color)
    # Palm and extended thumb
    poly = [
        (x + 9, y + 12),
        (x + 15, y + 2),
        (x + 19, y + 2),
        (x + 19, y + 10),
        (x + size + 2, y + 10),
        (x + size, y + 15),
        (x + size + 1, y + 20),
        (x + size - 1, y + 25),
        (x + 9, y + size)
    ]
    draw.polygon(poly, fill=color)


def draw_bell_vector(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    size: int = 28,
    color: Tuple[int, int, int, int] = (255, 215, 0, 255)
):
    """Draws a golden notification bell vector icon with vibration waves."""
    cx = x + size // 2
    # Top hanger
    draw.ellipse([(cx - 3, y), (cx + 3, y + 5)], fill=color)
    # Bell dome
    poly = [
        (cx - 5, y + 5),
        (cx + 5, y + 5),
        (cx + 12, y + size - 6),
        (cx - 12, y + size - 6)
    ]
    draw.polygon(poly, fill=color)
    # Rim
    draw.rounded_rectangle([(cx - 14, y + size - 7), (cx + 14, y + size - 3)], radius=2, fill=color)
    # Clapper
    draw.ellipse([(cx - 3, y + size - 3), (cx + 3, y + size + 3)], fill=color)
    # Sound vibration waves
    draw.arc([(cx - 19, y + 7), (cx - 14, y + 20)], 120, 240, fill=color, width=2)
    draw.arc([(cx + 14, y + 7), (cx + 19, y + 20)], 300, 60, fill=color, width=2)


def create_cta_badge(
    output_path: Path | str,
    aspect_ratio: str = "16:9",
    scale: float = 1.0
) -> Path:
    """Generates an ultra-crisp transparent PNG CTA badge (LIKE • SUBSCRIBE • CHUÔNG)."""
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Base dimensions
    if aspect_ratio == "9:16":
        w, h = int(580 * scale), int(96 * scale)
    else:
        w, h = int(720 * scale), int(100 * scale)

    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background frosted glassmorphism pill with subtle border
    draw.rounded_rectangle(
        [(0, 0), (w - 1, h - 1)],
        radius=h // 2,
        fill=(15, 18, 24, 235),
        outline=(255, 255, 255, 45),
        width=2
    )

    # Font setup
    font_path = "C:/Windows/Fonts/segoeuib.ttf"
    if not os.path.exists(font_path):
        font_path = "C:/Windows/Fonts/arialbd.ttf"

    font_size = int(22 * scale) if aspect_ratio != "9:16" else int(19 * scale)
    try:
        font = ImageFont.truetype(font_path, font_size)
    except Exception:
        font = ImageFont.load_default()

    if aspect_ratio == "9:16":
        # Compact vertical layout: LIKE | ĐĂNG KÝ | CHUÔNG
        # 1. Like
        draw_thumbs_up_vector(draw, int(25 * scale), int(34 * scale), size=int(26 * scale))
        draw.text((int(60 * scale), int(36 * scale)), "LIKE", fill=(255, 255, 255, 255), font=font)

        # Divider 1
        draw.line([(int(130 * scale), int(22 * scale)), (int(130 * scale), int(74 * scale))], fill=(255, 255, 255, 40), width=1)

        # 2. Subscribe (YouTube Red)
        sub_x0 = int(145 * scale)
        sub_y0 = int(14 * scale)
        sub_x1 = int(410 * scale)
        sub_y1 = h - int(14 * scale)
        draw.rounded_rectangle([(sub_x0, sub_y0), (sub_x1, sub_y1)], radius=(sub_y1 - sub_y0) // 2, fill=(225, 20, 20, 255))
        draw.polygon([
            (sub_x0 + int(20 * scale), int(36 * scale)),
            (sub_x0 + int(20 * scale), int(58 * scale)),
            (sub_x0 + int(36 * scale), int(47 * scale))
        ], fill=(255, 255, 255, 255))
        draw.text((sub_x0 + int(46 * scale), int(34 * scale)), "ĐĂNG KÝ", fill=(255, 255, 255, 255), font=font)

        # Divider 2
        draw.line([(int(430 * scale), int(22 * scale)), (int(430 * scale), int(74 * scale))], fill=(255, 255, 255, 40), width=1)

        # 3. Bell
        draw_bell_vector(draw, int(450 * scale), int(33 * scale), size=int(26 * scale), color=(255, 215, 0, 255))
        draw.text((int(490 * scale), int(36 * scale)), "CHUÔNG", fill=(255, 215, 0, 255), font=font)
    else:
        # Standard horizontal 16:9 layout
        # 1. Like
        draw_thumbs_up_vector(draw, int(35 * scale), int(36 * scale), size=int(28 * scale))
        draw.text((int(75 * scale), int(37 * scale)), "LIKE", fill=(255, 255, 255, 255), font=font)

        # Divider 1
        draw.line([(int(155 * scale), int(25 * scale)), (int(155 * scale), int(75 * scale))], fill=(255, 255, 255, 40), width=1)

        # 2. Subscribe (YouTube Red)
        sub_x0 = int(180 * scale)
        sub_y0 = int(15 * scale)
        sub_x1 = int(490 * scale)
        sub_y1 = h - int(15 * scale)
        draw.rounded_rectangle([(sub_x0, sub_y0), (sub_x1, sub_y1)], radius=(sub_y1 - sub_y0) // 2, fill=(225, 20, 20, 255))
        # YouTube Play triangle icon
        draw.polygon([
            (sub_x0 + int(25 * scale), int(38 * scale)),
            (sub_x0 + int(25 * scale), int(62 * scale)),
            (sub_x0 + int(45 * scale), int(50 * scale))
        ], fill=(255, 255, 255, 255))
        draw.text((sub_x0 + int(55 * scale), int(35 * scale)), "ĐĂNG KÝ / SUBSCRIBE", fill=(255, 255, 255, 255), font=font)

        # Divider 2
        draw.line([(int(515 * scale), int(25 * scale)), (int(515 * scale), int(75 * scale))], fill=(255, 255, 255, 40), width=1)

        # 3. Bell
        draw_bell_vector(draw, int(540 * scale), int(34 * scale), size=int(28 * scale), color=(255, 215, 0, 255))
        draw.text((int(585 * scale), int(37 * scale)), "CHUÔNG", fill=(255, 215, 0, 255), font=font)

    img.save(str(out_path), "PNG")
    return out_path


def compute_drama_cta_times(total_dur: float, aspect_ratio: str = "16:9") -> list[float]:
    """Computes periodic CTA appearance timestamps based on video duration.
    - Short/Vertical (<= 90s or 9:16): Appears proportionally at 25-28% into video.
    - Mid-form (91s - 300s): Proportional ~20% into video, capped at 50s.
    - Long-form (> 300s): First CTA at ~45-50s, then every ~160s.
    - Finale: Last 8-10s of video (if video is long enough).
    All timestamps are strictly proportional — no hardcoded minimums that exceed video length.
    """
    is_vertical = aspect_ratio == "9:16" or "vertical" in aspect_ratio
    if total_dur < 8.0:
        return []

    # Case 1: Shorts 9:16 or very short clips (<= 90s)
    if is_vertical or total_dur <= 90.0:
        # Proportional: 25-28% in, but never beyond 85% of duration
        t_first = round(min(total_dur * 0.80, max(total_dur * 0.20, min(16.0, total_dur * 0.28))), 1)
        # Ensure CTA appears at least 4s before end
        t_first = min(t_first, round(total_dur - 4.0, 1))
        times = [t_first]
        if total_dur >= 38.0 and (total_dur - 6.5) > (t_first + 12.0):
            times.append(round(total_dur - 6.5, 1))
        return times

    # Case 2: Mid/Long-form Video (16:9, > 90s)
    # Proportional first CTA: 20% into video, capped at 50s — NO hardcoded 25s minimum
    first_cta = round(min(50.0, total_dur * 0.20), 1)
    # Safety: never appear in last 15s
    first_cta = min(first_cta, round(total_dur - 15.0, 1))
    times = [first_cta]

    # Periodic interval: every ~160s (2.6 minutes) for optimal engagement
    interval = 160.0 if total_dur <= 600.0 else 180.0
    curr = first_cta + interval
    while curr <= (total_dur - 25.0):
        times.append(round(curr, 1))
        curr += interval

    # Finale CTA in the last 8 - 10 seconds before end
    finale_t = round(total_dur - 8.5, 1)
    if finale_t > (times[-1] + 35.0):
        times.append(finale_t)

    return times


def apply_cta_overlay_to_video(
    input_video_path: Path | str,
    output_video_path: Path | str,
    aspect_ratio: str = "16:9",
    start_offset_from_end: float = 5.0,
    cta_duration: float = 4.5,
    custom_times: list[float] | None = None
) -> Path:
    """Burns smooth animated CTA badge (fade in & fade out) onto video at multiple engagement timestamps
    while preserving native audio bit-for-bit."""
    in_video = Path(input_video_path)
    out_video = Path(output_video_path)
    out_video.parent.mkdir(parents=True, exist_ok=True)

    if not in_video.exists():
        raise FileNotFoundError(f"Input video not found: {in_video}")

    total_dur = get_video_duration(in_video)
    if total_dur < 8.0:
        if in_video.resolve() != out_video.resolve():
            import shutil
            shutil.copy2(str(in_video), str(out_video))
        return out_video

    # Calculate optimal timestamps
    times = custom_times if custom_times is not None else compute_drama_cta_times(total_dur, aspect_ratio)
    if not times:
        if in_video.resolve() != out_video.resolve():
            import shutil
            shutil.copy2(str(in_video), str(out_video))
        return out_video

    # Generate badge PNG in same folder
    badge_png = out_video.parent / "cta_sub_like_bell_badge.png"
    create_cta_badge(badge_png, aspect_ratio=aspect_ratio)

    # CTA vị trí: góc phải-trên để KHÔNG chồng lên phụ đề (phụ đề ở đáy)
    # 9:16 vertical: cách top 24px, cách right 16px
    # 16:9 horizontal: cách top 20px, cách right 24px
    if aspect_ratio == "9:16" or "vertical" in aspect_ratio:
        overlay_x = "W-w-16"
        overlay_y = "24"
    else:
        overlay_x = "W-w-24"
        overlay_y = "20"

    temp_out = out_video.with_suffix(".cta_temp.mp4")

    # Build dynamic filtergraph for multiple CTA appearances
    split_chain = f"[1:v]format=rgba,split={len(times)}" + "".join(f"[b{i}]" for i in range(len(times)))
    chains = [split_chain]
    curr_v = "0:v"
    for i, t in enumerate(times):
        start_t = t
        end_t = min(total_dur, start_t + cta_duration)
        fade_in_d = min(0.4, (end_t - start_t) / 4)
        fade_out_d = min(0.4, (end_t - start_t) / 4)
        fade_out_st = max(start_t + fade_in_d, end_t - fade_out_d)
        chains.append(f"[b{i}]fade=t=in:st={start_t:.2f}:d={fade_in_d:.2f}:alpha=1,fade=t=out:st={fade_out_st:.2f}:d={fade_out_d:.2f}:alpha=1[cta{i}]")
        next_v = "v" if i == len(times) - 1 else f"v{i}"
        # Đặt CTA góc phải-trên, tránh đè phụ đề ở vùng đáy
        chains.append(f"[{curr_v}][cta{i}]overlay={overlay_x}:{overlay_y}:enable='between(t,{start_t:.2f},{end_t:.2f})'[{next_v}]")
        curr_v = next_v

    filter_str = ";".join(chains)
    enc_flags = get_video_encoder_flags()

    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(in_video.resolve()),
        "-i", str(badge_png.resolve()),
        "-filter_complex", filter_str,
        "-map", "[v]",
        "-map", "0:a?",
        *enc_flags,
        "-c:a", "copy",
        str(temp_out.resolve())
    ]

    time_labels = [f"{int(t//60)}m{int(t%60):02d}s" if t >= 60 else f"{t:.1f}s" for t in times]
    print(f"[CTA_OVERLAY] Đang chèn nút Like/Sub/Chuông ({', '.join(time_labels)} - tổng {len(times)} lần)...", flush=True)

    try:
        subprocess.run(cmd, check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if temp_out.exists() and temp_out.stat().st_size > 1000:
            import shutil
            shutil.move(str(temp_out), str(out_video))
            print(f"[CTA_OVERLAY] ✅ Đã gắn thành công nút SUB, LIKE & CHUÔNG ({', '.join(time_labels)}) vào {out_video.name}", flush=True)
            return out_video
    except Exception as e:
        print(f"[CTA_OVERLAY_WARN] Lỗi khi gắn overlay CTA: {e}. Giữ nguyên video gốc.", flush=True)
        if temp_out.exists():
            try:
                temp_out.unlink()
            except Exception:
                pass
        if in_video.resolve() != out_video.resolve():
            import shutil
            shutil.copy2(str(in_video), str(out_video))
    return out_video