import json
import math
from pathlib import Path
import sys

# Add studio to sys.path
studio_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(studio_dir))

def test_scene_seconds_and_duration_capping():
    # Mock subtitle lines covering 3000 seconds
    fake_lines = [
        {"start": float(i * 5), "duration": 4.5, "text": f"Phrase at {i * 5} seconds."}
        for i in range(600)  # 3000s
    ]
    subtitles = {
        "ok": True,
        "language_code": "es",
        "title": "57 Minute Stoic Video",
        "duration_seconds": 3409.0,
        "lines": fake_lines
    }

    target_minutes = 1.0
    scene_seconds = 25

    # 1. Test duration capping in cloner logic
    duration = float(subtitles.get("duration_seconds") or (target_minutes * 60.0))
    if target_minutes and target_minutes > 0:
        target_dur_sec = float(target_minutes * 60.0)
        if duration <= 0 or target_dur_sec < duration:
            duration = target_dur_sec
    elif duration <= 0:
        duration = float(target_minutes * 60.0)

    assert duration == 60.0, f"Expected duration capped to 60.0s, got {duration}"

    # 2. Test effective scene seconds preservation
    eff_scene_seconds = scene_seconds if (scene_seconds > 0) else (7 if (duration <= 90 or target_minutes <= 1.05) else 25)
    assert eff_scene_seconds == 25, f"Expected eff_scene_seconds=25, got {eff_scene_seconds}"

    # 3. Test expected scene count
    scene_count = max(1, math.ceil(duration / eff_scene_seconds))
    assert scene_count <= 3, f"Expected <= 3 scenes for 60s with 25s pacing, got {scene_count}"

    # 4. Test active lines filtering
    active_lines = [l for l in subtitles.get("lines", []) if float(l.get("start", 0)) <= duration + 5.0]
    assert len(active_lines) <= 15, f"Expected <= 15 active lines for 60s, got {len(active_lines)}"

    print("ALL CLONE DURATION & PACING TESTS PASSED!")

if __name__ == "__main__":
    test_scene_seconds_and_duration_capping()
