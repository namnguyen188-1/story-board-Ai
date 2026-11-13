"""Storyboard Studio - Authentic After Skool Style Colored Marker Whiteboard Animation.

Draws true stroke-by-stroke marker line art followed by real marker hatching and
coloring strokes on a crisp whiteboard canvas. Eliminates fake radial image unmasking:
every outline, detail, and colored region is physically drawn and painted by the marker tip.
Features natural human cadence, nearest-neighbor stroke chaining, and uniform progress.
"""
from __future__ import annotations
from pathlib import Path
import math, os, subprocess, tempfile, wave
import cv2
import numpy as np
from PIL import Image, ImageOps


def _hand(height):
    assets = Path(__file__).resolve().parent / "engine" / "assets"
    image = cv2.imread(str(assets / "drawing-hand.png"))
    mask = cv2.imread(str(assets / "hand-mask.png"), cv2.IMREAD_GRAYSCALE)
    if image is None or mask is None or mask.shape[:2] != image.shape[:2]:
        raise RuntimeError("Drawing hand assets missing or invalid")
    scale = height * 0.65 / image.shape[0]
    size = (max(1, round(image.shape[1] * scale)), max(1, round(image.shape[0] * scale)))
    image = cv2.resize(image, size, interpolation=cv2.INTER_AREA)
    alpha = cv2.resize(mask, size, interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
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
        frame[y0:y1, x0:x1] * (1.0 - a) + image[sy : sy + y1 - y0, sx : sx + x1 - x0] * a
    ).astype(np.uint8)


def _extract_calibrated_contours(source, max_contours=450):
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

    smooth = cv2.bilateralFilter(work, 9, 75, 75)
    smooth = cv2.medianBlur(smooth, 3)
    gray = cv2.cvtColor(smooth, cv2.COLOR_BGR2GRAY)

    med = float(np.median(gray))
    low = int(max(24, min(100, med * 0.45)))
    high = int(max(low + 35, min(210, med * 1.15)))
    outlines = cv2.Canny(gray, low, high)
    contours, _ = cv2.findContours(outlines, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    min_len = max(8, round(min(work.shape[:2]) * 0.012))
    ranked = []
    for raw in contours:
        l = cv2.arcLength(raw, False)
        if l < min_len:
            continue
        app = cv2.approxPolyDP(raw, 1.25, False)
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
        best_dist = 1e12
        rev = False
        for i, p in enumerate(polys):
            d0 = float(np.sum((p[0] - curr_pt) ** 2))
            d1 = float(np.sum((p[-1] - curr_pt) ** 2))
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
    stride = max(3.5, min(work.shape[:2]) / 130.0)
    steps = []
    for poly in ordered_polys:
        prev = None
        for a, b in zip(poly[:-1], poly[1:]):
            diff = b.astype(np.float32) - a
            span = float(np.linalg.norm(diff))
            cnt = max(1, min(80, int(np.ceil(span / stride))))
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


def _extract_color_hatching_steps(source, line_mask):
    """Extracts authentic marker hatching/coloring stroke paths region-by-region.
    
    Segments the illustration into connected color components and generates
    alternating horizontal zigzag stroke paths (nét gạch zíc-zắc qua lại của ngòi bút dạ)
    ordered naturally from the image focal center outward.
    """
    height, width = source.shape[:2]
    scale = min(1.0, 960.0 / max(width, height))
    if scale < 1.0:
        work = cv2.resize(source, (max(64, round(width * scale)), max(64, round(height * scale))), interpolation=cv2.INTER_AREA)
        lmask_scaled = cv2.resize(line_mask.astype(np.uint8), (work.shape[1], work.shape[0]), interpolation=cv2.INTER_NEAREST) > 0
    else:
        work = source
        lmask_scaled = line_mask

    smooth = cv2.bilateralFilter(work, 9, 75, 75)
    smooth = cv2.medianBlur(smooth, 3)

    lab = cv2.cvtColor(smooth, cv2.COLOR_BGR2LAB)
    pts = lab.reshape(-1, 3).astype(np.float32)
    k = 16
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    try:
        _, labels, _ = cv2.kmeans(pts, k, None, criteria, 4, cv2.KMEANS_PP_CENTERS)
        labels = labels.reshape(work.shape[:2])
    except Exception:
        labels = np.zeros(work.shape[:2], dtype=np.int32)
        k = 1

    wh, ww = work.shape[:2]
    components = []
    min_area = max(35, round(ww * wh * 0.00035))

    for cid in range(k):
        mask = (labels == cid).astype(np.uint8)
        mask[lmask_scaled] = 0
        if not np.any(mask):
            continue
        cnt, parts, stats, centroids = cv2.connectedComponentsWithStats(mask, 8)
        for i in range(1, cnt):
            area = stats[i, cv2.CC_STAT_AREA]
            if area >= min_area:
                cx, cy = centroids[i]
                comp_mask = (parts == i).astype(np.uint8)
                mean_bgr = smooth[comp_mask > 0].mean(axis=0)
                # If area is already pure whiteboard white (>238), skip it
                if float(np.mean(mean_bgr)) > 238.0:
                    continue
                components.append({
                    'center': (float(cx), float(cy)),
                    'mask': comp_mask,
                    'bbox': (int(stats[i, cv2.CC_STAT_LEFT]), int(stats[i, cv2.CC_STAT_TOP]),
                             int(stats[i, cv2.CC_STAT_WIDTH]), int(stats[i, cv2.CC_STAT_HEIGHT]))
                })

    if not components:
        return []

    # Spatial Nearest-Neighbor chaining from image center outward
    screen_c = np.array([ww / 2.0, wh / 2.0], dtype=np.float32)
    components.sort(key=lambda c: float(np.sum((np.array(c['center']) - screen_c) ** 2)))
    ordered = [components.pop(0)]
    while components:
        cur = np.array(ordered[-1]['center'], dtype=np.float32)
        dists = [float(np.sum((np.array(c['center']) - cur) ** 2)) for c in components]
        idx = int(np.argmin(dists))
        ordered.append(components.pop(idx))

    # Generate zigzag scanlines for each ordered component
    inv = 1.0 / scale
    spacing = max(4, round(6.0 * scale))
    stride = max(5.0, 7.0 * scale)
    color_steps = []

    for comp in ordered:
        comp_mask = comp['mask']
        x_min, y_min, bw, bh = comp['bbox']
        y_max = min(wh, y_min + bh)
        direction = 1

        for y in range(y_min, y_max, spacing):
            row = comp_mask[y, :]
            active_x = np.where(row > 0)[0]
            if len(active_x) == 0:
                continue

            diffs = np.diff(active_x)
            splits = np.where(diffs > 2)[0]
            seg_starts = np.insert(active_x[splits + 1], 0, active_x[0])
            seg_ends = np.append(active_x[splits], active_x[-1])
            segs = list(zip(seg_starts, seg_ends))
            if direction == -1:
                segs.reverse()

            for x0, x1 in segs:
                if abs(x1 - x0) < 2:
                    continue
                mid_x = int((x0 + x1) // 2)
                bgr_col = tuple(int(c) for c in smooth[y, mid_x])
                span = float(abs(x1 - x0))
                cnt = max(1, min(120, int(np.ceil(span / stride))))

                for s in range(cnt + 1):
                    t = s / cnt
                    cur_x = round(x0 * (1.0 - t) + x1 * t) if direction == 1 else round(x1 * (1.0 - t) + x0 * t)
                    real_x = max(0, min(width - 1, round(cur_x * inv)))
                    real_y = max(0, min(height - 1, round(y * inv)))
                    color_steps.append((real_x, real_y, bgr_col, s > 0))

            direction *= -1

    return color_steps


def iter_colored_marker_frames(source, total_frames, hold_frames, make_hand, overlay):
    """Streams video frames with authentic stroke-by-stroke marker drawing and coloring.
    
    100% Stroke-Based Rendering:
    - Phase I (~42% drawing time): Crisp dark marker outline sketching stroke-by-stroke.
    - Phase II (~58% drawing time): Vibrant marker hatching strokes back-and-forth filling colors.
    - Phase III (hold frames): Clean completed marker illustration hold on pure whiteboard backdrop.
    NO photographic unmasking, NO radial blob unmasking, NO raw JPEG pop!
    """
    if source.ndim != 3 or source.shape[2] != 3 or total_frames < 3:
        raise ValueError("Need BGR 3-channel source and at least three frames")

    hold = max(1, min(int(hold_frames), max(1, total_frames // 4)))
    drawing = total_frames - hold
    outline_count = max(1, round(drawing * 0.42))
    paint_count = drawing - outline_count

    height, width = source.shape[:2]
    hand = make_hand(height)
    line_thickness = max(2, round(min(height, width) / 450))
    marker_hatch_thickness = max(5, round(min(height, width) / 100))

    # Pre-extract line art strokes
    line_steps = _extract_calibrated_contours(source)

    # Precompute line art mask
    line_art_mask = np.zeros((height, width), dtype=np.uint8)
    prev = None
    for x, y, down in line_steps:
        if down and prev:
            cv2.line(line_art_mask, prev, (x, y), 255, line_thickness + 1, cv2.LINE_AA)
        prev = (x, y)
    has_line_mask = line_art_mask > 0

    # Pre-extract color hatching strokes
    color_steps = _extract_color_hatching_steps(source, has_line_mask)

    # Initialize pure white canvases
    canvas_lines = np.full_like(source, 255)
    canvas_color = np.full_like(source, 255)

    # Phase I: Draw structural marker outlines stroke-by-stroke
    used_lines = 0
    prev_pt = None
    hand_pos = None

    for frame_no in range(outline_count):
        target = round((frame_no + 1) / outline_count * len(line_steps)) if line_steps else 0
        while used_lines < target:
            x, y, pen_down = line_steps[used_lines]
            if pen_down and prev_pt:
                # Prevent drawing across wide transit gaps
                if (x - prev_pt[0]) ** 2 + (y - prev_pt[1]) ** 2 < (width * 0.22) ** 2:
                    cv2.line(canvas_lines, prev_pt, (x, y), (28, 28, 32), line_thickness, cv2.LINE_AA)
            prev_pt = (x, y)
            used_lines += 1

        frame = canvas_lines.copy()
        if prev_pt and frame_no > 0:
            target_hand = np.array(prev_pt, dtype=np.float32)
            if hand_pos is None:
                hand_pos = target_hand
            else:
                diff = target_hand - hand_pos
                dist = float(np.linalg.norm(diff))
                blend = 0.65 if dist < 120.0 else 0.90
                hand_pos = hand_pos + diff * blend
            overlay(frame, hand, int(hand_pos[0]), int(hand_pos[1]))
        yield frame

    # Phase II: Real Marker Hatching Strokes (nét gạch zíc-zắc qua lại của bút dạ)
    used_color = 0
    prev_col_pt = None

    for frame_no in range(paint_count):
        target = round((frame_no + 1) / paint_count * len(color_steps)) if color_steps else 0
        while used_color < target:
            x, y, col, pen_down = color_steps[used_color]
            if pen_down and prev_col_pt:
                if (x - prev_col_pt[0]) ** 2 + (y - prev_col_pt[1]) ** 2 < (width * 0.22) ** 2:
                    cv2.line(canvas_color, prev_col_pt, (x, y), col, marker_hatch_thickness, cv2.LINE_AA)
            prev_col_pt = (x, y)
            used_color += 1

        frame = canvas_color.copy()
        # Overlay crisp black outlines on top of marker fills
        frame[has_line_mask] = canvas_lines[has_line_mask]

        if prev_col_pt and frame_no < paint_count - 1:
            target_hand = np.array(prev_col_pt, dtype=np.float32)
            if hand_pos is None:
                hand_pos = target_hand
            else:
                diff = target_hand - hand_pos
                dist = float(np.linalg.norm(diff))
                blend = 0.65 if dist < 120.0 else 0.90
                hand_pos = hand_pos + diff * blend
            overlay(frame, hand, int(hand_pos[0]), int(hand_pos[1]))
        yield frame

    # Phase III: Clean final artwork hold without hand
    final_artwork = canvas_color.copy()
    final_artwork[has_line_mask] = canvas_lines[has_line_mask]
    for _ in range(hold):
        yield final_artwork.copy()


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
