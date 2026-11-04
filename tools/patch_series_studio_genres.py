import re

def patch():
    path = "D:/STORYBOARD_AI/studio/series_studio.py"
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Find make_bible
    start_make_bible = -1
    end_make_bible = -1
    for i, l in enumerate(lines):
        if 'def make_bible(client, model, prompt, series,genre="documentary",style="color_cinematic"):' in l:
            start_make_bible = i
        if start_make_bible != -1 and 'Preserve character appearance across episodes' in l:
            end_make_bible = i + 1
            break

    if start_make_bible == -1 or end_make_bible == -1:
        print("ERROR: could not locate make_bible boundaries:", start_make_bible, end_make_bible)
        return False

    new_make_bible_lines = [
        'def make_bible(client, model, prompt, series,genre="documentary",style="color_cinematic"):\n',
        '    from studio_modes import ART\n',
        '    genre_spec = ART.get(genre, "")\n',
        '    genre_prompt_chunk = f"\\nAUTHORITATIVE GENRE SPECIFICATION (Strictly adhere to this aesthetic, world setting, and character archetype):\\n{genre_spec}\\n" if genre_spec else ""\n',
        '    request = (f"Design an ORIGINAL, production-ready, viral episodic series story bible for \'{series}\', with STYLE \'{style}\' and GENRE \'{genre}\'.\\n"\n',
        '         f"{genre_prompt_chunk}\\n"\n',
        '         "JSON only, with keys: "\n',
        '         "- world: detailed setting, geography, historical/cultural context, atmospheric palette, lighting rules matching the genre specification. "\n',
        '         "- visual_style: exact art direction, cinematic camera aesthetics, color temperature matching the genre. "\n',
        '         "- characters: array of 1-3 recurring protagonists with: name, stable_appearance (exact age, facial structure, skin tone, eye color, hairstyle matching the genre), attire (signature iconic clothing, textures, colors), signature_props (iconic accessories/items), personality, immutable_rules (rules to prevent appearance drift across scenes and episodes). "\n',
        '         "- continuity_rules: strict rules to preserve exact character visual DNA and world atmosphere across all episodes. "\n',
        '         "- narrator_style: voiceover tone, cadence, rhythm tailored to the genre. "\n',
        '         "- core_moral_theme: profound human life lesson, emotional awakening, or moral truth. "\n',
        '         "- series_hook_framework: central overarching mystery, quest, or dramatic stakes linking episodes together. "\n',
        '         f"Preserve character appearance across episodes. Series: {series}. Premise: {prompt[:5500]}")\n'
    ]

    lines = lines[:start_make_bible] + new_make_bible_lines + lines[end_make_bible:]
    print("SUCCESS: make_bible patched cleanly")

    content = "".join(lines)

    # 2. Patch genre cold open overrides in produce_plan
    target_stoic_block = '''                    if args.genre == "stoic":
                        # Stoic benchmark branch: Keep 100% UNTOUCHED for proven stability
                        request = re.sub(
                            r"1\\. SCENE 1 .*?(?=2\\. MIDDLE SCENES)",
                            "1. STOIC COLD OPEN: Begin with an urgent, relatable inner dilemma "
                            "or a counterintuitive philosophical question. Use reflective, "
                            "credible narration, never violent spectacle or invented danger.\\n",
                            request, flags=re.S)
                        request = re.sub(
                            r"3\\. FINAL SCENE .*?(?=4\\. CHARACTER & WORLD CONTINUITY)",
                            "3. STOIC FINAL SCENE: Deliver a useful insight or concrete "
                            "practice and invite the next chapter with a genuine unanswered "
                            "question rooted in the existing series premise; no fabricated mystery.\\n",
                            request, flags=re.S)
                        request += ("\\nSTOIC OVERRIDE: Prioritize philosophical clarity, source "
                                    "accuracy, calm pacing, and the saved series storyline over "
                                    "generic viral shock instructions or artificial cliffhangers.")'''

    new_genre_overrides = '''                    if args.genre == "stoic":
                        # Stoic benchmark branch: Keep 100% UNTOUCHED for proven stability
                        request = re.sub(
                            r"1\\. SCENE 1 .*?(?=2\\. MIDDLE SCENES)",
                            "1. STOIC COLD OPEN: Begin with an urgent, relatable inner dilemma "
                            "or a counterintuitive philosophical question. Use reflective, "
                            "credible narration, never violent spectacle or invented danger.\\n",
                            request, flags=re.S)
                        request = re.sub(
                            r"3\\. FINAL SCENE .*?(?=4\\. CHARACTER & WORLD CONTINUITY)",
                            "3. STOIC FINAL SCENE: Deliver a useful insight or concrete "
                            "practice and invite the next chapter with a genuine unanswered "
                            "question rooted in the existing series premise; no fabricated mystery.\\n",
                            request, flags=re.S)
                        request += ("\\nSTOIC OVERRIDE: Prioritize philosophical clarity, source "
                                    "accuracy, calm pacing, and the saved series storyline over "
                                    "generic viral shock instructions or artificial cliffhangers.")
                    elif args.genre == "family_drama":
                        # Family drama: authentic domestic conflict, never weapons or blood
                        request = re.sub(
                            r"1\\. SCENE 1 .*?(?=2\\. MIDDLE SCENES)",
                            "1. FAMILY DRAMA COLD OPEN (INTENSE DOMESTIC CROSSROADS & RAW EMOTION): "
                            "Plunge straight into a realistic, high-stakes family crossroads (e.g. an unexpected confrontation over a hidden will, "
                            "a painful secret discovered, a broken family dinner, or confronting a heartbreaking betrayal between loved ones). "
                            "STRICTLY FORBIDDEN: Armed combat, weapons, blood, gore, crime syndicates, or action stunts. "
                            "Spoken line ('narration') MUST be 100% realistic spoken dialogue between family members with authentic emotional depth.\\n",
                            request, flags=re.S)
                        request = re.sub(
                            r"3\\. FINAL SCENE .*?(?=4\\. CHARACTER & WORLD CONTINUITY)",
                            "3. FAMILY DRAMA FINAL SCENE (EMOTIONAL ZEIGARNIK CLIFFHANGER): "
                            "Deliver an emotional turning point or shocking domestic revelation (e.g. an unopened letter from the past, "
                            "a sudden knock on the door with unexpected news, an ultimatum given). "
                            "Leave viewers deeply invested in the family's fate for the next episode.\\n",
                            request, flags=re.S)
                        request += ("\\nFAMILY DRAMA OVERRIDE: Authentic Vietnamese/cultural family dynamics. "
                                    "Real human relationships, generational conflict, tears, emotional warmth and drama. Zero armed violence.")
                    elif args.genre == "romance_melodrama":
                        # Romance: emotional heartache and longing, zero armed violence
                        request = re.sub(
                            r"1\\. SCENE 1 .*?(?=2\\. MIDDLE SCENES)",
                            "1. ROMANCE COLD OPEN (HEARTBREAKING CROSSROADS & EMOTIONAL RUPTURE): "
                            "Open with an intensely romantic or devastating in medias res moment (e.g. an unexpected reunion after years apart, "
                            "a tearful confrontation in the rain, a painful broken promise, or discovering a hidden sacrifice). "
                            "STRICTLY FORBIDDEN: Armed violence, weapons, gore, crime, or action violence. "
                            "Spoken line ('narration') MUST be deeply emotional character dialogue filled with longing, hurt, or passionate love.\\n",
                            request, flags=re.S)
                        request = re.sub(
                            r"3\\. FINAL SCENE .*?(?=4\\. CHARACTER & WORLD CONTINUITY)",
                            "3. ROMANCE FINAL SCENE (ROMANTIC CLIFFHANGER): "
                            "End on a poignant unresolved choice or breathtaking romantic revelation (e.g. a confession interrupted at the last second, "
                            "a departure train pulling away, an unexpected sacrifice revealed). Leave viewers desperate for reconciliation.\\n",
                            request, flags=re.S)
                        request += ("\\nROMANCE OVERRIDE: Modern aesthetic romance. Golden hour warmth, expressive character glances, "
                                    "intimate emotional tension, beautiful cinematography. Zero physical combat.")
                    elif args.genre in ("whiteboard", "colored_marker"):
                        # Whiteboard: After Skool intellectual hook and visual metaphors
                        request = re.sub(
                            r"1\\. SCENE 1 .*?(?=2\\. MIDDLE SCENES)",
                            "1. WHITEBOARD INTELLECTUAL HOOK (AFTER SKOOL PARADOX & CURIOSITY GAP): "
                            "Open with a startling psychological paradox, counterintuitive life rule, or shocking human behavior truth. "
                            "Single engaging, witty Voiceover Narrator (NO character acting, NO life-or-death screams). "
                            "Visuals describe ingenious hand-drawn marker illustrations with visual metaphors sketching onto a clean white whiteboard.\\n",
                            request, flags=re.S)
                        request = re.sub(
                            r"3\\. FINAL SCENE .*?(?=4\\. CHARACTER & WORLD CONTINUITY)",
                            "3. WHITEBOARD FINAL SCENE (MIND-EXPANDING PAYOFF): "
                            "Deliver a profound mental model shift or actionable life lesson, completing the whiteboard conceptual drawing. "
                            "End with an intriguing open question that changes how the viewer sees reality.\\n",
                            request, flags=re.S)
                        request += ("\\nWHITEBOARD OVERRIDE: After Skool style whiteboard marker art. Images MUST be colorful marker drawings on pure white background. "
                                    "No live-action actors, no real human skin, no photorealism, no violence.")
                    elif args.genre == "animation":
                        # Animation: Charming adventure or heartfelt cartoon
                        request = re.sub(
                            r"1\\. SCENE 1 .*?(?=2\\. MIDDLE SCENES)",
                            "1. ANIMATION COLD OPEN (VIBRANT INCITING INCIDENT & CHARMING HOOK): "
                            "Plunge into a vibrant, whimsical, or thrilling animated inciting incident. "
                            "Expressive 3D stylized cartoon characters, family-friendly humor or charming adventure stakes. "
                            "STRICTLY FORBIDDEN: Gory blood, severed limbs, dark adult violence, or realistic photographic skin.\\n",
                            request, flags=re.S)
                        request = re.sub(
                            r"3\\. FINAL SCENE .*?(?=4\\. CHARACTER & WORLD CONTINUITY)",
                            "3. ANIMATION FINAL SCENE (AWE-INSPIRING ADVENTURE CLIFFHANGER): "
                            "Deliver a heartwarming resolution to this chapter while unveiling an exciting new magical horizon or mysterious creature for the next episode.\\n",
                            request, flags=re.S)
                        request += ("\\nANIMATION OVERRIDE: 3D Pixar/Disney style animated aesthetic. Vibrant colors, expressive cartoon acting, "
                                    "family-friendly themes. Zero dark gore or adult horror.")
                    elif args.genre == "psychological_horror":
                        # Psychological horror: creeping dread and paranoia, avoid generic gunfights
                        request = re.sub(
                            r"1\\. SCENE 1 .*?(?=2\\. MIDDLE SCENES)",
                            "1. PSYCHOLOGICAL HORROR COLD OPEN (ATMOSPHERIC DREAD & UNSETTLING ANOMALY): "
                            "Open with an eerie, skin-crawling anomaly (e.g. an unsettling shadow that moves on its own, a phone ringing from an empty house, "
                            "a whisper in the dark, or a creeping sense of paranoia). Focus on atmospheric dread and chilling suspense, not generic gunfights.\\n",
                            request, flags=re.S)
                        request = re.sub(
                            r"3\\. FINAL SCENE .*?(?=4\\. CHARACTER & WORLD CONTINUITY)",
                            "3. HORROR FINAL SCENE (CHILLING ZEIGARNIK OPEN LOOP): "
                            "End on a hair-raising revelation or unsettling twist that leaves the viewer questioning what was real, desperate to see what lurks next.\\n",
                            request, flags=re.S)'''

    if target_stoic_block not in content:
        print("ERROR: target_stoic_block not found in content")
        return False
    content = content.replace(target_stoic_block, new_genre_overrides)
    print("SUCCESS: genre cold open overrides patched")

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("All patches applied to series_studio.py successfully!")
    return True

if __name__ == "__main__":
    patch()
