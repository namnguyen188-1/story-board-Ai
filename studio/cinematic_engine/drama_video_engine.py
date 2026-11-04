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
        self, dialogue_beats, total_duration, srt_path, json_path=None,
        audio_path=None, language="auto",
    ):
        """Compatibility entry point; timings now come only from native audio."""
        from .native_audio_subtitles import write_native_subtitles
        srt_path = Path(srt_path)
        source = Path(audio_path) if audio_path else srt_path.parent / "muse_clip.mp4"
        expected = "\n".join(
            clean_dialogue_text(str(b.get("text", "") if isinstance(b, dict)
                                    else getattr(b, "text", "")))
            for b in dialogue_beats
        ).strip()
        return write_native_subtitles(source, expected, srt_path,
            json_path or srt_path.with_suffix(".json"), language=language)

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
        ref_proof = scene_dir / "scene_base_reference.json"
        ref_input = Path(reference_image_path) if reference_image_path else None
        ref_hash = None
        if ref_input and ref_input.is_file():
            import hashlib
            ref_hash = hashlib.sha256(ref_input.read_bytes()).hexdigest()
        secondary_refs = []
        if ref_hash:
            try:
                from .drama_asset_manager import get_scene_character_anchors
                episode_root = scene_dir.parent.parent if scene_dir.parent.name == "scenes" else scene_dir.parent
                characters = (scene.get("characters_present", []) if isinstance(scene, dict)
                              else getattr(scene, "characters_present", [])) or []
                for anchor in get_scene_character_anchors(episode_root, characters):
                    p = Path(anchor.get("image_path", ""))
                    if p.is_file() and p.resolve() != ref_input.resolve():
                        secondary_refs.append(p)
            except Exception:
                pass
        secondary_digests = [hashlib.sha256(p.read_bytes()).hexdigest() for p in secondary_refs] if ref_hash else []

        if base_img.exists() and base_img.stat().st_size > 5000:
            if not ref_hash:
                return base_img
            try:
                data = json.loads(ref_proof.read_text(encoding="utf-8"))
                if (data.get("reference_sha256") == ref_hash
                        and data.get("secondary_reference_sha256") == secondary_digests
                        and data.get("render_mode") == "character_identity"
                        and data.get("generation_source") == "comfyui_ipadapter"
                        and data.get("image_sha256") == hashlib.sha256(base_img.read_bytes()).hexdigest()):
                    return base_img
            except (OSError, ValueError):
                pass
            old = scene_dir / "scene_base_before_reference_repair.png"
            if not old.is_file():
                shutil.copy2(base_img, old)
            print("[DRAMA_REFERENCE] Existing frame has no valid identity-reference proof; creating a verified replacement.", flush=True)

        def save_reference_proof(source):
            if ref_hash:
                ref_proof.write_text(json.dumps({
                    "render_mode": "character_identity", "reference_image": str(ref_input),
                    "reference_sha256": ref_hash, "secondary_reference_sha256": secondary_digests,
                    "secondary_reference_images": [str(p) for p in secondary_refs],
                    "image_sha256": hashlib.sha256(base_img.read_bytes()).hexdigest(),
                    "generation_source": source,
                }, indent=2), encoding="utf-8")



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



        # Local ComfyUI SDXL + IP-Adapter. Gemini is NOT an image provider.
        # Every supplied cast portrait is applied to the sampling graph.
        try:
            from comfyui_image_provider import make_image as local_make_image
            frame_w, frame_h = ((1024, 576) if aspect_ratio == "16:9"
                                else (576, 1024))
            raw_path = local_make_image(
                prompt=prompt_text, output=scene_dir / "comfy_generated.png",
                reference_path=ref_str,
                character_reference_paths=[str(p) for p in secondary_refs],
                visual_style="cinematic", genre="drama",
                width=frame_w, height=frame_h, timeout=210)
            if raw_path and os.path.isfile(raw_path):
                shutil.copy2(raw_path, str(base_img))
                save_reference_proof("comfyui_ipadapter")
                return base_img

        except Exception as e:

            print(f"[DRAMA_VIDEO_WARN] Image generation tool encountered issue: {e}", flush=True)



        # Fallback 1: If reference image from Scene 1 exists, use it to preserve 100% visual consistency

        if ref_str and os.path.exists(ref_str) and os.path.getsize(ref_str) > 5000:

            print(f"[DRAMA_VIDEO] Anchoring visual style to episode reference frame: {Path(ref_str).name}", flush=True)

            from PIL import Image
            with Image.open(ref_str) as identity_image:
                identity_image.convert("RGB").save(str(base_img), format="PNG")
            save_reference_proof("reference_copy_after_generator_failure")

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

        image_provider: str = "comfyui",

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



        from audio_signal_guard import expected_scene_speech, require_audible_if_spoken
        expected_spoken_text = expected_scene_speech(scene)
        is_muse = str(image_provider).lower() == "muse_video"
        # Once an episode has an approved character asset pack, refuse unanchored
        # character scenes instead of silently falling back to text-to-video.
        scene_characters = (scene.get("characters_present", []) if isinstance(scene, dict)
                            else getattr(scene, "characters_present", [])) or []
        people = [str(name) for name in scene_characters if str(name).strip().lower() != "narrator"]
        episode_root = s_dir.parent.parent if s_dir.parent.name == "scenes" else s_dir.parent
        approved_assets = episode_root / "00_ASSET_PACK" / "characters"
        asset_bible = episode_root / "00_ASSET_PACK" / "asset_bible.json"
        if is_muse and asset_bible.is_file():
            from .drama_asset_first import bind_scene
            bind_scene(episode_root, scene if isinstance(scene, dict) else scene.to_dict(),
                       verify_scene_image=True)
        if people and approved_assets.is_dir():
            if not reference_image_path or not Path(reference_image_path).is_file():
                resolved_ref = None
                for person in people:
                    slug = re.sub(r"[^a-z0-9_\-]+", "_", person.strip().lower()).strip("_")
                    p_dir = approved_assets / slug
                    if p_dir.is_dir():
                        for img_f in sorted(p_dir.glob("*.png")):
                            if img_f.stat().st_size > 8000:
                                resolved_ref = img_f
                                break
                    if resolved_ref:
                        break
                if resolved_ref:
                    reference_image_path = resolved_ref
                elif is_muse:
                    raise RuntimeError("SCENE_CHARACTER_REFERENCE_MISSING: no approved image for " + ", ".join(people))

        base_img = s_dir / "scene_base.png"

        muse_clip = s_dir / "muse_clip.mp4"

        raw_motion_mp4 = s_dir / "scene_motion.mp4"

        final_mp4 = s_dir / "scene_final.mp4"

        srt_path = s_dir / "dialogue_subtitles.srt"



        # --- STEP 1: REAL AI VIDEO (MUSE) WITH 100% NATIVE AUDIO ---

        if is_muse:

            has_valid_muse_clip = muse_clip.is_file() and muse_clip.stat().st_size > 1024

            has_valid_base_img = base_img.is_file() and base_img.stat().st_size > 1000

            # Muse occasionally delivers genuine 3:2 footage for a requested
            # 16:9 scene. Preserve the original video and its Muse receipt.
            # Recovery uses the already downloaded clip; no second paid job.
            # Stage QC records ASPECT_ADAPTED, NOT native widescreen success.
            if has_valid_muse_clip and has_valid_base_img:
                from .drama_aspect_repair import video_info, normalize_3_2
                vw, vh, vdur = video_info(muse_clip)
                expected_ratio = width / height
                if abs((vw / vh) / expected_ratio - 1) > 0.05:
                    if abs(expected_ratio - 16 / 9) > 0.015:
                        raise RuntimeError("MUSE_ASPECT_MISMATCH_UNSUPPORTED")
                    proof = s_dir / "muse_job.json"
                    if not proof.is_file() or not (
                        __import__("json").loads(proof.read_text(encoding="utf-8")).get("video_remote")
                        or (s_dir / "aspect_adaptation.json").is_file()
                    ):
                        raise RuntimeError("MUSE_ASPECT_REPAIR_UNTRUSTED_ORIGIN")
                    fix = normalize_3_2(s_dir, target_width=width, target_height=height)
                    print("[MUSE_ASPECT_RECOVERY] Native 3:2 video preserved; "
                          "16:9 letterbox-free blurred side extension, "
                          "visual QC still required: " + str(fix["adapted_file"]), flush=True)



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
                        "reference_image": str(s_dir / "scene_master.png") if asset_bible.is_file() else (str(reference_image_path) if reference_image_path else None),
                        "character_anchors": [str(reference_image_path)] if reference_image_path else [],
                        "scene_image_path": str(s_dir / "scene_master.png") if asset_bible.is_file() else None,
                        "scene_dir": str(s_dir),
                        "episode_dir": str(s_dir.parent.parent if s_dir.parent.name == "scenes" else s_dir.parent),
                        "primary_focus_character": scene.get("primary_focus_character") if isinstance(scene, dict) else getattr(scene, "primary_focus_character", None),
                        "characters_present": scene.get("characters_present") if isinstance(scene, dict) else getattr(scene, "characters_present", []),

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
            if expected_spoken_text:
                require_audible_if_spoken(muse_clip, expected_spoken_text)

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



            # 3. Align captions to speech in the native video audio

            json_path = s_dir / "subtitles.json"

            sc_beats = scene.get("dialogue_beats", []) if isinstance(scene, dict) else [

                b.to_dict() if hasattr(b, "to_dict") else b for b in scene.dialogue_beats

            ]

            if not no_subtitles and subtitle_style not in ("none", "off", "disabled"):
                target_lang = ((scene.get("language") if isinstance(scene, dict)
                                else getattr(scene, "language", None))
                               or (bible or {}).get("language") or "auto")
                self.generate_dialogue_subtitles_for_duration(
                    sc_beats, clip_dur, srt_path, json_path=json_path,
                    audio_path=muse_clip, language=target_lang)
                try:
                    native_qc = json.loads(json_path.read_text(encoding="utf-8"))
                    if native_qc.get("script_mismatch"):
                        print("[MUSE_VOICE_NOTICE] Script mismatch noted, proceeding with video burn...", flush=True)
                except Exception:
                    pass



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

                burn_result = burn_subtitles_to_video_tool_fn(

                    video_path=str(muse_clip),

                    subtitles_json_path=str(json_path),

                    output_path=str(final_mp4),

                    subtitle_style=subtitle_style,

                    video_height=height,

                    video_width=width,

                    custom_font_size=subtitle_size,
            enable_stickers=True,

                )

                if str(burn_result).startswith("Error") or not final_mp4.is_file():
                    raise RuntimeError("SUBTITLE_BURN_FAILED: " + str(burn_result))

            else:

                cmd_copy = [

                    "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",

                    "-i", str(muse_clip.resolve()),

                    "-c", "copy",

                    str(final_mp4.resolve())

                ]

                subprocess.run(cmd_copy, check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))



            if expected_spoken_text:
                require_audible_if_spoken(final_mp4, expected_spoken_text)

            # Save render style metadata for cache invalidation & UI tracking

            (s_dir / "render_style.json").write_text(

                json.dumps({

                    "subtitle_style": subtitle_style,

                    "subtitle_size": subtitle_size,

                    "no_subtitles": no_subtitles,
                    "subtitle_timing_version": "native-audio-v1"

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



        if expected_spoken_text:
            require_audible_if_spoken(master_audio, expected_spoken_text)
        total_dur = get_wav_duration(master_audio)

        if total_dur <= 0.5:

            total_dur = 8.0

        if not no_subtitles and subtitle_style not in ("none", "off", "disabled"):
            dialogue_beats = (scene.get("dialogue_beats", []) if isinstance(scene, dict)
                              else scene.dialogue_beats)
            expected_speech = "\n".join(
                clean_dialogue_text(str(b.get("text", "") if isinstance(b, dict)
                                        else getattr(b, "text", "")))
                for b in dialogue_beats
            ).strip()
            if expected_speech:
                from .native_audio_subtitles import write_native_subtitles
                # Clean isolated dialogue matches timestamps in the mixed master track.
                clean_audio = s_dir / "dialogue_master.wav"
                if not clean_audio.is_file():
                    clean_audio = master_audio
                target_language = ((scene.get("language") if isinstance(scene, dict)
                                    else getattr(scene, "language", None))
                                   or (bible or {}).get("language") or "auto")
                write_native_subtitles(clean_audio, expected_speech, srt_path,
                                       s_dir / "subtitles.json", language=target_language)
                alignment_qc = json.loads((s_dir / "subtitles.json").read_text(encoding="utf-8"))
                if alignment_qc.get("script_mismatch"):
                    print("[DRAMA_VOICE_NOTICE] Script mismatch noted between ASR and script, proceeding with recognized audio alignment...", flush=True)

        if reference_image_path or not base_img.is_file() or base_img.stat().st_size < 1000:

            base_img = self.ensure_scene_base_visual(

                scene, s_dir, aspect_ratio=aspect_ratio, cast_map=cast_map, reference_image_path=reference_image_path

            )



        proof_path = s_dir / "scene_base_reference.json"
        if proof_path.is_file() and reference_image_path:
            proof = json.loads(proof_path.read_text(encoding="utf-8"))
            if proof.get("generation_source") == "reference_copy_after_generator_failure":
                print("[DRAMA_VIDEO_NOTICE] Using character anchor portrait with cinematic motion camera as fallback...", flush=True)

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

        if expected_spoken_text:
            require_audible_if_spoken(final_mp4, expected_spoken_text)

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

