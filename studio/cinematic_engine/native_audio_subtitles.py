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

def strip_vad_proven_repeated_silence_tail(data):
    """Trim an exact repeated ASR phrase wholly outside VAD speech, never a real utterance.

    Stable Whisper may hallucinate a repeated phrase after all speech has ended,
    returning several words with the same zero-length timestamp. Reject these
    only when the repeated tail exactly matches already transcribed speech,
    starts beyond a VAD-confirmed silent boundary, and the earlier phrase has
    valid spoken anchors. All other bad alignments still fail closed.
    """
    words = list(data.get("words") or [])
    intervals = list(data.get("speech_intervals") or [])
    if len(words) < 4 or not intervals:
        return data
    last_speech_end = max(float(v["end"]) for v in intervals)
    boundary = last_speech_end + 0.12
    cut = next((i for i, w in enumerate(words)
                if float(w.get("start", 0)) > boundary),len(words))
    head, tail = words[:cut], words[cut:]
    if len(head) < 2 or len(tail) < 2 or len(tail) > len(head):
        return data
    if any(float(w.get("start", 0)) <= boundary for w in tail):
        return data
    def normalized(items):
        return [str(w.get("word", "")).casefold().strip(".,?!…;: ") for w in items]
    if normalized(tail) != normalized(head[-len(tail):]):
        return data
    # Confirm the source phrase overlaps a VAD speech interval, not another
    # hallucination. VAD timestamps are in original clip seconds.
    if not all(any(float(v["start"])-0.12 <=
                   (float(w["start"])+float(w["end"]))/2 <= float(v["end"])+0.12
                   for v in intervals) for w in head[-len(tail):]):
        return data
    data["raw_recognized_transcript"] = data.get("transcript", "")
    data["words"] = head
    data["transcript"] = " ".join(str(w["word"]) for w in head)
    expected = str(data.get("expected_text") or "")
    if expected:
        data["script_mismatch"] = tokens(data["transcript"]) != tokens(expected)
    data["asr_silence_tail_filtered"] = {
        "reason":"Exact repeated ASR tokens outside the last VAD speech interval",
        "discarded_phantom_word_count":len(tail),
        "source_speech_end":last_speech_end
    }
    return data

def validate_words(words, duration):
    result = []
    last_end = 0.0
    for entry in words:
        text = str(entry.get("word", "")).strip()
        if not text:
            continue
        try:
            start = float(entry.get("start", 0))
            end = float(entry.get("end", 0))
        except (ValueError, TypeError):
            continue
        if not math.isfinite(start): start = last_end
        if not math.isfinite(end): end = start + 0.2
        start = max(0.0, start)
        start = max(start, last_end)
        if end <= start:
            end = start + 0.18
        end = min(max(end, start + 0.05), duration)
        if end > start:
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
            raise RuntimeError(f"WORD_IN_SILENCE: speech anchor absent at {midpoint:.3f}s")
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
        data = strip_vad_proven_repeated_silence_tail(data)
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
