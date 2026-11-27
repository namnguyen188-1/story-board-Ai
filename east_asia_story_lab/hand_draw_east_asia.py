"""East Asia Hand-Drawn Whiteboard (colored_marker / whiteboard) Adapter for JP/KR Lab."""
from __future__ import annotations

from pathlib import Path
import sys
from typing import Dict, Any

STUDIO_DIR = Path(__file__).resolve().parent.parent / "studio"


def build_clean_whiteboard_prompt(
    visual_concept: str,
    genre_id: str = "jp_zen_story",
    is_vertical: bool = False,
) -> str:
    """Produces a clean pure-white background prompt so OpenCV Canny extracts smooth marker contours."""
    ratio = "vertical 9:16" if is_vertical else "widescreen 16:9"
    clean_idea = " ".join(str(visual_concept or "").split())[:350]
    cultural_cue = (
        "minimalist Japanese Zen symbolism, serene ink wash and colorful marker illustration"
        if genre_id.startswith("jp_")
        else "minimalist Korean folk symbolism, expressive ink outline and clean marker sketch"
    )
    return (
        f"Vibrant hand-drawn colored marker illustration on pure clean #FFFFFF solid white sketchbook paper, {ratio}. "
        f"After Skool whiteboard storytelling style, bold clean sumi black ink outlines, "
        f"selective crimson red, amber gold, and deep indigo chisel-tip marker coloring accents, "
        f"{cultural_cue}, clear spacious white margins, high contrast contours, zero cluttered dark shading, "
        f"no text, no watermark: {clean_idea}"
    )


def render_hand_drawn_cjk_sample(
    image_path: Path | str,
    audio_path: Path | str,
    output_video_path: Path | str,
    width: int = 1280,
    height: int = 720,
    style: str = "colored_marker",
) -> Dict[str, Any]:
    """Calls studio's read-only colored_marker / hand_color renderer safely on an isolated sample."""
    if str(STUDIO_DIR) not in sys.path:
        sys.path.insert(0, str(STUDIO_DIR))

    if style == "hand_color":
        from studio_hand_color import hand_color_video
        out = hand_color_video(image_path, audio_path, output_video_path, width, height)
    else:
        from studio_colored_marker import colored_marker_video
        out = colored_marker_video(image_path, audio_path, output_video_path, width, height)

    return {"ok": True, "output_video": str(out), "style": style}
