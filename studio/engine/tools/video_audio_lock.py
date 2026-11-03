
import functools

@functools.lru_cache(maxsize=1)
def _hardware_encoder_usable() -> bool:
    try:
        from studio_color_render import _hardware_encoder_usable as _chk
        return _chk()
    except Exception:
        return False

def _get_encoder_args(crf: int = 20):
    if _hardware_encoder_usable():
        return ["-c:v", "h264_nvenc", "-preset", "p4", "-cq", str(crf)]
    return ["-c:v", "libx264", "-preset", "fast", "-crf", str(crf)]

"""
1:1 Audio-Visual Lock & Kinetic Motion Engine (Milestone 3).
Guarantees absolute frame-accurate synchronization between visual video track
and speech audio track, eliminating frozen frames, dead air, and cut-off speech.
"""
import os
import json
import subprocess
from pathlib import Path
from typing import Optional, Tuple


def ffprobe_duration(file_path: str) -> float:
    """Returns duration in seconds using ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format", "-show_streams",
        str(file_path)
    ]
    try:
        res = subprocess.run(
            cmd, capture_output=True, text=True,
            encoding="utf-8", errors="replace", check=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
        )
        data = json.loads(res.stdout)
        # Try format duration first, fallback to stream duration
        dur_str = data.get("format", {}).get("duration")
        if dur_str:
            return float(dur_str)
        streams = data.get("streams", [])
        for st in streams:
            if "duration" in st:
                return float(st["duration"])
        return 0.0
    except Exception as e:
        print(f"[AUDIO_VISUAL_LOCK] ffprobe warning for {file_path}: {e}")
        return 0.0


def lock_video_to_audio_duration(
    video_path: str,
    audio_path: str,
    output_path: str,
    cushion_seconds: float = 0.15,
    fps: int = 30,
    preset: str = "fast",
    crf: int = 20,
    subtitles_json_path: Optional[str] = None
) -> str:
    """
    Combines visual video and speech audio with 1:1 mathematical locking.

    Three Synchronization Modes:
    1. Case 1 (Video >= Audio):
       Trims visual video to audio duration + cushion. Zero dead air.
    2. Case 2 (Audio slightly longer, <= 20%):
       Applies Cinematic Slow-Motion via setpts with continuous smooth motion.
    3. Case 3 (Audio significantly longer, > 20%):
       Applies Symmetric Ping-Pong Loop (Forward -> Reverse -> Forward)
       to loop motion seamlessly without freezing on a static frame.
    """
    if not os.path.exists(video_path):
        return f"Error: Video file not found: {video_path}"
    if not os.path.exists(audio_path):
        return f"Error: Audio file not found: {audio_path}"

    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    v_dur = ffprobe_duration(video_path)
    a_dur = ffprobe_duration(audio_path)

    # Optional speech end detection from subtitles.json
    speech_end = 0.0
    if subtitles_json_path and os.path.exists(subtitles_json_path):
        try:
            with open(subtitles_json_path, "r", encoding="utf-8") as sf:
                sdata = json.load(sf)
                subs = sdata.get("subtitles", [])
                if subs:
                    last_sub = subs[-1]
                    words = last_sub.get("words", [])
                    if words:
                        speech_end = float(words[-1].get("end", last_sub.get("end", 0.0)))
                    else:
                        speech_end = float(last_sub.get("end", 0.0))
        except Exception:
            pass

    if v_dur <= 0.05:
        v_dur = 5.0
    if a_dur <= 0.05:
        a_dur = speech_end if speech_end > 0.05 else v_dur

    # Target master duration: audio length plus subtle tail cushion for breathing room
    target_dur = round(a_dur, 3)
    delta = a_dur - v_dur

    print(f"[AUDIO_VISUAL_LOCK] Video: {v_dur:.2f}s | Audio: {a_dur:.2f}s | Delta: {delta:+.2f}s", flush=True)

    # CASE 1: Video is longer than or equal to Audio (delta <= 0)
    # Trim video precisely to audio duration + cushion
    if delta <= 0:
        cushioned_dur = min(v_dur, target_dur + cushion_seconds)
        print(f"[AUDIO_VISUAL_LOCK] Case 1 (Trim): Trimming video to {cushioned_dur:.2f}s to eliminate dead air.", flush=True)
        cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-ss", "0", "-to", f"{cushioned_dur:.3f}",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-map", "0:v",
            "-map", "1:a",
            *_get_encoder_args(crf),
            "-c:a", "aac", "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            str(output_path)
        ]

    # CASE 2: Audio is slightly longer than Video (delta <= 20% of video)
    # Apply Cinematic Slow-Mo via setpts: smooth, continuous stretching without stutter
    elif delta <= 0.20 * v_dur:
        speed_factor = target_dur / v_dur
        print(f"[AUDIO_VISUAL_LOCK] Case 2 (Slow-Mo): Stretching video {speed_factor:.3f}x to {target_dur:.2f}s.", flush=True)
        cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-filter_complex", f"[0:v]setpts={speed_factor:.4f}*PTS,fps={fps}[v]",
            "-map", "[v]",
            "-map", "1:a",
            "-t", f"{target_dur:.3f}",
            *_get_encoder_args(crf),
            "-c:a", "aac", "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            str(output_path)
        ]

    # CASE 3: Audio is significantly longer (> 20% of video)
    # Apply Symmetric Ping-Pong Loop (Forward -> Reverse -> Forward)
    else:
        total_pp_frames = max(30, int(round(2 * v_dur * fps)))
        print(f"[AUDIO_VISUAL_LOCK] Case 3 (Ping-Pong): Seamless looping {v_dur:.2f}s video to cover {target_dur:.2f}s speech.", flush=True)
        filter_pp = (
            f"[0:v]fps={fps},split[fwd][rev_in];"
            f"[rev_in]reverse[rev];"
            f"[fwd][rev]concat=n=2:v=1:a=0[pp];"
            f"[pp]loop=loop=-1:size={total_pp_frames}:start=0[v]"
        )
        cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-filter_complex", filter_pp,
            "-map", "[v]",
            "-map", "1:a",
            "-t", f"{target_dur:.3f}",
            *_get_encoder_args(crf),
            "-c:a", "aac", "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            str(output_path)
        ]

    try:
        res = subprocess.run(
            cmd, capture_output=True, text=True,
            encoding="utf-8", errors="replace", check=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
        )
        if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            final_dur = ffprobe_duration(output_path)
            print(f"[AUDIO_VISUAL_LOCK] Successfully locked video duration: {final_dur:.2f}s -> {output_path}", flush=True)
            return output_path
        else:
            return f"Error: Output file not created or empty: {output_path}"
    except subprocess.CalledProcessError as e:
        err_msg = e.stderr[-300:] if e.stderr else str(e)
        print(f"[AUDIO_VISUAL_LOCK] FFmpeg error: {err_msg}", flush=True)
        return f"Error in lock_video_to_audio_duration: {err_msg}"
