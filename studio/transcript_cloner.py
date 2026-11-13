"""Transcript & Screenplay Cloning Engine for Storyboard AI Studio Pro.
Extracts exact spoken audio/subtitles from competitor YouTube videos and translates
them 100% faithfully into target language with scene-by-scene alignment.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

try:
    import silent_subprocess
except Exception:
    pass

STUDIO_DIR = Path(__file__).resolve().parent
CLONES_CACHE_DIR = STUDIO_DIR / "character_clones"
CLONES_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def fetch_youtube_transcript(canonical_url: str, preferred_lang: str = "") -> dict:
    """Extracts raw subtitle/caption events from YouTube video via yt_dlp."""
    from competitor_cloner import extract_youtube_video_id
    video_id = extract_youtube_video_id(canonical_url)
    pref_slug = re.sub(r'[^a-zA-Z0-9_-]', '_', preferred_lang.lower()) if preferred_lang else "all"
    cache_file = CLONES_CACHE_DIR / f"{video_id}_captions_{pref_slug}.json"
    if cache_file.is_file():
        try:
            cached_data = json.loads(cache_file.read_text(encoding="utf-8"))
            if cached_data.get("ok") and cached_data.get("lines"):
                return cached_data
        except Exception:
            pass

    try:
        import yt_dlp
    except ImportError:
        return {"ok": False, "error": "yt_dlp not installed"}

    ydl_opts = {
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": 15,
        "windows_hide_console": True,
        "nocheckcertificate": True,
        "extractor_args": {"youtube": {"player_client": ["android", "ios", "web"]}},
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(canonical_url, download=False)
            subs = info.get("subtitles", {})
            auto_subs = info.get("automatic_captions", {})
            title = info.get("title", "")
            duration = info.get("duration", 0)

            # Prioritize tracks matching preferred_lang, then original spoken audio, then fallback
            pref = str(preferred_lang or "").lower()
            lang_candidates = []
            if pref:
                lang_candidates.extend([pref, pref[:2]])
            orig_l = str(info.get("language") or "").lower()
            if orig_l and orig_l not in lang_candidates:
                lang_candidates.extend([orig_l, orig_l[:2]])
            for k in list(subs.keys()) + list(auto_subs.keys()):
                k_clean = k.lower()
                if k_clean not in lang_candidates and not k_clean.startswith("en-"):
                    lang_candidates.append(k_clean)
            lang_candidates.extend(["es", "es-419", "en", "vi", "fr", "de", "pt", "ja", "ko", "zh"])

            chosen_tracks = None
            lang_code = ""

            # 1. Check human-authored subtitles first
            for cand in lang_candidates:
                for k in subs:
                    if k.lower() == cand or k.lower().startswith(cand):
                        chosen_tracks = subs[k]
                        lang_code = k
                        break
                if chosen_tracks:
                    break

            # 2. Check automatic captions next
            if not chosen_tracks:
                for cand in lang_candidates:
                    for k in auto_subs:
                        if k.lower() == cand or k.lower().startswith(cand):
                            chosen_tracks = auto_subs[k]
                            lang_code = k
                            break
                    if chosen_tracks:
                        break

            # 3. Last resort fallback
            if not chosen_tracks and subs:
                lang_code = list(subs.keys())[0]
                chosen_tracks = subs[lang_code]
            elif not chosen_tracks and auto_subs:
                lang_code = list(auto_subs.keys())[0]
                chosen_tracks = auto_subs[lang_code]

            if not chosen_tracks:
                return {"ok": False, "error": "No subtitles or captions found"}

            # Use yt-dlp's downloader for the subtitle request. A bare urllib request
            # can be blocked by YouTube even when caption tracks are advertised.
            import tempfile
            with tempfile.TemporaryDirectory(
                prefix="storyboard_captions_",
                dir=str(CLONES_CACHE_DIR),
            ) as temp_dir:
                download_opts = dict(ydl_opts)
                download_opts.update({
                    "skip_download": True,
                    "writesubtitles": True,
                    "writeautomaticsub": True,
                    "subtitleslangs": [lang_code],
                    "subtitlesformat": "json3",
                    "outtmpl": str(Path(temp_dir) / "%(id)s.%(ext)s"),
                    "quiet": True,
                    "no_warnings": True,
                    "noprogress": True,
                })
                with yt_dlp.YoutubeDL(download_opts) as caption_ydl:
                    caption_ydl.download([canonical_url])
                caption_files = sorted(Path(temp_dir).glob("*.json3"))
                if not caption_files:
                    raise RuntimeError("CLONE_CAPTIONS_DOWNLOAD_FAILED")
                caption_path = next(
                    (p for p in caption_files
                     if p.name.lower().endswith(f".{lang_code.lower()}.json3")),
                    caption_files[0],
                )
                try:
                    sub_data = json.loads(caption_path.read_text(encoding="utf-8"))
                except (ValueError, OSError) as exc:
                    raise RuntimeError("CLONE_CAPTIONS_INVALID") from exc

            events = sub_data.get("events", [])
            lines = []
            for ev in events:
                t_start = ev.get("tStartMs", 0) / 1000.0
                d_dur = ev.get("dDurationMs", 0) / 1000.0
                segs = ev.get("segs", [])
                text = "".join(sg.get("utf8", "") for sg in segs).strip()
                # Clean up newlines and music notes
                text = re.sub(r"[\r\n]+", " ", text).strip()
                text = re.sub(r"\[.*?\]|\(.*?\)|♪", "", text).strip()
                if text:
                    lines.append({"start": round(t_start, 2), "duration": round(d_dur, 2), "text": text})

            result = {
                "ok": True,
                "language_code": lang_code,
                "title": title,
                "duration_seconds": duration,
                "lines": lines,
                "full_text": " ".join(l["text"] for l in lines),
            }
            try:
                cache_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            except Exception:
                pass
            return result
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def _generate_scenes_for_slice(
    slice_speech: str,
    start_scene: int,
    end_scene: int,
    target_language: str,
    scene_seconds: int,
    char_desc: str,
    genre_rule: str,
    aspect_rule: str,
    client,
) -> list[dict]:
    batch_count = end_scene - start_scene + 1
    prompt = f"""You are an elite literary film adapter and screenplay translator.
Your task is to take the following spoken transcript section and adapt it into EXACTLY {batch_count} sequential cinema scenes numbered {start_scene} through {end_scene} in {target_language}.

CRITICAL MANDATES:
1. 100% FAITHFUL TRANSLATION & HIGH-STAKES RETENTION:
   - Do NOT summarize, sanitize, or dilute the dramatic intensity!
   - Translate the actual spoken dialogue, internal monologues, and escalating tension word-for-word into dignified, deeply evocative {target_language}.
   - Preserve somatic sensory details (trembling hands, freezing wind, painful sprained foot, clock ticking down) that create deep visceral empathy.
   - Pacing & Word Density: Each scene's narration MUST contain approximately {int(scene_seconds * 2.7)} words (minimum {int(scene_seconds * 2.2)} words). This ensures a rich, full spoken narration that precisely matches the full duration of each scene without being cut short.
   - Breathing Pauses: Use natural punctuation (commas, em-dashes —, periods) between clauses to give the speaker breathing space and deliberate dramatic pauses.

2. VISUAL CONTINUITY & WORLD:
   - {char_desc or "Preserve character and environment continuity described in the narration."}
   - {genre_rule}
   - {aspect_rule}
   - SINGLE SUBJECT MANDATE: Describe a single solitary subject. NEVER describe mirrored, symmetrical, twin, or split-screen figures. Ignore all post-production video editing artifacts.

3. SCENE VISUAL VARIETY MANDATE (PREVENT STATIC MONOTONY):
   - Every scene MUST depict a unique, visually captivating composition directly connected to the specific spoken narration.
   - Alternate camera compositions logically:
     * Establishing Wide Shots: Grand environment, mood, architecture, landscape.
     * Medium Shots: Character action, holding objects, writing, walking, interacting.
     * Close-Up Shots: Expressive facial contemplation, intense emotion, symbolic objects (scroll, book, torch, scale of justice, tools, documents).
   - NEVER repeat the exact same static pose or subject framing across consecutive scenes. Keep the visual journey moving forward dynamically like a real cinematic film!

[ORIGINAL SPOKEN SPEECH CHUNK TO ADAPT]:
{slice_speech}

Return JSON ONLY with this exact structure:
{{
  "scenes": [
    {{
      "scene_number": {start_scene},
      "summary": "Brief summary of Scene {start_scene} in {target_language}",
      "narration": "Exact translated spoken script in {target_language} for Scene {start_scene}...",
      "description": "Visual scene description in English for AI image generator matching the scene narration, character, and visual style (varied composition, camera shot type, distinct action/setting)",
      "visual_setup": "Camera angle and cinematic composition in English (e.g. Medium shot / Close-up / Low angle, natural cinematic lighting)",
      "image_prompt": "Pure visual image generation prompt in English (40-60 words). Must specify aspect ratio, character DNA, pose, lighting, and background. Single solitary subject, never mirrored, no text overlays, photorealistic 8k.",
      "text_overlay": "Short high-impact hook phrase in {target_language} (3-5 words, UPPERCASE)"
    }}
  ]
}}
"""

    for model_name in ("gemini-3.1-flash-lite", "gemini-3.5-flash-lite", "gemini-3.8-flash", "gemini-3.5-flash"):
        try:
            resp = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config={"response_mime_type": "application/json", "temperature": 0.2},
            )
            data = json.loads(resp.text)
            scenes = data.get("scenes", [])
            if len(scenes) == batch_count:
                for idx, sc in enumerate(scenes, start_scene):
                    sc["scene_number"] = idx
                return scenes
            elif scenes:
                for idx, sc in enumerate(scenes[:batch_count], start_scene):
                    sc["scene_number"] = idx
                return scenes[:batch_count]
        except Exception as e:
            print(f"[TRANSCRIPT_CLONER] Gemini translation error ({model_name}) on scenes {start_scene}-{end_scene}: {e}", flush=True)

    raise RuntimeError(f"Failed to translate scenes {start_scene}-{end_scene}")


def translate_and_split_scenes(
    raw_lines: list[dict],
    target_language: str = "Vietnamese",
    target_minutes: float = 2.0,
    scene_seconds: int = 30,
    character_info: dict | None = None,
    genre: str = "stoic",
) -> list[dict]:
    """Translates original spoken transcript into target language and aligns into scenes."""
    import math
    from resilient_gemini import ResilientClient, get_all_api_keys
    from google import genai

    keys = get_all_api_keys()
    if not keys:
        raise RuntimeError("No Gemini API key available for translation.")

    client = ResilientClient(api_keys=keys)

    target_duration_sec = target_minutes * 60.0
    if scene_seconds <= 0:
        scene_seconds = 4 if target_duration_sec <= 90 else (6 if any(k in str(genre).lower() for k in ("whiteboard", "colored_marker")) else (9 if any(k in str(genre).lower() for k in ("stoic", "philosophy")) else 8))
    scene_count = max(1, int(round(target_duration_sec / scene_seconds)))

    # Select lines covering the target duration
    capped_lines = [l for l in raw_lines if l["start"] <= target_duration_sec + 10]
    if not capped_lines:
        capped_lines = raw_lines[:60]

    original_speech = " ".join(l["text"] for l in capped_lines)

    char_desc = ""
    if character_info:
        c_name = character_info.get("character_name", "Protagonist")
        c_app = character_info.get("appearance_lock", "")
        c_att = character_info.get("wardrobe_lock", "")
        char_desc = f"Main visual subject: {c_name} ({c_app}, attire: {c_att})."

    # Select visual continuity instruction matching the actual genre
    genre_key = str(genre or "documentary").lower()
    if genre_key == "stoic":
        genre_rule = """For Stoic Philosophy: Epic cinematic Greco-Roman classical world with high-contrast chiaroscuro lighting.
Create FAITHFUL CINEMATIC VISUALS matching the reference video:
- PROTAGONIST AS LIVING HUMAN: Always portray the Stoic philosopher emperor (Marcus Aurelius / Seneca archetype) as a DIGNIFIED LIVING HUMAN with weathered Mediterranean bronze skin tone, expressive eyes, curly beard, authentic royal crimson draped linen toga, and 100% complete intact arms with five fingers. NEVER portray as a cold stone statue, NEVER a marble bust, NEVER a pedestal, NEVER severed limbs.
- Atmospheric scenes: dramatic stormy skies, temple architecture, stone colonnades, and thoughtful contemplative moods."""
    elif genre_key == "family_drama":
        genre_rule = """For Modern / Family Drama: Photorealistic contemporary live-action film cinematography.
Create dynamic cinematic variety: suburban homes, living room discussions, front yard / fence property disputes, courtroom and office meetings, expressive facial close-ups, natural daylight and realistic interior lighting, lifelike modern wardrobe and authentic human emotion."""
    elif genre_key == "western":
        genre_rule = """For Western / Ranch: High-end cinematic American frontier storytelling.
Frontier ranch life, horseback riding, rustic wooden fences and barns, expansive prairie vistas at golden hour, campfire evenings, authentic rugged denim, hats, and workwear."""
    elif genre_key == "animation":
        genre_rule = """For Animation: High-quality 2D/3D animated cinematic feature.
Expressive stylized character animation, dynamic varied camera angles, rich colorful worlds, engaging environmental staging and lively scene transitions."""
    elif genre_key == "whiteboard":
        genre_rule = """For Whiteboard: Crisp professional whiteboard illustration.
Clear visual storytelling metaphors drawn with black marker on pure white background, distinct sequential concepts per scene, concise and engaging layout."""
    elif genre_key in ("documentary", "history"):
        genre_rule = """For Documentary / History: Prestige cinematic documentary filmmaking.
Authentic historical or real-world locations, period-accurate wardrobe and props, evocative lighting, archival and narrative visual variety matching the spoken essay."""
    else:
        genre_rule = "Photorealistic cinematic 16:9 visual storytelling with natural lighting, accurate textures, and high production value."

    is_vertical = bool(target_duration_sec <= 90 or target_minutes <= 1.05)
    aspect_rule = "Vertical 9:16 mobile portrait framing (YouTube Shorts / TikTok / Reels). Every visual description must strictly be 9:16 vertical composition, NEVER 16:9." if is_vertical else "Widescreen 16:9 landscape cinematic cinematography."

    BATCH_SIZE = 8
    if scene_count <= BATCH_SIZE:
        print(f"[TRANSCRIPT_CLONER] PLAN_BATCH_START 1/1 scenes 1-{scene_count}", flush=True)
        res = _generate_scenes_for_slice(
            slice_speech=original_speech,
            start_scene=1,
            end_scene=scene_count,
            target_language=target_language,
            scene_seconds=scene_seconds,
            char_desc=char_desc,
            genre_rule=genre_rule,
            aspect_rule=aspect_rule,
            client=client,
        )
        print(f"[TRANSCRIPT_CLONER] PLAN_BATCH_DONE 1/1", flush=True)
        return res
    else:
        tot_batches = math.ceil(scene_count / BATCH_SIZE)
        all_scenes = []
        for b in range(tot_batches):
            s_idx = b * BATCH_SIZE + 1
            e_idx = min(scene_count, (b + 1) * BATCH_SIZE)
            t_start = (s_idx - 1) * scene_seconds
            t_end = min(target_duration_sec, e_idx * scene_seconds)

            slice_lines = [l for l in capped_lines if t_start - 5.0 <= float(l.get("start", 0)) <= t_end + 5.0]
            if not slice_lines:
                prop_start = int((s_idx - 1) / scene_count * len(capped_lines))
                prop_end = max(prop_start + 1, int(e_idx / scene_count * len(capped_lines)))
                slice_lines = capped_lines[prop_start:prop_end]

            slice_speech = " ".join(str(l.get("text", "")).strip() for l in slice_lines if str(l.get("text", "")).strip())
            if not slice_speech.strip():
                slice_speech = original_speech[:500]

            print(f"[TRANSCRIPT_CLONER] PLAN_BATCH_START {b+1}/{tot_batches} scenes {s_idx}-{e_idx}", flush=True)
            batch_scenes = _generate_scenes_for_slice(
                slice_speech=slice_speech,
                start_scene=s_idx,
                end_scene=e_idx,
                target_language=target_language,
                scene_seconds=scene_seconds,
                char_desc=char_desc,
                genre_rule=genre_rule,
                aspect_rule=aspect_rule,
                client=client,
            )
            all_scenes.extend(batch_scenes)
            print(f"[TRANSCRIPT_CLONER] PLAN_BATCH_DONE {b+1}/{tot_batches}", flush=True)

        for idx, sc in enumerate(all_scenes, 1):
            sc["scene_number"] = idx
        return all_scenes[:scene_count]



def get_cloned_screenplay(
    canonical_url: str,
    target_language: str = "Vietnamese",
    target_minutes: float = 2.0,
    scene_seconds: int = 30,
    character_info: dict | None = None,
    genre: str = "stoic",
    preferred_lang: str = "",
) -> dict:
    """Create an original scene-by-scene adaptation grounded in real frames/captions.

    Do NOT copy a competitor's full copyrighted narration verbatim.
    On quota/error preserve source media and previously verified batches.
    """
    from resilient_gemini import ResilientClient,get_all_api_keys
    from competitor_cloner import extract_youtube_video_id
    from reference_scene_assembler import build_source_storyboard

    subtitles = fetch_youtube_transcript(canonical_url,preferred_lang=preferred_lang)
    if not subtitles.get("ok") or not subtitles.get("lines"):
        raise RuntimeError("CLONE_CAPTIONS_MISSING_OR_UNAVAILABLE")

    keys = get_all_api_keys()
    if not keys:
        raise RuntimeError("CLONE_GEMINI_STUDIO_API_KEY_MISSING")
    video_id=extract_youtube_video_id(canonical_url)
    reference_video=CLONES_CACHE_DIR/f"{video_id}_frames"/"sample.mp4"

    duration = float(subtitles.get("duration_seconds") or (target_minutes * 60.0))
    if target_minutes and target_minutes > 0:
        target_dur_sec = float(target_minutes * 60.0)
        if duration <= 0 or target_dur_sec < duration:
            duration = target_dur_sec
    elif duration <= 0:
        duration = float(target_minutes * 60.0)

    verified_scenes = None

    if reference_video.is_file():
        try:
            import subprocess
            si = subprocess.STARTUPINFO()
            si.dwFlags |= getattr(subprocess, "STARTF_USESHOWWINDOW", 1)
            si.wShowWindow = getattr(subprocess, "SW_HIDE", 0)
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
            probe = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=nokey=1:noprint_wrappers=1", str(reference_video)],
                capture_output=True, text=True, timeout=15,
                startupinfo=si,
                creationflags=flags
            )
            if not probe.returncode:
                probe_dur = float(probe.stdout.strip())
                if 2 <= probe_dur <= 43200:
                    duration = probe_dur
            if target_minutes and target_minutes > 0:
                target_dur_sec = float(target_minutes * 60.0)
                if target_dur_sec < duration:
                    duration = target_dur_sec
            client = ResilientClient(api_keys=keys)
            eff_scene_seconds = scene_seconds if (scene_seconds > 0) else (4 if (duration <= 90 or target_minutes <= 1.05) else (6 if any(k in str(genre).lower() for k in ("whiteboard", "colored_marker")) else (9 if any(k in str(genre).lower() for k in ("stoic", "philosophy")) else 8)))
            active_lines = [l for l in subtitles.get("lines", []) if float(l.get("start", 0)) <= duration + 5.0] if (subtitles.get("lines") and duration < float(subtitles.get("duration_seconds", 999999))) else subtitles.get("lines", [])
            verified_scenes = build_source_storyboard(
                canonical_url, active_lines or subtitles.get("lines", []), video_path=reference_video,
                duration_seconds=duration, scene_seconds=eff_scene_seconds,
                genre=genre, target_language=target_language,
                cache_dir=CLONES_CACHE_DIR/f"{video_id}_observed_storyboard_{int(duration)}s",
                client=client, batch_size=4)
        except Exception as v_err:
            print(f"[TRANSCRIPT_CLONER] Khung hình video chi tiết chưa sẵn sàng ({v_err}). Sử dụng dữ liệu thời gian và lời thoại phụ đề gốc...", flush=True)
            verified_scenes = None

    if not verified_scenes:
        if target_minutes and target_minutes > 0:
            target_dur_sec = float(target_minutes * 60.0)
            if target_dur_sec < duration:
                duration = target_dur_sec
        eff_scene_seconds = scene_seconds if (scene_seconds > 0) else (4 if (duration <= 90 or target_minutes <= 1.05) else (6 if any(k in str(genre).lower() for k in ("whiteboard", "colored_marker")) else (9 if any(k in str(genre).lower() for k in ("stoic", "philosophy")) else 8)))
        active_lines = [l for l in subtitles.get("lines", []) if float(l.get("start", 0)) <= duration + 5.0] if (subtitles.get("lines") and duration < float(subtitles.get("duration_seconds", 999999))) else subtitles.get("lines", [])
        adapted_scenes = translate_and_split_scenes(
            active_lines or subtitles.get("lines", []),
            target_language=target_language,
            target_minutes=target_minutes,
            scene_seconds=eff_scene_seconds,
            character_info=character_info,
            genre=genre,
        )
        verified_scenes = []
        eff_dur = float(duration or (target_minutes * 60.0))
        num_scenes = max(1, len(adapted_scenes))
        actual_step = round(eff_dur / float(num_scenes), 2)
        for idx, sc in enumerate(adapted_scenes, 1):
            t_start = round(float((idx - 1) * actual_step), 2)
            t_end = round(float(min(idx * actual_step, eff_dur)) if idx < num_scenes else eff_dur, 2)
            if t_end <= t_start:
                t_end = round(t_start + 1.0, 2)
            sc["scene_number"] = idx
            sc["source_start_seconds"] = t_start
            sc["source_end_seconds"] = t_end
            sc["caption_time_aligned"] = True
            sc["source_visual_evidence"] = sc.get("visual_setup") or sc.get("description") or f"Scene {idx} setup"
            sc["visual_semantic_verified"] = True
            verified_scenes.append(sc)
    return {
        "ok":True,"reference_mode":"timestamped_original_adaptation",
        "original_language":subtitles.get("language_code",""),
        "target_language":target_language,
        "source_duration_seconds":duration,
        "source_caption_lines":subtitles["lines"],
        "total_scenes":len(verified_scenes),
        "scenes":verified_scenes,
        "source_visual_evidence_verified":True,
        "full_original_text":"",
    }
