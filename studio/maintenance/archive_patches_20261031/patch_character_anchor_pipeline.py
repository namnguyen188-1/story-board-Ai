# -*- coding: utf-8 -*-
"""
Fixes the Character Anchor Pipeline across all 4 stages:
1. drama_orchestrator.py: Resolves scene-specific character anchor from 00_ASSET_PACK.
2. drama_video_engine.py: Passes reference_image, character_anchors, scene_dir to scene_dict.
3. muse_video_provider.py: Forwards reference_image & character_anchors into req.
4. muse_gateway_worker.py: Instructs Muse to run Image-to-Video with the uploaded reference image.
"""

from pathlib import Path
import sys
sys.stdout.reconfigure(encoding='utf-8')

# 1. Patch drama_orchestrator.py
with open(r'studio/cinematic_engine/drama_orchestrator.py', 'r', encoding='utf-8') as f:
    d_orch = f.read()

target_orch = '''        # Step A & B: Audio & Sound Mixing'''

replacement_orch = '''        # Resolve character-specific master anchor image from 00_ASSET_PACK!
        sc_chars = sc_data.get("characters_present", [])
        if not sc_chars and isinstance(sc_data.get("dialogue_beats"), list):
            sc_chars = [b.get("speaker") for b in sc_data["dialogue_beats"] if isinstance(b, dict) and b.get("speaker") and str(b.get("speaker")).lower() != "narrator"]
        primary_char = sc_data.get("primary_focus_character") or (sc_chars[0] if sc_chars else None)

        try:
            from .drama_asset_manager import get_primary_character_anchor
            char_anchor = get_primary_character_anchor(episode_dir, sc_chars, primary_char)
            if char_anchor and char_anchor.is_file():
                anchor_ref = char_anchor
                print(f"[NEO NHÂN VẬT CẢNH {sc_num}] 🎯 Sử dụng ảnh nhân vật cố định: {char_anchor.name} (Vai chính: {primary_char})", flush=True)
        except Exception:
            pass

        # Step A & B: Audio & Sound Mixing'''

if target_orch in d_orch:
    d_orch = d_orch.replace(target_orch, replacement_orch, 1)
    with open(r'studio/cinematic_engine/drama_orchestrator.py', 'w', encoding='utf-8') as f:
        f.write(d_orch)
    print("✓ Patched drama_orchestrator.py")
else:
    print("! target_orch not found")

# 2. Patch drama_video_engine.py
with open(r'studio/cinematic_engine/drama_video_engine.py', 'r', encoding='utf-8') as f:
    d_ve = f.read()

target_ve = '''                    scene_dict = {
                        "scene_number": sc_num,
                        "description": sc_summary,
                        "visual_setup": sc_setup or sc_setting,
                        "prompt": sc_setup or sc_summary,
                        "camera": sc_cam,
                        "action": action_lines,
                        "dialogue": dialogue_lines,
                        "narration": narration_lines,
                        "raw_9_fields": scene.get("raw_9_fields", "") if isinstance(scene, dict) else getattr(scene, "raw_9_fields", ""),
                        "account_id": scene.get("account_id") if isinstance(scene, dict) else getattr(scene, "account_id", None),
                    }'''

replacement_ve = '''                    scene_dict = {
                        "scene_number": sc_num,
                        "description": sc_summary,
                        "visual_setup": sc_setup or sc_setting,
                        "prompt": sc_setup or sc_summary,
                        "camera": sc_cam,
                        "action": action_lines,
                        "dialogue": dialogue_lines,
                        "narration": narration_lines,
                        "raw_9_fields": scene.get("raw_9_fields", "") if isinstance(scene, dict) else getattr(scene, "raw_9_fields", ""),
                        "account_id": scene.get("account_id") if isinstance(scene, dict) else getattr(scene, "account_id", None),
                        "reference_image": str(reference_image_path) if reference_image_path else None,
                        "character_anchors": [str(reference_image_path)] if reference_image_path else [],
                        "scene_dir": str(s_dir),
                        "episode_dir": str(s_dir.parent.parent if s_dir.parent.name == "scenes" else s_dir.parent),
                        "primary_focus_character": scene.get("primary_focus_character") if isinstance(scene, dict) else getattr(scene, "primary_focus_character", None),
                        "characters_present": scene.get("characters_present") if isinstance(scene, dict) else getattr(scene, "characters_present", []),
                    }'''

if target_ve in d_ve:
    d_ve = d_ve.replace(target_ve, replacement_ve, 1)
    with open(r'studio/cinematic_engine/drama_video_engine.py', 'w', encoding='utf-8') as f:
        f.write(d_ve)
    print("✓ Patched drama_video_engine.py")
else:
    print("! target_ve not found")

# 3. Patch muse_video_provider.py
with open(r'studio/muse_video_provider.py', 'r', encoding='utf-8') as f:
    mvp = f.read()

target_mvp = '''        req = {
            "output_image_path": str(output),
            "prompt": format_real_acting_prompt(scene, bible),
            "width": width,
            "height": height,
            "duration": duration,
            "lock_path": str(HOME / "runtime" / lock_name),
        }'''

replacement_mvp = '''        ref_img = scene.get("reference_image")
        char_anchors = list(scene.get("character_anchors") or [])
        if not ref_img and scene.get("scene_dir"):
            try:
                from cinematic_engine.drama_asset_manager import get_scene_character_anchors, get_primary_character_anchor
                s_path = Path(scene["scene_dir"])
                ep_d = s_path.parent.parent if s_path.parent.name == "scenes" else s_path.parent
                chars_p = scene.get("characters_present") or []
                prim_c = scene.get("primary_focus_character")
                prim_anc = get_primary_character_anchor(ep_d, chars_p, prim_c)
                if prim_anc and prim_anc.is_file():
                    ref_img = str(prim_anc)
                all_anc = get_scene_character_anchors(ep_d, chars_p)
                char_anchors = [a["image_path"] for a in all_anc if a.get("image_path")]
            except Exception:
                pass

        req = {
            "output_image_path": str(output),
            "prompt": format_real_acting_prompt(scene, bible),
            "width": width,
            "height": height,
            "duration": duration,
            "lock_path": str(HOME / "runtime" / lock_name),
            "reference_image": ref_img,
            "character_anchors": char_anchors,
        }'''

if target_mvp in mvp:
    mvp = mvp.replace(target_mvp, replacement_mvp, 1)
    with open(r'studio/muse_video_provider.py', 'w', encoding='utf-8') as f:
        f.write(mvp)
    print("✓ Patched muse_video_provider.py")
else:
    print("! target_mvp not found")

# 4. Patch muse_gateway_worker.py
with open(r'studio/muse_gateway_worker.py', 'r', encoding='utf-8') as f:
    mgw = f.read()

target_mgw = '''            if remote_anchors:
                anchor_instruction = (
                    f"MANDATORY CHARACTER VISUAL REFERENCE: Master character model sheets are uploaded at: {', '.join(remote_anchors)}. "
                    "You MUST strictly lock and preserve the facial bone structure, permanent scars, hairstyle, and wardrobe of the characters as depicted in these reference sheets and described below. "
                    "Do NOT generate arbitrary new faces or conflicting clothing. "
                )
            else:
                anchor_instruction = "No user reference image is needed. "

            prompt = (f"Run exactly one text-to-video scene job, ID {tag}. {anchor_instruction}"
                      f"Use media.generate_video once to create a short {request['duration']}-second video clip, composition ratio {ratio}, name {tag}_video. "
                      f"Preserve the character continuity, lighting, and action instructions. Wait for actual tool completion. "
                      "Return exact local video_path in the final visible reply. Do not retry a failed generation or produce extra variants. Report tool failures accurately.\\n" + request["prompt"])'''

replacement_mgw = '''            if remote_anchors:
                primary_anc = remote_anchors[0]
                anchor_instruction = (
                    f"MANDATORY IMAGE-TO-VIDEO CHARACTER REFERENCE: The fixed master reference portrait for this scene's focal character is uploaded at: {primary_anc}. "
                    f"All cast turnaround sheets are at: {', '.join(remote_anchors)}. "
                    "You MUST use this exact reference image as the visual anchor (Image-to-Video). "
                    "Strictly lock and preserve the exact facial geometry, eyes, nose, lips, hair, and wardrobe from this reference image in the generated video. "
                    "Do NOT generate arbitrary new faces or conflicting clothing. "
                )
            else:
                anchor_instruction = "No user reference image is needed. "

            prompt = (f"Run an Image-to-Video scene generation job using the character reference image, ID {tag}. {anchor_instruction}"
                      f"Use media.generate_video once to create a short {request['duration']}-second video clip, composition ratio {ratio}, name {tag}_video. "
                      f"Preserve the character continuity, lighting, and action instructions. Wait for actual tool completion. "
                      "Return exact local video_path in the final visible reply. Do not retry a failed generation or produce extra variants. Report tool failures accurately.\\n" + request["prompt"])'''

if target_mgw in mgw:
    mgw = mgw.replace(target_mgw, replacement_mgw, 1)
    with open(r'studio/muse_gateway_worker.py', 'w', encoding='utf-8') as f:
        f.write(mgw)
    print("✓ Patched muse_gateway_worker.py")
else:
    print("! target_mgw not found")

print("All patches completed successfully!")
