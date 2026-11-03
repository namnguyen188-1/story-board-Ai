# -*- coding: utf-8 -*-
"""
Patch Storyboard AI Studio to enforce Hyper-Muscular Chiseled Warrior-Philosopher Physique,
One-Shoulder Draped Crimson Toga, and Dramatic Chest-Up / Medium Framing for Stoic / Classical genre.
"""
import os
import re
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def patch_competitor_cloner():
    path = ROOT / "studio" / "competitor_cloner.py"
    if not path.is_file():
        print(f"[FAIL] {path} not found")
        return
    text = path.read_text(encoding="utf-8")
    
    old_target = 'If and ONLY if the footage shows an actual stone or bronze sculpture: characterize it as a FULL-LENGTH STANDING HEROIC CLASSICAL STATUE (complete anatomical figure standing from head to toe, full legs, feet firmly planted on an ancient plaza base, draped toga) or EQUESTRIAN MONUMENT.\n    - ABSOLUTE BUST BAN: NEVER characterize, describe, or prompt a severed half-body \'bust\', torso-only sculpture, armless figure, or tabletop pedestal!'
    
    new_replacement = '''For 'stoic' / Classical Greco-Roman philosophy (Valor Estoico style): Characterize the protagonist as a HYPER-MUSCULAR CHISELED GREEK/ROMAN WARRIOR-PHILOSOPHER / DEMIGOD (Marcus Aurelius / Hercules archetype). Emphasize the athletic demigod physique: massive broad shoulders, thick muscular neck, sculpted pectoral chest muscles, striated deltoids, powerful vascular arms, chiseled heroic jawline, weathered sun-kissed bronze skin, dark curly hair and thick salt-and-pepper beard.
     * Wardrobe for Stoic genre: Signature royal crimson red draped toga (chlamys) draped across ONE shoulder, leaving the sculpted muscular chest and powerful shoulder/arm bare and prominently displayed.
     * Dynamic Framing: Prioritize dramatic chest-up medium close-up (bust/torso composition) and heroic 3/4 medium shots where the muscular physique and intense facial expression dominate the screen. NEVER force tiny distant full-length figures that appear scrawny or weak!
     * If the footage features a living human, actor, or scholar: classify as a LIVING HUMAN with natural human skin tones and organic textile wardrobe. NEVER classify a living person as a cold stone statue!
     * If the footage features a classical fine-art painting: preserve the painted fine-art medium.
     * If and ONLY if the footage shows an actual monumental sculpture: capture its powerful heroic anatomical sculpting with dynamic chest-up or medium heroic framing.'''

    # Flexible regex replacement
    pattern = re.compile(r'If and ONLY if the footage shows an actual stone or bronze sculpture:[^\n]*\n\s*-\s*ABSOLUTE BUST BAN:[^\n]*', re.DOTALL)
    if pattern.search(text):
        text = pattern.sub(new_replacement, text, count=1)
        print("[OK] Replaced cloner prompt classification rules.")
    else:
        print("[WARN] Pattern for cloner prompt classification not matched directly, checking normalized...")
        # try replacing just the bust ban line
        text = re.sub(r'-\s*ABSOLUTE BUST BAN:[^\n]*', '- Dynamic Framing: Prioritize dramatic chest-up medium close-up and heroic 3/4 medium shots where the muscular build and intense facial expression dominate the screen. NEVER force tiny distant full-length figures!', text)

    # Also update keys in the cloner JSON prompt
    text = re.sub(
        r'"appearance_lock":\s*"[^"]*NEVER a bust\."',
        '"appearance_lock": "EXHAUSTIVE physical traits observed: hyper-muscular athletic demigod build, massive broad shoulders, thick muscular neck, sculpted chest pecs, striated deltoids, vascular arms, chiseled masculine jawline, weathered bronze skin tone, intense piercing dark eyes, thick salt-and-pepper curly hair and beard."',
        text
    )
    text = re.sub(
        r'"wardrobe_lock":\s*"[^"]*flowing draped classical toga extending down past knees to feet\."',
        '"wardrobe_lock": "EXACT clothing and accessories observed: royal crimson red draped toga (chlamys) draped across one shoulder, leaving the sculpted muscular chest and powerful shoulder/arm bare, with antique golden brooch."',
        text
    )
    text = re.sub(
        r'"immutable_rules":\s*"[^"]*NEVER render half-body busts\."',
        '"immutable_rules": "Strict continuity rules: maintain hyper-muscular warrior build, one-shoulder draped crimson toga exposing muscular chest/arm, intense facial expression, and dynamic chest-up / medium framing. Never render tiny distant figures or skinny scrawny anatomy."',
        text
    )
    text = re.sub(
        r'"clone_prompt":\s*"[^"]*FULL-LENGTH standing statue from head to toe[^\"]*"',
        '"clone_prompt": "High-impact positive prompt chunk: cinematic 16:9 composition, hyper-muscular chiseled Roman philosopher emperor, massive broad shoulders, thick muscular neck, sculpted chest pecs, striated deltoids, vascular arms, royal crimson red toga draped over one shoulder leaving muscular chest and arm exposed, dramatic golden chiaroscuro lighting, illuminated ancient Acropolis colonnades at twilight."',
        text
    )

    path.write_text(text, encoding="utf-8")
    print("[OK] competitor_cloner.py updated.")

def patch_studio_modes():
    path = ROOT / "studio" / "studio_modes.py"
    if not path.is_file():
        print(f"[FAIL] {path} not found")
        return
    text = path.read_text(encoding="utf-8")
    
    old_art = re.search(r'"stoic"\s*:\s*"[^"]*"', text)
    new_art = (
        '"stoic":"Cinematic Greco-Roman classical epic world (16:9 widescreen). '
        'Depicts hyper-muscular chiseled ancient Roman and Greek philosopher emperors (Marcus Aurelius archetype) '
        'with heroic demigod physiques (massive broad shoulders, thick muscular neck, sculpted chest pecs, striated deltoids, vascular arms), '
        'wearing royal crimson red togas draped across one shoulder leaving the muscular chest and arm bare. '
        'Weathered bronze skin, piercing gaze, amidst magnificent ancient colonnades, temples, and glowing night Acropolis vistas. '
        'Dynamic cinematic framing with dramatic chest-up medium close-ups, medium portraits, and majestic wide architectural compositions. '
        'Deep atmospheric chiaroscuro, volumetric golden rim light, and rich film depth."'
    )
    if old_art:
        text = text[:old_art.start()] + new_art + text[old_art.end():]
        path.write_text(text, encoding="utf-8")
        print("[OK] studio_modes.py ART['stoic'] updated.")
    else:
        print("[WARN] ART['stoic'] not found in studio_modes.py")

def patch_mcp_v2_batch():
    path = ROOT / "studio" / "mcp_v2_batch.py"
    if not path.is_file():
        print(f"[FAIL] {path} not found")
        return
    text = path.read_text(encoding="utf-8")

    # Update statue_instruction for stoic
    new_statue_instruction = (
        '    if genre == "stoic":\n'
        '        statue_instruction = (\n'
        '            ". EPIC LIVE-ACTION STOIC CINEMATIC: Depict a hyper-muscular, chiseled heroic Roman philosopher emperor "\n'
        '            "(Marcus Aurelius archetype) with an athletic Greek demigod physique: massive broad shoulders, thick muscular neck, "\n'
        '            "deeply sculpted pectoral chest muscles, striated deltoids, vascular arms, weathered sun-kissed bronze skin, "\n'
        '            "intense piercing dark eyes, salt-and-pepper beard, wearing a royal crimson red draped toga (chlamys) draped across one shoulder, "\n'
        '            "leaving the muscular chest and arm bare. Dynamic framing with dramatic chest-up medium close-up (bust) "\n'
        '            "and medium heroic compositions against majestic ancient colonnades and illuminated night Acropolis with golden rim light."\n'
        '        )'
    )
    text = re.sub(
        r'    if genre == "stoic":\s*statue_instruction = \([^\)]+\)',
        new_statue_instruction,
        text
    )

    # Add stoic prompt sanitizer in image_prompt
    if "def _stoic_enhance(txt:" not in text:
        helper = '''
    def _stoic_enhance(txt: str) -> str:
        if not txt or genre != "stoic":
            return txt
        txt = re.sub(r'(?i)\\bfull[- ]length\\s+standing\\s+(classical\\s+)?(marble\\s+)?statue\\s+(of\\s+an?\\s+ancient\\s+bearded\\s+stoic\\s+philosopher\\s+)?from\\s+head\\s+to\\s+toe,\\s+legs\\s+grounded\\s+on\\s+ancient\\s+temple\\s+base\\b',
                     'hyper-muscular chiseled Stoic philosopher emperor with massive broad shoulders, thick neck, and sculpted chest pecs', txt)
        txt = re.sub(r'(?i)\\bfull[- ]length\\s+standing\\s+(classical\\s+)?(marble\\s+)?statue\\b',
                     'hyper-muscular chiseled Roman philosopher emperor with massive broad shoulders and sculpted pecs', txt)
        txt = re.sub(r'(?i)\\bclassical\\s+marble\\s+statue\\b',
                     'heroic chiseled Roman philosopher emperor with weathered bronze skin and muscular build', txt)
        txt = re.sub(r'(?i)\\bstanding\\s+resolute\\s+on\\s+its\\s+weathered\\s+stone\\s+pedestal\\b',
                     'commanding presence in heroic medium close-up against illuminated ancient colonnades', txt)
        txt = re.sub(r'(?i)\\bstone\\s+pedestals?\\b', 'ancient marble colonnade', txt)
        txt = re.sub(r'(?i)\\bdraped\\s+stone\\s+toga(\\s+flowing\\s+down\\s+past\\s+knees\\s+to\\s+stone\\s+base)?\\b',
                     'royal crimson red toga draped over one shoulder leaving muscular chest and sculpted arm exposed', txt)
        txt = re.sub(r'(?i)\\bAlways\\s+render\\s+complete\\s+full[- ]length\\s+standing\\s+classical\\s+statue[^\\.]*\\.\\b',
                     'Always render hyper-muscular chiseled demigod physique (massive shoulders, thick neck, sculpted pecs, vascular arms) with royal crimson toga draped over one shoulder in dynamic medium or chest-up framing.', txt)
        txt = re.sub(r'(?i)\\bAbsolutely\\s+no\\s+severed\\s+half[- ]body\\s+busts[^\\.]*\\.\\b', '', txt)
        return txt
'''
        # Insert before raw_desc
        target = 'raw_desc = sanitize_statue_terms(str(scene.get("description","")))'
        if target in text:
            text = text.replace(target, helper + '\n    raw_desc = _stoic_enhance(str(scene.get("description","")))\n    raw_desc = sanitize_statue_terms(raw_desc)')
            text = text.replace('raw_setup = sanitize_statue_terms(str(scene.get("visual_setup","")))',
                                'raw_setup = _stoic_enhance(str(scene.get("visual_setup","")))\n    raw_setup = sanitize_statue_terms(raw_setup)')
            text = text.replace('cleaned_chars = [sanitize_statue_terms(c) for c in characters]',
                                'cleaned_chars = [sanitize_statue_terms(_stoic_enhance(c)) for c in characters]')
            print("[OK] Inserted _stoic_enhance sanitizer into mcp_v2_batch.py")

    path.write_text(text, encoding="utf-8")
    print("[OK] mcp_v2_batch.py updated.")

def patch_comfyui_image_provider():
    path = ROOT / "studio" / "comfyui_image_provider.py"
    if not path.is_file():
        print(f"[FAIL] {path} not found")
        return
    text = path.read_text(encoding="utf-8")

    old_stoic_block = re.search(
        r'elif is_statue or genre == "stoic":\s*positive = \([^\)]+\)\s*negative = \([^\)]+\)',
        text
    )
    if old_stoic_block:
        new_stoic_block = (
            'elif is_statue or genre == "stoic":\n'
            '        positive = (\n'
            '            f"Cinematic live-action 16:9 historical epic film still, heroic Roman philosopher emperor (Marcus Aurelius archetype), "\n'
            '            f"hyper-muscular chiseled Greek demigod physique, massive broad shoulders, thick muscular neck, sculpted pectoral chest muscles, "\n'
            '            f"striated deltoids, vascular arms, weathered sun-kissed bronze skin with realistic pores, intense piercing dark eyes, "\n'
            '            f"distinguished salt-and-pepper curly hair and thick groomed beard, royal crimson red draped toga (chlamys) draped across one shoulder leaving muscular chest and arm bare, "\n'
            '            f"dramatic chest-up medium close-up composition, standing in ancient Roman forum with illuminated marble pillars, sweeping view of distant Acropolis at twilight, "\n'
            '            f"dramatic chiaroscuro lighting, warm amber golden key light, deep sapphire teal shadows, soft volumetric rim glow, "\n'
            '            f"photorealistic 8k, master cinematography, shot on 35mm lens: {clean_prompt}"\n'
            '        )\n'
            '        negative = (\n'
            '            "scrawny, skinny, frail, weak, unmuscular, flat chest, narrow shoulders, lifeless stone statue, severed bust, tabletop pedestal, blank carved eyes, white stone skin, statue stand, "\n'
            '            "zombie, deformed, cartoon, 3d cgi render, anime, modern clothes, t-shirt, plastic, blurry, low quality, "\n'
            '            "ugly, bad anatomy, bad eyes, extra limbs, watermark, text, signature"\n'
            '        )'
        )
        text = text[:old_stoic_block.start()] + new_stoic_block + text[old_stoic_block.end():]
        path.write_text(text, encoding="utf-8")
        print("[OK] comfyui_image_provider.py stoic block updated.")
    else:
        print("[WARN] Stoic block in comfyui_image_provider.py not matched")

def patch_muse_video_provider():
    path = ROOT / "studio" / "muse_video_provider.py"
    if not path.is_file():
        print(f"[FAIL] {path} not found")
        return
    text = path.read_text(encoding="utf-8")

    # Update default_chars
    text = re.sub(
        r'default_chars = "Marcus Aurelius / Classical Roman Philosopher Emperor \([^"]+\)"',
        'default_chars = "Marcus Aurelius / Classical Roman Philosopher Emperor (hyper-muscular chiseled demigod warrior build, massive broad shoulders, thick muscular neck, sculpted chest pecs, striated deltoids, vascular arms, weathered bronze skin, piercing contemplative gaze, salt-and-pepper curly beard, royal crimson draped toga draped over one shoulder leaving muscular chest and arm bare)"',
        text
    )

    # Update camera and performance
    text = text.replace(
        "delicate volumetric rim light outlining actor's shoulders and curls.",
        "delicate volumetric rim light outlining actor's massive muscular shoulders, sculpted pecs, and curls."
    )
    text = text.replace(
        "Dignified statesman presence, organic subtle breathing and expressive eye gaze",
        "Commanding imperial warrior-philosopher presence, imposing athletic posture, organic subtle breathing and expressive eye gaze"
    )
    text = text.replace(
        'CONSTRAINTS: BANNED: lifeless stone statue',
        'CONSTRAINTS: BANNED: scrawny, skinny, frail, weak, unmuscular, flat chest, lifeless stone statue'
    )

    path.write_text(text, encoding="utf-8")
    print("[OK] muse_video_provider.py updated.")

def patch_series_studio():
    path = ROOT / "studio" / "series_studio.py"
    if not path.is_file():
        print(f"[FAIL] {path} not found")
        return
    text = path.read_text(encoding="utf-8")

    old_rule = '- When portraying monuments, historical statues, or Stoic philosophical scenes: keep statues majestic and structurally solid; do not depict speaking mannequins, but place them in dynamic cinematic environments (atmospheric weather, drifting embers, sweeping light, dramatic scale).'
    new_rule = '- When portraying Stoic philosophical scenes or classical heroes: Depict the protagonist as a HYPER-MUSCULAR CHISELED ROMAN PHILOSOPHER EMPEROR / WARRIOR (Marcus Aurelius archetype) with an imposing athletic demigod build: massive broad shoulders, thick muscular neck, sculpted chest pecs, striated deltoids, vascular arms, wearing a royal crimson red toga draped across one shoulder leaving the muscular chest and arm exposed. NEVER prompt a tiny distant statue on a plaza base from head to toe; alternate between dramatic chest-up medium close-ups, intense medium 3/4 portraits, and grand atmospheric forum settings.'
    
    if old_rule in text:
        text = text.replace(old_rule, new_rule)
        path.write_text(text, encoding="utf-8")
        print("[OK] series_studio.py screenwriting rule updated.")
    else:
        print("[WARN] series_studio.py rule text not matched exactly.")

def update_existing_project():
    # 1. Update DNA cache
    cache_dna = ROOT / "studio" / "character_clones" / "2pDQcrGwUds_dna_verified_v2.json"
    if cache_dna.is_file():
        dna = {
            "character_name": "Marcus Aurelius (Chiseled Demigod Philosopher Emperor)",
            "apparent_age": "Late 40s Classical Imperial Hero",
            "gender": "Male",
            "appearance_lock": "Hyper-muscular chiseled athletic demigod physique, massive broad shoulders, thick muscular neck, sculpted pectoral chest muscles, striated deltoids, powerful vascular arms, chiseled masculine jawline, weathered sun-kissed bronze skin, intense piercing dark eyes, thick salt-and-pepper curly hair and groomed beard.",
            "wardrobe_lock": "Royal crimson red draped toga (chlamys) draped across ONE shoulder, leaving the sculpted muscular chest and powerful shoulder/arm bare, secured with an antique golden fibula brooch.",
            "art_style": "Cinematic live-action historical epic 16:9 film still with dramatic chiaroscuro lighting, warm amber golden key light, deep sapphire teal shadows, and grand Acropolis backdrop at twilight.",
            "immutable_rules": "Maintain hyper-muscular warrior build, one-shoulder draped crimson toga exposing muscular chest/arm, intense facial expression, and dynamic chest-up / medium framing. Never render tiny distant figures or skinny scrawny anatomy.",
            "clone_prompt": "Cinematic 16:9, hyper-muscular chiseled Roman philosopher emperor, massive broad shoulders, thick muscular neck, sculpted chest pecs, striated deltoids, vascular arms, royal crimson red toga draped over one shoulder leaving muscular chest and arm exposed, dramatic golden chiaroscuro lighting, illuminated ancient Acropolis colonnades at twilight, photorealistic 8k.",
            "story_premise": "Exploration of Stoic philosophical tenets regarding letting go of what cannot be controlled to overcome anxiety.",
            "suggested_genre": "stoic",
            "vision_verified": True,
            "in_video_verified": True
        }
        cache_dna.write_text(json.dumps(dna, ensure_ascii=False, indent=2), encoding="utf-8")
        print("[OK] 2pDQcrGwUds_dna_verified_v2.json updated.")

    # 2. Update Bible in Stoic-Philosophy-Full-Guides
    bible_file = ROOT / "studio" / "productions" / "Stoic-Philosophy-Full-Guides" / "bibles" / "stoic_color_cinematic_904183bd0b681.json"
    if bible_file.is_file():
        bible_data = json.loads(bible_file.read_text(encoding="utf-8"))
        bible_data["visual_style"] = (
            "Cinematic live-action 16:9 historical epic Greco-Roman cinematography, "
            "dramatic chiaroscuro lighting, warm amber golden key light, deep sapphire teal atmospheric shadows, "
            "monumental illuminated ancient Acropolis backdrop at twilight."
        )
        bible_data["characters"] = [
            {
                "name": "Marcus Aurelius (Chiseled Demigod Philosopher Emperor)",
                "appearance": (
                    "Hyper-muscular chiseled athletic demigod physique, massive broad shoulders, thick muscular neck, "
                    "deeply sculpted pectoral chest muscles, striated deltoids, powerful vascular arms, chiseled masculine jawline, "
                    "weathered sun-kissed bronze skin, intense piercing dark eyes, thick salt-and-pepper curly hair and beard."
                ),
                "attire": (
                    "Royal crimson red draped toga (chlamys) draped across one shoulder, leaving the sculpted muscular chest "
                    "and powerful shoulder/arm bare, secured with an antique golden fibula brooch."
                ),
                "personality": "Stoic Roman emperor and master thinker, radiating supreme inner calm, indomitable mental fortitude, and commanding imperial authority.",
                "immutable_rules": (
                    "Always render hyper-muscular chiseled demigod physique (massive shoulders, thick neck, sculpted pecs, vascular arms) "
                    "with royal crimson toga draped over one shoulder in dynamic medium or chest-up framing. Never render tiny distant figures or scrawny anatomy."
                ),
                "clone_prompt": (
                    "Cinematic 16:9, hyper-muscular chiseled Roman philosopher emperor, massive broad shoulders, thick muscular neck, "
                    "sculpted chest pecs, striated deltoids, vascular arms, royal crimson red toga draped over one shoulder leaving muscular chest "
                    "and arm exposed, dramatic golden chiaroscuro lighting, illuminated ancient Acropolis colonnades at twilight, photorealistic 8k."
                )
            }
        ]
        bible_data["continuity_rules"] = (
            "CHARACTER CONTINUITY: Primary subject is Marcus Aurelius (Chiseled Demigod Philosopher Emperor). "
            "Appearance: Hyper-muscular chiseled demigod build, massive broad shoulders, thick neck, sculpted chest pecs, striated deltoids, vascular arms. "
            "Attire: Royal crimson red draped toga over one shoulder leaving muscular chest and arm exposed. "
            "Framing: Dramatic chest-up medium close-ups (bust), medium 3/4 heroic portraits, and grand atmospheric forum settings. "
            "Never render tiny distant scrawny statues."
        )
        bible_file.write_text(json.dumps(bible_data, ensure_ascii=False, indent=2), encoding="utf-8")
        print("[OK] stoic_color_cinematic_904183bd0b681.json updated.")

    # 3. Update plan.json in Stoic-Philosophy-Full-Guides/episode_001
    plan_file = ROOT / "studio" / "productions" / "Stoic-Philosophy-Full-Guides" / "episode_001" / "plan.json"
    if plan_file.is_file():
        plan_data = json.loads(plan_file.read_text(encoding="utf-8"))
        
        # Sync bible inside plan
        if "bible" in plan_data:
            plan_data["bible"]["visual_style"] = (
                "Cinematic live-action 16:9 historical epic Greco-Roman cinematography, "
                "dramatic chiaroscuro lighting, warm amber golden key light, deep sapphire teal atmospheric shadows, "
                "monumental illuminated ancient Acropolis backdrop at twilight."
            )
            plan_data["bible"]["characters"] = [
                {
                    "name": "Marcus Aurelius (Chiseled Demigod Philosopher Emperor)",
                    "appearance": (
                        "Hyper-muscular chiseled athletic demigod physique, massive broad shoulders, thick muscular neck, "
                        "deeply sculpted pectoral chest muscles, striated deltoids, powerful vascular arms, chiseled masculine jawline, "
                        "weathered sun-kissed bronze skin, intense piercing dark eyes, thick salt-and-pepper curly hair and beard."
                    ),
                    "attire": (
                        "Royal crimson red draped toga (chlamys) draped across one shoulder, leaving the sculpted muscular chest "
                        "and powerful shoulder/arm bare, secured with an antique golden fibula brooch."
                    ),
                    "personality": "Stoic Roman emperor and master thinker, radiating supreme inner calm, indomitable mental fortitude, and commanding imperial authority.",
                    "immutable_rules": (
                        "Always render hyper-muscular chiseled demigod physique (massive shoulders, thick neck, sculpted pecs, vascular arms) "
                        "with royal crimson toga draped over one shoulder in dynamic medium or chest-up framing. Never render tiny distant figures or scrawny anatomy."
                    ),
                    "clone_prompt": (
                        "Cinematic 16:9, hyper-muscular chiseled Roman philosopher emperor, massive broad shoulders, thick muscular neck, "
                        "sculpted chest pecs, striated deltoids, vascular arms, royal crimson red toga draped over one shoulder leaving muscular chest "
                        "and arm exposed, dramatic golden chiaroscuro lighting, illuminated ancient Acropolis colonnades at twilight, photorealistic 8k."
                    )
                }
            ]
            plan_data["bible"]["continuity_rules"] = (
                "CHARACTER CONTINUITY: Primary subject is Marcus Aurelius (Chiseled Demigod Philosopher Emperor). "
                "Appearance: Hyper-muscular chiseled demigod build, massive broad shoulders, thick neck, sculpted chest pecs, striated deltoids, vascular arms. "
                "Attire: Royal crimson red draped toga over one shoulder leaving muscular chest and arm exposed. "
                "Framing: Dramatic chest-up medium close-ups (bust), medium 3/4 heroic portraits, and grand atmospheric forum settings."
            )

        # Sanitize all scenes
        statue_replacements = [
            (r'(?i)\bin the center stands a heroic full-length classical marble statue of an ancient bearded stoic philosopher from head to toe, legs grounded on ancient temple base, wearing a draped stone toga\b',
             'Cinematic chest-up shot of the hyper-muscular chiseled Stoic philosopher emperor (Marcus Aurelius archetype) with massive broad shoulders, thick neck, and sculpted chest pecs, royal crimson toga draped over one shoulder leaving muscular chest and arm exposed'),
            (r'(?i)\bfull[- ]length\s+standing\s+heroic\s+classical\s+marble\s+statue\s+of\s+a\s+bearded\s+stoic\s+philosopher\b',
             'hyper-muscular chiseled Stoic philosopher emperor with massive broad shoulders, thick neck, sculpted pecs, and royal crimson toga over one shoulder'),
            (r'(?i)\bheroic\s+full[- ]length\s+classical\s+marble\s+statue\s+of\s+an\s+ancient\s+bearded\s+stoic\s+philosopher\s+from\s+head\s+to\s+toe,\s+legs\s+grounded\s+on\s+ancient\s+temple\s+base\b',
             'hyper-muscular chiseled Stoic philosopher emperor with massive broad shoulders, sculpted chest pecs, and royal crimson toga over one shoulder'),
            (r'(?i)\bfull[- ]length\s+standing\s+marble\s+philosopher\b',
             'heroic hyper-muscular Stoic emperor in commanding chest-up framing'),
            (r'(?i)\bweathered\s+carrara\s+marble\s+textures,\s+draped\s+toga\s+flowing\s+to\s+stone\s+base\b',
             'weathered bronze skin, sculpted muscular pecs and shoulder, royal crimson red toga draped over one shoulder'),
            (r'(?i)\bstone\s+pedestals?\b', 'ancient marble colonnade'),
            (r'(?i)\bpedestals?\b', 'ancient colonnade'),
        ]

        count_mod = 0
        for sc in plan_data.get("scenes", []):
            d = sc.get("description", "")
            vs = sc.get("visual_setup", "")
            orig_d = d
            for pat, rep in statue_replacements:
                d = re.sub(pat, rep, d)
                vs = re.sub(pat, rep, vs)
            if d != orig_d:
                sc["description"] = d
                sc["visual_setup"] = vs
                count_mod += 1

        plan_file.write_text(json.dumps(plan_data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[OK] plan.json updated! Sanitized {count_mod} scenes from skinny full-length statues to muscular demigod warrior framing.")

if __name__ == "__main__":
    print("=== STARTING HYPER-MUSCULAR OVERHAUL ===")
    patch_competitor_cloner()
    patch_studio_modes()
    patch_mcp_v2_batch()
    patch_comfyui_image_provider()
    patch_muse_video_provider()
    patch_series_studio()
    update_existing_project()
    print("=== HYPER-MUSCULAR OVERHAUL COMPLETED SUCCESSFULLY ===")
