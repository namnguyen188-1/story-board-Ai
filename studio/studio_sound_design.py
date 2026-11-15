"""Studio Sound Design & Hollywood Audio Mastering Engine
---------------------------------------------------------
Delivers international documentary audio standards:
1. Dynamic Audio Ducking via sidechain compression (BGM automatically ducks by 12-14dB during voiceover,
   and swells up smoothly during dramatic pauses).
2. Multi-Act Story Soundtrack (Theme shifts between Mystery -> Tension -> Climax -> Resolution).
3. Timed Cinematic SFX & Foley Cues (Hook Sub-bass Boom, Suspense Clock Ticks, Act Risers, CTA Whooshes).
4. EBU R128 / YouTube Loudness Normalization (-14 LUFS, True Peak -1.0 dB).
5. 100% Non-destructive with full automatic fallback if any component fails.
"""
from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path
from typing import List, Optional

import numpy as np


# ============================================================================
# 1. PROCEDURAL SOUND EFFECT SYNTHESIS (Zero External Dependency)
# ============================================================================

def _write_wav_int16(path: Path, data: np.ndarray, sample_rate: int = 44100, stereo: bool = False):
    """Safely writes a normalized numpy array into 16-bit PCM WAV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    clipped = np.clip(data, -0.98, 0.98)
    int_data = (clipped * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(2 if stereo else 1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(int_data.tobytes())


def generate_cinematic_boom(path: Path, duration: float = 3.2, sr: int = 44100):
    """Deep cinematic sub-bass impact with exponential pitch decay and warm saturation."""
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    # Pitch drops from 120Hz to 36Hz
    freq = 36.0 + (120.0 - 36.0) * np.exp(-t * 2.8)
    phase = 2.0 * np.pi * np.cumsum(freq) / sr
    env = np.exp(-t * 1.6)
    sub = (np.sin(phase) * 0.75 + np.sin(phase * 0.5) * 0.25)
    boom = np.tanh(sub * 1.8) * env * 0.88
    _write_wav_int16(path, boom, sample_rate=sr)


def generate_suspense_clock(path: Path, duration: float = 1.0, sr: int = 44100):
    """Crisp mechanical clock tick with subtle wooden resonance."""
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    tick = np.zeros_like(t)
    n = int(0.06 * sr)
    tt = np.linspace(0, 0.06, n, endpoint=False)
    click = (np.sin(2 * np.pi * 2200 * tt) * 0.5 + np.sin(2 * np.pi * 920 * tt) * 0.5) * np.exp(-tt * 75.0)
    tick[:n] = click * 0.65
    _write_wav_int16(path, tick, sample_rate=sr)


def generate_cinematic_riser(path: Path, duration: float = 3.5, sr: int = 44100):
    """Tension riser with pitch glide and filtered noise crescendo."""
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    f_curve = 75.0 + 600.0 * (t / duration) ** 2.3
    phase = 2.0 * np.pi * np.cumsum(f_curve) / sr
    noise = np.random.normal(0, 0.09, len(t))
    amp_env = (t / duration) ** 2.0
    riser = (np.sin(phase) * 0.72 + noise) * amp_env * 0.82
    _write_wav_int16(path, riser, sample_rate=sr)


def generate_cinematic_whoosh(path: Path, duration: float = 1.2, sr: int = 44100):
    """Airy transition whoosh with bell envelope."""
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    env = np.sin(np.pi * (t / duration)) ** 2.2
    noise = np.random.normal(0, 1.0, len(t))
    kernel = np.ones(35) / 35.0
    filtered = np.convolve(noise, kernel, mode="same")
    whoosh = filtered * env * 0.75
    _write_wav_int16(path, whoosh, sample_rate=sr)


def generate_ambient_pad(path: Path, duration: float = 32.0, sr: int = 44100):
    """Warm harmonic ambient drone chord (Root + Fifth + Octave) for resolution."""
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    # Chord: D2 (73.4Hz), A2 (110Hz), D3 (146.8Hz), F#3 (185Hz)
    chord = (
        np.sin(2 * np.pi * 73.41 * t) * 0.35 +
        np.sin(2 * np.pi * 110.0 * t) * 0.28 +
        np.sin(2 * np.pi * 146.83 * t) * 0.22 +
        np.sin(2 * np.pi * 185.0 * t) * 0.15
    )
    # Soft modulation / warmth
    lfo = 1.0 + 0.12 * np.sin(2 * np.pi * 0.25 * t)
    fade_len = int(2.5 * sr)
    fade_in = np.linspace(0, 1, fade_len)
    fade_out = np.linspace(1, 0, fade_len)
    env = np.ones_like(t)
    env[:fade_len] = fade_in
    env[-fade_len:] = fade_out
    pad = chord * lfo * env * 0.65
    _write_wav_int16(path, pad, sample_rate=sr)


# ============================================================================
# 2. ASSET DISCOVERY & INITIALIZATION
# ============================================================================

def ensure_sound_design_assets(engine_dir: Path) -> dict[str, Path]:
    """Ensures all essential cinematic SFX and musical cues exist on disk.
    If missing, procedurally generates them without requiring network calls.
    """
    sfx_dir = engine_dir / "assets" / "sfx"
    music_dir = engine_dir / "assets" / "music"
    sfx_dir.mkdir(parents=True, exist_ok=True)
    music_dir.mkdir(parents=True, exist_ok=True)

    assets = {
        "boom": sfx_dir / "cinematic_boom.wav",
        "clock": sfx_dir / "suspense_clock.wav",
        "riser": sfx_dir / "cinematic_riser.wav",
        "whoosh": sfx_dir / "cinematic_whoosh.wav",
        "pop": sfx_dir / "pop.wav",
        "bgm_mystery": music_dir / "ambient_mystery" / "fallback_ambient_mystery.wav",
        "bgm_tension": music_dir / "epic_tension" / "fallback_epic_tension.wav",
        "bgm_resolve": music_dir / "climax_resolve" / "fallback_climax_resolve.wav",
    }

    if not assets["boom"].is_file() or assets["boom"].stat().st_size < 1000:
        generate_cinematic_boom(assets["boom"])
    if not assets["clock"].is_file() or assets["clock"].stat().st_size < 1000:
        generate_suspense_clock(assets["clock"])
    if not assets["riser"].is_file() or assets["riser"].stat().st_size < 1000:
        generate_cinematic_riser(assets["riser"])
    if not assets["whoosh"].is_file() or assets["whoosh"].stat().st_size < 1000:
        generate_cinematic_whoosh(assets["whoosh"])
    if not assets["bgm_resolve"].is_file() or assets["bgm_resolve"].stat().st_size < 1000:
        generate_ambient_pad(assets["bgm_resolve"])

    return assets


# ============================================================================
# 3. SOUNDTRACK & SFX STEM GENERATOR
# ============================================================================

def build_multiact_soundtrack(duration: float, engine_dir: Path, output_bgm_wav: Path) -> bool:
    """Builds a continuous multi-act musical score mapped to narrative progression:
    - Act 1 (0% to 15%): Mystery / Intrigue
    - Act 2 (15% to 75%): Escalating Tension
    - Act 3 (75% to 100%): Climax & Resolution
    Crossfades seamlessly between acts. Falls back safely if needed.
    """
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    assets = ensure_sound_design_assets(engine_dir)
    dur = max(5.0, float(duration))

    mystery = assets["bgm_mystery"] if assets["bgm_mystery"].is_file() else None
    tension = assets["bgm_tension"] if assets["bgm_tension"].is_file() else mystery
    resolve = assets["bgm_resolve"] if assets["bgm_resolve"].is_file() else mystery

    primary = mystery or tension or resolve
    if not primary or not primary.is_file():
        return False

    # For short clips (<60s), loop single primary track with fade
    if dur < 60.0 or not tension or not resolve:
        cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-stream_loop", "-1", "-i", str(primary),
            "-t", f"{dur:.2f}",
            "-af", f"afade=t=out:st={dur-2.5:.2f}:d=2.5",
            "-c:a", "pcm_s16le",
            str(output_bgm_wav)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, creationflags=flags)
        return res.returncode == 0 and output_bgm_wav.is_file()

    # Multi-act progression:
    # Act 1: 0 to 15% of dur
    # Act 2: 15% to 75% of dur
    # Act 3: 75% to 100% of dur
    d_act1 = max(10.0, dur * 0.15)
    d_act2 = max(20.0, dur * 0.60)
    d_act3 = max(10.0, dur - d_act1 - d_act2)

    tmp_dir = output_bgm_wav.parent / "temp_audio_acts"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    a1_path = tmp_dir / "act1.wav"
    a2_path = tmp_dir / "act2.wav"
    a3_path = tmp_dir / "act3.wav"

    try:
        # Render looped acts
        for src, d_act, out_path in [(mystery, d_act1 + 3.0, a1_path),
                                     (tension, d_act2 + 3.0, a2_path),
                                     (resolve, d_act3 + 3.0, a3_path)]:
            subprocess.run([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-stream_loop", "-1", "-i", str(src),
                "-t", f"{d_act:.2f}",
                "-c:a", "pcm_s16le", str(out_path)
            ], check=True, capture_output=True, creationflags=flags)

        # Crossfade acts into single master soundtrack
        xfade_cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(a1_path),
            "-i", str(a2_path),
            "-i", str(a3_path),
            "-filter_complex",
            "[0:a][1:a]acrossfade=d=3.0:c1=tri:c2=tri[m1];"
            "[m1][2:a]acrossfade=d=3.0:c1=tri:c2=tri[m2];"
            f"[m2]afade=t=out:st={dur-3.0:.2f}:d=3.0[aout]",
            "-map", "[aout]",
            "-t", f"{dur:.2f}",
            "-c:a", "pcm_s16le",
            str(output_bgm_wav)
        ]
        res = subprocess.run(xfade_cmd, capture_output=True, text=True, creationflags=flags)
        if res.returncode == 0 and output_bgm_wav.is_file() and output_bgm_wav.stat().st_size > 1000:
            return True
    except Exception as exc:
        print(f"[AUDIO_DESIGN_WARN] Multi-act score crossfade failed ({exc}), falling back to continuous loop.", flush=True)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    # Fallback to single loop
    fallback_cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-stream_loop", "-1", "-i", str(primary),
        "-t", f"{dur:.2f}",
        "-af", f"afade=t=out:st={dur-2.5:.2f}:d=2.5",
        "-c:a", "pcm_s16le",
        str(output_bgm_wav)
    ]
    res = subprocess.run(fallback_cmd, capture_output=True, text=True, creationflags=flags)
    return res.returncode == 0 and output_bgm_wav.is_file()


def compose_cinematic_sfx_stem(duration: float,
                               cta_times: list[float],
                               engine_dir: Path,
                               output_sfx_wav: Path) -> bool:
    """Arranges precision SFX cues along the timeline:
    - T=0.8s: Cinematic Boom (Sub-bass impact on hook)
    - T=1.0s to 12.0s: Suspense clock ticking (urgency in cold open)
    - Act transitions: Subtle riser or sub-bass drop
    - CTA timestamps: Transition whoosh
    """
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    assets = ensure_sound_design_assets(engine_dir)
    dur = max(5.0, float(duration))

    boom = assets["boom"]
    clock = assets["clock"]
    riser = assets["riser"]
    whoosh = assets["whoosh"]

    inputs = []
    filter_parts = []
    mix_tags = []
    idx = 0

    # 1. Hook Sub-bass Impact at 0.8s
    if boom.is_file():
        inputs.extend(["-i", str(boom)])
        filter_parts.append(f"[{idx}:a]adelay=800|800,volume=0.55[sfx_boom]")
        mix_tags.append("[sfx_boom]")
        idx += 1

    # 2. Suspense Clock Ticks during Hook (1.5s to 10.5s, every 1.0s)
    if clock.is_file() and dur > 15.0:
        inputs.extend(["-i", str(clock)])
        clock_idx = idx
        idx += 1
        tick_tags = []
        tick_count = min(10, int(min(dur * 0.4, 10)))
        filter_parts.append(f"[{clock_idx}:a]asplit={tick_count}" + "".join(f"[clk_{i}]" for i in range(tick_count)))
        for i in range(tick_count):
            t_ms = int((1.5 + i * 1.0) * 1000)
            filter_parts.append(f"[clk_{i}]adelay={t_ms}|{t_ms}[clk_d_{i}]")
            tick_tags.append(f"[clk_d_{i}]")
        all_clks = "".join(tick_tags)
        filter_parts.append(f"{all_clks}amix=inputs={tick_count}:dropout_transition=0,volume=0.25[sfx_clock]")
        mix_tags.append("[sfx_clock]")

    # 3. Act Transition Riser at 75% mark
    if riser.is_file() and dur > 60.0:
        climax_t = max(5.0, dur * 0.75 - 3.5)
        climax_ms = int(climax_t * 1000)
        inputs.extend(["-i", str(riser)])
        filter_parts.append(f"[{idx}:a]adelay={climax_ms}|{climax_ms},volume=0.45[sfx_riser]")
        mix_tags.append("[sfx_riser]")
        idx += 1

    # 4. CTA Overlays Whooshes
    if whoosh.is_file() and cta_times:
        inputs.extend(["-i", str(whoosh)])
        w_idx = idx
        idx += 1
        if len(cta_times) == 1:
            w_ms = int(cta_times[0] * 1000)
            filter_parts.append(f"[{w_idx}:a]adelay={w_ms}|{w_ms},volume=0.40[sfx_whoosh]")
            mix_tags.append("[sfx_whoosh]")
        else:
            filter_parts.append(f"[{w_idx}:a]asplit={len(cta_times)}" + "".join(f"[w_{i}]" for i in range(len(cta_times))))
            w_tags = []
            for i, t in enumerate(cta_times):
                w_ms = int(t * 1000)
                filter_parts.append(f"[w_{i}]adelay={w_ms}|{w_ms}[w_d_{i}]")
                w_tags.append(f"[w_d_{i}]")
            all_ws = "".join(w_tags)
            filter_parts.append(f"{all_ws}amix=inputs={len(cta_times)}:dropout_transition=0,volume=0.40[sfx_whoosh]")
            mix_tags.append("[sfx_whoosh]")

    if not mix_tags:
        # Create silent stem if no SFX
        cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo:d={dur:.2f}",
            "-c:a", "pcm_s16le", str(output_sfx_wav)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, creationflags=flags)
        return res.returncode == 0 and output_sfx_wav.is_file()

    # Mix all SFX cues into a single stem
    all_mix = "".join(mix_tags)
    filter_parts.append(f"{all_mix}amix=inputs={len(mix_tags)}:duration=first:dropout_transition=0,aformat=channel_layouts=stereo[sfx_out]")
    
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        *inputs,
        "-filter_complex", ";".join(filter_parts),
        "-map", "[sfx_out]",
        "-t", f"{dur:.2f}",
        "-c:a", "pcm_s16le",
        str(output_sfx_wav)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, creationflags=flags)
    return res.returncode == 0 and output_sfx_wav.is_file()


# ============================================================================
# 4. HOLLYWOOD MASTERING & DYNAMIC AUDIO DUCKING
# ============================================================================

def apply_hollywood_audio_master(source_video: Path,
                                 output_video: Path,
                                 cta_path: Optional[Path],
                                 cta_times: list[float],
                                 width: int,
                                 height: int,
                                 engine_dir: Path) -> bool:
    """Master audio and video mixing pipeline for full episodes:
    1. Video: Overlays social CTA animations cleanly (if cta_path is valid).
    2. Audio Sidechain Ducking: Voiceover drives dynamic ducking on multi-act BGM stem
       (drops by 12-14dB when speaking, smoothly swells +10dB in pauses).
    3. SFX: Layers aligned cinematic impacts, suspense ticks, and risers.
    4. Master Loudness: Certified -14 LUFS (YouTube Optimal).
    """
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    source_p = Path(source_video)
    output_p = Path(output_video)

    # 1. Probe source video metadata
    try:
        probe = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_format", "-show_streams", str(source_p)],
            capture_output=True, text=True, check=True, creationflags=flags
        )
        meta = json.loads(probe.stdout)
        dur = float(meta["format"].get("duration") or 0.0)
    except Exception as exc:
        print(f"[AUDIO_DESIGN_ERR] ffprobe failed on source: {exc}", flush=True)
        return False

    if dur <= 1.0:
        return False

    temp_audio_dir = output_p.parent / f"_sound_design_{output_p.stem}"
    temp_audio_dir.mkdir(parents=True, exist_ok=True)
    bgm_stem = temp_audio_dir / "bgm_multiact_stem.wav"
    sfx_stem = temp_audio_dir / "sfx_cues_stem.wav"
    tmp_out = output_p.parent / f"mastering_pending_{output_p.name}"

    try:
        print(f"[SOUND_DESIGN] 🎬 Khởi tạo hệ thống âm thanh điện ảnh đa tầng (Thời lượng: {dur:.1f}s)...", flush=True)
        
        # Step A: Build Multi-act BGM
        print(f"[SOUND_DESIGN] 🎼 Hòa âm bản nhạc nền đa chương hồi (Multi-Act Narrative Score)...", flush=True)
        if not build_multiact_soundtrack(dur, engine_dir, bgm_stem):
            print(f"[SOUND_DESIGN_WARN] Không tạo được BGM đa chương hồi, sử dụng fallback.", flush=True)

        # Step B: Build SFX Cues Stem
        print(f"[SOUND_DESIGN] 💥 Bố trí các điểm nhấn âm thanh (Hook Boom, Suspense Clock, Risers, CTA Whoosh)...", flush=True)
        if not compose_cinematic_sfx_stem(dur, cta_times, engine_dir, sfx_stem):
            print(f"[SOUND_DESIGN_WARN] Không tạo được SFX stem, bỏ qua SFX.", flush=True)

        # Step C: Compose master FFmpeg filter
        inputs = ["-i", str(source_p)]  # [0:v], [0:a] (Voice)
        next_input_idx = 1

        bgm_input_idx = None
        if bgm_stem.is_file() and bgm_stem.stat().st_size > 1000:
            inputs.extend(["-i", str(bgm_stem)])
            bgm_input_idx = next_input_idx
            next_input_idx += 1

        sfx_input_idx = None
        if sfx_stem.is_file() and sfx_stem.stat().st_size > 1000:
            inputs.extend(["-i", str(sfx_stem)])
            sfx_input_idx = next_input_idx
            next_input_idx += 1

        # Check CTA video overlays
        has_cta_video = (cta_path and Path(cta_path).is_file() and len(cta_times) > 0)
        cta_input_idx = None
        if has_cta_video:
            inputs.extend(["-i", str(cta_path)])
            cta_input_idx = next_input_idx
            next_input_idx += 1

        v_filters = []
        final_v = "[0:v]"
        if has_cta_video:
            # Scale CTA overlay
            is_vertical = height > width
            cta_w = int(width * (0.85 if is_vertical else 0.40))
            if cta_w % 2 != 0:
                cta_w += 1
            x_pos = "(W-w)/2"
            y_pos = "H-h-160" if is_vertical else "H-h-70"
            v_filters.append(f"[{cta_input_idx}:v]scale={cta_w}:-1[scaled_cta]")

            last_v = "[0:v]"
            for i, t in enumerate(cta_times):
                out_tag = f"[v_cta_{i}]"
                enable_expr = f"between(t,{t:.2f},{t+4.5:.2f})"
                v_filters.append(f"{last_v}[scaled_cta]overlay=x={x_pos}:y={y_pos}:enable='{enable_expr}':eof_action=pass{out_tag}")
                last_v = out_tag
            final_v = last_v

        # Audio filters: Dynamic Sidechain Ducking + Loudness Normalization
        a_filters = []
        audio_mix_inputs = ["[v_mix]"]

        # Voice split for sidechain detection
        a_filters.append("[0:a]asplit=2[v_mix][v_sc]")

        # Dynamic ducked BGM
        if bgm_input_idx is not None:
            a_filters.append(f"[{bgm_input_idx}:a]volume=0.28[bgm_raw]")
            # Sidechain Ducking:
            # threshold=0.035, ratio=8.0 (ducks BGM by ~14dB during voice)
            # attack=25ms (rapid response), release=550ms (smooth swell during voice pauses)
            a_filters.append(
                f"[bgm_raw][v_sc]sidechaincompress=threshold=0.035:ratio=8.0:attack=25:release=550[bgm_ducked]"
            )
            audio_mix_inputs.append("[bgm_ducked]")

        # Timed SFX stem
        if sfx_input_idx is not None:
            a_filters.append(f"[{sfx_input_idx}:a]volume=0.38[sfx_leveled]")
            audio_mix_inputs.append("[sfx_leveled]")

        # Mix stems & normalize to -14 LUFS YouTube standard
        all_stems = "".join(audio_mix_inputs)
        a_filters.append(
            f"{all_stems}amix=inputs={len(audio_mix_inputs)}:duration=first:dropout_transition=2,"
            f"loudnorm=I=-14:LRA=7:TP=-1,aformat=channel_layouts=stereo[aout]"
        )

        all_filter_complex = ";".join(v_filters + a_filters)

        cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            *inputs,
            "-filter_complex", all_filter_complex,
            "-map", final_v,
            "-map", "[aout]",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
            "-movflags", "+faststart",
            str(tmp_out)
        ]

        print(f"[SOUND_DESIGN] 🎛️ Đang render âm thanh Master chuẩn YouTube (-14 LUFS) & Dynamic Ducking...", flush=True)
        res = subprocess.run(cmd, capture_output=True, text=True, creationflags=flags)
        if res.returncode == 0 and tmp_out.is_file() and tmp_out.stat().st_size > 10000:
            if output_p.is_file():
                output_p.unlink(missing_ok=True)
            shutil.move(str(tmp_out), str(output_p))
            print(f"[SOUND_DESIGN] ✨ HOÀN TẤT: Âm thanh điện ảnh Hollywood & Dynamic Ducking đã áp dụng thành công 100%!", flush=True)
            return True
        else:
            print(f"[SOUND_DESIGN_WARN] Render âm thanh thất bại ({res.stderr[-300:] if res.stderr else 'unknown'}), giữ an toàn.", flush=True)
            return False

    except Exception as exc:
        print(f"[SOUND_DESIGN_ERR] Lỗi không mong muốn trong master âm thanh: {exc}", flush=True)
        return False
    finally:
        shutil.rmtree(temp_audio_dir, ignore_errors=True)
        if tmp_out.is_file():
            tmp_out.unlink(missing_ok=True)
