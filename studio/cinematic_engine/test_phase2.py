"""Test Phase 2 - Multi-Voice Character Dialogue Audio Engine.
Loads Scene 1 from drama_plan.json and synthesizes:
1. Individual beat audios with assigned cast voices (Fenrir, Sadachbia, Charon)
2. Dialogue master track with conversational pauses
3. Subtitle file (.srt) and time-aligned timeline (.json)
"""
import sys
import os
import json
from pathlib import Path

# Fix Windows stdout encoding
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Add studio to sys.path
STUDIO_ROOT = Path(__file__).resolve().parent.parent
if str(STUDIO_ROOT) not in sys.path:
    sys.path.insert(0, str(STUDIO_ROOT))

from cinematic_engine.drama_audio_engine import DramaAudioEngine, get_wav_duration
from cinematic_engine.drama_schema import CharacterProfile


def run_phase2_test():
    print("=" * 60)
    print("TESTING PHASE 2: MULTI-VOICE DIALOGUE AUDIO ENGINE")
    print("=" * 60)

    plan_path = STUDIO_ROOT / "productions" / "test-drama-series" / "episode_001" / "drama_plan.json"
    if not plan_path.exists():
        print(f"[FAIL] Plan not found: {plan_path}")
        return False

    with open(plan_path, "r", encoding="utf-8") as f:
        plan = json.load(f)

    scene_1 = plan["scenes"][0]
    language = plan.get("language", "Vietnamese")
    cast_dict = {
        name: CharacterProfile(
            name=name,
            gender=data.get("gender", "male"),
            role=data.get("role", "supporting"),
            voice_id=data.get("voice_id", "Charon"),
            voice_label=data.get("voice_label", ""),
            personality=data.get("personality", "")
        )
        for name, data in plan.get("cast", {}).items()
    }

    print(f"\n[SCENE 1 INFO]")
    print(f"Setting: {scene_1['setting']}")
    print(f"Summary: {scene_1['summary']}")
    print(f"Number of Dialogue Beats: {len(scene_1['dialogue_beats'])}")
    for b in scene_1["dialogue_beats"]:
        print(f"  - Beat {b['beat_id']} | {b['speaker']} ({b['voice_id']}): \"{b['text']}\"")

    # Output directory for test
    test_scene_dir = STUDIO_ROOT / "productions" / "test-drama-series" / "episode_001" / "scenes" / "scene_001"
    audio_engine = DramaAudioEngine(target_sample_rate=24000)

    print("\n[STARTING DIALOGUE ASSEMBLY]")
    res = audio_engine.assemble_scene_dialogue(
        scene=scene_1,
        language=language,
        scene_dir=test_scene_dir,
        cast_map=cast_dict
    )

    print("\n[PHASE 2 VERIFICATION RESULTS]")
    master_wav = Path(res["master_audio_path"])
    timeline_file = Path(res["timeline_path"])
    srt_file = Path(res["srt_path"])
    total_dur = res["total_duration"]

    assert master_wav.exists(), f"Master WAV not found: {master_wav}"
    assert master_wav.stat().st_size > 10000, f"Master WAV too small: {master_wav.stat().st_size} bytes"
    actual_wav_dur = get_wav_duration(master_wav)
    print(f" Master WAV generated: {master_wav.name} ({master_wav.stat().st_size / 1024:.1f} KB)")
    print(f" Duration reported in timeline: {total_dur:.2f}s | Measured from WAV: {actual_wav_dur:.2f}s")
    assert abs(actual_wav_dur - total_dur) < 0.2, f"Duration mismatch: {actual_wav_dur} vs {total_dur}"

    assert timeline_file.exists(), f"Timeline JSON not found: {timeline_file}"
    with open(timeline_file, "r", encoding="utf-8") as f:
        timeline_data = json.load(f)
    print(f" Timeline entries verified: {len(timeline_data['beats'])} beats with precise timecodes")
    for beat in timeline_data["beats"]:
        print(f"    [{beat['start_time']:.2f}s -> {beat['end_time']:.2f}s] {beat['speaker']} ({beat['voice_id']}): {beat['text'][:35]}...")

    assert srt_file.exists(), f"SRT file not found: {srt_file}"
    print(f"\n[GENERATED SUBTITLES PREVIEW ({srt_file.name})]")
    with open(srt_file, "r", encoding="utf-8") as f:
        print(f.read())

    print("\n[SUCCESS] PHASE 2 COMPLETE: Multi-Voice Dialogue Audio Engine is fully functional!")
    return True


if __name__ == "__main__":
    success = run_phase2_test()
    sys.exit(0 if success else 1)
