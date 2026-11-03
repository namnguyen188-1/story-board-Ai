import os
import sys
import json
import subprocess
import shutil
from pathlib import Path

ROOT = Path(r"D:\STORYBOARD_AI")
EP_DIR = ROOT / "studio" / "productions" / "stoi" / "episode_002"
SCENES_DIR = EP_DIR / "scenes"
NATIVE_IMG_DIR = EP_DIR / "shorts_native_scenes"
OUT_DIR = EP_DIR / "00_DANG_BAI_YOUTUBE"
SERIES_PUB_ROOT = ROOT / "studio" / "productions" / "stoi" / "00_XUAT_BAN_TOAN_BO_SERIES"

AUDIO_FILE = SCENES_DIR / "scene_0001" / "audio.wav"
WORDS_FILE = SCENES_DIR / "scene_0001" / "audio.wav.words.json"

def format_ass_time(sec):
    hrs = int(sec // 3600)
    mins = int((sec % 3600) // 60)
    s = sec % 60
    secs = int(s)
    centis = int(round((s - secs) * 100))
    if centis >= 100:
        secs += 1
        centis = 0
    return f"{hrs}:{mins:02d}:{secs:02d}.{centis:02d}"

def assemble_short():
    img1 = NATIVE_IMG_DIR / "scene_01_hook_9x16.png"
    img2 = NATIVE_IMG_DIR / "scene_02_warrior_9x16.png"
    img3 = NATIVE_IMG_DIR / "scene_03_wisdom_9x16.png"
    img4 = NATIVE_IMG_DIR / "scene_04_mastery_9x16.png"

    for img_p in [img1, img2, img3, img4]:
        if not img_p.exists():
            print(f"Missing image: {img_p}")
            return False

    with open(WORDS_FILE, "r", encoding="utf-8") as f:
        words_data = json.load(f)

    # Clean Spanish text with proper accents
    SPANISH_WORDS = [
        "¿Qué", "pasaría", "si", "te", "dijera", "que", "una", "de", "las", "formas", "más", "astutas",
        "de", "ganarse", "el", "respeto", "ajeno", "es", "fingir", "ignorancia?",
        "Sí,", "has", "escuchado", "bien.",
        "Mientras", "otros", "se", "desesperan", "por", "demostrar", "cuánto", "saben,",
        "tú", "puedes", "lograr", "mucho", "más", "simplemente", "guardando", "silencio.",
        "Porque", "seamos", "honestos,",
        "¿qué", "sentido", "tiene", "ganar", "una", "discusión",
        "si", "al", "final", "terminas", "perdiendo", "tu", "paz", "interior?",
        "La", "verdadera", "maestría", "reside", "en", "la", "calma", "absoluta."
    ]

    raw_words = words_data["words"]
    total_dur = words_data["duration"]

    for i in range(min(len(SPANISH_WORDS), len(raw_words))):
        raw_words[i]["word"] = SPANISH_WORDS[i]

    # Group into 2-3 words per subtitle line
    chunks = []
    i = 0
    while i < len(raw_words):
        if i + 2 < len(raw_words) and any(raw_words[i+k]["word"].endswith(('.', '?', '!', ',')) for k in range(2)):
            c_len = 2
        elif i + 3 <= len(raw_words):
            c_len = 3
        else:
            c_len = len(raw_words) - i

        chunk_words = raw_words[i:i+c_len]
        chunks.append(chunk_words)
        i += c_len

    dialogue_lines = []
    for chunk in chunks:
        c_start = chunk[0]["start"]
        c_end = chunk[-1]["end"]
        for active_idx, w in enumerate(chunk):
            w_start = w["start"]
            w_end = w["end"]
            if active_idx == len(chunk) - 1:
                w_end = max(w_end, c_end)

            line_parts = []
            for j, cw in enumerate(chunk):
                word_str = cw["word"]
                if j == active_idx:
                    # Highlighted active word in bright yellow with crisp outline
                    line_parts.append(r"{\c&H00D7FF&\b1\fscx104\fscy104}" + word_str + r"{\c&HFFFFFF&\b1\fscx100\fscy100}")
                else:
                    line_parts.append(r"{\c&HFFFFFF&\b1\fscx100\fscy100}" + word_str)

            if len(line_parts) == 3:
                line_text = line_parts[0] + " " + line_parts[1] + r"\N" + line_parts[2]
            else:
                line_text = " ".join(line_parts)

            t_start = format_ass_time(w_start)
            t_end = format_ass_time(w_end)
            dialogue_lines.append(f"Dialogue: 0,{t_start},{t_end},StudioShorts,,0,0,0,,{line_text}")

    ass_content = f"""[Script Info]
Title: Stoic Shorts 9x16 True Native
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: StudioShorts,Arial,44,&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,1,0,0,0,100,100,0.5,0,1,4.5,1.5,2,140,140,460,1
Style: HookHeader,Arial,34,&H0000E5FF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,1.5,0,1,3.0,1.5,8,80,80,240,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,{format_ass_time(total_dur)},HookHeader,,0,0,0,,EL ARTE DEL SILENCIO
""" + "\n".join(dialogue_lines)

    ass_path = EP_DIR / "shorts_native_subtitles.ass"
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_content)

    cuts = [
        {"img": img1, "dur": 9.62, "motion": "slow_zoom_in"},
        {"img": img2, "dur": 9.96, "motion": "slow_pan_up"},
        {"img": img3, "dur": 9.52, "motion": "slow_zoom_in"},
        {"img": img4, "dur": 6.79, "motion": "subtle_pulse"},
    ]

    temp_dir = EP_DIR / "_du_lieu_tam"
    temp_dir.mkdir(exist_ok=True)
    clip_files = []

    for idx, c in enumerate(cuts):
        clip_out = temp_dir / f"native_short_clip_{idx}.mp4"
        dur = c["dur"]
        frames = int(dur * 30)

        if c["motion"] == "slow_zoom_in":
            z_expr = f"min(1.10, 1.0 + 0.10*on/{frames})"
            x_expr = "iw/2-(iw/zoom/2)"
            y_expr = "ih/2-(ih/zoom/2)"
        elif c["motion"] == "slow_pan_up":
            z_expr = "1.06"
            x_expr = "iw/2-(iw/zoom/2)"
            y_expr = f"ih/2-(ih/zoom/2) - (ih*0.03)*(on/{frames})"
        else:
            z_expr = f"min(1.08, 1.02 + 0.06*on/{frames})"
            x_expr = "iw/2-(iw/zoom/2)"
            y_expr = "ih/2-(ih/zoom/2)"

        vf = (
            f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
            f"zoompan=z='{z_expr}':x='{x_expr}':y='{y_expr}':d=1:s=1080x1920:fps=30"
        )

        cmd = [
            "ffmpeg", "-y", "-loop", "1", "-i", str(c["img"]),
            "-t", str(dur),
            "-vf", vf,
            "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
            "-r", "30",
            str(clip_out)
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        clip_files.append(clip_out)

    concat_txt = temp_dir / "native_short_concat.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        for cf in clip_files:
            f.write(f"file '{cf.as_posix()}'\n")

    raw_video = temp_dir / "native_short_raw.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_txt),
        "-c", "copy", str(raw_video)
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    final_short = EP_DIR / "episode_short.mp4"
    escaped_ass = str(ass_path).replace("\\", "/").replace(":", "\\:")

    cmd_final = [
        "ffmpeg", "-y",
        "-i", str(raw_video),
        "-i", str(AUDIO_FILE),
        "-vf", f"subtitles='{escaped_ass}'",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(final_short)
    ]
    subprocess.run(cmd_final, check=True)

    dst1 = OUT_DIR / "02_VIDEO_SHORTS_9x16.mp4"
    shutil.copy2(final_short, dst1)

    if SERIES_PUB_ROOT.exists():
        for d in SERIES_PUB_ROOT.glob("Tap_02*"):
            if d.is_dir():
                shutil.copy2(final_short, d / "VIDEO_SHORTS_9x16_Tap_02.mp4")

    print(f"SUCCESS: {final_short} -> {dst1}")
    return True

if __name__ == "__main__":
    assemble_short()
