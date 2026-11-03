"""Master Pre-Production Asset Manager for Cinematic Drama & AI Filmmaking.
Generates, tracks, and locks:
1. Character Turnaround Sheets (4-angle model sheets: front, 3/4 left, 3/4 right, back view).
2. Master Location Plates (Wide establishing, reverse angle, lighting/color scheme).
3. Key Hero Story Props (3-angle studio turnaround with scale reference).
4. HTML / Markdown Master Asset Manifest & Visual Previews.
Strictly adheres to Hollywood pre-production standards and ComfyUI/IP-Adapter/PuLID consistency guidelines.
"""

from __future__ import annotations

import os
import sys
import re
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

STUDIO_DIR = Path(__file__).resolve().parent.parent
if str(STUDIO_DIR) not in sys.path:
    sys.path.insert(0, str(STUDIO_DIR))

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def slugify_name(name: str) -> str:
    """Converts names to clean filesystem-safe slugs."""
    s = str(name or "").strip().lower()
    s = re.sub(r"[^a-z0-9_\-]+", "_", s)
    return s.strip("_") or "character"


def _get_font(size: int = 16, bold: bool = False) -> ImageFont.ImageFont:
    """Loads a reliable Windows system font or falls back gracefully."""
    font_names = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf",
    ]
    for fn in font_names:
        if os.path.exists(fn):
            try:
                return ImageFont.truetype(fn, size=size)
            except Exception:
                pass
    return ImageFont.load_default()


def build_character_turnaround_prompt(
    char_name: str,
    char_profile: Dict[str, Any],
    genre: str = "drama",
    visual_style: str = "color_cinematic"
) -> Dict[str, Any]:
    """
    Constructs an industry-standard 4-view character turnaround sheet prompt.
    Views: Front View (0°), Three-quarter Left (45°), Three-quarter Right (315°), Profile Back View (180°).
    Rendered on a neutral 18% gray backdrop (#808080) with flat diffused softbox studio lighting.
    """
    g_low = str(genre or "").lower().strip()
    s_low = str(visual_style or "").lower().strip()

    raw_app = str(
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
    app_dna = extract_single_character_description(raw_app, char_name).strip()

    attire = str(char_profile.get("attire") or char_profile.get("wardrobe") or "").strip()
    gender = str(char_profile.get("gender") or "unspecified").lower()
    role = str(char_profile.get("role") or "supporting")

    # Detect artistic style family
    is_stoic = (
        g_low == "stoic" or
        any(k in app_dna.lower() for k in ["classical statue", "marble statue", "tượng đá", "sculpture", "carrara marble", "marcus aurelius"])
    )
    is_3d_anim = (
        g_low in ("animation", "3d_animation", "hoạt hình") or
        s_low in ("color_animation", "animation_3d", "3d_cgi")
    )
    is_anime_2d = (
        not is_3d_anim and (
            g_low in ("anime", "2d_animation") or
            s_low in ("anime", "2d_anime", "manga")
        )
    )
    is_whiteboard = (
        g_low in ("whiteboard", "colored_marker") or
        s_low in ("whiteboard", "colored_marker")
    )

    if is_stoic:
        style_header = (
            "FORMAT & STYLE: Classical Roman sculpture model turnaround sheet, 4 distinct camera views of the exact same carved classical statue aligned horizontally: "
            "full front view (0 deg), three-quarter left view (45 deg), three-quarter right view (315 deg), profile back view (180 deg). "
            "Authentic weathered Carrara marble texture with subtle historical fissure lines and smooth chisel marks. "
            "Full-length standing statue from head to toe, legs and sandals anchored on stone plinth. "
            "Neutral dark gray studio backdrop (#404040), dramatic soft chiaroscuro rim lighting carving stone curls and draped toga folds. "
            "ABSOLUTELY BANNED: living human flesh, living person, pink skin tones, severed bust, tabletop pedestal."
        )
        neg_rules = "Living human flesh, pink skin pores, modern clothing, severed bust, missing limbs, floating torso, yellow plastic skin."
    elif is_3d_anim:
        style_header = (
            "FORMAT & STYLE: 3D animated feature film character model sheet (Pixar, DreamWorks animation quality). "
            "4 distinct camera views of the exact same stylized character aligned horizontally: "
            "full front view (0 deg), three-quarter left view (45 deg), three-quarter right view (315 deg), profile back view (180 deg). "
            "Stylized character design, velvety subsurface scattering (SSS) on skin, rich 3D textures, clean volumetric rim lights, solid neutral 18% gray backdrop (#808080). "
            "ABSOLUTELY BANNED: live-action photorealism, real human flesh pores."
        )
        neg_rules = "Live-action photorealism, real human flesh pores, uncannily realistic eyes, flat unlit geometry, distorted hands."
    elif is_anime_2d:
        style_header = (
            "FORMAT & STYLE: High-end 2D anime feature film character model sheet (Kyoto Animation, Makoto Shinkai aesthetic). "
            "4 distinct camera views of the exact same character aligned horizontally: "
            "full front view (0 deg), three-quarter left view (45 deg), three-quarter right view (315 deg), profile back view (180 deg). "
            "Clean professional line-art, vibrant cel-shaded color gradients, clean studio turnaround on neutral light gray backdrop (#C0C0C0). "
            "ABSOLUTELY BANNED: live-action footage, photorealistic skin."
        )
        neg_rules = "Live-action footage, photorealistic skin pores, 3D CGI plastic render, inconsistent hair color across angles."
    elif is_whiteboard:
        style_header = (
            "FORMAT & STYLE: Expressive colored whiteboard marker character sheet in signature style of After Skool (16:9). "
            "4 distinct hand-drawn marker views of the exact same character aligned horizontally: "
            "front view, three-quarter left view, three-quarter right view, back view. "
            "Hand-drawn with deep crimson red, royal blue, and bold ink black contours on pure white background (#ffffff)."
        )
        neg_rules = "Photorealistic skin, dark background, 3D CGI, blurry smudges, gray gradients."
    else:
        # Standard Cinematic Photorealistic Drama
        style_header = (
            "FORMAT & STYLE: Professional cinema character model sheet, turnaround reference plate, 4 distinct camera views of the exact same living actor aligned horizontally: "
            "full front view (0 deg), three-quarter left view (45 deg), three-quarter right view (315 deg), profile back view (180 deg). "
            "Shot on 35mm anamorphic lens, organic skin texture with natural pores, subtle imperfections, authentic hair strands. "
            "Identical facial geometry, identical hairstyle, identical immutable wardrobe across all 4 angles. "
            "Clean neutral 18% gray studio backdrop (#808080), flat diffused softbox lighting with soft rim light separating subject from background. "
            "ABSOLUTELY BANNED: background clutter, multiple different people, distorted anatomy, waxy plastic skin."
        )
        neg_rules = "Waxy plastic mannequin skin, artificial CGI smoothing, distorted hands, fluctuating clothing, cluttered background."

    wardrobe_desc = attire or "Locked wardrobe maintained identically across all 4 angles."
    full_prompt = (
        f"{style_header}\n"
        f"CHARACTER DNA: {char_name} ({gender}, role: {role}). {app_dna}.\n"
        f"WARDROBE & ATTIRE: {wardrobe_desc}\n"
        f"LIGHTING & SETUP: Professional studio turnaround alignment, horizontal baseline, perfect anatomical consistency."
    )

    return {
        "character_name": char_name,
        "slug": slugify_name(char_name),
        "gender": gender,
        "role": role,
        "appearance_dna": app_dna,
        "attire": wardrobe_desc,
        "negative_rules": neg_rules,
        "style_category": "stoic" if is_stoic else ("3d_animation" if is_3d_anim else ("anime" if is_anime_2d else ("whiteboard" if is_whiteboard else "cinematic_drama"))),
        "turnaround_prompt_4_views": full_prompt,
        "views": [
            {"angle": 0, "name": "front_view", "label": "Chính diện (0°)"},
            {"angle": 45, "name": "three_quarter_left", "label": "Nghiêng 3/4 trái (45°)"},
            {"angle": 315, "name": "three_quarter_right", "label": "Nghiêng 3/4 phải (315°)"},
            {"angle": 180, "name": "profile_back", "label": "Góc quay sau lưng (180°)"}
        ]
    }


def render_character_turnaround_sheet(
    char_meta: Dict[str, Any],
    output_path: Path,
    reference_image: Optional[Path] = None,
    series_name: str = "Series",
    episode_num: int = 1
) -> Path:
    """
    Renders an industry-grade 1920x1080 Character Model Sheet blueprint.
    Integrates 4 angle viewports, Hollywood alignment guidelines, and biometric DNA spec.
    """
    out_p = Path(output_path).resolve()
    out_p.parent.mkdir(parents=True, exist_ok=True)

    w, h = 1920, 1080
    style_cat = char_meta.get("style_category", "cinematic_drama")

    # Background color scheme based on style
    if style_cat == "stoic":
        bg_color = (22, 24, 28)
        grid_color = (36, 40, 48)
        header_accent = (212, 175, 55)  # Gold
        text_primary = (240, 242, 245)
        text_secondary = (160, 168, 180)
        panel_bg = (16, 18, 22)
    elif style_cat == "whiteboard":
        bg_color = (248, 250, 252)
        grid_color = (226, 232, 240)
        header_accent = (220, 38, 38)   # Crimson Red
        text_primary = (15, 23, 42)
        text_secondary = (71, 85, 105)
        panel_bg = (255, 255, 255)
    else:  # cinematic_drama, 3d_animation, anime
        bg_color = (32, 35, 42)
        grid_color = (48, 52, 64)
        header_accent = (56, 189, 248)  # Cyan
        text_primary = (241, 245, 249)
        text_secondary = (148, 163, 184)
        panel_bg = (20, 22, 28)

    img = Image.new("RGB", (w, h), color=bg_color)
    draw = ImageDraw.Draw(img)

    # 1. Subtle Hollywood studio alignment grid
    grid_spacing = 40
    for gx in range(0, w, grid_spacing):
        draw.line([(gx, 0), (gx, h)], fill=grid_color, width=1)
    for gy in range(0, h, grid_spacing):
        draw.line([(gy, 0), (w, gy)], fill=grid_color, width=1)

    # 2. Top Header Bar (Height 90px)
    draw.rectangle([0, 0, w, 85], fill=panel_bg)
    draw.line([(0, 85), (w, 85)], fill=header_accent, width=2)

    font_title = _get_font(28, bold=True)
    font_sub = _get_font(13, bold=False)
    font_badge = _get_font(12, bold=True)
    font_panel = _get_font(14, bold=True)
    font_spec_head = _get_font(13, bold=True)
    font_spec_body = _get_font(11, bold=False)

    char_name = char_meta.get("character_name", "Character")
    role_str = str(char_meta.get("role", "Protagonist")).upper()
    gender_str = str(char_meta.get("gender", "")).upper()

    # Left header info
    draw.text((40, 16), char_name.upper(), fill=text_primary, font=font_title)
    sub_title_text = f"SERIES: {series_name.upper()} | EPISODE {episode_num:03d} | ROLE: {role_str} | GENDER: {gender_str} | STYLE: {style_cat.upper()}"
    draw.text((40, 56), sub_title_text, fill=text_secondary, font=font_sub)

    # Right header badge
    badge_text = "MASTER MODEL SHEET // 4-VIEW ROTATION LOCK"
    draw.rectangle([w - 480, 22, w - 40, 62], fill=(0, 0, 0, 160), outline=header_accent, width=1)
    draw.text((w - 460, 32), badge_text, fill=header_accent, font=font_badge)

    # 3. Four Panels for 4 Angles
    margin_x = 40
    panel_y_top = 110
    panel_y_bot = 820
    panel_h = panel_y_bot - panel_y_top
    total_w = w - (margin_x * 2)
    gap_x = 24
    panel_w = (total_w - (gap_x * 3)) // 4

    views = char_meta.get("views", [
        {"angle": 0, "name": "front_view", "label": "CHÍNH DIỆN (0°)"},
        {"angle": 45, "name": "three_quarter_left", "label": "NGHIÊNG 3/4 TRÁI (45°)"},
        {"angle": 315, "name": "three_quarter_right", "label": "NGHIÊNG 3/4 PHẢI (315°)"},
        {"angle": 180, "name": "profile_back", "label": "SAU LƯNG (180°)"}
    ])

    # If reference image provided, try to load it
    ref_loaded = None
    if reference_image and Path(reference_image).is_file():
        try:
            with Image.open(reference_image) as ref_im:
                ref_loaded = ref_im.convert("RGB")
        except Exception:
            ref_loaded = None

    for i, v in enumerate(views[:4]):
        px1 = margin_x + i * (panel_w + gap_x)
        px2 = px1 + panel_w

        # Panel background
        draw.rectangle([px1, panel_y_top, px2, panel_y_bot], fill=panel_bg, outline=grid_color, width=1)

        # Panel Angle Header Badge
        badge_y = panel_y_top + 10
        draw.rectangle([px1 + 10, badge_y, px2 - 10, badge_y + 28], fill=(30, 34, 42), outline=header_accent, width=1)
        angle_lbl = v.get("label", f"ANGLE {v.get('angle', 0)}°")
        draw.text((px1 + 20, badge_y + 6), angle_lbl, fill=header_accent, font=font_panel)

        # Inner Viewport for Character
        vx1 = px1 + 12
        vy1 = badge_y + 36
        vx2 = px2 - 12
        vy2 = panel_y_bot - 14
        vw = vx2 - vx1
        vh = vy2 - vy1

        draw.rectangle([vx1, vy1, vx2, vy2], fill=(12, 14, 18), outline=(36, 40, 50), width=1)

        # Insert Character Artwork if reference image exists
        if ref_loaded:
            try:
                # If ref_loaded is wide (likely already a 4-view model sheet), crop each quadrant!
                rw, rh = ref_loaded.size
                if rw / rh > 1.3:
                    # Crop quadrant for view i
                    qx1 = int(i * (rw / 4.0))
                    qx2 = int((i + 1) * (rw / 4.0))
                    quad = ref_loaded.crop((qx1, 0, qx2, rh))
                    fitted = ImageOps.fit(quad, (vw, vh), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
                    img.paste(fitted, (vx1, vy1))
                else:
                    # Single reference image: use perspective / flipping cues
                    fitted = ImageOps.fit(ref_loaded, (vw, vh), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
                    if v.get("angle") == 315:
                        fitted = ImageOps.mirror(fitted)
                    elif v.get("angle") == 180:
                        fitted = fitted.filter(ImageFilter.BoxBlur(1))
                    img.paste(fitted, (vx1, vy1))
            except Exception:
                pass
        else:
            # Procedural Anatomical Silhouette & Vector Markers
            mid_vx = vx1 + vw // 2
            # Head circle
            head_y = vy1 + int(vh * 0.18)
            head_r = int(vh * 0.07)
            draw.ellipse([mid_vx - head_r, head_y - head_r, mid_vx + head_r, head_y + head_r], fill=(45, 52, 65), outline=header_accent, width=1)
            # Torso trapezoid
            torso_y1 = head_y + head_r + 10
            torso_y2 = torso_y1 + int(vh * 0.28)
            tw_top = int(head_r * 2.2)
            tw_bot = int(head_r * 1.6)
            draw.polygon([
                (mid_vx - tw_top // 2, torso_y1),
                (mid_vx + tw_top // 2, torso_y1),
                (mid_vx + tw_bot // 2, torso_y2),
                (mid_vx - tw_bot // 2, torso_y2)
            ], fill=(36, 42, 54), outline=(70, 80, 100))
            # Legs
            leg_y2 = vy2 - int(vh * 0.08)
            draw.rectangle([mid_vx - tw_bot // 2, torso_y2, mid_vx - 6, leg_y2], fill=(30, 35, 45))
            draw.rectangle([mid_vx + 6, torso_y2, mid_vx + tw_bot // 2, leg_y2], fill=(30, 35, 45))
            # Angle vector notation
            draw.text((vx1 + 16, vy2 - 30), f"CAM: {v.get('angle', 0)}° | LOCKED", fill=text_secondary, font=font_sub)

    # 4. Golden Hollywood Horizontal Baselines across all panels
    guide_y_levels = [
        ("CROWN", panel_y_top + int(panel_h * 0.14), (80, 90, 110)),
        ("EYE LEVEL", panel_y_top + int(panel_h * 0.22), (56, 189, 248)),  # Cyan
        ("CHIN", panel_y_top + int(panel_h * 0.29), (80, 90, 110)),
        ("SHOULDER", panel_y_top + int(panel_h * 0.35), (80, 90, 110)),
        ("WAIST", panel_y_top + int(panel_h * 0.52), (80, 90, 110)),
        ("BASE PLINTH", panel_y_top + int(panel_h * 0.88), (212, 175, 55)), # Gold
    ]

    for lbl, gy, col in guide_y_levels:
        # Draw dashed line across the 4 panels
        dash_len = 8
        gap_len = 6
        curr_x = margin_x
        while curr_x < w - margin_x:
            draw.line([(curr_x, gy), (min(curr_x + dash_len, w - margin_x), gy)], fill=col, width=1)
            curr_x += dash_len + gap_len
        draw.text((margin_x - 32, gy - 6), lbl[:2], fill=col, font=font_sub)

    # 5. Bottom Specification Dashboard (y=840 to y=1050)
    spec_y1 = 845
    spec_y2 = 1055
    draw.rectangle([margin_x, spec_y1, w - margin_x, spec_y2], fill=panel_bg, outline=grid_color, width=1)
    draw.line([(margin_x, spec_y1), (w - margin_x, spec_y1)], fill=header_accent, width=1)

    spec_col_w = (total_w - 40) // 3
    # Box 1: Biometric DNA
    bx1 = margin_x + 15
    draw.text((bx1, spec_y1 + 10), "🧬 KHÓA DNA NGOẠI HÌNH (BIOMETRIC DNA LOCK)", fill=header_accent, font=font_spec_head)
    dna_text = char_meta.get("appearance_dna", "Authentic actor with distinct features")
    _draw_wrapped_text(draw, dna_text, (bx1, spec_y1 + 34), spec_col_w - 20, fill=text_primary, font=font_spec_body, max_lines=6)

    # Box 2: Wardrobe & Attire
    bx2 = bx1 + spec_col_w + 15
    draw.line([(bx2 - 8, spec_y1 + 10), (bx2 - 8, spec_y2 - 10)], fill=grid_color, width=1)
    draw.text((bx2, spec_y1 + 10), "👔 TRANG PHỤC BẤT BIẾN (IMMUTABLE WARDROBE)", fill=header_accent, font=font_spec_head)
    wardrobe_text = char_meta.get("attire", "Locked complete wardrobe maintained across all 4 angles.")
    _draw_wrapped_text(draw, wardrobe_text, (bx2, spec_y1 + 34), spec_col_w - 20, fill=text_primary, font=font_spec_body, max_lines=6)

    # Box 3: Anti-Drift Constraints
    bx3 = bx2 + spec_col_w + 15
    draw.line([(bx3 - 8, spec_y1 + 10), (bx3 - 8, spec_y2 - 10)], fill=grid_color, width=1)
    draw.text((bx3, spec_y1 + 10), "🚫 RÀNG BUỘC CHỐNG BIẾN ĐỔI (ANTI-DRIFT RULES)", fill=(244, 63, 94), font=font_spec_head)
    neg_text = char_meta.get("negative_rules", "No plastic skin, no distorted anatomy, no clothing mutation.")
    _draw_wrapped_text(draw, neg_text, (bx3, spec_y1 + 34), spec_col_w - 20, fill=(254, 205, 211), font=font_spec_body, max_lines=6)

    img.save(str(out_p), quality=95)
    print(f"[ASSET_RENDER] Đã kết xuất Character Model Sheet: {out_p.name} ({out_p.stat().st_size / 1024:.1f} KB)", flush=True)
    return out_p


def _draw_wrapped_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    pos: tuple[int, int],
    max_width: int,
    fill: tuple[int, int, int],
    font: ImageFont.ImageFont,
    max_lines: int = 5
) -> None:
    """Helper to cleanly wrap and render multi-line text blocks."""
    x, y = pos
    words = str(text or "").replace("\n", " ").split()
    lines = []
    curr_line = []

    for w in words:
        test_line = " ".join(curr_line + [w])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if (bbox[2] - bbox[0]) <= max_width:
            curr_line.append(w)
        else:
            if curr_line:
                lines.append(" ".join(curr_line))
            curr_line = [w]
            if len(lines) >= max_lines:
                break

    if curr_line and len(lines) < max_lines:
        lines.append(" ".join(curr_line))

    for i, line in enumerate(lines[:max_lines]):
        draw.text((x, y + (i * 18)), line, fill=fill, font=font)


def generate_master_asset_pack(
    episode_dir: Path,
    plan_data: Dict[str, Any],
    genre: str = "drama",
    visual_style: str = "color_cinematic",
    render_images: bool = True
) -> Dict[str, Any]:
    """
    Initializes the Pre-Production Master Asset Pack for an episode:
    - 00_ASSET_PACK/characters/ : Turnaround sheets & specs for each character
    - 00_ASSET_PACK/locations/  : Master location plates & color palettes
    - 00_ASSET_PACK/props/      : Hero prop turnaround sheets
    - 00_ASSET_PACK/MASTER_ASSET_MANIFEST.md & HTML preview.
    """
    ep_dir = Path(episode_dir)
    asset_root = ep_dir / "00_ASSET_PACK"
    chars_dir = asset_root / "characters"
    locs_dir = asset_root / "locations"
    props_dir = asset_root / "props"

    for d in (chars_dir, locs_dir, props_dir):
        d.mkdir(parents=True, exist_ok=True)

    print(f"\n=======================================================", flush=True)
    print(f"👑 [TIỀN KỲ ĐIỆN ẢNH] KHỞI TẠO BỘ TÀI SẢN CHUẨN (MASTER ASSET PACK)", flush=True)
    print(f"   Thư mục lưu trữ: {asset_root}", flush=True)
    print(f"=======================================================\n", flush=True)

    series_name = plan_data.get("series_name") or ep_dir.parent.name or "Series"
    ep_num = plan_data.get("episode_num") or 1
    if isinstance(ep_num, str) and ep_num.isdigit():
        ep_num = int(ep_num)

    # 1. Process Characters (Turnaround Sheets)
    cast_dict = (
        plan_data.get("cast") or
        plan_data.get("bible", {}).get("characters") or
        plan_data.get("characters") or
        {}
    )
    char_records = []

    if isinstance(cast_dict, list):
        new_cast = {}
        for c in cast_dict:
            if isinstance(c, dict) and c.get("name"):
                new_cast[c["name"]] = c
            elif isinstance(c, str):
                new_cast[c] = {"description": c}
        cast_dict = new_cast

    # Check for potential reference images from scenes
    scene_ref_map = {}
    for sc_sub in (ep_dir / "scenes").glob("scene_*"):
        img_p = sc_sub / "image.png"
        if img_p.is_file():
            scene_ref_map["first_scene"] = img_p
            break

    for char_name, char_data in cast_dict.items():
        if str(char_name).lower() in ("narrator", "người dẫn chuyện", "dẫn chuyện"):
            continue

        c_prof = char_data if isinstance(char_data, dict) else {"description": str(char_data)}
        turnaround_meta = build_character_turnaround_prompt(char_name, c_prof, genre, visual_style)
        c_slug = turnaround_meta["slug"]

        img_target = chars_dir / f"{c_slug}_turnaround.jpg"
        turnaround_meta["image_path"] = str(img_target)

        # Look for existing master character portrait or reference images
        char_ref = None
        # 1. Direct local master portrait in characters directory
        for cand_name in [f"{c_slug}_master.jpg", f"{c_slug}_master.png", f"{c_slug}_portrait.jpg"]:
            cand_p = chars_dir / cand_name
            if cand_p.is_file():
                char_ref = cand_p
                break
        # 2. Check sibling episodes in same series
        if not char_ref and ep_dir.parent.is_dir():
            for sibling_ep in ep_dir.parent.glob("episode_*/00_ASSET_PACK/characters"):
                cand_p = sibling_ep / f"{c_slug}_master.jpg"
                if cand_p.is_file():
                    char_ref = cand_p
                    break
        # 3. Check brain directory for subagent-generated master portraits
        if not char_ref:
            brain_dir = Path.home() / ".gemini" / "antigravity" / "brain"
            for ext in ["jpg", "png", "jpeg"]:
                for sub_img in brain_dir.glob(f"**/*{c_slug}*.{ext}"):
                    if sub_img.is_file():
                        char_ref = sub_img
                        break
                if char_ref:
                    break
        if not char_ref and "marcus" in c_slug:
            for sub_img in brain_dir.glob("**/*marcus_aurelius*.jpg"):
                if sub_img.is_file():
                    char_ref = sub_img
                    break
        if not char_ref:
            char_ref = scene_ref_map.get("first_scene")

        # Copy found char_ref to local master if not already there
        if char_ref and char_ref.is_file() and not (chars_dir / f"{c_slug}_master.jpg").is_file():
            import shutil
            try:
                shutil.copy(char_ref, chars_dir / f"{c_slug}_master.jpg")
            except Exception:
                pass

        # Save metadata JSON
        meta_file = chars_dir / f"{c_slug}_turnaround.json"
        meta_file.write_text(json.dumps(turnaround_meta, indent=2, ensure_ascii=False), encoding="utf-8")

        # Render visual model sheet
        if render_images:
            render_character_turnaround_sheet(
                turnaround_meta,
                img_target,
                reference_image=char_ref,
                series_name=series_name,
                episode_num=ep_num
            )

        char_records.append(turnaround_meta)
        print(f"  👤 [CHARACTER DNA] Đã tạo Model Sheet 4 góc quay cho: '{char_name}' -> {img_target.name}", flush=True)

    # 2. Process Master Locations (Sequence Blocks)
    scenes = plan_data.get("scenes") or []
    locations_seen = set()
    location_records = []

    for sc in scenes:
        setting = str(sc.get("setting") or sc.get("visual_setup") or "").strip()
        if setting and setting not in locations_seen and len(setting) > 5:
            locations_seen.add(setting)
            l_slug = slugify_name(setting[:30])
            loc_meta = {
                "location_name": setting,
                "slug": l_slug,
                "wide_establishing_prompt": f"Cinematic 16:9 wide master establishing shot of {setting}, architectural depth, atmospheric lighting, spatial composition, photorealistic 8k.",
                "reverse_angle_prompt": f"Cinematic 16:9 reverse angle 180-degree shot of {setting}, interior background for over-the-shoulder cuts, consistent spatial geometry.",
                "lighting_palette": "Cinematic volumetric lighting, balanced practical lights, deep lifted shadow pedestal."
            }
            loc_file = locs_dir / f"{l_slug}_plate.json"
            loc_file.write_text(json.dumps(loc_meta, indent=2, ensure_ascii=False), encoding="utf-8")
            location_records.append(loc_meta)
            print(f"  🏛️ [LOCATION PLATE] Đã khóa bối cảnh không gian: '{setting[:50]}...'", flush=True)
            if len(location_records) >= 8:
                break

    # 3. Process Hero Props
    prop_records = []
    props_seen = set()
    for sc in scenes:
        start_state = str(sc.get("start_state") or "")
        end_state = str(sc.get("end_state") or "")
        combined_props = f"{start_state} {end_state} {sc.get('summary', '')}"
        found_props = re.findall(r"\b(letter|key|gun|phone|document|photo|dossier|knife|sword|medallion|ring|scroll|whisky glass|suitcase|briefcase|tập tài liệu|chìa khóa|bức thư|khẩu súng|vali|tượng cẩm thạch|toga)\b", combined_props, re.IGNORECASE)
        for p in found_props:
            p_clean = p.lower().strip()
            if p_clean not in props_seen:
                props_seen.add(p_clean)
                p_slug = slugify_name(p_clean)
                prop_meta = {
                    "prop_name": p_clean,
                    "slug": p_slug,
                    "studio_turnaround_prompt": f"Hero story prop model sheet, 3 distinct studio angles of {p_clean} on neutral gray pedestal with human hand scale reference, macro details, pristine focus, 8k.",
                    "continuity_rule": f"Keep {p_clean} appearance, wear and condition identical across all scenes where it appears."
                }
                prop_file = props_dir / f"{p_slug}_sheet.json"
                prop_file.write_text(json.dumps(prop_meta, indent=2, ensure_ascii=False), encoding="utf-8")
                prop_records.append(prop_meta)
                print(f"  🗝️ [HERO PROP] Đã khóa thông số đạo cụ then chốt: '{p_clean}'", flush=True)
                if len(prop_records) >= 6:
                    break

    # 4. Write Master Markdown Specification
    readme_md = asset_root / "MASTER_ASSET_MANIFEST.md"
    readme_lines = [
        f"# HỒ SƠ TÀI SẢN TIỀN KỲ ĐIỆN ẢNH (MASTER ASSET PACK)",
        f"* **Series:** {series_name}",
        f"* **Tập:** {ep_num} - {plan_data.get('title', '')}",
        f"* **Thể loại:** {genre} | **Phong cách thị giác:** {visual_style}",
        f"* **Thời gian tạo:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 1. DÀN NHÂN VẬT & BẢN VẼ XOAY 4 GÓC (TURNAROUND SHEETS)",
    ]
    for cr in char_records:
        readme_lines.append(f"### 🎭 {cr['character_name']} ({cr['gender']}, vai: {cr['role']})")
        readme_lines.append(f"* **Ảnh Model Sheet:** `{cr.get('image_path')}`")
        readme_lines.append(f"* **DNA ngoại hình:** {cr['appearance_dna']}")
        readme_lines.append(f"* **Trang phục bất biến:** {cr['attire']}")
        readme_lines.append(f"* **Quy tắc chống lỗi (Anti-Drift):** {cr['negative_rules']}")
        readme_lines.append(f"* **Định dạng 4 góc quay:** Chính diện (0°), Nghiêng 3/4 trái (45°), Nghiêng 3/4 phải (315°), Sau lưng (180°)")
        readme_lines.append("")

    readme_lines.append("## 2. BỐI CẢNH MẪU (MASTER LOCATION PLATES)")
    for lr in location_records:
        readme_lines.append(f"* **🏛️ {lr['location_name']}:** {lr['wide_establishing_prompt'][:120]}...")

    readme_lines.append("")
    readme_lines.append("## 3. ĐẠO CỤ THEN CHỐT (KEY STORY PROPS)")
    for pr in prop_records:
        readme_lines.append(f"* **🗝️ {pr['prop_name']}:** {pr['continuity_rule']}")

    readme_md.write_text("\n".join(readme_lines), encoding="utf-8")

    # 5. Generate Standalone HTML Asset Preview
    html_file = asset_root / "asset_pack_preview.html"
    _generate_html_asset_preview(
        series_name=series_name,
        ep_num=ep_num,
        genre=genre,
        visual_style=visual_style,
        characters=char_records,
        locations=location_records,
        props=prop_records,
        output_file=html_file
    )

    print(f"\n[ASSET_PACK] Đã xuất bản hồ sơ tài sản tổng hợp: {readme_md.name} & {html_file.name}\n", flush=True)

    return {
        "ok": True,
        "asset_root": str(asset_root),
        "characters_count": len(char_records),
        "locations_count": len(location_records),
        "props_count": len(prop_records),
        "characters": char_records,
        "locations": location_records,
        "props": prop_records,
        "manifest_path": str(readme_md),
        "preview_html": str(html_file)
    }


def _generate_html_asset_preview(
    series_name: str,
    ep_num: int,
    genre: str,
    visual_style: str,
    characters: List[Dict[str, Any]],
    locations: List[Dict[str, Any]],
    props: List[Dict[str, Any]],
    output_file: Path
) -> None:
    """Creates a modern dark-mode HTML visual showcase of the entire asset pack."""
    char_cards = []
    for c in characters:
        img_name = Path(c.get("image_path", "")).name
        card = f"""
        <div class="card">
            <div class="card-header">
                <span class="role-badge">{c.get('role', 'Character').upper()}</span>
                <h3>{c.get('character_name')}</h3>
            </div>
            <div class="img-wrapper">
                <img src="./characters/{img_name}" alt="{c.get('character_name')}" onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22400%22 height=%22225%22><rect width=%22100%%22 height=%22100%%22 fill=%22%23222%22/><text x=%2250%%22 y=%2250%%22 fill=%22%23666%22 font-family=%22sans-serif%22 font-size=%2216%22 text-anchor=%22middle%22>Model Sheet Pending</text></svg>'">
            </div>
            <div class="card-body">
                <p><strong>🧬 DNA Ngoại hình:</strong> {c.get('appearance_dna')}</p>
                <p><strong>👔 Trang phục:</strong> {c.get('attire')}</p>
                <p class="negative"><strong>🚫 Chống biến đổi:</strong> {c.get('negative_rules')}</p>
            </div>
        </div>
        """
        char_cards.append(card)

    loc_items = "".join([f"<li><strong>🏛️ {l['location_name']}:</strong> {l['wide_establishing_prompt'][:110]}...</li>" for l in locations]) or "<li>Chưa có bối cảnh riêng</li>"
    prop_items = "".join([f"<li><strong>🗝️ {p['prop_name']}:</strong> {p['continuity_rule']}</li>" for p in props]) or "<li>Chưa có đạo cụ riêng</li>"

    html_content = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pre-Production Master Asset Pack - {series_name} Ep {ep_num}</title>
    <style>
        body {{
            background: #0f1117;
            color: #e2e8f0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            margin: 0;
            padding: 30px;
        }}
        .header {{
            border-bottom: 2px solid #38bdf8;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        h1 {{ margin: 0 0 10px 0; color: #f8fafc; font-size: 26px; }}
        .meta-bar {{ color: #94a3b8; font-size: 14px; display: flex; gap: 20px; }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(420px, 1fr));
            gap: 25px;
            margin-bottom: 40px;
        }}
        .card {{
            background: #1e222d;
            border: 1px solid #334155;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0,0,0,0.4);
        }}
        .card-header {{
            background: #181b24;
            padding: 12px 18px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid #334155;
        }}
        .card-header h3 {{ margin: 0; font-size: 18px; color: #38bdf8; }}
        .role-badge {{
            background: #0284c7;
            color: #fff;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
        }}
        .img-wrapper {{ width: 100%; aspect-ratio: 16/9; background: #0b0d13; display: flex; align-items: center; justify-content: center; }}
        .img-wrapper img {{ width: 100%; height: 100%; object-fit: contain; }}
        .card-body {{ padding: 16px; font-size: 13px; line-height: 1.6; }}
        .card-body p {{ margin: 0 0 8px 0; }}
        .card-body p.negative {{ color: #fda4af; }}
        .section-title {{ font-size: 20px; margin: 30px 0 15px 0; color: #f1f5f9; border-left: 4px solid #38bdf8; padding-left: 12px; }}
        .spec-list {{ background: #1e222d; border: 1px solid #334155; border-radius: 8px; padding: 20px 30px; }}
        .spec-list li {{ margin-bottom: 10px; font-size: 14px; line-height: 1.5; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎬 HỒ SƠ TÀI SẢN TIỀN KỲ ĐIỆN ẢNH (MASTER ASSET PACK)</h1>
        <div class="meta-bar">
            <span><strong>Series:</strong> {series_name}</span>
            <span><strong>Tập:</strong> {ep_num}</span>
            <span><strong>Thể loại:</strong> {genre}</span>
            <span><strong>Phong cách:</strong> {visual_style}</span>
            <span><strong>Định dạng:</strong> 16:9 Widescreen</span>
        </div>
    </div>

    <div class="section-title">👤 BẢN VẼ XOAY 4 GÓC CỦA NHÂN VẬT (CHARACTER MODEL SHEETS)</div>
    <div class="grid">
        {"".join(char_cards)}
    </div>

    <div class="section-title">🏛️ BỐI CẢNH MẪU (MASTER LOCATION PLATES)</div>
    <ul class="spec-list">
        {loc_items}
    </ul>

    <div class="section-title">🗝️ ĐẠO CỤ THEN CHỐT (KEY STORY PROPS)</div>
    <ul class="spec-list">
        {prop_items}
    </ul>
</body>
</html>
"""
    output_file.write_text(html_content, encoding="utf-8")


def get_scene_character_anchors(episode_dir: Path, characters_present: List[str]) -> List[Dict[str, Any]]:
    """
    Retrieves the turnaround sheet specifications for characters present in a specific scene.
    Enables video providers to anchor facial geometry and wardrobe against pre-production sheets.
    """
    chars_dir = Path(episode_dir) / "00_ASSET_PACK" / "characters"
    if not chars_dir.is_dir():
        return []

    anchors = []
    for name in characters_present:
        slug = slugify_name(name)
        meta_p = chars_dir / f"{slug}_turnaround.json"
        img_master_jpg = chars_dir / f"{slug}_master.jpg"
        img_master_png = chars_dir / f"{slug}_master.png"
        img_turn_jpg = chars_dir / f"{slug}_turnaround.jpg"
        img_turn_png = chars_dir / f"{slug}_turnaround.png"
        # Prioritize single photorealistic master portrait over 4-view blueprint
        img_file = None
        for cand in [img_master_jpg, img_master_png, img_turn_jpg, img_turn_png]:
            if cand.is_file():
                img_file = cand
                break
        if meta_p.is_file():
            try:
                item = json.loads(meta_p.read_text(encoding="utf-8"))
                if img_file:
                    item["image_path"] = str(img_file)
                anchors.append(item)
            except Exception:
                pass
        elif img_file:
            anchors.append({
                "character_name": name,
                "slug": slug,
                "image_path": str(img_file)
            })
    return anchors


def get_primary_character_anchor(episode_dir: Path, characters_present: List[str], primary_name: str | None = None) -> Optional[Path]:
    """Returns the image Path of the primary character's turnaround sheet for anchor-based rendering."""
    anchors = get_scene_character_anchors(episode_dir, characters_present)
    if not anchors:
        return None
    if primary_name:
        for a in anchors:
            if a.get("character_name", "").lower() == str(primary_name).lower() and a.get("image_path"):
                p = Path(a["image_path"])
                if p.is_file():
                    return p
    # Return first available anchor image
    for a in anchors:
        if a.get("image_path"):
            p = Path(a["image_path"])
            if p.is_file():
                return p
    return None
