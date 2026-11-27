"""Safe Drop-In Bridge Between D:\\STORYBOARD_AI\\studio\\ and east_asia_story_lab.

Every function here strictly gates on East Asia genres or Japanese/Korean scripts.
Non-CJK languages (English, Spanish, Vietnamese, etc.) return None/False immediately
so existing Storyboard AI pipelines behave identically.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .cjk_text_utils import (
    chunk_cjk_text,
    chunk_cjk_word_timestamps,
    contains_cjk,
    detect_cjk_language,
    resolve_ass_font_name,
    resolve_cjk_font_path,
    split_cjk_hook_lines,
)
from .cjk_subtitle_ass import build_cjk_subtitles_json, generate_cjk_ass
from .cjk_thumbnail_renderer import render_cjk_3d_text_overlay
from .east_asia_profiles import (
    EAST_ASIA_GENRES,
    EAST_ASIA_LOCALE,
    build_east_asia_seo_seed,
    get_east_asia_shot_bank,
    map_east_asia_shots_to_scenes,
    normalize_east_asia_bcp47,
    tts_delivery_for_east_asia,
    voice_for_east_asia,
)
from .hand_draw_east_asia import build_clean_whiteboard_prompt

_JP_KR_LANG_HINTS = ("jap", "ja", "nhật", "nhat", "kor", "ko", "hàn", "han")


def is_east_asia_language(language: str = "") -> bool:
    l = str(language or "").strip().lower()
    return any(k in l for k in _JP_KR_LANG_HINTS) or detect_cjk_language(str(language or ""), language) in ("Japanese", "Korean")


def is_east_asia_genre(genre: str = "") -> bool:
    return str(genre or "").strip().lower() in EAST_ASIA_GENRES


def canonical_east_asia_language(value: Any) -> Optional[str]:
    raw = str(value or "").strip()
    l = raw.lower()
    if any(k in l for k in ("jap", "ja", "jpn", "tiếng nhật", "tieng nhat", "nhật", "nhat")):
        return "Japanese"
    if any(k in l for k in ("kor", "ko", "kor", "tiếng hàn", "tieng han", "hàn", "han")):
        return "Korean"
    cjk = detect_cjk_language(raw, raw)
    if cjk in ("Japanese", "Korean"):
        return cjk
    return None


def east_asia_locale(language: str = "") -> Optional[tuple]:
    lang = canonical_east_asia_language(language)
    if lang and lang in EAST_ASIA_LOCALE:
        return EAST_ASIA_LOCALE[lang]
    return None


def register_east_asia_modes(genres_dict: Dict[str, Any], art_dict: Dict[str, str]) -> int:
    """Safely registers JP/KR genre presets into studio_modes GENRES/ART dictionaries."""
    added = 0
    for gid, cfg in EAST_ASIA_GENRES.items():
        if gid not in genres_dict:
            genres_dict[gid] = (cfg["display_name"], cfg["recommended_style"])
            added += 1
        if gid not in art_dict:
            art_dict[gid] = cfg["art_direction"]
    return added


def resolve_voice(language: str = "", genre: str = "auto", region: str = "auto") -> Optional[str]:
    return voice_for_east_asia(language=language, genre=genre, region=region)


def resolve_tts_delivery(genre: str) -> Optional[str]:
    return tts_delivery_for_east_asia(genre)


def resolve_image_instruction(genre: str = "", style: str = "", visual_concept: str = "", is_vertical: bool = False) -> Optional[str]:
    g = str(genre or "").strip().lower()
    st = str(style or "").strip().lower()
    if g not in EAST_ASIA_GENRES:
        return None
    if st in ("colored_marker", "whiteboard") or g == "jp_zen_story":
        if visual_concept:
            return build_clean_whiteboard_prompt(visual_concept, genre_id=g, is_vertical=is_vertical)
        return EAST_ASIA_GENRES["jp_zen_story"]["art_direction"]
    return EAST_ASIA_GENRES[g]["art_direction"]


def subtitle_json_if_cjk(
    scene: Dict[str, Any],
    duration: float,
    path: Path | str,
    is_vertical: bool = False,
    language: str = "auto",
) -> bool:
    """Segments narration and writes subtitles.json if narration/language is Japanese or Korean."""
    narration = str(scene.get("narration") or "").strip()
    if not narration:
        return False

    cjk_lang = detect_cjk_language(narration, language)
    if cjk_lang not in ("Japanese", "Korean") and not contains_cjk(narration):
        return False
    if cjk_lang == "Chinese":
        return False

    payload = build_cjk_subtitles_json(
        narration=narration,
        duration=duration,
        output_json=path,
        is_vertical=is_vertical,
        language=cjk_lang or language,
    )
    return bool(payload.get("subtitles"))


def generate_ass_if_cjk(
    subtitles_json_path: str,
    ass_output_path: str,
    subtitle_style: str = "karaoke_viral",
    video_width: int = 1280,
    video_height: int = 720,
    custom_font_size: int = 0,
    language: str = "auto",
) -> Optional[str]:
    """Generates JP/KR ASS subtitles when CJK script or language is present; else returns None."""
    p_sub = Path(subtitles_json_path)
    if not p_sub.is_file():
        return None

    try:
        data = json.loads(p_sub.read_text(encoding="utf-8"))
    except Exception:
        return None

    subtitles = data.get("subtitles", [])
    sample = " ".join(str(s.get("text") or "") for s in subtitles[:6] if isinstance(s, dict))
    lang_hint = str(data.get("language") or language or "auto")
    cjk_lang = detect_cjk_language(sample, lang_hint)
    if cjk_lang not in ("Japanese", "Korean"):
        return None

    return generate_cjk_ass(
        subtitles_json_path=p_sub,
        ass_output_path=ass_output_path,
        subtitle_style=subtitle_style,
        video_width=video_width,
        video_height=video_height,
        custom_font_size=custom_font_size,
        language=cjk_lang,
    )


def chunk_words_if_cjk(
    words: list,
    language: Optional[str] = None,
    is_vertical: bool = False,
    max_duration_seconds: float = 3.5,
) -> Optional[list]:
    return chunk_cjk_word_timestamps(
        words=words,
        language=language,
        is_vertical=is_vertical,
        max_duration_seconds=max_duration_seconds,
    )


def resolve_thumb_font_if_cjk(text_or_lines: Any, language: Optional[str] = None, fallback: str = "") -> Optional[str]:
    joined = " ".join(str(x) for x in text_or_lines) if isinstance(text_or_lines, (list, tuple)) else str(text_or_lines or "")
    cjk_lang = detect_cjk_language(joined, language)
    if cjk_lang in ("Japanese", "Korean") or contains_cjk(joined):
        return resolve_cjk_font_path(joined, language=cjk_lang or language, fallback=fallback)
    return None


def split_hook_if_cjk(text: str, language: Optional[str] = None, max_lines: int = 3) -> Optional[List[str]]:
    clean = str(text or "").strip()
    if not clean:
        return None
    if detect_cjk_language(clean, language) in ("Japanese", "Korean") or contains_cjk(clean):
        return split_cjk_hook_lines(clean, max_lines=max_lines)
    return None


def render_3d_overlay_if_cjk(
    canvas_size: Tuple[int, int],
    lines: List[str],
    text_box: Tuple[int, int, int, int],
    language: Optional[str] = None,
):
    """Returns RGBA 3D CJK text overlay Image if any line contains JP/KR text, else None."""
    joined = " ".join(str(x or "") for x in (lines or []))
    cjk_lang = detect_cjk_language(joined, language)
    if cjk_lang not in ("Japanese", "Korean") and not contains_cjk(joined):
        return None
    return render_cjk_3d_text_overlay(
        canvas_size=canvas_size,
        lines=lines,
        text_box=text_box,
        language=cjk_lang,
    )


def resolve_shot_bank_for_genre(genre: str) -> Optional[Tuple[str, List[Dict[str, Any]]]]:
    return get_east_asia_shot_bank(genre)


def apply_east_asia_shot_bank_montage(
    scenes: List[Dict[str, Any]],
    genre: str,
    shot_map: Dict[str, Path],
    scenes_dir: Path,
) -> bool:
    if not get_east_asia_shot_bank(genre):
        return False
    map_east_asia_shots_to_scenes(scenes=scenes, genre=genre, shot_map=shot_map, scenes_dir=scenes_dir)
    return True


def east_asia_skill_addendum(genre: str, language: str = "", is_short: bool = False) -> str:
    """Returns compact cultural & visual discipline addendum for East Asia script generation."""
    g = str(genre or "").strip().lower()
    if g not in EAST_ASIA_GENRES and not is_east_asia_language(language):
        return ""

    if g == "jp_zen_story":
        return (
            "\nEAST ASIA GENRE ADDENDUM (jp_zen_story - Hand-Drawn / Zen):\n"
            "- Write spoken narration in natural conversational Japanese (110-125 wpm calm tone).\n"
            "- For every scene's visual description (40-80 English words), specify pure solid white sketchbook background (#FFFFFF), "
            "bold black sumi ink contours and 1-2 vibrant chisel-tip marker colors (crimson/amber/indigo), zero dark shadows, clean outlines for hand-drawn animation.\n"
        )
    if g == "jp_edo_sleepless":
        return (
            "\nEAST ASIA GENRE ADDENDUM (jp_edo_sleepless - Sleep History):\n"
            "- Write calm, poetic, nocturnal Japanese historical narration ideal for nighttime listening.\n"
            "- Keep scene visual prompts atmospheric Edo-period twilight, paper lanterns, tatami rooms, ukiyo-e woodblock mood (English visual prompts).\n"
        )
    if g == "kr_yadam_joseon":
        return (
            "\nEAST ASIA GENRE ADDENDUM (kr_yadam_joseon - Korean Yadam):\n"
            "- Write vivid, dignified Korean traditional folktale narration with clear moral resonance.\n"
            "- Keep scene visual prompts authentic Joseon Dynasty architecture, hanok courtyards, hanbok attire, silk lanterns in moonlight (English visual prompts).\n"
        )
    if g == "kr_sayeon_drama":
        return (
            "\nEAST ASIA GENRE ADDENDUM (kr_sayeon_drama - Real-Life Drama):\n"
            "- Write emotionally gripping Korean contemporary first/third-person confession drama beats with strong opening hook"
            + (" (<58s 9:16 pacing)." if is_short else ".")
            + "\n- Keep scene visual prompts realistic Seoul/modern East Asian interiors and expressive acting (English visual prompts).\n"
        )
    return (
        f"\nEAST ASIA LANGUAGE RULE: Ensure narration is pure natural {canonical_east_asia_language(language) or language} "
        "without mixing Vietnamese or English words in narration text; write visual image prompts in English.\n"
    )
