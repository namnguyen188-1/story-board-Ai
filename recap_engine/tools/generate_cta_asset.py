"""
High-Resolution Transparent Animated Social CTA Generator (Zero Black Box).
Pure Chromakey Green Screen (0x00FF00) - 100% Transparent Background.
Only renders the sleek YouTube buttons floating directly over the movie:
- LIKE: Independent oval pill [👍 THÍCH] -> [👍 ĐÃ THÍCH] (Neon Cyan)
- SUBSCRIBE: Classic YouTube Red Pill [ĐĂNG KÝ] -> [ĐÃ ĐĂNG KÝ ✓] (Slate Gray)
- BELL: Golden Bell [🔔] with dynamic ringing oscillation & sound waves
- Cursor: Smooth animated mouse pointer with click bounce & ripple
- ZERO BLACK BACKGROUND: Everything between and around buttons is 100% transparent!
"""
import math
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1280, 720
FPS = 30
TOTAL_FRAMES = 165  # 5.5 seconds

ffmpeg = "D:/MOVIE_RECAP_STUDIO/runtime/ffmpeg/ffmpeg.exe"
out_mp4 = Path("D:/MOVIE_RECAP_STUDIO/web/assets/cta_like_subscribe_bell_v9.mp4")
out_mp4.parent.mkdir(parents=True, exist_ok=True)

try:
    font_btn = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 25)
    font_sub = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 24)
except Exception:
    font_btn = ImageFont.load_default()
    font_sub = font_btn

cmd = [
    ffmpeg, "-y",
    "-f", "rawvideo",
    "-vcodec", "rawvideo",
    "-s", f"{W}x{H}",
    "-pix_fmt", "rgb24",
    "-r", str(FPS),
    "-i", "-",
    "-c:v", "libx264",
    "-preset", "veryfast",
    "-pix_fmt", "yuv420p",
    str(out_mp4)
]

proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Button layout parameters (Center aligned, NO black background box!)
base_y = (H - 70) // 2
like_w, like_h = 160, 64
sub_w, sub_h = 240, 64
bell_size = 64

gap = 18
total_w = like_w + gap + sub_w + gap + bell_size
start_x = (W - total_w) // 2

like_x = start_x
sub_x = like_x + like_w + gap
bell_x = sub_x + sub_w + gap

for f in range(TOTAL_FRAMES):
    t = f / FPS
    # Pure Green Screen for 100% clean chromakey removal
    im = Image.new("RGB", (W, H), (0, 255, 0))
    draw = ImageDraw.Draw(im)

    # 1. Slide In/Out Animation
    if t < 0.6:
        progress = t / 0.6
        cur_y = int(H - (H - base_y) * (1 - (1 - progress)**3))
    elif t > 4.7:
        progress = (t - 4.7) / 0.8
        cur_y = int(base_y + (H - base_y) * (progress**3))
    else:
        cur_y = base_y

    # ==========================================
    # SECTION 1: LIKE BUTTON (Individual Pill)
    # ==========================================
    is_liked = t >= 1.3
    like_bounce = 0
    if 1.3 <= t < 1.6:
        # Subtle scale bounce on click
        like_bounce = int(4 * math.sin((t - 1.3) * math.pi / 0.3))

    # Pill background: Dark sleek pill with subtle white border
    l_bg = (30, 36, 48) if not is_liked else (15, 23, 42)
    l_border = (80, 95, 120) if not is_liked else (56, 189, 248)
    draw.rounded_rectangle(
        [like_x - like_bounce, cur_y - like_bounce, like_x + like_w + like_bounce, cur_y + like_h + like_bounce],
        radius=32, fill=l_bg, outline=l_border, width=2
    )

    like_col = (56, 189, 248) if is_liked else (225, 235, 245)
    like_text = "THÍCH" if not is_liked else "ĐÃ THÍCH"

    # Thumb Up icon
    tx = like_x + 20
    ty = cur_y + 16
    draw.polygon([(tx, ty+14), (tx+8, ty+14), (tx+8, ty+30), (tx, ty+30)], fill=like_col)
    draw.polygon([(tx+11, ty+14), (tx+19, ty+2), (tx+27, ty+2), (tx+27, ty+10), (tx+34, ty+10), (tx+30, ty+30), (tx+11, ty+30)], fill=like_col)
    draw.text((like_x + 62, cur_y + 17), like_text, fill=like_col, font=font_btn)

    # ==========================================
    # SECTION 2: SUBSCRIBE BUTTON (YouTube Red Pill)
    # ==========================================
    is_subbed = t >= 2.5
    sub_bounce = 0
    if 2.5 <= t < 2.8:
        sub_bounce = int(4 * math.sin((t - 2.5) * math.pi / 0.3))

    if not is_subbed:
        s_bg = (225, 29, 72)  # YouTube Red
        s_border = (255, 75, 110)
        s_text = "ĐĂNG KÝ"
        s_fg = (255, 255, 255)
        tx_offset = 58
    else:
        s_bg = (30, 36, 48)  # Slate Gray
        s_border = (90, 105, 125)
        s_text = "ĐÃ ĐĂNG KÝ ✓"
        s_fg = (220, 230, 245)
        tx_offset = 38

    draw.rounded_rectangle(
        [sub_x - sub_bounce, cur_y - sub_bounce, sub_x + sub_w + sub_bounce, cur_y + sub_h + sub_bounce],
        radius=32, fill=s_bg, outline=s_border, width=2
    )
    draw.text((sub_x + tx_offset, cur_y + 17), s_text, fill=s_fg, font=font_sub)

    # ==========================================
    # SECTION 3: BELL BUTTON (Individual Circular Pill)
    # ==========================================
    is_belled = t >= 3.6
    b_bg = (30, 36, 48)
    b_border = (250, 204, 21) if is_belled else (80, 95, 120)
    draw.rounded_rectangle(
        [bell_x, cur_y, bell_x + bell_size, cur_y + bell_size],
        radius=32, fill=b_bg, outline=b_border, width=2
    )

    bell_cx = bell_x + bell_size // 2
    bell_cy = cur_y + bell_size // 2
    bell_col = (250, 204, 21)

    rot = 0
    if is_belled and t < 4.3:
        ring_prog = (t - 3.6)
        rot = int(12 * math.sin(ring_prog * 25) * math.exp(-ring_prog * 4))

    # Bell drawing
    b_ox = rot
    draw.polygon([
        (bell_cx - 13 + b_ox, bell_cy + 12),
        (bell_cx + 13 + b_ox, bell_cy + 12),
        (bell_cx + 10 - b_ox, bell_cy - 10),
        (bell_cx - 10 - b_ox, bell_cy - 10)
    ], fill=bell_col)
    draw.ellipse([bell_cx - 10 + b_ox, bell_cy - 15, bell_cx + 10 + b_ox, bell_cy - 5], fill=bell_col)
    draw.ellipse([bell_cx - 4 - b_ox, bell_cy + 11, bell_cx + 4 - b_ox, bell_cy + 18], fill=bell_col)

    if is_belled:
        draw.arc([bell_cx - 24, bell_cy - 10, bell_cx - 14, bell_cy + 10], 90, 270, fill=bell_col, width=3)
        draw.arc([bell_cx + 14, bell_cy - 10, bell_cx + 24, bell_cy + 10], 270, 90, fill=bell_col, width=3)

    # ==========================================
    # SECTION 4: MOUSE POINTER & CLICKS
    # ==========================================
    if 0.5 <= t <= 4.5:
        if t < 1.3:
            p = (t - 0.5) / 0.8
            cx = int(like_x - 40 + (like_x + like_w // 2 - (like_x - 40)) * p)
            cy = int((H + 30) + (cur_y + like_h // 2 - (H + 30)) * p)
            click = (1.25 <= t <= 1.35)
        elif t < 2.5:
            p = (t - 1.3) / 1.2
            cx = int((like_x + like_w // 2) + (sub_x + sub_w // 2 - (like_x + like_w // 2)) * p)
            cy = int((cur_y + like_h // 2) + (cur_y + sub_h // 2 - (cur_y + like_h // 2)) * p)
            click = (2.45 <= t <= 2.55)
        elif t < 3.6:
            p = (t - 2.5) / 1.1
            cx = int((sub_x + sub_w // 2) + (bell_cx - (sub_x + sub_w // 2)) * p)
            cy = int((cur_y + sub_h // 2) + (bell_cy - (cur_y + sub_h // 2)) * p)
            click = (3.55 <= t <= 3.65)
        else:
            p = (t - 3.6) / 0.9
            cx = int(bell_cx + (W + 50 - bell_cx) * p)
            cy = int(bell_cy + (H + 50 - bell_cy) * p)
            click = False

        scale = 0.85 if click else 1.0
        if click:
            draw.ellipse([cx - 18, cy - 18, cx + 18, cy + 18], outline=(255, 255, 255), width=2)

        c_pts = [
            (cx, cy),
            (cx, int(cy + 24 * scale)),
            (int(cx + 7 * scale), int(cy + 18 * scale)),
            (int(cx + 13 * scale), int(cy + 29 * scale)),
            (int(cx + 17 * scale), int(cy + 27 * scale)),
            (int(cx + 12 * scale), int(cy + 16 * scale)),
            (int(cx + 20 * scale), int(cy + 16 * scale))
        ]
        draw.polygon(c_pts, fill=(255, 255, 255), outline=(0, 0, 0))

    raw_bytes = im.tobytes()
    proc.stdin.write(raw_bytes)

proc.stdin.close()
proc.wait()
print(f"Generated {out_mp4} successfully! Size: {out_mp4.stat().st_size} bytes")
