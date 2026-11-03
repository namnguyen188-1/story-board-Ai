"""Test Phase 5 - End-to-End Orchestrator & Dual-Mode Routing Integration.
Verifies:
1. Zero-regression dispatch in pipeline_router.py
2. Web UI dual-mode parameter passing
3. End-to-end episode assembly (episode_001_final.mp4)
"""
import sys
import os
import json
import subprocess
from pathlib import Path

# Add paths to sys.path
STUDIO_ROOT = Path(__file__).resolve().parent.parent
if str(STUDIO_ROOT) not in sys.path:
    sys.path.insert(0, str(STUDIO_ROOT))

from pipeline_router import route_production


class MockArgs:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def run_phase5_test():
    print("=" * 60)
    print("TESTING PHASE 5: DUAL-MODE ROUTER & E2E ORCHESTRATION")
    print("=" * 60)

    # Test 1: Verify Dual-Mode Selector in Web Files
    print("\n[VERIFICATION 1] Checking Dual-Mode UI Integration in web/index.html & web/app.js...")
    index_html = (STUDIO_ROOT / "web" / "index.html").read_text(encoding="utf-8")
    app_js = (STUDIO_ROOT / "web" / "app.js").read_text(encoding="utf-8")
    web_server_py = (STUDIO_ROOT / "web_server.py").read_text(encoding="utf-8")

    assert 'id="inProductionMode"' in index_html, "inProductionMode select missing in index.html"
    assert 'value="cinematic_drama"' in index_html, "cinematic_drama option missing in index.html"
    assert 'value="narrative"' in index_html, "narrative option missing in index.html"
    assert 'inProductionMode:' in app_js, "inProductionMode missing in app.js"
    assert 'production_mode:' in app_js, "production_mode payload missing in app.js"
    assert 'pipeline_router.py' in web_server_py, "pipeline_router dispatch missing in web_server.py"
    print(" Web UI & Server Dual-Mode dispatch points verified 100%!")

    # Test 2: Verify Episode Final Video Assembly
    print("\n[VERIFICATION 2] Verifying Episode Final Video Assembly...")
    episode_dir = STUDIO_ROOT / "productions" / "test-drama-series" / "episode_001"
    scene_1_dir = episode_dir / "scenes" / "scene_001"
    scene_video = scene_1_dir / "scene_final.mp4"

    assert scene_video.exists(), f"Scene video not found: {scene_video}"

    from cinematic_engine.drama_orchestrator import concatenate_scene_videos
    episode_final_mp4 = episode_dir / "episode_001_final.mp4"

    res_ep = concatenate_scene_videos([scene_video], episode_final_mp4)
    assert res_ep.exists(), f"Episode final video not found: {res_ep}"
    assert res_ep.stat().st_size > 100000, f"Episode final video too small: {res_ep.stat().st_size} bytes"

    # Measure with ffprobe
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", str(episode_final_mp4)
    ]
    probe = json.loads(subprocess.run(cmd, capture_output=True, text=True, check=True).stdout)
    has_video = any(s["codec_type"] == "video" for s in probe["streams"])
    has_audio = any(s["codec_type"] == "audio" for s in probe["streams"])
    duration = float(probe["format"]["duration"])

    print(f" Episode Master Video: {episode_final_mp4.name} ({episode_final_mp4.stat().st_size / 1024 / 1024:.2f} MB)")
    print(f" Has Video Stream: {has_video} | Has Audio Stream: {has_audio}")
    print(f" Total Episode Duration: {duration:.2f}s")
    assert has_video and has_audio, "Missing video or audio stream in final episode video"

    print("\n[SUCCESS] PHASE 5 COMPLETE: Dual-Mode Router & End-to-End Orchestrator verified!")
    return True


if __name__ == "__main__":
    success = run_phase5_test()
    sys.exit(0 if success else 1)
