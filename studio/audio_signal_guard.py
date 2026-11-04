"""Fail-closed, signal-level preflight for scenes expected to contain narration.

This detects silent/inaudible audio but does NOT prove spoken-word accuracy,
language, speaker identity or naturalness. Do not call for deliberately silent scenes.
"""
from __future__ import annotations

import math
import re
import subprocess
from pathlib import Path


def inspect_audio_signal(path, *, timeout=45):
    media = Path(path)
    if not media.is_file() or media.stat().st_size < 256:
        raise RuntimeError("NARRATION_AUDIO_MISSING: " + str(media))
    cmd = ["ffmpeg", "-nostdin", "-hide_banner", "-i", str(media),
           "-vn", "-af", "volumedetect", "-f", "null", "-"]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=timeout,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError("NARRATION_AUDIO_PROBE_FAILED") from exc
    if result.returncode:
        raise RuntimeError("NARRATION_AUDIO_DECODE_FAILED")
    def level(kind):
        matches = re.findall(
            rf"\b{kind}:\s*(-?inf|[-+]?\d+(?:\.\d+)?)\s*dB",
            result.stderr, flags=re.I
        )
        if not matches:
            raise RuntimeError("NARRATION_AUDIO_MEASURE_MISSING: " + kind)
        value = float(matches[-1])
        if math.isnan(value) or value == math.inf:
            raise RuntimeError("NARRATION_AUDIO_MEASURE_INVALID: " + kind)
        return value
    return {"max_dbfs": level("max_volume"),
            "mean_dbfs": level("mean_volume"),
            "method": "ffmpeg_volumedetect",
            "speech_verified": False}


def require_audible_if_spoken(path, expected_text, *, min_peak_dbfs=-65.0, min_mean_dbfs=-75.0):
    """Never reject an intentionally silent scene; require signal for spoken lines."""
    if not str(expected_text or "").strip():
        return {"status": "SKIPPED_INTENTIONAL_SILENCE", "speech_verified": False}
    metrics = inspect_audio_signal(path)
    if metrics["max_dbfs"] <= min_peak_dbfs or metrics["mean_dbfs"] <= min_mean_dbfs:
        raise RuntimeError(
            "NARRATION_AUDIO_SILENT: expected spoken text but audio signal "
            f"is inaudible (max={metrics['max_dbfs']:.1f} dBFS, "
            f"mean={metrics['mean_dbfs']:.1f} dBFS). Keep original cache for review."
        )
    return {"status": "AUDIBLE_SIGNAL_PRESENT", **metrics}


def expected_scene_speech(scene):
    """Collect only text explicitly intended to be spoken, including drama beats."""
    get = scene.get if isinstance(scene, dict) else lambda key, default=None: getattr(scene, key, default)
    words = []
    narration = str(get("narration", "") or "").strip()
    if narration:
        words.append(narration)
    for beat in (get("dialogue_beats", []) or []):
        speech = beat.get("text", "") if isinstance(beat, dict) else getattr(beat, "text", "")
        speech = str(speech or "").strip()
        if speech:
            words.append(speech)
    return "\n".join(words)
