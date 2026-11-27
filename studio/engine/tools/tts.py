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
    import re as _re
    l = str(lang_str or "").lower().strip()
    if any(k in l for k in ("viet", "tiếng việt", "tieng viet")) or l in ("vi", "vn", "vi-vn"):
        return "vi"
    if any(k in l for k in ("russ", "tiếng nga", "рус")) or l in ("ru", "ru-ru", "nga"):
        return "ru"
    if any(k in l for k in ("span", "tây ban nha", "español", "espanol")) or bool(_re.search(r"(?:^|[\s_\-/,(])(?:es|es-[a-z]{2}|esp)(?:$|[\s_\-/,)])", l)):
        return "es"
    if any(k in l for k in ("chin", "tiếng trung", "mandarin", "中文")) or l in ("zh", "zh-cn", "zh-tw"):
        return "zh"
    if any(k in l for k in ("jap", "tiếng nhật", "日本語")) or l in ("ja", "ja-jp", "jp"):
        return "ja"
    if any(k in l for k in ("kor", "tiếng hàn", "한국")) or l in ("ko", "ko-kr", "kr"):
        return "ko"
    if any(k in l for k in ("fren", "tiếng pháp", "français")) or l in ("fr", "fr-fr"):
        return "fr"
    if any(k in l for k in ("germ", "tiếng đức", "deutsch")) or l in ("de", "de-de"):
        return "de"
    if any(k in l for k in ("port", "bồ đào nha")) or l in ("pt", "pt-br"):
        return "pt"
    if any(k in l for k in ("ital", "tiếng ý")) or l in ("it", "it-it"):
        return "it"
    if any(k in l for k in ("thai", "tiếng thái")) or l in ("th", "th-th"):
        return "th"
    if any(k in l for k in ("arab", "ả rập")) or l in ("ar", "ar-sa"):
        return "ar"
    if any(k in l for k in ("hind", "ấn độ")) or l in ("hi", "hi-in"):
        return "hi"
    if any(k in l for k in ("indo", "malay")) or l in ("id", "id-id"):
        return "id"
    if any(k in l for k in ("dutc", "hà lan")) or l in ("nl", "nl-nl"):
        return "nl"
    if any(k in l for k in ("poli", "ba lan")) or l in ("pl", "pl-pl"):
        return "pl"
    if any(k in l for k in ("turk", "thổ nhĩ kỳ")) or l in ("tr", "tr-tr"):
        return "tr"
    return "en"


ENABLE_EDGE_TTS = True


def _write_tts_engine_meta(audio_path: str, engine: str, voice_name: str, actual_voice: str, gender: str) -> None:
    try:
        meta_path = str(audio_path) + ".engine.json"
        with open(meta_path, "w", encoding="utf-8") as mf:
            json.dump(
                {
                    "engine": engine,
                    "voice_name": voice_name,
                    "actual_voice": actual_voice,
                    "gender": gender,
                },
                mf,
                ensure_ascii=False,
                indent=2,
            )
    except Exception:
        pass


def _render_edge_tts(text: str, output_path: str, voice_name: str, language: str, pacing: str = "slow") -> bool:
    """Renders high-quality Neural voice via Edge-TTS strictly as emergency fallback when Gemini TTS pool is exhausted, matching speaker gender."""
    if not ENABLE_EDGE_TTS:
        return False
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

    temp_mp3 = output_path + ".edge.mp3"
    word_events = []

    async def _run_plain_neural():
        nonlocal word_events
        word_events = []
        # Note: edge-tts 7.3+ rejects custom SSML rate/pitch for several neural voices (e.g. vi-VN);
        # plain default Communicate with WordBoundary produces clean audio + exact word timings.
        comm = edge_tts.Communicate(text, chosen_voice, boundary="WordBoundary")
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

    try:
        asyncio.run(_run_plain_neural())
        if os.path.exists(temp_mp3) and os.path.getsize(temp_mp3) > 500:
            # Gentle tempo tuning via ffmpeg if user explicitly asked slow/fast without breaking MS SSML
            af_chain = []
            if pacing == "fast":
                af_chain.append("atempo=1.05")
            cmd = [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-i", temp_mp3,
                *(["-af", ",".join(af_chain)] if af_chain else []),
                "-ar", "24000", "-ac", "1",
                output_path
            ]
            subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            if os.path.exists(temp_mp3):
                try:
                    os.unlink(temp_mp3)
                except Exception:
                    pass
            if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                sanitize_audio_duration(output_path)
                print(f"[TTS_EDGE] Đã tạo âm thanh Neural dự phòng ({chosen_voice}, gender={gender_key}): {output_path}", flush=True)
                try:
                    from .word_aligner import chunk_words_into_subtitle_phrases, align_existing_audio
                    companion_json = output_path + ".words.json"
                    if word_events:
                        sub_chunks = chunk_words_into_subtitle_phrases(word_events, max_words_per_chunk=4)
                        with open(companion_json, "w", encoding="utf-8") as wf:
                            json.dump({
                                "audio_file": os.path.basename(output_path),
                                "voice": chosen_voice,
                                "words": word_events,
                                "subtitles": sub_chunks
                            }, wf, ensure_ascii=False, indent=2)
                    else:
                        align_existing_audio(output_path, text)
                except Exception as w_err:
                    print(f"[TTS_EDGE] Note saving words companion: {w_err}", flush=True)
                _write_tts_engine_meta(output_path, "edge_tts", voice_name, chosen_voice, gender_key)
                return True
    except Exception as e:
        print(f"[TTS_EDGE] Edge-TTS gặp lỗi ({e}), chuyển sang phương thức dự phòng...", flush=True)
        if os.path.exists(temp_mp3):
            try:
                os.unlink(temp_mp3)
            except Exception:
                pass
    return False

def sanitize_audio_duration(audio_path: str) -> str:
    """Trims excessive leading, trailing, and internal silence gaps so narration flows smoothly without dead air."""
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

        if sampwidth != 2 or nchannels != 1:
            return audio_path

        samples = np.frombuffer(frames, dtype=np.int16)
        dur = len(samples) / max(1, sr)
        chunk_size = max(1, int(sr * 0.025))  # 25ms chunks for crisp, non-destructive boundaries
        num_chunks = len(samples) // chunk_size

        is_speech = []
        for c in range(num_chunks):
            chk = samples[c * chunk_size : (c + 1) * chunk_size]
            rms = np.sqrt(np.mean(chk.astype(np.float64) ** 2))
            mx = np.max(np.abs(chk))
            is_speech.append(rms > 300 or mx > 2200)

        if not any(is_speech):
            return audio_path

        first_speech = next(i for i, val in enumerate(is_speech) if val)
        last_speech = len(is_speech) - 1 - next(i for i, val in enumerate(reversed(is_speech)) if val)

        start_chunk = max(0, first_speech - 3)      # ~0.075s crisp leading attack
        end_chunk = min(num_chunks, last_speech + 6)  # ~0.15s tight trailing breath

        # Collapse any internal pause > 0.65s (26 chunks) down to 0.35s (14 chunks)
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

        cleaned_samples = np.concatenate(kept_chunks).astype(np.float64)
        new_dur = len(cleaned_samples) / max(1, sr)

        if dur - new_dur >= 0.12 and new_dur >= 0.35:
            fade_n = min(len(cleaned_samples) // 8, max(1, int(sr * 0.012)))
            if fade_n > 1:
                cleaned_samples[:fade_n] *= np.linspace(0.0, 1.0, fade_n)
                cleaned_samples[-fade_n:] *= np.linspace(1.0, 0.0, fade_n)
            out_i16 = np.clip(cleaned_samples, -32767, 32767).astype(np.int16)
            with wave.open(audio_path, "wb") as w:
                w.setnchannels(nchannels)
                w.setsampwidth(sampwidth)
                w.setframerate(sr)
                w.writeframes(out_i16.tobytes())
            print(f"[TTS_SANITIZER] Đã siết nhịp, cắt {dur - new_dur:.2f}s khoảng lặng thừa: {dur:.2f}s -> {new_dur:.2f}s", flush=True)

        return audio_path
    except Exception as e:
        print(f"[TTS_SANITIZER] Note: {e}", flush=True)
        return audio_path


def generate_tts_audio_tool_fn(text: str, speaker_one: str = None, speaker_two: str = None, language: str = "vietnamese", voice_name: str = "Charon", voice_style: str = "") -> str:
    """
    Generates high-quality TTS audio with natural emotion, inflection, and pacing.
    Prioritizes Gemini Studio TTS voices across full key pool, with gender-matched Neural Edge-TTS & Google TTS fallbacks.
    """
    try:
        voice_name = validate_voice(voice_name)
    except Exception:
        voice_name = "Charon"

    voice_lower = str(voice_name or "").lower()
    gender_key = "male" if any(m in voice_lower for m in MALE_NAMES) else "female"

    timestamp = uuid.uuid4().hex
    filename = f"generated_audio_{timestamp}.wav"
    output_path = os.path.join(utils.GLOBAL_OUTPUT_DIR, filename) if utils.GLOBAL_OUTPUT_DIR else filename

    print(f"Generating TTS [{voice_name}] for: {text[:60]}...", flush=True)

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

    force_engine = str(os.environ.get("STUDIO_FORCE_TTS_ENGINE", "") or "").strip().lower()

    # 1. Primary Engine: Gemini Studio TTS (Authentic human nuance & emotion)
    if utils.client and force_engine not in ("edge", "edge_tts", "gtts"):
        if voice_style:
            primary_prompt = f"[{voice_style}]\nRead aloud word-for-word without conversational reply:\n{text}"
        else:
            primary_prompt = (
                f"[narration style: natural warm storytelling human voice, emotional cadence, clear inflection, speaking in {language}]\n"
                f"Read aloud word-for-word without conversational reply:\n{text}"
            )
        fallback_prompt = (
            f"Voiceover recording transcript in {language}. Speak ONLY the words inside quotes aloud with expressive narration:\n"
            f'"{text}"'
        )
        model_to_use = TTS_MODEL or "gemini-2.5-flash-preview-tts"
        for prompt_attempt in (primary_prompt, fallback_prompt):
            try:
                response = utils.client.models.generate_content(
                    model=model_to_use,
                    contents=prompt_attempt,
                    config=types.GenerateContentConfig(
                        response_modalities=["AUDIO"],
                        speech_config=types.SpeechConfig(
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name)
                            )
                        ),
                    )
                )
                candidates = getattr(response, "candidates", None) or []
                parts = getattr(getattr(candidates[0], "content", None), "parts", None) if candidates else None
                if parts:
                    for part in parts:
                        inline = getattr(part, "inline_data", None)
                        data = getattr(inline, "data", None) if inline else None
                        if data:
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
                                _write_tts_engine_meta(output_path, "gemini", voice_name, voice_name, gender_key)
                                return output_path
            except Exception as e:
                msg_low = str(e).lower()
                if prompt_attempt is primary_prompt and ("model tried to generate text" in msg_low or "nonetype" in msg_low):
                    print(f"[TTS_GEMINI_RETRY] Thử lại prompt đọc thuần audio ({str(e)[:80]})...", flush=True)
                    continue
                print(f"[TTS_FALLBACK] Gemini TTS gặp sự cố ({e}), chuyển sang giọng Neural dự phòng...", flush=True)
                break

    # 2. Secondary Engine: Microsoft Neural Edge-TTS matching requested voice gender & language
    if force_engine != "gtts" and _render_edge_tts(text, output_path, voice_name, language, pacing="normal"):
        return output_path

    # 3. Tertiary Engine: Google TTS Fallback (last resort)
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
            sanitize_audio_duration(output_path)
            print(f"[TTS_FALLBACK] Đã tạo âm thanh qua Google TTS: {output_path}", flush=True)
            try:
                from .word_aligner import align_existing_audio
                align_existing_audio(output_path, text)
            except Exception as al_err:
                print(f"[TTS_FALLBACK] Note aligning words: {al_err}", flush=True)
            _write_tts_engine_meta(output_path, "gtts", voice_name, f"gtts:{lang_code}", "female")
            return output_path
    except Exception as fb_err:
        print(f"[TTS_FALLBACK] Lỗi Google TTS: {fb_err}", flush=True)

    return f"An error occurred during TTS generation"
