"""Storyboard Studio - Google Flow AI Motion Video (Veo 3.1 / Omni 1.1 Flash).

Converts scenes and keyframe images into animated AI motion videos via Google Flow.
Includes Image-to-Video continuity (preserving character DNA & scenery),
Seamless Ping-Pong loop & slow-motion adaptation, Multi-Account CDP failover pool,
Atmospheric VFX particle overlays, Foley Soundscape environmental audio mixing,
and graceful fallback to Ken Burns camera motion.
"""
from __future__ import annotations
import os
import shutil
import subprocess
import json
import time
import re
from pathlib import Path

from studio_mcp.video_backend import StoryboardVideoBackend, VIDEO_MODELS, DEFAULT_VIDEO_MODEL, StoryboardVideoError
from mcp_v2_batch import sanitize_statue_terms

def video_motion_prompt(scene: dict, bible: dict) -> str:
    """Generate a prompt optimized for continuous camera and subject motion."""
    genre = bible.get("production_genre", "whiteboard")
    desc = sanitize_statue_terms(str(scene.get("description", "")))
    setup = sanitize_statue_terms(str(scene.get("visual_setup", "")))
    world = str(bible.get("world", ""))[:250]
    art_style = str(bible.get("visual_style", "Cinematic 3D animation"))[:300]
    
    # Motion directions based on scene setup
    motion_cues = []
    setup_lower = setup.lower()
    if "pan" in setup_lower or "move" in setup_lower:
        motion_cues.append("Continuous smooth camera tracking.")
    elif "zoom" in setup_lower or "push" in setup_lower:
        motion_cues.append("Slow cinematic camera push-in.")
    else:
        motion_cues.append("Subtle cinematic camera motion with dynamic atmospheric depth.")

    motion_cues.append("Natural lifelike character movement, expressive posture changes, ambient dust and lighting drift.")

    # Master Character DNA Locking
    char_dna = []
    for c in bible.get("characters", []):
        if isinstance(c, dict):
            c_name = c.get("name", "").strip()
            c_app = c.get("appearance", "").strip()
            c_attire = c.get("attire", "").strip()
            c_rules = c.get("immutable_rules", "").strip()
            details = ", ".join(filter(None, [c_name, c_app, c_attire, c_rules]))
            if details:
                char_dna.append(details)
    
    dna_part = f"CHARACTER DNA CONTINUITY: Maintain exact facial features, hair, eyes, and clothing of {'; '.join(char_dna[:2])}." if char_dna else ""

    prompt_parts = [
        f"Cinematic video clip, continuous motion, high production quality.",
        f"SCENE ACTION: {desc}.",
        f"COMPOSITION & MOVEMENT: {setup}. {' '.join(motion_cues)}",
        f"ATMOSPHERE: {world}.",
        f"STYLE: {art_style}.",
    ]
    if dna_part:
        prompt_parts.append(dna_part)
        
    prompt_parts.append("Strict rule: Continuous fluid motion, no sudden cuts, no jump cuts, preserve facial identity, no text overlays, no watermarks, no stickers, no logos, no channel bugs, no commercial labels, no captions, no floating artifacts.")
    return " ".join(prompt_parts)[:3800]


def adapt_video_clip_to_audio(
    video_path: Path,
    audio_path: Path,
    output_silent_mp4: Path,
    width: int = 1280,
    height: int = 720,
    fallback_seconds: float = 8.0,
) -> bool:
    """Adapts an AI motion video clip (Veo 3.1 / Omni 1.1) to match scene audio duration.
    
    - Seamless Ping-Pong: Forward -> Reverse -> Forward with continuous boundary frames, eliminating jump cuts.
    - Gentle Slow-Motion (time-stretching) for minor audio extensions (<= 25%) without any loop or reversal.
    - Trims or adjusts speed cleanly if video clip is longer than audio.
    - Scales/pads to exact resolution (16:9 or 9:16) and strips audio (-an).
    """
    if not video_path.is_file() or video_path.stat().st_size < 1024:
        return False
    try:
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        a_dur = float(fallback_seconds)
        if audio_path.is_file() and audio_path.stat().st_size > 100:
            try:
                probe_a = subprocess.run(
                    ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(audio_path)],
                    capture_output=True, text=True, check=True, creationflags=flags
                )
                a_dur = float(json.loads(probe_a.stdout)["format"]["duration"])
            except Exception:
                pass

        probe_v = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(video_path)],
            capture_output=True, text=True, check=True, creationflags=flags
        )
        v_dur = float(json.loads(probe_v.stdout)["format"]["duration"])

        scale_pad = f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1"
        tmp_out = output_silent_mp4.parent / f"temp_adapt_{output_silent_mp4.name}"

        # Strategy 1: Audio is slightly longer than video (<= 1.25x)
        # Apply cinematic slow-motion time stretch: 0 cuts, 0 loops, beautiful fluid drift!
        if v_dur < a_dur <= v_dur * 1.25:
            speed_ratio = a_dur / max(0.1, v_dur)
            vf = f"setpts={speed_ratio:.6f}*PTS,{scale_pad}"
            cmd = [
                "ffmpeg", "-y",
                "-i", str(video_path),
                "-t", f"{a_dur:.3f}",
                "-vf", vf,
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-an", str(tmp_out)
            ]

        # Strategy 2: Audio is significantly longer (> 1.25x)
        # Apply Seamless Ping-Pong (Forward -> Reverse -> Forward ...)
        # mathematically identical boundary frames (Frame N -> Frame N), eliminating jump cuts!
        elif a_dur > v_dur * 1.25:
            k = int(a_dur // max(0.1, v_dur)) + 1
            split_labels = "".join(f"[s{i}]" for i in range(k))
            filter_parts = [f"[0:v]split={k}{split_labels}"]
            concat_inputs = []
            for i in range(k):
                if i % 2 == 1:
                    filter_parts.append(f"[s{i}]reverse[r{i}]")
                    concat_inputs.append(f"[r{i}]")
                else:
                    concat_inputs.append(f"[s{i}]")
            concat_str = "".join(concat_inputs)
            filter_parts.append(f"{concat_str}concat=n={k}:v=1:a=0[vcat]")
            filter_parts.append(f"[vcat]{scale_pad}[out]")
            full_filter = ";".join(filter_parts)

            cmd = [
                "ffmpeg", "-y",
                "-i", str(video_path),
                "-filter_complex", full_filter,
                "-map", "[out]",
                "-t", f"{a_dur:.3f}",
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-an", str(tmp_out)
            ]

        # Strategy 3: Video is slightly longer than audio (0.8x <= a_dur < v_dur)
        # Apply gentle speed-up to fit entire motion
        elif 0.8 * v_dur <= a_dur < v_dur - 0.2:
            speed_ratio = a_dur / max(0.1, v_dur)
            vf = f"setpts={speed_ratio:.6f}*PTS,{scale_pad}"
            cmd = [
                "ffmpeg", "-y",
                "-i", str(video_path),
                "-t", f"{a_dur:.3f}",
                "-vf", vf,
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-an", str(tmp_out)
            ]

        # Strategy 4: Video is substantially longer or nearly equal
        # Clean trim to audio duration
        else:
            cmd = [
                "ffmpeg", "-y",
                "-i", str(video_path),
                "-t", f"{a_dur:.3f}",
                "-vf", scale_pad,
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-an", str(tmp_out)
            ]

        res = subprocess.run(cmd, capture_output=True, text=True, creationflags=flags)
        if res.returncode == 0 and tmp_out.is_file() and tmp_out.stat().st_size > 1024:
            try:
                from clean_watermark import remove_video_watermark
                remove_video_watermark(tmp_out, tmp_out, width=width, height=height)
            except Exception:
                pass
            shutil.move(str(tmp_out), str(output_silent_mp4))
            return True
        elif res.returncode != 0:
            print(f"[ADAPT_VIDEO_WARN] FFmpeg exit {res.returncode}: {res.stderr[:200]}", flush=True)
    except Exception as exc:
        print(f"[ADAPT_VIDEO_WARN] Lỗi xử lý clip video: {exc}", flush=True)

    try:
        shutil.copy2(video_path, output_silent_mp4)
        return True
    except Exception:
        return False


def apply_atmospheric_particle_overlay(
    video_path: Path,
    scene: dict,
    bible: dict,
    output_path: Path,
    width: int,
    height: int,
    duration: float,
) -> bool:
    """Applies atmospheric particle overlays (rain, embers, smoke, dust) onto the Flow video clip."""
    try:
        from studio_color_render import resolve_atmospheric_overlay
        scene_idx = scene.get("scene_number", 1)
        scene_text = " ".join(filter(None, [
            scene.get("prompt"), scene.get("description"), scene.get("visual_setup")
        ]))
        overlay_path, overlay_opacity = resolve_atmospheric_overlay(
            scene.get("atmospheric_overlay", "auto"),
            bible.get("production_genre", "documentary"),
            scene_idx,
            scene_text=scene_text
        )
        if not overlay_path or not overlay_path.is_file():
            return False

        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        tmp_ovl = output_path.parent / f"temp_ovl_{output_path.name}"
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-stream_loop", "-1", "-i", str(overlay_path),
            "-filter_complex",
            f"[1:v]scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}[ovl];"
            f"[0:v][ovl]blend=all_mode='screen':all_opacity={overlay_opacity:.2f},format=yuv420p[vout]",
            "-map", "[vout]",
            "-t", f"{duration:.3f}",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-an", str(tmp_ovl)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, creationflags=flags)
        if res.returncode == 0 and tmp_ovl.is_file() and tmp_ovl.stat().st_size > 1024:
            shutil.move(str(tmp_ovl), str(output_path))
            return True
    except Exception as exc:
        print(f"[FLOW_OVERLAY_WARN] Không thể phủ hiệu ứng hạt: {exc}", flush=True)
    return False


def synthesize_scene_foley_audio(scene: dict, duration: float, output_foley_wav: Path) -> bool:
    """Generates a subtle, high-fidelity ambient soundscape matched to scene physical environment."""
    text = (str(scene.get("description", "")) + " " + str(scene.get("visual_setup", "")) + " " + str(scene.get("narration", ""))).lower()
    dur = max(1.0, float(duration))
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

    # 1. Rain / Storm soundscape
    if any(k in text for k in ("rain", "mưa", "storm", "bão", "sấm", "thunder", "drizzle")):
        filter_str = f"anoisesrc=d={dur:.2f}:c=pink:r=44100,lowpass=f=2200,volume=0.08,afade=t=in:ss=0:d=0.5,afade=t=out:st={dur-0.5:.2f}:d=0.5"
    # 2. Fire / Campfire / Hearth
    elif any(k in text for k in ("fire", "lửa", "cháy", "flame", "embers", "hearth", "fireplace", "lò sưởi")):
        filter_str = f"anoisesrc=d={dur:.2f}:c=white:r=44100,bandpass=f=1200:w=800,volume=0.04,afade=t=in:ss=0:d=0.5,afade=t=out:st={dur-0.5:.2f}:d=0.5"
    # 3. Wind / Cold / Mountain / Night
    elif any(k in text for k in ("wind", "gió", "cold", "lạnh", "mountain", "đồi", "rừng", "forest")):
        filter_str = f"anoisesrc=d={dur:.2f}:c=brown:r=44100,lowpass=f=380,volume=0.10,afade=t=in:ss=0:d=0.5,afade=t=out:st={dur-0.5:.2f}:d=0.5"
    # 4. Deep Cinematic Mystery / Ancient Hall / Drone
    elif any(k in text for k in ("dark", "đêm", "night", "mystery", "bí ẩn", "temple", "đền", "ancient", "tượng", "statue")):
        filter_str = f"anoisesrc=d={dur:.2f}:c=brown:r=44100,lowpass=f=220,volume=0.08,afade=t=in:ss=0:d=0.5,afade=t=out:st={dur-0.5:.2f}:d=0.5"
    else:
        # Subtle sub-bass room tone (eliminates digital vacuum silence)
        filter_str = f"anoisesrc=d={dur:.2f}:c=brown:r=44100,lowpass=f=160,volume=0.04,afade=t=in:ss=0:d=0.5,afade=t=out:st={dur-0.5:.2f}:d=0.5"

    cmd = [
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", filter_str,
        "-c:a", "pcm_s16le",
        str(output_foley_wav)
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, creationflags=flags)
        return res.returncode == 0 and output_foley_wav.is_file() and output_foley_wav.stat().st_size > 500
    except Exception:
        return False


def mix_foley_into_scene_audio(audio_path: Path, scene: dict, output_path: Path) -> bool:
    """Blends atmospheric soundscape under the scene narration audio, preserving 100% speech clarity."""
    if not audio_path.is_file() or audio_path.stat().st_size < 100:
        return False
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        probe = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(audio_path)],
            capture_output=True, text=True, check=True, creationflags=flags
        )
        dur = float(json.loads(probe.stdout)["format"]["duration"])
        foley_wav = audio_path.parent / f"temp_foley_{audio_path.name}"
        if not synthesize_scene_foley_audio(scene, dur, foley_wav):
            return False

        mix_cmd = [
            "ffmpeg", "-y",
            "-i", str(audio_path),
            "-i", str(foley_wav),
            "-filter_complex",
            "[0:a]volume=1.0[voice]; [1:a]volume=0.20[foley]; [voice][foley]amix=inputs=2:duration=first:dropout_transition=2[aout]",
            "-map", "[aout]",
            "-c:a", "pcm_s16le",
            str(output_path)
        ]
        res = subprocess.run(mix_cmd, capture_output=True, text=True, creationflags=flags)
        foley_wav.unlink(missing_ok=True)
        return res.returncode == 0 and output_path.is_file() and output_path.stat().st_size > 1000
    except Exception as exc:
        print(f"[FOLEY_WARN] Lỗi trộn âm thanh Foley: {exc}", flush=True)
        return False


def ensure_flow_account_browser(account: dict, timeout: float = 12.0) -> bool:
    """Ensures Chrome CDP is alive and listening for this specific Flow account.
    If the browser process is offline, launches it in the background and verifies CDP.
    """
    if not isinstance(account, dict) or not account.get("id"):
        return False
    try:
        from studio.studio_mcp.accounts import connection_check, _chrome_path, account_tool_url, bundled_shared_tool_url, _pid_browser_for_account
        from studio.studio_flow_accounts import minimize_chrome_window

        check = connection_check(account["id"])
        if check.get("connected"):
            pid = _pid_browser_for_account(account)
            if pid:
                minimize_chrome_window(pid)
            return True

        chrome = _chrome_path()
        if not chrome or not Path(chrome).is_file():
            return False

        target_url = account_tool_url(account) or bundled_shared_tool_url() or "https://flow.google.com"
        cmd = [
            str(chrome),
            f"--remote-debugging-port={account['cdp_port']}",
            f"--user-data-dir={account['user_data_dir']}",
            "--profile-directory=Default",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding",
            "--disable-features=CalculateNativeWinOcclusion",
            "--window-size=900,760",
            "--window-position=80,70",
            f"--app={target_url}",
        ]
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        deadline = time.time() + timeout
        while time.time() < deadline:
            time.sleep(1.0)
            st = connection_check(account["id"])
            if st.get("connected"):
                pid = _pid_browser_for_account(account) or proc.pid
                if pid:
                    minimize_chrome_window(pid)
                return True
    except Exception as exc:
        print(f"[FLOW_ACCOUNT_WARN] Không thể khởi động Chrome cho {account.get('name', account.get('id'))}: {exc}", flush=True)

    return False


def get_flow_candidate_accounts() -> list[dict]:
    """Returns prioritized Google Flow accounts:
    Active account first, followed by remaining registered accounts in pool.
    """
    try:
        from studio.studio_mcp.accounts import active_account, load_accounts
        store = load_accounts()
        current_active = active_account()
        active_id = current_active.get("id")
        accounts_list = store.get("accounts", [])
        
        candidates = [current_active]
        for acc in accounts_list:
            if acc.get("id") != active_id:
                candidates.append(acc)
        return candidates
    except Exception:
        return []


def render_flow_video_for_scene(
    scene: dict,
    bible: dict,
    image_path: Path,
    output_silent_mp4: Path,
    *,
    model: str = DEFAULT_VIDEO_MODEL,
    duration: int = 8,
    aspect_ratio: str = "16:9",
    width: int = 1536,
    height: int = 864,
) -> str:
    """Generate a motion video for a single scene via Google Flow with multi-account failover.
    
    Uses image_path as the reference first frame for Image-to-Video continuity.
    Iterates across candidate Google Flow accounts (port 9550, 9460, 9461) if quota or error occurs.
    Falls back gracefully to 2.5D Ken Burns color_video only if all Flow accounts fail.
    """
    scene_idx = scene.get("scene_number", 1)
    sid = f"scene_{scene_idx:04d}"
    scope_dir = output_silent_mp4.parent / ".flow_video_temp"
    scope_dir.mkdir(parents=True, exist_ok=True)

    prompt = video_motion_prompt(scene, bible)
    ref_image = str(image_path) if image_path and image_path.is_file() else None

    # Preserve Master Character Anchor from Scene 1 across the episode
    try:
        episode_dir = output_silent_mp4.parent.parent
        anchor_file = episode_dir / "master_character_anchor.png"
        if scene_idx == 1 and image_path and image_path.is_file():
            shutil.copy2(image_path, anchor_file)
        elif not ref_image and anchor_file.is_file():
            ref_image = str(anchor_file)
    except Exception:
        pass

    print(f"[FLOW_VIDEO] Bắt đầu tạo video chuyển động cho {sid} (Model ưu tiên: {model}, Ref: {bool(ref_image)})...", flush=True)

    models_to_try = [model]
    if model != "Omni 1.1 Flash":
        models_to_try.append("Omni 1.1 Flash")
    if "Veo 3.1 - Fast" not in models_to_try:
        models_to_try.append("Veo 3.1 - Fast")

    candidates = get_flow_candidate_accounts()
    if not candidates:
        candidates = [None]

    for acc in candidates:
        acc_name = acc.get("name", "Active") if acc else "Default"
        acc_port = acc.get("cdp_port", 9550) if acc else 9550
        
        # Verify or auto-launch browser for this account
        if acc and not ensure_flow_account_browser(acc):
            print(f"[FLOW_VIDEO_SKIP] Tài khoản '{acc_name}' (Port {acc_port}) không phản hồi CDP, chuyển tài khoản kế tiếp...", flush=True)
            continue

        print(f"[FLOW_VIDEO] 🚀 Đang kết nối tài khoản Flow: '{acc_name}' (Port {acc_port}) cho {sid}...", flush=True)

        account_failed = False
        for current_model in models_to_try:
            try:
                if current_model != model:
                    print(f"[FLOW_VIDEO] Chuyển sang model dự phòng: {current_model} trên '{acc_name}'...", flush=True)
                backend = StoryboardVideoBackend(
                    scope_dir,
                    account=acc,
                    model=current_model,
                    duration=duration,
                    aspect_ratio=aspect_ratio,
                )
                batch = [{
                    "scene_id": sid,
                    "prompt": prompt,
                    "reference_image": ref_image,
                    "duration": duration,
                    "aspect_ratio": aspect_ratio,
                }]
                receipts = backend.render_video_batch(batch)
                if sid in receipts:
                    result_mp4 = Path(receipts[sid]["path"])
                    if result_mp4.is_file() and result_mp4.stat().st_size > 1024:
                        audio_path = output_silent_mp4.parent / "audio.wav"
                        if adapt_video_clip_to_audio(result_mp4, audio_path, output_silent_mp4, width, height, duration):
                            # Optional atmospheric particle overlay blending (rain, fire embers, bokeh dust)
                            if bible.get("atmospheric_overlay") != "none" and scene.get("atmospheric_overlay") != "none":
                                ovl_tmp = output_silent_mp4.parent / f"ovl_{output_silent_mp4.name}"
                                if apply_atmospheric_particle_overlay(output_silent_mp4, scene, bible, ovl_tmp, width, height, duration=duration):
                                    shutil.move(str(ovl_tmp), str(output_silent_mp4))

                            print(f"[FLOW_VIDEO_SUCCESS] ✅ Hoàn thành video chuyển động AI cho {sid} bằng tài khoản '{acc_name}' ({current_model}) -> {output_silent_mp4.name} ({output_silent_mp4.stat().st_size} bytes)", flush=True)
                            return str(output_silent_mp4)
            except Exception as exc:
                err_str = str(exc)
                print(f"[FLOW_VIDEO_WARN] Lỗi sinh video Flow ({current_model}) trên '{acc_name}': {err_str}", flush=True)
                if "QUOTA" in err_str.upper() or "RATE_LIMIT" in err_str.upper() or "LIMIT_REACHED" in err_str.upper() or "NOT_CONNECTED" in err_str.upper():
                    print(f"[FLOW_VIDEO_FAILOVER] ⚠️ Tài khoản '{acc_name}' chạm hạn mức quota/lỗi kết nối! Kích hoạt bọc lót sang tài khoản tiếp theo...", flush=True)
                    account_failed = True
                    break

        if account_failed:
            continue

    print(f"[FLOW_VIDEO_FALLBACK] ⚠️ Tất cả tài khoản Flow đã thử nghiệm; chuyển đổi an toàn sang Ken Burns camera animation cho {sid}...", flush=True)

    # Safe fallback to Ken Burns camera motion without ever crashing on NoneType
    from studio_color_render import color_video, create_silence
    audio_path = output_silent_mp4.parent / "audio.wav"
    if not audio_path.is_file() or audio_path.stat().st_size < 100:
        audio_path = output_silent_mp4.parent / "temp_silence.wav"
        create_silence(audio_path, seconds=scene.get("script_seconds", duration))

    return color_video(
        image_path,
        audio_path,
        output_silent_mp4,
        width,
        height,
        scene_index=scene_idx,
        motion_type="auto",
        overlay_effect="auto",
        genre=bible.get("production_genre", "documentary"),
    )
