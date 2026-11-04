import re

def patch():
    path = "D:/STORYBOARD_AI/studio/mcp_v2_batch.py"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Patch clone branch media prefix
    old_clone_prefix = 'f"Cinematic {ratio_tag} photograph, {aspect_desc}",'
    new_clone_prefix = '''(f"Vibrant After Skool whiteboard marker illustration, {aspect_desc}" if (is_stoic is False and genre in ("whiteboard", "colored_marker"))
             else (f"Cinematic {ratio_tag} 3D animated film still, {aspect_desc}" if (is_stoic is False and genre == "animation")
             else f"Cinematic {ratio_tag} photograph, {aspect_desc}")),'''

    if old_clone_prefix in content:
        content = content.replace(old_clone_prefix, new_clone_prefix, 1)
        print("SUCCESS: clone prefix patched")
    else:
        print("WARNING: old_clone_prefix not found")

    # 2. Patch non-clone branch (lines 284-293)
    target_non_clone = '''    else:
        style_snippet = str(bible.get("visual_style", "Cinematic")).strip()[:180]
        short_prompt = (
            f"Cinematic {ratio_tag} photograph, {aspect_desc} "
            f"{scene_core}{comp_core}.{char_essence} "
            f"Art style: {style_snippet}. "
            "High quality, rich atmosphere, natural lighting, photorealistic 8k. "
            "Single continuous image filling entire canvas from edge to edge, single shot only, absolutely no split screen, no collage, no diptych, no dual panels, no borders, no filmstrip, no perforated margins, no text overlays, no watermarks, no distorted faces, no broken arms, no severed arms, no amputee, no missing limbs, no broken ruins."
        )
    return re.sub(r'\\s{2,}', ' ', short_prompt).strip()[:1000]'''

    new_non_clone = '''    elif genre in ("whiteboard", "colored_marker") or style in ("whiteboard", "colored_marker"):
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
    return re.sub(r'\\s{2,}', ' ', short_prompt).strip()[:1000]'''

    if target_non_clone not in content:
        print("ERROR: target_non_clone not found")
        return False
    content = content.replace(target_non_clone, new_non_clone)
    print("SUCCESS: non_clone genre branching patched")

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("All patches applied to mcp_v2_batch.py successfully!")
    return True

if __name__ == "__main__":
    patch()
