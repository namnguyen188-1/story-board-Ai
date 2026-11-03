"""
Merge Audio Video Tool - Synchronizes audio and video tracks using 1:1 Audio-Visual Locking.
Guarantees continuous motion, eliminates frozen frames, and trims dead air.
"""
import os
import subprocess
import json
from .video_audio_lock import lock_video_to_audio_duration, ffprobe_duration

def get_duration(file_path):
    """Get duration of a file in seconds using ffprobe."""
    return ffprobe_duration(file_path)

def merge_audio_video_tool_fn(video_path: str, audio_path: str, output_path: str = "output.mp4") -> str:
    """
    Merges audio and video files with 1:1 frame-accurate kinetic synchronization.
    If video >= audio: trims dead air.
    If audio slightly longer (<=20%): applies Cinematic Slow-Mo.
    If audio much longer (>20%): applies Symmetric Ping-Pong continuous motion.
    
    Args:
        video_path: Path to the input video file.
        audio_path: Path to the input audio file.
        output_path: Path for the merged output file.
        
    Returns:
        Path to the output file if successful, or error message.
    """
    return lock_video_to_audio_duration(
        video_path=video_path,
        audio_path=audio_path,
        output_path=output_path
    )
