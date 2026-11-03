# -*- coding: utf-8 -*-
"""
LIVE E2E TEST: Character Anchor Image-to-Video Validation
=========================================================
Tests the entire pipeline live against Muse:
1. Resolves Bà Hòa's fixed master reference image (b_h_a_turnaround.jpg).
2. Forwards it through make_scene_media.
3. Uploads it in 24KB Noise-safe chunks to character_anchors/b_h_a_turnaround.jpg on the remote Muse VM.
4. Verifies that Muse receives the MANDATORY IMAGE-TO-VIDEO REFERENCE instruction.
5. Verifies Muse session chat history and downloads the resulting video clip.
"""

import sys
import json
import shutil
from pathlib import Path

STUDIO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(STUDIO_ROOT))
sys.path.insert(0, str(STUDIO_ROOT / "cinematic_engine"))
# Add bundled muse_cli site-packages
muse_site = STUDIO_ROOT / "runtime" / "muse" / "python" / "Lib" / "site-packages"
if muse_site.is_dir():
    sys.path.insert(0, str(muse_site))

from muse_video_provider import make_scene_media
from muse_gateway_worker import GatewayAPI

def main():
    print("=" * 60)
    print("🚀 LIVE E2E TEST: CHARACTER ANCHOR IMAGE-TO-VIDEO PIPELINE")
    print("=" * 60)

    ep_dir = STUDIO_ROOT / "productions" / "kh-m-ph" / "episode_004"
    anchor_file = ep_dir / "00_ASSET_PACK" / "characters" / "b_h_a_turnaround.jpg"
    assert anchor_file.is_file(), f"Missing anchor file: {anchor_file}"
    print(f"✓ Found Master Character Anchor: {anchor_file.name} ({anchor_file.stat().st_size} bytes)")

    # Target test scene directory
    test_scene_dir = STUDIO_ROOT / "productions" / "test_anchor_e2e" / "scenes" / "scene_0002"
    if test_scene_dir.exists():
        shutil.rmtree(test_scene_dir, ignore_errors=True)
    test_scene_dir.mkdir(parents=True, exist_ok=True)

    output_base_img = test_scene_dir / "scene_base.png"

    # Read Scene 2 from episode_004 drama_plan.json
    plan_data = json.load(open(ep_dir / "drama_plan.json", encoding="utf-8"))
    sc2_data = plan_data["scenes"][1]
    bible = {
        "production_genre": "drama",
        "characters": plan_data.get("cast", {}),
        "visual_style": "Full-color cinematic live-action film"
    }

    # Construct scene_dict exactly as drama_video_engine does
    scene_dict = {
        "scene_number": 2,
        "description": sc2_data.get("summary", ""),
        "visual_setup": sc2_data.get("visual_setup", ""),
        "prompt": sc2_data.get("visual_setup", ""),
        "camera": sc2_data.get("camera_motion", "medium close-up 50mm"),
        "action": "Bà Hòa vội vã bước ra bậc thềm hành lang, chùm chìa khóa đồng va vào nhau lách cách",
        "dialogue": 'BÀ HÒA: "Cô Linh! Đừng chạm vào mép đá, phong ấn ba mươi năm qua chưa từng lay động!"',
        "narration": 'BÀ HÒA: "Cô Linh! Đừng chạm vào mép đá, phong ấn ba mươi năm qua chưa từng lay động!"',
        "primary_focus_character": "BÀ HÒA",
        "characters_present": ["BÀ HÒA"],
        "reference_image": str(anchor_file),
        "character_anchors": [str(anchor_file)],
        "scene_dir": str(test_scene_dir),
        "episode_dir": str(ep_dir),
        "raw_9_fields": ""
    }

    print("\nCalling make_scene_media live...")
    res = make_scene_media(
        scene=scene_dict,
        bible=bible,
        output_image_path=output_base_img,
        width=1280,
        height=720,
        duration=10
    )

    print("\n✓ make_scene_media returned result:", res)
    muse_clip = test_scene_dir / "muse_clip.mp4"
    assert muse_clip.is_file() and muse_clip.stat().st_size > 100000, f"muse_clip.mp4 invalid: {muse_clip}"
    print(f"✓ Video clip produced: {muse_clip.name} ({muse_clip.stat().st_size / 1024 / 1024:.2f} MB)")

    # Read muse_job.json to inspect the session ID and account
    job_info = json.load(open(test_scene_dir / "muse_job.json", encoding="utf-8"))
    sid = job_info.get("session_id")
    vm_id = job_info.get("account_vm_id")
    print(f"✓ Muse Session ID: {sid} (VM ID: {vm_id})")

    # Connect to Muse and verify chat history
    from muse_cli.cli import connect
    # Find matching account profile for this VM ID
    matched_cfg = None
    for prof_dir in (STUDIO_ROOT / "runtime" / "muse_profiles").glob("account_*"):
        cfg_p = prof_dir / ".config" / "muse-cli" / "config.json"
        cook_p = prof_dir / ".config" / "muse-cli" / "cookies.txt"
        if cfg_p.is_file() and cook_p.is_file():
            c = json.loads(cfg_p.read_text(encoding="utf-8"))
            if c.get("vm_id") == vm_id or not matched_cfg:
                c["cookies_file"] = str(cook_p)
                matched_cfg = c
                if c.get("vm_id") == vm_id:
                    break

    assert matched_cfg, "Could not find valid Muse profile config!"
    gw = connect(matched_cfg)
    hist = gw.call_json("chat.history", body={"session_id": sid, "limit": 10})
    user_prompts = [
        ev.get("payload", {}).get("display_text") or ""
        for ev in hist.get("chat_events", [])
        if ev.get("event_name") == "message.user"
    ]
    assert user_prompts, "No user message found in session history!"
    sent_prompt = user_prompts[0]
    print("\n--- AUDIT OF ACTUAL PROMPT SENT TO MUSE ---")
    print(sent_prompt[:500] + "...")

    assert "MANDATORY IMAGE-TO-VIDEO CHARACTER REFERENCE" in sent_prompt, "Missing Image-to-Video Anchor instruction!"
    assert "b_h_a_turnaround.jpg" in sent_prompt, "Missing b_h_a_turnaround.jpg anchor filename!"
    assert "No user reference image is needed" not in sent_prompt, "Found forbidden 'No user reference image is needed'!"

    print("\n" + "=" * 60)
    print("ALL E2E CHECKS PASSED: MUSE LIVE VALIDATION CONFIRMED!")
    print("=" * 60)

if __name__ == "__main__":
    main()
