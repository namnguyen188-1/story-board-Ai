"""Standalone 3D Viral CJK Typography Renderer (Japanese & Korean Thumbnails)."""
from __future__ import annotations

import math
from pathlib import Path
from typing import List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .cjk_text_utils import detect_cjk_language, resolve_cjk_font_path, split_cjk_hook_lines


def _measure_cjk_line(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    tracking: int,
) -> Tuple[int, int]:
    if not text:
        return 0, 0
    total_w = 0
    min_y = 9999
    max_y = -9999
    for idx, ch in enumerate(text):
        bb = draw.textbbox((0, 0), ch, font=font)
        cw = bb[2] - bb[0]
        total_w += cw + (tracking if idx < len(text) - 1 else 0)
        min_y = min(min_y, bb[1])
        max_y = max(max_y, bb[3])
    return max(1, total_w), max(1, max_y - min_y)


def _draw_cjk_line(
    draw: ImageDraw.ImageDraw,
    pos: Tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: Tuple[int, int, int, int],
    stroke_w: int = 0,
    stroke_fill: Tuple[int, int, int, int] = (0, 0, 0, 255),
    tracking: int = 2,
) -> None:
    cur_x, y = pos
    # Compute consistent baseline offset so all CJK glyphs align cleanly horizontally
    full_bb = draw.textbbox((0, 0), text, font=font)
    base_top = full_bb[1]
    for ch in text:
        bb = draw.textbbox((0, 0), ch, font=font)
        cw = max(1, bb[2] - bb[0])
        draw_x = cur_x - bb[0]
        draw_y = y - base_top
        draw.text(
            (draw_x, draw_y),
            ch,
            font=font,
            fill=fill,
            stroke_width=stroke_w,
            stroke_fill=stroke_fill if stroke_w > 0 else None,
        )
        cur_x += cw + tracking


def render_cjk_3d_text_overlay(
    canvas_size: Tuple[int, int],
    lines: List[str],
    text_box: Tuple[int, int, int, int],
    language: Optional[str] = None,
) -> Image.Image:
    """Renders tri-chromatic 3D typography (Gold + Crimson Glow Arc + Titanium White) for JP/KR hooks."""
    W, H = canvas_size
    bx1, by1, bx2, by2 = text_box
    box_w = max(80, bx2 - bx1)
    box_h = max(80, by2 - by1)

    cleaned_lines = [str(ln or "").strip() for ln in lines if str(ln or "").strip()]
    if not cleaned_lines:
        return Image.new("RGBA", (W, H), (0, 0, 0, 0))

    joined = " ".join(cleaned_lines)
    font_path = resolve_cjk_font_path(joined, language=language)
    cjk_lang = detect_cjk_language(joined, language)

    # Tri-chromatic High-CTR formula matching create-youtube-thumbnail
    if len(cleaned_lines) <= 1:
        palette = [((255, 229, 0), (245, 165, 0))]
    elif len(cleaned_lines) == 2:
        palette = [
            ((255, 229, 0), (245, 165, 0)),     # Imperial Gold top line
            ((255, 255, 255), (235, 240, 250)), # Titanium White bottom line
        ]
    else:
        palette = [
            ((255, 229, 0), (245, 165, 0)),
            ((255, 255, 255), (235, 240, 250)),
            ((255, 229, 0), (245, 165, 0)),
        ]

    dummy = Image.new("RGBA", (10, 10))
    d_test = ImageDraw.Draw(dummy)
    max_fs = 260 if H > 1200 else 220
    min_fs = 64

    line_data = []
    for idx, line in enumerate(cleaned_lines):
        fs = max_fs
        font = ImageFont.truetype(font_path, fs)
        # CJK characters look tighter and cleaner with modest tracking
        tracking = max(1, int(fs * (0.018 if cjk_lang in ("Japanese", "Korean") else 0.03)))
        lw, lh = _measure_cjk_line(d_test, line, font, tracking)
        target_lw = box_w * 0.94
        while lw > target_lw and fs > min_fs:
            fs -= 2
            font = ImageFont.truetype(font_path, fs)
            tracking = max(1, int(fs * (0.018 if cjk_lang in ("Japanese", "Korean") else 0.03)))
            lw, lh = _measure_cjk_line(d_test, line, font, tracking)

        line_data.append({
            "text": line,
            "font": font,
            "fs": fs,
            "w": lw,
            "h": lh,
            "tracking": tracking,
            "colors": palette[min(idx, len(palette) - 1)],
        })

    tight_gap = 18 if H > 1200 else 14
    arc_gap = 28 if len(line_data) >= 2 else 0
    total_h = sum(d["h"] for d in line_data) + tight_gap * max(0, len(line_data) - 1) + arc_gap

    if total_h > box_h:
        scale = box_h / float(total_h)
        for d in line_data:
            d["fs"] = max(min_fs, int(d["fs"] * scale))
            d["font"] = ImageFont.truetype(font_path, d["fs"])
            d["tracking"] = max(1, int(d["fs"] * 0.018))
            lw, lh = _measure_cjk_line(d_test, d["text"], d["font"], d["tracking"])
            d["w"] = lw
            d["h"] = lh
        total_h = sum(d["h"] for d in line_data) + tight_gap * max(0, len(line_data) - 1) + arc_gap

    start_y = by1 + max(0, (box_h - total_h) // 2)
    text_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shadow_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    accent_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    d_txt = ImageDraw.Draw(text_layer)
    d_shd = ImageDraw.Draw(shadow_layer)
    d_acc = ImageDraw.Draw(accent_layer)

    cur_y = start_y
    arc_bbox = None
    arc_after_idx = 0 if len(line_data) == 2 else (1 if len(line_data) >= 3 else -1)

    for idx, d in enumerate(line_data):
        txt = d["text"]
        fnt = d["font"]
        fs = d["fs"]
        trk = d["tracking"]
        cur_x = bx1 + max(0, (box_w - d["w"]) // 2)

        # Extruded 3D dark block shadow
        ext_depth = max(5, min(11, int(fs * 0.06)))
        shd_stroke = max(4, min(9, int(fs * 0.045)))
        for depth in range(ext_depth, 0, -2):
            _draw_cjk_line(
                d_shd, (cur_x + depth // 2, cur_y + depth), txt, fnt,
                fill=(0, 0, 0, 210), stroke_w=shd_stroke, stroke_fill=(0, 0, 0, 230),
                tracking=trk,
            )

        # Sharp outer dark contour separating text from bright plates
        crisp_stroke = max(2, min(5, int(fs * 0.028)))
        _draw_cjk_line(
            d_txt, (cur_x, cur_y), txt, fnt,
            fill=(0, 0, 0, 255), stroke_w=crisp_stroke, stroke_fill=(0, 0, 0, 255),
            tracking=trk,
        )

        # Gradient glyph mask
        mask = Image.new("L", (W, H), 0)
        d_m = ImageDraw.Draw(mask)
        _draw_cjk_line(d_m, (cur_x, cur_y), txt, fnt, fill=255, stroke_w=0, tracking=trk)
        m_bbox = mask.getbbox()
        if m_bbox:
            y1, y2 = m_bbox[1], m_bbox[3]
            span_y = max(1, y2 - y1)
            top_c, bot_c = d["colors"]
            grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            d_g = ImageDraw.Draw(grad)
            for y_i in range(y1, y2 + 1):
                t = (y_i - y1) / float(span_y)
                t = t * t * (3 - 2 * t)
                col = (
                    int(top_c[0] * (1 - t) + bot_c[0] * t),
                    int(top_c[1] * (1 - t) + bot_c[1] * t),
                    int(top_c[2] * (1 - t) + bot_c[2] * t),
                    255,
                )
                d_g.line([(m_bbox[0] - 4, y_i), (m_bbox[2] + 4, y_i)], fill=col)
            text_layer.paste(grad, (0, 0), mask=mask)

        if idx == arc_after_idx:
            arc_base_y = m_bbox[3] if m_bbox else (cur_y + d["h"])
            arc_y = arc_base_y + 12
            arc_w = int(d["w"] * 0.92)
            ax1 = cur_x + int(d["w"] * 0.04)
            arc_bbox = (ax1, arc_y, ax1 + arc_w)
            cur_y += d["h"] + tight_gap + arc_gap
        else:
            cur_y += d["h"] + tight_gap

    if arc_bbox:
        ax1, ay, ax2 = arc_bbox
        mid_x = (ax1 + ax2) / 2.0
        mid_y = ay - 5
        top_pts, bot_pts = [], []
        max_th = 9.0 if H >= 720 else 6.0
        steps = 48
        for i in range(steps + 1):
            t = i / float(steps)
            bx = (1 - t) ** 2 * ax1 + 2 * (1 - t) * t * mid_x + t ** 2 * ax2
            by = (1 - t) ** 2 * ay + 2 * (1 - t) * t * mid_y + t ** 2 * ay
            th = max_th * math.sin(math.pi * t)
            top_pts.append((bx, by - th / 2.0))
            bot_pts.append((bx, by + th / 2.0))
        poly = top_pts + list(reversed(bot_pts))
        d_shd.polygon([(x, y + 4) for x, y in poly], fill=(0, 0, 0, 230))
        d_acc.polygon(poly, fill=(220, 38, 38, 255))

    blurred_shadow = shadow_layer.filter(ImageFilter.GaussianBlur(radius=3.5))
    out = Image.alpha_composite(blurred_shadow, accent_layer)
    out = Image.alpha_composite(out, text_layer)
    return out


def compose_cjk_thumbnail(
    base_image_path: Path | str,
    output_path: Path | str,
    hook_text: str,
    language: Optional[str] = None,
    aspect_ratio: str = "16:9",
) -> str:
    """Composes a clean YouTube thumbnail (1280x720 or 1080x1920) with 3D JP/KR typography."""
    is_short = "9:16" in str(aspect_ratio)
    W, H = (1080, 1920) if is_short else (1280, 720)
    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(base_image_path) as src:
        base = src.convert("RGBA")
        # Crop-fit to target dimensions without distorting subject proportions
        src_ratio = base.width / max(1, base.height)
        tgt_ratio = W / float(H)
        if src_ratio > tgt_ratio:
            new_w = int(round(base.height * tgt_ratio))
            left = (base.width - new_w) // 2
            base = base.crop((left, 0, left + new_w, base.height))
        elif src_ratio < tgt_ratio:
            new_h = int(round(base.width / tgt_ratio))
            top = max(0, (base.height - new_h) // 4)
            base = base.crop((0, top, base.width, min(base.height, top + new_h)))
        canvas = base.resize((W, H), Image.Resampling.LANCZOS)

    # Dark vignette behind typography zone for mobile readability
    vignette = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d_v = ImageDraw.Draw(vignette)
    if is_short:
        # Bottom-lower readability band above YouTube Shorts safe zone (leave bottom 240px clear)
        for y in range(int(H * 0.48), int(H * 0.88)):
            alpha = int(175 * ((y - H * 0.48) / (H * 0.40)))
            d_v.line([(0, y), (W, y)], fill=(8, 10, 16, min(190, alpha)))
        text_box = (70, int(H * 0.52), W - 70, int(H * 0.85))
    else:
        # Classic 50/50 left readability vignette for horizontal 16:9 thumbnails
        for x in range(0, int(W * 0.62)):
            ratio = 1.0 - (x / float(W * 0.62))
            alpha = int(205 * (ratio ** 1.15))
            d_v.line([(x, 0), (x, H)], fill=(8, 10, 16, alpha))
        text_box = (45, 55, int(W * 0.52), H - 55)

    canvas = Image.alpha_composite(canvas, vignette)
    lines = split_cjk_hook_lines(hook_text, max_lines=3)
    overlay = render_cjk_3d_text_overlay((W, H), lines, text_box, language=language)
    final_rgba = Image.alpha_composite(canvas, overlay)
    final_rgba.convert("RGB").save(out_p, format="JPEG", quality=94, optimize=True)
    return str(out_p)
