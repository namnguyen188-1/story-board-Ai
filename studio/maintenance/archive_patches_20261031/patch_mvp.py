# -*- coding: utf-8 -*-
with open(r'studio/muse_video_provider.py', 'r', encoding='utf-8') as f:
    mvp = f.read()

target = '''            if t_json:

                app = t_json.get("appearance_dna", "")

                att = t_json.get("attire", "")

                if att and "locked complete wardrobe" not in att.lower():

                    app = f"{app} Wardrobe: {att}".strip()

                chars_info.append(f"{name}: {app}")

            elif isinstance(prof, dict):

                app = prof.get("appearance_lock") or prof.get("appearance") or prof.get("description") or ""'''

replacement = '''            try:
                from studio.cinematic_engine.character_isolator import extract_single_character_description
            except ImportError:
                try:
                    from cinematic_engine.character_isolator import extract_single_character_description
                except ImportError:
                    def extract_single_character_description(txt, n): return txt

            if t_json:

                app = t_json.get("appearance_dna", "")

                att = t_json.get("attire", "")

                if att and "locked complete wardrobe" not in att.lower():

                    app = f"{app} Wardrobe: {att}".strip()

                app = extract_single_character_description(app, name)
                chars_info.append(f"{name}: {app}")

            elif isinstance(prof, dict):

                app = prof.get("appearance_lock") or prof.get("appearance") or prof.get("description") or ""
                app = extract_single_character_description(app, name)'''

assert target in mvp, "Target not found in muse_video_provider.py!"
mvp = mvp.replace(target, replacement, 1)
with open(r'studio/muse_video_provider.py', 'w', encoding='utf-8') as f:
    f.write(mvp)
print("Successfully patched muse_video_provider.py!")
