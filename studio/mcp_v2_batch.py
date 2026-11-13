"""One-batch Storyboard Studio MCP image pipeline.







Studio's private Flow MCP image backend is used. It manages one queue,



has durable verified receipts and never re-submits an uncertain job.



"""



from __future__ import annotations



import os,sys,uuid,re,shutil,json,hashlib



from pathlib import Path



from PIL import Image,ImageOps



from studio_image_budget import inspect_budget, select_keyframes, ImageBudgetError



from mcp_v2_images import preflight,PRODUCTION_ROOT,clean_id,StudioMcpImageError







def sanitize_statue_terms(text: str, genre: str = "stoic") -> str:

    if not text:

        return ""

    import re

    t = text

    # Clean video post-production editing artifacts (applicable to all genres)

    t = re.sub(r'(?i)\b(peripheral|subtle|vertical|edge)?\s*(mirroring|mirrored|mirror seam|mirror effect|mirrored border effects?|kaleidoscope(\s+edge\s+blur)?|diptych|split[- ]screen|two statues|two men|twin statues|dual|double)\b', '', t)

    t = re.sub(r'(?i)\b(cinematic\s+)?(16:9|9:16)\s*(shot|composition|framing)?\b', '', t)



    # ONLY apply marble statue cleanup if the genre is strictly Stoic / Philosophy!

    # For all other genres (family drama, romance, action, documentary, etc.), preserve human actors and settings!

    if str(genre or "").strip().lower() in ("stoic", "philosophy"):

        t = re.sub(r'(?i)\b(half[- ]?body\s+)?(marble\s+)?busts?\b', 'heroic monumental classical Carrara marble statue with unbroken complete arms', t)

        t = re.sub(r'(?i)\btượng\s+bán\s+thân\b', 'tượng cẩm thạch cơ bắp vạm vỡ đầy đủ hai cánh tay nguyên vẹn', t)

        t = re.sub(r'(?i)\btượng\s+nửa\s+người\b', 'tượng cẩm thạch đứng uy nghi đầy đủ hai cánh tay nguyên vẹn', t)

        t = re.sub(r'(?i)\b(on|upon)\s+(a\s+)?([a-z\s]+)?pedestal\b', 'among ancient Roman marble colonnades', t)

        t = re.sub(r'(?i)\b([a-z\s]+)?pedestals?\b', 'ancient Roman colonnade', t)

        t = re.sub(r'(?i)\b(half[- ]?body|torso[- ]only|waist[- ]up)(\s+statue|\s+sculpture)?\b', 'heroic medium torso statue with complete intact arms', t)

        t = re.sub(r'(?i)\b(broken|ruined|headless|armless|damaged|fragmented|amputated)\s+(statue|sculpture|marble|torso|limbs?)\b', 'magnificent unbroken intact classical Carrara marble statue', t)

        t = re.sub(r'(?i)\b(severed|broken|missing)\s+(arms?|hands?|limbs?)\b', 'fully sculpted unbroken muscular arms and natural hands', t)

        t = re.sub(r'(?i)\b(living\s+human\s+flesh|real\s+human\s+skin|skin\s+pores|vascular\s+veins|cosplay)\b', 'classical carved Carrara marble stone', t)



    t = re.sub(r'\s{2,}', ' ', t).strip()

    return t



STOIC_CINEMATIC_BEATS = [

    # Beat 1: Imperial Palace Terrace / Golden Sunrise Chiaroscuro

    {

        "action": "A monumental heroic classical carved Carrara marble statue of Stoic philosopher emperor Marcus Aurelius, medium shot torso framing occupying frame. Imposing athletic demigod anatomy, massive broad shoulders, chiseled chest pecs, fully sculpted unbroken muscular stone arms seamlessly attached extending naturally, thick curly beard and calm contemplative stone eyes, signature royal crimson draped linen toga over one shoulder.",

        "setup": "Medium shot torso framing, imposing heroic stance, warm golden sunrise key light highlighting muscular stone chest and shoulders against grand ancient Roman palace colonnades at dawn with floating golden embers.",

        "keywords": ["imperial terrace", "sunrise chiaroscuro", "unbroken marble statue"]

    },

    # Beat 2: Imperial Study / Warm Torchlight & Candlelight Chiaroscuro

    {

        "action": "Inside a majestic ancient Roman imperial hall, the monumental carved Carrara marble statue of Marcus Aurelius in medium heroic framing, powerful chiseled pectoral chest and sculpted deltoids illuminated by flickering warm candlelight and bronze torchlight casting dramatic chiaroscuro shadows across the weathered stone fissures.",

        "setup": "Medium shot torso framing, three-quarter heroic profile, warm amber flame highlights, dark atmospheric imperial study backdrop with shelves of antique parchment scrolls.",

        "keywords": ["imperial study", "candlelight chiaroscuro", "chiseled marble torso"]

    },

    # Beat 3: Monumental Roman Arches & Colonnades / Golden Hour

    {

        "action": "Standing before the towering monumental stone arches and colonnades of ancient Rome at golden hour, the colossal Carrara marble statue of Marcus Aurelius in imposing heroic torso framing, cinematic sunlight casting deep heroic shadows across the sculpted stone chest and draped crimson toga.",

        "setup": "Heroic medium torso framing, dramatic golden backlight, ancient Roman monumental arches and stone pillars in background, unbroken complete stone arms, no people in frame.",

        "keywords": ["Roman arches", "golden hour heroic", "monumental marble statue"]

    },

    # Beat 4: Olive Grove Courtyard / Dappled Sunlight

    {

        "action": "The imposing classical Carrara marble statue of Marcus Aurelius standing resolute in a sun-dappled stone courtyard among ancient Roman olive trees, natural golden sunlight filtering through leaves highlighting the chiseled stone pecs, broad shoulders, and draped crimson toga.",

        "setup": "Medium heroic torso framing, natural daylight with soft shadows, ancient olive grove and stone arches in background, unbroken complete stone arms.",

        "keywords": ["olive grove courtyard", "dappled sunlight", "heroic marble statue"]

    },

    # Beat 5: Pantheon Interior / Divine Oculus Sunbeam

    {

        "action": "Inside the vast monumental interior of the Roman Pantheon, the towering classical Carrara marble statue of Marcus Aurelius in medium heroic framing, a dramatic divine shaft of golden sunlight descending through the central ceiling oculus onto the sculpted muscular shoulders and crimson toga.",

        "setup": "Medium shot torso framing, dramatic volumetric god-rays from ceiling oculus, monumental fluted marble columns and polished stone floor in background.",

        "keywords": ["Pantheon interior", "oculus god-rays", "divine marble statue"]

    },

    # Beat 6: Peristyle Garden / Reflecting Fountain Pool

    {

        "action": "The magnificent Carrara marble statue of Marcus Aurelius beside a clear reflecting stone fountain pool in an imperial palace peristyle garden, water reflections gently shimmering across the powerfully carved pectoral muscles, thick stone neck, and dignified bearded face.",

        "setup": "Medium profile heroic framing, soft diffused lighting with water reflection highlights, serene Roman peristyle garden in background.",

        "keywords": ["reflecting pool", "peristyle garden", "sculpted marble torso"]

    },

    # Beat 7: Macro Insert - Bronze Oil Lamp & Latin Papyrus Scrolls

    {

        "action": "A cinematic close-up of an antique Roman bronze oil lamp with a soft steady flame, resting on a carved marble ledge next to unrolled papyrus scrolls inscribed with classical Latin philosophical text.",

        "setup": "Macro detail shot, warm flame glow, rich stone and parchment textures, atmospheric low-key lighting, symbolic philosophical insert.",

        "keywords": ["bronze oil lamp", "papyrus scrolls", "Latin inscription"]

    },

    # Beat 8: Danube Frontier Campfire / Winter Twilight

    {

        "action": "On the snowy northern Danube frontier at dusk, the monumental Carrara marble statue of Marcus Aurelius wrapped in heavy imperial crimson drapery, warm glowing brazier embers drifting upward into the blue twilight, illuminating the hyper-muscular chiseled stone chest and broad shoulders.",

        "setup": "Medium shot torso framing, striking contrast between cool blue twilight snow and warm orange fire embers, unbroken complete muscular arms.",

        "keywords": ["Danube frontier", "military camp brazier", "winter twilight statue"]

    },

    # Beat 9: Over-The-Shoulder / Roman Forum at Dusk

    {

        "action": "A cinematic heroic shot framing the imposing classical Carrara marble statue of Marcus Aurelius as he stands resolute amidst towering marble arches overlooking the majestic Roman Forum bathed in deep twilight shadows and torchlight.",

        "setup": "Heroic medium composition, dramatic low-angle chiaroscuro, majestic Roman colonnades framing the distant Colosseum and Forum.",

        "keywords": ["over-the-shoulder", "marble arches", "Roman Forum twilight"]

    },

    # Beat 10: Monumental Sunset Panorama / Golden Rome Skyline

    {

        "action": "The towering classical Carrara marble statue of Marcus Aurelius in medium heroic torso framing, silhouetted against an epic wide fiery amber and purple sunset sky over the ancient city of Rome, the Colosseum, and distant stone aqueducts.",

        "setup": "Medium heroic torso framing, rich sunset rim lighting illuminating the muscular stone deltoids and curly beard, epic ancient Rome landscape in backdrop.",

        "keywords": ["sunset panorama", "heroic marble silhouette", "ancient Rome skyline"]

    },

    # Beat 11: Extreme Close-Up / Contemplative Eyes & Chiseled Marble Beard

    {

        "action": "A dramatic intimate cinematic close-up of the weathered Carrara marble face of Stoic emperor Marcus Aurelius, capturing deep contemplative stone eyes, finely sculpted curly beard, and subtle historical chisel marks.",

        "setup": "Tight facial close-up, dramatic side chiaroscuro key light cutting across stone cheekbones, shallow depth of field, 85mm portrait cinema lens.",

        "keywords": ["intimate close-up", "stoic contemplative eyes", "chiseled facial features"]

    },

    # Beat 12: Heroic Low-Angle Worm's Eye View / Stormy Sky

    {

        "action": "Standing before monumental Roman arches under a stormy sky, the colossal Carrara marble statue of Marcus Aurelius looms heroically with draped crimson toga billowing.",

        "setup": "Dramatic low-angle worm's-eye view looking up, dynamic heroic perspective, moody stormy sky with distant lightning flashes, high contrast chiaroscuro.",

        "keywords": ["low-angle hero shot", "worm's-eye view", "stormy sky chiaroscuro"]

    }

]



def image_prompt(scene,bible):

    scene_num = int(scene.get("scene_number") or scene.get("number") or 1)

    characters=[]

    genre_hint = str(bible.get("production_genre") or bible.get("genre") or "").strip().lower()

    has_clone = bool(bible.get("characters") and isinstance(bible["characters"][0], dict) and (

        bible["characters"][0].get("clone_prompt")

        or (str(bible["characters"][0].get("personality", "")).startswith("Cloned protagonist:")

            and bible["characters"][0].get("appearance"))

        or (genre_hint in ("", "auto", "stoic", "philosophy") and bible["characters"][0].get("appearance"))

    ))



    is_vert = bool(bible.get("is_vertical") or bible.get("aspect_ratio") == "9:16" or str(scene.get("aspect_ratio","")).strip() == "9:16")

    aspect_desc = "vertical 9:16 mobile portrait." if is_vert else "wide 16:9 landscape."

    ratio_tag = "9:16" if is_vert else "16:9"



    # Explicit prompt override if supplied

    explicit_prompt = str(scene.get("image_prompt", "")).strip()

    if explicit_prompt and len(explicit_prompt) >= 15:

        p = explicit_prompt

        if "16:9" not in p and "9:16" not in p:

            p = f"Cinematic {ratio_tag}, {p}"

        if "no text" not in p.lower() and "no watermark" not in p.lower():

            if genre_hint == "animation":

                p = p.rstrip(". ") + ". No text overlays, no watermarks, stylized animation."

            elif genre_hint in ("whiteboard", "colored_marker"):

                p = p.rstrip(". ") + ". No text overlays, no watermarks, hand-drawn marker illustration."

            else:

                p = p.rstrip(". ") + ". No text overlays, no watermarks, photorealistic 8k."

        return p[:1000]



    # Determine genre early

    genre = str(bible.get("production_genre") or bible.get("genre") or "").strip().lower()

    series_name = str(bible.get("series") or scene.get("series") or "").strip().lower()

    scene_desc_low = (str(scene.get("description", "")) + " " + str(scene.get("visual_setup", ""))).lower()

    is_stoic = (genre in ("stoic", "philosophy") or (genre in ("", "auto") and "stoi" in series_name))



    # ACCURATE VIDEO CLONING MODE: 100% faithful replication of competitor reference video

    if has_clone:

        c = bible["characters"][0]

        clone_base = c.get("clone_prompt") or c.get("appearance", "")

        clean_clone = re.sub(r'(?i)\b(cinematic\s+)?(16:9|9:16)\s*(shot|composition|framing)?,?\s*', '', clone_base).strip(', ')

        rules = str(c.get("immutable_rules", "")).strip()

        scene_desc = str(scene.get("description", "")).strip()

        setup = str(scene.get("visual_setup", "")).strip()

        

        # Sanitize against any mirrored/split/kaleidoscope/dual/pedestal defects

        bad_words_pattern = r'(?i)\b(mirrored|symmetrical|mirror|kaleidoscope|dual|twin|two statues|two men|double|split|collage|diptych|pedestal|severed bust)\b'

        scene_desc = re.sub(bad_words_pattern, '', scene_desc).strip(', ')

        setup = re.sub(bad_words_pattern, '', setup).strip(', ')



        # STOIC SPECIFIC ENFORCEMENT: 100% Faithful Competitor Clone: Heroic Monumental Carrara Marble Statue

        if is_stoic:

            clean_clone = (

                f"Cinematic {ratio_tag} composition. "

                "Monumental heroic classical carved Carrara marble statue of Stoic philosopher emperor Marcus Aurelius, unbroken complete sculpture. "

                "Deeply sculpted hyper-muscular anatomy, colossal broad stone shoulders, powerfully chiseled pectoral chest muscles, thick sculpted stone neck, "

                "fully sculpted unbroken muscular stone arms seamlessly attached extending naturally down to complete intact stone hands with carved fingers resting naturally within frame, "

                "arms and hands 100% complete and fully visible inside the frame borders, never cut off, "

                "signature royal crimson draped linen toga cascading over one shoulder leaving muscular stone chest exposed. "

                "Authentic weathered Carrara marble texture with smooth chisel marks and subtle fissure lines, 100% pure classical stone sculpture. "

                "Dramatic golden chiaroscuro key lighting, atmospheric ancient Roman colonnade ruins at twilight with floating golden torch embers. "

                "Masterpiece, photorealistic 8k, sharp focus. "

                "Absolutely no living human flesh, no real skin pores, no severed arms, no amputated limbs, no missing hands, no missing fingers, no hands cropped out, no arm stumps, no broken statues, no tabletop pedestals, no floating busts, no cartoon"

            )

            # Sanitize any bust or pedestal terms from scene_desc and setup

            for pat, rep in [

                (r'(?i)\b(half[- ]?body\s+)?(marble\s+)?busts?\b', 'heroic monumental classical Carrara marble statue with unbroken complete arms and sculpted hands'),

                (r'(?i)\btượng\s+bán\s+thân\b', 'tượng cẩm thạch cơ bắp vạm vỡ đầy đủ hai cánh tay và bàn tay nguyên vẹn'),

                (r'(?i)\b(medium\s+shot\s+torso\s+framing|medium\s+torso\s+shot)\b', 'upper body shot with complete arms and hands fully in frame'),

                (r'(?i)\bpedestals?\b', 'ancient Roman colonnade'),

                (r'(?i)\b(broken|ruined|headless|armless|damaged|fragmented|amputated)\s+(statue|sculpture|marble|torso|limbs?)\b', 'magnificent unbroken intact classical Carrara marble statue'),

                (r'(?i)\b(severed|broken|missing)\s+(arms?|hands?|limbs?)\b', 'fully sculpted unbroken muscular arms and natural hands'),

                (r'(?i)\b(living|human\s+flesh|real\s+skin|skin\s+pores|vascular\s+veins|cosplay)\b', 'classical carved Carrara marble stone'),

            ]:

                scene_desc = re.sub(pat, rep, scene_desc)

                setup = re.sub(pat, rep, setup)



            # ANTI-STAGNATION CINEMATIC DIVERSITY: If scene description is generic/static, rotate 10-beat staging!

            beat = STOIC_CINEMATIC_BEATS[(scene_num - 1) % len(STOIC_CINEMATIC_BEATS)]

            is_static_generic = len(scene_desc.strip()) < 15 or scene_desc.strip().lower() in ("stands in", "standing", "statue", "pedestal")

            if is_static_generic:

                scene_desc = beat["action"]

                setup = beat["setup"]
        if is_stoic:
            is_macro_insert = any(kw in scene_desc.lower() or kw in setup.lower() for kw in ("macro", "hourglass", "oil lamp", "pantheon interior", "sunset panorama", "no people in frame", "papyrus", "scroll", "brazier", "relic"))
            if is_macro_insert:
                prompt_parts = [
                    f"Cinematic {ratio_tag} photograph, {aspect_desc}",
                    f"Framing: {setup}",
                    f"Scene: {scene_desc}",
                    "Symbolic cinematic classical establishing insert, antique Roman relics, candlelight bokeh, 35mm cinema lens"
                ]
            else:
                f_part = f"Framing: {setup}" if setup and setup.lower() not in scene_desc.lower() else ""
                prompt_parts = [
                    f"Cinematic {ratio_tag} photograph, {aspect_desc}",
                    f_part,
                    f"Scene: {scene_desc}"
                ]
            if rules and rules.lower() not in clean_clone.lower():
                prompt_parts.append(f"Visual rules: {rules}")
        else:
            # NON-STOIC GENRES (Documentary, Family Drama, Western, Animation, Whiteboard, etc.)
            # Critical Rule: Scene description MUST lead the prompt. Never let a static character or thumbnail block overwrite scene-by-scene variety.
            is_collage_artifact = any(kw in clean_clone.lower() for kw in (
                "composite", "top-left", "bottom-left", "top-right", "bottom-right",
                "split-screen", "four-panel", "quadrant", "distinct visual styles", "white serif text", "in the top", "in the bottom"
            ))

            char_name = str(c.get("name", "")).strip()
            char_app = str(c.get("appearance", "")).strip()
            char_attire = str(c.get("attire", "")).strip()
            char_mentioned = bool(char_name and (char_name.lower() in scene_desc.lower() or char_name.lower() in setup.lower()))

            raw_style = str(bible.get("visual_style") or c.get("art_style") or "Photorealistic cinematic film").strip()
            if any(kw in raw_style.lower() for kw in ("collage", "combining various", "composite")):
                raw_style = "Photorealistic 8k cinematic film still"
            style_snippet = re.sub(r'(?i)(collage|composite|multi[- ]panel|split screen|diptych)', 'cinematic', raw_style)[:180].strip()

            genre_medium = (
                f"Vibrant After Skool whiteboard marker illustration, {aspect_desc}" if genre in ("whiteboard", "colored_marker")
                else (f"Cinematic {ratio_tag} 3D animated film still, {aspect_desc}" if genre == "animation"
                else f"Cinematic {ratio_tag} film still, {aspect_desc}")
            )

            prompt_parts = [
                genre_medium,
                f"Scene: {scene_desc}"
            ]
            if setup and setup.lower() not in scene_desc.lower():
                prompt_parts.append(f"Framing: {setup}")

            # HOLLYWOOD CINEMATIC DISCRIMINATION:
            # ONLY attach protagonist visual DNA if the scene is EXPLICITLY about the protagonist.
            # NEVER attach protagonist visual DNA to objects, landscapes, B-roll, or OTHER characters (women, children, postman, elders)!
            is_object_or_env = any(kw in scene_desc.lower() for kw in (
                "boots", "shoes", "envelope", "letter", "hand", "hands", "counter", "desk", 
                "paper", "pen", "road", "landscape", "cabin", "doorway", "fireplace", 
                "window", "scale", "post office", "mailbag", "snow", "outdoor", "interior", "wagon"
            )) and not any(kw in scene_desc.lower() for kw in ("man's face", "his face", "protagonist's face", "he looks"))

            is_other_char = any(kw in scene_desc.lower() for kw in (
                "woman", "widow", "female", "girl", "elderly woman", "postman", "mailman", "child", "children", "boy", "wife"
            )) and not (char_name and char_name.lower() in scene_desc.lower())

            should_anchor_protagonist = (char_mentioned or ("protagonist" in scene_desc.lower())) and not is_other_char and not is_object_or_env

            if char_app and should_anchor_protagonist:
                c_details = []
                if char_app:
                    c_details.append(char_app[:180])
                if char_attire:
                    c_details.append(char_attire[:120])
                if c_details:
                    label = f"Protagonist ({char_name})" if char_name else "Protagonist"
                    prompt_parts.append(f"{label} visual DNA: {', '.join(c_details)}")
            elif not is_collage_artifact and len(clean_clone) < 220 and clean_clone.lower() not in scene_desc.lower() and should_anchor_protagonist:
                prompt_parts.append(f"Subject reference: {clean_clone[:200]}")

            prompt_parts.append(f"Art style: {style_snippet}")

        prompt_parts.append("Masterpiece, cinematic lighting, photorealistic 8k, ultra-detailed. Single continuous image filling entire canvas from top to bottom and edge to edge, single shot only, absolutely no split screen, no collage, no diptych, no dual panels, no white lines, no borders, no filmstrip, no perforated margins, no text overlays, no watermarks, no distorted faces, no pedestals.")

        full_prompt = ". ".join(p.rstrip(". ") for p in prompt_parts if p)

        return re.sub(r'\s{2,}', ' ', full_prompt).strip()[:1000]



    for row in bible.get("characters",[]):

        if isinstance(row,dict):

            parts = [str(row.get(k,"")).strip() for k in ("name","appearance","attire","personality") if row.get(k)]

            if row.get("clone_prompt"):

                parts.append(f"CLONE PROMPT: {row['clone_prompt']}")

            if row.get("immutable_rules"):

                parts.append(f"RULES: {row['immutable_rules']}")

            characters.append(" | ".join(parts))



    from studio_modes import image_instruction

    genre = str(bible.get("production_genre") or bible.get("genre") or "").strip().lower()

    style = bible.get("visual_style_mode","whiteboard")

    series_name = str(bible.get("series") or scene.get("series") or "").strip().lower()



    scene_desc_low = (str(scene.get("description", "")) + " " + str(scene.get("visual_setup", ""))).lower()



    is_stoic = (genre in ("stoic", "philosophy") or (genre in ("", "auto") and "stoi" in series_name))



    def _stoic_enhance(txt: str) -> str:

        if not txt:

            return txt

        txt = re.sub(r'(?i)\b(half[- ]?body\s+)?(marble\s+)?busts?\b', 'heroic monumental classical Carrara marble statue with unbroken complete arms', txt)

        txt = re.sub(r'(?i)\btượng\s+bán\s+thân\b', 'tượng cẩm thạch cơ bắp vạm vỡ đầy đủ hai cánh tay nguyên vẹn', txt)

        txt = re.sub(r'(?i)\bpedestals?\b', 'ancient Roman colonnade', txt)

        txt = re.sub(r'(?i)\b(broken|ruined|headless|armless|damaged|fragmented|amputated)\s+(statue|sculpture|marble|torso|limbs?)\b', 'magnificent unbroken intact classical Carrara marble statue', txt)

        txt = re.sub(r'(?i)\b(severed|broken|missing)\s+(arms?|hands?|limbs?)\b', 'fully sculpted unbroken muscular arms and natural hands', txt)

        txt = re.sub(r'(?i)\b(living|human\s+flesh|real\s+skin|skin\s+pores|vascular\s+veins|cosplay)\b', 'classical carved Carrara marble stone', txt)

        statue_traits = (

            "Monumental heroic classical carved Carrara marble statue of Stoic philosopher emperor Marcus Aurelius, medium shot torso framing. "

            "Deeply sculpted hyper-muscular anatomy, colossal broad stone shoulders, powerfully chiseled pectoral chest muscles, thick sculpted stone neck, "

            "fully sculpted unbroken muscular stone arms seamlessly attached extending naturally, majestic curly stone beard and contemplative stone eyes, "

            "signature royal crimson draped linen toga cascading over one shoulder. "

            "Authentic weathered Carrara marble texture with smooth chisel marks, 100% pure classical stone sculpture, "

            "absolutely no living human flesh, no real skin pores, no severed arms, no amputated limbs, no tabletop pedestal, no floating bust, no wide shot"

        )

        if "carrara marble" not in txt.lower():

            txt = f"{statue_traits}, {txt}"

        return txt

    if is_stoic:

        raw_desc = _stoic_enhance(str(scene.get("description", "")))

        raw_setup = _stoic_enhance(str(scene.get("visual_setup", "")))

        cleaned_chars = [_stoic_enhance(c) for c in characters]

    else:

        raw_desc = str(scene.get("description", ""))

        raw_setup = str(scene.get("visual_setup", ""))

        cleaned_chars = characters



    is_vert = bool(bible.get("is_vertical") or bible.get("aspect_ratio") == "9:16")

    aspect_desc = "vertical 9:16 mobile portrait." if is_vert else "wide 16:9 landscape."

    ratio_tag = "9:16" if is_vert else "16:9"



    # Explicit prompt override if supplied

    explicit_prompt = str(scene.get("image_prompt", "")).strip()

    if explicit_prompt and len(explicit_prompt) >= 15:

        p = explicit_prompt

        if is_stoic:

            p = _stoic_enhance(p)

        if "16:9" not in p and "9:16" not in p:

            p = f"Cinematic {ratio_tag}, {p}"

        if "no text" not in p.lower() and "no watermark" not in p.lower():

            p = p.rstrip(". ") + ". No text overlays, no watermarks, photorealistic 8k."

        return p[:1000]



    char_essence = ""

    if cleaned_chars:

        first_c = cleaned_chars[0].split("|")[0].strip()

        if first_c and first_c.lower() not in raw_desc.lower():

            char_essence = f" Featuring {first_c[:120]}."



    scene_core = raw_desc.strip()[:450]

    comp_core = (" " + raw_setup.strip()[:200]) if raw_setup and raw_setup.lower() not in scene_core.lower() else ""



    if is_stoic:

        anti_cutoff = (

            "Medium shot torso framing occupying frame, full sculpted head, thick muscular neck, colossal broad stone shoulders, "

            "powerfully chiseled pectoral chest muscles, both stone arms fully intact, sculpted and unbroken, completely attached, "

            "unbroken classical Carrara marble sculpture, anatomically complete. "

            "Never living human flesh, no real skin pores, no severed arms, no amputated limbs, no stump arms, no tabletop pedestal, no floating bust, no wide shot, no tiny distant figures."

        )

        beat = STOIC_CINEMATIC_BEATS[(scene_num - 1) % len(STOIC_CINEMATIC_BEATS)]

        is_static_generic = any(kw in scene_core.lower() for kw in ("stands in", "standing", "statue", "pedestal", "solitary figure")) or len(scene_core) < 20

        if is_static_generic:

            scene_core = beat["action"]

            comp_core = " " + beat["setup"]



        short_prompt = (

            f"Cinematic {ratio_tag} photograph, {aspect_desc} "

            f"{scene_core}.{comp_core} {anti_cutoff} "

            "Art style: authentic neoclassical Carrara marble sculpture photography, dramatic golden chiaroscuro lighting, ancient Roman colonnade ruins with torch embers. "

            "High quality, rich atmosphere, photorealistic 8k, sharp focus. "

            "Single continuous image filling entire canvas from edge to edge, single shot only, absolutely no split screen, no collage, no diptych, no dual panels, no borders, no text overlays, no watermarks, no distorted faces, no living human flesh, no real skin, no broken arms, no severed arms, no amputee."

        )

    elif genre in ("whiteboard", "colored_marker") or style in ("whiteboard", "colored_marker"):

        short_prompt = (

            f"Vibrant colored whiteboard marker illustration in the signature style of After Skool, {aspect_desc} "

            f"{scene_core}{comp_core}. "

            "Clean pure white whiteboard backdrop, hand-drawn with expressive multicolored chisel-tip marker pens "

            "(deep crimson red, royal blue, warm amber yellow, emerald green, and bold ink black contours). "

            "Energetic sketchy marker cross-hatching, conceptual philosophical visual metaphors, expressive caricature character designs, "

            "crisp marker lines with authentic dry-erase texture. "

            "Zero photorealism, no 3D render, no photographic human skin, no gray background, no dark shadows, no messy borders, no text overlays, no watermarks."

        )

    elif genre == "animation" or style == "color_animation":

        short_prompt = (

            f"Cinematic {ratio_tag} 3D animated film still, {aspect_desc} "

            f"{scene_core}{comp_core}.{char_essence} "

            "Art style: high-end vibrant 3D stylized animated movie aesthetic (Pixar and Disney animation quality). "

            "Expressive stylized cartoon characters, vivid lively colors, soft cinematic volumetric lighting, beautiful 3D digital render. "

            "Zero photorealism, no real human photos, no grain, no split screen, no borders, no text overlays, no watermarks."

        )

    elif genre in ("drama", "family_drama", "romance_melodrama", "mafia_thriller", "action", "western", "history", "documentary", "psychological_horror"):

        style_snippet = str(bible.get("visual_style", "Photorealistic cinematic drama")).strip()[:180]

        short_prompt = (

            f"Cinematic {ratio_tag} film still, {aspect_desc} "

            f"{scene_core}{comp_core}.{char_essence} "

            f"Art style: {style_snippet}. "

            "Photorealistic 8k, authentic human skin tones and lifelike expressions, rich natural textures, cinematic lighting with soft bokeh background. "

            "Single continuous frame filling entire canvas from edge to edge, single shot only, absolutely no split screen, no collage, no diptych, no dual panels, no borders, no filmstrip, no perforated margins, no text overlays, no watermarks, no distorted faces."

        )

    else:

        style_snippet = str(bible.get("visual_style", "Cinematic")).strip()[:180]

        short_prompt = (

            f"Cinematic {ratio_tag} photograph, {aspect_desc} "

            f"{scene_core}{comp_core}.{char_essence} "

            f"Art style: {style_snippet}. "

            "High quality, rich atmosphere, natural lighting, photorealistic 8k. "

            "Single continuous image filling entire canvas from edge to edge, single shot only, absolutely no split screen, no collage, no diptych, no dual panels, no borders, no filmstrip, no perforated margins, no text overlays, no watermarks, no distorted faces, no broken arms, no severed arms, no amputee, no missing limbs, no broken ruins."

        )

    return re.sub(r'\s{2,}', ' ', short_prompt).strip()[:1000]







def import_receipt_image(receipt,target,idx=None,total=None):



    original=Path(str(receipt["path"]))



    if not original.is_file():



        raise StudioMcpImageError("Missing verified image in MCP receipt")



    with Image.open(original) as im:



        im.load()



        if im.width<256 or im.height<256:



            raise StudioMcpImageError("MCP image too small")



        rgb=im.convert("RGB")



        is_vert = im.height > im.width



        target_size = (864, 1536) if is_vert else (1536, 864)



        target_ratio = 9/16 if is_vert else 16/9



        if abs(rgb.width/rgb.height - target_ratio) > 0.01:



            rgb = ImageOps.pad(rgb, target_size, color="white", method=Image.Resampling.LANCZOS)



        dest=Path(target)



        dest.parent.mkdir(parents=True,exist_ok=True)



        temp=dest.with_name(dest.stem+"."+uuid.uuid4().hex+".png")



        rgb.save(temp,format="PNG")



        os.replace(temp,dest)



    try:



        from clean_watermark import remove_gemini_watermark



        remove_gemini_watermark(dest)



    except Exception as cw_err:



        print(f"[WATERMARK_CLEANER] Note: {cw_err}", flush=True)



    prefix = f"scene {idx}/{total} " if idx and total else ""



    print("MCP_IMAGE_IMPORTED",prefix+dest.name,"bytes",dest.stat().st_size,flush=True)







def _clear_completed_flow_queue(cdp_port=9550):



    node_dir = Path(__file__).resolve().parent / "studio_mcp" / "node"



    node_exe = node_dir / ("node.exe" if os.name == "nt" else "node")



    executable = str(node_exe) if node_exe.is_file() else (shutil.which("node") or "node")



    script = (



        "import('playwright-core').then(async ({chromium}) => {\n"



        "  try {\n"



        f"    const browser = await chromium.connectOverCDP('http://127.0.0.1:{cdp_port}');\n"



        "    for (const page of browser.contexts().flatMap(c => c.pages())) {\n"



        "      for (const frame of page.frames()) {\n"



        "        const cleared = await frame.evaluate(() => {\n"



        "          const b = window.__STORYBOARD_MCP__;\n"



        "          if (!b || b.isProcessing) return false;\n"



        "          const q = b.queue || [];\n"



        "          if (q.length > 0) {\n"



        "            if (b.capabilities && b.capabilities.clearQueue) {\n"



        "              b.capabilities.clearQueue();\n"



        "              return true;\n"



        "            }\n"



        "          }\n"



        "          return false;\n"



        "        }).catch(() => false);\n"



        "        if (cleared) { await page.waitForTimeout(400); break; }\n"



        "      }\n"



        "    }\n"



        "    await browser.close();\n"



        "  } catch (e) {}\n"



        "});\n"



    )



    try:



        from silent_subprocess import _get_silent_si_and_flags



        si, flags = _get_silent_si_and_flags()



        subprocess.run([executable, "-e", script], cwd=str(node_dir), startupinfo=si, creationflags=flags, timeout=8)



    except Exception:



        pass







def generate_episode_images(scenes,bible,*,series,episode,episode_dir,max_new_images,



                            model_index=1,backend_factory=None,visual_policy="unique"):



    if not scenes or len(scenes)>1000:



        raise StudioMcpImageError("Invalid scene batch length")



    try:



        budget=inspect_budget(len(scenes),max_new_images,visual_policy)



        anchor_indices,mapping=select_keyframes(len(scenes),budget["image_jobs"])



    except ImageBudgetError as exc:



        raise StudioMcpImageError(str(exc)) from exc



    from studio_flow_accounts import apply_worker_env



    account = apply_worker_env()



    klass,models=preflight()



    print("MCP_ACCOUNT_SELECTED",account["name"],flush=True)



    if model_index not in (0,1,2):



        raise StudioMcpImageError("Invalid image model")



    os.environ["STORYBOARD_MCP_APPROVED"]="1"



    os.environ["STORYBOARD_MCP_MAX_NEW_IMAGES"]=str(int(max_new_images))



    folder="storyboard_studio_mcp_"+clean_id(series)+"_ep"+str(int(episode)).zfill(3)



    kw={"enabled":True,"spending_approved":True,"max_new_images":int(max_new_images),



        "model":models[model_index],"fallback":False}



    specs=[]



    for idx in anchor_indices:



        scene=scenes[idx-1]



        specs.append({



            "scene_id":clean_id(series)[:55]+"_ep"+str(int(episode))+



                      "_scene_"+str(idx).zfill(4),



            "prompt":image_prompt(scene,bible),



            "aspect_ratio":"9:16" if bible.get("is_vertical") or bible.get("aspect_ratio") == "9:16" else "16:9"



        })



    # The exact image batch owns a durable budget. Resuming unchanged input



    # reuses the same receipts; a revised script cannot inherit old spent slots.



    revision=hashlib.sha256(json.dumps({"specs":specs,"model":models[model_index],



        "fallback":False},sort_keys=True,ensure_ascii=False).encode()).hexdigest()[:20]



    scope=PRODUCTION_ROOT/(folder+"_run_"+revision)



    backend=(backend_factory or klass)(scope,**kw)



    print("MCP_BATCH_PREPARED",len(specs),"scenes",len(scenes),"budget",max_new_images,



          "visual_policy",visual_policy,"model_index",model_index,flush=True)



    print("MCP_RENDERING_BATCH",len(specs),"account",account.get("name","MCP"),flush=True)




    _clear_completed_flow_queue(account.get("cdp_port", 9550))

    backend.preflight()

    receipts = backend.render_one_queue(specs)

    if len(receipts) != len(specs):

        raise StudioMcpImageError("MCP batch incomplete: no local render started")

    for idx, spec in zip(anchor_indices, specs):

        if spec["scene_id"] not in receipts:

            raise StudioMcpImageError("Missing MCP image receipt for scene " + str(idx))

        target = Path(episode_dir) / "scenes" / f"scene_{idx:04d}" / "image.png"

        import_receipt_image(receipts[spec["scene_id"]], target, idx, len(scenes))



    # Reuse images ONLY when the operator selected that cheaper mode before



    # pressing Produce. No unapproved remote image generations are added.



    if visual_policy=="reuse" and len(anchor_indices)<len(scenes):



        for scene_no in range(1,len(scenes)+1):



            anchor=int(mapping[str(scene_no)])



            if scene_no==anchor:



                continue



            source=Path(episode_dir)/"scenes"/f"scene_{anchor:04d}"/"image.png"



            target=Path(episode_dir)/"scenes"/f"scene_{scene_no:04d}"/"image.png"



            if not source.is_file() or source.stat().st_size<1024:



                raise StudioMcpImageError("Missing key visual for scene "+str(scene_no))



            target.parent.mkdir(parents=True,exist_ok=True)



            tmp=target.with_name("image."+uuid.uuid4().hex+".png")



            try:



                shutil.copy2(source,tmp)



                os.replace(tmp,target)



            finally:



                tmp.unlink(missing_ok=True)



        print("MCP_VISUALS_REUSED",len(scenes)-len(specs),"scene images",flush=True)



    for scene_no in range(1,len(scenes)+1):



        asset=Path(episode_dir)/"scenes"/f"scene_{scene_no:04d}"/"image.png"



        if not asset.is_file() or asset.stat().st_size<1024:



            raise StudioMcpImageError("Image mapping incomplete at scene "+str(scene_no))



    mapping_file=Path(episode_dir)/"visual_mapping.json"



    temp=mapping_file.with_name("visual_mapping."+uuid.uuid4().hex+".json")



    temp.write_text(json.dumps({"policy":visual_policy,"scene_count":len(scenes),



        "approved_max_new_images":int(max_new_images),"remote_jobs":len(specs),



        "anchor_scenes":anchor_indices,"scene_to_anchor":mapping},ensure_ascii=False,indent=2),encoding="utf-8")



    os.replace(temp,mapping_file)



    print("MCP_BATCH_ALL_IMAGES_PASS",len(scenes),"remote_jobs",len(specs),flush=True)



    return len(scenes)



