# -*- coding: utf-8 -*-
with open(r'studio/studio_input_modes.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = '''def convert_locked_scenes_to_drama_plan(parsed_scenes, series_name="Cinematic Drama", episode_num=1, language="Vietnamese", genre="drama"):
    """Converts user-supplied locked scenes into a 100% compliant Drama Plan without calling an LLM."""
    cast = {}
    drama_scenes = []

    for sc in parsed_scenes:
        sc_num = sc["scene_number"]
        beats = sc.get("dialogue_beats", [])
        chars_present = []

        for b in beats:
            spk = b.get("speaker", "Character")
            if spk not in chars_present and spk.lower() != "narrator":
                chars_present.append(spk)
            if spk not in cast and spk.lower() != "narrator":
                cast[spk] = {
                    "name": spk,
                    "gender": "male" if any(k in spk.lower() for k in ("anh", "ông", "mr", "marcus", "man", "boy")) else "female",
                    "role": "protagonist" if len(cast) == 0 else "supporting",
                    "voice_id": "Fenrir" if len(cast) == 0 else "Charon",
                    "voice_label": "Giọng nhân vật kịch bản",
                    "personality": "Kịch bản gốc người dùng",
                    "appearance_lock": sc.get("characters", "") or "Theo miêu tả kịch bản"
                }'''

replacement = '''def convert_locked_scenes_to_drama_plan(parsed_scenes, series_name="Cinematic Drama", episode_num=1, language="Vietnamese", genre="drama"):
    """Converts user-supplied locked scenes into a 100% compliant Drama Plan without calling an LLM."""
    try:
        from studio.cinematic_engine.character_isolator import extract_single_character_description
    except ImportError:
        try:
            from cinematic_engine.character_isolator import extract_single_character_description
        except ImportError:
            def extract_single_character_description(txt, name):
                return txt

    cast = {}
    drama_scenes = []

    # Aggregate character texts across scenes
    all_char_blocks = []
    for sc_scan in parsed_scenes:
        c_text = sc_scan.get("characters", "") or ""
        if c_text and c_text not in all_char_blocks:
            all_char_blocks.append(c_text)
    combined_char_text = "\\n".join(all_char_blocks)

    for sc in parsed_scenes:
        sc_num = sc["scene_number"]
        beats = sc.get("dialogue_beats", [])
        chars_present = []

        for b in beats:
            spk = b.get("speaker", "Character")
            if spk not in chars_present and spk.lower() != "narrator":
                chars_present.append(spk)
            if spk not in cast and spk.lower() != "narrator":
                sc_char_text = sc.get("characters", "") or ""
                isolated_dna = extract_single_character_description(sc_char_text, spk)
                if not isolated_dna or (isolated_dna == sc_char_text and combined_char_text):
                    isolated_dna = extract_single_character_description(combined_char_text, spk)

                cast[spk] = {
                    "name": spk,
                    "gender": "male" if any(k in spk.lower() for k in ("anh", "ông", "mr", "marcus", "man", "boy")) else "female",
                    "role": "protagonist" if len(cast) == 0 else "supporting",
                    "voice_id": "Fenrir" if len(cast) == 0 else "Charon",
                    "voice_label": "Giọng nhân vật kịch bản",
                    "personality": "Kịch bản gốc người dùng",
                    "appearance_lock": isolated_dna or "Theo miêu tả kịch bản"
                }'''

assert target in content, "Target not found in content!"
content = content.replace(target, replacement, 1)
with open(r'studio/studio_input_modes.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Successfully patched studio_input_modes.py!")
