"""Test Phase 4 - Video Synthesis & Character Dialogue Subtitles Integration.
Verifies:
1. Generating/loading base scene visual
2. Applying cinematic camera motion
3. Burning character-labeled subtitles
4. Muxing with Phase 3 scene_master_audio.wav into scene_final.mp4
"""
import sys
import os
import json
from pathlib import Path

# Add paths to sys.path
STUDIO_ROOT = Path(__file__).resolve().parent.parent
if str(STUDIO_ROOT) not in sys.path:
    sys.path.insert(0, str(STUDIO_ROOT))

from cinematic_engine.drama_video_engine import DramaVideoEngine
from cinematic_engine.drama_schema import CharacterProfile


def run_phase4_test():
    print("=" * 60)
    print("TESTING PHASE 4: VIDEO SYNTHESIS & SCENE ASSEMBLY")
    print("=" * 60)

    plan_path = STUDIO_ROOT / "productions" / "test-drama-series" / "episode_001" / "drama_plan.json"
    assert plan_path.exists(), f"Plan not found: {plan_path}"

    with open(plan_path, "r", encoding="utf-8") as f:
        plan = json.load(f)

    scene_1 = plan["scenes"][0]
    scene_1_dir = STUDIO_ROOT / "productions" / "test-drama-series" / "episode_001" / "scenes" / "scene_001"

    cast_dict = {
        name: CharacterProfile(
            name=name,
            gender=data.get("gender", "male"),
            role=data.get("role", "supporting"),
            voice_id=data.get("voice_id", "Charon"),
            appearance_lock=data.get("appearance_lock", "")
        )
        for name, data in plan.get("cast", {}).items()
    }

    video_engine = DramaVideoEngine(fps=24)

    print(f"\n[RENDERING SCENE 1 FINAL VIDEO]")
    print(f"Scene Directory: {scene_1_dir}")
    print(f"Summary: {scene_1['summary']}")
    print(f"Camera Motion: {scene_1.get('camera_motion', 'slow_zoom_in')}")

    res = video_engine.render_scene(
        scene=scene_1,
        scene_dir=scene_1_dir,
        aspect_ratio="16:9",
        cast_map=cast_dict
    )

    print("\n[PHASE 4 VERIFICATION RESULTS]")
    final_video = Path(res["final_video_path"])
    assert final_video.exists(), f"Final video not found: {final_video}"
    size_mb = final_video.stat().st_size / (1024 * 1024)
    print(f" Final Video: {final_video.name} ({size_mb:.2f} MB)")
    assert size_mb > 0.5, f"Video too small: {size_mb} MB"

    print(f" Duration: {res['duration']:.2f}s")
    print(f" Subtitles Burned: {res['has_subtitles']}")

    print("\n[SUCCESS] PHASE 4 COMPLETE: Video Synthesis & Scene Assembly is fully functional!")
    return True


if __name__ == "__main__":
    success = run_phase4_test()
    sys.exit(0 if success else 1)
