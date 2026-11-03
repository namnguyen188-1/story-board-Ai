# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

# Patch drama_video_engine.py
with open(r'studio/cinematic_engine/drama_video_engine.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
inserted_ve = False
for line in lines:
    new_lines.append(line)
    if '"account_id": scene.get("account_id")' in line and not inserted_ve:
        new_lines.append('                        "reference_image": str(reference_image_path) if reference_image_path else None,\n')
        new_lines.append('                        "character_anchors": [str(reference_image_path)] if reference_image_path else [],\n')
        new_lines.append('                        "scene_dir": str(s_dir),\n')
        new_lines.append('                        "episode_dir": str(s_dir.parent.parent if s_dir.parent.name == "scenes" else s_dir.parent),\n')
        new_lines.append('                        "primary_focus_character": scene.get("primary_focus_character") if isinstance(scene, dict) else getattr(scene, "primary_focus_character", None),\n')
        new_lines.append('                        "characters_present": scene.get("characters_present") if isinstance(scene, dict) else getattr(scene, "characters_present", []),\n')
        inserted_ve = True

assert inserted_ve, "Could not find account_id insertion point in drama_video_engine.py"
with open(r'studio/cinematic_engine/drama_video_engine.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print("✓ Successfully patched drama_video_engine.py!")

# Patch muse_video_provider.py
with open(r'studio/muse_video_provider.py', 'r', encoding='utf-8') as f:
    lines_mvp = f.readlines()

new_mvp = []
inserted_mvp = False
for idx, line in enumerate(lines_mvp):
    if 'req = {' in line and not inserted_mvp:
        new_mvp.append('        ref_img = scene.get("reference_image")\n')
        new_mvp.append('        char_anchors = list(scene.get("character_anchors") or [])\n')
        new_mvp.append('        if not ref_img and scene.get("scene_dir"):\n')
        new_mvp.append('            try:\n')
        new_mvp.append('                from cinematic_engine.drama_asset_manager import get_scene_character_anchors, get_primary_character_anchor\n')
        new_mvp.append('                s_path = Path(scene["scene_dir"])\n')
        new_mvp.append('                ep_d = s_path.parent.parent if s_path.parent.name == "scenes" else s_path.parent\n')
        new_mvp.append('                chars_p = scene.get("characters_present") or []\n')
        new_mvp.append('                prim_c = scene.get("primary_focus_character")\n')
        new_mvp.append('                prim_anc = get_primary_character_anchor(ep_d, chars_p, prim_c)\n')
        new_mvp.append('                if prim_anc and prim_anc.is_file():\n')
        new_mvp.append('                    ref_img = str(prim_anc)\n')
        new_mvp.append('                all_anc = get_scene_character_anchors(ep_d, chars_p)\n')
        new_mvp.append('                char_anchors = [a["image_path"] for a in all_anc if a.get("image_path")]\n')
        new_mvp.append('            except Exception:\n')
        new_mvp.append('                pass\n')
        new_mvp.append(line)
        inserted_mvp = True
    elif '"lock_path": str(HOME / "runtime" / lock_name),' in line:
        new_mvp.append(line)
        new_mvp.append('            "reference_image": ref_img,\n')
        new_mvp.append('            "character_anchors": char_anchors,\n')
    else:
        new_mvp.append(line)

assert inserted_mvp, "Could not find req = { in muse_video_provider.py"
with open(r'studio/muse_video_provider.py', 'w', encoding='utf-8') as f:
    f.writelines(new_mvp)
print("✓ Successfully patched muse_video_provider.py!")
