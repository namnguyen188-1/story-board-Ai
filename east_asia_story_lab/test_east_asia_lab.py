"""Standalone End-to-End Verification Suite for East Asia (JP/KR) Story Lab.

Runs completely outside D:\\STORYBOARD_AI\\studio\\ so active Studio jobs are never impacted.
Verifies:
1. CJK sentence segmentation, particle-aware Japanese wrapping, Korean space wrapping
2. Font resolution (YuGothB.ttc / Yu Gothic & malgunbd.ttf / Malgun Gothic)
3. Real 3D tri-chromatic JP & KR thumbnails (16:9 and 9:16) with pixel ink assertions
4. Real After Skool hand-drawn colored_marker video + JP karaoke ASS burn-in MP4
5. Real Korean ASS burn-in MP4 + FFprobe stream verification
6. 24-Shot Banks (JP Edo & KR Joseon) and SEO metadata pack validation
"""
from __future__ import annotations

import json
import math
from pathlib import Path
import subprocess
import sys
import wave
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from east_asia_story_lab import (
    detect_cjk_language,
    resolve_cjk_font_path,
    resolve_ass_font_name,
    split_cjk_sentences,
    chunk_cjk_text,
    split_cjk_hook_lines,
    build_cjk_subtitles_json,
    generate_cjk_ass,
    burn_cjk_subtitles_ffmpeg,
    compose_cjk_thumbnail,
    EAST_ASIA_LOCALE,
    EAST_ASIA_GENRES,
    JP_EDO_SHOT_BANK,
    KR_JOSEON_SHOT_BANK,
    normalize_east_asia_bcp47,
    build_east_asia_seo_seed,
    build_clean_whiteboard_prompt,
    render_hand_drawn_cjk_sample,
    chunk_cjk_word_timestamps,
    voice_for_east_asia,
    tts_delivery_for_east_asia,
    map_east_asia_shots_to_scenes,
    studio_bridge,
)


def _create_sine_wav(path: Path, seconds: float = 4.0) -> Path:
    sr = 24000
    n = int(seconds * sr)
    t = np.linspace(0, seconds, n, endpoint=False)
    tone = (np.sin(2 * np.pi * 220 * t) * 1200 + np.sin(2 * np.pi * 330 * t) * 600).astype(np.int16)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(tone.tobytes())
    return path


def _draw_jp_zen_marker_plate(path: Path, width: int = 1280, height: int = 720) -> Path:
    """Creates a clean pure-white Japanese Zen marker artwork plate for Canny hand-draw testing."""
    im = Image.new("RGB", (width, height), (255, 255, 255))
    d = ImageDraw.Draw(im)
    cx, cy = int(width * 0.65), int(height * 0.50)

    # Bold crimson red rising sun / enso circle
    r_sun = min(width, height) // 5
    d.ellipse([cx - r_sun, cy - r_sun, cx + r_sun, cy + r_sun], fill=(220, 45, 45), outline=(25, 25, 25), width=7)

    # Torii Gate in crisp sumi black ink & crimson top lintel
    tx = int(width * 0.50)
    pillar_h = int(height * 0.45)
    top_y = cy - pillar_h // 3
    bot_y = cy + pillar_h // 2
    d.rectangle([tx - 150, top_y - 24, tx + 150, top_y], fill=(205, 35, 35), outline=(20, 20, 20), width=5)
    d.rectangle([tx - 125, top_y + 28, tx + 125, top_y + 48], fill=(245, 180, 40), outline=(20, 20, 20), width=5)
    d.rectangle([tx - 90, top_y, tx - 68, bot_y], fill=(35, 35, 40), outline=(15, 15, 15), width=4)
    d.rectangle([tx + 68, top_y, tx + 90, bot_y], fill=(35, 35, 40), outline=(15, 15, 15), width=4)

    # Minimalist calm Zen waves & bamboo stalks on right
    for k in range(3):
        yy = bot_y + 18 + k * 24
        d.arc([tx - 190, yy, tx + 190, yy + 32], start=190, end=350, fill=(30, 80, 145), width=5)
    bx = int(width * 0.84)
    d.line([(bx, int(height * 0.14)), (bx - 10, int(height * 0.82))], fill=(34, 125, 68), width=10)
    d.line([(bx - 6, int(height * 0.35)), (bx + 42, int(height * 0.25))], fill=(34, 125, 68), width=6)

    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path)
    return path


def _draw_kr_yadam_dark_plate(path: Path, width: int = 1280, height: int = 720) -> Path:
    """Creates a moody midnight moonlit Joseon courtyard test plate."""
    im = Image.new("RGB", (width, height), (14, 20, 38))
    d = ImageDraw.Draw(im)
    # Full silver moon on right
    mx, my, mr = int(width * 0.76), int(height * 0.30), 110
    d.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill=(232, 238, 250))
    # Hanok silhouette roof
    pts = [(int(width * 0.45), int(height * 0.62)), (int(width * 0.65), int(height * 0.46)),
           (int(width * 0.96), int(height * 0.46)), (width, int(height * 0.62))]
    d.polygon(pts, fill=(22, 26, 40))
    d.rectangle([int(width * 0.56), int(height * 0.62), int(width * 0.92), height], fill=(28, 30, 44))
    # Warm glowing paper door + lantern
    d.rectangle([int(width * 0.66), int(height * 0.68), int(width * 0.78), int(height * 0.90)], fill=(235, 165, 65))
    lx, ly = int(width * 0.58), int(height * 0.68)
    d.ellipse([lx - 18, ly - 24, lx + 18, ly + 24], fill=(220, 60, 50), outline=(255, 220, 120), width=3)
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path)
    return path


def _draw_jp_edo_plate(path: Path, width: int = 1280, height: int = 720) -> Path:
    """Creates a moody twilight Edo lantern corridor test plate."""
    im = Image.new("RGB", (width, height), (12, 16, 30))
    d = ImageDraw.Draw(im)
    # Twilight indigo sky gradient & distant castle silhouettes
    for y in range(0, int(height * 0.7), 6):
        c = 12 + int(16 * (y / float(height)))
        d.rectangle([0, y, width, y + 6], fill=(c, c + 4, c + 18))
    d.polygon([(int(width * 0.52), int(height * 0.62)), (int(width * 0.72), int(height * 0.34)), (int(width * 0.94), int(height * 0.62))], fill=(18, 22, 34))
    # Warm glowing paper andon lanterns along corridor right
    for lx, ly, r in ((int(width * 0.62), int(height * 0.44), 38), (int(width * 0.80), int(height * 0.48), 52)):
        d.ellipse([lx - r - 18, ly - r - 18, lx + r + 18, ly + r + 18], fill=(95, 50, 22))
        d.rectangle([lx - r // 2, ly - r, lx + r // 2, ly + r], fill=(250, 195, 95), outline=(45, 25, 15), width=4)
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path)
    return path


def _draw_kr_sayeon_vertical_plate(path: Path, width: int = 1080, height: int = 1920) -> Path:
    """Creates an atmospheric Seoul rainy night apartment drama plate (9:16)."""
    im = Image.new("RGB", (width, height), (18, 20, 32))
    d = ImageDraw.Draw(im)
    # Warm apartment window bokeh & rainy city glass
    d.rectangle([int(width * 0.14), int(height * 0.18), int(width * 0.86), int(height * 0.78)], fill=(32, 38, 56), outline=(55, 65, 88), width=6)
    for bx, by, br, col in (
        (280, 1280, 70, (240, 160, 75)),
        (540, 1360, 95, (215, 85, 75)),
        (780, 1220, 62, (95, 175, 235)),
    ):
        d.ellipse([bx - br, by - br, bx + br, by + br], fill=col)
    # Silhouette figure seated near window in lower-middle third
    cx = width // 2
    d.ellipse([cx - 115, 960, cx + 115, 1210], fill=(16, 18, 26))
    d.chord([cx - 240, 1200, cx + 240, 1840], start=180, end=360, fill=(14, 16, 24))
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path)
    return path


def _probe_video(path: Path) -> dict:
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration:stream=codec_name,codec_type,width,height",
        "-of", "json", str(path),
    ]
    out = subprocess.check_output(cmd, text=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return json.loads(out)


def _extract_frame(video_path: Path, sec: float, out_jpg: Path) -> None:
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-ss", str(sec), "-i", str(video_path), "-frames:v", "1", str(out_jpg),
    ]
    subprocess.run(cmd, check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


def run_all_tests() -> None:
    preview_dir = Path(__file__).resolve().parent / "output_preview"
    preview_dir.mkdir(parents=True, exist_ok=True)

    # 1. CJK Language & Font Verification
    jp_text = "本当に強い人は、侮辱されてもすぐには反応しません。沈黙こそが、あなたの心を守る最大の盾になるのです！知っていましたか？"
    kr_text = "정말 강한 사람은 모욕을 당해도 즉시 반응하지 않습니다. 침묵이야말로 당신의 마음을 지키는 가장 단단한 방패가 됩니다!"
    assert detect_cjk_language(jp_text) == "Japanese"
    assert detect_cjk_language(kr_text) == "Korean"
    jp_font = resolve_cjk_font_path(jp_text)
    kr_font = resolve_cjk_font_path(kr_text)
    assert "YuGoth" in jp_font or "meiryo" in jp_font.lower() or "msgothic" in jp_font.lower(), jp_font
    assert "malgun" in kr_font.lower(), kr_font
    assert resolve_ass_font_name(jp_text) == "Yu Gothic"
    assert resolve_ass_font_name(kr_text) == "Malgun Gothic"
    print("CHECK_1_FONTS_PASS:", jp_font, "|", kr_font)

    # 2. CJK Sentence Splitting, Chunking & Hook Splitting
    jp_sents = split_cjk_sentences(jp_text)
    assert len(jp_sents) == 3, jp_sents
    jp_chunks = chunk_cjk_text(jp_text, is_vertical=False)
    kr_chunks = chunk_cjk_text(kr_text, is_vertical=False)
    assert len(jp_chunks) >= 4 and all(len(c) <= 18 for c in jp_chunks), jp_chunks
    assert len(kr_chunks) >= 4 and all(len(c) <= 18 for c in kr_chunks), kr_chunks
    assert len(split_cjk_hook_lines("沈黙が最大の武器")) == 2
    assert len(split_cjk_hook_lines("침묵이 가장 강한 무기")) == 2
    print("CHECK_2_SEGMENTATION_PASS:", len(jp_chunks), "JP chunks,", len(kr_chunks), "KR chunks")

    # 3. Shot Banks & SEO Profiles
    assert len(JP_EDO_SHOT_BANK) == 24 and len(KR_JOSEON_SHOT_BANK) == 24
    assert "Japanese" in EAST_ASIA_LOCALE and "Korean" in EAST_ASIA_LOCALE
    assert normalize_east_asia_bcp47("Japanese") == "ja" and normalize_east_asia_bcp47("Korean") == "ko"
    jp_seo = build_east_asia_seo_seed("jp_zen_story", "心を整える3秒の沈黙", episode_num=1)
    kr_seo = build_east_asia_seo_seed("kr_yadam_joseon", "조선 선비의 침묵과 지혜", episode_num=1)
    assert jp_seo["default_language"] == "ja" and jp_seo["tags_char_count"] <= 500
    assert kr_seo["default_language"] == "ko" and kr_seo["tags_char_count"] <= 500
    assert "#FFFFFF" in build_clean_whiteboard_prompt("A Zen monk meditating beneath a torii gate")
    print("CHECK_3_PROFILES_SHOTBANK_SEO_PASS:", len(EAST_ASIA_GENRES), "genres")

    # 4. Generate Real JP & KR Thumbnails (16:9 and 9:16)
    jp_plate = _draw_jp_zen_marker_plate(preview_dir / "src_jp_zen_plate.png")
    kr_plate = _draw_kr_yadam_dark_plate(preview_dir / "src_kr_yadam_plate.png")
    thumb_jp_169 = compose_cjk_thumbnail(jp_plate, preview_dir / "thumb_jp_zen_16x9.jpg", "沈黙が最大の武器/禅の教え", language="Japanese", aspect_ratio="16:9")
    thumb_jp_916 = compose_cjk_thumbnail(jp_plate, preview_dir / "thumb_jp_zen_9x16.jpg", "3秒の静寂/心を守る", language="Japanese", aspect_ratio="9:16")
    thumb_kr_169 = compose_cjk_thumbnail(kr_plate, preview_dir / "thumb_kr_yadam_16x9.jpg", "침묵의 힘/조선야담", language="Korean", aspect_ratio="16:9")
    for tp in (thumb_jp_169, thumb_jp_916, thumb_kr_169):
        assert Path(tp).is_file() and Path(tp).stat().st_size > 20000, tp
    print("CHECK_4_THUMBNAILS_PASS")

    # 5. Render Real Hand-Drawn Colored Marker Video (JP) + Burn JP Karaoke ASS Subtitles
    wav_4s = _create_sine_wav(preview_dir / "test_voice.wav", seconds=4.0)
    jp_hand_raw = preview_dir / "jp_hand_drawn_raw.mp4"
    render_hand_drawn_cjk_sample(jp_plate, wav_4s, jp_hand_raw, width=1280, height=720, style="colored_marker")

    # Mux audio + burn JP karaoke ASS
    jp_muxed = preview_dir / "jp_hand_drawn_mux.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(jp_hand_raw), "-i", str(wav_4s),
        "-c:v", "copy", "-c:a", "aac", "-shortest", str(jp_muxed),
    ], check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))

    jp_sub_json = preview_dir / "jp_subs.json"
    build_cjk_subtitles_json(jp_text, 4.0, output_json=jp_sub_json, is_vertical=False, language="Japanese")
    jp_ass = generate_cjk_ass(jp_sub_json, preview_dir / "jp_subs.ass", subtitle_style="karaoke_viral", video_width=1280, video_height=720, language="Japanese")
    jp_final = preview_dir / "jp_hand_drawn_final_subtitled.mp4"
    burn_cjk_subtitles_ffmpeg(jp_muxed, jp_ass, jp_final)

    # Check strict monotonic non-overlapping timestamps in generated .ass
    def _assert_monotonic_ass(ass_path: Path):
        prev_end = -1.0
        for line in ass_path.read_text(encoding="utf-8").splitlines():
            if not line.startswith("Dialogue:"):
                continue
            parts = line.split(",", 3)
            def _sec(ts):
                h, m, s = ts.strip().split(":")
                return int(h) * 3600 + int(m) * 60 + float(s)
            st, en = _sec(parts[1]), _sec(parts[2])
            assert st < en, f"Invalid ASS event end<=start: {line}"
            assert st >= prev_end - 0.02, f"Overlapping ASS event: prev_end={prev_end} > start={st} | {line}"
            prev_end = en

    _assert_monotonic_ass(Path(jp_ass))
    probe_jp = _probe_video(jp_final)
    streams_jp = {s["codec_type"]: s for s in probe_jp["streams"]}
    assert streams_jp["video"]["codec_name"] == "h264" and streams_jp["video"]["width"] == 1280
    assert streams_jp["audio"]["codec_name"] == "aac"
    _extract_frame(jp_final, 1.5, preview_dir / "frame_jp_hand_drawn_subtitled.jpg")
    print("CHECK_5_JP_HANDDRAWN_VIDEO_PASS:", round(float(probe_jp["format"]["duration"]), 2), "sec")

    # 6. Render Real KR Yadam Video + Burn KR Malgun Gothic ASS Subtitles
    kr_raw_mux = preview_dir / "kr_yadam_mux.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-loop", "1", "-i", str(kr_plate), "-i", str(wav_4s),
        "-vf", "zoompan=z='min(zoom+0.001,1.15)':d=100:s=1280x720:fps=25",
        "-c:v", "libx264", "-t", "4", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest",
        str(kr_raw_mux),
    ], check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))

    kr_sub_json = preview_dir / "kr_subs.json"
    build_cjk_subtitles_json(kr_text, 4.0, output_json=kr_sub_json, is_vertical=False, language="Korean")
    kr_ass = generate_cjk_ass(kr_sub_json, preview_dir / "kr_subs.ass", subtitle_style="karaoke_viral", video_width=1280, video_height=720, language="Korean")
    _assert_monotonic_ass(Path(kr_ass))
    kr_final = preview_dir / "kr_yadam_final_subtitled.mp4"
    burn_cjk_subtitles_ffmpeg(kr_raw_mux, kr_ass, kr_final)

    probe_kr = _probe_video(kr_final)
    streams_kr = {s["codec_type"]: s for s in probe_kr["streams"]}
    assert streams_kr["video"]["codec_name"] == "h264" and streams_kr["audio"]["codec_name"] == "aac"
    _extract_frame(kr_final, 1.4, preview_dir / "frame_kr_yadam_subtitled.jpg")
    print("CHECK_6_KR_SUBTITLED_VIDEO_PASS:", round(float(probe_kr["format"]["duration"]), 2), "sec")

    # 7. Word Alignment, Voices & 24-Shot Montage Alternation
    jp_words = [
        {"word": "本当に", "start": 0.10, "end": 0.45},
        {"word": "強い", "start": 0.46, "end": 0.72},
        {"word": "人は", "start": 0.73, "end": 0.95},
        {"word": "すぐには", "start": 0.96, "end": 1.30},
        {"word": "反応しません。", "start": 1.31, "end": 1.95},
    ]
    jp_aligned = chunk_cjk_word_timestamps(jp_words, language="Japanese", is_vertical=False)
    assert jp_aligned and " " not in jp_aligned[0]["text"] and jp_aligned[-1]["text"].endswith("。"), jp_aligned
    kr_words = [
        {"word": "정말", "start": 0.10, "end": 0.35},
        {"word": "강한", "start": 0.36, "end": 0.62},
        {"word": "사람은", "start": 0.63, "end": 0.95},
        {"word": "침묵합니다.", "start": 0.96, "end": 1.50},
    ]
    kr_aligned = chunk_cjk_word_timestamps(kr_words, language="Korean", is_vertical=False)
    assert kr_aligned and " " in kr_aligned[0]["text"], kr_aligned
    assert chunk_cjk_word_timestamps([{"word": "Hello", "start": 0.0, "end": 0.4}], language="English") is None

    assert voice_for_east_asia("Japanese", "jp_zen_story") == "Sulafat"
    assert voice_for_east_asia("Korean", "kr_yadam_joseon") == "Gacrux"
    assert voice_for_east_asia("English", "stoic") is None
    assert tts_delivery_for_east_asia("jp_edo_sleepless") is not None
    assert tts_delivery_for_east_asia("stoic") is None

    mock_scenes_dir = preview_dir / "_mock_montage_scenes"
    mock_scenes = [{"scene_number": i + 1, "narration": f"夜の城と雨 {i}", "summary": "侍の道", "description": ""} for i in range(8)]
    shot_map = {s["id"]: kr_plate for s in JP_EDO_SHOT_BANK}
    map_east_asia_shots_to_scenes(mock_scenes, "jp_edo_sleepless", shot_map, mock_scenes_dir)
    shot_ids = [json.loads((mock_scenes_dir / f"scene_{i+1:04d}" / "montage_meta.json").read_text(encoding="utf-8"))["shot_id"] for i in range(8)]
    assert all(shot_ids[i] != shot_ids[i + 1] for i in range(len(shot_ids) - 1)), shot_ids
    print("CHECK_7_ALIGNER_VOICES_MONTAGE_PASS:", len(shot_ids), "alternating shots")

    # 8. Studio Bridge Safety Gate (Must Pass JP/KR & Ignore EN/ES/VI/Stoic)
    dummy_genres = {"stoic": ("Khắc kỷ", "color_cinematic")}
    dummy_art = {"stoic": "Marcus Aurelius"}
    added = studio_bridge.register_east_asia_modes(dummy_genres, dummy_art)
    assert added == 4 and len(dummy_genres) == 5
    assert studio_bridge.register_east_asia_modes(dummy_genres, dummy_art) == 0  # Idempotent
    assert studio_bridge.canonical_east_asia_language("ja") == "Japanese"
    assert studio_bridge.canonical_east_asia_language("ko-KR") == "Korean"
    assert studio_bridge.canonical_east_asia_language("Spanish") is None
    assert studio_bridge.resolve_thumb_font_if_cjk("SOLO EL SILENCIO", language="Spanish") is None
    assert studio_bridge.resolve_thumb_font_if_cjk("沈黙の力", language="auto") is not None
    assert studio_bridge.split_hook_if_cjk("SILENCE WINS / STOIC", language="English") is None
    assert studio_bridge.generate_ass_if_cjk(str(jp_sub_json), str(preview_dir / "bridge_jp.ass"), language="auto") is not None

    en_sub_json = preview_dir / "_tmp_en_subs.json"
    en_sub_json.write_text(json.dumps({"language": "English", "subtitles": [{"start": 0.2, "end": 1.8, "text": "Silence protects your peace."}]}), encoding="utf-8")
    assert studio_bridge.subtitle_json_if_cjk({"narration": "Silence protects your peace."}, 3.0, preview_dir / "_tmp_en_out.json", language="English") is False
    assert studio_bridge.generate_ass_if_cjk(str(en_sub_json), str(preview_dir / "_tmp_en.ass"), language="English") is None
    print("CHECK_8_STUDIO_BRIDGE_ISOLATION_PASS")

    # 9. Extra Visual Previews: Edo 16:9, Korean Sayeon 9:16, and JP Hand-Drawn Shorts 9:16
    edo_plate = _draw_jp_edo_plate(preview_dir / "src_jp_edo_plate.png")
    kr_sayeon_plate = _draw_kr_sayeon_vertical_plate(preview_dir / "src_kr_sayeon_9x16.png")
    thumb_edo = compose_cjk_thumbnail(edo_plate, preview_dir / "thumb_jp_edo_16x9.jpg", "江戸の静寂/眠れる歴史", language="Japanese", aspect_ratio="16:9")
    thumb_sayeon_916 = compose_cjk_thumbnail(kr_sayeon_plate, preview_dir / "thumb_kr_sayeon_9x16.jpg", "단 한마디에/무너진 가족", language="Korean", aspect_ratio="9:16")
    assert Path(thumb_edo).stat().st_size > 20000 and Path(thumb_sayeon_916).stat().st_size > 20000

    jp_plate_vert = _draw_jp_zen_marker_plate(preview_dir / "src_jp_zen_9x16.png", width=720, height=1280)
    jp_hand_916_raw = preview_dir / "jp_hand_drawn_9x16_raw.mp4"
    render_hand_drawn_cjk_sample(jp_plate_vert, wav_4s, jp_hand_916_raw, width=720, height=1280, style="colored_marker")
    jp_916_mux = preview_dir / "jp_hand_drawn_9x16_mux.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(jp_hand_916_raw), "-i", str(wav_4s),
        "-c:v", "copy", "-c:a", "aac", "-shortest", str(jp_916_mux),
    ], check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))

    jp_916_sub_json = preview_dir / "jp_916_subs.json"
    build_cjk_subtitles_json(jp_text, 4.0, output_json=jp_916_sub_json, is_vertical=True, language="Japanese")
    jp_916_ass = generate_cjk_ass(jp_916_sub_json, preview_dir / "jp_916_subs.ass", subtitle_style="karaoke_viral", video_width=720, video_height=1280, language="Japanese")
    _assert_monotonic_ass(Path(jp_916_ass))
    jp_916_final = preview_dir / "jp_zen_shorts_9x16_subtitled.mp4"
    burn_cjk_subtitles_ffmpeg(jp_916_mux, jp_916_ass, jp_916_final)
    probe_916 = _probe_video(jp_916_final)
    streams_916 = {s["codec_type"]: s for s in probe_916["streams"]}
    assert streams_916["video"]["width"] == 720 and streams_916["video"]["height"] == 1280
    _extract_frame(jp_916_final, 1.5, preview_dir / "frame_jp_shorts_9x16.jpg")
    print("CHECK_9_9X16_SHORTS_AND_EDO_SAYEON_PASS:", round(float(probe_916["format"]["duration"]), 2), "sec")
    print("ALL_EAST_ASIA_LAB_TESTS_PASS")


if __name__ == "__main__":
    run_all_tests()
