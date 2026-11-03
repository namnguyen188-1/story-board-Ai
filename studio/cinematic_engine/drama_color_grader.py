"""
Cinematic Drama Color Grader & Dynamic Range Normalizer.
Provides Hollywood-grade color grading, shadow pedestal lifting,
and automatic exposure compensation for AI-generated drama footage.
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None
    np = None


def analyze_video_luminance(video_path: Path | str, sample_frames: int = 20) -> Dict[str, float]:
    """Analyzes the brightness and contrast distribution of a video by sampling keyframes."""
    v_path = Path(video_path)
    if not v_path.is_file():
        return {"mean_luminance": 50.0, "contrast_std": 30.0, "is_dark": False}

    if cv2 is None or np is None:
        # Fallback if cv2 is not available in main process
        return {"mean_luminance": 40.0, "contrast_std": 30.0, "is_dark": True}

    cap = cv2.VideoCapture(str(v_path.resolve()))
    if not cap.isOpened():
        return {"mean_luminance": 50.0, "contrast_std": 30.0, "is_dark": False}

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames <= 0:
        cap.release()
        return {"mean_luminance": 50.0, "contrast_std": 30.0, "is_dark": False}

    step = max(1, total_frames // max(sample_frames, 1))
    means = []
    stds = []
    shadow_clips = []  # pixels < 8

    for idx in range(0, total_frames, step):
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if not ret or frame is None:
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        means.append(float(np.mean(gray)))
        stds.append(float(np.std(gray)))
        shadow_clips.append(float(np.mean(gray < 8)))

    cap.release()

    if not means:
        return {"mean_luminance": 50.0, "contrast_std": 30.0, "is_dark": False}

    avg_mean = float(np.mean(means))
    avg_std = float(np.mean(stds))
    avg_shadow_clip = float(np.mean(shadow_clips))

    is_dark = (avg_mean < 42.0) or (avg_shadow_clip > 0.40 and avg_mean < 55.0)

    return {
        "mean_luminance": round(avg_mean, 2),
        "contrast_std": round(avg_std, 2),
        "shadow_clip_ratio": round(avg_shadow_clip, 3),
        "is_dark": is_dark,
    }


def build_cinematic_filter_chain(
    stats: Dict[str, Any],
    genre: str = "drama",
    boost_level: str = "auto"
) -> str:
    """Builds an optimal FFmpeg video filter chain based on luminance analysis and genre.
    
    Hollywood Techniques:
    - Shadow Pedestal Lift: curves=all='0/0.05 0.2/0.28 0.5/0.58 0.8/0.88 1/1'
      Converts dead pitch-black (0) into deep cinematic sapphire/navy shadows (13-20),
      revealing all creature and character details without washing out the image.
    - S-Curve Contrast & Saturation Boost:
      Pushes midtones up while maintaining punchy highlights, making bioluminescent
      cyans, emerald greens, and warm amber accents pop electrifyingly.
    - Unsharp Clarity:
      Crisps up edges (scales, eyes, teeth, fabric textures) for 8k documentary feel.
    """
    mean_lum = stats.get("mean_luminance", 50.0)
    is_dark = stats.get("is_dark", False)

    if boost_level == "force_dark" or (boost_level == "auto" and is_dark):
        # Deep ocean / night-for-night / dark mystery grade
        if mean_lum < 25.0:
            # Extreme darkness (like deep bathypelagic abyss)
            # Heavy midtone lift + rich shadow pedestal + vivid bioluminescent saturation
            return (
                "eq=contrast=1.32:brightness=0.08:saturation=1.45:gamma=1.45,"
                "curves=all='0/0.05 0.20/0.32 0.50/0.62 0.80/0.89 1/1',"
                "unsharp=5:5:0.7:5:5:0.0"
            )
        else:
            # Moderate darkness
            return (
                "eq=contrast=1.28:brightness=0.06:saturation=1.38:gamma=1.32,"
                "curves=all='0/0.04 0.25/0.32 0.50/0.58 0.85/0.90 1/1',"
                "unsharp=5:5:0.6:5:5:0.0"
            )
    else:
        # Standard daylight / well-lit cinema grade
        # Subtle cinema contrast S-curve + color richness + slight clarity
        return (
            "eq=contrast=1.12:brightness=0.02:saturation=1.18:gamma=1.06,"
            "curves=all='0/0.01 0.50/0.52 1/1',"
            "unsharp=5:5:0.5:5:5:0.0"
        )


def grade_video_cinematic(
    input_video_path: Path | str,
    output_video_path: Optional[Path | str] = None,
    genre: str = "drama",
    force: bool = False
) -> Path:
    """Applies automated Hollywood color grading, exposure compensation,
    and dynamic range normalization to a video.
    """
    in_path = Path(input_video_path)
    if not in_path.is_file():
        raise FileNotFoundError(f"Input video not found: {in_path}")

    if output_video_path is None:
        out_path = in_path.parent / f"{in_path.stem}_graded{in_path.suffix}"
    else:
        out_path = Path(output_video_path)

    out_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Analyze video luminance
    stats = analyze_video_luminance(in_path)
    print(f"[COLOR_GRADE] Video luminance analysis for {in_path.name}: "
          f"mean={stats['mean_luminance']}/255, contrast={stats['contrast_std']}, "
          f"shadow_clip={stats['shadow_clip_ratio']*100:.1f}%, is_dark={stats['is_dark']}",
          flush=True)

    # If already bright and not forced, we can skip heavy re-encoding
    if not stats["is_dark"] and not force and stats["mean_luminance"] > 60.0:
        print(f"[COLOR_GRADE] Video has excellent natural exposure (mean={stats['mean_luminance']}). Preserving original.", flush=True)
        if in_path.resolve() != out_path.resolve():
            shutil.copy2(str(in_path), str(out_path))
        return out_path

    # 2. Build filter chain
    vf = build_cinematic_filter_chain(stats, genre=genre)
    print(f"[COLOR_GRADE] Applying Hollywood Master Color Grade: {vf}", flush=True)

    # 3. Render with FFmpeg (fast preset, maintain original audio)
    tmp_out = out_path.parent / f"tmp_grading_{out_path.name}"
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(in_path.resolve()),
        "-vf", vf,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        str(tmp_out.resolve())
    ]

    try:
        subprocess.run(cmd, check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if out_path.exists():
            out_path.unlink()
        tmp_out.rename(out_path)
        print(f"[COLOR_GRADE_SUCCESS] Successfully graded video: {out_path} ({out_path.stat().st_size / 1024 / 1024:.2f} MB)", flush=True)
        return out_path
    except Exception as err:
        if tmp_out.exists():
            try:
                tmp_out.unlink()
            except Exception:
                pass
        print(f"[COLOR_GRADE_ERROR] Failed to grade video: {err}. Falling back to original.", flush=True)
        if in_path.resolve() != out_path.resolve():
            shutil.copy2(str(in_path), str(out_path))
        return out_path
