"""Isolated East Asia (Japanese & Korean) Storytelling Lab for Storyboard AI.

All modules here run completely independently of D:\\STORYBOARD_AI\\studio\\ until
verified end-to-end and explicitly wired into production.
"""
from .cjk_text_utils import (
    detect_cjk_language,
    contains_cjk,
    resolve_cjk_font_path,
    resolve_ass_font_name,
    split_cjk_sentences,
    chunk_cjk_text,
    chunk_cjk_word_timestamps,
    split_cjk_hook_lines,
)
from .cjk_subtitle_ass import (
    build_cjk_subtitles_json,
    generate_cjk_ass,
    burn_cjk_subtitles_ffmpeg,
)
from .cjk_thumbnail_renderer import (
    render_cjk_3d_text_overlay,
    compose_cjk_thumbnail,
)
from .east_asia_profiles import (
    EAST_ASIA_LOCALE,
    EAST_ASIA_GENRES,
    EAST_ASIA_UI_PRESETS,
    JP_EDO_SHOT_BANK,
    KR_JOSEON_SHOT_BANK,
    normalize_east_asia_bcp47,
    build_east_asia_seo_seed,
    voice_for_east_asia,
    tts_delivery_for_east_asia,
    get_east_asia_shot_bank,
    map_east_asia_shots_to_scenes,
)
from .hand_draw_east_asia import (
    build_clean_whiteboard_prompt,
    render_hand_drawn_cjk_sample,
)
from . import studio_bridge

__all__ = [
    "detect_cjk_language",
    "contains_cjk",
    "resolve_cjk_font_path",
    "resolve_ass_font_name",
    "split_cjk_sentences",
    "chunk_cjk_text",
    "chunk_cjk_word_timestamps",
    "split_cjk_hook_lines",
    "build_cjk_subtitles_json",
    "generate_cjk_ass",
    "burn_cjk_subtitles_ffmpeg",
    "render_cjk_3d_text_overlay",
    "compose_cjk_thumbnail",
    "EAST_ASIA_LOCALE",
    "EAST_ASIA_GENRES",
    "EAST_ASIA_UI_PRESETS",
    "JP_EDO_SHOT_BANK",
    "KR_JOSEON_SHOT_BANK",
    "normalize_east_asia_bcp47",
    "build_east_asia_seo_seed",
    "voice_for_east_asia",
    "tts_delivery_for_east_asia",
    "get_east_asia_shot_bank",
    "map_east_asia_shots_to_scenes",
    "build_clean_whiteboard_prompt",
    "render_hand_drawn_cjk_sample",
    "studio_bridge",
]
