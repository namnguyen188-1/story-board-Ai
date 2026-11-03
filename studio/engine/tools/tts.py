import uuid
import os
import sys
import time
import subprocess

import json

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from google.genai import types
from config import TTS_MODEL
from studio_voices import validate_voice
from . import utils

MALE_NAMES = {
    "charon", "orus", "fenrir", "alnilam", "iapetus", "algenib", "schedar",
    "gacrux", "rasalgethi", "enceladus", "umbriel", "pulcherrima", "achird",
    "zubenelgenubi", "sadaltager", "namminh", "nam", "male"
}

EDGE_NEURAL_VOICES = {
    "vi": {"male": "vi-VN-NamMinhNeural", "female": "vi-VN-HoaiMyNeural"},
    "ru": {"male": "ru-RU-DmitryNeural", "female": "ru-RU-SvetlanaNeural"},
    "en": {"male": "en-US-ChristopherNeural", "female": "en-US-JennyNeural"},
    "es": {"male": "es-ES-AlvaroNeural", "female": "es-ES-ElviraNeural"},
    "fr": {"male": "fr-FR-HenriNeural", "female": "fr-FR-DeniseNeural"},
    "de": {"male": "de-DE-ConradNeural", "female": "de-DE-KatjaNeural"},
    "zh": {"male": "zh-CN-YunxiNeural", "female": "zh-CN-XiaoxiaoNeural"},
    "ja": {"male": "ja-JP-KeitaNeural", "female": "ja-JP-NanamiNeural"},
    "ko": {"male": "ko-KR-InJoonNeural", "female": "ko-KR-SunHiNeural"},
    "pt": {"male": "pt-BR-AntonioNeural", "female": "pt-BR-FranciscaNeural"},
    "it": {"male": "it-IT-DiegoNeural", "female": "it-IT-ElsaNeural"},
    "th": {"male": "th-TH-NiwatNeural", "female": "th-TH-PremwadeeNeural"},
    "ar": {"male": "ar-SA-HamedNeural", "female": "ar-SA-ZariyahNeural"},
    "hi": {"male": "hi-IN-MadhurNeural", "female": "hi-IN-SwaraNeural"},
    "id": {"male": "id-ID-ArdiNeural", "female": "id-ID-GadisNeural"},
    "nl": {"male": "nl-NL-MaartenNeural", "female": "nl-NL-FennaNeural"},
    "pl": {"male": "pl-PL-MarekNeural", "female": "pl-PL-ZofiaNeural"},
    "tr": {"male": "tr-TR-AhmetNeural", "female": "tr-TR-EmelNeural"},
}

def resolve_lang_code(lang_str: str) -> str:
    l = str(lang_str or "").lower().strip()
    if any(k in l for k in ("viet", "vn", "tiếng việt")): return "vi"
    if any(k in l for k in ("russ", "ru", "tiếng nga")): return "ru"
    if any(k in l for k in ("span", "es", "tây ban nha")): return "es"
    if any(k in l for k in ("chin", "zh", "tiếng trung")): return "zh"
    if any(k in l for k in ("jap", "ja", "tiếng nhật")): return "ja"
    if any(k in l for k in ("kor", "ko", "tiếng hàn")): return "ko"
    if any(k in l for k in ("fren", "fr", "tiếng pháp")): return "fr"
    if any(k in l for k in ("germ", "de", "tiếng đức")): return "de"
    if any(k in l for k in ("port", "pt", "bồ đào nha")): return "pt"
    if any(k in l for k in ("ital", "it", "tiếng ý")): return "it"
    if any(k in l for k in ("thai", "th", "tiếng thái")): return "th"
    if any(k in l for k in ("arab", "ar", "ả rập")): return "ar"
    if any(k in l for k in ("hind", "hi", "ấn độ")): return "hi"
    if any(k in l for k in ("indo", "id", "malay")): return "id"
    if any(k in l for k in ("dutc", "nl", "hà lan")): return "nl"
    if any(k in l for k in ("poli", "pl", "ba lan")): return "pl"
    if any(k in l for k in ("turk", "tr", "thổ nhĩ kỳ")): return "tr"
    return "en"

ENABLE_EDGE_TTS = False

def _render_edge_tts(text: str, output_path: str, voice_name: str, language: str, pacing: str = "slow") -> bool:
    # STRICT BAN: Edge-TTS forbidden by user
    if not ENABLE_EDGE_TTS:
        return False
    """Renders high-quality Neural voice using Edge-TTS with natural pacing and emotion."""
    import asyncio
    try:
        import edge_tts
    except ImportError:
        return False

    lang_code = resolve_lang_code(language)
    voice_lower = str(voice_name or "").lower()
    is_male = any(m in voice_lower for m in MALE_NAMES)
    gender_key = "male" if is_male else "female"

    pair = EDGE_NEURAL_VOICES.get(lang_code, EDGE_NEURAL_VOICES["en"])
    chosen_voice = pair.get(gender_key, pair["male"])

    if pacing == "slow":
        rate = "-4%" if lang_code in ("vi", "ru", "es", "de") else "-6%"
        pitch = "-1Hz"
    elif pacing == "normal":
        rate = "+0%" if lang_code in ("vi", "ru", "es", "de") else "+0%"
        pitch = "+0Hz"
    else:
        rate = "+5%"
        pitch = "+1Hz"

    temp_mp3 = output_path + ".edge.mp3"
    word_events = []
    try:
        async def _run():
            nonlocal word_events
            comm = edge_tts.Communicate(text, chosen_voice, rate=rate, pitch=pitch, boundary="WordBoundary")
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
                "-ar", "24000", "-ac", "1",
                output_path
            ]
            subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            if os.path.exists(temp_mp3):
                try: os.unlink(temp_mp3)
                except Exception: pass
            if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                print(f"[TTS_EDGE] Đã tạo âm thanh Neural ({chosen_voice}, {rate}, {pitch}): {output_path}", flush=True)
                try:
                    from .word_aligner import chunk_words_into_subtitle_phrases
                    companion_json = output_path + ".words.json"
                    sub_chunks = chunk_words_into_subtitle_phrases(word_events, max_words_per_chunk=4)
                    with open(companion_json, "w", encoding="utf-8") as wf:
                        json.dump({
                            "audio_file": os.path.basename(output_path),
                            "voice": chosen_voice,
                            "words": word_events,
                            "subtitles": sub_chunks
                        }, wf, ensure_ascii=False, indent=2)
                except Exception as w_err:
                    print(f"[TTS_EDGE] Note saving words companion: {w_err}", flush=True)
                return True
    except Exception as e:
        print(f"[TTS_EDGE] Edge-TTS gặp lỗi ({e}), chuyển sang phương thức dự phòng...", flush=True)
        if os.path.exists(temp_mp3):
            try: os.unlink(temp_mp3)
            except Exception: pass
    return False

def sanitize_audio_duration(audio_path: str) -> str:
    """Detects and trims excessive leading, trailing, and internal silence gaps from TTS output.
    Prevents Gemini TTS pauses from hallucinating minutes of dead silence.
    """
    try:
        import wave
        import numpy as np
        if not os.path.exists(audio_path) or os.path.getsize(audio_path) < 1000:
            return audio_path

        with wave.open(audio_path, "rb") as w:
            nchannels = w.getnchannels()
            sampwidth = w.getsampwidth()
            sr = w.getframerate()
            frames = w.readframes(w.getnframes())

        samples = np.frombuffer(frames, dtype=np.int16)
        dur = len(samples) / sr
        chunk_size = int(sr * 0.05) # 50ms chunks
        num_chunks = len(samples) // chunk_size

        is_speech = []
        for c in range(num_chunks):
            chk = samples[c * chunk_size : (c + 1) * chunk_size]
            rms = np.sqrt(np.mean(chk.astype(np.float64) ** 2))
            mx = np.max(np.abs(chk))
            is_speech.append(rms > 500 or mx > 3500)

        if not any(is_speech):
            return audio_path

        first_speech = next(i for i, val in enumerate(is_speech) if val)
        last_speech = len(is_speech) - 1 - next(i for i, val in enumerate(reversed(is_speech)) if val)

        start_chunk = max(0, first_speech - 5) # 0.25s leading pause
        end_chunk = min(num_chunks, last_speech + 20) # 1.0s trailing pause

        # Collapse any internal pause > 1.2s (24 chunks) down to 0.7s (14 chunks)
        kept_chunks = []
        silence_run = 0
        for c in range(start_chunk, end_chunk):
            if is_speech[c]:
                silence_run = 0
                kept_chunks.append(samples[c * chunk_size : (c + 1) * chunk_size])
            else:
                silence_run += 1
                if silence_run <= 14:
                    kept_chunks.append(samples[c * chunk_size : (c + 1) * chunk_size])

        if not kept_chunks:
            return audio_path

        cleaned_samples = np.concatenate(kept_chunks)
        new_dur = len(cleaned_samples) / sr

        if dur - new_dur > 1.5:
            with wave.open(audio_path, "wb") as w:
                w.setnchannels(nchannels)
                w.setsampwidth(sampwidth)
                w.setframerate(sr)
                w.writeframes(cleaned_samples.tobytes())
            print(f"[TTS_SANITIZER] Đã lọc bỏ {dur - new_dur:.1f}s khoảng lặng chết: {dur:.1f}s -> {new_dur:.1f}s", flush=True)

        return audio_path
    except Exception as e:
        print(f"[TTS_SANITIZER] Note: {e}", flush=True)
        return audio_path


def generate_tts_audio_tool_fn(text: str, speaker_one: str = None, speaker_two: str = None, language: str = "vietnamese", voice_name: str = "Charon", voice_style: str = "") -> str:
    """
    Generates high-quality TTS audio with natural emotion, inflection, and pacing.
    Prioritizes Gemini 3.8 Studio TTS voices, with Edge-TTS & Google TTS fallbacks.
    """
    try:
        voice_name = validate_voice(voice_name)
    except Exception:
        voice_name = "Charon"

    timestamp = uuid.uuid4().hex
    filename = f"generated_audio_{timestamp}.wav"
    output_path = os.path.join(utils.GLOBAL_OUTPUT_DIR, filename) if utils.GLOBAL_OUTPUT_DIR else filename

    print(f"Generating TTS [{voice_name}] for: {text[:60]}...", flush=True)

    # NOTE: Edge-TTS is strictly banned per user directive.
    # All languages including Vietnamese route directly to Gemini Studio Audio.
    lang_code = resolve_lang_code(language)

    # Ensure GenAI client is available
    if utils.client is None:
        try:
            from google import genai
            from resilient_gemini import ResilientClient, get_all_api_keys
            keys = [k for k in get_all_api_keys() if not k.startswith("http") and not k.startswith("sk-")]
            if keys:
                utils.client = ResilientClient(genai.Client(api_key=keys[0]), api_keys=keys)
        except Exception:
            pass

    # 1. Primary Engine: Gemini 3.8 Studio TTS (Authentic human nuance & emotion)
    if utils.client:
        try:
            if voice_style:
                prompt_text = f"[{voice_style}]\n{text}"
            else:
                prompt_text = (
                    f"[narration style: natural human voice, warm, emotional, slow and contemplative pacing (~125 words per minute), natural pauses between sentences, speaking in {language}]\n"
                    f"{text}"
                )

            model_to_use = TTS_MODEL or "gemini-2.5-flash-preview-tts"
            response = utils.client.models.generate_content(
                model=model_to_use,
                contents=prompt_text,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name)
                        )
                    ),
                )
            )
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.inline_data and part.inline_data.data:
                        data = part.inline_data.data
                        if data[:4] == b"RIFF" and data[8:12] == b"WAVE":
                            with open(output_path, "wb") as f:
                                f.write(data)
                        else:
                            utils.save_pcm_to_wav(output_path, data)

                        if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                            sanitize_audio_duration(output_path)
                            print(f"[TTS_GEMINI] Đã tạo âm thanh Gemini Studio ({voice_name}): {output_path}", flush=True)
                            try:
                                from .word_aligner import align_existing_audio
                                align_existing_audio(output_path, text)
                            except Exception as al_err:
                                print(f"[TTS_GEMINI] Note aligning words: {al_err}", flush=True)
                            return output_path
        except Exception as e:
            print(f"[TTS_FALLBACK] Gemini TTS gặp sự cố ({e}), tự động chuyển sang giọng dự phòng cấp 2 (Edge-TTS)...", flush=True)

    # 2. Secondary Engine: Edge-TTS permanently disabled per user directive

    # 3. Tertiary Engine: Google TTS Fallback
    try:
        from gtts import gTTS
        lang_code = resolve_lang_code(language)
        temp_mp3 = output_path + ".temp.mp3"
        tts = gTTS(text, lang=lang_code)
        tts.save(temp_mp3)
        cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-i", temp_mp3,
            "-ar", "24000", "-ac", "1",
            output_path
        ]
        subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if os.path.exists(temp_mp3):
            try: os.unlink(temp_mp3)
            except Exception: pass
        if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            print(f"[TTS_FALLBACK] Đã tạo âm thanh qua Google TTS: {output_path}", flush=True)
            try:
                from .word_aligner import align_existing_audio
                align_existing_audio(output_path, text)
            except Exception as al_err:
                print(f"[TTS_FALLBACK] Note aligning words: {al_err}", flush=True)
            return output_path
    except Exception as fb_err:
        print(f"[TTS_FALLBACK] Lỗi Google TTS: {fb_err}", flush=True)

    return f"An error occurred during TTS generation"
