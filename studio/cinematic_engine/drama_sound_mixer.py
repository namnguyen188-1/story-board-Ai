"""Cinematic Drama Engine - BGM & SFX Mixing Engine with Dynamic Auto-Ducking (Phase 3).
Ducks background score automatically when characters speak, swells up during dramatic pauses,
and layers atmospheric sound effects for a cinematic soundscape.
"""
from __future__ import annotations

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add paths to sys.path if not present
CURRENT_DIR = Path(__file__).resolve().parent
STUDIO_DIR = CURRENT_DIR.parent
ENGINE_DIR = STUDIO_DIR / "engine"
WORKSPACE_DIR = STUDIO_DIR.parent
for p in [str(STUDIO_DIR), str(ENGINE_DIR), str(WORKSPACE_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)


# BGM Mood to Asset mapping
DEFAULT_BGM_MAP = {
    "tense_investigation": "ambient_mystery/fallback_ambient_mystery.wav",
    "mystery": "ambient_mystery/fallback_ambient_mystery.wav",
    "mystery_noir": "ambient_mystery/fallback_ambient_mystery.wav",
    "dramatic_climax": "epic_tension/fallback_epic_tension.wav",
    "epic_tension": "epic_tension/fallback_epic_tension.wav",
    "action_chase": "epic_tension/fallback_epic_tension.wav",
    "emotional_revelation": "ambient_mystery/fallback_ambient_mystery.wav",
}


class DramaSoundMixer:
    """Intelligent audio mixer for Cinematic Drama productions."""

    def __init__(self, assets_dir: Optional[Path] = None):
        self.assets_dir = assets_dir or (ENGINE_DIR / "assets")
        self.music_dir = self.assets_dir / "music"
        self.sfx_dir = self.assets_dir / "sfx"

    def resolve_bgm_track(self, mood: str, custom_bgm_dir: Optional[Path] = None) -> Optional[Path]:
        """Finds the most suitable BGM track for the requested scene mood."""
        # 1. Check custom user/series BGM directory
        if custom_bgm_dir and custom_bgm_dir.exists():
            for ext in (".mp3", ".wav", ".aac", ".ogg"):
                candidate = custom_bgm_dir / f"{mood}{ext}"
                if candidate.exists() and candidate.stat().st_size > 1000:
                    return candidate

        # 2. Check engine bundled assets
        rel_path = DEFAULT_BGM_MAP.get(mood.lower(), DEFAULT_BGM_MAP["tense_investigation"])
        stock_path = self.music_dir / rel_path
        if stock_path.exists() and stock_path.stat().st_size > 1000:
            return stock_path

        # 3. Fallback to any available audio file in music_dir
        for sub in self.music_dir.iterdir():
            if sub.is_dir():
                for f in sub.glob("*.wav"):
                    if f.stat().st_size > 1000:
                        return f

        return None

    def generate_procedural_ambient(self, mood: str, duration: float, output_path: Path) -> Path:
        """Synthesizes a clean atmospheric ambient drone using FFmpeg audio filters as fallback."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        # Deep sub-bass pad + gentle warm noise
        cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", f"anoisesrc=d={duration:.2f}:c=pink:r=24000:a=0.015",
            "-af", "lowpass=f=220,volume=1.8",
            str(output_path)
        ]
        try:
            subprocess.run(cmd, check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            return output_path
        except Exception as e:
            print(f"[SOUND_MIXER] Error synthesizing procedural ambient: {e}", flush=True)
            return output_path

    def mix_scene_audio(
        self,
        dialogue_master_wav: Path | str,
        bgm_mood: str,
        sfx_cues: List[str],
        output_master_wav: Path | str,
        custom_bgm_dir: Optional[Path] = None,
        bgm_volume: float = 0.32,
        ducking_threshold: float = 0.02,
        ducking_ratio: float = 4.5,
        attack_ms: int = 150,
        release_ms: int = 650
    ) -> Path:
        """Mixes dialogue, BGM with intelligent sidechain auto-ducking, and ambient SFX cues."""
        diag_path = Path(dialogue_master_wav)
        out_path = Path(output_master_wav)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        if not diag_path.exists():
            raise FileNotFoundError(f"Dialogue master WAV not found: {diag_path}")

        bgm_track = self.resolve_bgm_track(bgm_mood, custom_bgm_dir)
        temp_bgm = None

        if not bgm_track or not bgm_track.exists():
            # Generate procedural atmospheric bed
            from .drama_audio_engine import get_wav_duration
            dur = get_wav_duration(diag_path)
            temp_bgm = out_path.parent / "temp_procedural_bgm.wav"
            bgm_track = self.generate_procedural_ambient(bgm_mood, dur + 2.0, temp_bgm)

        print(f"[SOUND_MIXER] Mixing Scene Audio -> Dialogue: {diag_path.name} | BGM ({bgm_mood}): {bgm_track.name}", flush=True)

        # Check for rain / ambient SFX cues
        has_rain = any("rain" in s.lower() for s in sfx_cues)
        has_fire = any("fire" in s.lower() or "hearth" in s.lower() for s in sfx_cues)

        # Build FFmpeg Filter Complex with sidechaincompress auto-ducking
        # [0:a] = dialogue
        # [1:a] = bgm (looped indefinitely)
        if has_rain:
            # Generate ambient rain layer directly in filter complex
            filter_complex = (
                f"[1:a]volume={bgm_volume}[bgm_base];"
                f"anoisesrc=d=3600:c=pink:r=24000:a=0.018,lowpass=f=2500,volume=0.25[rain_bed];"
                f"[bgm_base][rain_bed]amix=inputs=2[music_and_ambience];"
                f"[music_and_ambience][0:a]sidechaincompress=threshold={ducking_threshold}:ratio={ducking_ratio}:attack={attack_ms}:release={release_ms}[ducked_bed];"
                f"[0:a][ducked_bed]amix=inputs=2:duration=first:dropout_transition=2[out]"
            )
            inputs = [
                "-i", str(diag_path),
                "-stream_loop", "-1", "-i", str(bgm_track),
                "-f", "lavfi", "-i", "anoisesrc=d=3600:c=pink:r=24000:a=0.015"
            ]
        else:
            filter_complex = (
                f"[1:a]volume={bgm_volume}[bgm_base];"
                f"[bgm_base][0:a]sidechaincompress=threshold={ducking_threshold}:ratio={ducking_ratio}:attack={attack_ms}:release={release_ms}[ducked_bgm];"
                f"[0:a][ducked_bgm]amix=inputs=2:duration=first:dropout_transition=2[out]"
            )
            inputs = [
                "-i", str(diag_path),
                "-stream_loop", "-1", "-i", str(bgm_track)
            ]

        cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            *inputs,
            "-filter_complex", filter_complex,
            "-map", "[out]",
            "-c:a", "pcm_s16le",
            "-ar", "24000",
            "-ac", "1",
            str(out_path)
        ]

        try:
            subprocess.run(cmd, check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            if out_path.exists() and out_path.stat().st_size > 1000:
                print(f"[SOUND_MIXER_SUCCESS] Master Scene Audio Mixed: {out_path} ({out_path.stat().st_size / 1024:.1f} KB)", flush=True)
                return out_path
        except subprocess.CalledProcessError as e:
            print(f"[SOUND_MIXER_ERR] FFmpeg mix failed: {e}. Falling back to dialogue audio.", flush=True)
            import shutil
            shutil.copy2(str(diag_path), str(out_path))
            return out_path
        finally:
            if temp_bgm and temp_bgm.exists():
                try:
                    temp_bgm.unlink()
                except Exception:
                    pass

        return out_path
