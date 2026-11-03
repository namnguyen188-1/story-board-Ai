# -*- coding: utf-8 -*-
with open(r'studio/cinematic_engine/drama_skill9.py', 'r', encoding='utf-8') as f:
    s9 = f.read()

target_s9 = '''        appearance = prof.get("appearance_lock") or prof.get("appearance") or ""
        clean_app = appearance.strip()'''

replacement_s9 = '''        appearance = prof.get("appearance_lock") or prof.get("appearance") or ""
        try:
            from studio.cinematic_engine.character_isolator import extract_single_character_description
        except ImportError:
            try:
                from cinematic_engine.character_isolator import extract_single_character_description
            except ImportError:
                def extract_single_character_description(txt, n): return txt
        clean_app = extract_single_character_description(appearance, name).strip()'''

assert target_s9 in s9, "target_s9 not found in drama_skill9.py"
s9 = s9.replace(target_s9, replacement_s9, 1)
with open(r'studio/cinematic_engine/drama_skill9.py', 'w', encoding='utf-8') as f:
    f.write(s9)
print("Successfully patched drama_skill9.py!")

with open(r'studio/cinematic_engine/drama_asset_manager.py', 'r', encoding='utf-8') as f:
    dam = f.read()

target_dam = '''    app_dna = str(
        char_profile.get("appearance_lock") or
        char_profile.get("appearance") or
        char_profile.get("description") or
        "Authentic actor with distinct features"
    ).strip()'''

replacement_dam = '''    raw_app = str(
        char_profile.get("appearance_lock") or
        char_profile.get("appearance") or
        char_profile.get("description") or
        "Authentic actor with distinct features"
    ).strip()
    try:
        from studio.cinematic_engine.character_isolator import extract_single_character_description
    except ImportError:
        try:
            from cinematic_engine.character_isolator import extract_single_character_description
        except ImportError:
            def extract_single_character_description(txt, n): return txt
    app_dna = extract_single_character_description(raw_app, char_name).strip()'''

assert target_dam in dam, "target_dam not found in drama_asset_manager.py"
dam = dam.replace(target_dam, replacement_dam, 1)
with open(r'studio/cinematic_engine/drama_asset_manager.py', 'w', encoding='utf-8') as f:
    f.write(dam)
print("Successfully patched drama_asset_manager.py!")
