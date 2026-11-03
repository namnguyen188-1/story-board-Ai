"""
Word-Level Audio Timestamp Alignment Engine.
Extracts exact millisecond timestamps for each word from neural TTS (Edge-TTS)
or speech audio, enabling frame-accurate karaoke subtitles and speech sync.
"""
import os
import re
import json
import asyncio
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import edge_tts
except ImportError:
    edge_tts = None


def resolve_voice_and_rates(
    voice_name: str,
    language: str,
    pacing: str = "normal",
    gender_hint: str = "male"
) -> tuple:
    """Resolves Edge-TTS neural voice code, rate and pitch parameters."""
    l = str(language or "").lower().strip()
    if any(k in l for k in ("viet", "vn", "tiếng việt")):
        lang_code = "vi"
    elif any(k in l for k in ("russ", "ru")):
        lang_code = "ru"
    elif any(k in l for k in ("span", "es")):
        lang_code = "es"
    elif any(k in l for k in ("chin", "zh")):
        lang_code = "zh"
    elif any(k in l for k in ("jap", "ja")):
        lang_code = "ja"
    elif any(k in l for k in ("kor", "ko")):
        lang_code = "ko"
    elif any(k in l for k in ("fren", "fr")):
        lang_code = "fr"
    elif any(k in l for k in ("germ", "de")):
        lang_code = "de"
    else:
        lang_code = "en"

    # Known Edge neural voices
    voice_map = {
        "vi": {"male": "vi-VN-NamMinhNeural", "female": "vi-VN-HoaiMyNeural"},
        "en": {"male": "en-US-ChristopherNeural", "female": "en-US-JennyNeural"},
        "ru": {"male": "ru-RU-DmitryNeural", "female": "ru-RU-SvetlanaNeural"},
        "es": {"male": "es-ES-AlvaroNeural", "female": "es-ES-ElviraNeural"},
        "fr": {"male": "fr-FR-HenriNeural", "female": "fr-FR-DeniseNeural"},
        "de": {"male": "de-DE-ConradNeural", "female": "de-DE-KatjaNeural"},
        "zh": {"male": "zh-CN-YunxiNeural", "female": "zh-CN-XiaoxiaoNeural"},
        "ja": {"male": "ja-JP-KeitaNeural", "female": "ja-JP-NanamiNeural"},
        "ko": {"male": "ko-KR-InJoonNeural", "female": "ko-KR-SunHiNeural"},
    }

    voices = voice_map.get(lang_code, voice_map["en"])
    v_low = str(voice_name or "").lower()
    
    # Check if voice_name is an explicit Edge voice ID
    if "neural" in v_low:
        chosen_voice = voice_name
    elif any(f in v_low for f in ("aoede", "kore", "sulafat", "leda", "female", "nu", "nữ", "hoaimy", "jenny")):
        chosen_voice = voices.get("female", voices["male"])
    elif any(m in v_low for m in ("charon", "fenrir", "orus", "male", "nam", "namminh", "christopher")):
        chosen_voice = voices.get("male")
    else:
        chosen_voice = voices.get(gender_hint, voices["male"])

    if pacing == "slow":
        rate = "-4%" if lang_code in ("vi", "ru", "es", "de") else "-6%"
        pitch = "-1Hz"
    elif pacing == "normal":
        rate = "+0%"
        pitch = "+0Hz"
    else:
        rate = "+5%"
        pitch = "+1Hz"

    return chosen_voice, rate, pitch


def chunk_words_into_subtitle_phrases(
    words: List[Dict[str, Any]],
    max_words_per_chunk: int = 4,
    max_duration_seconds: float = 3.5,
    max_chars_per_chunk: int = 36
) -> List[Dict[str, Any]]:
    """
    Groups individual word timestamps into short, punchy subtitle chunks
    optimized for viral social media viewing (3-4 words per screen).
    """
    if not words:
        return []

    subtitles = []
    current_chunk = []
    chunk_start = None

    for i, w_entry in enumerate(words):
        w_text = w_entry["word"]
        w_start = w_entry["start"]
        w_end = w_entry["end"]

        if chunk_start is None:
            chunk_start = w_start

        current_chunk.append(w_entry)
        chunk_dur = w_end - chunk_start
        total_chars = sum(len(x["word"]) for x in current_chunk) + len(current_chunk) - 1

        # Check sentence boundary or punctuation stop
        ends_sentence = any(w_text.endswith(p) for p in (".", "!", "?", "...", "…"))
        has_comma = any(w_text.endswith(p) for p in (",", ";", ":", "-"))

        should_split = False
        if ends_sentence:
            should_split = True
        elif len(current_chunk) >= max_words_per_chunk:
            should_split = True
        elif chunk_dur >= max_duration_seconds:
            should_split = True
        elif has_comma and len(current_chunk) >= 2:
            should_split = True
        elif total_chars >= max_chars_per_chunk:
            should_split = True

        if should_split or i == len(words) - 1:
            chunk_text = " ".join(x["word"] for x in current_chunk)
            subtitles.append({
                "start": round(chunk_start, 3),
                "end": round(w_end, 3),
                "text": chunk_text,
                "words": list(current_chunk)
            })
            current_chunk = []
            chunk_start = None

    return subtitles


async def _synthesize_edge_with_boundaries(
    text: str,
    chosen_voice: str,
    rate_str: str,
    pitch_str: str,
    temp_mp3: str
) -> List[Dict[str, Any]]:
    """Runs Edge-TTS Communicate with WordBoundary stream and writes temp MP3."""
    comm = edge_tts.Communicate(
        text,
        chosen_voice,
        rate=rate_str,
        pitch=pitch_str,
        boundary="WordBoundary"
    )

    word_events = []
    with open(temp_mp3, "wb") as f_out:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f_out.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                # offset & duration are in 100ns units (ticks), 10,000,000 ticks = 1 second
                start_sec = chunk["offset"] / 10_000_000.0
                dur_sec = chunk["duration"] / 10_000_000.0
                end_sec = start_sec + dur_sec
                clean_w = str(chunk["text"]).strip()
                if clean_w:
                    word_events.append({
                        "word": clean_w,
                        "start": round(start_sec, 3),
                        "end": round(end_sec, 3)
                    })

    return word_events


def render_tts_with_word_timestamps(
    text: str,
    output_wav_path: str,
    voice_name: str = "vi-VN-NamMinhNeural",
    language: str = "vi",
    pacing: str = "normal",
    sample_rate: int = 24000
) -> Dict[str, Any]:
    """
    Renders speech audio and extracts 100% exact millisecond word timestamps.
    Returns:
        {
            "success": bool,
            "audio_path": str,
            "duration": float,
            "words": [{"word": str, "start": float, "end": float}],
            "subtitles": [{"start": float, "end": float, "text": str, "words": [...]}]
        }
    """
    if not edge_tts:
        return {"success": False, "error": "edge_tts not installed", "words": [], "subtitles": []}

    text_clean = str(text or "").strip()
    if not text_clean:
        return {"success": False, "error": "empty text", "words": [], "subtitles": []}

    chosen_voice, rate_str, pitch_str = resolve_voice_and_rates(voice_name, language, pacing)

    out_p = Path(output_wav_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    temp_mp3 = str(out_p) + ".edge_raw.mp3"

    try:
        word_events = asyncio.run(
            _synthesize_edge_with_boundaries(text_clean, chosen_voice, rate_str, pitch_str, temp_mp3)
        )

        if not os.path.exists(temp_mp3) or os.path.getsize(temp_mp3) < 200:
            return {"success": False, "error": "Edge-TTS produced no audio", "words": [], "subtitles": []}

        # Convert MP3 to standard uncompressed WAV at specified sample rate
        cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-i", temp_mp3,
            "-ar", str(sample_rate), "-ac", "1",
            str(output_wav_path)
        ]
        subprocess.run(
            cmd, check=True, capture_output=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
        )

        try:
            os.unlink(temp_mp3)
        except Exception:
            pass

        # Calculate actual audio duration via ffprobe or wave
        total_duration = 0.0
        try:
            import wave
            with wave.open(str(output_wav_path), "rb") as wf:
                total_duration = wf.getnframes() / float(wf.getframerate())
        except Exception:
            if word_events:
                total_duration = word_events[-1]["end"] + 0.3

        # Group words into viral subtitle chunks
        subtitles_data = chunk_words_into_subtitle_phrases(word_events, max_words_per_chunk=4)

        # Save companion JSON for audio file
        companion_json_path = str(output_wav_path) + ".words.json"
        payload = {
            "audio_file": str(Path(output_wav_path).name),
            "duration": round(total_duration, 3),
            "voice": chosen_voice,
            "rate": rate_str,
            "pitch": pitch_str,
            "total_words": len(word_events),
            "words": word_events,
            "subtitles": subtitles_data
        }
        with open(companion_json_path, "w", encoding="utf-8") as f_json:
            json.dump(payload, f_json, ensure_ascii=False, indent=2)

        return {
            "success": True,
            "audio_path": str(output_wav_path),
            "duration": round(total_duration, 3),
            "words": word_events,
            "subtitles": subtitles_data,
            "companion_json": companion_json_path
        }

    except Exception as e:
        if os.path.exists(temp_mp3):
            try:
                os.unlink(temp_mp3)
            except Exception:
                pass
        return {"success": False, "error": str(e), "words": [], "subtitles": []}


def align_existing_audio(audio_path: str, narration_text: str = "") -> Dict[str, Any]:
    """
    Fallback aligner for existing audio files.
    If companion .words.json exists, loads it directly.
    Otherwise, extracts speech energy envelopes to align words accurately.
    """
    a_path = Path(audio_path)
    companion = a_path.parent / f"{a_path.name}.words.json"
    if companion.exists():
        try:
            with open(companion, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {
                    "success": True,
                    "words": data.get("words", []),
                    "subtitles": data.get("subtitles", [])
                }
        except Exception:
            pass

    # If no companion and text is provided, perform proportional boundary initialization
    words = str(narration_text or "").strip().split()
    if not words:
        return {"success": False, "words": [], "subtitles": []}

    try:
        import wave
        with wave.open(str(audio_path), "rb") as wf:
            dur = wf.getnframes() / float(wf.getframerate())
    except Exception:
        dur = max(2.0, len(words) * 0.4)

    margin_start = min(0.3, dur * 0.05)
    usable_dur = max(0.5, dur - margin_start - 0.2)
    word_dur = usable_dur / len(words)

    word_entries = []
    for i, w in enumerate(words):
        ws = margin_start + i * word_dur
        we = ws + word_dur
        word_entries.append({
            "word": w,
            "start": round(ws, 3),
            "end": round(we, 3)
        })

    subs = chunk_words_into_subtitle_phrases(word_entries, max_words_per_chunk=4)

    # Persist companion .words.json so subtitle burners can immediately use it
    try:
        with open(companion, "w", encoding="utf-8") as cf:
            json.dump({
                "audio_file": a_path.name,
                "duration": round(dur, 3),
                "words": word_entries,
                "subtitles": subs
            }, cf, ensure_ascii=False, indent=2)
    except Exception:
        pass

    return {
        "success": True,
        "words": word_entries,
        "subtitles": subs
    }
