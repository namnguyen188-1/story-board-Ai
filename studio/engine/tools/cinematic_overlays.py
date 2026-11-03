"""
Cinematic Multi-Layer Overlay Engine (Milestone 4).
Applies seamless 3D atmospheric particle loops (golden dust motes, fire embers, smoke)
and authentic 35mm organic film grain to eliminate the flat AI plastic look.
"""
import os
import subprocess
from pathlib import Path
from typing import Optional, Tuple
from .video_audio_lock import ffprobe_duration

OVERLAYS_DIR = Path(__file__).resolve().parent.parent / "assets" / "overlays"

# Genre to atmospheric particle mapping
GENRE_OVERLAY_PRESETS = {
    "stoic": ("dust_particles.mp4", 0.22, 10),
    "philosophy": ("dust_particles.mp4", 0.22, 10),
    "history": ("vintage_film.mp4", 0.24, 14),
    "documentary": ("dust_particles.mp4", 0.20, 9),
    "mafia_thriller": ("cinematic_smoke.mp4", 0.25, 12),
    "psychological_horror": ("cinematic_smoke.mp4", 0.28, 14),
    "action": ("fire_embers.mp4", 0.32, 11),
    "western": ("dust_particles.mp4", 0.25, 12),
    "romance_melodrama": ("sun_rays.mp4", 0.24, 8),
    "family_drama": ("dust_particles.mp4", 0.18, 8),
    "animation": ("sun_rays.mp4", 0.16, 5),
    "whiteboard": ("none", 0.0, 0),
}


def resolve_overlay_for_genre(
    genre: str = "stoic",
    overlay_type: str = "auto"
) -> Tuple[Optional[Path], float, int]:
    """
    Resolves the overlay file, screen blend opacity, and film grain intensity.
    Returns: (overlay_path, opacity, grain_strength)
    """
    g = str(genre or "stoic").lower().strip()
    ov = str(overlay_type or "auto").lower().strip()

    preset = GENRE_OVERLAY_PRESETS.get(g, GENRE_OVERLAY_PRESETS["stoic"])
    chosen_file, default_opacity, default_grain = preset

    if ov != "auto" and ov != "none":
        cand = OVERLAYS_DIR / f"{ov}.mp4"
        if cand.is_file():
            chosen_file = cand.name
    elif ov == "none":
        return None, 0.0, default_grain

    if chosen_file == "none":
        return None, 0.0, 0

    target_path = OVERLAYS_DIR / chosen_file
    if not target_path.is_file():
        dust = OVERLAYS_DIR / "dust_particles.mp4"
        if dust.is_file():
            return dust, 0.22, default_grain
        return None, 0.0, default_grain

    return target_path, default_opacity, default_grain


def apply_cinematic_overlays(
    video_path: str,
    output_path: str,
    genre: str = "stoic",
    overlay_type: str = "auto",
    enable_grain: bool = True,
    width: int = 1280,
    height: int = 720
) -> str:
    """
    Applies multi-layer cinematic treatment:
    Layer 1: Base Video
    Layer 2: Atmospheric Floating Particle Overlay (Screen Blend, shortest=1)
    Layer 3: 35mm Organic Film Grain (Procedural noise + contrast)
    """
    if not os.path.exists(video_path):
        return f"Error: Video not found at {video_path}"

    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    v_dur = ffprobe_duration(video_path)
    if v_dur <= 0.05:
        v_dur = 5.0

    overlay_path, opacity, grain_strength = resolve_overlay_for_genre(genre, overlay_type)

    # Check if whiteboard genre (skip overlays for clean aesthetic)
    if genre.lower() == "whiteboard":
        import shutil
        if os.path.abspath(video_path) != os.path.abspath(output_path):
            shutil.copy2(video_path, output_path)
        return output_path

    grain_filter = f"noise=alls={grain_strength}:allf=t+u,eq=contrast=1.03:saturation=1.04" if (enable_grain and grain_strength > 0) else "null"

    if overlay_path and overlay_path.is_file():
        print(f"[CINEMATIC_FX] Applying Layer 2 ({overlay_path.name}, opacity={opacity:.2f}) & Layer 3 (35mm Grain={grain_strength}) for {v_dur:.2f}s...", flush=True)
        filter_complex = (
            f"[0:v]scale={width}:{height},format=gbrp[base];"
            f"[1:v]scale={width}:{height},format=gbrp[ovl];"
            f"[base][ovl]blend=all_mode='screen':all_opacity={opacity:.2f}:shortest=1,format=yuv420p,{grain_filter}[vout]"
        )
        cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(video_path),
            "-stream_loop", "-1", "-i", str(overlay_path),
            "-filter_complex", filter_complex,
            "-map", "[vout]",
            "-map", "0:a?",
            "-t", f"{v_dur:.3f}",
            "-c:a", "copy",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
            "-pix_fmt", "yuv420p",
            str(output_path)
        ]
    else:
        print(f"[CINEMATIC_FX] Applying Layer 3 (35mm Film Grain={grain_strength}) for {v_dur:.2f}s...", flush=True)
        filter_vf = f"scale={width}:{height},{grain_filter}"
        cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(video_path),
            "-vf", filter_vf,
            "-map", "0:v",
            "-map", "0:a?",
            "-t", f"{v_dur:.3f}",
            "-c:a", "copy",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
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
            print(f"[CINEMATIC_FX] Successfully rendered cinematic treatment: {output_path}", flush=True)
            return output_path
        else:
            return f"Error: Output file not created: {output_path}"
    except subprocess.CalledProcessError as e:
        err_msg = e.stderr[-250:] if e.stderr else str(e)
        print(f"[CINEMATIC_FX] Warning FFmpeg error: {err_msg}", flush=True)
        import shutil
        if os.path.abspath(video_path) != os.path.abspath(output_path):
            shutil.copy2(video_path, output_path)
        return output_path
