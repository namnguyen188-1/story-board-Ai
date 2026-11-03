# -*- coding: utf-8 -*-
with open(r'studio/muse_video_provider.py', 'r', encoding='utf-8') as f:
    txt = f.read()

# Remove misplaced block from line 307
bad_block = '''        if acc and acc.get("profile_home"):

        ref_img = scene.get("reference_image")
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
            req = {"account_home": str(acc["profile_home"]), "account_id": target_id}'''

good_top = '''        if acc and acc.get("profile_home"):
            req = {"account_home": str(acc["profile_home"]), "account_id": target_id}'''

assert bad_block in txt, "bad_block not found in muse_video_provider.py"
txt = txt.replace(bad_block, good_top, 1)

# Now insert ref_img and char_anchors resolution right above req = { in render_video_scene
target_vid = '''        lock_name = f"muse_render_{acc['id']}.lock" if acc["id"] != "default" else "muse_render.lock"

        req = {'''

replacement_vid = '''        ref_img = scene.get("reference_image")
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

        lock_name = f"muse_render_{acc['id']}.lock" if acc["id"] != "default" else "muse_render.lock"

        req = {'''

assert target_vid in txt, "target_vid not found in muse_video_provider.py"
txt = txt.replace(target_vid, replacement_vid, 1)

with open(r'studio/muse_video_provider.py', 'w', encoding='utf-8') as f:
    f.write(txt)
print("Cleaned up muse_video_provider.py successfully!")
