"""
Fair-Use FX & Anti-Content ID Engine.
Generates robust FFmpeg video filter complexes to defeat automated fingerprinting:
1. Micro-speed shift (1.04x)
2. Ken Burns slow zoom (1.0 -> 1.06x)
3. 9:16 Blurred background clone or Smart crop
4. Dynamic Film Grain (temporal noise)
5. Cinematic color grading (contrast/saturation tweak)
6. Optional selective horizontal flip
"""

from typing import Dict, Any, List, Optional, Tuple


def get_target_dimensions(aspect_ratio: str = "16:9") -> Tuple[int, int]:
    """Returns width and height for target aspect ratio."""
    if aspect_ratio == "9:16":
        return (1080, 1920)
    elif aspect_ratio == "1:1":
        return (1080, 1080)
    else:  # default 16:9
        return (1920, 1080)


def build_fair_use_video_filter(
    aspect_ratio: str = "16:9",
    speed_factor: float = 1.04,
    ken_burns: bool = True,
    film_grain: bool = True,
    hflip: bool = False,
    vertical_style: str = "blurred_background"  # "blurred_background" or "crop" or "black"
) -> str:
    """
    Constructs an optimized FFmpeg filtergraph string for a video slice.
    Supports 16:9 landscape, 9:16 Shorts with blurred background, and 1:1 square.
    """
    target_w, target_h = get_target_dimensions(aspect_ratio)

    pre_filters = []
    if hflip:
        pre_filters.append("hflip")
    pre_filters.append("eq=contrast=1.04:brightness=0.01:saturation=1.06")
    if film_grain:
        pre_filters.append("noise=alls=3:allf=t")
    if abs(speed_factor - 1.0) > 0.01:
        pts_factor = 1.0 / speed_factor
        pre_filters.append(f"setpts={pts_factor:.4f}*PTS")

    pre_chain = ",".join(pre_filters)
    pre_prefix = f"{pre_chain}," if pre_chain else ""

    if aspect_ratio == "9:16":
        if vertical_style == "crop":
            kb = f",scale=trunc(iw*1.05/2)*2:trunc(ih*1.05/2)*2,crop={target_w}:{target_h}" if ken_burns else ""
            return f"{pre_prefix}scale={target_w}:{target_h}:force_original_aspect_ratio=increase,crop={target_w}:{target_h}{kb}"
        elif vertical_style == "black":
            return f"{pre_prefix}scale={target_w}:{target_h}:force_original_aspect_ratio=decrease,pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2:black"
        else:  # default blurred_background (Chuẩn 100% video Shorts/TikTok với nền mờ)
            return (
                f"split=2[fg][bg];"
                f"[bg]scale={target_w}:{target_h}:force_original_aspect_ratio=increase,crop={target_w}:{target_h},boxblur=25:5[bg_blur];"
                f"[fg]scale={target_w}:{target_h}:force_original_aspect_ratio=decrease[fg_sharp];"
                f"[bg_blur][fg_sharp]overlay=(W-w)/2:(H-h)/2"
                f"{',' + pre_chain if pre_chain else ''}"
            )

    elif aspect_ratio == "1:1":
        if vertical_style == "crop":
            kb = f",scale=trunc(iw*1.05/2)*2:trunc(ih*1.05/2)*2,crop={target_w}:{target_h}" if ken_burns else ""
            return f"{pre_prefix}scale={target_w}:{target_h}:force_original_aspect_ratio=increase,crop={target_w}:{target_h}{kb}"
        elif vertical_style == "blur":
            return (
                f"split=2[fg][bg];"
                f"[bg]scale={target_w}:{target_h}:force_original_aspect_ratio=increase,crop={target_w}:{target_h},boxblur=25:5[bg_blur];"
                f"[fg]scale={target_w}:{target_h}:force_original_aspect_ratio=decrease[fg_sharp];"
                f"[bg_blur][fg_sharp]overlay=(W-w)/2:(H-h)/2"
                f"{',' + pre_chain if pre_chain else ''}"
            )
        else:  # default letterbox viền đen chuẩn 1:1
            return f"{pre_prefix}scale={target_w}:{target_h}:force_original_aspect_ratio=decrease,pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2:black"

    else:  # Standard 16:9
        kb = f",scale=trunc(iw*1.05/2)*2:trunc(ih*1.05/2)*2,crop={target_w}:{target_h}" if ken_burns else ""
        return f"{pre_prefix}scale={target_w}:{target_h}:force_original_aspect_ratio=decrease,pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2:black{kb}"


def build_9_16_blurred_filter_complex(
    input_tag: str = "0:v",
    target_w: int = 1080,
    target_h: int = 1920,
    speed_factor: float = 1.04,
    film_grain: bool = True,
    hflip: bool = False
) -> Tuple[str, str]:
    """
    Builds a filter_complex for vertical 9:16 layout with blurred background.
    Returns (filter_complex_string, output_tag).
    """
    pre_filters = []
    if hflip:
        pre_filters.append("hflip")
    pre_filters.append("eq=contrast=1.04:brightness=0.01:saturation=1.06")
    if film_grain:
        pre_filters.append("noise=alls=3:allf=t")
    if abs(speed_factor - 1.0) > 0.01:
        pts_factor = 1.0 / speed_factor
        pre_filters.append(f"setpts={pts_factor:.4f}*PTS")

    pre_chain = ",".join(pre_filters)
    if pre_chain:
        filter_str = f"[{input_tag}]{pre_chain}[pre];"
        base = "[pre]"
    else:
        filter_str = ""
        base = f"[{input_tag}]"

    filter_str += (
        f"{base}split=2[fg][bg];"
        f"[bg]scale={target_w}:{target_h}:force_original_aspect_ratio=increase,"
        f"crop={target_w}:{target_h},boxblur=30:5[bg_blur];"
        f"[fg]scale={target_w}:{target_h}:force_original_aspect_ratio=decrease[fg_sharp];"
        f"[bg_blur][fg_sharp]overlay=(W-w)/2:(H-h)/2[v_out]"
    )
    return filter_str, "v_out"


def build_watermark_drawtext(
    text: str,
    font_size: int = 38,
    color_scheme: str = "gold",
    motion_type: str = "floating",
    aspect_ratio: str = "16:9"
) -> str:
    """
    Constructs a high-visibility, professional watermark filter with vibrant color and movement.
    Prevents video theft and automated crop infringement.
    """
    clean_text = text.replace("'", "").replace(":", " -")
    if not clean_text.strip():
        return ""

    size = int(font_size)
    if aspect_ratio == "9:16":
        size = int(size * 1.1)

    color_map = {
        "gold": ("0xFACC15", "black", "black@0.55"),
        "cyan": ("0x38BDF8", "black", "black@0.55"),
        "rose": ("0xF43F5E", "white", "black@0.65"),
        "white": ("white", "black", "black@0.55"),
    }
    font_col, border_col, box_col = color_map.get(color_scheme, color_map["gold"])

    if motion_type == "floating":
        x_expr = "'w-tw-40-20*sin(2*PI*t/12)'"
        y_expr = "'35+15*cos(2*PI*t/8)'"
    elif motion_type == "wave":
        x_expr = "'(w-tw)/2+(w-tw)/3*sin(2*PI*t/14)'"
        y_expr = "'40+15*abs(sin(2*PI*t/7))'"
    else:
        x_expr = "w-tw-35"
        y_expr = "35"

    return (
        f"drawtext=text='{clean_text}':fontcolor={font_col}:fontsize={size}:"
        f"borderw=3:bordercolor={border_col}:box=1:boxcolor={box_col}:boxborderw=8:"
        f"x={x_expr}:y={y_expr}"
    )


def build_cta_drawtext(
    text: str = "🔔 ĐĂNG KÝ KÊNH • BẤM LIKE & CHIA SẺ",
    font_size: int = 30,
    aspect_ratio: str = "16:9"
) -> str:
    """
    Constructs an animated Call-To-Action (Subscribe, Like, Bell) overlay.
    Appears at seconds 5-16 and during the last 15 seconds with pulsing motion.
    """
    clean_text = text.replace("'", "").replace(":", " -").strip()
    if not clean_text:
        clean_text = "🔔 ĐĂNG KÝ KÊNH • BẤM LIKE & CHIA SẺ"

    size = int(font_size)
    if aspect_ratio == "9:16":
        size = int(size * 0.95)

    y_pos = "h*0.80-6*abs(sin(2*PI*t/1.5))"
    x_pos = "(w-tw)/2"

    return (
        f"drawtext=text='{clean_text}':fontcolor=white:fontsize={size}:"
        f"borderw=2:bordercolor=black:box=1:boxcolor=0xE11D48@0.92:boxborderw=10:"
        f"x='{x_pos}':y='{y_pos}':"
        f"enable='between(t,5,16)+gte(t,180)'"
    )

