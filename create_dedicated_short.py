import os
import sys
import json
import subprocess
from pathlib import Path

# Paths
ROOT = Path(r"D:\STORYBOARD_AI")
EP_DIR = ROOT / "studio" / "productions" / "stoi" / "episode_002"
SCENES_DIR = EP_DIR / "scenes"
OUT_DIR = EP_DIR / "00_DANG_BAI_YOUTUBE"
SERIES_PUB_DIR = ROOT / "studio" / "productions" / "stoi" / "00_XUAT_BAN_TOAN_BO_SERIES" / "Tap_02 - EL ARTE DEL SILENCIO - La Dura Verdad Que Nadie Te Dice - Sabiduría Estoica"

AUDIO_FILE = SCENES_DIR / "scene_0001" / "audio.wav"
WORDS_FILE = SCENES_DIR / "scene_0001" / "audio.wav.words.json"
JOB_FILE = SCENES_DIR / "scene_0001" / "job.json"

IMG_1 = SCENES_DIR / "scene_0001" / "image.png"
IMG_2 = SCENES_DIR / "scene_0002" / "image.png"
IMG_3 = SCENES_DIR / "scene_0003" / "image.png"
IMG_5 = SCENES_DIR / "scene_0005" / "image.png"

# Load words
with open(WORDS_FILE, "r", encoding="utf-8") as f:
    words_data = json.load(f)

# The correct Spanish script
SPANISH_SCRIPT = (
    "¿Qué pasaría si te dijera que una de las formas más astutas de ganarse el respeto ajeno "
    "es fingir ignorancia? Sí, has escuchado bien. Mientras otros se desesperan por demostrar cuánto "
    "saben, tú puedes lograr mucho más simplemente guardando silencio. Porque seamos honestos, "
    "¿qué sentido tiene ganar una discusión si al final terminas perdiendo tu paz interior? "
    "La verdadera maestría reside en la calma absoluta."
)
clean_words = SPANISH_SCRIPT.split()
raw_words = words_data["words"]
total_dur = words_data["duration"]  # 35.891

assert len(clean_words) == len(raw_words), f"Mismatch {len(clean_words)} vs {len(raw_words)}"

for i in range(len(clean_words)):
    raw_words[i]["word"] = clean_words[i]

# Generate ASS subtitle file
ass_path = EP_DIR / "shorts_native_subtitles.ass"

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

# Group words into short punchy chunks (2-3 words per chunk)
chunks = []
i = 0
while i < len(raw_words):
    # Determine chunk size: 2 or 3 words
    w_curr = raw_words[i]["word"]
    # Check punctuation for natural breaks
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
    
    # Within this chunk, create a dialogue line for each active word
    for active_idx, w in enumerate(chunk):
        w_start = w["start"]
        w_end = w["end"]
        # Extend end slightly so no flickering
        if active_idx == len(chunk) - 1:
            w_end = max(w_end, c_end)

        line_parts = []
        for j, cw in enumerate(chunk):
            word_str = cw["word"]
            if j == active_idx:
                # Active word: glowing yellow with subtle pop
                line_parts.append(r"{\c&H00FFFF&\b1\fscx106\fscy106}" + word_str + r"{\c&HFFFFFF&\b1\fscx100\fscy100}")
            else:
                line_parts.append(r"{\c&HFFFFFF&\b1\fscx100\fscy100}" + word_str)
        
        # If 3 words, break into 2 lines if needed
        if len(line_parts) == 3:
            line_text = line_parts[0] + " " + line_parts[1] + r"\N" + line_parts[2]
        else:
            line_text = " ".join(line_parts)

        t_start = format_ass_time(w_start)
        t_end = format_ass_time(w_end)
        dialogue_lines.append(f"Dialogue: 0,{t_start},{t_end},StudioShorts,,0,0,0,,{line_text}")

ass_content = f"""[Script Info]
Title: Stoic Shorts 9x16 Native
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: StudioShorts,Arial,58,&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,1,0,0,0,100,100,0.5,0,1,5.5,2.0,2,100,100,430,1
Style: HookHeader,Arial,36,&H0000FFFF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,1.5,0,1,3.5,1.5,8,60,60,220,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,{format_ass_time(total_dur)},HookHeader,,0,0,0,,EL ARTE DEL SILENCIO
""" + "\n".join(dialogue_lines)

with open(ass_path, "w", encoding="utf-8") as f:
    f.write(ass_content)

print(f"Generated ASS: {ass_path} ({len(dialogue_lines)} cues)")

# Timeline cuts (total 35.89s)
cuts = [
    {"img": IMG_1, "dur": 9.62, "zoom": "in"},    # 0.00 -> 9.62
    {"img": IMG_2, "dur": 2.09, "zoom": "punch"}, # 9.62 -> 11.71 (arms intact!)
    {"img": IMG_3, "dur": 9.96, "zoom": "in"},    # 11.71 -> 21.67
    {"img": IMG_5, "dur": 9.52, "zoom": "out"},   # 21.67 -> 31.19
    {"img": IMG_2, "dur": 4.70, "zoom": "in"},    # 31.19 -> 35.89 (climax)
]

clip_files = []
temp_dir = EP_DIR / "_du_lieu_tam"
temp_dir.mkdir(exist_ok=True)

for idx, c in enumerate(cuts):
    clip_out = temp_dir / f"short_clip_{idx}.mp4"
    dur = c["dur"]
    frames = int(dur * 30)
    
    # Zoom filter for vertical 1080x1920
    # Center crop of statue: statue is centered, scale height to 1920 then crop 1080
    if c["zoom"] == "in":
        z_expr = f"min(1.15, 1.0 + 0.15*on/{frames})"
    elif c["zoom"] == "out":
        z_expr = f"max(1.0, 1.15 - 0.15*on/{frames})"
    else: # punch
        z_expr = f"min(1.20, 1.05 + 0.15*on/{frames})"

    # Clean, smooth zoompan filter: input 1536x864, scale to 1080x1920 center
    # Use high-quality scale + crop + subtle ken burns
    vf = (
        f"scale=-1:1920,crop=1080:1920:(in_w-1080)/2:(in_h-1920)/2,"
        f"zoompan=z='{z_expr}':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30"
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
    print(f"Rendered clip {idx+1}/{len(cuts)}: {dur:.2f}s")

# Concat clips
concat_txt = temp_dir / "short_concat.txt"
with open(concat_txt, "w", encoding="utf-8") as f:
    for cf in clip_files:
        f.write(f"file '{cf.as_posix()}'\n")

raw_video = temp_dir / "short_raw_concat.mp4"
subprocess.run([
    "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_txt),
    "-c", "copy", str(raw_video)
], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Final burn: raw_video + AUDIO_FILE + ASS subtitles
final_short_path = EP_DIR / "episode_short.mp4"
escaped_ass = str(ass_path).replace("\\", "/").replace(":", "\\:")

cmd_final = [
    "ffmpeg", "-y",
    "-i", str(raw_video),
    "-i", str(AUDIO_FILE),
    "-vf", f"subtitles='{escaped_ass}'",
    "-c:v", "libx264", "-preset", "medium", "-crf", "18",
    "-c:a", "aac", "-b:a", "192k",
    "-shortest",
    str(final_short_path)
]
print("Burning final subtitles and audio...")
subprocess.run(cmd_final, check=True)
print(f"Generated Short Video: {final_short_path} (Size: {final_short_path.stat().st_size / 1024 / 1024:.2f} MB)")

# Copy to 00_DANG_BAI_YOUTUBE and series export
shutil_dst = OUT_DIR / "02_VIDEO_SHORTS_9x16.mp4"
import shutil
shutil.copy2(final_short_path, shutil_dst)
print(f"Copied to: {shutil_dst}")

if SERIES_PUB_DIR.exists():
    series_dst = SERIES_PUB_DIR / "VIDEO_SHORTS_9x16_Tap_02.mp4"
    shutil.copy2(final_short_path, series_dst)
    print(f"Copied to: {series_dst}")
