import os
import json
import subprocess
from pathlib import Path

# Subtitle styling presets for libass
# Note: In ASS/SSA format, colors are &HAABBGGRR (Alpha-Blue-Green-Red)
SUBTITLE_STYLES = {
    "yellow_black": {
        "name": "Vàng Viền Đen (Viral)",
        "PrimaryColour": "&H0000FFFF",  # Bright Yellow (BGR: 00, FF, FF)
        "OutlineColour": "&H00000000",  # Pure Black Outline
        "BackColour": "&H80000000",     # Subtle dark shadow
        "BorderStyle": "1",             # Outline + drop shadow
        "Outline": "3.2",
        "Shadow": "1.5",
        "Bold": "1",
    },
    "yellow_box": {
        "name": "Vàng Nền Hộp Đen",
        "PrimaryColour": "&H0000FFFF",  # Bright Yellow
        "OutlineColour": "&H00000000",
        "BackColour": "&H90000000",     # Translucent Black Box (~60% opacity)
        "BorderStyle": "3",             # Opaque Box Background
        "Outline": "2.0",
        "Shadow": "0",
        "Bold": "1",
    },
    "white_box": {
        "name": "Trắng Nền Hộp Đen",
        "PrimaryColour": "&H00FFFFFF",  # Pure White
        "OutlineColour": "&H00000000",
        "BackColour": "&H90000000",     # Translucent Black Box
        "BorderStyle": "3",             # Opaque Box Background
        "Outline": "2.0",
        "Shadow": "0",
        "Bold": "1",
    },
    "white_stroke": {
        "name": "Trắng Viền Đen Dày",
        "PrimaryColour": "&H00FFFFFF",  # Pure White
        "OutlineColour": "&H00000000",  # Thick Black Outline
        "BackColour": "&H80000000",
        "BorderStyle": "1",
        "Outline": "3.5",
        "Shadow": "1.5",
        "Bold": "1",
    },
    "cyan_black": {
        "name": "Xanh Neon Viền Đen",
        "PrimaryColour": "&H00FFFF00",  # Cyan (BGR: FF, FF, 00)
        "OutlineColour": "&H00000000",
        "BackColour": "&H80000000",
        "BorderStyle": "1",
        "Outline": "3.2",
        "Shadow": "1.5",
        "Bold": "1",
    },
    "green_black": {
        "name": "Xanh Lá Viền Đen",
        "PrimaryColour": "&H0000FF00",  # Neon Green (BGR: 00, FF, 00)
        "OutlineColour": "&H00000000",
        "BackColour": "&H80000000",
        "BorderStyle": "1",
        "Outline": "3.2",
        "Shadow": "1.5",
        "Bold": "1",
    },
    "karaoke_viral": {
        "name": "🔥 Karaoke Chạy Chữ (Trending TikTok/Shorts)",
        "PrimaryColour": "&H00FFFFFF",
        "OutlineColour": "&H00000000",
        "BackColour": "&H90000000",
        "BorderStyle": "1",
        "Outline": "3.4",
        "Shadow": "1.5",
        "Bold": "1",
    },
}


def generate_styled_ass(
    subtitles_json_path: str,
    ass_output_path: str,
    subtitle_style: str = "karaoke_viral",
    video_height: int = 720,
    video_width: int = 1280,
    custom_font_size: int = 0,
    enable_stickers: bool = True,
    language: str = "auto",
) -> str:
    """
    Generates an Advanced SubStation Alpha (.ass) file with:
    - Precise resolution scaling calibrated to 720p base standard (so 52px looks identical in proportion on 360p, 720p, 1080p).
    - Perfect visual alignment, contrast outline/box, and drop shadows.
    - Support for word-by-word viral karaoke animation OR beautiful styled static phrases.
    """
    with open(subtitles_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        subtitles = data.get("subtitles", [])

    # Strict language normalization to forbid cross-language badge pollution (e.g. Vietnamese in Spanish)
    p_sub = Path(subtitles_json_path)
    resolved_lang = str(language or "auto").lower().strip()
    if resolved_lang in ("auto", "none", "", "vi", "en"):
        job_file = p_sub.parent / "job.json"
        if job_file.is_file():
            try:
                import json as _jf_json
                with open(job_file, 'r', encoding='utf-8') as jf:
                    j_val = _jf_json.load(jf).get("language")
                    if j_val:
                        resolved_lang = str(j_val).lower().strip()
            except Exception:
                pass
        if resolved_lang in ("auto", "none", ""):
            sample_txt = " ".join(str(s.get("text", "")) for s in subtitles[:6]).lower()
            if any(c in sample_txt for c in 'àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ'):
                resolved_lang = "vi"
            elif any(w in sample_txt for w in [' que ', ' de ', ' la ', ' el ', ' en ', ' y ', ' por ', ' una ', ' con ', ' para ', 'existe']):
                resolved_lang = "es"
            else:
                resolved_lang = "en" 

    # Auto-load companion .words.json if present and root has no word-level timestamps
    if subtitles:
        has_words = any(s.get("words") for s in subtitles if isinstance(s, dict))
        if not has_words:
            # Check for sibling .words.json
            p_sub = Path(subtitles_json_path)
            candidate_words_files = [
                p_sub.with_name(p_sub.stem + ".words.json"),
                p_sub.parent / "dialogue_master.wav.words.json",
                p_sub.parent / "narration.wav.words.json",
            ]
            for cand in candidate_words_files:
                if cand.exists():
                    try:
                        with open(cand, 'r', encoding='utf-8') as wf:
                            w_payload = json.load(wf)
                            cand_subs = w_payload.get("subtitles", [])
                            if cand_subs and any(cs.get("words") for cs in cand_subs):
                                subtitles = cand_subs
                                print(f"[SUBTITLE_ENGINE] Auto-enriched with exact word boundaries from: {cand.name}")
                                break
                    except Exception:
                        pass

    if not subtitles:
        return ""

    # Baseline font size is calibrated against standard 720p HD canvas
    base_font_size = int(custom_font_size) if custom_font_size and int(custom_font_size) > 0 else 52
    scale = (video_height / 720.0) if video_height > 0 else 1.0
    font_size = max(14, int(round(base_font_size * scale)))

    cfg = SUBTITLE_STYLES.get(subtitle_style, SUBTITLE_STYLES.get("yellow_black", {}))
    is_box = str(cfg.get("BorderStyle", "1")) == "3" or "box" in subtitle_style
    border_style = "3" if is_box else "1"

    outline = round(max(1.8, font_size * 0.088), 1)
    box_outline = round(max(2.0, font_size * 0.06), 1) if is_box else outline
    shadow = 0 if is_box else round(max(1.0, font_size * 0.035), 1)
    
    # Smart vertical safe zone for 9:16 Shorts to avoid TikTok/Reels UI overlay
    is_vertical = (video_width > 0 and video_height > video_width) or (video_height >= 1200 and video_width <= 1080)
    if is_vertical:
        margin_v = max(140, int(video_height * 0.14))
    else:
        margin_v = round(max(24, font_size * 0.95))
    margin_lr = round(max(24, video_width * 0.035))

    primary_col = cfg.get("PrimaryColour", "&H00FFFFFF")
    secondary_col = "&H0000FFFF"  # Yellow for active karaoke word
    outline_col = cfg.get("OutlineColour", "&H00000000")
    back_col = cfg.get("BackColour", "&H90000000")
    bold = cfg.get("Bold", "1")

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {video_width}
PlayResY: {video_height}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: StudioSub,Arial,{font_size},{primary_col},{secondary_col},{outline_col},{back_col},{bold},0,0,0,100,100,0,0,{border_style},{box_outline},{shadow},2,{margin_lr},{margin_lr},{margin_v},1
Style: KineticSticker,Segoe UI Emoji,{max(18, int(round(font_size * 0.95)))},&H0000FFFF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,3.2,1.8,2,{margin_lr},{margin_lr},{margin_v + int(round(font_size * 1.55))},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    dialogues = []

    def format_ass_ts(seconds):
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centis = int(round((seconds * 100) % 100))
        if centis >= 100:
            centis = 99
        return f"{hrs}:{mins:02d}:{secs:02d}.{centis:02d}"

    if subtitle_style == "karaoke_viral":
        chunk_size = 3 if base_font_size >= 65 else 4
        for sub in subtitles:
            sub_words = sub.get("words")
            if sub_words and isinstance(sub_words, list) and len(sub_words) > 0 and isinstance(sub_words[0], dict):
                # 1. Exact Word-Level Audio Timestamp Alignment (Milestone 1)
                lines_words = [sub_words[i:i + chunk_size] for i in range(0, len(sub_words), chunk_size)]
                for line_w in lines_words:
                    for w_pos, w_info in enumerate(line_w):
                        w_start = float(w_info.get("start", sub.get("start", 0.0)))
                        if w_pos + 1 < len(line_w):
                            next_start = float(line_w[w_pos + 1].get("start", w_start + 0.3))
                            raw_end = float(w_info.get("end", w_start + 0.3))
                            w_end = next_start if (next_start - raw_end) < 0.35 else raw_end
                        else:
                            w_end = float(w_info.get("end", w_start + 0.3)) + 0.18

                        parts = []
                        for j, item in enumerate(line_w):
                            word_str = item.get("word", "") if isinstance(item, dict) else str(item)
                            if j == w_pos:
                                parts.append(r"{\c&H0000FFFF\b1\fscx112\fscy112}" + word_str + r"{\c" + primary_col + r"\b0\fscx100\fscy100}")
                            else:
                                parts.append(word_str)
                        line_text = " ".join(parts)
                        dialogues.append(f"Dialogue: 0,{format_ass_ts(w_start)},{format_ass_ts(w_end)},StudioSub,,0,0,0,,{line_text}")
            else:
                # Fallback: Proportional distribution when word timestamps are absent
                text = sub.get("text", "").strip()
                words = text.split()
                if not words:
                    continue

                lines_words = [words[i:i + chunk_size] for i in range(0, len(words), chunk_size)]
                total_words = len(words)
                chunk_dur = max(0.2, sub["end"] - sub["start"])
                word_dur = chunk_dur / max(1, total_words)

                word_idx = 0
                for line_w in lines_words:
                    line_start = sub["start"] + word_idx * word_dur
                    for w_pos, w in enumerate(line_w):
                        w_start = line_start + w_pos * word_dur
                        w_end = w_start + word_dur

                        parts = []
                        for j, word_item in enumerate(line_w):
                            if j == w_pos:
                                parts.append(r"{\c&H0000FFFF\b1\fscx112\fscy112}" + word_item + r"{\c" + primary_col + r"\b0\fscx100\fscy100}")
                            else:
                                parts.append(word_item)
                        line_text = " ".join(parts)
                        dialogues.append(f"Dialogue: 0,{format_ass_ts(w_start)},{format_ass_ts(w_end)},StudioSub,,0,0,0,,{line_text}")
                    word_idx += len(line_w)
    else:
        # Non-karaoke styles: chunk into short, readable 4-6 word phrases
        chunk_size = 4 if base_font_size >= 65 else 6
        for sub in subtitles:
            sub_words = sub.get("words")
            if sub_words and isinstance(sub_words, list) and len(sub_words) > 0 and isinstance(sub_words[0], dict):
                chunks = [sub_words[i:i + chunk_size] for i in range(0, len(sub_words), chunk_size)]
                for cwords in chunks:
                    cs = float(cwords[0].get("start", sub.get("start", 0.0)))
                    ce = float(cwords[-1].get("end", cs + 0.8)) + 0.15
                    line_text = " ".join(cw.get("word", "") for cw in cwords)
                    dialogues.append(f"Dialogue: 0,{format_ass_ts(cs)},{format_ass_ts(ce)},StudioSub,,0,0,0,,{line_text}")
            else:
                text = sub.get("text", "").strip()
                words = text.split()
                if not words:
                    continue

                chunks = [words[i:i + chunk_size] for i in range(0, len(words), chunk_size)]
                dur = max(0.2, sub["end"] - sub["start"])
                cdur = dur / max(1, len(chunks))

                for ci, cwords in enumerate(chunks):
                    cs = sub["start"] + ci * cdur
                    ce = min(sub["end"], cs + cdur)
                    line_text = " ".join(cwords)
                    dialogues.append(f"Dialogue: 0,{format_ass_ts(cs)},{format_ass_ts(ce)},StudioSub,,0,0,0,,{line_text}")

    # Inject Kinetic Keyword Stickers (Milestone 4)
    if enable_stickers:
        try:
            from .kinetic_stickers import extract_kinetic_stickers_from_subtitles, generate_ass_sticker_events
            stickers = extract_kinetic_stickers_from_subtitles(subtitles, language=resolved_lang)
            if stickers:
                sticker_lines = generate_ass_sticker_events(stickers, format_ass_ts)
                dialogues.extend(sticker_lines)
                print(f"[SUBTITLE_ENGINE] Injected {len(sticker_lines)} kinetic keyword stickers: {[s['badge'] for s in stickers]}", flush=True)
        except Exception as st_err:
            print(f"[SUBTITLE_ENGINE] Note kinetic stickers: {st_err}", flush=True)

    with open(ass_output_path, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(dialogues) + "\n")

    return ass_output_path


def generate_karaoke_ass(
    subtitles_json_path: str,
    ass_output_path: str,
    video_height: int = 720,
    video_width: int = 1280,
    custom_font_size: int = 0,
) -> str:
    """Backward-compatible wrapper for generating viral karaoke ASS subtitles."""
    return generate_styled_ass(
        subtitles_json_path=subtitles_json_path,
        ass_output_path=ass_output_path,
        subtitle_style="karaoke_viral",
        video_height=video_height,
        video_width=video_width,
        custom_font_size=custom_font_size,
    )


def build_force_style(
    style_key: str = "yellow_black",
    video_height: int = 720,
    custom_font_size: int = 0,
    video_width: int = 1280
) -> str:
    """Builds a libass force_style string properly proportioned to video resolution."""
    cfg = SUBTITLE_STYLES.get(style_key, SUBTITLE_STYLES.get("yellow_black", {}))
    base_font_size = int(custom_font_size) if custom_font_size and int(custom_font_size) > 0 else 52
    scale = (video_height / 720.0) if video_height > 0 else 1.0
    font_size = max(14, int(round(base_font_size * scale)))
    outline = round(max(1.8, font_size * 0.088), 1)

    is_vertical = (video_width > 0 and video_height > video_width) or (video_height >= 1200 and video_width <= 1080)
    if is_vertical:
        margin_v = max(140, int(video_height * 0.14))
    else:
        margin_v = round(max(24, font_size * 0.95))

    parts = [
        "FontName=Arial",
        f"FontSize={font_size}",
        f"Bold={cfg.get('Bold', '1')}",
        f"PrimaryColour={cfg.get('PrimaryColour', '&H0000FFFF')}",
        f"OutlineColour={cfg.get('OutlineColour', '&H00000000')}",
        f"BackColour={cfg.get('BackColour', '&H80000000')}",
        f"BorderStyle={cfg.get('BorderStyle', '1')}",
        f"Outline={cfg.get('Outline', str(outline))}",
        f"Shadow={cfg.get('Shadow', '1.5')}",
        "Alignment=2",  # Bottom-Center alignment
        f"MarginV={margin_v}",
    ]
    return ",".join(parts)


def burn_subtitles_to_video_tool_fn(
    video_path: str,
    subtitles_json_path: str,
    output_path: str = None,
    subtitle_style: str = "karaoke_viral",
    video_height: int = 720,
    video_width: int = 0,
    custom_font_size: int = 0,
    enable_stickers: bool = True,
    language: str = "auto",
) -> str:
    """
    Burns high-contrast, beautiful subtitles into a video file using FFmpeg and libass.
    
    Args:
        video_path: Path to the input video file.
        subtitles_json_path: Path to the JSON subtitle file.
        output_path: Optional path for the output video.
        subtitle_style: Style preset ('karaoke_viral', 'yellow_black', 'yellow_box', 'white_box', 'white_stroke', 'cyan_black', 'green_black', 'none').
        video_height: Height of the video for proportional font sizing.
        video_width: Width of the video canvas (e.g. 1080 for 9:16, 1280 for 16:9).
        custom_font_size: Custom font size in pixels (0 for standard 52px).
    
    Returns:
        Path to the video file with burned-in subtitles.
    """
    if not os.path.exists(video_path):
        return f"Error: Video file not found at {video_path}"
    if not os.path.exists(subtitles_json_path):
        return f"Error: Subtitle file not found at {subtitles_json_path}"

    if subtitle_style == "none":
        if output_path and os.path.abspath(video_path) != os.path.abspath(output_path):
            import shutil
            shutil.copy2(video_path, output_path)
            return output_path
        return video_path

    try:
        with open(subtitles_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            subtitles = data.get("subtitles", [])

        if not subtitles:
            print("[SUBTITLE_ENGINE] Warning: No subtitles found in JSON. Keeping original video.")
            if output_path and os.path.abspath(video_path) != os.path.abspath(output_path):
                import shutil
                shutil.copy2(video_path, output_path)
                return output_path
            return video_path

        # Determine output path
        if not output_path:
            base, ext = os.path.splitext(video_path)
            output_path = f"{base}_with_subtitles{ext}"

        same_file = os.path.abspath(video_path) == os.path.abspath(output_path)
        actual_output = f"{output_path}.tmp_sub_burn.mp4" if same_file else output_path

        base_sz = int(custom_font_size) if custom_font_size and int(custom_font_size) > 0 else 52
        if video_width > 0:
            width = video_width
        else:
            width = int(video_height * 16 / 9) if video_height > 0 else 1280

        # 1. UNIFIED ASS ENGINE (PIXEL-PERFECT SCALING FOR ALL STYLES)
        ass_path = subtitles_json_path.replace(".json", ".ass")
        generate_styled_ass(
            subtitles_json_path, ass_path,
            subtitle_style=subtitle_style,
            video_height=video_height, video_width=width,
            custom_font_size=base_sz,
            enable_stickers=enable_stickers,
            language=language
        )

        ass_p = Path(ass_path)
        parent_dir = ass_p.parent
        use_cwd = parent_dir.exists() and Path(video_path).parent == parent_dir

        if use_cwd:
            cmd = [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-i", Path(video_path).name,
                "-vf", f"ass='{ass_p.name}'",
                "-c:a", "copy",
                Path(actual_output).name
            ]
            run_cwd = str(parent_dir)
        else:
            escaped_ass = ass_p.as_posix().replace(':', r'\:')
            cmd = [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-i", str(video_path),
                "-vf", f"ass='{escaped_ass}'",
                "-c:a", "copy",
                str(actual_output)
            ]
            run_cwd = None

        print(f"[SUBTITLE_ENGINE] Burning {subtitle_style} subtitles (base={base_sz}px, canvas={width}x{video_height}) into: {output_path}")
        result = subprocess.run(
            cmd, cwd=run_cwd, capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
        )

        # Clean up temporary ASS file
        if os.path.exists(ass_path):
            try:
                os.remove(ass_path)
            except OSError:
                pass

        if result.returncode == 0 and os.path.exists(actual_output) and os.path.getsize(actual_output) > 1000:
            if same_file:
                import shutil
                if os.path.exists(output_path):
                    try:
                        os.remove(output_path)
                    except Exception:
                        pass
                shutil.move(actual_output, output_path)
            return output_path
        else:
            print(f"[SUBTITLE_ENGINE] Warning: ASS burn failed ({result.stderr[-250:]}), falling back to force_style")

        # 2. FALLBACK SRT ENGINE WITH EXPLICIT ORIGINAL_SIZE
        srt_path = subtitles_json_path.replace(".json", ".srt")
        with open(srt_path, 'w', encoding='utf-8') as f:
            for i, sub in enumerate(subtitles):
                start = sub['start']
                end = sub['end']
                text = sub['text']

                def format_ts(seconds):
                    hrs = int(seconds // 3600)
                    mins = int((seconds % 3600) // 60)
                    secs = int(seconds % 60)
                    milli = int((seconds * 1000) % 1000)
                    return f"{hrs:02d}:{mins:02d}:{secs:02d},{milli:03d}"

                f.write(f"{i+1}\n")
                f.write(f"{format_ts(start)} --> {format_ts(end)}\n")
                f.write(f"{text}\n\n")

        srt_p = Path(srt_path)
        fallback_style = subtitle_style if subtitle_style in SUBTITLE_STYLES and subtitle_style != "karaoke_viral" else "yellow_black"
        force_style = build_force_style(fallback_style, video_height, custom_font_size=base_sz, video_width=width)

        if use_cwd:
            cmd_fallback = [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-i", Path(video_path).name,
                "-vf", f"subtitles='{srt_p.name}':original_size={width}x{video_height}:force_style='{force_style}'",
                "-c:a", "copy",
                Path(actual_output).name
            ]
        else:
            escaped_srt = srt_p.as_posix().replace(':', r'\:')
            cmd_fallback = [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-i", str(video_path),
                "-vf", f"subtitles='{escaped_srt}':original_size={width}x{video_height}:force_style='{force_style}'",
                "-c:a", "copy",
                str(actual_output)
            ]

        print(f"[SUBTITLE_ENGINE] Burning fallback subtitles ({fallback_style}) into: {output_path}")
        result_fb = subprocess.run(
            cmd_fallback, cwd=run_cwd, capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
        )

        if os.path.exists(srt_path):
            try:
                os.remove(srt_path)
            except OSError:
                pass

        if result_fb.returncode == 0 and os.path.exists(actual_output) and os.path.getsize(actual_output) > 1000:
            if same_file:
                import shutil
                if os.path.exists(output_path):
                    try:
                        os.remove(output_path)
                    except Exception:
                        pass
                shutil.move(actual_output, output_path)
            return output_path
        else:
            if os.path.exists(actual_output):
                try:
                    os.remove(actual_output)
                except Exception:
                    pass
            return f"Error during FFmpeg subtitle burn: {result_fb.stderr}"

    except Exception as e:
        return f"Error in burn_subtitles_to_video_tool: {str(e)}"
