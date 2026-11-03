"""Audio-derived subtitles for native video. No duration-based fallback."""
from __future__ import annotations
import contextlib
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import threading
import time
import wave

VERSION = "native-audio-v1"
STUDIO = Path(__file__).resolve().parents[1]
LOCK = threading.Lock()

def atomic_json(path, data):
    path = Path(path)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temp, path)

def tokens(text):
    return re.findall(r"\w+", text.casefold(), re.UNICODE)

def language_code(value):
    value = str(value or "auto").casefold().strip()
    aliases = {"vietnamese": "vi", "tiếng việt": "vi", "english": "en",
               "spanish": "es", "español": "es", "korean": "ko",
               "japanese": "ja", "chinese": "zh", "french": "fr",
               "german": "de", "russian": "ru"}
    return aliases.get(value, value) if value not in ("", "auto") else None

def validate_words(words, duration):
    result = []
    last_end = 0.0
    for entry in words:
        text = str(entry.get("word", "")).strip()
        start, end = float(entry["start"]), float(entry["end"])
        # Stable Whisper occasionally returns one zero-duration word at a shared
        # boundary. Allocate at most 60 ms from the preceding measured word,
        # only inside the same speech interval; never spread words over silence.
        if end == start and result and math.isfinite(start) and start >= 0:
            prev = result[-1]
            prev_duration = prev["end"] - prev["start"]
            if abs(prev["end"] - start) <= 0.012 and prev_duration > 0.18:
                carve = min(0.06, (prev_duration - 0.08) / 2)
                prev["end"] = round(start - carve, 3)
                start = prev["end"]
                last_end = start
                end = float(entry["start"])
        if (not text or not math.isfinite(start) or not math.isfinite(end)
                or start < 0 or end <= start or end > duration + 0.05
                or start < last_end - 0.025):
            raise RuntimeError("SUBTITLE_ALIGNMENT_INVALID_WORD_TIMING")
        start = max(start, last_end)
        end = min(end, duration)
        if end <= start:
            raise RuntimeError("SUBTITLE_ALIGNMENT_INVALID_WORD_TIMING")
        result.append({"word": text, "start": round(start, 3), "end": round(end, 3)})
        last_end = end
    return result

def validate_vad_anchor(words, speech_intervals, tolerance=0.12):
    """Reject words whose midpoint falls in a VAD-confirmed silent gap.

    A full-clip forced alignment can slide an isolated word across seconds of
    silence while still satisfying monotonic timestamp validation.
    """
    for word in words:
        midpoint = (float(word["start"]) + float(word["end"])) / 2
        if not any(float(s["start"]) - tolerance <= midpoint <= float(s["end"]) + tolerance
                   for s in speech_intervals):
            raise RuntimeError("SUBTITLE_ALIGNMENT_WORD_IN_SILENCE")
    return words

def chunk_words(words):
    chunks, group = [], []
    def flush():
        if group:
            chunks.append({"start": group[0]["start"], "end": group[-1]["end"],
                           "text": " ".join(w["word"] for w in group), "words": list(group)})
            group.clear()
    for w in words:
        if group and (w["start"] - group[-1]["end"] >= 0.35 or len(group) >= 6):
            flush()
        group.append(w)
        if w["word"].endswith((".", "!", "?", "…")):
            flush()
    flush()
    return chunks

def srt_time(value):
    total = int(round(value * 1000))
    hours, total = divmod(total, 3600000)
    minutes, total = divmod(total, 60000)
    seconds, millis = divmod(total, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"

@contextlib.contextmanager
def gpu_lock():
    # Serializes only local ASR. Muse network/render workers remain independent.
    path = STUDIO / "runtime" / "subtitle_alignment.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    with LOCK, open(path, "a+b") as handle:
        handle.seek(0, 2)
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        deadline = time.monotonic() + 1800
        while True:
            try:
                handle.seek(0)
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if time.monotonic() > deadline:
                    raise RuntimeError("SUBTITLE_ALIGNMENT_BUSY")
                time.sleep(0.2)
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

def align_native_audio(audio_path, expected_text="", language="auto"):
    audio_path = Path(audio_path)
    if not audio_path.is_file():
        raise RuntimeError("SUBTITLE_ALIGNMENT_AUDIO_MISSING")
    config_path = STUDIO / "runtime" / "subtitle_alignment.json"
    if not config_path.is_file():
        raise RuntimeError("SUBTITLE_ALIGNMENT_NOT_CONFIGURED")
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    ffmpeg = str(STUDIO / "engine" / "bin" / "ffmpeg.exe")
    if not Path(ffmpeg).is_file():
        ffmpeg = "ffmpeg"
    cache = audio_path.parent / "native_audio_alignment.json"
    with tempfile.TemporaryDirectory(prefix="subtitle_sync_") as tmp:
        tmp = Path(tmp)
        wav = tmp / "speech.wav"
        extract = subprocess.run([ffmpeg, "-v", "error", "-y", "-i", str(audio_path),
            "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(wav)],
            capture_output=True, timeout=120,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if extract.returncode:
            raise RuntimeError("SUBTITLE_ALIGNMENT_AUDIO_DECODE_FAILED")
        with wave.open(str(wav), "rb") as wf:
            duration = wf.getnframes() / wf.getframerate()
            pcm = wf.readframes(wf.getnframes())
        signature = hashlib.sha256(pcm).hexdigest()
        lang = language_code(language)
        key = hashlib.sha256(json.dumps([VERSION, signature, expected_text, lang,
            cfg.get("model", "turbo"), "silero-minimal-v1"], ensure_ascii=False).encode()).hexdigest()
        if cache.is_file():
            try:
                data = json.loads(cache.read_text(encoding="utf-8"))
                if data.get("cache_key") == key:
                    data["words"] = validate_words(data["words"], duration)
                    validate_vad_anchor(data["words"], data.get("speech_intervals", []))
                    if not data["words"] and expected_text.strip():
                        raise ValueError("empty cached speech")
                    data["subtitles"] = chunk_words(data["words"])
                    return data
            except (ValueError, KeyError, RuntimeError):
                pass
        request = tmp / "request.json"
        output = tmp / "result.json"
        atomic_json(request, {"audio": str(wav), "expected_text": expected_text,
                             "language": lang, "config": cfg})
        with gpu_lock():
            proc = subprocess.run([cfg.get("python_executable", sys.executable),
                str(Path(__file__).resolve()), "--worker", str(request), str(output)],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                timeout=900, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if proc.returncode or not output.is_file():
            raise RuntimeError("SUBTITLE_ALIGNMENT_FAILED: " + proc.stderr[-1800:])
        data = json.loads(output.read_text(encoding="utf-8"))
        try:
            data["words"] = validate_words(data.get("words", []), duration)
            validate_vad_anchor(data["words"], data.get("speech_intervals", []))
        except RuntimeError:
            atomic_json(audio_path.parent / "native_audio_alignment_error.json", data)
            raise
        if expected_text.strip() and not data["words"]:
            raise RuntimeError("SUBTITLE_ALIGNMENT_NO_SPEECH")
        data.update({"timing_source": VERSION, "cache_key": key,
                     "source_audio_sha256": signature, "duration": duration,
                     "subtitles": chunk_words(data["words"])})
        atomic_json(cache, data)
        return data

def write_native_subtitles(audio_path, expected_text, srt_path, json_path, language="auto"):
    data = align_native_audio(audio_path, expected_text, language)
    srt_path, json_path = Path(srt_path), Path(json_path)
    lines = [f"{i}\n{srt_time(s['start'])} --> {srt_time(s['end'])}\n{s['text']}\n"
             for i, s in enumerate(data["subtitles"], 1)]
    temp = srt_path.with_name(srt_path.name + ".tmp")
    temp.write_text("\n".join(lines), encoding="utf-8")
    os.replace(temp, srt_path)
    word_srt_path = srt_path.with_name(srt_path.stem + ".words.srt")
    word_lines = [f"{i}\n{srt_time(w['start'])} --> {srt_time(w['end'])}\n{w['word']}\n"
                  for i, w in enumerate(data["words"], 1)]
    word_temp = word_srt_path.with_name(word_srt_path.name + ".tmp")
    word_temp.write_text("\n".join(word_lines), encoding="utf-8")
    os.replace(word_temp, word_srt_path)
    atomic_json(json_path, data)
    if data.get("script_mismatch"):
        print("[SUBTITLE_SYNC] Speech differs from script; captions follow recognized audio. Review native_audio_alignment.json.", flush=True)
    print(f"[SUBTITLE_SYNC] {len(data['words'])} audio-derived word timestamps: {audio_path}", flush=True)
    return srt_path

def worker(request_path, output_path):
    req = json.loads(Path(request_path).read_text(encoding="utf-8"))
    cfg = req["config"]
    sys.path.insert(0, str(STUDIO / "runtime" / "subtitle_alignment_vendor"))
    os.environ["PATH"] = str(STUDIO / "engine" / "bin") + os.pathsep + os.environ.get("PATH", "")
    import numpy as np
    import torch
    import stable_whisper
    from silero_vad import load_silero_vad, get_speech_timestamps
    from stable_whisper.default import cached_model_instances
    vad_model = load_silero_vad()
    cached_model_instances["silero_vad"][False] = (vad_model, get_speech_timestamps)
    torch.set_num_threads(2)
    with wave.open(req["audio"], "rb") as wf:
        pcm = wf.readframes(wf.getnframes())
    audio = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0
    if not len(audio) or np.max(np.abs(audio)) < 0.0001:
        atomic_json(output_path, {"words": [], "transcript": "", "script_mismatch": bool(req["expected_text"].strip())})
        return
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model_root = STUDIO / "runtime" / "subtitle_models"
    model_name = cfg.get("model", "turbo")
    model_file = model_root / (model_name + ".pt")
    if not model_file.is_file():
        raise RuntimeError("SUBTITLE_ALIGNMENT_MODEL_MISSING: " + str(model_file))
    model = stable_whisper.load_model(str(model_file), device=device)
    speech = get_speech_timestamps(torch.from_numpy(audio), vad_model, sampling_rate=16000)
    speech_intervals = [{"start": s["start"] / 16000, "end": s["end"] / 16000} for s in speech]
    if not speech_intervals:
        atomic_json(output_path, {"words": [], "transcript": "", "script_mismatch": bool(req["expected_text"].strip()),
                                 "speech_intervals": []})
        return
    result = model.transcribe_minimal(audio, language=req["language"], verbose=None,
        temperature=0.0, beam_size=5, condition_on_previous_text=False,
        initial_prompt=req["expected_text"] or None,
        word_timestamps=True, regroup=False, suppress_silence=True,
        suppress_word_ts=True, vad=True, fp16=device == "cuda")
    transcript = result.text.strip()
    expected = req["expected_text"].strip()
    mismatch = bool(expected) and tokens(expected) != tokens(transcript)
    # Only restore script spelling/punctuation when every lexical token agrees.
    # Never force unheard script words onto music/silence.
    if expected and not mismatch:
        aligned = model.align(audio, expected, language=req["language"] or result.language,
            verbose=None, original_split=True, suppress_silence=True,
            suppress_word_ts=True, vad=True, failure_threshold=0.05)
        if aligned is not None:
            candidate = [{"word": w.word.strip(), "start": w.start, "end": w.end}
                         for seg in aligned.segments for w in seg.words]
            try:
                validate_words(candidate, len(audio) / 16000)
                validate_vad_anchor(candidate, speech_intervals)
                if candidate:
                    result = aligned
            except RuntimeError:
                # Keep the independently measured transcription timestamps.
                pass
    words = [{"word": w.word.strip(), "start": w.start, "end": w.end}
             for seg in result.segments for w in seg.words]
    atomic_json(output_path, {"words": words, "transcript": transcript,
        "expected_text": expected, "script_mismatch": mismatch, "language": result.language,
        "model": model_name, "device": device, "alignment_engine": "stable-ts-2.19.1+silero-vad-6.2.3",
        "speech_intervals": speech_intervals})

if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--worker":
        worker(sys.argv[2], sys.argv[3])
    else:
        raise SystemExit("Use --worker REQUEST OUTPUT")
