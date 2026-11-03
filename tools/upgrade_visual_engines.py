"""Complete Visual & Cinematic Overhaul for Stoic / Classical Genre:
1. studio/thumbnail_studio.py: Masterclass Valor Estoico style 50/50 thumbnails
2. studio/muse_video_provider.py: Live-action Roman philosopher emperor (no lifeless statues)
3. studio/comfyui_image_provider.py: Remove marble/statue restrictions & enable living cinematic characters
4. studio/studio_modes.py: Update stoic world description to live-action epic
5. studio/mcp_v2_batch.py: Lift full-length statue mandate for stoic genre
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# =========================================================================
# 1. Update studio/thumbnail_studio.py
# =========================================================================
thumb_py = ROOT / "studio" / "thumbnail_studio.py"
thumb_text = thumb_py.read_text(encoding="utf-8")

# 1A. Update Stoic Preset in LOCKED_THUMBNAIL_GENRE_PRESETS
old_stoic_preset = '''    "stoic": {
        "name": "Stoic Philosophy & Wisdom",
        "framing": "chest_up_bust",
        "subject_prompt": (
            "Monumental heroic chest-up bust portrait of a chiseled classical Greek and Roman emperor philosopher ({char_desc}), "
            "extreme close-up from chest to head, intense piercing brooding eyes, muscular neck and detailed chiseled beard, "
            "dramatic chiaroscuro golden rim lighting carving out weathered marble texture, "
            "ancient Roman forum ruins and dark tempestuous stormy sky with volumetric rim glow in the background, "
            "subject strictly occupying 48% on the LEFT half facing towards the right, leaving the entire RIGHT 52% dark atmospheric space for bold text, "
            "never full body, never standing on pedestal, never distant figure, 8k resolution cinematic masterpiece, no text, no watermark."
        ),
        "primary_color": (255, 230, 0),     # Radiant Solar Yellow #FFE600
        "secondary_color": (255, 255, 255), # Crisp Marble White
        "accent_color": (255, 230, 0),      # Radiant Solar Yellow #FFE600
        "stroke_color": (0, 0, 0),
        "stroke_width": 10,
        "shadow_layers": 6,
        "default_hooks": [
            ["DEJA DE", "CONTROLAR", "LO IMPOSIBLE"],
            ["HABLA MENOS", "OBSERVA", "TODO"],
            ["NO TE JUSTIFIQUES", "SE FUERTE", "EN SILENCIO"],
            ["DOMINA TU", "PROPIA MENTE", "AHORA"],
        ],
        "default_hooks_vi": [
            ["IM LẶNG ĐI", "QUAN SÁT TẤT CẢ", "HÀNH ĐỘNG"],
            ["ĐỪNG BIỆN MINH", "LÀM CHỦ", "TÂM TRÍ"],
            ["BÌNH THẢN", "TRƯỚC NGHỊCH CẢNH", "CHIẾN THẮNG"],
        ],
    },'''

new_stoic_preset = '''    "stoic": {
        "name": "Stoic Philosophy & Wisdom (Valor Estoico Masterclass)",
        "framing": "chest_up_bust",
        "subject_prompt": (
            "Monumental heroic live-action chest-up cinematic portrait of a chiseled Roman Emperor philosopher ({char_desc}), "
            "weathered sun-kissed bronze skin, intense piercing expressive eyes with alive pupils, muscular neck and detailed salt-and-pepper curly beard, "
            "wearing a vibrant royal crimson red draped toga (chlamys) over one shoulder, golden rim lighting outlining sculpted features and curls, "
            "magnificent illuminated ancient Athens Acropolis and Parthenon on distant rocky hill in deep starry night sky with glowing emerald teal aurora borealis and floating golden embers, "
            "subject strictly occupying 50% on the RIGHT half facing towards the left, leaving the entire LEFT 50% open deep twilight atmospheric sky for bold typography, "
            "never full body, never standing on pedestal, never distant figure, never lifeless stone statue, hyper-realistic 8k masterpiece film still, cinematic lighting, no text, no watermark."
        ),
        "primary_color": (255, 230, 0),     # Radiant Solar Yellow #FFE600
        "secondary_color": (255, 255, 255), # Crisp Pure White #FFFFFF
        "accent_color": (229, 9, 20),       # Intense Crimson Red Slash #E50914
        "brand_tag": "VALOR ESTOICO",
        "stroke_color": (0, 0, 0),
        "stroke_width": 12,
        "shadow_layers": 8,
        "default_hooks": [
            ["TU SILENCIO", "IMPONE", "RESPETO"],
            ["NO PERSIGAS,", "ATRAE", "TU DESTINO"],
            ["TU PAZ", "ES LO", "PRIMERO"],
            ["SUELTA Y", "DEJA", "BRILLAR"],
            ["ALÉJATE Y", "VOLVERÁ", "A BUSCARTE"],
            ["SUELTA Y", "GANARÁS", "TODO"],
        ],
        "default_hooks_vi": [
            ["IM LẶNG ĐI", "KẺ KHÔN NGOAN", "HÀNH ĐỘNG"],
            ["ĐỪNG BIỆN MINH", "LÀM CHỦ", "TÂM TRÍ"],
            ["BÌNH THẢN", "TRƯỚC NGHỊCH CẢNH", "CHIẾN THẮNG"],
            ["TẬP TRUNG", "VÀO CHÍNH MÌNH", "BỨT PHÁ"],
        ],
    },'''

norm_thumb = thumb_text.replace("\r\n", "\n")
norm_old_stoic = old_stoic_preset.replace("\r\n", "\n")
norm_new_stoic = new_stoic_preset.replace("\r\n", "\n")

if norm_old_stoic in norm_thumb:
    norm_thumb = norm_thumb.replace(norm_old_stoic, norm_new_stoic)
    print("1A. Successfully updated Stoic Preset in thumbnail_studio.py")
else:
    print("1A. Warning: old_stoic_preset not matched in thumbnail_studio.py")

# 1B. Soften ambient backdrop: keep background rich, reduce max_alpha from 250 to 135
old_backdrop = """    span = int(target_w * 0.60)  # Covers 60% width
    max_alpha = 250

    if text_on_left:
        for x in range(0, span, 4):
            prog = x / float(span)
            alpha = int(max_alpha * ((1.0 - prog) ** 1.25))
            ov_draw.rectangle([(x, 0), (x + 4, target_h)], fill=(0, 0, 0, alpha))
    else:
        start_x = target_w - span
        for x in range(start_x, target_w, 4):
            prog = (x - start_x) / float(span)
            alpha = int(max_alpha * (prog ** 1.25))
            ov_draw.rectangle([(x, 0), (x + 4, target_h)], fill=(0, 0, 0, alpha))"""

new_backdrop = """    span = int(target_w * 0.54)  # Covers 54% width softly
    max_alpha = 135  # Subtle cinematic sapphire vignette, preserves Acropolis & stars!

    if text_on_left:
        for x in range(0, span, 4):
            prog = x / float(span)
            alpha = int(max_alpha * ((1.0 - prog) ** 1.3))
            ov_draw.rectangle([(x, 0), (x + 4, target_h)], fill=(6, 12, 24, alpha))
    else:
        start_x = target_w - span
        for x in range(start_x, target_w, 4):
            prog = (x - start_x) / float(span)
            alpha = int(max_alpha * (prog ** 1.3))
            ov_draw.rectangle([(x, 0), (x + 4, target_h)], fill=(6, 12, 24, alpha))"""

norm_old_bd = old_backdrop.replace("\r\n", "\n")
norm_new_bd = new_backdrop.replace("\r\n", "\n")
if norm_old_bd in norm_thumb:
    norm_thumb = norm_thumb.replace(norm_old_bd, norm_new_bd)
    print("1B. Successfully softened ambient backdrop in thumbnail_studio.py")
else:
    print("1B. Warning: old_backdrop not matched in thumbnail_studio.py")

# 1C. Upgrade _smart_bust_crop_and_fit blur from 25 to 6
old_blur = "canvas = canvas.filter(ImageFilter.GaussianBlur(25))\n            # Darken canvas slightly\n            canvas = ImageEnhance.Brightness(canvas).enhance(0.55)"
new_blur = "canvas = canvas.filter(ImageFilter.GaussianBlur(6))\n            # Soft cinematic contrast\n            canvas = ImageEnhance.Brightness(canvas).enhance(0.75)"
if old_blur in norm_thumb:
    norm_thumb = norm_thumb.replace(old_blur, new_blur)
    print("1C. Successfully reduced destructive blur from 25 to 6 in thumbnail_studio.py")
else:
    print("1C. Warning: old_blur not matched in thumbnail_studio.py")

# 1D. Add dynamic red underline slash and brand watermark to typography
old_typo_loop = """        # Draw Main Crisp Stroke & Fill
        draw.text(
            (text_x_start, y_pos),
            line,
            font=font,
            fill=line_color,
            stroke_width=stroke_w,
            stroke_fill=(0, 0, 0),
        )

        cur_y += c['h'] + gap

    return im"""

new_typo_loop = """        # Draw Main Crisp Stroke & Fill
        draw.text(
            (text_x_start, y_pos),
            line,
            font=font,
            fill=line_color,
            stroke_width=stroke_w,
            stroke_fill=(0, 0, 0),
        )

        # Draw Dynamic Crimson Red Underline Slash for key action word / last line
        if i == len(line_configs) - 1 or any(kw in line.upper() for kw in ("IMPONE", "ATRAE", "GANARÁS", "CONTROLAR", "RESPETO", "BRILLAR", "VOLVERÁ", "PRIMERO", "HÀNH ĐỘNG", "CHIẾN THẮNG")):
            slash_y = y_pos + c['h'] + 4
            slash_w = min(c['w'], 380)
            if slash_w > 40:
                slash_pts = [
                    (text_x_start + 4, slash_y + 4),
                    (text_x_start + slash_w // 2, slash_y + 8),
                    (text_x_start + slash_w, slash_y + 2),
                    (text_x_start + slash_w - 6, slash_y + 9),
                    (text_x_start + slash_w // 2, slash_y + 14),
                    (text_x_start + 2, slash_y + 10),
                ]
                # Shadow
                draw.polygon([(p[0] + 3, p[1] + 3) for p in slash_pts], fill=(0, 0, 0, 220))
                # Vibrant crimson stroke
                draw.polygon(slash_pts, fill=(229, 9, 20, 255))

        cur_y += c['h'] + gap

    # Draw Elegant Brand Tagline below text (e.g. — VALOR ESTOICO —)
    brand_text = preset.get("brand_tag") or "VALOR ESTOICO"
    if brand_text:
        try:
            b_fs = 26
            b_font = ImageFont.truetype(font_path, b_fs)
            b_bbox = draw.textbbox((0, 0), brand_text, font=b_font)
            b_w = b_bbox[2] - b_bbox[0]
            b_y = cur_y + 16
            if b_y < target_h - 40:
                # Decorative gold divider lines
                line_len = 50
                line_y = b_y + (b_bbox[3] - b_bbox[1]) // 2 + 2
                draw.line([(text_x_start, line_y), (text_x_start + line_len, line_y)], fill=(255, 215, 0, 200), width=2)
                draw.text((text_x_start + line_len + 14, b_y), brand_text, font=b_font, fill=(240, 240, 240, 230), stroke_width=2, stroke_fill=(0, 0, 0, 255))
                draw.line([(text_x_start + line_len + 28 + b_w, line_y), (text_x_start + line_len * 2 + 28 + b_w, line_y)], fill=(255, 215, 0, 200), width=2)
        except Exception:
            pass

    return im"""

norm_old_typo = old_typo_loop.replace("\r\n", "\n")
norm_new_typo = new_typo_loop.replace("\r\n", "\n")
if norm_old_typo in norm_thumb:
    norm_thumb = norm_thumb.replace(norm_old_typo, norm_new_typo)
    print("1D. Successfully added dynamic red underline & brand watermark to typography in thumbnail_studio.py")
else:
    print("1D. Warning: old_typo_loop not matched in thumbnail_studio.py")

thumb_py.write_text(norm_thumb.replace("\n", "\r\n"), encoding="utf-8")


# =========================================================================
# 2. Update studio/muse_video_provider.py
# =========================================================================
muse_py = ROOT / "studio" / "muse_video_provider.py"
muse_text = muse_py.read_text(encoding="utf-8")

old_muse_stoic = """    elif is_stoic:
        default_chars = "Heroic Full-Length Classical Standing Statue of Ancient Philosopher (strictly a carved stone/marble sculpture, NEVER a living human)"
        chars_str = "; ".join(chars_info) if chars_info else default_chars
        parts = [
            "FORMAT & STYLE: Cinematic 16:9 shot of monumental full-length classical Greco-Roman carved marble or bronze statues standing tall from head to toe on ancient stone forum ground. Authentic weathered Carrara marble texture with realistic micro-cracks and polished highlights, grand flowing carved stone togas draping down past knees to feet. High-contrast chiaroscuro lighting, floating embers and dust particles, dark ancient Roman ruins background.",
            f"CHARACTERS: {chars_str}.",
            f"SETTING & VISUAL SETUP: {visual_setup or master_setting}.",
            "LIGHTING & COLOR: Dramatic high-contrast chiaroscuro lighting, golden rim light accentuating chiseled stone features, atmospheric shadows, volumetric dust motes.",
            f"CAMERA: {camera}, majestic cinematic push-in or slow pan around the monumental full-length sculpture.",
            "PERFORMANCE & PRESENCE: Magnificent monumental statue presence, majestic carved stone stillness with drifting atmospheric dust particles and lighting shifts. The sculpture remains authentic carved stone/marble.",
        ]
        if action:
            parts.append(f"TIMED ACTION: {action}.")
        if dialogue:
            parts.append(f"AUDIO & DIALOGUE: Deep contemplative, dignified stoic philosophical narration echoing through ancient stone colonnades: \\"{dialogue}\\". Atmospheric reverberation, subtle wind and ambient forum echoes.")
        else:
            parts.append("AUDIO: Atmospheric ancient forum room tone, distant wind, subtle dust and stone echoes.")
        parts.append("CONSTRAINTS: ABSOLUTELY BANNED: living human being, human flesh and skin tones, real living person, half-body bust, severed torso, tabletop pedestal, cropped legs, missing feet, modern clothing.")"""

new_muse_stoic = """    elif is_stoic:
        default_chars = "Marcus Aurelius / Classical Roman Philosopher Emperor (dignified live-action statesman with weathered bronze skin, piercing contemplative gaze, salt-and-pepper curly beard, wearing royal crimson draped toga)"
        chars_str = "; ".join(chars_info) if chars_info else default_chars
        parts = [
            "FORMAT & STYLE: Cinematic 16:9 historical epic film still. Masterful live-action Greco-Roman cinematography with natural skin pores, realistic wrinkles, expressive eye gaze, and lifelike presence. Grand illuminated ancient Roman forum, majestic marble colonnades, and distant Acropolis at twilight under a starry sky with glowing torches and floating golden embers.",
            f"CHARACTERS: {chars_str}.",
            f"SETTING & VISUAL SETUP: {visual_setup or master_setting}.",
            "LIGHTING & COLOR: Dramatic cinematic chiaroscuro, warm amber golden key light with deep sapphire teal fill, delicate volumetric rim light outlining actor's shoulders and curls. Vibrant imperial crimson red and warm ivory textile togas. Never pitch black.",
            f"CAMERA: {camera}, smooth motivated cinematic tracking shot, natural depth of field with soft bokeh background.",
            "PERFORMANCE & PRESENCE: Dignified statesman presence, organic subtle breathing and expressive eye gaze, natural contemplative movement (slow deliberate walking, gesturing thoughtfully, gazing out over the city). Authentic live-action dramatic performance.",
        ]
        if action:
            parts.append(f"TIMED ACTION: {action}.")
        if dialogue:
            parts.append(f"AUDIO & DIALOGUE: Deep resonant, dignified stoic philosophical narration echoing through ancient colonnades: \\"{dialogue}\\". Rich vocal warmth, subtle wind and ambient forum echoes.")
        else:
            parts.append("AUDIO: Atmospheric ancient forum room tone, distant night breeze, subtle torch fire crackles.")
        parts.append("CONSTRAINTS: BANNED: lifeless stone statue, severed torso, blank white eyes, plastic CGI render, cartoon, modern clothing, ugly artifacts, watermark.")"""

norm_muse = muse_text.replace("\r\n", "\n")
norm_old_muse = old_muse_stoic.replace("\r\n", "\n")
norm_new_muse = new_muse_stoic.replace("\r\n", "\n")

if norm_old_muse in norm_muse:
    norm_muse = norm_muse.replace(norm_old_muse, norm_new_muse)
    muse_py.write_text(norm_muse.replace("\n", "\r\n"), encoding="utf-8")
    print("2. Successfully updated Stoic prompt in muse_video_provider.py to Live-Action Epic.")
else:
    print("2. Warning: old_muse_stoic not matched in muse_video_provider.py")


# =========================================================================
# 3. Update studio/comfyui_image_provider.py
# =========================================================================
comfy_py = ROOT / "studio" / "comfyui_image_provider.py"
comfy_text = comfy_py.read_text(encoding="utf-8")

old_comfy = """    elif is_statue or genre == "stoic":
        import re
        sanitized = re.sub(
            r"(?i)\\b(golden[- ]?bronze|golden|gold skin|shirtless|bodybuilder|praying hands|lotus pose|pecs|deltoids|bust|half[- ]?body|torso[- ]only|tabletop bust|pedestal)\\b",
            "",
            clean_prompt,
        ).strip()
        positive = (
            f"monumental full-length classical Roman marble sculpture standing tall from head to toe, "
            f"complete anatomical standing figure with full legs and feet firmly planted on grand ancient stone plaza base, "
            f"heroic posture, authentic flowing classical Roman toga draping all the way down past knees to feet, "
            f"masterpiece antique carved Carrara marble stone texture with subtle weathered fissures, "
            f"blank carved marble eyes, panoramic wide 16:9 cinematic composition, grand ancient Roman architecture and colonnade backdrop, "
            f"dramatic atmospheric chiaroscuro lighting, soft volumetric rim light, epic cinematic depth: {sanitized}"
        )
        negative = (
            "half-body bust, bust, torso only, severed bust, amputated statue, waist-up, tabletop pedestal, "
            "small pedestal, museum bust stand, headless, armless, cropped legs, missing feet, cut off at waist, floating torso, "
            "real living person, human skin pores, nipples, modern clothes, "
            "yellow skin, shiny gold paint, golden skin, orange skin tone, oily body paint, "
            "9:16, vertical framing, portrait mode, side bars, pillarbox, narrow frame, split screen, "
            "ugly, deformed, bad anatomy, blurry, low quality, artifacts, watermark, text, signature"
        )"""

new_comfy = """    elif is_statue or genre == "stoic":
        positive = (
            f"Cinematic live-action 16:9 historical epic film still, heroic Roman philosopher emperor (Marcus Aurelius archetype), "
            f"weathered sun-kissed bronze skin with realistic pores and wrinkles, intense piercing dark eyes with living expressive pupils, "
            f"distinguished salt-and-pepper curly hair and thick groomed beard, draped in rich royal crimson red and ivory toga (chlamys), "
            f"standing in ancient Roman forum with illuminated marble pillars, sweeping view of distant Acropolis at twilight, "
            f"dramatic chiaroscuro lighting, warm amber golden key light, deep sapphire teal shadows, soft volumetric rim glow, "
            f"photorealistic 8k, master cinematography, shot on 35mm lens: {clean_prompt}"
        )
        negative = (
            "lifeless stone statue, severed bust, tabletop pedestal, blank carved eyes, white stone skin, statue stand, "
            "zombie, deformed, cartoon, 3d cgi render, anime, modern clothes, t-shirt, plastic, blurry, low quality, "
            "ugly, bad anatomy, bad eyes, extra limbs, watermark, text, signature"
        )"""

norm_comfy = comfy_text.replace("\r\n", "\n")
norm_old_comfy = old_comfy.replace("\r\n", "\n")
norm_new_comfy = new_comfy.replace("\r\n", "\n")

if norm_old_comfy in norm_comfy:
    norm_comfy = norm_comfy.replace(norm_old_comfy, norm_new_comfy)
    comfy_py.write_text(norm_comfy.replace("\n", "\r\n"), encoding="utf-8")
    print("3. Successfully updated Stoic prompt in comfyui_image_provider.py to Live-Action Epic.")
else:
    print("3. Warning: old_comfy not matched in comfyui_image_provider.py")


# =========================================================================
# 4. Update studio/studio_modes.py
# =========================================================================
modes_py = ROOT / "studio" / "studio_modes.py"
modes_text = modes_py.read_text(encoding="utf-8")

old_mode = '"stoic":"Cinematic Greco-Roman classical world of monumental classical statues (16:9 widescreen). Depicts magnificent full-length classical marble and bronze sculptures of ancient philosophers standing and seated from head to toe with complete anatomical figures, weathered Carrara marble textures, flowing classical draped togas extending to the feet, and grand ground-level ancient Roman architecture backdrop. Deep atmospheric chiaroscuro lighting, volumetric rim light, and cinematic depth of field. Strictly full statues only, never half-body busts."'

new_mode = '"stoic":"Cinematic Greco-Roman classical epic world (16:9 widescreen). Depicts dignified ancient Roman and Greek philosopher emperors (Marcus Aurelius archetype) in rich royal crimson and ivory togas, weathered bronze skin, piercing gaze, amidst magnificent ancient colonnades, temples, and glowing night Acropolis vistas. Dynamic cinematic framing with expressive close-ups, medium portraits, and majestic wide architectural compositions. Deep atmospheric chiaroscuro, volumetric golden rim light, and rich film depth."'

if old_mode in modes_text:
    modes_text = modes_text.replace(old_mode, new_mode)
    modes_py.write_text(modes_text, encoding="utf-8")
    print("4. Successfully updated stoic mode definition in studio_modes.py.")
else:
    print("4. Warning: old_mode not matched in studio_modes.py")


# =========================================================================
# 5. Update studio/mcp_v2_batch.py
# =========================================================================
mcp_py = ROOT / "studio" / "mcp_v2_batch.py"
mcp_text = mcp_py.read_text(encoding="utf-8")

old_mcp = """    is_statue_scene = any(kw in scene_desc_low for kw in ("statue", "sculpture", "monument", "tượng", "carrara marble", "stone figure", "carved stone")) or genre == "stoic"
    if is_statue_scene:
        statue_instruction = (
            ". FULL-LENGTH COMPLETE CLASSICAL HEROIC STATUE MANDATE: Depict the subject strictly as a magnificent classical Greek or Roman stone/marble or bronze sculpture. "
            "It MUST be a COMPLETE FULL-LENGTH STATUE visible from head to toe, with complete anatomical figure (full legs, feet firmly planted on a grand ground-level ancient plaza base, and flowing classical toga draping all the way down). "
            "ABSOLUTE PROHIBITION: NEVER render amputated half-body museum busts, torso-only sculptures, armless busts, tabletop pedestals, or waist-up statues. The entire full-length statue must be completely visible."
        )"""

new_mcp = """    is_statue_scene = any(kw in scene_desc_low for kw in ("statue", "sculpture", "monument", "tượng", "carrara marble", "stone figure", "carved stone")) and genre != "stoic"
    if genre == "stoic":
        statue_instruction = (
            ". EPIC LIVE-ACTION STOIC CINEMATIC: Depict a distinguished live-action Roman philosopher emperor with weathered bronze skin, "
            "deep piercing contemplative eyes, salt-and-pepper beard, wearing a rich royal crimson red draped toga. "
            "Dynamic framing with dramatic close-up and medium bust compositions against ancient colonnades and illuminated night Acropolis."
        )
    elif is_statue_scene:
        statue_instruction = (
            ". CLASSICAL SCULPTURE: Depict the subject as a heroic classical sculpture with dramatic lighting and architectural backdrop."
        )"""

norm_mcp = mcp_text.replace("\r\n", "\n")
norm_old_mcp = old_mcp.replace("\r\n", "\n")
norm_new_mcp = new_mcp.replace("\r\n", "\n")

if norm_old_mcp in norm_mcp:
    norm_mcp = norm_mcp.replace(norm_old_mcp, norm_new_mcp)
    mcp_py.write_text(norm_mcp.replace("\n", "\r\n"), encoding="utf-8")
    print("5. Successfully updated stoic prompt in mcp_v2_batch.py.")
else:
    print("5. Warning: old_mcp not matched in mcp_v2_batch.py")

print("\nALL VISUAL ENGINE UPGRADES COMPLETED!")
