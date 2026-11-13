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
