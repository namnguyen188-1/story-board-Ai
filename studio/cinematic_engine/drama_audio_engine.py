"""Cinematic Drama Engine - Multi-Voice Dialogue Audio Engine (Phase 2).
Synthesizes individual character dialogue beats with distinct persona voices and tones,
inserts natural conversational pauses, concatenates into a master dialogue track,
and generates time-accurate dialogue timeline and subtitles.
"""
from __future__ import annotations

import os
import sys
import re
import wave
import json
import uuid
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple


def clean_dialogue_text(text: str) -> str:
    """Strips character tags, speaker prefixes, and bracketed notes to keep pure spoken dialogue."""
    if not text:
        return ""
    cleaned = text.strip()
    cleaned = re.sub(r"^\[.*?\]\s*", "", cleaned)
    cleaned = re.sub(r"^\(.*?\)\s*", "", cleaned)
    cleaned = re.sub(r"^[A-Za-z0-9_\s\u00C0-\u1EF9\.\-]{2,35}(?:\(.*?\))?:\s*", "", cleaned)
    return cleaned.strip() or text.strip()

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

from .drama_schema import DialogueBeat, SceneDrama, EpisodeDramaPlan, CharacterProfile


# Tone-to-style prompts for Gemini Studio TTS and Edge-TTS emotional inflection
TONE_STYLE_PROMPTS = {
    "whisper": "[speaking style: whisper, very low volume, conspiratorial, intimate, slow tempo]",
    "defiant": "[speaking style: defiant, fierce, unwavering determination, sharp projection, confident]",
    "menacing": "[speaking style: menacing, cold, cynical, calculating, low pitch, sinister undertone]",
    "trembling": "[speaking style: trembling with rage and heartbreak, emotional, breathless, intense]",
    "urgent": "[speaking style: urgent, rapid, heightened tension, breathless, alert]",
    "commanding": "[speaking style: commanding, authoritative, stern, deep and resonant projection]",
    "cold": "[speaking style: cold, emotionless, detached, icy, calculated]",
    "sarcastic": "[speaking style: sarcastic, mocking, dry, condescending chuckle undertone]",
    "grief": "[speaking style: grieving, cracked voice, choked with tears, slow, painful]",
    "warm": "[speaking style: warm, comforting, gentle, smiling, friendly]",
    "natural": "[speaking style: natural conversational dialogue, authentic human nuance]",
}

EDGE_PITCH_OFFSETS = {
    "whisper": ("-10%", "-4Hz"),
    "defiant": ("+5%", "+2Hz"),
    "menacing": ("-8%", "-3Hz"),
    "trembling": ("-5%", "+1Hz"),
    "urgent": ("+10%", "+2Hz"),
    "commanding": ("-5%", "-2Hz"),
    "cold": ("-6%", "-2Hz"),
    "sarcastic": ("+0%", "+1Hz"),
    "grief": ("-12%", "-3Hz"),
    "warm": ("-4%", "-1Hz"),
    "natural": ("-5%", "-1Hz"),
}


def get_wav_duration(wav_path: str | Path) -> float:
    """Returns exact duration of a WAV file in seconds using wave or ffprobe."""
    wav_str = str(wav_path)
    if not os.path.exists(wav_str) or os.path.getsize(wav_str) < 100:
        return 0.0

    try:
        with wave.open(wav_str, "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            if rate > 0:
                return float(frames) / float(rate)
    except Exception:
        pass

    # Fallback to ffprobe
    try:
        cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_format", wav_str
        ]
        res = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
        )
        data = json.loads(res.stdout)
        return float(data["format"]["duration"])
    except Exception:
        return 0.0


def create_silence_wav(
    duration: float,
    output_path: str | Path,
    sample_rate: int = 24000,
    channels: int = 1,
    sampwidth: int = 2
) -> str:
    """Generates a pure PCM silence WAV file of exact duration."""
    out_str = str(output_path)
    os.makedirs(os.path.dirname(out_str), exist_ok=True)
    num_frames = int(sample_rate * max(0.01, duration))
    silence_bytes = b"\x00" * (num_frames * channels * sampwidth)

    with wave.open(out_str, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(sample_rate)
        wf.writeframes(silence_bytes)

    return out_str


def normalize_wav_format(
    input_path: str | Path,
    output_path: str | Path,
    sample_rate: int = 24000,
    channels: int = 1
) -> bool:
    """Ensures WAV file matches exact target sample rate, mono channel, 16-bit PCM."""
    inp = str(input_path)
    out = str(output_path)
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", inp,
        "-ar", str(sample_rate),
        "-ac", str(channels),
        "-c:a", "pcm_s16le",
        out
    ]
    try:
        subprocess.run(
            cmd, capture_output=True, check=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
        )
        return os.path.exists(out) and os.path.getsize(out) > 500
    except Exception as e:
        print(f"[AUDIO_NORM] Error normalizing {inp}: {e}", flush=True)
        return False


def format_srt_time(seconds: float) -> str:
    """Converts seconds float to SRT timestamp 00:00:00,000."""
    millis = int(round((seconds % 1) * 1000))
    if millis >= 1000:
        millis = 999
    total_seconds = int(seconds)
    secs = total_seconds % 60
    total_mins = total_seconds // 60
    mins = total_mins % 60
    hours = total_mins // 60
    return f"{hours:02d}:{mins:02d}:{secs:02d},{millis:03d}"


# HARD BAN: Edge-TTS is strictly forbidden across the entire cinematic pipeline
ENABLE_EDGE_TTS = False

class DramaAudioEngine:
    """Multi-Voice Character Dialogue Audio Engine for Cinematic Drama."""

    def __init__(self, target_sample_rate: int = 24000):
        self.target_sample_rate = target_sample_rate

    def _synthesize_vietnamese_beat(
        self,
        text: str,
        speaker: str,
        voice_id: str,
        gender: str,
        tone: str,
        output_path: Path
    ) -> bool:
        """STRICT BAN: Edge-TTS is completely prohibited per user directive. Returns False."""
        return False
        import asyncio
        try:
            import edge_tts
        except ImportError:
            return False

        is_male = gender.lower() == "male" or any(k in voice_id.lower() for k in ("charon", "fenrir", "orus", "alnilam", "iapetus", "gacrux", "nam"))
        chosen_voice = "vi-VN-NamMinhNeural" if is_male else "vi-VN-HoaiMyNeural"

        # Persona base modulation - Cinematic Standard: deliberate, emotional, steady pacing (-6% to -10%)
        v_low = voice_id.lower()
        base_rate = -7
        base_pitch = 0  # in Hz

        if is_male:
            if "fenrir" in v_low:  # Young vigorous male protagonist (Hoàng Minh, Minh Tuyên)
                base_rate = -5
                base_pitch = 18  # +18Hz noticeable youthful brightness
            elif "charon" in v_low or "narrator" in speaker.lower():  # Mature deep narrator
                base_rate = -11
                base_pitch = -25  # -25Hz deep resonance
            elif "orus" in v_low or "gacrux" in v_low:  # Middle-aged leader / advisor
                base_rate = -8
                base_pitch = -12
            elif "alnilam" in v_low:  # Authoritative patriarch / Emperor / General
                base_rate = -9
                base_pitch = -20
            else:
                base_rate = -7
                base_pitch = 0
        else:
            if "sadachbia" in v_low or "kore" in v_low:  # Sharp / haughty antagonist / firm heroine (Lâm An)
                base_rate = -6
                base_pitch = 15  # +15Hz sharp clarity
            elif "aoede" in v_low or "sulafat" in v_low:  # Soft emotional woman / mother
                base_rate = -10
                base_pitch = -12
            elif "puck" in v_low or "leda" in v_low:  # Youthful vibrant girl
                base_rate = -5
                base_pitch = 26  # +26Hz bright youthful
            else:
                base_rate = -7
                base_pitch = 5

        # Dramatic Tone Modulation
        t_low = tone.lower()
        if t_low in ("defiant", "angry", "menacing"):
            base_rate += 2
            base_pitch += 6
        elif t_low in ("whisper", "secretive"):
            base_rate -= 4
            base_pitch -= 6
        elif t_low in ("commanding", "authoritative"):
            base_rate -= 2
            base_pitch -= 8
        elif t_low in ("sarcastic", "mocking"):
            base_rate += 0
            base_pitch += 4
        elif t_low in ("grief", "choked"):
            base_rate -= 5
            base_pitch -= 10
        elif t_low in ("cold", "calculated"):
            base_rate -= 3
            base_pitch -= 6

        rate_str = f"{'+' if base_rate >= 0 else ''}{base_rate}%"
        pitch_str = f"{'+' if base_pitch >= 0 else ''}{base_pitch}Hz"

        temp_mp3 = str(output_path) + ".temp.mp3"
        word_events = []
        try:
            async def _run():
                nonlocal word_events
                comm = edge_tts.Communicate(text, chosen_voice, rate=rate_str, pitch=pitch_str, boundary="WordBoundary")
                with open(temp_mp3, "wb") as f_mp3:
                    async for chunk in comm.stream():
                        if chunk["type"] == "audio":
                            f_mp3.write(chunk["data"])
                        elif chunk["type"] == "WordBoundary":
                            start_sec = chunk["offset"] / 10_000_000.0
                            dur_sec = chunk["duration"] / 10_000_000.0
                            w_txt = str(chunk["text"]).strip()
                            if w_txt:
                                word_events.append({
                                    "word": w_txt,
                                    "start": round(start_sec, 3),
                                    "end": round(start_sec + dur_sec, 3)
                                })

            asyncio.run(_run())
            if os.path.exists(temp_mp3) and os.path.getsize(temp_mp3) > 500:
                cmd = [
                    "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                    "-i", temp_mp3,
                    "-ar", str(self.target_sample_rate), "-ac", "1",
                    str(output_path)
                ]
                subprocess.run(cmd, check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                try: os.unlink(temp_mp3)
                except Exception: pass
                print(f"[DRAMA_AUDIO_VIETNAMESE] Neural Persona Speech ({speaker} -> {chosen_voice}, {rate_str}, {pitch_str}): {output_path.name}", flush=True)
                try:
                    words_companion = str(output_path) + ".words.json"
                    with open(words_companion, "w", encoding="utf-8") as wf:
                        json.dump({"words": word_events}, wf, ensure_ascii=False, indent=2)
                except Exception:
                    pass
                return True
        except Exception as e:
            print(f"[DRAMA_AUDIO_WARN] Edge-TTS error ({e}), falling back to studio TTS...", flush=True)
            if os.path.exists(temp_mp3):
                try: os.unlink(temp_mp3)
                except Exception: pass
        return False


    def render_dialogue_beat(
        self,
        beat: DialogueBeat | Dict[str, Any],
        language: str,
        output_wav: Path | str,
        cast_map: Optional[Dict[str, CharacterProfile]] = None
    ) -> Optional[Path]:
        """Synthesizes speech for a single DialogueBeat using persona voice and tone."""
        out_path = Path(output_wav)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(beat, dict):
            speaker = beat.get("speaker", "Narrator")
            text = beat.get("text", "")
            tone = beat.get("tone", "natural")
            voice_id = beat.get("voice_id")
            gender = beat.get("gender", "male")
        else:
            speaker = beat.speaker
            text = beat.text
            tone = beat.tone
            voice_id = beat.voice_id
            gender = beat.gender

        # Resolve voice_id from cast_map if available
        if cast_map and speaker in cast_map:
            profile = cast_map[speaker]
            voice_id = profile.voice_id
            gender = profile.gender

        if not voice_id:
            voice_id = "Charon" if gender == "male" else "Aoede"

        # Build style guidance for Gemini Studio TTS
        tone_style = TONE_STYLE_PROMPTS.get(tone.lower(), TONE_STYLE_PROMPTS["natural"])
        voice_prompt_style = f"{tone_style}, character: {speaker}, gender: {gender}, speaking language: {language}"

        print(f"[DRAMA_AUDIO] Synthesizing [{speaker} | Voice: {voice_id} | Tone: {tone}]: {text[:50]}...", flush=True)

        # NOTE: Edge-TTS is strictly banned. All dialogue beats route directly to Gemini Studio Audio.

        # Import TTS tool
        try:
            from engine.tools.tts import generate_tts_audio_tool_fn
        except ImportError:
            from studio.engine.tools.tts import generate_tts_audio_tool_fn

        # Generate audio using the studio resilient TTS engine
        raw_audio_path = generate_tts_audio_tool_fn(
            text=text,
            language=language,
            voice_name=voice_id,
            voice_style=voice_prompt_style
        )

        if not raw_audio_path or not os.path.exists(raw_audio_path) or raw_audio_path.startswith("An error"):
            print(f"[DRAMA_AUDIO_ERR] Failed to generate TTS for beat: {text[:40]}", flush=True)
            return None

        # Normalize and copy to target beat path
        if normalize_wav_format(raw_audio_path, out_path, sample_rate=self.target_sample_rate):
            # Clean up temporary raw path if different
            if os.path.abspath(raw_audio_path) != os.path.abspath(str(out_path)):
                try:
                    os.unlink(raw_audio_path)
                except Exception:
                    pass
            return out_path

        return None

    def assemble_scene_dialogue(
        self,
        scene: SceneDrama | Dict[str, Any],
        language: str,
        scene_dir: Path | str,
        cast_map: Optional[Dict[str, CharacterProfile]] = None
    ) -> Dict[str, Any]:
        """Assembles all dialogue beats of a scene into a master dialogue track with timecodes."""
        s_dir = Path(scene_dir)
        s_dir.mkdir(parents=True, exist_ok=True)
        beats_dir = s_dir / "beats"
        beats_dir.mkdir(parents=True, exist_ok=True)

        scene_num = scene.get("scene_number", 1) if isinstance(scene, dict) else scene.scene_number
        beats_data = scene.get("dialogue_beats", []) if isinstance(scene, dict) else scene.dialogue_beats

        dialogue_timeline: List[Dict[str, Any]] = []
        assembled_wav_segments: List[Path] = []
        silence_files_to_cleanup: List[Path] = []

        cursor = 0.0

        for i, beat_raw in enumerate(beats_data):
            if isinstance(beat_raw, dict):
                beat = DialogueBeat(
                    beat_id=beat_raw.get("beat_id", i + 1),
                    speaker=beat_raw.get("speaker", "Narrator"),
                    text=beat_raw.get("text", ""),
                    tone=beat_raw.get("tone", "natural"),
                    voice_id=beat_raw.get("voice_id", "Charon"),
                    gender=beat_raw.get("gender", "male"),
                    is_narrator=beat_raw.get("is_narrator", False),
                    action=beat_raw.get("action", ""),
                    pause_after_seconds=float(beat_raw.get("pause_after_seconds", 0.35))
                )
            else:
                beat = beat_raw

            safe_speaker = "".join(c if c.isalnum() else "_" for c in beat.speaker).strip("_").lower()
            beat_wav_path = beats_dir / f"beat_{beat.beat_id:03d}_{safe_speaker}.wav"

            # Check if cached or generate new
            rendered_path = self.render_dialogue_beat(beat, language, beat_wav_path, cast_map)
            if not rendered_path or not rendered_path.exists():
                print(f"[DRAMA_AUDIO_WARN] Skipping missing beat audio {beat.beat_id}", flush=True)
                continue

            beat_duration = get_wav_duration(rendered_path)
            if beat_duration <= 0.05:
                print(f"[DRAMA_AUDIO_WARN] Audio duration too short ({beat_duration}s) for beat {beat.beat_id}", flush=True)
                continue

            start_time = cursor
            end_time = cursor + beat_duration

            timeline_entry = {
                "beat_id": beat.beat_id,
                "speaker": beat.speaker,
                "voice_id": beat.voice_id,
                "gender": beat.gender,
                "is_narrator": beat.is_narrator,
                "tone": beat.tone,
                "text": beat.text,
                "action": beat.action,
                "audio_file": str(rendered_path.relative_to(s_dir)),
                "start_time": round(start_time, 3),
                "end_time": round(end_time, 3),
                "duration": round(beat_duration, 3),
            }
            dialogue_timeline.append(timeline_entry)
            assembled_wav_segments.append(rendered_path)

            # Determine pause before next beat
            if i < len(beats_data) - 1:
                next_beat_raw = beats_data[i + 1]
                next_speaker = next_beat_raw.get("speaker", "") if isinstance(next_beat_raw, dict) else next_beat_raw.speaker
                if next_speaker == beat.speaker:
                    # Same speaker continuing speech: tight breath pause (0.18s)
                    pause_sec = 0.18
                else:
                    # Turn changes to another speaker: natural conversational reaction lag
                    pause_sec = max(0.30, beat.pause_after_seconds)
            else:
                # End of scene tail padding
                pause_sec = 0.50

            # Generate silence WAV segment
            silence_path = beats_dir / f"pause_{beat.beat_id:03d}_{pause_sec:.2f}s.wav"
            create_silence_wav(pause_sec, silence_path, sample_rate=self.target_sample_rate)
            assembled_wav_segments.append(silence_path)
            silence_files_to_cleanup.append(silence_path)

            cursor = end_time + pause_sec

        total_scene_duration = round(cursor, 3)

        # Concatenate all segments into dialogue_master.wav using wave library
        master_wav_path = s_dir / "dialogue_master.wav"
        self._concat_wav_files(assembled_wav_segments, master_wav_path)

        # Cleanup intermediate silence files
        for s_file in silence_files_to_cleanup:
            try:
                s_file.unlink()
            except Exception:
                pass

        # Write dialogue_timeline.json
        timeline_payload = {
            "scene_number": scene_num,
            "total_duration": total_scene_duration,
            "master_audio_file": str(master_wav_path.name),
            "num_beats": len(dialogue_timeline),
            "beats": dialogue_timeline
        }
        timeline_json_path = s_dir / "dialogue_timeline.json"
        with open(timeline_json_path, "w", encoding="utf-8") as f:
            json.dump(timeline_payload, f, ensure_ascii=False, indent=2)

        # Generate dialogue_subtitles.srt & subtitles.json
        srt_path = s_dir / "dialogue_subtitles.srt"
        self._generate_srt(dialogue_timeline, srt_path)

        # Generate subtitles.json for Studio UI, Gallery and Styled ASS Renderer
        subtitles_json_path = s_dir / "subtitles.json"
        sub_list = []
        for beat in dialogue_timeline:
            clean_txt = clean_dialogue_text(beat.get("text", ""))
            if clean_txt:
                beat_wav_rel = beat.get("audio_file", "")
                beat_wav_abs = s_dir / beat_wav_rel
                beat_words_json = Path(str(beat_wav_abs) + ".words.json")
                global_words = []
                if beat_words_json.exists():
                    try:
                        with open(beat_words_json, "r", encoding="utf-8") as bf:
                            b_data = json.load(bf)
                            beat_start = float(beat["start_time"])
                            for bw in b_data.get("words", []):
                                global_words.append({
                                    "word": bw["word"],
                                    "start": round(beat_start + float(bw["start"]), 3),
                                    "end": round(beat_start + float(bw["end"]), 3)
                                })
                    except Exception:
                        pass
                sub_entry = {
                    "start": round(float(beat["start_time"]), 3),
                    "end": round(float(beat["end_time"]), 3),
                    "text": clean_txt
                }
                if global_words:
                    sub_entry["words"] = global_words
                sub_list.append(sub_entry)
        with open(subtitles_json_path, "w", encoding="utf-8") as f:
            json.dump({"subtitles": sub_list}, f, ensure_ascii=False, indent=2)

        print(f"[DRAMA_AUDIO_SUCCESS] Scene {scene_num} Master Audio: {master_wav_path} ({total_scene_duration}s, {len(dialogue_timeline)} beats)", flush=True)

        return {
            "scene_number": scene_num,
            "master_audio_path": master_wav_path,
            "timeline_path": timeline_json_path,
            "srt_path": srt_path,
            "subtitles_json_path": subtitles_json_path,
            "total_duration": total_scene_duration,
            "timeline": timeline_payload
        }

    def _concat_wav_files(self, wav_paths: List[Path], output_path: Path):
        """Concatenates multiple standardized WAV files into a single master WAV."""
        if not wav_paths:
            return

        with wave.open(str(wav_paths[0]), "rb") as wf_first:
            params = wf_first.getparams()

        with wave.open(str(output_path), "wb") as wf_out:
            wf_out.setparams(params)
            for p in wav_paths:
                with wave.open(str(p), "rb") as wf_in:
                    wf_out.writeframes(wf_in.readframes(wf_in.getnframes()))

    def _generate_srt(self, timeline: List[Dict[str, Any]], srt_path: Path):
        """Generates a clean SRT subtitle file from dialogue timeline entries."""
        with open(srt_path, "w", encoding="utf-8") as f:
            for idx, entry in enumerate(timeline, start=1):
                clean_txt = clean_dialogue_text(entry.get("text", ""))
                if not clean_txt:
                    continue
                start_ts = format_srt_time(float(entry["start_time"]))
                end_ts = format_srt_time(float(entry["end_time"]))
                speaker = entry.get("speaker", "")
                if speaker and not entry.get("is_narrator", False):
                    line_text = f"[{speaker}]: {clean_txt}"
                else:
                    line_text = clean_txt
                f.write(f"{idx}\n{start_ts} --> {end_ts}\n{line_text}\n\n")
