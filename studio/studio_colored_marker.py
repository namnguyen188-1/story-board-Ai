"""Storyboard Studio - After Skool Style Colored Marker Whiteboard Animation.

Draws vibrant multicolored marker strokes (bút dạ màu đa sắc) on a crisp whiteboard,
followed by smooth marker shading and regional coloring, preserving 100% exact original art.
Features natural human-cadence drawing speeds, nearest-neighbor contour chaining,
and uniform cumulative area progression so that drawing and coloring maintain a steady,
engaging pace from the first second to the last.
"""
from __future__ import annotations
from pathlib import Path
import math, os, subprocess, tempfile, wave
import cv2
import numpy as np
from PIL import Image, ImageOps

from studio_hand_color_strokes import _color_regions

def _hand(height):
    assets = Path(__file__).resolve().parent / "engine" / "assets"
    image = cv2.imread(str(assets / "drawing-hand.png"))
    mask = cv2.imread(str(assets / "hand-mask.png"), cv2.IMREAD_GRAYSCALE)
    if image is None or mask is None or mask.shape[:2] != image.shape[:2]:
        raise RuntimeError("Drawing hand assets missing or invalid")
    scale = height * 0.65 / image.shape[0]
    size = (max(1, round(image.shape[1] * scale)), max(1, round(image.shape[0] * scale)))
    image = cv2.resize(image, size, interpolation=cv2.INTER_AREA)
    alpha = cv2.resize(mask, size, interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    return image, alpha, round(35 * scale), round(18 * scale)

def _overlay(frame, hand, x, y):
    image, alpha, tip_x, tip_y = hand
    left, top = int(x) - tip_x, int(y) - tip_y
    h, w = frame.shape[:2]
    hh, hw = image.shape[:2]
    x0, y0 = max(0, left), max(0, top)
    x1, y1 = min(w, left + hw), min(h, top + hh)
    if x0 >= x1 or y0 >= y1:
        return
    sx, sy = x0 - left, y0 - top
    a = alpha[sy : sy + y1 - y0, sx : sx + x1 - x0, None]
    frame[y0:y1, x0:x1] = (
        frame[y0:y1, x0:x1] * (1 - a) + image[sy : sy + y1 - y0, sx : sx + x1 - x0] * a
    ).astype(np.uint8)

def _vibrant_marker_color(bgr_pixel):
    """Converts a source pixel to a rich, saturated whiteboard marker ink color."""
    b, g, r = int(bgr_pixel[0]), int(bgr_pixel[1]), int(bgr_pixel[2])
    # If the pixel is near-white or very light, use a bold dark ink for visibility
    brightness = 0.299 * r + 0.587 * g + 0.114 * b
    if brightness > 215:
        return (38, 38, 42)
    
    # Calculate saturation difference
    max_c = max(r, g, b)
    min_c = min(r, g, b)
    diff = max_c - min_c
    if diff < 16:
        # Near-grayscale or dark shadow -> bold black marker ink
        return (32, 32, 35)
    
    # Convert to HSV and boost saturation for chisel-tip whiteboard marker look
    hsv = cv2.cvtColor(np.uint8([[[b, g, r]]]), cv2.COLOR_BGR2HSV)[0][0]
    h, s, v = int(hsv[0]), int(hsv[1]), int(hsv[2])
    s = min(255, max(125, int(s * 1.55)))
    v = min(205, max(45, int(v * 0.92)))
    res = cv2.cvtColor(np.uint8([[[h, s, v]]]), cv2.COLOR_HSV2BGR)[0][0]
    return (int(res[0]), int(res[1]), int(res[2]))

def _extract_calibrated_contours(source, max_contours=220):
    """Extracts structural line contours ordered via Nearest-Neighbor chaining.
    
    Eliminates erratic hand jumping by ensuring the pen glides smoothly from each
    completed stroke to the closest adjacent line endpoint.
    """
    height, width = source.shape[:2]
    scale = min(1.0, 960.0 / max(width, height))
    if scale < 1.0:
        work = cv2.resize(source, (max(64, round(width * scale)), max(64, round(height * scale))), interpolation=cv2.INTER_AREA)
    else:
        work = source

    gray = cv2.cvtColor(work, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    med = float(np.median(gray))
    low = int(max(28, min(110, med * 0.48)))
    high = int(max(low + 38, min(215, med * 1.15)))
    outlines = cv2.Canny(gray, low, high)
    contours, _ = cv2.findContours(outlines, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    min_len = max(14, round(min(work.shape[:2]) * 0.020))
    ranked = []
    for raw in contours:
        l = cv2.arcLength(raw, True)
        if l < min_len:
            continue
        app = cv2.approxPolyDP(raw, 1.35, True)
        if len(app) >= 2:
            ranked.append((l, app[:, 0]))

    ranked.sort(key=lambda item: -item[0])
    ranked = ranked[:max_contours]
    if not ranked:
        return []

    # Greedy Nearest-Neighbor chaining across contour endpoints
    polys = [r[1] for r in ranked]
    ordered_polys = [polys.pop(0)]
    curr_pt = ordered_polys[0][-1]

    while polys:
        best_idx = 0
        best_dist = 1e9
        rev = False
        for i, p in enumerate(polys):
            d0 = np.sum((p[0] - curr_pt) ** 2)
            d1 = np.sum((p[-1] - curr_pt) ** 2)
            if d0 < best_dist:
                best_dist = d0
                best_idx = i
                rev = False
            if d1 < best_dist:
                best_dist = d1
                best_idx = i
                rev = True
        nxt = polys.pop(best_idx)
        if rev:
            nxt = nxt[::-1]
        ordered_polys.append(nxt)
        curr_pt = nxt[-1]

    # Convert polylines into dense, smooth step coordinates
    inv = 1.0 / scale
    stride = max(3.5, min(work.shape[:2]) / 120.0)
    steps = []
    for poly in ordered_polys:
        # Close loop if polyline start and end are near
        if len(poly) > 2 and np.linalg.norm(poly[0] - poly[-1]) < 25:
            poly = np.vstack([poly, poly[0]])
        prev = None
        for a, b in zip(poly[:-1], poly[1:]):
            diff = b.astype(np.float32) - a
            span = float(np.linalg.norm(diff))
            cnt = max(1, min(100, int(np.ceil(span / stride))))
            for s in range(cnt + 1):
                t = s / cnt
                pt = a * (1.0 - t) + b * t
                xy = (max(0, min(width - 1, round(float(pt[0]) * inv))),
                      max(0, min(height - 1, round(float(pt[1]) * inv))))
                if xy == prev:
                    continue
                steps.append((xy[0], xy[1], prev is not None))
                prev = xy

    return steps

def iter_colored_marker_frames(source, total_frames, hold_frames, make_hand, overlay):
    """Streams video frames with vibrant colored marker strokes and smooth marker shading.
    
    Synchronized naturally to scene duration:
    - Phase I (~48% drawing time): Calm, deliberate colored marker outline sketching.
    - Phase II (~52% drawing time): Fluid regional shading with uniform area progression.
    - Phase III (hold frames): Clean final artwork hold without hand.
    """
    if source.ndim != 3 or source.shape[2] != 3 or total_frames < 3:
        raise ValueError("Need BGR 3-channel source and at least three frames")

    # Dynamic time allocation: 86-88% active drawing, remaining is clean hold
    hold = max(1, min(int(hold_frames), max(1, total_frames // 4)))
    drawing = total_frames - hold
    outline_count = max(1, round(drawing * 0.48))
    paint_count = drawing - outline_count

    height, width = source.shape[:2]
    hand = make_hand(height)
    thickness = max(2, round(height / 420))
    raw_steps = _extract_calibrated_contours(source)

    # Distribute outline steps smoothly and completely across outline_count frames
    steps = raw_steps

    # Canvases
    canvas_white = np.full_like(source, 255)
    marker_lines = canvas_white.copy()
    marker_mask = np.zeros((height, width), dtype=np.uint8)

    # Phase I: Draw true colored marker strokes following contours
    used = 0
    hand_xy = None
    for frame_no in range(outline_count):
        target = round((frame_no + 1) / outline_count * len(steps)) if steps else 0
        if frame_no == 0:
            target = 0
            
        while used < target:
            x, y, pen_down = steps[used]
            if pen_down and used > 0:
                prev_x, prev_y, _ = steps[used - 1]
                # Avoid drawing across long pen-up transit gaps
                if (x - prev_x) ** 2 + (y - prev_y) ** 2 < (width * 0.18) ** 2:
                    marker_col = _vibrant_marker_color(source[y, x])
                    cv2.line(marker_lines, (prev_x, prev_y), (x, y), marker_col, thickness, cv2.LINE_AA)
                    cv2.line(marker_mask, (prev_x, prev_y), (x, y), 255, thickness, cv2.LINE_AA)
            hand_xy = (x, y)
            used += 1

        frame = marker_lines.copy()
        if frame_no > 0 and hand_xy:
            overlay(frame, hand, *hand_xy)
        yield frame

    # Phase II: Colored marker fill & fluid shading with uniform area progression
    if paint_count:
        color_order, regions, radii, center_x, center_y, low_w, low_h = _color_regions(source)
        n = len(regions)
        areas = np.array([r[1] for r in regions], dtype=np.float32)
        total_area = float(np.sum(areas)) if n > 0 else 1.0
        cum_areas = np.cumsum(areas)
        start_frac = np.zeros(n, dtype=np.float32)
        start_frac[1:] = cum_areas[:-1] / total_area
        end_frac = cum_areas / total_area

        hand_pos = np.array(hand_xy) if hand_xy else None

        for frame_no in range(paint_count):
            # Uniform area progression: exactly equal area revealed each frame
            progress = (frame_no + 1) / paint_count
            painted = color_order <= progress

            frame = marker_lines.copy()
            frame[painted] = source[painted]
            frame[marker_mask > 0] = marker_lines[marker_mask > 0]
            frame[painted] = source[painted]

            if frame_no < paint_count - 1 and n > 0:
                # Find which region is currently active
                act = int(np.clip(np.searchsorted(end_frac, progress), 0, n - 1))
                cx = center_x[act]
                cy = center_y[act]
                cur_span = max(1e-5, float(end_frac[act] - start_frac[act]))
                rel = max(0.0, min(1.0, float((progress - start_frac[act]) / cur_span)))

                # Active shading radius and subtle marker drawing oscillation
                r_val = float(radii[act]) * (width / low_w) * rel
                wiggle_r = min(18.0, max(3.5, r_val * 0.45))
                angle = rel * (2 * np.pi * 3.5) + frame_no * 0.45
                target_px = cx * width / low_w + wiggle_r * np.cos(angle)
                target_py = cy * height / low_h + wiggle_r * np.sin(angle)

                # Smooth adaptive hand motion with responsive transition
                if hand_pos is None:
                    hand_pos = np.array([target_px, target_py])
                else:
                    diff = np.array([target_px, target_py]) - hand_pos
                    dist = float(np.linalg.norm(diff))
                    blend = 0.55 if dist < 110.0 else 0.85
                    hand_pos = hand_pos + diff * blend

                overlay(frame, hand, int(hand_pos[0]), int(hand_pos[1]))
            else:
                frame = source.copy()
            yield frame

    # Phase III: Clean final artwork hold without hand
    for _ in range(hold):
        yield source.copy()

def colored_marker_video(image, audio, output, width, height, fps=25):
    """Renders After Skool style Colored Marker Whiteboard video synchronized to audio."""
    if width <= 0 or height <= 0 or width % 2 or height % 2 or fps <= 0:
        raise ValueError("Video dimensions must be positive even integers")
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(audio), "rb") as w:
        seconds = w.getnframes() / max(1, w.getframerate())
    total = max(3, math.ceil(seconds * fps))

    # Balanced hold time: 1.5s to 4.5s hold (around 12-14% of scene), leaving 86-88% for drawing
    hold_seconds = max(1.5, min(4.5, seconds * 0.12))
    hold_frames = max(1, round(hold_seconds * fps))

    with Image.open(image) as original:
        source = np.asarray(ImageOps.pad(original.convert("RGB"), (width, height),
            method=Image.Resampling.LANCZOS, color="white"))[:, :, ::-1].copy()

    fd, temp = tempfile.mkstemp(suffix=".mp4", prefix="colored_marker_", dir=output.parent)
    os.close(fd)
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo",
        "-pix_fmt", "bgr24", "-s", f"{width}x{height}", "-r", str(fps),
        "-i", "pipe:0", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", temp
    ]
    process = None
    try:
        with tempfile.TemporaryFile() as errors:
            process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=errors, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            try:
                for frame in iter_colored_marker_frames(source, total, hold_frames, _hand, _overlay):
                    process.stdin.write(frame.tobytes())
                process.stdin.close()
                code = process.wait(timeout=180)
            except BaseException:
                process.kill()
                process.wait()
                raise
            if code:
                errors.seek(0)
                raise RuntimeError("Colored marker encode failed: " + errors.read().decode(errors="replace")[-500:])
        cap = cv2.VideoCapture(temp)
        try:
            fc = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            valid = cap.isOpened() and abs(fc - total) <= 1
        finally:
            cap.release()
        if not valid:
            raise RuntimeError("Colored marker MP4 verification failed")
        os.replace(temp, output)
    finally:
        if Path(temp).exists():
            Path(temp).unlink()
    return str(output)
