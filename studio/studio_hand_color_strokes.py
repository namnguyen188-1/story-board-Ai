"""Stroke-aware full-color whiteboard animation.

No network, GUI or external dependency beyond bundled OpenCV/Numpy.
The real hand follows image contours, then colors contiguous regions.
The original source pixels are preserved exactly after the last brush pass.
"""
from __future__ import annotations

import cv2
import numpy as np


def _outline_steps(source):
    """Object-aware contour traversal, similar to the original mono drawing engine."""
    height, width = source.shape[:2]
    scale = min(1.0, 800.0 / max(width, height))
    if scale < 1.0:
        work = cv2.resize(source, (max(64, round(width * scale)),
                                   max(64, round(height * scale))),
                          interpolation=cv2.INTER_AREA)
    else:
        work = source
    gray = cv2.cvtColor(work, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    med = float(np.median(gray))
    low = int(max(24, min(110, med * .48)))
    high = int(max(low + 35, min(215, med * 1.12)))
    outlines = cv2.Canny(gray, low, high)
    contours, _ = cv2.findContours(outlines, cv2.RETR_LIST,
                                   cv2.CHAIN_APPROX_SIMPLE)
    minimum = max(9, round(min(work.shape[:2]) * .020))
    ranked = []
    for raw in contours:
        length = cv2.arcLength(raw, True)
        if length < minimum:
            continue
        approximation = cv2.approxPolyDP(raw, 1.35, True)
        if len(approximation) < 2:
            continue
        ranked.append((length, approximation[:, 0]))
    ranked.sort(key=lambda item: -item[0])
    ranked = ranked[:520]

    # Sample the true contour polyline, not the horizontal image rows.
    stride = max(4.0, min(work.shape[:2]) / 95)
    inv = 1.0 / scale
    steps = []
    for _, poly in ranked:
        poly = np.vstack([poly, poly[0]])
        prev = None
        for a, b in zip(poly[:-1], poly[1:]):
            difference = b.astype(np.float32) - a
            span = float(np.linalg.norm(difference))
            count = max(1, min(240, int(np.ceil(span / stride))))
            for step in range(count + 1):
                t = step / count
                coord = a * (1 - t) + b * t
                xy = (max(0, min(width - 1, round(float(coord[0]) * inv))),
                      max(0, min(height - 1, round(float(coord[1]) * inv))))
                if xy == prev:
                    continue
                steps.append((xy[0], xy[1], prev is not None))
                prev = xy
                if len(steps) >= 14000:
                    break
            if len(steps) >= 14000:
                break
        if len(steps) >= 14000:
            break
    return steps


def _color_regions(source):
    """Small-scale color segmentation with connected object/paint regions.
    Uses Cumulative Area Progression and Nearest-Neighbor spatial chaining so that
    painting advances at a completely uniform, natural pace from start to finish.
    """
    h, w = source.shape[:2]
    tiny_w = max(48, min(192, round(w / max(h, w) * 192)))
    tiny_h = max(48, min(192, round(h / max(h, w) * 192)))
    sample = cv2.resize(source, (tiny_w, tiny_h), interpolation=cv2.INTER_AREA)
    sample = cv2.GaussianBlur(sample, (5, 5), 0)
    lab = cv2.cvtColor(sample, cv2.COLOR_BGR2LAB)
    points = lab.reshape(-1, 3).astype(np.float32)
    if float(points.std(axis=0).max()) < 2.0:
        clusters = np.zeros((tiny_h, tiny_w), np.int32)
        n_clusters = 1
    else:
        n_clusters = 9
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
                    14, .35)
        means = points.mean(axis=0)
        distances = np.sum((points - means) ** 2, axis=1)
        starts = [points[int(np.argmax(distances))]]
        for _ in range(n_clusters - 1):
            dist = np.min(np.stack([
                np.sum((points - seed) ** 2, axis=1) for seed in starts
            ]), axis=0)
            starts.append(points[int(np.argmax(dist))])
        palette = np.asarray(starts, dtype=np.float32)
        clusters = np.argmin(
            np.sum((points[:, None, :] - palette[None, :, :]) ** 2, axis=2),
            axis=1).astype(np.int32).reshape(tiny_h, tiny_w)

    labels = np.full((tiny_h, tiny_w), -1, dtype=np.int32)
    raw_regions = []
    min_region_area = max(6, round(tiny_w * tiny_h / 680))
    for color_id in range(n_clusters):
        count, parts, sizes, centers = cv2.connectedComponentsWithStats(
            (clusters == color_id).astype(np.uint8), 8)
        for comp in range(1, count):
            area = int(sizes[comp, cv2.CC_STAT_AREA])
            if area < min_region_area:
                continue
            uid = len(raw_regions)
            labels[parts == comp] = uid
            raw_regions.append((uid, area, tuple(map(float, centers[comp]))))

    if not raw_regions:
        labels.fill(0)
        raw_regions = [(0, tiny_w * tiny_h, (tiny_w / 2.0, tiny_h / 2.0))]

    missing = (labels < 0)
    if np.any(missing):
        _, nearest = cv2.distanceTransformWithLabels(
            (labels < 0).astype(np.uint8), cv2.DIST_L2, 3,
            labelType=cv2.DIST_LABEL_PIXEL)
        good = labels[~missing]
        lut = np.zeros(len(good) + 1, dtype=np.int32)
        lut[1:] = good
        labels[missing] = lut[nearest[missing]]

    # Spatial Nearest-Neighbor chaining from center
    screen_c = (tiny_w / 2.0, tiny_h / 2.0)
    rem = list(raw_regions)
    rem.sort(key=lambda r: (r[2][0] - screen_c[0]) ** 2 + (r[2][1] - screen_c[1]) ** 2)
    ord_regions = [rem.pop(0)] if rem else []
    while rem:
        cur = np.array(ord_regions[-1][2])
        idx = int(np.argmin([np.sum((np.array(r[2]) - cur) ** 2) for r in rem]))
        ord_regions.append(rem.pop(idx))

    # Re-map labels to ordered region index
    remap = np.zeros(len(raw_regions), dtype=np.int32)
    regions = []
    for new_idx, r in enumerate(ord_regions):
        remap[r[0]] = new_idx
        regions.append((new_idx, r[1], r[2]))
    labels = remap[labels]

    # Cumulative area calculation for uniform area progression across time
    areas = np.array([r[1] for r in regions], dtype=np.float32)
    total_area = float(np.sum(areas)) if len(areas) > 0 else 1.0
    cum_areas = np.cumsum(areas)
    start_frac = np.zeros(len(regions), dtype=np.float32)
    start_frac[1:] = cum_areas[:-1] / total_area
    end_frac = cum_areas / total_area
    span_frac = np.maximum(1e-6, end_frac - start_frac)

    ids = cv2.resize(labels, (w, h), interpolation=cv2.INTER_NEAREST)
    yy, xx = np.indices((h, w), dtype=np.float32)
    center_x = np.array([r[2][0] for r in regions], dtype=np.float32)
    center_y = np.array([r[2][1] for r in regions], dtype=np.float32)
    fx = center_x[ids] * (w / tiny_w)
    fy = center_y[ids] * (h / tiny_h)
    radial = np.sqrt((xx - fx) ** 2 + (yy - fy) ** 2)
    max_radius = np.zeros(len(regions), dtype=np.float32)
    np.maximum.at(max_radius, ids.ravel(), radial.ravel())
    norm_r = np.minimum(0.999, radial / np.maximum(1.0, max_radius[ids]))

    # Exact uniform cumulative area progression
    score = start_frac[ids] + norm_r * span_frac[ids]
    score = cv2.GaussianBlur(score, (0, 0), 2.0)
    return score, regions, max_radius, center_x, center_y, tiny_w, tiny_h


def iter_stroke_color_frames(source, total_frames, hold_frames, make_hand, overlay):
    """Stream frames: contour ink -> object color fill -> perfect color hold."""
    if source.ndim != 3 or source.shape[2] != 3 or total_frames < 3:
        raise ValueError("Need BGR 3-channel source and at least three frames")
    hold = max(1, min(int(hold_frames), max(1, total_frames // 4)))
    drawing = total_frames - hold
    outline_count = max(1, round(drawing * .35))
    paint_count = drawing - outline_count
    height, width = source.shape[:2]
    hand = make_hand(height)
    thickness = max(1, round(height / 620))
    steps = _outline_steps(source)
    contour = np.zeros((height, width), dtype=np.uint8)
    canvas_white = np.full_like(source, 255)

    # Phase I: build true ink path progressively
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
                cv2.line(contour, (prev_x, prev_y), (x, y), 255,
                         thickness, cv2.LINE_AA)
            hand_xy = (x, y)
            used += 1
        frame = canvas_white.copy()
        frame[contour > 0] = (35, 35, 35)
        if frame_no and hand_xy:
            overlay(frame, hand, *hand_xy)
        yield frame

    # Phase II: source colors spread uniformly through contiguous image regions
    if paint_count:
        color_order, regions, radii, center_x, center_y, low_w, low_h = (
            _color_regions(source))
        n = len(regions)
        areas = np.array([r[1] for r in regions], dtype=np.float32)
        total_area = float(np.sum(areas)) if n > 0 else 1.0
        cum_areas = np.cumsum(areas)
        start_frac = np.zeros(n, dtype=np.float32)
        start_frac[1:] = cum_areas[:-1] / total_area
        end_frac = cum_areas / total_area

        hand_pos = np.array(hand_xy) if hand_xy else None

        for frame_no in range(paint_count):
            progress = (frame_no + 1) / paint_count
            painted = color_order <= progress
            frame = canvas_white.copy()
            frame[contour > 0] = (35, 35, 35)
            frame[painted] = source[painted]
            if frame_no < paint_count - 1 and n > 0:
                act = int(np.clip(np.searchsorted(end_frac, progress), 0, n - 1))
                uid, _, (cx, cy) = regions[act]
                cur_span = max(1e-5, float(end_frac[act] - start_frac[act]))
                rel = max(0.0, min(1.0, float((progress - start_frac[act]) / cur_span)))
                
                r_val = float(radii[uid]) * (width / low_w) * rel
                wiggle_r = min(16.0, max(3.0, r_val * 0.4))
                angle = rel * (2 * np.pi * 3.0) + frame_no * 0.45
                target_px = cx * width / low_w + np.cos(angle) * wiggle_r
                target_py = cy * height / low_h + np.sin(angle) * wiggle_r

                if hand_pos is None:
                    hand_pos = np.array([target_px, target_py])
                else:
                    diff = np.array([target_px, target_py]) - hand_pos
                    dist = float(np.linalg.norm(diff))
                    blend = 0.55 if dist < 100.0 else 0.85
                    hand_pos = hand_pos + diff * blend

                overlay(frame, hand, int(hand_pos[0]), int(hand_pos[1]))
            else:
                frame = source.copy()
            yield frame

    # Phase III: clean exact original with no hand / no black-outline remnants
    for _ in range(hold):
        yield source.copy()
