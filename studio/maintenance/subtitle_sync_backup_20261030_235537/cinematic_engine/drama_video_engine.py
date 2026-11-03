"""Cinematic Drama Engine - Video Synthesis & AI Lip-Sync Engine (Phase 4).

Generates cinematic scene visual frames, applies dynamic camera movements,

coordinates character turn-taking cuts, lip-sync / talking-head animations,

and burns character-labeled subtitles into the final master video.

"""

from __future__ import annotations



import os

import sys

import re

import json

import shutil

import subprocess

from pathlib import Path

from typing import Dict, List, Any, Optional, Tuple



# Reconfigure stdout/stderr for clean utf-8 logging on Windows

if hasattr(sys.stdout, "reconfigure"):

    try:

        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    except Exception:

        pass



# Add paths to sys.path if not present

CURRENT_DIR = Path(__file__).resolve().parent

STUDIO_DIR = CURRENT_DIR.parent

ENGINE_DIR = STUDIO_DIR / "engine"

WORKSPACE_DIR = STUDIO_DIR.parent

for p in [str(STUDIO_DIR), str(ENGINE_DIR), str(WORKSPACE_DIR)]:

    if p not in sys.path:

        sys.path.insert(0, p)



from .drama_schema import SceneDrama, DialogueBeat, CharacterProfile

from .drama_audio_engine import get_wav_duration





def clean_dialogue_text(text: str) -> str:

    """Strips character tags, speaker prefixes, and bracketed notes to keep pure spoken dialogue."""

    if not text:

        return ""

    cleaned = text.strip()

    cleaned = re.sub(r"^\[.*?\]\s*", "", cleaned)

    cleaned = re.sub(r"^\(.*?\)\s*", "", cleaned)

    cleaned = re.sub(r"^[A-Za-z0-9_\s\u00C0-\u1EF9\.\-]{2,35}(?:\(.*?\))?:\s*", "", cleaned)

    return cleaned.strip() or text.strip()





def get_media_duration(media_path: Path | str) -> float:

    """Probes the exact duration in seconds of any video or audio media file using ffprobe."""

    cmd = [

        "ffprobe", "-v", "error", "-show_entries", "format=duration",

        "-of", "default=noprint_wrappers=1:nokey=1", str(media_path)

    ]

    try:

        res = subprocess.run(

            cmd, capture_output=True, text=True, check=True,

            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)

        )

        return float(res.stdout.strip())

    except Exception:

        return 10.0





def format_srt_time(seconds: float) -> str:

    """Converts seconds float to SRT timestamp format 00:00:00,000."""

    millis = int(round((seconds % 1) * 1000))

    if millis >= 1000:

        millis = 999

    total_seconds = int(seconds)

    secs = total_seconds % 60

    total_mins = total_seconds // 60

    mins = total_mins % 60

    hours = total_mins // 60

    return f"{hours:02d}:{mins:02d}:{secs:02d},{millis:03d}"





def split_dialogue_into_subtitles(text: str, max_words: int = 12, min_words: int = 4) -> List[str]:

    """Splits dialogue text into natural, digestible sentence-level subtitle units."""

    text = re.sub(r'[\r\n]+', ' ', text).strip()

    if not text:

        return []

    parts = re.split(r'([.!?]+(?:\s+|$))', text)

    raw_sentences = []

    current = ''

    for p in parts:

        current += p

        if re.search(r'[.!?]+(?:\s+|$)', p):

            s = current.strip()

            if s:

                raw_sentences.append(s)

            current = ''

    if current.strip():

        raw_sentences.append(current.strip())



    merged = []

    buffer = ''

    for s in raw_sentences:

        w_count = len(s.split())

        buf_count = len(buffer.split())

        if not buffer:

            buffer = s

        elif buf_count + w_count <= max_words and (buf_count < min_words or w_count < min_words):

            buffer = f'{buffer} {s}'

        else:

            merged.append(buffer)

            buffer = s

    if buffer:

        merged.append(buffer)

    return merged





class DramaVideoEngine:

    """Orchestrates Visual Generation, Camera Cinematography, and Lip-Sync Video Production."""



    def __init__(self, fps: int = 30):

        self.fps = fps



    def generate_dialogue_subtitles_for_duration(

        self,

        dialogue_beats: List[Any],

        total_duration: float,

        srt_path: Path,

        json_path: Optional[Path] = None,

    ) -> Path:

        """Generates proportioned sentence-level SRT subtitles and JSON timeline across video duration."""

        srt_path = Path(srt_path)

        srt_path.parent.mkdir(parents=True, exist_ok=True)



        valid_beats = []

        for b in dialogue_beats:

            raw_t = b.get("text", "") if isinstance(b, dict) else getattr(b, "text", "")

            cleaned_t = clean_dialogue_text(str(raw_t or ""))

            if cleaned_t:

                valid_beats.append((b, cleaned_t))



        if not valid_beats:

            if srt_path.exists():

                try:

                    srt_path.unlink()

                except Exception:

                    pass

            if json_path and Path(json_path).exists():

                try:

                    Path(json_path).unlink()

                except Exception:

                    pass

            return srt_path



        # Check if dialogue_timeline.json exists for exact audio alignment

        timeline_file = srt_path.parent / "dialogue_timeline.json"

        timeline_beats = {}

        if timeline_file.exists():

            try:

                t_data = json.loads(timeline_file.read_text(encoding="utf-8"))

                for tb in t_data.get("beats", []):

                    b_id = tb.get("beat_id")

                    if b_id is not None:

                        timeline_beats[b_id] = tb

            except Exception:

                pass



        total_chars = max(1, sum(len(c_text) for _, c_text in valid_beats))

        margin_start = 0.4

        margin_end = 0.3

        usable_duration = max(1.0, total_duration - margin_start - margin_end)

        beat_gap = 0.20 if len(valid_beats) > 1 else 0.0

        speech_pool = max(0.5, usable_duration - beat_gap * (len(valid_beats) - 1))



        sub_items = []

        lines = []

        beat_cursor = margin_start



        for i, (b, clean_text) in enumerate(valid_beats, 1):

            b_id = b.get("beat_id", i) if isinstance(b, dict) else getattr(b, "beat_id", i)

            # 1. Determine beat time window [b_start, b_end]

            if b_id in timeline_beats:

                tb = timeline_beats[b_id]

                b_start = float(tb.get("start_time", beat_cursor))

                b_end = float(tb.get("end_time", b_start + 2.0))

            else:

                fraction = len(clean_text) / total_chars

                beat_dur = max(0.8, fraction * speech_pool)

                b_start = beat_cursor

                b_end = min(total_duration - 0.1, beat_cursor + beat_dur)

                beat_cursor = b_end + beat_gap



            # 2. Split dialogue text into distinct sentences (Sentence-by-Sentence rule)

            sentences = split_dialogue_into_subtitles(clean_text)

            if not sentences:

                sentences = [clean_text]



            # 3. Subdivide beat duration across its sentences

            if len(sentences) == 1:

                sub_items.append({

                    "start": round(b_start, 3),

                    "end": round(b_end, 3),

                    "text": sentences[0]

                })

            else:

                s_chars_total = max(1, sum(len(s) for s in sentences))

                s_gap = 0.12

                s_pool = max(0.4, (b_end - b_start) - s_gap * (len(sentences) - 1))

                s_cursor = b_start

                for s in sentences:

                    s_fraction = len(s) / s_chars_total

                    s_dur = max(0.6, s_fraction * s_pool)

                    s_start = round(s_cursor, 3)

                    s_end = round(min(b_end, s_cursor + s_dur), 3)

                    sub_items.append({

                        "start": s_start,

                        "end": s_end,

                        "text": s

                    })

                    s_cursor = s_end + s_gap



        # Format SRT entries

        for idx, item in enumerate(sub_items, 1):

            start_str = format_srt_time(item["start"])

            end_str = format_srt_time(item["end"])

            lines.append(f"{idx}\n{start_str} --> {end_str}\n{item['text']}\n")



        with open(srt_path, "w", encoding="utf-8") as f:

            f.write("\n".join(lines))



        if json_path:

            j_path = Path(json_path)

            j_path.parent.mkdir(parents=True, exist_ok=True)

            with open(j_path, "w", encoding="utf-8") as f:

                json.dump({"subtitles": sub_items}, f, ensure_ascii=False, indent=2)



        return srt_path



        total_chars = sum(len(c_text) for _, c_text in valid_beats)

        total_chars = max(1, total_chars)



        margin_start = 0.3

        margin_end = 0.3

        usable_duration = max(1.0, total_duration - margin_start - margin_end)

        gap = 0.15 if len(valid_beats) > 1 else 0.0

        speech_pool = max(0.5, usable_duration - gap * (len(valid_beats) - 1))



        lines = []

        sub_items = []

        cursor = margin_start

        for i, (b, clean_text) in enumerate(valid_beats, 1):

            fraction = len(clean_text) / total_chars

            beat_dur = max(0.8, fraction * speech_pool)

            start_t = cursor

            end_t = min(total_duration - 0.1, cursor + beat_dur)



            start_str = format_srt_time(start_t)

            end_str = format_srt_time(end_t)



            lines.append(f"{i}\n{start_str} --> {end_str}\n{clean_text}\n")

            sub_items.append({

                "start": round(start_t, 3),

                "end": round(end_t, 3),

                "text": clean_text

            })

            cursor = end_t + gap



        with open(srt_path, "w", encoding="utf-8") as f:

            f.write("\n".join(lines))



        if json_path:

            j_path = Path(json_path)

            j_path.parent.mkdir(parents=True, exist_ok=True)

            with open(j_path, "w", encoding="utf-8") as f:

                json.dump({"subtitles": sub_items}, f, ensure_ascii=False, indent=2)



        return srt_path



    def ensure_scene_base_visual(

        self,

        scene: SceneDrama | Dict[str, Any],

        scene_dir: Path,

        aspect_ratio: str = "16:9",

        cast_map: Optional[Dict[str, CharacterProfile]] = None,

        reference_image_path: Optional[Path] = None

    ) -> Path:

        """Generates or retrieves the high-resolution base artwork for the scene."""

        scene_dir = Path(scene_dir)

        scene_dir.mkdir(parents=True, exist_ok=True)

        base_img = scene_dir / "scene_base.png"



        if base_img.exists() and base_img.stat().st_size > 5000:

            return base_img



        # Check visual prompt

        visual_setup = scene.get("visual_setup", "") if isinstance(scene, dict) else scene.visual_setup

        visual_prompt = scene.get("visual_prompt", "") if isinstance(scene, dict) else scene.visual_prompt

        prompt_text = visual_prompt or visual_setup or "Cinematic drama interior, dramatic moody cinematic lighting, 8k resolution"



        # Append character appearance locks if present

        if cast_map:

            chars_present = scene.get("characters_present", []) if isinstance(scene, dict) else scene.characters_present

            for ch_name in chars_present:

                if ch_name in cast_map and cast_map[ch_name].appearance_lock:

                    prompt_text += f", {ch_name}: {cast_map[ch_name].appearance_lock}"



        ref_str = str(reference_image_path) if (reference_image_path and reference_image_path.exists()) else None

        print(f"[DRAMA_VIDEO] Generating scene base artwork (Ref: {bool(ref_str)}): {prompt_text[:60]}...", flush=True)



        # Attempt Gemini 2.5 Flash / Imagen image generation with style reference anchor

        try:

            from engine.tools.image_gen import image_gen_tool_fn

            raw_path = image_gen_tool_fn(prompt=prompt_text, reference_image_path=ref_str)

            if raw_path and os.path.exists(raw_path) and not raw_path.startswith("Error"):

                shutil.copy2(raw_path, str(base_img))

                return base_img

        except Exception as e:

            print(f"[DRAMA_VIDEO_WARN] Image generation tool encountered issue: {e}", flush=True)



        # Fallback 1: If reference image from Scene 1 exists, use it to preserve 100% visual consistency

        if ref_str and os.path.exists(ref_str) and os.path.getsize(ref_str) > 5000:

            print(f"[DRAMA_VIDEO] Anchoring visual style to episode reference frame: {Path(ref_str).name}", flush=True)

            shutil.copy2(ref_str, str(base_img))

            return base_img



        # Fallback to high-quality procedural cinematic frame using Pillow

        from PIL import Image, ImageDraw, ImageFont

        w, h = (1920, 1080) if aspect_ratio == "16:9" else (1080, 1920)

        img = Image.new("RGB", (w, h), color=(18, 22, 28))

        draw = ImageDraw.Draw(img)



        # Draw subtle cinematic gradient / vignette

        for y in range(h):

            factor = 1.0 - (abs(y - h / 2) / (h / 2)) * 0.4

            r = int(18 * factor)

            g = int(24 * factor)

            b = int(32 * factor)

            draw.line([(0, y), (w, y)], fill=(r, g, b))



        # Title and scene information

        summary_text = scene.get("summary", "") if isinstance(scene, dict) else scene.summary

        draw.text((80, 80), f"SCENE: {summary_text[:70]}", fill=(210, 215, 225))

        draw.rectangle([80, 115, w - 80, 117], fill=(80, 100, 130))



        img.save(str(base_img), quality=95)

        print(f"[DRAMA_VIDEO] Created procedural cinematic artwork: {base_img.name}", flush=True)

        return base_img



    def render_cinematic_motion_clip(

        self,

        image_path: Path,

        duration: float,

        output_video_path: Path,

        camera_motion: str = "slow_zoom_in",

        aspect_ratio: str = "16:9"

    ) -> Path:

        """Animates a static scene artwork into a dynamic cinematic camera movement clip."""

        out_path = Path(output_video_path)

        out_path.parent.mkdir(parents=True, exist_ok=True)

        w, h = ("1920", "1080") if aspect_ratio == "16:9" else ("1080", "1920")

        total_frames = max(30, int(duration * self.fps))



        # Motion equations for FFmpeg zoompan filter

        if camera_motion in ("slow_zoom_in", "slow_push_in"):

            vf = f"zoompan=z='min(zoom+0.0004,1.14)':d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps={self.fps}"

        elif camera_motion == "slow_zoom_out":

            vf = f"zoompan=z='max(1.14-0.0004*on,1.0)':d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps={self.fps}"

        elif camera_motion == "slow_pan_right":

            vf = f"zoompan=z=1.08:d={total_frames}:x='if(lte(on,1),(iw-iw/zoom)/2,x+0.4)':y='(ih-ih/zoom)/2':s={w}x{h}:fps={self.fps}"

        elif camera_motion == "slow_pan_left":

            vf = f"zoompan=z=1.08:d={total_frames}:x='if(lte(on,1),(iw-iw/zoom)/2,x-0.4)':y='(ih-ih/zoom)/2':s={w}x{h}:fps={self.fps}"

        else:

            # Subtle organic breathing motion

            vf = f"zoompan=z='min(zoom+0.0003,1.10)':d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps={self.fps}"



        cmd = [

            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",

            "-loop", "1", "-i", str(image_path),

            "-vf", vf,

            "-t", f"{duration:.3f}",

            "-c:v", "libx264",

            "-pix_fmt", "yuv420p",

            str(out_path)

        ]



        subprocess.run(cmd, check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))

        return out_path



    def assemble_final_scene_video(

        self,

        visual_video_path: Path,

        master_audio_path: Path,

        srt_subtitles_path: Optional[Path],

        output_final_path: Path,

        scene_dir: Path,

        aspect_ratio: str = "16:9",

        subtitle_style: str = "karaoke_viral",

        subtitle_size: int = 0,

        no_subtitles: bool = False,

        subtitles_json_path: Optional[Path] = None,

        width: int = 1280,

        height: int = 720,

    ) -> Path:

        """Muxes visual video track with master audio soundscape and burns styled subtitles."""

        out_path = Path(output_final_path)

        out_path.parent.mkdir(parents=True, exist_ok=True)

        s_dir = Path(scene_dir)



        in_vis = visual_video_path.name if visual_video_path.parent == s_dir else str(visual_video_path.resolve())

        in_aud = master_audio_path.name if master_audio_path.parent == s_dir else str(master_audio_path.resolve())



        if visual_video_path.is_file():

            try:

                from clean_watermark import remove_video_watermark

                remove_video_watermark(visual_video_path, visual_video_path, width=width, height=height)

            except Exception:

                pass

        burn_subs = not no_subtitles and subtitle_style not in ("none", "off", "disabled")

        has_sub_json = (subtitles_json_path and Path(subtitles_json_path).exists() and Path(subtitles_json_path).stat().st_size > 15)



        try:

            from tools.video_audio_lock import lock_video_to_audio_duration

        except ImportError:

            from studio.engine.tools.video_audio_lock import lock_video_to_audio_duration



        if not burn_subs or not has_sub_json:

            lock_video_to_audio_duration(

                video_path=str(visual_video_path),

                audio_path=str(master_audio_path),

                output_path=str(out_path),

                subtitles_json_path=str(subtitles_json_path) if subtitles_json_path else None

            )

            return out_path



        # Step 1: 1:1 Audio-Visual Kinetic Lock (Milestone 3)

        tmp_muxed = s_dir / "tmp_raw_muxed.mp4"

        lock_video_to_audio_duration(

            video_path=str(visual_video_path),

            audio_path=str(master_audio_path),

            output_path=str(tmp_muxed),

            subtitles_json_path=str(subtitles_json_path) if subtitles_json_path else None

        )



        # Step 1.5: Multi-Layer Atmospheric Overlay & 35mm Film Grain (Milestone 4)
        video_to_burn = str(tmp_muxed)
        try:
            from tools.cinematic_overlays import apply_cinematic_overlays
            tmp_fx = s_dir / "tmp_cinematic_fx.mp4"
            g_hint = getattr(self, "genre", "stoic") if hasattr(self, "genre") else "stoic"
            fx_res = apply_cinematic_overlays(
                video_path=str(tmp_muxed),
                output_path=str(tmp_fx),
                genre=g_hint,
                width=width,
                height=height
            )
            if Path(fx_res).is_file() and Path(fx_res).stat().st_size > 1000:
                video_to_burn = str(tmp_fx)
        except Exception as fx_err:
            print(f"[DRAMA_VIDEO] Note applying cinematic overlays: {fx_err}", flush=True)

        # Step 2: Burn styled subtitles & kinetic stickers using unified ASS subtitle engine (Milestone 1, 2, 4)

        from tools.video_subtitle import burn_subtitles_to_video_tool_fn

        burn_subtitles_to_video_tool_fn(

            video_path=video_to_burn,

            subtitles_json_path=str(subtitles_json_path),

            output_path=str(out_path),

            subtitle_style=subtitle_style,

            video_height=height,

            video_width=width,

            custom_font_size=subtitle_size,
            enable_stickers=True,

        )



        if tmp_muxed.exists():

            try:

                tmp_muxed.unlink()

            except Exception:

                pass



        return out_path



    def render_scene(

        self,

        scene: SceneDrama | Dict[str, Any],

        scene_dir: Path | str,

        aspect_ratio: str = "16:9",

        cast_map: Optional[Dict[str, CharacterProfile]] = None,

        reference_image_path: Optional[Path] = None,

        image_provider: str = "gemini",

        bible: Optional[Dict[str, Any]] = None,

        width: int = 1280,

        height: int = 720,

        subtitle_style: str = "karaoke_viral",

        subtitle_size: int = 0,

        no_subtitles: bool = False,

    ) -> Dict[str, Any]:

        """Full end-to-end rendering pipeline for a single drama scene.

        Supports Muse AI Real Motion Video (muse_video) with 100% native audio/speech,

        and procedural/Gemini visual frames with voiceover soundscape.

        """

        s_dir = Path(scene_dir)

        s_dir.mkdir(parents=True, exist_ok=True)



        is_muse = str(image_provider).lower() == "muse_video"

        base_img = s_dir / "scene_base.png"

        muse_clip = s_dir / "muse_clip.mp4"

        raw_motion_mp4 = s_dir / "scene_motion.mp4"

        final_mp4 = s_dir / "scene_final.mp4"

        srt_path = s_dir / "dialogue_subtitles.srt"



        # --- STEP 1: REAL AI VIDEO (MUSE) WITH 100% NATIVE AUDIO ---

        if is_muse:

            has_valid_muse_clip = muse_clip.is_file() and muse_clip.stat().st_size > 1024

            has_valid_base_img = base_img.is_file() and base_img.stat().st_size > 1000



            if not (has_valid_muse_clip and has_valid_base_img):

                print(f"[DRAMA_VIDEO] 🎬 Khởi động Muse AI Video Provider cho cảnh...", flush=True)

                try:

                    from muse_video_provider import make_scene_media



                    sc_num = scene.get("scene_number", 1) if isinstance(scene, dict) else scene.scene_number

                    sc_summary = scene.get("summary", "") if isinstance(scene, dict) else scene.summary

                    sc_setting = scene.get("setting", "") if isinstance(scene, dict) else scene.setting

                    sc_setup = scene.get("visual_setup", "") if isinstance(scene, dict) else scene.visual_setup

                    sc_cam = scene.get("camera_motion", "slow cinematic camera tracking") if isinstance(scene, dict) else scene.camera_motion

                    sc_beats = scene.get("dialogue_beats", []) if isinstance(scene, dict) else [

                        b.to_dict() if hasattr(b, "to_dict") else b for b in scene.dialogue_beats

                    ]



                    narration_lines = "\n".join([f"{b.get('speaker', '')}: {b.get('text', '')}" for b in sc_beats if isinstance(b, dict)])

                    action_lines = "; ".join([f"{b.get('speaker', '')}: {b.get('action', '')}" for b in sc_beats if isinstance(b, dict) and b.get("action")])

                    dialogue_lines = "; ".join([f"{b.get('speaker', '')}: {b.get('text', '')}" for b in sc_beats if isinstance(b, dict)])



                    scene_dict = {

                        "scene_number": sc_num,

                        "description": sc_summary,

                        "visual_setup": sc_setup or sc_setting,

                        "prompt": sc_setup or sc_summary,

                        "camera": sc_cam,

                        "action": action_lines,

                        "dialogue": dialogue_lines,

                        "narration": narration_lines,

                        "raw_9_fields": scene.get("raw_9_fields", "") if isinstance(scene, dict) else getattr(scene, "raw_9_fields", ""),

                        "account_id": scene.get("account_id") if isinstance(scene, dict) else getattr(scene, "account_id", None),

                    }



                    make_scene_media(

                        scene=scene_dict,

                        bible=bible or {},

                        output_image_path=base_img,

                        width=width,

                        height=height,

                        duration=10

                    )

                except Exception as muse_err:

                    print(f"[DRAMA_VIDEO_WARN] ⚠️ Muse AI gặp sự cố ({muse_err}).", flush=True)

                    raise



            if not (muse_clip.is_file() and muse_clip.stat().st_size > 1024):

                raise RuntimeError(f"MUSE_CLIP_MISSING: Cảnh {sc_num} không có file muse_clip.mp4 hợp lệ.")



            clip_dur = get_media_duration(muse_clip)

            print(f"[DRAMA_VIDEO] 🎥 Sử dụng VIDEO & ÂM THANH GỐC từ Muse ({muse_clip.stat().st_size / 1024 / 1024:.2f} MB, {clip_dur:.2f}s, KHÔNG ghép giọng ngoài)...", flush=True)



            # 1. Extract native audio for Studio tools/players

            try:

                cmd_extract_audio = [

                    "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",

                    "-i", str(muse_clip.resolve()),

                    "-vn", "-c:a", "pcm_s16le", "-ar", "24000", "-ac", "1",

                    str((s_dir / "scene_master_audio.wav").resolve())

                ]

                subprocess.run(cmd_extract_audio, check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))

                shutil.copy2(str(s_dir / "scene_master_audio.wav"), str(s_dir / "audio.wav"))

            except Exception as e_aud:

                print(f"[DRAMA_VIDEO_WARN] Không thể trích xuất audio WAV từ Muse: {e_aud}", flush=True)



            # 2. Extract base image thumbnail if missing

            if not base_img.is_file() or base_img.stat().st_size < 1000:

                try:

                    cmd_extract_frame = [

                        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",

                        "-ss", "00:00:00.500", "-i", str(muse_clip.resolve()),

                        "-vframes", "1", str(base_img.resolve())

                    ]

                    subprocess.run(cmd_extract_frame, check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))

                except Exception:

                    pass

            if base_img.is_file():

                try:

                    shutil.copy2(str(base_img), str(s_dir / "image.png"))

                except Exception:

                    pass



            # 3. Generate subtitles proportional to clip duration (pure dialogue only)

            json_path = s_dir / "subtitles.json"

            sc_beats = scene.get("dialogue_beats", []) if isinstance(scene, dict) else [

                b.to_dict() if hasattr(b, "to_dict") else b for b in scene.dialogue_beats

            ]

            self.generate_dialogue_subtitles_for_duration(sc_beats, clip_dur, srt_path, json_path=json_path)



            # 4. Burn subtitles according to selected style and size

            if muse_clip.is_file():

                try:

                    from clean_watermark import remove_video_watermark

                    remove_video_watermark(muse_clip, muse_clip, width=width, height=height)

                except Exception:

                    pass

            burn_subs = not no_subtitles and subtitle_style not in ("none", "off", "disabled")

            if burn_subs and json_path.exists() and json_path.stat().st_size > 15:

                from tools.video_subtitle import burn_subtitles_to_video_tool_fn

                burn_subtitles_to_video_tool_fn(

                    video_path=str(muse_clip),

                    subtitles_json_path=str(json_path),

                    output_path=str(final_mp4),

                    subtitle_style=subtitle_style,

                    video_height=height,

                    video_width=width,

                    custom_font_size=subtitle_size,
            enable_stickers=True,

                )

            else:

                cmd_copy = [

                    "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",

                    "-i", str(muse_clip.resolve()),

                    "-c", "copy",

                    str(final_mp4.resolve())

                ]

                subprocess.run(cmd_copy, check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))



            # Save render style metadata for cache invalidation & UI tracking

            (s_dir / "render_style.json").write_text(

                json.dumps({

                    "subtitle_style": subtitle_style,

                    "subtitle_size": subtitle_size,

                    "no_subtitles": no_subtitles

                }, indent=2),

                encoding="utf-8"

            )



            # 5. Synchronize final.mp4 for web player

            try:

                shutil.copy2(str(final_mp4), str(s_dir / "final.mp4"))

            except Exception:

                pass



            print(f"[DRAMA_VIDEO_SUCCESS] Hoàn thành cảnh với Video & Âm thanh gốc Muse (Phụ đề: {subtitle_style}, Cỡ: {subtitle_size or 52}px): {final_mp4} ({final_mp4.stat().st_size / 1024 / 1024:.2f} MB, {clip_dur:.2f}s)", flush=True)

            return {

                "final_video_path": final_mp4,

                "duration": clip_dur,

                "base_image": base_img,

                "has_subtitles": srt_path.exists(),

                "used_real_video": True,

            }



        # --- STEP 2: FALLBACK / STANDARD PROCEDURAL IMAGE ZOOMPAN MODE ---

        master_audio = s_dir / "scene_master_audio.wav"

        if not master_audio.exists():

            master_audio = s_dir / "dialogue_master.wav"



        if not master_audio.exists():

            try:

                from .drama_audio_engine import DramaAudioEngine

                from .drama_sound_mixer import DramaSoundMixer

                ae = DramaAudioEngine()

                target_lang = scene.get("language") or (bible or {}).get("language") or getattr(self, "default_language", "Vietnamese")
                a_res = ae.assemble_scene_dialogue(scene=scene, language=target_lang, scene_dir=s_dir, cast_map=cast_map)

                sm = DramaSoundMixer()

                b_mood = scene.get("bgm_mood", "tense_investigation") if isinstance(scene, dict) else getattr(scene, "bgm_mood", "tense_investigation")

                s_cues = scene.get("sfx_cues", []) if isinstance(scene, dict) else getattr(scene, "sfx_cues", [])

                sm.mix_scene_audio(

                    dialogue_master_wav=Path(a_res["master_audio_path"]),

                    bgm_mood=b_mood,

                    sfx_cues=s_cues,

                    output_master_wav=master_audio

                )

            except Exception as e_syn:

                print(f"[DRAMA_VIDEO_WARN] Tự động tổng hợp master audio: {e_syn}", flush=True)

        if not master_audio.exists():

            raise FileNotFoundError(f"Neither scene_master_audio.wav nor dialogue_master.wav found in {s_dir}")



        total_dur = get_wav_duration(master_audio)

        if total_dur <= 0.5:

            total_dur = 8.0



        if not base_img.is_file() or base_img.stat().st_size < 1000:

            base_img = self.ensure_scene_base_visual(

                scene, s_dir, aspect_ratio=aspect_ratio, cast_map=cast_map, reference_image_path=reference_image_path

            )



        camera_motion = scene.get("camera_motion", "slow_zoom_in") if isinstance(scene, dict) else scene.camera_motion

        self.render_cinematic_motion_clip(

            image_path=base_img,

            duration=total_dur,

            output_video_path=raw_motion_mp4,

            camera_motion=camera_motion,

            aspect_ratio=aspect_ratio

        )



        img_png = s_dir / "image.png"

        if base_img.is_file() and (not img_png.exists() or img_png.stat().st_size != base_img.stat().st_size):

            try:

                shutil.copy2(str(base_img), str(img_png))

            except Exception:

                pass



        json_path = s_dir / "subtitles.json"

        self.assemble_final_scene_video(

            visual_video_path=raw_motion_mp4,

            master_audio_path=master_audio,

            srt_subtitles_path=srt_path if srt_path.exists() else None,

            output_final_path=final_mp4,

            scene_dir=s_dir,

            aspect_ratio=aspect_ratio,

            subtitle_style=subtitle_style,

            subtitle_size=subtitle_size,

            no_subtitles=no_subtitles,

            subtitles_json_path=json_path if json_path.exists() else None,

            width=width,

            height=height

        )

        (s_dir / "render_style.json").write_text(

            json.dumps({

                "subtitle_style": subtitle_style,

                "subtitle_size": subtitle_size,

                "no_subtitles": no_subtitles

            }, indent=2),

            encoding="utf-8"

        )



        legacy_final = s_dir / "final.mp4"

        if final_mp4.exists():

            try:

                shutil.copy2(str(final_mp4), str(legacy_final))

            except Exception:

                pass



        if raw_motion_mp4.exists() and final_mp4.exists():

            try:

                raw_motion_mp4.unlink()

            except Exception:

                pass



        print(f"[DRAMA_VIDEO_SUCCESS] Scene Final Video Produced: {final_mp4} ({final_mp4.stat().st_size / 1024 / 1024:.2f} MB, {total_dur:.2f}s, Real Video=False)", flush=True)



        return {

            "final_video_path": final_mp4,

            "duration": total_dur,

            "base_image": base_img,

            "has_subtitles": srt_path.exists(),

            "used_real_video": False,

        }

