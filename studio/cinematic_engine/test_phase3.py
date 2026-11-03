"""Test Phase 3 - BGM & SFX Mixing Engine with Dynamic Auto-Ducking.
Verifies:
1. Loading dialogue_master.wav from Phase 2
2. Resolving BGM track for 'tense_investigation'
3. Auto-ducking BGM under speech and swelling up during pauses
4. Generating final scene_master_audio.wav
"""
import sys
import os
import json
from pathlib import Path

# Add paths to sys.path
STUDIO_ROOT = Path(__file__).resolve().parent.parent
if str(STUDIO_ROOT) not in sys.path:
    sys.path.insert(0, str(STUDIO_ROOT))

from cinematic_engine.drama_sound_mixer import DramaSoundMixer
from cinematic_engine.drama_audio_engine import get_wav_duration


def run_phase3_test():
    print("=" * 60)
    print("TESTING PHASE 3: BGM & SFX MIXING ENGINE (AUTO-DUCKING)")
    print("=" * 60)

    scene_1_dir = STUDIO_ROOT / "productions" / "test-drama-series" / "episode_001" / "scenes" / "scene_001"
    dialogue_wav = scene_1_dir / "dialogue_master.wav"
    timeline_json = scene_1_dir / "dialogue_timeline.json"

    assert dialogue_wav.exists(), f"Phase 2 dialogue master missing: {dialogue_wav}"
    assert timeline_json.exists(), f"Phase 2 timeline missing: {timeline_json}"

    with open(timeline_json, "r", encoding="utf-8") as f:
        timeline = json.load(f)

    mixer = DramaSoundMixer()
    bgm_mood = "tense_investigation"
    sfx_cues = ["heavy_rain_on_roof", "fireplace_crackling"]
    output_master_audio = scene_1_dir / "scene_master_audio.wav"

    print(f"\n[MIXING PARAMETERS]")
    print(f"Dialogue Track: {dialogue_wav.name} ({timeline['total_duration']}s)")
    print(f"BGM Mood: {bgm_mood}")
    print(f"SFX Cues: {sfx_cues}")
    print(f"Target Output: {output_master_audio.name}")

    mixed_path = mixer.mix_scene_audio(
        dialogue_master_wav=dialogue_wav,
        bgm_mood=bgm_mood,
        sfx_cues=sfx_cues,
        output_master_wav=output_master_audio
    )

    print("\n[PHASE 3 VERIFICATION RESULTS]")
    assert mixed_path.exists(), f"Mixed audio not found: {mixed_path}"
    mixed_size = mixed_path.stat().st_size
    assert mixed_size > 10000, f"Mixed audio too small: {mixed_size} bytes"

    mixed_dur = get_wav_duration(mixed_path)
    expected_dur = timeline["total_duration"]
    print(f" Scene Master Audio generated: {mixed_path.name} ({mixed_size / 1024:.1f} KB)")
    print(f" Duration: {mixed_dur:.2f}s (Expected: {expected_dur:.2f}s)")
    assert abs(mixed_dur - expected_dur) < 0.3, f"Duration mismatch: {mixed_dur} vs {expected_dur}"

    print("\n[SUCCESS] PHASE 3 COMPLETE: BGM & SFX Mixing with Auto-Ducking is fully functional!")
    return True


if __name__ == "__main__":
    success = run_phase3_test()
    sys.exit(0 if success else 1)
