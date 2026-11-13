"""
Voice Engine powered by Google Gemini TTS with Key Rotation & Duration Tracking.
Synthesizes cinema-grade voiceovers for movie recap segments.
"""

from pathlib import Path
import sys
import subprocess
import time
import re
import concurrent.futures
from typing import Dict, Any, List, Optional

WIN_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0
from google import genai
from google.genai import types

try:
    from ..config import load_config, KeyRotator
    from .ffmpeg_utils import get_ffmpeg_path, get_ffprobe_path, run_ffprobe_json
except (ImportError, ValueError):
    from config import load_config, KeyRotator
    from core.ffmpeg_utils import get_ffmpeg_path, get_ffprobe_path, run_ffprobe_json


GEMINI_TTS_MODELS = [
    "gemini-3.1-flash-tts-preview",
    "gemini-3.8-flash-tts",
    "gemini-2.5-flash-preview-tts",
    "gemini-3.8-flash-lite-tts"
]


class RecapVoiceEngine:
    """Manages Gemini TTS voice synthesis for movie recap scripts."""

    def __init__(self):
        self.config = load_config()
        self.keys = self.config.get("gemini_keys", [])
        if not self.keys:
            raise ValueError("Chưa cấu hình Gemini API Key trong recap_config.json!")
        self.rotator = KeyRotator(self.keys)
        self.ffmpeg = get_ffmpeg_path()
        self.default_voice = self.config.get("gemini_voice", "Fenrir")
        self.default_speed = float(self.config.get("voice_speed", 1.15))

    def generate_single_speech(
        self,
        text: str,
        output_file: str,
        voice_name: Optional[str] = None,
        speed: Optional[float] = None
    ) -> float:
        """
        Synthesizes a single voice segment using Gemini TTS.
        Applies speed multiplier via FFmpeg atempo filter.
        Returns exact audio duration in seconds.
        """
        voice = voice_name or self.default_voice
        target_speed = speed if speed is not None else self.default_speed

        clean_text = text.strip()
        if not clean_text:
            raise ValueError("Văn bản đọc trống!")

        out_path = Path(output_file).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        raw_pcm_path = out_path.with_suffix(".raw.pcm")

        max_attempts = len(self.keys) * len(GEMINI_TTS_MODELS)
        attempt = 0
        model_idx = 0
        raw_bytes = None

        while attempt < max_attempts:
            client = self.rotator.get_client(timeout_sec=30.0)
            current_model = GEMINI_TTS_MODELS[model_idx % len(GEMINI_TTS_MODELS)]
            try:
                resp = client.models.generate_content(
                    model=current_model,
                    contents=clean_text,
                    config=types.GenerateContentConfig(
                        response_modalities=["AUDIO"],
                        speech_config=types.SpeechConfig(
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                    voice_name=voice
                                )
                            )
                        )
                    )
                )

                if resp.candidates and resp.candidates[0].content and resp.candidates[0].content.parts:
                    for part in resp.candidates[0].content.parts:
                        if part.inline_data and part.inline_data.data:
                            raw_bytes = part.inline_data.data
                            break

                if raw_bytes:
                    break
                else:
                    raise RuntimeError("Không nhận được dữ liệu âm thanh từ Gemini TTS.")
            except Exception as e:
                err_str = str(e).lower()
                # If quota exhausted, rotate to next key
                if "429" in err_str or "resource_exhausted" in err_str or "quota" in err_str:
                    self.rotator.rotate_next()
                elif "404" in err_str or "not found" in err_str or "503" in err_str:
                    model_idx += 1
                else:
                    self.rotator.rotate_next()
                attempt += 1
                time.sleep(0.5)

        if not raw_bytes:
            raise RuntimeError(f"Không thể tạo giọng đọc qua Gemini TTS sau {attempt} lần thử.")

        # Save raw PCM
        raw_pcm_path.write_bytes(raw_bytes)

        # Convert raw PCM (24kHz s16le mono) to final audio file (mp3 or wav) with speed filter
        tempo_filter = []
        if abs(target_speed - 1.0) > 0.02:
            # atempo supports 0.5 to 2.0
            tempo_filter = ["-filter:a", f"atempo={target_speed}"]

        cmd = [
            self.ffmpeg, "-y",
            "-f", "s16le",
            "-ar", "24000",
            "-ac", "1",
            "-i", str(raw_pcm_path),
        ] + tempo_filter + [
            "-b:a", "192k",
            str(out_path)
        ]

        conv_res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=WIN_NO_WINDOW)
        if raw_pcm_path.is_file():
            try:
                raw_pcm_path.unlink()
            except Exception:
                pass

        if conv_res.returncode != 0 or not out_path.is_file():
            raise RuntimeError(f"Lỗi chuyển đổi audio: {conv_res.stderr.decode('utf-8', errors='replace')}")

        return self.get_audio_duration(str(out_path))

    @staticmethod
    def get_audio_duration(audio_file: str) -> float:
        """Measures precise audio duration in seconds using ffprobe."""
        raw = run_ffprobe_json([
            "-show_entries", "format=duration",
            str(audio_file)
        ])
        fmt = raw.get("format", {})
        return float(fmt.get("duration", 0.0))

    def batch_generate(
        self,
        segments: List[Dict[str, Any]],
        output_dir: str,
        voice_name: Optional[str] = None,
        speed: Optional[float] = None,
        progress_callback=None
    ) -> List[Dict[str, Any]]:
        """
        Synthesizes audio for all segments in a script, updating durations and timeline timestamps.
        """
        out_dir = Path(output_dir).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)

        voice = voice_name or self.default_voice
        target_speed = speed if speed is not None else self.default_speed

        total = len(segments)
        completed_count = 0
        import threading
        lock = threading.Lock()

        def process_segment(item):
            nonlocal completed_count
            idx, seg = item
            seg_id = seg.get("id", idx + 1)
            filename = f"audio_seg_{seg_id:03d}.mp3"
            target_path = out_dir / filename

            duration = self.generate_single_speech(
                text=seg["text"],
                output_file=str(target_path),
                voice_name=voice,
                speed=target_speed
            )

            seg["audio_file"] = str(target_path)
            seg["duration"] = round(duration, 2)

            with lock:
                completed_count += 1
                if progress_callback:
                    progress_callback(completed_count, total, seg)
            return (idx, seg)

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            indexed_items = list(enumerate(segments))
            results = list(executor.map(process_segment, indexed_items))

        # Re-sort to maintain original order and calculate timeline
        results.sort(key=lambda x: x[0])
        current_timeline_time = 0.0
        for _, seg in results:
            seg["timeline_start"] = round(current_timeline_time, 2)
            seg["timeline_end"] = round(current_timeline_time + seg["duration"], 2)
            current_timeline_time += seg["duration"]

        return [r[1] for r in results]
