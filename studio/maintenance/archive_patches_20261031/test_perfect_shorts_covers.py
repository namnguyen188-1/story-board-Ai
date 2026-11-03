import sys
sys.path.insert(0, 'studio')
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image, ImageEnhance, ImageFilter, ImageDraw, ImageFont
import numpy as np
from pathlib import Path
import seo_packager

# Load base image
base_path = Path("studio/productions/stoi/episode_001/thumbnail_fierce_base.jpg")
im_src = Image.open(base_path).convert("RGB")
sw, sh = im_src.size # 1536 x 864

# Target vertical dimensions: 1080 x 1920
tw, th = 1080, 1920

# Detect face
faces = seo_packager.detect_faces_in_image(im_src)
if faces:
    fx, fy, fw, fh = faces[0]
    fcx = fx + fw // 2
    fcy = fy + fh // 2
else:
    fcx, fcy = 646, 303

print(f"Face center in source: ({fcx}, {fcy})")

# Extract the full statue:
# Statue extends around x: fcx - 420 to fcx + 420 (width 840)
x1 = max(0, fcx - 430)
x2 = min(sw, fcx + 430)
statue_crop = im_src.crop((x1, 0, x2, sh))
sc_w, sc_h = statue_crop.size

# Scale statue so width matches 1080
scale = tw / float(sc_w)
new_w = tw
new_h = int(sc_h * scale)
statue_scaled = statue_crop.resize((new_w, new_h), Image.Resampling.LANCZOS)

# Create 1080x1920 canvas
canvas = Image.new("RGB", (tw, th), (12, 16, 24))

# Create atmospheric sky extension at top
# Sample top 100px of statue_crop
top_slice = statue_crop.crop((0, 0, sc_w, 180)).resize((tw, 750), Image.Resampling.LANCZOS)
top_slice = top_slice.filter(ImageFilter.GaussianBlur(15))
canvas.paste(top_slice, (0, 0))

# Place statue anchored from bottom or lower-middle:
# Statue height is new_h (~1100px). Let's anchor it at y = th - new_h = 820
statue_y = max(450, th - new_h)

# Feather top edge of statue onto the sky
statue_rgba = statue_scaled.convert("RGBA")
st_arr = np.array(statue_rgba, dtype=np.float32)
feather_h = 160
for r in range(feather_h):
    st_arr[r, :, 3] = 255.0 * (r / float(feather_h))
statue_blended = Image.fromarray(np.clip(st_arr, 0, 255).astype(np.uint8))

canvas.paste(statue_blended, (0, statue_y), statue_blended)

# Overall contrast & sharpness boost
canvas = ImageEnhance.Contrast(canvas).enhance(1.22)
canvas = ImageEnhance.Sharpness(canvas).enhance(1.35)

# Calculate where the face ended up on the 1080x1920 canvas
face_on_canvas_y1 = statue_y + int(fy * scale)
face_on_canvas_y2 = statue_y + int((fy + fh) * scale)
print(f"Face on 1080x1920 canvas is at Y: {face_on_canvas_y1} to {face_on_canvas_y2}")

# ========================================================
# LAYOUT A: Text in UPPER SKY (above face: Y in 180..420)
# ========================================================
im_layout_a = canvas.copy()
draw_a = ImageDraw.Draw(im_layout_a, "RGBA")

font_path = "C:/Windows/Fonts/impact.ttf"
lines = ["DEJA DE REGALAR", "TU VIDA"]

f_size = 96
font = ImageFont.truetype(font_path, f_size)
for l in lines:
    bb = draw_a.textbbox((0, 0), l, font=font)
    while (bb[2] - bb[0]) > (tw - 100) and f_size > 48:
        f_size -= 4
        font = ImageFont.truetype(font_path, f_size)
        bb = draw_a.textbbox((0, 0), l, font=font)

line_h = int(f_size * 1.15)
start_y_a = 180

# Dark gradient behind text in upper sky
overlay_a = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
ov_draw_a = ImageDraw.Draw(overlay_a)
for y in range(120, start_y_a + len(lines)*line_h + 80):
    dist = abs(y - (start_y_a + line_h)) / 180.0
    alpha = int(140 * max(0.0, 1.0 - dist*dist))
    ov_draw_a.line([(0, y), (tw, y)], fill=(0, 0, 0, alpha))
im_layout_a = Image.alpha_composite(im_layout_a.convert("RGBA"), overlay_a).convert("RGB")
draw_a = ImageDraw.Draw(im_layout_a, "RGBA")

for idx, line in enumerate(lines):
    bb = draw_a.textbbox((0, 0), line, font=font)
    lw = bb[2] - bb[0]
    lx = (tw - lw) // 2
    ly = start_y_a + idx * line_h
    fill_c = (255, 215, 0, 255) if idx == 0 else (255, 255, 255, 255)
    # Multi-pass shadow
    for s_idx in range(6, 0, -1):
        s_off = s_idx * 2
        draw_a.text((lx + s_off, ly + s_off), line, font=font, fill=(0, 0, 0, 230))
    # Thick black stroke
    for dx in range(-8, 9):
        for dy in range(-8, 9):
            if dx*dx + dy*dy <= 64:
                draw_a.text((lx + dx, ly + dy), line, font=font, fill=(0, 0, 0, 255))
    draw_a.text((lx, ly), line, font=font, fill=fill_c)

out_a = Path("studio/productions/stoi/episode_001/test_shorts_layout_a_sky.jpg")
im_layout_a.save(out_a, "JPEG", quality=95)
print(f"Saved Layout A (Text in Sky): {out_a}")

# ========================================================
# LAYOUT B: Text on CHEST (below face: Y in 1250..1550)
# ========================================================
im_layout_b = canvas.copy()
start_y_b = max(face_on_canvas_y2 + 80, 1220)

overlay_b = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
ov_draw_b = ImageDraw.Draw(overlay_b)
for y in range(start_y_b - 60, start_y_b + len(lines)*line_h + 80):
    dist = abs(y - (start_y_b + line_h)) / 180.0
    alpha = int(160 * max(0.0, 1.0 - dist*dist))
    ov_draw_b.line([(0, y), (tw, y)], fill=(0, 0, 0, alpha))
im_layout_b = Image.alpha_composite(im_layout_b.convert("RGBA"), overlay_b).convert("RGB")
draw_b = ImageDraw.Draw(im_layout_b, "RGBA")

for idx, line in enumerate(lines):
    bb = draw_b.textbbox((0, 0), line, font=font)
    lw = bb[2] - bb[0]
    lx = (tw - lw) // 2
    ly = start_y_b + idx * line_h
    fill_c = (255, 215, 0, 255) if idx == 0 else (255, 255, 255, 255)
    for s_idx in range(6, 0, -1):
        s_off = s_idx * 2
        draw_b.text((lx + s_off, ly + s_off), line, font=font, fill=(0, 0, 0, 230))
    for dx in range(-8, 9):
        for dy in range(-8, 9):
            if dx*dx + dy*dy <= 64:
                draw_b.text((lx + dx, ly + dy), line, font=font, fill=(0, 0, 0, 255))
    draw_b.text((lx, ly), line, font=font, fill=fill_c)

out_b = Path("studio/productions/stoi/episode_001/test_shorts_layout_b_chest.jpg")
im_layout_b.save(out_b, "JPEG", quality=95)
print(f"Saved Layout B (Text on Chest): {out_b}")
