"""Local full-color cinematic scene animation with dynamic camera motion and atmospheric particle overlays.
Supports:
- Dynamic Camera Movements:
    * zoom_in: Smooth cinematic push-in towards subject
    * zoom_out: Smooth pull-out revealing grand scale
    * pan_right: Smooth horizontal glide left to right
    * pan_left: Smooth horizontal glide right to left
    * tilt_up: Smooth vertical pedestal from base to subject's head
    * orbit_drift: Subtle parallax rotational orbit drift (xoay quanh / thị sai)
- Atmospheric Particle Overlays:
    * dust_particles: Cinematic golden/warm bokeh dust motes (bụi bay)
    * cinematic_smoke: Volumetric drifting fog and smoke wisps (khói bụi)
    * falling_snow: Gentle fluttering snowflakes (tuyết rơi)
    * none: Direct camera motion without overlay
"""
from __future__ import annotations
import subprocess, wave, math, os, re
import threading, functools
from pathlib import Path
from PIL import Image, ImageOps

ENGINE_DIR = Path(__file__).resolve().parent / "engine"
OVERLAYS_DIR = ENGINE_DIR / "assets" / "overlays"

# Ordered cinematic motions for dynamic per-scene variation (Hollywood Camera Language)
CINEMATIC_MOTIONS = [
    "zoom_in",
    "pan_right",
    "orbit_drift",
    "zoom_out",
    "crane_reveal",
    "tilt_up",
    "pan_left",
    "dolly_zoom",
    "macro_drift"
]


def create_silence(destination, seconds=8):
    seconds = max(1, min(60, float(seconds)))
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(target), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(24000)
        for _ in range(math.ceil(seconds)):
            n = min(24000, int(seconds * 24000) - w.getnframes())
            if n > 0:
                w.writeframes(b"\0\0" * n)
    return str(target)


def get_camera_motion_filter(motion_type: str, frames: int, width: int, height: int, fps: int, duration_sec: float) -> str:
    """Builds mathematically precise, smooth Ken Burns & 3D compound camera movements
    with cosine ease-in/ease-out acceleration (Hollywood documentary standard).
    """
    f_total = max(1, frames)
    d_sec = max(0.5, duration_sec)
    
    # Cosine smoothstep easing: zero acceleration at start and finish, peak velocity in the middle
    ease = f"(0.5*(1-cos(PI*on/{f_total})))"
    
    if motion_type == "zoom_in":
        # Smooth push-in towards Golden Ratio eye line (from 1.0 to 1.20)
        return (
            f"zoompan=z='1.0+0.20*{ease}':"
            f"x='(iw-iw/zoom)*0.50':"
            f"y='(ih-ih/zoom)*(0.38+0.12*{ease})':"
            f"d={f_total}:s={width}x{height}:fps={fps}"
        )
    elif motion_type == "zoom_out":
        # Smooth pull-back revealing grand environmental scale (from 1.20 to 1.0)
        return (
            f"zoompan=z='1.20-0.20*{ease}':"
            f"x='(iw-iw/zoom)*0.50':"
            f"y='(ih-ih/zoom)*(0.50-0.12*{ease})':"
            f"d={f_total}:s={width}x{height}:fps={fps}"
        )
    elif motion_type == "pan_right":
        # Smooth horizontal tracking glide left-to-right with subtle depth push
        return (
            f"zoompan=z='1.15':"
            f"x='(iw-iw/zoom)*{ease}':"
            f"y='(ih-ih/zoom)*0.45':"
            f"d={f_total}:s={width}x{height}:fps={fps}"
        )
    elif motion_type == "pan_left":
        # Smooth horizontal tracking glide right-to-left
        return (
            f"zoompan=z='1.15':"
            f"x='(iw-iw/zoom)*(1.0-{ease})':"
            f"y='(ih-ih/zoom)*0.45':"
            f"d={f_total}:s={width}x{height}:fps={fps}"
        )
    elif motion_type == "tilt_up":
        # Vertical pedestal reveal moving from waist/base to subject's eyes
        return (
            f"zoompan=z='1.15':"
            f"x='(iw-iw/zoom)*0.50':"
            f"y='(ih-ih/zoom)*(0.80-0.45*{ease})':"
            f"d={f_total}:s={width}x{height}:fps={fps}"
        )
    elif motion_type == "orbit_drift":
        # Orbital parallax camera drift: elliptical (x,y) orbit combined with subtle rotational sway
        return (
            f"zoompan=z='1.12+0.08*{ease}':"
            f"x='(iw-iw/zoom)*(0.50+0.35*sin(2*PI*(on/{f_total})*0.8))':"
            f"y='(ih-ih/zoom)*(0.50+0.35*cos(2*PI*(on/{f_total})*0.8))':"
            f"d={f_total}:s={width}x{height}:fps={fps},"
            f"rotate='0.005*sin(2*PI*t/{d_sec})':ow='{width}':oh='{height}':c=black"
        )
    elif motion_type == "crane_reveal":
        # Technocrane compound move: diagonal lift + horizontal glide + gentle pull
        return (
            f"zoompan=z='1.18-0.12*{ease}':"
            f"x='(iw-iw/zoom)*(0.20+0.60*{ease})':"
            f"y='(ih-ih/zoom)*(0.75-0.45*{ease})':"
            f"d={f_total}:s={width}x{height}:fps={fps}"
        )
    elif motion_type == "dolly_zoom":
        # Vertigo / Dolly Zoom: push-pull perspective shift
        return (
            f"zoompan=z='1.05+0.18*{ease}':"
            f"x='(iw-iw/zoom)*(0.30+0.40*{ease})':"
            f"y='(ih-ih/zoom)*(0.40-0.10*{ease})':"
            f"d={f_total}:s={width}x{height}:fps={fps}"
        )
    elif motion_type == "macro_drift":
        # Ultra-slow inspection scan across maps, relics, and archival documents
        return (
            f"zoompan=z='1.25':"
            f"x='(iw-iw/zoom)*(0.15+0.70*{ease})':"
            f"y='(ih-ih/zoom)*(0.30+0.40*{ease})':"
            f"d={f_total}:s={width}x{height}:fps={fps}"
        )
    else:
        # Default smooth cinematic push
        return (
            f"zoompan=z='1.0+0.15*{ease}':"
            f"x='(iw-iw/zoom)*0.50':"
            f"y='(ih-ih/zoom)*(0.45+0.05*{ease})':"
            f"d={f_total}:s={width}x{height}:fps={fps}"
        )


INDOOR_ENV_PATTERN = r"(indoor|indoors|inside|interior|room|office|shop|store|counter|desk|table|stationery|copier|photocopier|hallway|corridor|bedroom|living room|kitchen|bathroom|apartment|house|home|classroom|studio|restaurant|cafe|bar|elevator|lobby|hospital|clinic|courtroom|prison cell|library|hotel room|trong nhà|trong phòng|văn phòng|quầy|bàn làm việc|tiệm|cửa hàng|phòng khách|phòng ngủ|nhà bếp|hành lang|lớp học|quán cafe|nhà hàng)"
OUTDOOR_ENV_PATTERN = r"(outdoor|outdoors|outside|exterior|street|road|avenue|highway|park|forest|mountain|field|beach|ocean|sea|sky|bus terminal|bus stop|station exterior|parking lot|courtyard|patio|garden|rooftop|alley|square|ngoài trời|đường phố|con đường|vỉa hè|công viên|khu rừng|núi|cánh đồng|bãi biển|bến xe|trạm xe|sân ga|bãi đỗ xe|sân thượng|sân vườn)"
SUNNY_LIGHT_PATTERN = r"(sunny|sunlight|sunshine|bright daylight|sun rays|clear blue sky|golden hour|sunset|sunrise|dawn|nắng|ánh nắng|nắng gắt|trưa nắng|nắng chói|buổi sáng nắng|hoàng hôn|bình minh)"
RAIN_WEATHER_PATTERN = r"(heavy rain|raining|downpour|drizzle|thunderstorm|rainstorm|lightning storm|mưa|mưa rào|mưa bão|sấm chớp|giông bão|mưa phùn)"
SNOW_WEATHER_PATTERN = r"(heavy snow|snowing|snowfall|blizzard|snow storm|frosty winter|ice storm|frozen lake|tuyết|tuyết rơi|bão tuyết|mùa đông giá rét|băng tuyết|phủ tuyết)"
FIRE_HEAT_PATTERN = r"(burning fire|bonfire|campfire|fireplace|flames|house fire|explosion|battlefield|warzone|ngọn lửa|đám cháy|bốc cháy|lò sưởi|đống lửa|tàn tro)"
SMOKE_MIST_PATTERN = r"(dense smoke|thick fog|misty morning|smoky room|foggy forest|sương mù|khói lửa|sương dày|mờ sương|hơi nước dày)"
VINTAGE_ARCHIVE_PATTERN = r"(vintage film|black and white|1920s|1930s|1940s|1950s|1960s|1970s|1980s|sepia tone|old archival footage|thời bao cấp|phim tài liệu cũ|thế kỷ trước)"


def resolve_atmospheric_overlay(overlay_effect: str, genre: str, scene_index: int,
                                scene_text: str = "") -> tuple[Path | None, float]:
    """Selects the atmospheric particle overlay file and blending opacity.
    Intelligently analyzes scene physical environment (indoor vs. outdoor),
    weather, lighting, and genre to ensure believable physical continuity.
    - Never rain or snow inside indoor rooms/offices/shops.
    - Never snow in bright sunny daylight.
    - Clean by default for indoor dialogue and everyday dramatic scenes.
    """
    effect = str(overlay_effect or "auto").lower().strip()
    g = str(genre or "documentary").lower().strip()
    st = str(scene_text or "")
    st_l = st.lower()
    
    if effect in ("none", "off", "disabled"):
        return None, 0.0
    
    if effect == "auto":
        is_indoor = bool(re.search(INDOOR_ENV_PATTERN, st_l, re.IGNORECASE))
        is_outdoor = bool(re.search(OUTDOOR_ENV_PATTERN, st_l, re.IGNORECASE))
        is_sunny = bool(re.search(SUNNY_LIGHT_PATTERN, st_l, re.IGNORECASE))
        is_rain = bool(re.search(RAIN_WEATHER_PATTERN, st_l, re.IGNORECASE))
        is_snow = bool(re.search(SNOW_WEATHER_PATTERN, st_l, re.IGNORECASE))
        is_fire = bool(re.search(FIRE_HEAT_PATTERN, st_l, re.IGNORECASE))
        is_smoke = bool(re.search(SMOKE_MIST_PATTERN, st_l, re.IGNORECASE))
        is_vintage = bool(re.search(VINTAGE_ARCHIVE_PATTERN, st_l, re.IGNORECASE))

        # PHYSICAL CONTINUITY GUARDS:
        # 1. Never rain or snow indoors (inside rooms, offices, shops, counters, houses)
        if is_indoor and not is_outdoor:
            is_snow = False
            is_rain = False

        # 2. Never snow in bright sunny daylight
        if is_sunny and not is_rain:
            is_snow = False

        # 3. Fire embers indoors only if explicit fireplace or house fire
        if is_indoor and not is_outdoor and not any(w in st_l for w in ("fireplace", "lò sưởi", "đám cháy", "house fire")):
            is_fire = False

        if is_snow:
            chosen = "falling_snow"
        elif is_rain:
            chosen = "cinematic_rain"
        elif is_fire:
            chosen = "fire_embers"
        elif is_smoke:
            chosen = "cinematic_smoke"
        elif is_sunny and is_outdoor:
            chosen = "sun_rays"
        elif is_vintage:
            chosen = "vintage_film"
        elif is_indoor:
            # Clean indoor rooms! No distracting snow/rain/sparks
            chosen = "none"
        else:
            # General outdoor scenes fallback
            if g in ("history", "stoic", "documentary"):
                chosen = "vintage_film" if (scene_index % 3 == 1) else ("dust_particles" if (scene_index % 3 == 2) else "none")
            elif g in ("horror", "thriller", "mystery"):
                chosen = "cinematic_smoke" if (scene_index % 2 == 1) else "none"
            elif g in ("war", "western"):
                chosen = "cinematic_smoke" if (scene_index % 2 == 1) else "none"
            else:
                chosen = "dust_particles" if (scene_index % 3 == 1) else "none"
    else:
        chosen = effect

    if chosen == "none":
        return None, 0.0

    target_file = OVERLAYS_DIR / f"{chosen}.mp4"
    if not target_file.is_file():
        dust_fallback = OVERLAYS_DIR / "dust_particles.mp4"
        if dust_fallback.is_file():
            target_file = dust_fallback
            chosen = "dust_particles"
        else:
            return None, 0.0

    opacity_map = {
        "dust_particles": 0.28,
        "cinematic_smoke": 0.32,
        "falling_snow": 0.45,
        "cinematic_rain": 0.45,
        "fire_embers": 0.45,
        "vintage_film": 0.28,
        "sun_rays": 0.35,
    }
    opacity = opacity_map.get(chosen, 0.30)
    return target_file, opacity


# Balanced renderer: bound CPU-heavy software filters and use dedicated NVENC
# hardware for final H264 encoding. CPU fallback is always supported.
_RENDER_SLOTS = threading.BoundedSemaphore(
    max(1, min(4, int(os.environ.get("STORYBOARD_RENDER_SLOTS", "2"))))
)
_CPU_ARGS = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20"]
_GPU_ARGS = ["-c:v", "h264_nvenc", "-preset", "p4",
             "-rc", "vbr", "-cq", "21", "-b:v", "0"]


@functools.lru_cache(maxsize=1)
def _hardware_encoder_usable() -> bool:
    """Test actual NVENC capability, not merely listed encoders."""
    if os.environ.get("STORYBOARD_VIDEO_ENCODER", "auto").lower() in ("cpu", "off", "software"):
        return False
    probe = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi",
             "-i", "color=c=black:s=256x144:r=2", "-frames:v", "2",
             "-c:v", "h264_nvenc", "-f", "null", "-"]
    try:
        result = subprocess.run(
            probe, capture_output=True, timeout=15,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return result.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def _replace_encoder_args(command, before, after):
    for i in range(len(command) - len(before) + 1):
        if command[i:i+len(before)] == before:
            return command[:i] + after + command[i+len(before):]
    raise ValueError("Encoder arguments not found")


def color_video(image, audio, output, width, height, fps=25,
                scene_index=1, motion_type="auto", overlay_effect="auto", genre="documentary",
                scene_text: str = ""):
    from series_studio import ffprobe
    image = Path(image)
    audio = Path(audio)
    output = Path(output)
    
    with wave.open(str(audio), "rb") as f:
        seconds = f.getnframes() / max(1, f.getframerate())
    frames = max(1, math.ceil(seconds * fps))

    # Fit source image to target canvas filling 100% of the screen (no black bars, no shrinking)
    # Oversample to 1.5x canvas size so zoompan maintains razor-sharp native pixel density at peak zoom
    inp = output.parent / f"color_source_{scene_index:04d}_16x9.png"
    with Image.open(image) as original:
        orig_rgb = original.convert("RGB")
        target_w = int(width * 1.5)
        target_h = int(height * 1.5)
        rgb = ImageOps.fit(orig_rgb, (target_w, target_h), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        rgb.save(inp, "PNG")
    job_file = output.parent / "job.json"
    is_comfy = False
    if job_file.is_file():
        try:
            import json as _json
            jdata = _json.loads(job_file.read_text(encoding="utf-8"))
            if jdata.get("image_provider") in ("comfyui", "muse_video"):
                is_comfy = True
        except Exception:
            pass

    if not is_comfy and str(genre).lower() not in ("stoic", "philosophy"):
        try:
            from clean_watermark import remove_gemini_watermark
            remove_gemini_watermark(inp)
        except Exception:
            pass

    # Resolve camera motion
    m_type = str(motion_type or "auto").lower().strip()
    if m_type == "auto":
        m_type = CINEMATIC_MOTIONS[(int(scene_index) - 1) % len(CINEMATIC_MOTIONS)]
    
    camera_vf = get_camera_motion_filter(m_type, frames, width, height, fps, seconds)

    # Resolve atmospheric particle overlay with smart scene content matching
    overlay_path, overlay_opacity = resolve_atmospheric_overlay(
        overlay_effect, genre, int(scene_index), scene_text=scene_text
    )

    gpu_enabled = _hardware_encoder_usable()

    if overlay_path and overlay_path.is_file():
        # Composite dynamic camera motion with seamless looping particle overlay using screen blend
        filter_complex = (
            f"[0:v]{camera_vf},format=gbrp[base];"
            f"[1:v]scale={width}:{height},format=gbrp[ovl];"
            f"[base][ovl]blend=all_mode='screen':all_opacity={overlay_opacity:.2f},format=yuv420p[vout]"
        )
        cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-filter_threads", "2", "-filter_complex_threads", "2",
            "-loop", "1", "-framerate", str(fps), "-i", str(inp),
            "-stream_loop", "-1", "-i", str(overlay_path),
            "-filter_complex", filter_complex,
            "-map", "[vout]",
            "-frames:v", str(frames), "-an",
            *(_GPU_ARGS if gpu_enabled else _CPU_ARGS),
            "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            str(output)
        ]
    else:
        # Direct camera motion without overlay
        cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-filter_threads", "2", "-filter_complex_threads", "2",
            "-loop", "1", "-framerate", str(fps), "-i", str(inp),
            "-vf", f"{camera_vf},format=yuv420p",
            "-frames:v", str(frames), "-an",
            *(_GPU_ARGS if gpu_enabled else _CPU_ARGS),
            "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            str(output)
        ]

    # Do not change sources or active plans. Bound simultaneous costly filters.
    with _RENDER_SLOTS:
        r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           text=True, encoding="utf-8", errors="replace",
                           timeout=max(120, min(1800, int(seconds * 20))),
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if r.returncode and gpu_enabled:
            # Non-destructive fallback if NVENC fails due to driver/session limits.
            cmd = _replace_encoder_args(cmd, _GPU_ARGS, _CPU_ARGS)
            print("[RENDER_ACCEL] NVENC failed, retrying CPU codec", flush=True)
            r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, encoding="utf-8", errors="replace",
                               timeout=max(120, min(1800, int(seconds * 20))),
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if r.returncode:
        raise RuntimeError("Color scene ffmpeg failed: " + r.stderr[-350:])
        
    _, actual = ffprobe(output)
    if actual < seconds - 0.3 or actual > seconds + 0.5:
        raise RuntimeError("Color video duration QC failed")
        
    return str(output)
