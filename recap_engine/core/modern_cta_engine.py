"""
Modern CTA Overlay Engine for Movie Recap Studio Pro.
Generates pixel-perfect transparent capsule pill Call-to-Action badges
(Like, Subscribe, Bell) matching the cinematic recap drama standard:
- Pink/Red to Warm Golden Orange gradient pill
- Twin golden bells vector icons
- Crisp white typography with subtle drop shadow & soft glowing border
- 100% transparent alpha channel (RGBA) - Zero green screen fringing, Zero black background box.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont


def draw_golden_bell_vector(draw: ImageDraw.ImageDraw, cx: int, cy: int, size: int = 24):
    """Draws a beautiful vector golden bell with metallic shading."""
    color = (255, 215, 0, 255)       # Gold
    outline = (210, 150, 0, 255)     # Deep gold outline
    clapper = (255, 235, 120, 255)   # Light gold clapper
    
    # Hanger loop
    draw.ellipse([(cx - 3, cy - size // 2), (cx + 3, cy - size // 2 + 5)], fill=color, outline=outline)
    
    # Bell dome (trapezoid-like polygon)
    poly = [
        (cx - 5, cy - size // 2 + 4),
        (cx + 5, cy - size // 2 + 4),
        (cx + size // 2, cy + size // 2 - 4),
        (cx - size // 2, cy + size // 2 - 4)
    ]
    draw.polygon(poly, fill=color, outline=outline)
    
    # Bell rim (rounded rectangle)
    draw.rounded_rectangle(
        [(cx - size // 2 - 3, cy + size // 2 - 5), (cx + size // 2 + 3, cy + size // 2 - 1)],
        radius=2,
        fill=color,
        outline=outline
    )
    
    # Clapper
    draw.ellipse([(cx - 3, cy + size // 2 - 2), (cx + 3, cy + size // 2 + 4)], fill=clapper, outline=outline)
    
    # Sound sparkles / wave lines
    draw.arc([(cx - size // 2 - 8, cy - 4), (cx - size // 2 - 2, cy + 8)], 120, 240, fill=color, width=2)
    draw.arc([(cx + size // 2 + 2, cy - 4), (cx + size // 2 + 8, cy + 8)], 300, 60, fill=color, width=2)


def generate_modern_pill_badge(
    output_path: Path | str,
    text: str = "Đăng ký & Like để không bỏ lỡ phim hay!",
    target_width: int = 680,
    target_height: int = 76,
    language: str = "vi"
) -> Path:
    """
    Generates a gorgeous gradient pill badge matching the user's reference:
    - Gradient from vivid rose-red/pink (#ea2360) to warm amber-orange (#ffa500)
    - 2 Golden Bells on the left
    - Bold white text with subtle shadow
    - Delicate semi-translucent glowing border
    - 100% clean transparent background (RGBA)
    """
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    # If text is default or empty, localize appropriately
    if not text or text.strip() in ["", "default"]:
        if language == "zh":
            text = "点击订阅与点赞，精彩不迷路！"
        elif language == "en":
            text = "Subscribe & Like to never miss great movies!"
        else:
            text = "Đăng ký & Like để không bỏ lỡ phim hay!"
            
    # Clean text
    clean_text = text.replace("🔔", "").strip()

    width = target_width
    height = target_height
    radius = height // 2

    # 1. Base transparent image
    base = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    
    # 2. Gradient layer
    grad = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    for x in range(width):
        t = x / max(1, width - 1)
        if t < 0.5:
            # Interpolate #ea2360 (234, 35, 96) to #ff5e36 (255, 94, 54)
            u = t * 2.0
            r = int(234 * (1 - u) + 255 * u)
            g = int(35 * (1 - u) + 94 * u)
            b = int(96 * (1 - u) + 54 * u)
        else:
            # Interpolate #ff5e36 to #ffa500 (255, 165, 0)
            u = (t - 0.5) * 2.0
            r = int(255 * (1 - u) + 255 * u)
            g = int(94 * (1 - u) + 165 * u)
            b = int(54 * (1 - u) + 0 * u)
            
        # 92% opacity so background movie subtly bleeds through with glass effect
        for y in range(height):
            grad.putpixel((x, y), (r, g, b, 235))
            
    # 3. Pill mask with smooth antialiased corners
    mask = Image.new("L", (width, height), 0)
    m_draw = ImageDraw.Draw(mask)
    m_draw.rounded_rectangle([(0, 0), (width - 1, height - 1)], radius=radius, fill=255)
    
    pill = Image.composite(grad, base, mask)
    p_draw = ImageDraw.Draw(pill)
    
    # 4. Glowing translucent outer border
    p_draw.rounded_rectangle(
        [(1, 1), (width - 2, height - 2)],
        radius=radius,
        outline=(255, 235, 245, 190),
        width=2
    )
    # Subtle inner highlight line at top
    p_draw.arc([(radius // 2, 2), (width - radius // 2, height - 2)], 200, 340, fill=(255, 255, 255, 90), width=1)
    
    # 5. Twin Golden Bells on the left
    bell1_cx = int(radius * 0.95)
    bell2_cx = int(radius * 1.65)
    draw_golden_bell_vector(p_draw, bell1_cx, height // 2, size=int(height * 0.46))
    draw_golden_bell_vector(p_draw, bell2_cx, height // 2 - 1, size=int(height * 0.38))
    
    # 6. Typography
    font_size = int(height * 0.38)
    font = None
    font_candidates = [
        "C:/Windows/Fonts/msyhbd.ttc",   # Microsoft YaHei Bold (great for CJK & Latin)
        "C:/Windows/Fonts/segoeuib.ttf",  # Segoe UI Bold
        "C:/Windows/Fonts/arialbd.ttf",   # Arial Bold
        "C:/Windows/Fonts/tahoma.ttf",
    ]
    for fp in font_candidates:
        if os.path.exists(fp):
            try:
                font = ImageFont.truetype(fp, font_size)
                break
            except Exception:
                pass
    if not font:
        font = ImageFont.load_default()
        
    text_start_x = bell2_cx + int(radius * 0.65)
    text_y = height // 2 - font_size // 2 - 2
    
    # Soft drop shadow for maximum legibility over bright movie scenes
    p_draw.text((text_start_x + 1, text_y + 2), clean_text, font=font, fill=(60, 10, 20, 180))
    p_draw.text((text_start_x, text_y), clean_text, font=font, fill=(255, 255, 255, 255))
    
    pill.save(str(out_path), "PNG")
    return out_path
