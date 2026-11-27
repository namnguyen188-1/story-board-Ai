"""Standalone CJK (Japanese & Korean) Subtitle Segmentation & ASS Burn-in Engine."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
from typing import Dict, List, Optional

from .cjk_text_utils import (
    chunk_cjk_text,
    detect_cjk_language,
    resolve_ass_font_name,
)


def build_cjk_subtitles_json(
    narration: str,
    duration: float,
    output_json: Optional[Path | str] = None,
    is_vertical: bool = False,
    language: str = "auto",
) -> Dict[str, object]:
    """Creates timed subtitle chunks safe for spaceless Japanese and Hangul Korean."""
    chunks = chunk_cjk_text(narration, is_vertical=is_vertical, language=language)
    if not chunks:
        return {"subtitles": [], "language": language}

    dur = max(1.0, float(duration))
    margin_start = min(0.25, dur * 0.05)
    margin_end = min(0.25, dur * 0.05)
    n_chunks = len(chunks)
    gap = min(0.10, (dur - margin_start - margin_end) / max(4, n_chunks * 4)) if n_chunks > 1 else 0.0
    usable = max(0.4, dur - margin_start - margin_end - gap * max(0, n_chunks - 1))
    total_chars = max(1, sum(len(c) for c in chunks))

    subs: List[Dict[str, object]] = []
    cursor = margin_start
    for idx, chunk in enumerate(chunks):
        span = usable * (len(chunk) / float(total_chars))
        start_t = round(cursor, 3)
        end_t = round((dur - margin_end) if idx == n_chunks - 1 else (cursor + span), 3)
        if end_t <= start_t:
            end_t = round(start_t + 0.08, 3)
        subs.append({"start": start_t, "end": end_t, "text": chunk})
        cursor = end_t + gap

    payload = {
        "language": detect_cjk_language(narration, language) or language,
        "cjk_segmented": True,
        "subtitles": subs,
    }
    if output_json:
        out_p = Path(output_json)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload


def _format_ass_ts(seconds: float) -> str:
    sec = max(0.0, float(seconds))
    hrs = int(sec // 3600)
    mins = int((sec % 3600) // 60)
    secs = int(sec % 60)
    centis = min(99, int(round((sec * 100) % 100)))
    return f"{hrs}:{mins:02d}:{secs:02d}.{centis:02d}"


def _tokenize_cjk_karaoke(text: str, lang: Optional[str]) -> List[str]:
    """Splits a Korean phrase by space words or a Japanese phrase into 2-char optical beats."""
    clean = str(text or "").strip()
    if not clean:
        return []
    if " " in clean and lang == "Korean":
        return [w for w in clean.split() if w]
    if lang == "Japanese":
        # Group Japanese into readable 2-character beats so highlight sweeps cleanly without spacing bugs
        return [clean[i : i + 2] for i in range(0, len(clean), 2)]
    return [w for w in clean.split() if w] or [clean]


def generate_cjk_ass(
    subtitles_json_path: Path | str,
    ass_output_path: Path | str,
    subtitle_style: str = "karaoke_viral",
    video_width: int = 1280,
    video_height: int = 720,
    custom_font_size: int = 0,
    language: str = "auto",
) -> str:
    """Generates an ASS subtitle file with native JP/KR font selection and no tofu artifacts."""
    p_json = Path(subtitles_json_path)
    data = json.loads(p_json.read_text(encoding="utf-8"))
    subtitles = data.get("subtitles", [])
    if not subtitles:
        return ""

    sample_text = " ".join(str(s.get("text") or "") for s in subtitles[:6])
    lang = detect_cjk_language(sample_text, language or data.get("language"))
    font_name = resolve_ass_font_name(sample_text, lang)

    is_vertical = video_height > video_width
    if custom_font_size and int(custom_font_size) > 0:
        font_size = int(custom_font_size)
    elif is_vertical:
        font_size = max(54, int(round(78 * (video_width / 1080.0))))
    else:
        font_size = max(36, int(round(52 * (video_height / 720.0))))

    margin_v = max(180, int(video_height * 0.16)) if is_vertical else max(28, int(round(font_size * 0.95)))
    margin_lr = max(24, int(round(video_width * 0.04)))
    outline = round(max(2.0, font_size * 0.08), 1)
    shadow = round(max(1.2, font_size * 0.035), 1)

    is_box = "box" in subtitle_style
    border_style = "3" if is_box else "1"
    primary_col = "&H0000FFFF" if "yellow" in subtitle_style else "&H00FFFFFF"
    secondary_col = "&H0000FFFF"
    outline_col = "&H00000000"
    back_col = "&H90000000" if is_box else "&H80000000"

    header = (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        f"PlayResX: {video_width}\n"
        f"PlayResY: {video_height}\n"
        "ScaledBorderAndShadow: yes\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
        "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: StudioSub,{font_name},{font_size},{primary_col},{secondary_col},{outline_col},{back_col},"
        f"1,0,0,0,100,100,0,0,{border_style},{outline},{shadow},2,{margin_lr},{margin_lr},{margin_v},1\n\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )

    dialogues: List[str] = []
    joiner = " " if lang == "Korean" else ""

    for sub in subtitles:
        text = str(sub.get("text") or "").strip()
        if not text:
            continue
        start_s = float(sub.get("start", 0.0))
        end_s = max(start_s + 0.3, float(sub.get("end", start_s + 1.0)))

        if subtitle_style == "karaoke_viral":
            tokens = _tokenize_cjk_karaoke(text, lang)
            tok_dur = max(0.04, (end_s - start_s) / max(1, len(tokens)))
            for idx in range(len(tokens)):
                t0 = start_s + idx * tok_dur
                t1 = end_s if idx == len(tokens) - 1 else min(end_s, t0 + tok_dur)
                if t1 <= t0:
                    continue
                parts = []
                for j, tok in enumerate(tokens):
                    if j == idx:
                        parts.append(r"{\c&H00FFFF&\b1\fscx108\fscy108}" + tok + r"{\c" + primary_col + r"\b1\fscx100\fscy100}")
                    else:
                        parts.append(r"{\c" + primary_col + r"\b1\fscx100\fscy100}" + tok)
                line = joiner.join(parts)
                dialogues.append(f"Dialogue: 0,{_format_ass_ts(t0)},{_format_ass_ts(t1)},StudioSub,,0,0,0,,{line}")
        else:
            dialogues.append(f"Dialogue: 0,{_format_ass_ts(start_s)},{_format_ass_ts(end_s)},StudioSub,,0,0,0,,{text}")

    out_ass = Path(ass_output_path)
    out_ass.parent.mkdir(parents=True, exist_ok=True)
    out_ass.write_text(header + "\n".join(dialogues) + "\n", encoding="utf-8")
    return str(out_ass)


def burn_cjk_subtitles_ffmpeg(
    video_path: Path | str,
    ass_path: Path | str,
    output_path: Path | str,
) -> str:
    """Burns generated CJK ASS subtitles into an MP4 file safely on Windows paths."""
    in_vid = Path(video_path).resolve()
    ass_f = Path(ass_path).resolve()
    out_vid = Path(output_path).resolve()
    out_vid.parent.mkdir(parents=True, exist_ok=True)

    # Escape Windows drive colon and backslashes for libass filter syntax
    esc_ass = str(ass_f).replace("\\", "/").replace(":", "\\:")
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(in_vid),
        "-vf", f"ass='{esc_ass}'",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "copy", "-movflags", "+faststart",
        str(out_vid),
    ]
    subprocess.run(cmd, check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return str(out_vid)
