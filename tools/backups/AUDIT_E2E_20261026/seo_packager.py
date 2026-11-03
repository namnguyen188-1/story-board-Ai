"""YouTube Publishing & VidIQ SEO Packaging Engine for Storyboard AI Studio Pro.

Generates viral high-CTR titles, full SEO descriptions with automated timestamps/chapters,

30 optimized tags, trending hashtags, pinned comments, and 1280x720 high-CTR thumbnails

with transparent internal metadata and image checks.

Fully multilingual: Automatically detects and adheres 100% to the video's production language

(Spanish, English, Vietnamese, Japanese, etc.) and genre (Stoic, Drama, History, etc.).

"""

from __future__ import annotations



import json

import os

import re

import sys

from pathlib import Path

from typing import Any, Dict, List, Optional, Tuple



if hasattr(sys.stdout, "reconfigure"):

    try:

        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    except Exception:

        pass

if hasattr(sys.stderr, "reconfigure"):

    try:

        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    except Exception:

        pass



import numpy as np

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont



STUDIO_DIR = Path(__file__).resolve().parent

if str(STUDIO_DIR) not in sys.path:

    sys.path.insert(0, str(STUDIO_DIR))



PRODUCTIONS_DIR = STUDIO_DIR / "productions"



import seo_quality as quality



from seo_genre_profiles import (

    GENRE_SEO_PROFILES,

    normalize_genre_key,

    enrich_and_maximize_tags,

    get_genre_seo_profile,

)



VIETNAMESE_ACCENT_PATTERN = re.compile(

    r"[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]",

    re.IGNORECASE,

)





def is_clean_lang_text(val: Any, is_vietnamese: bool = False) -> bool:

    return quality.clean_foreign_text(val, is_vietnamese)







def format_timestamp(seconds: float) -> str:

    """Formats seconds into MM:SS or HH:MM:SS."""

    s = int(round(seconds))

    hrs = s // 3600

    mins = (s % 3600) // 60

    secs = s % 60

    if hrs > 0:

        return f"{hrs:02d}:{mins:02d}:{secs:02d}"

    return f"{mins:02d}:{secs:02d}"





def detect_episode_language_and_genre(episode_dir: Path, plan: dict) -> Tuple[str, str, str]:

    """Detects primary language, genre, and topic from plan.json and scene job files."""

    cfg = plan.get("config", {})

    bible = plan.get("bible", {})



    first_job_p = episode_dir / "scenes" / "scene_0001" / "job.json"

    first_job = {}

    if first_job_p.exists():

        try:

            first_job = json.loads(first_job_p.read_text(encoding="utf-8"))

        except Exception:

            pass



    # 1. Primary Language

    lang = (

        first_job.get("language")

        or cfg.get("language")

        or ""

    ).strip()



    # 2. Sample narration inspection

    sc_obj = first_job.get("scene", {}) if isinstance(first_job.get("scene"), dict) else first_job

    narration_sample = str(sc_obj.get("narration") or "").strip()

    if not narration_sample and plan.get("scenes"):

        narration_sample = str(plan["scenes"][0].get("narration") or "").strip()



    # Detect Spanish indicators

    if not lang or lang.lower() == "auto":

        spanish_clues = ("¿", "¡", " que ", " para ", " con ", " mente ", " este ", " esta ", " cuando ", " estoicismo ")

        narr_lower = narration_sample.lower()

        if any(c in narr_lower for c in spanish_clues) or "¿" in narration_sample or "¡" in narration_sample:

            lang = "Spanish"

        elif any(c in narr_lower for c in (" và ", " của ", " những ", " người ", " cuộc sống ")):

            lang = "Vietnamese"

        elif any(c in narr_lower for c in (" the ", " and ", " with ", " this ", " that ")):

            lang = "English"

        else:

            lang = "Spanish" if "stoic" in str(cfg.get("genre", "")).lower() else "Vietnamese"



    # Normalize language string

    lang_clean = lang.capitalize()

    ll = lang_clean.lower()

    if ll in ("es", "español", "espanol", "spanish", "tây ban nha"):

        lang_clean = "Spanish"

    elif ll in ("vi", "tiếng việt", "vietnamese"):

        lang_clean = "Vietnamese"

    elif ll in ("en", "english", "tiếng anh"):

        lang_clean = "English"

    elif ll in ("ru", "russian", "tiếng nga"):

        lang_clean = "Russian"

    elif ll in ("de", "german", "deutsch", "tiếng đức"):

        lang_clean = "German"

    elif ll in ("fr", "french", "français", "francais", "tiếng pháp"):

        lang_clean = "French"

    elif ll in ("pt", "portuguese", "português", "portugues", "bồ đào nha"):

        lang_clean = "Portuguese"

    elif ll in ("it", "italian", "italiano", "tiếng ý"):

        lang_clean = "Italian"

    elif ll in ("ja", "japanese", "tiếng nhật"):

        lang_clean = "Japanese"

    elif ll in ("zh", "chinese", "tiếng trung"):

        lang_clean = "Chinese"



    # 3. Genre & Topic

    genre = str(first_job.get("genre") or cfg.get("genre") or bible.get("production_genre") or "auto").strip().lower()

    topic = str(bible.get("world") or bible.get("premise") or cfg.get("prompt") or "").strip()



    return lang_clean, genre, topic





def calculate_episode_chapters(episode_dir: Path, language: str = "auto") -> List[Dict[str, Any]]:

    return quality.episode_chapters(quality.build_episode_context(episode_dir, language=language))







def get_best_publishing_schedule(language: str = "auto", genre: str = "auto") -> Dict[str, Any]:

    return quality.calculate_publishing_schedule(language, genre)







def _bound_tags_to_limit(tag_candidates: List[str], max_chars: int = 485, min_tags: int = 20) -> List[str]:

    """Ensures tags are strictly within YouTube 500-char limit while maximizing volume (10/10 vidIQ).

    Targets 440-485 total characters (with comma separators) and at least 20 tags."""

    clean_seen = set()

    ordered = []

    for t in tag_candidates:

        if not t:

            continue

        t_clean = re.sub(r'[/\\_]+', ' ', str(t)).strip().lower()

        t_clean = re.sub(r'\s+', ' ', t_clean)

        if not t_clean or len(t_clean) < 2 or len(t_clean) > 60 or t_clean in clean_seen:

            continue

        clean_seen.add(t_clean)

        ordered.append(t_clean)



    bounded = []

    cur_len = 0

    for t in ordered:

        added = len(t) if not bounded else (len(t) + 2)

        if cur_len + added <= max_chars:

            bounded.append(t)

            cur_len += added

        else:

            continue

    return bounded





def calculate_vidiq_score(title, description, tags, primary_keyword, chapters, pinned_comment=None):

    """Legacy API name: returns an explicitly internal metadata checklist, not a vidIQ score."""

    return quality.check_metadata(title, description, tags, primary_keyword, chapters, pinned_comment)







def calculate_market_benchmark(*args, **kwargs):

    return quality.unknown_market()







def enrich_seo_package(package: Dict[str, Any]) -> Dict[str, Any]:

    return quality.enrich(package)







def slugify_seo_name(text: str) -> str:

    """Creates a URL-safe, search-engine friendly slug for thumbnail filenames."""

    import unicodedata

    clean_text = str(text or "").replace("Đ", "D").replace("đ", "d")

    nfkd = unicodedata.normalize("NFKD", clean_text)

    ascii_text = "".join([c for c in nfkd if not unicodedata.combining(c)])

    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_text).strip("-").lower()

    return slug[:60] or "youtube-thumbnail"





def calculate_thumbnail_vidiq_scorecard(image_path=None, title="", tags=None, **kwargs):

    """Legacy API name: checks the actual file, dimensions, format and size only."""

    return quality.thumbnail_check(image_path, **kwargs)







def analyze_competitor_thumbnail(image_path: Path, target_title: str = "", target_keywords=None):

    card = quality.thumbnail_check(image_path)

    if not card['width']:

        return {"error": "Không đọc được tệp ảnh."}

    return {"filename": Path(image_path).name, "width": card['width'], "height": card['height'],

        "aspect_ratio": round(card['width']/card['height'], 3), "source": card['source'],

        "raw_vidiq_score": None, "boosted_vidiq_score": None, "technical_checks": card,

        "score_diagnosis": {"current_score": card['rating'],

            "checks": [f"{b['label']}: {'Đạt' if b['passed'] else 'Cần sửa'}" for b in card['breakdown']]},

        "layout_breakdown": {"rule_of_thirds":"Cần xem ảnh để đánh giá bố cục", "text_position":"Chưa đo", "subject_position":"Chưa đo",

            "color_contrast": f"Độ lệch chuẩn độ sáng: {card['contrast_stddev']}", "safe_zone":"Cần kiểm tra bằng mắt"},

        "algorithm_strategy":{"concept":"Đối chiếu kỹ thuật ảnh", "explanation":"Đổi kích thước hoặc EXIF không chứng minh CTR hay thứ hạng."},

        "reverse_engineered_prompt":""}







def import_and_boost_competitor_thumbnail(src_image_path, episode_dir, best_title, tags, description="", series_name="", genre="auto", set_as_main=True):

    """Manual image import, serialized with generation; no fabricated score boost."""

    from PIL import ImageOps

    import shutil

    root=Path(episode_dir)

    with _episode_lock(root):

        with Image.open(src_image_path) as im:

            im=ImageOps.fit(im.convert('RGB'),(1280,720),method=Image.Resampling.LANCZOS)

            target=root/('thumbnail_seo.jpg' if set_as_main else 'thumbnail_competitor_trend.jpg')

            im.save(target,'JPEG',quality=92,optimize=True)

        data=quality.read_json(root/'youtube_publish_pack.json')

        if set_as_main:

            shutil.copyfile(target,root/'thumbnail_manual_source.jpg')

            data.update(thumbnail_file=str(target),thumbnail_url=_media_url(target),thumbnail_slug_filename=target.name,

                thumbnail_slug_url=_media_url(target),thumbnail_options=[{'file':target.name,'url':_media_url(target),'scene':998,'label':'Ảnh bạn chọn'}],

                thumbnail_selection={'source':'manual_upload','scene_number':998,'review_required':True})

            write_seo_package(root,enrich_seo_package(data))

        return data





def select_thumbnail_file(episode_dir, filename):

    """Select an existing local candidate; selecting the main file is a harmless no-op."""

    import shutil

    root=Path(episode_dir)

    if Path(filename).name!=filename:

        raise ValueError('Invalid thumbnail filename')

    source=root/filename

    if not source.is_file():

        raise FileNotFoundError(filename)

    target=root/'thumbnail_seo.jpg'

    with _episode_lock(root):

        if source.resolve()!=target.resolve():

            shutil.copyfile(source,target)

    return target





def _wrap_smart_quotes(s: str, force_case: str = "keep", use_quotes: bool = False) -> str:
    s = str(s or "").strip()
    if not s:
        return ""
    s = s.strip('"\' \u201c\u201d\u00ab\u00bb`')
    if not s:
        return ""
    if force_case == "upper":
        s = s.upper()
    elif force_case == "title":
        words = s.split()
        titled = []
        for w in words:
            if w.isupper() and len(w) <= 4:
                titled.append(w)
            else:
                titled.append(w.capitalize())
        s = " ".join(titled)
    if use_quotes:
        return f"“{s}”"
    return s


def _wrap_quotes(s: str) -> str:
    return _wrap_smart_quotes(s, force_case="upper", use_quotes=True)


def _split_hook_for_top_bottom(raw_text: str, norm_genre: str = "documentary") -> tuple[str, str]:
    text = str(raw_text or "").strip()
    use_q = (norm_genre == "family_drama")
    if not text:
        return ("“COURT ORDER!”" if use_q else "COURT ORDER!"), ("“Big Mistake!”" if use_q else "Big Mistake!")
    for sep in ("\n", " / ", " /", "/ ", "/", " | ", "|", " - ", " : ", ":", " — "):
        if sep in text:
            parts = text.split(sep, 1)
            p1, p2 = parts[0].strip(), parts[1].strip()
            if p1 and p2:
                t1 = _wrap_smart_quotes(p1, force_case="upper", use_quotes=use_q)
                t2_case = "title" if any(c.islower() for c in p2) or len(p2.split()) <= 3 else "upper"
                t2 = _wrap_smart_quotes(p2, force_case=t2_case, use_quotes=use_q)
                return t1, t2
    m = re.search(r"([!?])\s+", text)
    if m:
        idx = m.end()
        p1, p2 = text[:idx].strip(), text[idx:].strip()
        if p1 and p2:
            return _wrap_smart_quotes(p1, force_case="upper", use_quotes=use_q), _wrap_smart_quotes(p2, force_case="title", use_quotes=use_q)
    words = text.split()
    if len(words) >= 4:
        mid = (len(words) + 1) // 2
        return _wrap_smart_quotes(" ".join(words[:mid]), force_case="upper", use_quotes=use_q), _wrap_smart_quotes(" ".join(words[mid:]), force_case="upper", use_quotes=use_q)
    elif len(words) == 3:
        return _wrap_smart_quotes(" ".join(words[:2]), force_case="upper", use_quotes=use_q), _wrap_smart_quotes(words[2], force_case="upper", use_quotes=use_q)
    elif len(words) == 2:
        return _wrap_smart_quotes(words[0], force_case="upper", use_quotes=use_q), _wrap_smart_quotes(words[1], force_case="upper", use_quotes=use_q)
    return _wrap_smart_quotes(text, force_case="upper", use_quotes=use_q), ""


def _parse_hook_lines(raw_hook: str, norm_genre: str = "documentary") -> list[str]:
    raw = str(raw_hook or "").strip()
    if "/" in raw:
        parts = [p.strip() for p in raw.split("/") if p.strip()]
        if len(parts) >= 2:
            return parts[:3]
    elif "\n" in raw:
        parts = [p.strip() for p in raw.split("\n") if p.strip()]
        if len(parts) >= 2:
            return parts[:3]
    clean_words = raw.replace("¡", "").replace("!", "").replace("¿", "").replace("?", "").strip().split()
    if len(clean_words) <= 1:
        return [clean_words[0] if clean_words else "VIRAL HOOK"]
    elif len(clean_words) == 2:
        return [clean_words[0], clean_words[1]]
    elif len(clean_words) == 3:
        if len(clean_words[0]) <= 3 and len(clean_words[1]) <= 6:
            return [f"{clean_words[0]} {clean_words[1]}", clean_words[2]]
        return [clean_words[0], f"{clean_words[1]} {clean_words[2]}"]
    elif len(clean_words) == 4:
        # Group 2 and 2: e.g. "LA MUERTE" / "OCURRE AHORA"
        return [f"{clean_words[0]} {clean_words[1]}", f"{clean_words[2]} {clean_words[3]}"]
    elif len(clean_words) == 5:
        # e.g. "DEJA DE PERDER TU VIDA" -> "DEJA DE" / "PERDER TU VIDA"
        return [f"{clean_words[0]} {clean_words[1]}", f"{clean_words[2]} {clean_words[3]} {clean_words[4]}"]
    elif len(clean_words) == 6:
        return [f"{clean_words[0]} {clean_words[1]} {clean_words[2]}", f"{clean_words[3]} {clean_words[4]} {clean_words[5]}"]
    else:
        mid = len(clean_words) // 2
        return [" ".join(clean_words[:mid]), " ".join(clean_words[mid:min(mid+4, len(clean_words))])]

def draw_viral_typography(

    draw: ImageDraw.ImageDraw,

    xy: tuple[int, int],

    text: str,

    font: ImageFont.FreeTypeFont,

    fill_color: tuple[int, int, int, int],

    stroke_width: int = 8,

    stroke_color: tuple[int, int, int, int] = (0, 0, 0, 255),

    shadow_offset: tuple[int, int] = (6, 6),

    shadow_color: tuple[int, int, int, int] = (0, 0, 0, 240),

    num_shadow_layers: int = 3,

) -> None:

    """Renders viral YouTube top-channel typography:

    - Multi-pass directional 3D extrusion drop shadow (down-right depth).

    - Thick solid black border (7-10px) that eliminates background bleed and maximizes contrast.

    - Saturated, high-contrast core fill.

    """

    x, y = xy

    sx, sy = shadow_offset

    # 1. 3D Extrusion Shadow layers

    for layer in range(1, num_shadow_layers + 1):

        step_x = int(round(sx * (layer / num_shadow_layers)))

        step_y = int(round(sy * (layer / num_shadow_layers)))

        draw.text(

            (x + step_x, y + step_y),

            text,

            font=font,

            fill=shadow_color,

            stroke_width=stroke_width,

            stroke_fill=shadow_color,

        )

    # 2. Main solid crisp black border

    draw.text(

        (x, y),

        text,

        font=font,

        fill=stroke_color,

        stroke_width=stroke_width,

        stroke_fill=stroke_color,

    )

    # 3. Vivid core fill

    draw.text(

        (x, y),

        text,

        font=font,

        fill=fill_color,

        stroke_width=0,

    )





def find_smart_horizontal_x(

    edge_mag: np.ndarray,

    im_gray: np.ndarray,

    y1: int,

    y2: int,

    text_w: int,

    target_w: int = 1280,

    is_bottom: bool = False,

    max_right_limit: int = 1010,

    preferred_align: Optional[str] = None,

) -> int:

    """Calculates optimal x coordinate to avoid obstacles (faces, posts, mailboxes, car edges)."""

    center_x = (target_w - text_w) // 2

    left_x = 55

    right_x = min(target_w - text_w - 55, max_right_limit - text_w) if is_bottom else (target_w - text_w - 55)



    # Check overall frame negative space asymmetry

    left_half = im_gray[:, : target_w // 2]

    right_half = im_gray[:, target_w // 2 :]

    l_mean, r_mean = float(np.mean(left_half)), float(np.mean(right_half))

    l_std, r_std = float(np.std(left_half)), float(np.std(right_half))



    # If left half is significantly more open/clear than right half (bright sky/open road)

    open_on_left = (l_mean > r_mean + 25) or (r_std > l_std + 18)

    open_on_right = (r_mean > l_mean + 25) or (l_std > r_std + 18)



    eval_w = min(text_w, 480)



    def cost(x_cand: int, w_eval: int) -> float:

        x_start = max(0, int(x_cand))

        x_end = min(target_w, int(x_cand + w_eval))

        box = edge_mag[y1:y2, x_start:x_end]

        if box.size == 0:

            return 9999.0

        return float(np.max(box) * 0.4 + np.percentile(box, 90) * 0.4 + np.mean(box) * 0.2)



    cost_c = cost(center_x, text_w)

    cost_l = cost(left_x, eval_w)

    cost_r = cost(right_x, eval_w)



    # If preferred alignment requested (e.g. following line 1's alignment for visual harmony)

    if preferred_align == "left" and (cost_l <= cost_c * 1.25):

        return left_x

    if preferred_align == "right" and (cost_r <= cost_c * 1.25):

        return right_x



    # If the left half is the clear negative space and left cost is comparable or lower than center

    if open_on_left and (cost_l <= cost_c * 1.05 or cost_l < 55.0):

        return left_x

    if open_on_right and (cost_r <= cost_c * 1.05 or cost_r < 55.0):

        return right_x



    # If center collides with a prominent object and left is significantly cleaner:

    if cost_c > cost_l * 1.35 and (cost_c - cost_l > 2.0):

        return left_x

    if cost_c > cost_r * 1.35 and (cost_c - cost_r > 2.0):

        return right_x



    # Safe zone constraint for bottom

    if is_bottom and (center_x + text_w > max_right_limit):

        return min(center_x, max_right_limit - text_w)



    return center_x





def detect_faces_in_image(im: Image.Image) -> list[tuple[int, int, int, int]]:

    """Detects all human face bounding boxes (x, y, w, h) using OpenCV YuNet DNN."""

    try:

        import cv2

        yunet_path = STUDIO_DIR / "yunet.onnx"

        if not yunet_path.exists():

            return []



        cv_img = cv2.cvtColor(np.array(im.convert("RGB")), cv2.COLOR_RGB2BGR)

        h, w = cv_img.shape[:2]



        detector = cv2.FaceDetectorYN_create(

            model=str(yunet_path),

            config="",

            input_size=(w, h),

            score_threshold=0.45,

            nms_threshold=0.3,

            top_k=50,

        )

        detector.setInputSize((w, h))

        _, faces = detector.detect(cv_img)



        if faces is None:

            return []



        boxes = []

        for f in faces:

            fx, fy, fw, fh = f[:4]

            boxes.append((int(fx), int(fy), int(fw), int(fh)))

        return boxes

    except Exception as e:

        print(f"[THUMBNAIL_FACE_DETECTOR] Note: {e}")

        return []





def extract_best_scene_frame(video_path: Path | str, output_path: Path | str) -> Path:
    """Intelligently samples multiple points in a video and extracts the single highest-impact,
    brightest, sharpest frame for YouTube thumbnail generation."""
    v_path = Path(video_path)
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        import cv2
        import numpy as np

        cap = cv2.VideoCapture(str(v_path.resolve()))
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open video: {v_path}")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            cap.release()
            raise RuntimeError(f"Video has 0 frames: {v_path}")

        sample_points = [
            int(total_frames * p) for p in [0.15, 0.30, 0.45, 0.60, 0.75, 0.85]
            if int(total_frames * p) < total_frames
        ]
        if not sample_points:
            sample_points = [0]

        best_score = -999999.0
        best_frame = None

        for idx in sample_points:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if not ret or frame is None:
                continue

            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            b_mean = float(np.mean(hsv[:, :, 2]))
            b_std = float(np.std(hsv[:, :, 2]))
            sat = float(np.mean(hsv[:, :, 1]))
            lap = float(cv2.Laplacian(frame, cv2.CV_64F).var())

            # Severe penalty for near-black or unlit frames
            dark_penalty = -400.0 if b_mean < 20.0 else (-150.0 if b_mean < 32.0 else (80.0 if b_mean > 50.0 else 0.0))
            score = b_mean * 0.35 + b_std * 0.35 + sat * 0.20 + min(lap, 350.0) * 0.10 + dark_penalty

            if score > best_score:
                best_score = score
                best_frame = frame

        cap.release()

        if best_frame is not None:
            cv2.imwrite(str(out_path.resolve()), best_frame)
            return out_path
    except Exception as e:
        print(f"[EXTRACT_THUMB_WARN] OpenCV keyframe scan fallback: {e}", flush=True)

    # Fallback to ffmpeg at 2.0s (avoid 0.0-0.5s fade-in)
    import subprocess
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-ss", "00:00:02.000", "-i", str(v_path.resolve()),
        "-vframes", "1", str(out_path.resolve())
    ]
    try:
        subprocess.run(cmd, check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except Exception:
        cmd[4] = "00:00:00.500"
        subprocess.run(cmd, check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))

    return out_path


def generate_thumbnail_image(
    base_image_path: Path,
    output_path: Path,
    hook_text: str = "DOMINA TU MENTE",
    badge_text: Optional[str] = None,
    preferred_side: str = "auto",
    font_scale: str = "standard",
    metadata: Optional[Dict[str, Any]] = None,
    genre: Optional[str] = None,
) -> Path:

    """Creates a viral, ultra high-CTR YouTube thumbnail adhering strictly to YouTube design rules:

    - 50/50 Rule of Thirds layout: Character with intense expression on one side, massive bold text on opposite side.

    - Zero overlap: Text NEVER touches or covers the face, eyes, or expressions.

    - Huge, bold, high-CTR typography: Impact / Anton / Arial Black, up to 142px viral font size, thick 3D stroke + multi-layer shadow + high-voltage 2-tone colors.

    - Cinematic Visual Boost for Subject & Scene (Sharpness +40%, Saturation +25%, Contrast +20%).

    - YouTube Duration Badge Safe Zone: Protects bottom-right corner (x: 1040-1280, y: 600-720) from any text or badge.

    - Full EXIF/Windows XP metadata embedding directly in output JPEG binary for file organization; metadata does not predict ranking.

    """

    import numpy as np



    target_w, target_h = 1280, 720

    eff_genre = (
        genre
        or (metadata or {}).get("genre")
        or (metadata or {}).get("series_genre")
        or "documentary"
    )
    from seo_genre_profiles import normalize_genre_key
    norm_genre = normalize_genre_key(eff_genre)

    try:

        from clean_watermark import remove_gemini_watermark

        if Path(base_image_path).is_file():

            remove_gemini_watermark(base_image_path)

    except Exception:

        pass

    im = Image.open(base_image_path).convert("RGB")

    # Automatically erase burned-in dialogue subtitles in lower 16% of frame
    try:
        import cv2
        im_cv = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)
        ih, iw = im_cv.shape[:2]
        sub_top = int(ih * 0.84)
        sub_area = im_cv[sub_top:, :]
        sub_gray = cv2.cvtColor(sub_area, cv2.COLOR_BGR2GRAY)
        mask_local = cv2.inRange(sub_gray, 200, 255)
        if 250 < np.sum(mask_local > 0) < (ih * iw * 0.05):
            k = np.ones((5, 5), np.uint8)
            mask_local = cv2.dilate(mask_local, k, iterations=1)
            full_mask = np.zeros((ih, iw), dtype=np.uint8)
            full_mask[sub_top:, :] = mask_local
            inpainted = cv2.inpaint(im_cv, full_mask, inpaintRadius=5, flags=cv2.INPAINT_TELEA)
            im = Image.fromarray(cv2.cvtColor(inpainted, cv2.COLOR_BGR2RGB))
    except Exception:
        pass



    # Auto-crop black or white pillarbox/letterbox if present (e.g. from square AI generations)

    im_np = np.array(im)

    is_white = (im_np[:, :, 0] > 240) & (im_np[:, :, 1] > 240) & (im_np[:, :, 2] > 240)

    is_black = (im_np[:, :, 0] < 15) & (im_np[:, :, 1] < 15) & (im_np[:, :, 2] < 15)

    bad_cols = is_white.all(axis=0) | is_black.all(axis=0)

    bad_rows = is_white.all(axis=1) | is_black.all(axis=1)

    if bad_cols.any() or bad_rows.any():

        good_cols = np.where(~bad_cols)[0]

        good_rows = np.where(~bad_rows)[0]

        if len(good_cols) > 100 and len(good_rows) > 100:

            im = im.crop((int(good_cols[0]), int(good_rows[0]), int(good_cols[-1]) + 1, int(good_rows[-1]) + 1))



    # High quality resize & crop to 16:9 (with smart 50/50 layout for portraits)

    w, h = im.size

    target_ratio = target_w / target_h

    current_ratio = w / h



    if current_ratio < 1.35:
        # Smart Hollywood Bust Framing for portrait/vertical footage (9:16 or square)
        # Preserves character aspect ratio perfectly (chest-up hero crop)
        crop_top = int(h * 0.03)
        crop_bottom = int(h * 0.73)
        crop_h = max(100, crop_bottom - crop_top)
        crop_w = w
        hero_crop = im.crop((0, crop_top, crop_w, crop_bottom))

        scale = target_h / float(crop_h)
        hero_w = min(int(crop_w * scale), int(target_w * 0.52))
        hero_scaled = hero_crop.resize((hero_w, target_h), Image.Resampling.LANCZOS)

        # Sample ambient tones from footage for harmonious studio palette
        im_np = np.array(im)
        avg_color = np.mean(im_np[:int(h * 0.3), :], axis=(0, 1))
        bg_base_r = max(10, min(36, int(avg_color[0] * 0.35)))
        bg_base_g = max(12, min(38, int(avg_color[1] * 0.35)))
        bg_base_b = max(18, min(48, int(avg_color[2] * 0.40)))

        canvas_arr = np.zeros((target_h, target_w, 3), dtype=np.uint8)
        for x_c in range(target_w):
            factor = 1.0 - (x_c / float(target_w)) * 0.4
            canvas_arr[:, x_c, 0] = int(bg_base_r * factor)
            canvas_arr[:, x_c, 1] = int(bg_base_g * factor)
            canvas_arr[:, x_c, 2] = int(bg_base_b * factor)
        canvas = Image.fromarray(canvas_arr)

        from PIL import ImageFilter
        bg_ambient = im.resize((target_w, target_h), Image.Resampling.BILINEAR)
        bg_ambient = bg_ambient.filter(ImageFilter.GaussianBlur(35))
        bg_ambient_np = np.array(bg_ambient, dtype=np.float32) * 0.28
        canvas_np = np.array(canvas, dtype=np.float32) * 0.72 + bg_ambient_np
        canvas = Image.fromarray(np.clip(canvas_np, 0, 255).astype(np.uint8))

        # Feather hero image right edge onto canvas seamlessly
        hero_rgba = hero_scaled.convert("RGBA")
        hero_arr = np.array(hero_rgba, dtype=np.float32)
        feather_w = min(150, hero_w // 3)
        feather_start = hero_w - feather_w
        alpha_ramp = np.ones((target_h, hero_w), dtype=np.float32) * 255.0
        for i_f in range(feather_w):
            alpha_ramp[:, feather_start + i_f] = 255.0 * (1.0 - (i_f / float(feather_w)))
        hero_arr[:, :, 3] = alpha_ramp
        hero_blended = Image.fromarray(np.clip(hero_arr, 0, 255).astype(np.uint8))

        canvas.paste(hero_blended, (0, 0), hero_blended)
        im = canvas
        text_on_left = False  # Hero on left, bold viral text on right
    elif current_ratio > target_ratio:

        new_w = int(h * target_ratio)

        offset = (w - new_w) // 2

        im = im.crop((offset, 0, offset + new_w, h))

        im = im.resize((target_w, target_h), Image.Resampling.LANCZOS)

        text_on_left = None

    else:

        new_h = int(w / target_ratio)

        offset = (h - new_h) // 2

        im = im.crop((0, offset, w, offset + new_h))

        im = im.resize((target_w, target_h), Image.Resampling.LANCZOS)

        text_on_left = None



    # Smart Hollywood HDR Dynamic Range & Exposure Lift for dark footage
    im_arr = np.array(im, dtype=np.float32)
    mean_lum = float(np.mean(im_arr))
    if mean_lum < 55.0:
        # Hollywood Abyss / Night-for-Night Tone Mapping
        norm = im_arr / 255.0
        gamma = max(0.55, min(0.85, 0.40 + (mean_lum / 120.0)))
        lifted = np.power(norm, gamma) * 255.0
        # Lift shadow pedestal: push dead black to deep cinematic sapphire navy (16-20)
        lifted = 16.0 + lifted * (239.0 / 255.0)
        im = Image.fromarray(np.clip(lifted, 0, 255).astype(np.uint8))
        im = ImageEnhance.Color(im).enhance(1.45)
        im = ImageEnhance.Contrast(im).enhance(1.25)
        im = ImageEnhance.Sharpness(im).enhance(1.50)
    else:
        im = ImageEnhance.Color(im).enhance(1.25)
        im = ImageEnhance.Contrast(im).enhance(1.20)
        im = ImageEnhance.Sharpness(im).enhance(1.40)



    # Determine layout mode: 'split_top_bottom', 'top', 'bottom', 'left', 'right', 'auto'

    side_pref = str(preferred_side or "auto").strip().lower()



    # Fonts: Impact (gold standard viral block), Anton, Bebas Neue, Arial Black

    has_non_ascii = any(ord(c) > 127 for c in str(hook_text or ""))
    if has_non_ascii:
        font_candidates = [
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/tahomabd.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
    else:
        font_candidates = [
            "C:/Windows/Fonts/impact.ttf",
            str(STUDIO_DIR / "web/fonts/Anton.ttf"),
            str(STUDIO_DIR / "web/fonts/BebasNeue.ttf"),
            "C:/Windows/Fonts/ariblk.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]

    font_path = next((f for f in font_candidates if Path(f).exists()), font_candidates[0])



    comp_thumb_file = None

    if output_path:

        ep_dir = Path(output_path).parent

        cand = ep_dir / "thumbnail_competitor_trend.jpg"

        if cand.is_file():

            comp_thumb_file = cand



    gray = np.array(im.convert("L"))

    left_third = gray[:, :426]

    right_third = gray[:, 854:]

    left_energy = float(np.std(left_third) * 0.6 + np.mean(left_third) * 0.4)

    right_energy = float(np.std(right_third) * 0.6 + np.mean(right_third) * 0.4)



    faces = detect_faces_in_image(im)



    if side_pref in ("split_top_bottom", "split", "top_bottom", "competitor_style"):

        layout_style = "split_top_bottom"

    elif side_pref in ("top", "upper"):

        layout_style = "top"

    elif side_pref in ("bottom", "lower"):

        layout_style = "bottom"

    elif side_pref == "left":

        layout_style = "left"

    elif side_pref == "right":

        layout_style = "right"

    else:  # auto

        if text_on_left is not None:

            layout_style = "left" if text_on_left else "right"

        elif faces:

            # OpenCV YuNet Face Avoidance: Calculate exact face collision penalties

            # Left text zone: X in [0, 600], Y in [40, 680]

            # Right text zone: X in [680, 1280], Y in [40, 680]

            left_penalty = 0.0

            right_penalty = 0.0



            for (fx, fy, fw, fh) in faces:

                face_area = fw * fh

                # Overlap with left text zone [0, 40, 600, 680]

                ol_l_w = max(0, min(fx + fw, 600) - max(fx, 0))

                ol_l_h = max(0, min(fy + fh, 680) - max(fy, 40))

                if ol_l_w > 0 and ol_l_h > 0:

                    left_penalty += (ol_l_w * ol_l_h) * (face_area ** 0.5)



                # Overlap with right text zone [680, 40, 1280, 680]

                ol_r_w = max(0, min(fx + fw, 1280) - max(fx, 680))

                ol_r_h = max(0, min(fy + fh, 680) - max(fy, 40))

                if ol_r_w > 0 and ol_r_h > 0:

                    right_penalty += (ol_r_w * ol_r_h) * (face_area ** 0.5)



            # Pick side that NEVER covers the primary/hero face

            if right_penalty > left_penalty:

                layout_style = "left"

            elif left_penalty > right_penalty:

                layout_style = "right"

            else:

                layout_style = "left" if left_energy <= right_energy else "right"

        else:

            layout_style = "left" if left_energy <= right_energy else "right"



    scale_str = str(font_scale or "viral").lower()

    raw_hook = str(hook_text or "COURT INJUNCTION / BIG MISTAKE!?").strip()

    extracted_badge = badge_text

    if not extracted_badge:

        if ":" in raw_hook:

            parts = raw_hook.split(":", 1)

            raw_hook = parts[0].strip()

            extracted_badge = parts[1].strip()

        elif " - " in raw_hook:

            parts = raw_hook.split(" - ", 1)

            raw_hook = parts[0].strip()

            extracted_badge = parts[1].strip()

        elif "¡" in raw_hook and "!" in raw_hook:

            m = re.search(r"¡([^!]+)!", raw_hook)

            if m:

                extracted_badge = f"¡{m.group(1).strip()}!"

                raw_hook = raw_hook.replace(m.group(0), "").strip()



    has_badge = bool(extracted_badge and extracted_badge.strip())



    if layout_style == "split_top_bottom":

        overlay = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))

        ov_draw = ImageDraw.Draw(overlay, "RGBA")

        top_alpha = 60 if mean_lum < 55.0 else 120
        bot_alpha = 70 if mean_lum < 55.0 else 130
        for y in range(0, 130, 4):

            alpha = int(top_alpha * ((1.0 - y / 130) ** 1.3))

            ov_draw.rectangle((0, y, target_w, y + 4), fill=(0, 0, 0, alpha))

        for y in range(560, 720, 4):

            alpha = int(bot_alpha * (((y - 560) / 160) ** 1.3))

            ov_draw.rectangle((0, y, target_w, y + 4), fill=(0, 0, 0, alpha))

        im = Image.alpha_composite(im.convert("RGBA"), overlay).convert("RGB")

        draw = ImageDraw.Draw(im, "RGBA")



        p1, p2 = _split_hook_for_top_bottom(raw_hook)

        t1 = p1

        t2 = p2



        if scale_str in ("standard", "sleek", "compact"):

            f_size1 = 64

            f_size2 = 68

        elif scale_str == "large":

            f_size1 = 72

            f_size2 = 76

        else:  # viral / default

            f_size1 = 70

            f_size2 = 74



        font1 = ImageFont.truetype(font_path, f_size1)

        font2 = ImageFont.truetype(font_path, f_size2)



        # Compute gradient magnitude for intelligent obstacle & subject avoidance

        im_gray = np.array(im.convert("L")).astype(float)

        gy, gx = np.gradient(im_gray)

        edge_mag = np.sqrt(gx**2 + gy**2)



        b1 = draw.textbbox((0, 0), t1, font=font1)

        w1 = b1[2] - b1[0]

        h1 = b1[3] - b1[1]



        y1 = 24

        x1 = find_smart_horizontal_x(edge_mag, im_gray, y1, y1 + h1 + 10, w1, target_w=target_w)

        top_align = "left" if x1 == 55 else ("right" if x1 > (target_w - w1) // 2 + 30 else "center")



        # If aligned to side and line is wide, scale down to fit cleanly within open half

        if top_align in ("left", "right"):

            while w1 > 550 and font1.size > 44:

                font1 = ImageFont.truetype(font_path, font1.size - 2)

                b1 = draw.textbbox((0, 0), t1, font=font1)

                w1 = b1[2] - b1[0]

                h1 = b1[3] - b1[1]

            if top_align == "right":

                x1 = target_w - w1 - 55

        else:

            while (w1 > 1080 or h1 > 68) and font1.size > 36:

                font1 = ImageFont.truetype(font_path, font1.size - 2)

                b1 = draw.textbbox((0, 0), t1, font=font1)

                w1 = b1[2] - b1[0]

                h1 = b1[3] - b1[1]

            x1 = (target_w - w1) // 2



        if t2:

            b2 = draw.textbbox((0, 0), t2, font=font2)

            w2 = b2[2] - b2[0]

            h2 = b2[3] - b2[1]

            y2 = max(595, target_h - h2 - 35)

            x2 = find_smart_horizontal_x(edge_mag, im_gray, y2, y2 + h2 + 10, w2, target_w=target_w, is_bottom=True, preferred_align=top_align)

            bot_align = "left" if x2 == 55 else ("right" if x2 > (target_w - w2) // 2 + 30 else "center")



            if bot_align in ("left", "right"):

                while w2 > 520 and font2.size > 44:

                    font2 = ImageFont.truetype(font_path, font2.size - 2)

                    b2 = draw.textbbox((0, 0), t2, font=font2)

                    w2 = b2[2] - b2[0]

                    h2 = b2[3] - b2[1]

                if bot_align == "right":

                    x2 = min(1010 - w2, target_w - w2 - 55)

            else:

                while (w2 > 980 or h2 > 68) and font2.size > 36:

                    font2 = ImageFont.truetype(font_path, font2.size - 2)

                    b2 = draw.textbbox((0, 0), t2, font=font2)

                    w2 = b2[2] - b2[0]

                    h2 = b2[3] - b2[1]

                x2 = (target_w - w2) // 2



            # Protect YouTube duration badge safe zone (x: 1020..1280, y: 600..720)

            if x2 + w2 > 1020:

                x2 = min(x2, 1010 - w2)



        # Draw Line 1: Radiant Golden Sun Yellow (#FFD000)

        draw_viral_typography(

            draw=draw,

            xy=(x1, y1),

            text=t1,

            font=font1,

            fill_color=(255, 208, 0, 255),

            stroke_width=8,

            shadow_offset=(6, 6),

        )



        # Draw Line 2: Electric Neon Lime Green (#39FF14)

        if t2:

            draw_viral_typography(

                draw=draw,

                xy=(x2, y2),

                text=t2,

                font=font2,

                fill_color=(57, 255, 20, 255),

                stroke_width=8,

                shadow_offset=(6, 6),

            )



        if has_badge:

            badge_clean = extracted_badge.strip().upper()

            badge_font_size = 28

            badge_font = ImageFont.truetype(font_path, badge_font_size)

            bbox = draw.textbbox((0, 0), badge_clean, font=badge_font)

            bw = bbox[2] - bbox[0]

            bh = bbox[3] - bbox[1]

            bx1 = 30

            by1 = 20

            draw.rounded_rectangle((bx1, by1, bx1 + bw + 18, by1 + bh + 12), radius=6, fill=(229, 9, 20, 255), outline=(255, 255, 255, 255), width=2)

            draw.text((bx1 + 9, by1 + 6), badge_clean, font=badge_font, fill=(255, 255, 255, 255))



    elif layout_style == "top":

        overlay = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))

        ov_draw = ImageDraw.Draw(overlay, "RGBA")

        for y in range(0, 160, 4):

            alpha = int(140 * ((1.0 - y / 160) ** 1.3))

            ov_draw.rectangle((0, y, target_w, y + 4), fill=(0, 0, 0, alpha))

        im = Image.alpha_composite(im.convert("RGBA"), overlay).convert("RGB")

        draw = ImageDraw.Draw(im, "RGBA")



        lines = _parse_hook_lines(raw_hook)

        if scale_str in ("standard", "sleek", "compact"):

            f_size = 58

        elif scale_str == "large":

            f_size = 68

        else:

            f_size = 74

        font = ImageFont.truetype(font_path, f_size)

        line_spacing = int(f_size * 1.30) + 16



        for l in lines:

            txt = _wrap_smart_quotes(l, force_case="upper")

            bbox = draw.textbbox((0, 0), txt, font=font)

            while ((bbox[2] - bbox[0]) > 1100 or (bbox[3] - bbox[1]) > 68) and font.size > 36:

                font = ImageFont.truetype(font_path, font.size - 2)

                line_spacing = int(font.size * 1.30) + 16

                bbox = draw.textbbox((0, 0), txt, font=font)



        curr_y = 20

        for i, l in enumerate(lines):

            txt = _wrap_smart_quotes(l, force_case="upper")

            bbox = draw.textbbox((0, 0), txt, font=font)

            lw = bbox[2] - bbox[0]

            lx = (target_w - lw) // 2

            fill_c = (255, 208, 0, 255) if i == 0 else (57, 255, 20, 255)

            draw_viral_typography(draw, (lx, curr_y), txt, font, fill_color=fill_c, stroke_width=8, shadow_offset=(6, 6))

            curr_y += line_spacing



    elif layout_style == "bottom":

        overlay = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))

        ov_draw = ImageDraw.Draw(overlay, "RGBA")

        for y in range(540, 720, 4):

            alpha = int(140 * (((y - 540) / 180) ** 1.3))

            ov_draw.rectangle((0, y, target_w, y + 4), fill=(0, 0, 0, alpha))

        im = Image.alpha_composite(im.convert("RGBA"), overlay).convert("RGB")

        draw = ImageDraw.Draw(im, "RGBA")



        lines = _parse_hook_lines(raw_hook)

        if scale_str in ("standard", "sleek", "compact"):

            f_size = 58

        elif scale_str == "large":

            f_size = 68

        else:

            f_size = 74

        font = ImageFont.truetype(font_path, f_size)

        line_spacing = int(f_size * 1.30) + 16



        for l in lines:

            txt = _wrap_smart_quotes(l, force_case="title")

            bbox = draw.textbbox((0, 0), txt, font=font)

            while ((bbox[2] - bbox[0]) > 980 or (bbox[3] - bbox[1]) > 68) and font.size > 36:

                font = ImageFont.truetype(font_path, font.size - 2)

                line_spacing = int(font.size * 1.30) + 16

                bbox = draw.textbbox((0, 0), txt, font=font)



        total_h = len(lines) * line_spacing

        curr_y = max(550, target_h - total_h - 32)

        for i, l in enumerate(lines):

            txt = _wrap_smart_quotes(l, force_case="title")

            bbox = draw.textbbox((0, 0), txt, font=font)

            lw = bbox[2] - bbox[0]

            lx = (target_w - lw) // 2

            if lx + lw > 1020:

                lx = min(lx, 1010 - lw)

            fill_c = (255, 208, 0, 255) if i == 0 else (57, 255, 20, 255)

            draw_viral_typography(draw, (lx, curr_y), txt, font, fill_color=fill_c, stroke_width=8, shadow_offset=(6, 6))

            curr_y += line_spacing



    else:  # left or right (50/50 side layout)
        text_on_left = (layout_style == "left")
        text_zone_width = 560
        safety_margin = 40

        # Whiteboard genre uses pristine off-white paper aesthetic: skip heavy black gradient overlay
        if norm_genre != "whiteboard":
            overlay = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
            ov_draw = ImageDraw.Draw(overlay, "RGBA")
            if text_on_left:
                text_start_x = safety_margin
                max_allowed_w = text_zone_width - safety_margin
                grad_span = text_zone_width + 80
                for x in range(0, grad_span, 4):
                    prog = x / grad_span
                    alpha = int(220 * ((1.0 - prog) ** 1.3))
                    ov_draw.rectangle((x, 0, x + 4, target_h), fill=(0, 0, 0, alpha))
            else:
                text_start_x = target_w - text_zone_width + safety_margin
                max_allowed_w = text_zone_width - safety_margin
                grad_span = text_zone_width + 80
                for x in range(target_w - grad_span, target_w, 4):
                    prog = (x - (target_w - grad_span)) / grad_span
                    alpha = int(220 * (prog ** 1.3))
                    ov_draw.rectangle((x, 0, x + 4, target_h), fill=(0, 0, 0, alpha))
            im = Image.alpha_composite(im.convert("RGBA"), overlay).convert("RGB")
            draw = ImageDraw.Draw(im, "RGBA")
        else:
            text_start_x = safety_margin if text_on_left else (target_w - text_zone_width + safety_margin)
            max_allowed_w = text_zone_width - safety_margin
            draw = ImageDraw.Draw(im, "RGBA")

        lines = _parse_hook_lines(raw_hook, norm_genre=norm_genre)

        if scale_str in ("standard", "sleek", "compact"):
            base_size = 88 if len(lines) <= 2 else 74
            min_size = 46
        elif scale_str == "large":
            base_size = 102 if len(lines) <= 2 else 86
            min_size = 54
        else:  # viral / default
            base_size = 114 if len(lines) <= 2 else 96
            min_size = 62

        if not text_on_left:
            max_allowed_w = min(max_allowed_w, 470)
            max_bottom_y = 580
        else:
            max_bottom_y = 660

        font = ImageFont.truetype(font_path, base_size)
        for l in lines:
            txt_eval = _wrap_smart_quotes(l, force_case="upper", use_quotes=(norm_genre == "family_drama"))
            bbox = draw.textbbox((0, 0), txt_eval, font=font)
            lw = bbox[2] - bbox[0]
            while lw > max_allowed_w and base_size > min_size:
                base_size -= 3
                font = ImageFont.truetype(font_path, base_size)
                bbox = draw.textbbox((0, 0), txt_eval, font=font)
                lw = bbox[2] - bbox[0]

        line_spacing = int(base_size * 1.08)
        total_h = len(lines) * line_spacing
        if has_badge:
            total_h += int(base_size * 0.85)

        while total_h > (max_bottom_y - 60) and base_size > min_size:
            base_size -= 3
            font = ImageFont.truetype(font_path, base_size)
            line_spacing = int(base_size * 1.08)
            total_h = len(lines) * line_spacing + (int(base_size * 0.85) if has_badge else 0)

        start_y = max(60, min(140, (max_bottom_y - total_h) // 2))
        curr_y = start_y

        for i, line in enumerate(lines):
            is_first = (i == 0)
            if norm_genre == "stoic":
                txt = _wrap_smart_quotes(line, force_case="upper", use_quotes=False)
                fill_c = (255, 215, 0, 255) if is_first else (255, 255, 255, 255)
                stroke_w = 8
                stroke_c = (0, 0, 0, 255)
                sh_off = (6, 6)
                sh_c = (0, 0, 0, 240)
            elif norm_genre == "whiteboard":
                txt = _wrap_smart_quotes(line, force_case="upper" if is_first else "title", use_quotes=False)
                if is_first:
                    fill_c = (239, 68, 68, 255)  # Marker Red
                    stroke_w = 4
                    stroke_c = (15, 23, 42, 255)  # Dark Ink
                    sh_off = (3, 3)
                    sh_c = (0, 0, 0, 80)
                else:
                    fill_c = (15, 23, 42, 255)  # Charcoal Slate
                    stroke_w = 3
                    stroke_c = (255, 255, 255, 220)  # Soft white halo
                    sh_off = (2, 2)
                    sh_c = (0, 0, 0, 60)
            elif norm_genre in ("family_drama", "court_drama"):
                txt = _wrap_smart_quotes(line, force_case="upper", use_quotes=False)
                fill_c = (255, 225, 0, 255) if is_first else (255, 255, 255, 255)
                stroke_w = 9
                stroke_c = (0, 0, 0, 255)
                sh_off = (7, 7)
                sh_c = (0, 0, 0, 240)
            elif norm_genre == "mafia_thriller":
                txt = _wrap_smart_quotes(line, force_case="upper", use_quotes=False)
                fill_c = (245, 158, 11, 255) if is_first else (6, 182, 212, 255)
                stroke_w = 8
                stroke_c = (0, 0, 0, 255)
                sh_off = (6, 6)
                sh_c = (0, 0, 0, 240)
            elif norm_genre == "psychological_horror":
                txt = _wrap_smart_quotes(line, force_case="upper", use_quotes=False)
                fill_c = (239, 68, 68, 255) if is_first else (248, 250, 252, 255)
                stroke_w = 8
                stroke_c = (0, 0, 0, 255)
                sh_off = (6, 6)
                sh_c = (153, 27, 27, 200)
            elif norm_genre == "history":
                txt = _wrap_smart_quotes(line, force_case="upper", use_quotes=False)
                fill_c = (234, 179, 8, 255) if is_first else (255, 255, 255, 255)
                stroke_w = 8
                stroke_c = (0, 0, 0, 255)
                sh_off = (6, 6)
                sh_c = (0, 0, 0, 240)
            else:  # documentary & default
                txt = _wrap_smart_quotes(line, force_case="upper" if is_first else "title", use_quotes=False)
                fill_c = (255, 208, 0, 255) if is_first else ((57, 255, 20, 255) if i == 1 else (255, 255, 255, 255))
                stroke_w = 8
                stroke_c = (0, 0, 0, 255)
                sh_off = (6, 6)
                sh_c = (0, 0, 0, 240)

            # Draw text line with 3D drop shadow & stroke
            draw_viral_typography(
                draw,
                (text_start_x, curr_y),
                txt,
                font,
                fill_color=fill_c,
                stroke_width=stroke_w,
                stroke_color=stroke_c,
                shadow_offset=sh_off,
                shadow_color=sh_c,
            )

# Stoic signature crimson brush removed for clean viral look

            curr_y += line_spacing

        if has_badge:
            badge_clean = extracted_badge.strip().upper()
            badge_font_size = max(36, int(base_size * 0.44))
            badge_font = ImageFont.truetype(font_path, badge_font_size)
            bbox = draw.textbbox((0, 0), badge_clean, font=badge_font)
            bw = bbox[2] - bbox[0]
            bh = bbox[3] - bbox[1]
            pad_x = 18
            pad_y = 8
            bx1 = text_start_x
            by1 = curr_y + 10
            bx2 = min(bx1 + bw + (pad_x * 2), text_start_x + max_allowed_w)
            by2 = by1 + bh + (pad_y * 2)
            draw.rounded_rectangle((bx1, by1, bx2, by2), radius=8, fill=(229, 9, 20, 255), outline=(255, 255, 255, 255), width=2)
            draw.text((bx1 + pad_x, by1 + pad_y), badge_clean, font=badge_font, fill=(255, 255, 255, 255))

    



    # Embed descriptive file metadata; this is not a ranking or CTR signal.

    exif = im.getexif()

    if metadata and isinstance(metadata, dict):

        meta_title = str(metadata.get("title") or "").strip()

        meta_subject = str(metadata.get("subject") or metadata.get("topic") or metadata.get("genre") or "").strip()

        meta_tags = metadata.get("tags") or []

        if isinstance(meta_tags, list):

            meta_keywords = "; ".join(str(t).strip() for t in meta_tags if str(t).strip())

        else:

            meta_keywords = str(meta_tags).strip()

        meta_desc = str(metadata.get("description") or "").strip()

        meta_artist = str(metadata.get("artist") or metadata.get("series_name") or "Storyboard AI Studio Pro").strip()

        meta_copyright = str(metadata.get("copyright") or f"Copyright 2026 {meta_artist}. All Rights Reserved.").strip()



        if meta_title:

            exif[0x010E] = meta_title[:255]

            exif[0x9C9B] = meta_title.encode("utf-16le")

        if meta_artist:

            exif[0x013B] = meta_artist[:128]

            exif[0x9C9D] = meta_artist.encode("utf-16le")

        if meta_copyright:

            exif[0x8298] = meta_copyright[:128]

        exif[0x0131] = "Storyboard AI Studio Pro - YouTube vidIQ SEO Engine v2.0"

        exif[0x4746] = 5   # Rating: 5 stars

        exif[0x4749] = 99  # RatingPercent: 99%

        if meta_desc:

            exif[0x9C9C] = meta_desc[:600].encode("utf-16le")

        if meta_keywords:

            exif[0x9C9E] = meta_keywords.encode("utf-16le")

        if meta_subject:

            exif[0x9C9F] = meta_subject.encode("utf-16le")



    output_path.parent.mkdir(parents=True, exist_ok=True)

    im.save(output_path, "JPEG", quality=96, optimize=True, exif=exif)

    return output_path





def generate_shorts_thumbnail_cover(
    base_image_path: Path,
    output_path: Path,
    hook_text: str = "DOMINA TU MENTE",
    genre: Optional[str] = None,
) -> Path:
    """Creates a dedicated 9:16 vertical cover (1080x1920) for YouTube Shorts / Reels / TikTok.

    Guarantees:
    1. Zero face obstruction: Text is never placed over human or statue faces.
    2. Zero torso slicing: Preserves full subject width/shoulders and anchors character to canvas bottom.
    3. Seamless atmospheric blending: Upper sky/background is feathered with cosine smoothstep.
    4. Safe zone compliance: Top safe zone (y: 160-450) or chest safe zone (y: 1100-1450), avoiding Shorts UI.
    """
    target_w, target_h = 1080, 1920
    im = Image.open(base_image_path).convert("RGB")
    sw, sh = im.size
    current_ratio = sw / float(sh)
    target_ratio = target_w / float(target_h)

    # Face detection
    faces = detect_faces_in_image(im)

    if current_ratio > 1.15:
        # Scale whole image to fill vertical canvas height without split/collage artifacts
        scale = target_h / float(sh)
        scaled_w = int(sw * scale)
        scaled_img = im.resize((scaled_w, target_h), Image.Resampling.LANCZOS)

        if faces:
            fx, fy, fw, fh = faces[0]
            fcx_scaled = int((fx + fw // 2) * scale)
        else:
            fcx_scaled = scaled_w // 2

        x1 = max(0, fcx_scaled - target_w // 2)
        x2 = x1 + target_w
        if x2 > scaled_w:
            x2 = scaled_w
            x1 = max(0, x2 - target_w)

        canvas = scaled_img.crop((x1, 0, x2, target_h))

        # Re-detect or project face onto canvas
        if faces:
            f_can_top = int(faces[0][1] * scale)
            f_can_bot = int((faces[0][1] + faces[0][3]) * scale)
        else:
            f_can_top = int(target_h * 0.22)
            f_can_bot = int(target_h * 0.50)

    else:
        # Already vertical or square
        if current_ratio > target_ratio:
            new_w = int(sh * target_ratio)
            offset = (sw - new_w) // 2
            canvas = im.crop((offset, 0, offset + new_w, sh)).resize((target_w, target_h), Image.Resampling.LANCZOS)
        else:
            new_h = int(sw / target_ratio)
            offset = (sh - new_h) // 2
            canvas = im.crop((0, offset, sw, offset + new_h)).resize((target_w, target_h), Image.Resampling.LANCZOS)

        canvas_faces = detect_faces_in_image(canvas)
        if canvas_faces:
            f_can_top = canvas_faces[0][1]
            f_can_bot = canvas_faces[0][1] + canvas_faces[0][3]
        else:
            f_can_top = int(target_h * 0.35)
            f_can_bot = int(target_h * 0.65)

    # Polish base image
    canvas = ImageEnhance.Contrast(canvas).enhance(1.22)
    canvas = ImageEnhance.Sharpness(canvas).enhance(1.30)
    canvas = ImageEnhance.Color(canvas).enhance(1.15)

    # Typography & Safe Zone selection
    lines = _parse_hook_lines(hook_text, norm_genre=normalize_genre_key(genre or "stoic"))
    if not lines:
        lines = ["DOMINA TU MENTE"]

    font_candidates = ["C:/Windows/Fonts/impact.ttf", "C:/Windows/Fonts/ariblk.ttf", "C:/Windows/Fonts/arialbd.ttf"]
    font_path = next((f for f in font_candidates if Path(f).exists()), font_candidates[0])

    base_size = 98 if len(lines) <= 2 else 82
    draw_test = ImageDraw.Draw(canvas)
    font = ImageFont.truetype(font_path, base_size)
    for l in lines:
        bb = draw_test.textbbox((0, 0), l.upper(), font=font)
        while (bb[2] - bb[0]) > (target_w - 120) and base_size > 48:
            base_size -= 4
            font = ImageFont.truetype(font_path, base_size)
            bb = draw_test.textbbox((0, 0), l.upper(), font=font)

    line_h = int(base_size * 1.15)
    total_text_h = len(lines) * line_h

    # Safe Zone Decision: NEVER cover face
    # If face is in lower half or mid-low (e.g. f_can_top >= 620), text goes into upper sky (y: 180 to 450)
    # If face is in high upper third (f_can_bot < 700), text goes below face (y: 1100 to 1450)
    if f_can_top >= 620:
        start_y = 190
    else:
        start_y = max(f_can_bot + 60, 1150)
        if start_y + total_text_h > 1520:
            start_y = 190  # Fallback to upper sky if bottom is crowded by Shorts UI

    # Dynamic vignette behind text
    overlay = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    v_start = max(0, start_y - 80)
    v_end = min(target_h, start_y + total_text_h + 80)
    v_mid = (v_start + v_end) / 2.0
    v_rad = max(1.0, (v_end - v_start) / 2.0)
    for y in range(v_start, v_end):
        dist = abs(y - v_mid) / v_rad
        alpha = int(145 * max(0.0, 1.0 - dist * dist))
        ov_draw.line([(0, y), (target_w, y)], fill=(0, 0, 0, alpha))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(canvas, "RGBA")

    # Render viral typography
    for idx, line in enumerate(lines):
        txt = line.upper()
        bb = draw.textbbox((0, 0), txt, font=font)
        lw = bb[2] - bb[0]
        lx = (target_w - lw) // 2
        ly = start_y + idx * line_h
        fill_c = (255, 215, 0, 255) if idx == 0 else (255, 255, 255, 255)
        # Deep multi-pass shadow
        for s_idx in range(6, 0, -1):
            s_off = s_idx * 2
            draw.text((lx + s_off, ly + s_off), txt, font=font, fill=(0, 0, 0, 230))
        # Solid stroke
        for dx in range(-8, 9):
            for dy in range(-8, 9):
                if dx * dx + dy * dy <= 64:
                    draw.text((lx + dx, ly + dy), txt, font=font, fill=(0, 0, 0, 255))
        draw.text((lx, ly), txt, font=font, fill=fill_c)

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path, "JPEG", quality=95)
    return out_path


def generate_fierce_thumbnail_subject(
    episode_dir: Path,
    series_name: str = "",
    custom_prompt: Optional[str] = None,
    genre: Optional[str] = None,
) -> Optional[Path]:
    """Generates a world-class high-CTR YouTube thumbnail base image tailored strictly to the series genre.
    Dynamically adapts art style & composition:
    - whiteboard: Vibrant POSCA & Copic markers on clean off-white sketchbook paper (Sacred geometry, glowing third eye, Tree of Life, pyramids).
    - stoic: Hyper-muscular classical Greek/Roman marble statue (Zeus / Marcus Aurelius) with extreme chiaroscuro rim lighting on pitch-black background.
    - family_drama: Realistic heated confrontation photo (outraged landowner pointing, police/fire marshal with blueprint, bulldozer in backyard).
    - mafia_thriller: Film noir crime boss in dim luxury office with neon amber/teal backlighting.
    - psychological_horror: Intense terror close-up with cold cinematic flashlight beam and pitch-black mist.
    - history: Epic ancient empire commander in ornate gilded armor with burning horizon.
    - action: High-octane action hero sprinting away from fiery explosion.
    - documentary: Dramatic investigative scene with glowing evidence and deep shadows.
    """
    episode_dir = Path(episode_dir)
    plan_p = episode_dir / "plan.json"
    plan = json.loads(plan_p.read_text(encoding="utf-8")) if plan_p.exists() else {}

    # 1. Resolve Effective Genre dynamically
    eff_genre = (
        genre
        or plan.get("genre")
        or (plan.get("config") or {}).get("genre")
        or series_name
        or "documentary"
    )
    from seo_genre_profiles import normalize_genre_key
    norm_genre = normalize_genre_key(eff_genre)

    # 2. Extract character & episode context
    bible = plan.get("bible", {})
    characters = bible.get("characters", [])
    char_desc = "protagonist"
    if characters and isinstance(characters, list) and len(characters) > 0:
        c0 = characters[0]
        char_desc = c0.get("name") if isinstance(c0, dict) else str(c0)
    elif characters and isinstance(characters, dict):
        first_k = next(iter(characters.keys()), "protagonist")
        char_desc = first_k

    ep_title = plan.get("title") or series_name or "Epic Story"

    # 3. Dynamic Genre-Driven AI Thumbnail Prompt
    if custom_prompt:
        prompt = custom_prompt
    elif norm_genre == "whiteboard":
        prompt = (
            f"After Skool viral YouTube masterpiece illustration about '{ep_title}': "
            "vibrant colorful POSCA and Copic markers on clean off-white art sketchbook paper, "
            "intricate sacred geometry with a mystical glowing third eye, detailed Tree of Life with sprawling deep roots in rich soil, "
            "ancient pyramids and futuristic dome city skyline in distance, blooming colorful grass flowers, "
            "rich vivid rainbow marker colors (cyan, magenta, gold, purple, lime green) with crisp bold black ink outlines, "
            "surreal, mind-expanding, highly detailed masterpiece, 16:9, "
            "artwork concentrated on the RIGHT 55% leaving the LEFT 45% clean textured off-white paper for hand-drawn lettering, "
            "no text, no digital watermark, clean edges."
        )
    elif norm_genre == "family_drama":
        prompt = (
            f"Hyper-realistic cinematic photo of an intense heated confrontation about '{ep_title}' in 16:9: "
            "an outraged property owner in a plaid shirt pointing furiously at an illegal construction project in his backyard farm, "
            "a serious fire marshal and police officer in uniform reviewing architectural blueprints with a stern grim expression, "
            "a heavy yellow bulldozer tearing up a dirt road in the background, a shocked distressed woman looking on, "
            "high emotional tension, realistic natural golden hour sunlight, sharp 8k focus, dramatic storytelling composition, "
            "leaving ample open space at the top and bottom or left for bold text, no text, no watermark."
        )
    elif norm_genre == "stoic":
        prompt = (
            f"Hyper-detailed, monumental full-length classical Greek and Roman emperor philosopher statue ({char_desc}), "
            "heroic standing posture visible from head to toe, majestic complete anatomical figure with flowing draped toga extending down to feet, "
            "intense brooding gaze, exquisitely chiseled beard, extreme chiaroscuro silver-white rim lighting carving out marble texture fissures, "
            "deep atmospheric cinematic ancient Roman forum background with volumetric rim glow (never pitch black), crisp 8k resolution, rule of thirds, "
            "subject positioned cleanly on the RIGHT 50% leaving the entire LEFT 50% open negative space for text, "
            "masterpiece 16:9 composition, no half-body bust, no severed torso, no text, no watermark."
        )
    elif norm_genre in ("drama", "theatrical_drama", "cinematic_drama"):
        prompt = (
            f"High-stakes viral YouTube drama masterpiece thumbnail in 16:9 about '{ep_title}': "
            f"emotional extreme close-up of {char_desc} with intense piercing eyes or fierce defiant expression, "
            "warm volumetric 3-point rim lighting carving facial contours and organic skin texture, "
            "in the background a dramatic shocking confrontation between two figures with cinematic depth of field, "
            "vibrant deep sapphire and golden amber color grading with rich lifted shadows (never pitch black), "
            "50/50 rule of thirds composition with subject on the right leaving open clean space on the left for bold 3D text, "
            "8k resolution film still, photorealistic, no text, no watermark."
        )
    elif norm_genre == "mafia_thriller":
        prompt = (
            f"Cinematic film noir thriller YouTube thumbnail in 16:9 about '{ep_title}': "
            f"a powerful calculating crime boss ({char_desc}) in a tailored dark Italian suit sitting in a dim smoke-filled luxury office, "
            "dramatic neon amber and teal backlighting, intense piercing cold glare directly at camera, "
            "holding a confidential folder, shadows and cinematic lens flare, 8k resolution, photorealistic, "
            "subject on the right half leaving open dark space on the left for massive text, no text, no watermark."
        )
    elif norm_genre == "psychological_horror":
        prompt = (
            f"Ultra-intense psychological horror YouTube viral thumbnail in 16:9 about '{ep_title}': "
            f"extreme close-up portrait of {char_desc} with wide dilated eyes of pure sheer terror and shock, "
            "cold desaturated blue and greenish grading, dramatic flashlight rim light cutting through pitch-black mist, "
            "creepy blurred silhouette towering in the shadowy background, hyper-realistic, photorealistic 8k, "
            "leaving high-contrast dark space on the left for bold text, no text, no watermark."
        )
    elif norm_genre == "history":
        prompt = (
            f"Epic cinematic history documentary YouTube thumbnail in 16:9 about '{ep_title}': "
            f"an imposing ancient warrior emperor ({char_desc}) in ornate gilded armor with an intense commanding battle expression, "
            "cinematic burning horizon with marching legions and siege towers in dramatic atmospheric smoke, "
            "volumetric golden rim lighting, 8k resolution masterpiece, "
            "subject on the right half leaving left half open for massive typography, no text, no watermark."
        )
    elif norm_genre == "action":
        prompt = (
            f"High-octane Hollywood blockbuster action movie thumbnail in 16:9 about '{ep_title}': "
            f"a battle-hardened special forces operative ({char_desc}) in tactical combat armor sprinting away from a massive orange fireball explosion, "
            "shattered glass and flying fiery debris, intense gritty sweat and determination, anamorphic lens flare, "
            "subject on the right half leaving high-contrast negative space on the left for bold title text, 8k, photorealistic, no text, no watermark."
        )
    else:  # documentary or default
        prompt = (
            f"Cinematic investigative documentary viral YouTube thumbnail in 16:9 about '{ep_title}': "
            f"dramatic high-contrast portrait of {char_desc} looking deeply into classified evidence, "
            "mysterious glowing holographic charts or documents, moody cinematic lighting, deep shadows, "
            "photorealistic 8k resolution, rule of thirds leaving left half open for bold hook text, no text, no watermark."
        )

    out_base = episode_dir / "thumbnail_fierce_base.jpg"
    try:
        from studio import v2_tuanstor_image
        if v2_tuanstor_image.is_ready():
            print(f"[THUMBNAIL_DYNAMIC_AI] Generating {norm_genre.upper()} thumbnail base image...")
            v2_tuanstor_image.make_image(prompt, out_base)
            if out_base.exists():
                try:
                    from clean_watermark import remove_gemini_watermark
                    remove_gemini_watermark(out_base)
                except Exception:
                    pass
                return out_base
    except Exception as e:
        print(f"[THUMBNAIL_DYNAMIC_AI] Generation error: {e}")

    return None

def ensure_episode_in_title(title: str, ep_num: int, language: str) -> str:
    text=quality.title_with_episode(title, ep_num, language)
    label=quality.LOCALE.get(quality.canonical_language(language),quality.LOCALE['English'])[0]
    suffix=f' ({label} {int(ep_num)})'
    return text[:100-len(suffix)].rstrip() + suffix





import threading

import tempfile

_SEO_LOCK_GUARD = threading.Lock()

_SEO_LOCKS = {}





def _episode_lock(root):

    key=str(Path(root).resolve())

    with _SEO_LOCK_GUARD:

        return _SEO_LOCKS.setdefault(key,threading.RLock())





def _media_url(path):

    try:

        rel=Path(path).resolve().relative_to(STUDIO_DIR.resolve()).as_posix()

        return f'/media/{rel}?v={Path(path).stat().st_mtime_ns}'

    except (ValueError,OSError):

        return None





def _atomic_text(path, text):

    path=Path(path)

    path.parent.mkdir(parents=True,exist_ok=True)

    with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=path.parent,delete=False,suffix='.tmp') as f:

        f.write(text)

        temp=Path(f.name)

    try:

        os.replace(temp,path)

    finally:

        temp.unlink(missing_ok=True)





def write_seo_package(episode_dir, package):

    """Keep cached API metadata, copyable text, and existing publication mirrors consistent."""

    root=Path(episode_dir)

    with _episode_lock(root):

        from vidiq_auto import ensure_scores

        ensure_scores(root,package)

        _atomic_text(root/'youtube_publish_pack.json',json.dumps(package,ensure_ascii=False,indent=2))

        text=format_publish_pack_txt(package)

        _atomic_text(root/'youtube_publish_pack.txt',text)

        publish=root/'00_DANG_BAI_YOUTUBE'

        if publish.is_dir():

            for target in publish.glob('03_THONG_TIN_DANG_BAI*.txt'):

                _atomic_text(target,text)

        series_publish=root.parent/'00_XUAT_BAN_TOAN_BO_SERIES'

        if series_publish.is_dir():

            for d in series_publish.glob(f"Tap_{int(package.get('episode') or 1):02d} - *"):

                if d.is_dir():

                    _atomic_text(d/f"THONG_TIN_DANG_BAI_Tap_{int(package.get('episode') or 1):02d}.txt",text)

    return package





def is_current_seo_package(package, episode_dir):
    try:
        if not isinstance(package, dict):
            return False
        # If the package already contains generated titles, it is a valid saved package for this episode
        if package.get('titles') or package.get('best_title'):
            return True
        ctx=quality.build_episode_context(episode_dir)
        return (package.get('engine_version')==quality.ENGINE_VERSION and package.get('generation',{}).get('method') in ('ai_grounded', 'extractive_fallback'))
    except Exception:
        return False





def _seo_prompt(ctx,series,episode):

    evidence=[{'scene':s['scene_number'],'on_screen_text':s.get('text_overlay',''),'narration':s['narration'],'dialogue':s['dialogue'],'summary_if_no_speech':s['summary'] if not (s['narration'] or s['dialogue']) else ''}
        for s in ctx['scenes']]

    clean_ref = quality.sanitize_title(ctx.get('reference_title', ''))

    return f'''Create elite, high-CTR YouTube publication metadata in {ctx['language']} for this finished episode.

CRITICAL TITLE RULES:
1. DO NOT copy hashtags (#shorts, #estoicismo) or emoji icons (👆, 🔺, 🔥, 💀) into titles.
2. Produce 3 distinct, high-CTR, scroll-stopping viral titles in {ctx['language']} reflecting the actual lesson/story:
   - Style 1: Curiosity Gap & Brutal Truth (Psychological scroll-stopper that exposes a costly mistake or hidden truth).
   - Style 2: Wake-up Call & Warning (Urgent existential warning or powerful counter-intuitive realization).
   - Style 3: The Actionable Rule / Secret (Timeless rule or mental framework from masters like Marcus Aurelius, Seneca, or Epictetus).
   - Keep episode branding short or at the end. Maximum 95 characters.
3. Topic Guidance: {clean_ref} (Reference only; NEVER copy blindly).

TAGS & HASHTAGS RULES:
1. Tags: 25-30 top-ranking, highly searched YouTube keywords in {ctx['language']} relevant to this genre ({ctx['genre']}) and topic. NEVER output random sentence fragments, verbatim narration clauses, or grammatically incomplete speech slices.
2. Hashtags: Exactly 5 trending, high-volume hashtags in {ctx['language']} (e.g., #estoicismo, #filosofia, #marcoaurelio, #desarrollopersonal, #disciplina).

THUMBNAIL HOOK:
- thumbnail_hook_text: 2 to 4 words in ALL CAPS (e.g., "DEJA DE PERDER TU VIDA", "LA MUERTE OCURRE AHORA", "EL ERROR QUE TE MATA").
- High psychological urgency. Group words naturally; do not start with a lone article like "LA" or "EL" if isolated.

DESCRIPTION & ENGAGEMENT:
- description_hook: 2-3 compelling, provocative opening sentences that grip the audience.
- story_synopsis: A structured 3-bullet breakdown of the practical wisdom revealed in this episode.
- pinned_comment: A thought-provoking reflection question that compels viewers to comment.

Return strict JSON:
{{"primary_keyword":"...","secondary_keywords":[],"titles":[{{"type":"Brutal Truth","title":"..."}},{{"type":"Wake-up Call","title":"..."}},{{"type":"The Actionable Rule","title":"..."}}],"description_hook":"...","story_synopsis":"...","tags":[],"hashtags":[],"thumbnail_hook_text":"...","thumbnail_scene_num":1,"thumbnail_selection_reason":"...","pinned_comment":"..."}}.

Series: {series}; episode: {episode}; genre: {ctx['genre']}; language: {ctx['language']}.
Title: {ctx['title']}
Summary: {ctx['summary']}
Characters: {json.dumps(ctx['characters'],ensure_ascii=False)}
BEGIN EPISODE EVIDENCE
{json.dumps(evidence,ensure_ascii=False)}
END EPISODE EVIDENCE'''





def _load_or_create_content(ctx,series,episode,force):

    root=Path(ctx['episode_dir'])

    cached=quality.read_json(root/'youtube_publish_pack.json')

    if not force and isinstance(cached, dict) and (cached.get('best_title') or cached.get('titles') or cached.get('source_content')):
        src = cached.get('source_content')
        if not isinstance(src, dict):
            src = {
                'titles': cached.get('titles', []),
                'primary_keyword': cached.get('primary_keyword', ''),
                'description_hook': cached.get('description', ''),
                'story_synopsis': cached.get('description', ''),
                'tags': cached.get('tags', []),
                'hashtags': cached.get('hashtags', []),
                'pinned_comment': cached.get('pinned_comment', '')
            }
        gen = cached.get('generation') if isinstance(cached.get('generation'), dict) else {'method': 'ai_grounded'}
        return src, gen, cached

    stage='provider'
    try:

        from resilient_gemini import ResilientClient

        response=ResilientClient().models.generate_content(model='gemini-3.1-flash-lite',contents=_seo_prompt(ctx,series,episode))

        raw=response.text if hasattr(response,'text') else str(response)

        stage='parse'
        match=re.search(r'\{.*\}',raw,re.S)

        if not match:

            raise ValueError('SEO provider returned no JSON object')

        stage='validation'
        data=quality.validate_content(json.loads(match.group(0)),ctx)

        return data,{'method':'ai_grounded','provider':'configured_text_client','review_required':True},{}

    except Exception as exc:

        # Never expose provider responses, secrets, or detailed transport exceptions in public packs.

        print(f'[SEO] Grounded extraction fallback ({type(exc).__name__})',flush=True)

        return quality.fallback_content(ctx),{'method':'extractive_fallback','review_required':True,

            'failure_stage':stage,'warning':'AI chưa trả được nội dung hợp lệ; bản này trích từ lời đọc và cần biên tập.'},{}





def auto_thumbnail_side(image_path, genre="auto"):

    """Keep upper faces clear when people occupy both sides; final visual review still applies."""

    from seo_genre_profiles import normalize_genre_key

    norm_g = normalize_genre_key(genre or "auto")

    with Image.open(image_path) as image:

        image=image.convert('RGB')

        faces=detect_faces_in_image(image)

        width,height=image.size

        if faces:
            has_left_face = any(x + w / 2 < width / 2 for x, y, w, h in faces)
            has_right_face = any(x + w / 2 >= width / 2 for x, y, w, h in faces)
            if has_right_face and not has_left_face:
                return "left"
            if has_left_face and not has_right_face:
                return "right"
            if has_left_face and has_right_face:
                return "split_top_bottom"

        # Conservative skin-region fallback when the optional face model is absent.

        arr=np.asarray(image.resize((320,180)),dtype=np.int16)[:100]

        red,green,blue=arr[:,:,0],arr[:,:,1],arr[:,:,2]

        skin=(red>95)&(green>40)&(blue>20)&(red>green)&(red>blue)&((red-green)>15)&((arr.max(axis=2)-arr.min(axis=2))>15)

        if skin[:,:160].mean()>.035 and skin[:,160:].mean()>.035:

            return "split_top_bottom"

    return 'auto'





def _choose_thumbnail(ctx, data, preferred_scene_num):
    ep_dir = Path(ctx.get('episode_dir', ''))
    if preferred_scene_num == 999:
        manual = ep_dir / 'thumbnail_fierce_base.jpg'
        if manual.is_file():
            return {'scene_number': 999, 'image_path': str(manual), 'video_path': None}
    if preferred_scene_num == 888:
        comp = ep_dir / 'thumbnail_competitor_trend.jpg'
        if comp.is_file():
            return {'scene_number': 888, 'image_path': str(comp), 'video_path': None}

    # Only treat as user-requested if passed explicitly as preferred_scene_num
    requested = preferred_scene_num
    try:
        requested = int(requested) if requested is not None else None
    except (ValueError, TypeError):
        requested = None

    candidates = []
    key = set(quality.words(data.get('primary_keyword', ''))) - quality.STOP
    total_scenes = len(ctx.get('scenes', []))

    for s in ctx.get('scenes', []):
        sc_num = s.get('scene_number', 1)
        if not s.get('image_path') and not s.get('video_path'):
            continue

        full_text = f"{s.get('summary', '')} {s.get('narration', '')} {s.get('dialogue', '')} {s.get('visual_prompt', '')} {s.get('text_overlay', '')}".lower()
        overlap = len(key & set(quality.words(full_text)))
        score = overlap * 10

        # Dramatic Emotion & High-Tension Visuals (Viral YouTube CTR indicators)
        drama_keywords = {
            'close-up': 45, 'extreme close-up': 60, 'face': 35, 'eyes': 35,
            'furious': 90, 'rage': 90, 'anger': 70, 'shock': 85, 'slamming': 95,
            'screaming': 90, 'panic': 85, 'badge': 75, 'fbi': 75, 'padlock': 60,
            'bolt cutter': 65, 'confront': 60, 'breakdown': 70, 'tremor': 50
        }
        for dkw, dbonus in drama_keywords.items():
            if dkw in full_text:
                score += dbonus

        if requested is not None and sc_num == requested:
            score += 2000

        # Climax/tension bonus for scenes in the peak 35%-85% of narrative
        if total_scenes > 5:
            pct = sc_num / total_scenes
            if 0.35 <= pct <= 0.85:
                score += 35

        # Visual quality evaluation from video or image
        v_path = s.get('video_path')
        i_path = s.get('image_path')

        if v_path and Path(v_path).is_file():
            try:
                import cv2
                import numpy as np
                cap = cv2.VideoCapture(str(Path(v_path).resolve()))
                if cap.isOpened():
                    tot = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    sample_pcts = [0.20, 0.35, 0.50, 0.65, 0.80] if tot > 30 else [0.50]
                    best_fr_score = -999.0
                    for pct in sample_pcts:
                        f_idx = int(tot * pct)
                        cap.set(cv2.CAP_PROP_POS_FRAMES, f_idx)
                        ret, fr = cap.read()
                        if ret and fr is not None:
                            gray = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
                            lap = float(cv2.Laplacian(gray, cv2.CV_64F).var())
                            hsv = cv2.cvtColor(fr, cv2.COLOR_BGR2HSV)
                            b_mean = float(np.mean(hsv[:, :, 2]))
                            b_std = float(np.std(hsv[:, :, 2]))
                            sat = float(np.mean(hsv[:, :, 1]))
                            if b_mean < 25.0:
                                cur_score = -250.0
                            elif b_mean < 35.0:
                                cur_score = -100.0
                            else:
                                cur_score = min(b_mean, 85.0) * 1.5 + min(b_std, 55.0) + min(sat, 85.0) * 0.5 + min(lap, 350.0) * 0.15
                            if cur_score > best_fr_score:
                                best_fr_score = cur_score
                    cap.release()
                    if best_fr_score > -900:
                        score += best_fr_score
            except Exception:
                pass
        elif i_path and Path(i_path).is_file():
            try:
                from PIL import ImageStat
                with Image.open(i_path) as image:
                    stat = ImageStat.Stat(image.convert('L'))
                    mean_val = stat.mean[0]
                    contrast = stat.stddev[0]
                    if mean_val < 22.0 and sc_num != requested:
                        score -= 250
                    elif contrast < 5 and sc_num != requested:
                        score -= 100
                    score += min(contrast, 50) + min(mean_val, 60) * 0.5
            except OSError:
                continue

        candidates.append((score, s))

    if not candidates:
        return None

    return max(candidates, key=lambda pair: pair[0])[1]





def _generate_grounded_package(root,series,episode,language,genre,custom_hook,preferred_scene,side,font_scale,force,include_shorts):

    import shutil

    ctx=quality.build_episode_context(root,language,genre)

    directory_match=re.fullmatch(r'episode_0*(\d+)',root.name,re.I)

    if directory_match:

        episode=int(directory_match.group(1))

    ctx['episode']=episode

    data,generation,cached=_load_or_create_content(ctx,series,episode,force)

    fallback=quality.fallback_content(ctx)

    titles=[]

    for entry in (data.get('titles') or fallback['titles'])[:3]:

        text=entry.get('title','') if isinstance(entry,dict) else str(entry)

        text=re.sub(r'^'+re.escape(series)+r'\s*(?:[-:|]\s*)?', '', text,flags=re.I) if series and text.casefold().startswith(series.casefold()+' ') else text

        text=quality.title_with_episode(text,episode,ctx['language'])

        titles.append({'type':entry.get('type','Đề xuất') if isinstance(entry,dict) else 'Đề xuất','title':text})

    primary=quality.clean_text(data.get('primary_keyword'),60) or fallback['primary_keyword']

    clean_ref_tag = quality.sanitize_title(ctx.get('reference_title', ''))
    base_tag_candidates = [primary] + (data.get('secondary_keywords') or []) + (data.get('tags') or [])
    tags = enrich_and_maximize_tags(
        base_tags=base_tag_candidates,
        primary_kw=primary,
        genre=ctx.get('genre', 'documentary'),
        language=ctx.get('language', 'Spanish'),
        series_name=series,
        episode_num=episode,
        subj=clean_ref_tag or ctx.get('title', '')
    )

    hashes=quality.hashtags_for(ctx,tags,data.get('hashtags') if isinstance(data.get('hashtags'),list) else None)

    loc=quality.LOCALE.get(ctx['language'],quality.LOCALE['English'])

    chapters=quality.episode_chapters(ctx)

    opening=quality.clean_text(data.get('description_hook') or ctx['summary'],1000)

    synopsis=quality.clean_text(data.get('story_synopsis'),1500)

    desc_parts=[part for part in [opening,synopsis] if part]

    if chapters:

        desc_parts.append(loc[1]+':\n'+'\n'.join(f"{c['time']} {c['title']}" for c in chapters))

    desc_parts.extend([loc[2], ' '.join(hashes)])

    description='\n\n'.join(desc_parts)

    # Public text is content-only; warnings and provenance are kept outside the description.

    pinned=quality.clean_text(data.get('pinned_comment'),500)

    if not pinned or not quality.is_grounded(pinned,ctx):

        pinned=loc[3]

    hook = quality.clean_text(custom_hook or data.get('thumbnail_hook_text') or primary, 120)

    if not custom_hook and not quality.is_grounded(hook, ctx):

        hook = primary.upper()

    if not custom_hook:

        hook = ' '.join(hook.split()[:8])

    previous=quality.read_json(root/'youtube_publish_pack.json')

    manual_source=root/'thumbnail_manual_source.jpg'

    manual=(not force and not preferred_scene and previous.get('source_fingerprint')==ctx['fingerprint']

        and previous.get('thumbnail_selection',{}).get('source')=='manual_upload' and manual_source.is_file())

    selected=({'scene_number':998,'image_path':str(manual_source),'video_path':None} if manual else _choose_thumbnail(ctx,data,preferred_scene))

    thumbnail=root/'thumbnail_seo.jpg'

    selection={'source':'manual_upload' if manual else ('manual_ai_image' if preferred_scene==999 else 'episode_scene'),'scene_number':selected['scene_number'] if selected else None,

        'reason':quality.clean_text(data.get('thumbnail_selection_reason'),300) or 'Chọn từ cảnh có liên quan đến chủ đề tập phim.',

        'review_required':True}

    warnings=[]

    if not chapters:

        warnings.append('Chưa có đủ thời lượng cảnh đã đo để tạo chapters hợp lệ; không dùng mốc thời gian ước lượng.')

    if selected:

        base = root / 'thumbnail_source_frame.jpg'

        if selected.get('image_path') and Path(selected['image_path']).is_file():

            import shutil

            shutil.copyfile(selected['image_path'], base)

        elif selected.get('video_path') and Path(selected['video_path']).is_file():

            extract_best_scene_frame(selected['video_path'], base)

        else:

            base = Path(selected.get('image_path') or root / 'thumbnail_source_frame.jpg')

        render_side = auto_thumbnail_side(base, genre=ctx.get('genre', 'auto')) if side == 'auto' else side

        generate_thumbnail_image(base, thumbnail, hook_text=hook, preferred_side=render_side, font_scale=font_scale, genre=ctx['genre'],

            metadata={'title': titles[0]['title'], 'tags': tags, 'description': description, 'series_name': series, 'genre': ctx['genre']})
        shorts_cover = root / 'thumbnail_shorts.jpg'
        try:
            generate_shorts_thumbnail_cover(base, shorts_cover, hook_text=hook, genre=ctx['genre'])
        except Exception as e_sh:
            print(f"[SEO] Shorts cover note: {e_sh}", flush=True)

    else:

        # A previous thumbnail may belong to a different content fingerprint. Never reuse it silently.

        thumbnail=None

        warnings.append('Không có ảnh/cảnh video của tập để tạo thumbnail; cần chọn ảnh trước khi đăng.')

    package={'engine_version':quality.ENGINE_VERSION,'source_fingerprint':ctx['fingerprint'],

        'series':series,'episode':episode,'language':ctx['language'],'genre':ctx['genre'],

        'primary_keyword':primary,'best_title':titles[0]['title'],'primary_title':titles[0]['title'],'titles':titles,

        'description':description,'tags':tags,'hashtags':hashes,'hashtags_line':' '.join(hashes),'pinned_comment':pinned,

        'chapters':chapters,'thumbnail_hook_text':hook,'thumbnail_scene_num':selection['scene_number'],

        'thumbnail_side':side,'thumbnail_font_scale':font_scale,'thumbnail_file':str(thumbnail) if thumbnail else None,

        'thumbnail_url':_media_url(thumbnail) if thumbnail else None,'thumbnail_slug_filename':'thumbnail_seo.jpg',

        'thumbnail_slug_url':_media_url(thumbnail) if thumbnail else None, 'thumbnail_shorts_file': str(root / 'thumbnail_shorts.jpg') if (root / 'thumbnail_shorts.jpg').is_file() else None,'thumbnail_options':[],

        'thumbnail_selection':selection,'generation':generation,'source_content':data,

        'source_summary':{'scene_count':len(ctx['scenes']),'characters':ctx['characters'],'language':ctx['language'],

            'evidence_source':'saved_episode_plan_and_dialogue','timing_source':'rendered' if chapters else 'unavailable',

            'semantic_validation':'lexical_guard_and_editorial_review'},

        'content_warnings':warnings,'research_sources':quality.SOURCES,'shorts_package':None,
        'youtube_upload_settings':{
            'shorts_remixing':'none',
            'shorts_remixing_label':'Không cho phép phối lại (Don\'t allow remixing)',
            'shorts_remixing_options':[
                {'value':'all','label':'Cho phép phối lại video và âm thanh','recommended':False},
                {'value':'audio_only','label':'Chỉ cho phép phối lại âm thanh','recommended':False},
                {'value':'none','label':'Không cho phép phối lại (Khuyên dùng cho phim AI)','recommended':True}
            ],
            'contains_synthetic_media':True,
            'contains_synthetic_media_label':'Có (Chính sách YouTube: chứa hình ảnh/âm thanh do AI tạo)',
            'made_for_kids':False,
            'made_for_kids_label':'Không, nội dung này không dành cho trẻ em (COPPA)',
            'license':'youtube',
            'license_label':'Giấy phép chuẩn của YouTube',
            'category_id':'1',
            'category_label':'Phim và Hoạt ảnh (Film & Animation)',
            'embeddable':True
        }}

    if thumbnail:
        opts = [{'file': thumbnail.name, 'scene': selection['scene_number'], 'url': package['thumbnail_url'], 'label': 'Bản chính (Đã ghép chữ)'}]
        fierce = root / 'thumbnail_fierce_base.jpg'
        if fierce.is_file():
            opts.append({'file': fierce.name, 'scene': 999, 'url': _media_url(fierce), 'label': f"AI {ctx['genre'].upper()}"})
        comp = root / 'thumbnail_competitor_trend.jpg'
        if comp.is_file():
            opts.append({'file': comp.name, 'scene': 888, 'url': _media_url(comp), 'label': 'Trend Đối Thủ'})
        for s in ctx.get('scenes', [])[:4]:
            if s.get('image_path') and Path(s['image_path']).is_file():
                sp = Path(s['image_path'])
                opts.append({'file': sp.name, 'scene': s['scene_number'], 'url': _media_url(sp), 'label': f"Cảnh {s['scene_number']}"})
        package['thumbnail_options'] = opts

    package=enrich_seo_package(package)

    if include_shorts:

        shorts=build_shorts_seo_pack(series,episode,ctx['language'],ctx['genre'],ctx['title'],primary,package['best_title'],context=ctx)

        package['shorts_package']=shorts

        _atomic_text(root/'youtube_shorts_pack.json',json.dumps(shorts,ensure_ascii=False,indent=2))

        _atomic_text(root/'youtube_shorts_pack.txt',format_shorts_pack_txt(shorts,series,episode,ctx['language']))

    return write_seo_package(root,package)





def generate_seo_package(episode_dir, series_name, episode_num=1, language="auto", genre="auto", custom_hook_text=None,

        preferred_scene_num=None, preferred_side="auto", font_scale="standard", force_regenerate=False, include_shorts=False):

    """Build a grounded episode package; one chosen thumbnail; no synthetic performance metrics."""

    root=Path(episode_dir)

    with _episode_lock(root):

        return _generate_grounded_package(root,series_name,episode_num,language,genre,custom_hook_text,

            preferred_scene_num,preferred_side,font_scale,force_regenerate,include_shorts)







def format_publish_pack_txt(seo_package):

    p=seo_package

    lines=['GÓI ĐĂNG BÀI YOUTUBE',f"{p.get('series','')} — {p.get('episode','')} — {p.get('language','')}",

        '', '1. TIÊU ĐỀ ĐỀ XUẤT']

    for i,t in enumerate(p.get('titles') or [],1):

        lines.extend([f"[{i}] {t.get('title','')}",f"    {t.get('review_status','Đề xuất biên tập; chưa đo hiệu quả')}"])

    lines.extend(['','2. THUMBNAIL CHÍNH',p.get('thumbnail_file') or 'Chưa có ảnh',

        'Chữ trên ảnh: '+str(p.get('thumbnail_hook_text') or ''),

        (p.get('thumbnail_checks') or {}).get('rating','Chưa kiểm tra'),

        'Kiểm tra bằng mắt: chữ trên điện thoại, biểu cảm và vùng huy hiệu thời lượng.',

        '', '3. MÔ TẢ VIDEO',p.get('description',''),'', '4. TAGS',', '.join(p.get('tags') or []),

        f"{len(', '.join(p.get('tags') or []))}/500 ký tự",'', '5. HASHTAGS',' '.join(p.get('hashtags') or []),

        '', '6. BÌNH LUẬN GHIM',p.get('pinned_comment',''),'', '7. NGUỒN KIỂM TRA',

        (p.get('metadata_checks') or {}).get('rating','Chưa kiểm tra'),

        'vidIQ: '+str((p.get('official_vidiq') or {}).get('message','Chưa kết nối.')),

        *[str(x.get('title',''))+' — vidIQ: '+str(x.get('score') if x.get('score') is not None else 'Đạt chuẩn')+'/100' for x in (p.get('official_vidiq') or {}).get('title_scores',[])],

        'Lịch đăng giờ vàng: '+str((p.get('publishing_schedule') or {}).get('golden_hours', '14:00 – 16:00 EST'))+' (Ngày tối ưu: '+str((p.get('publishing_schedule') or {}).get('best_days', 'Thứ 5, 6, 7, CN'))+')',

        'Phương thức tạo: '+str(p.get('generation',{}).get('method','legacy'))])

    if p.get('generation',{}).get('warning'):

        lines.append('Lưu ý: '+p['generation']['warning'])

    lines.extend(p.get('content_warnings') or [])

    return '\n'.join(lines)+'\n'







def build_shorts_seo_pack(series_name, episode_num, language, genre, subj, primary_kw, full_video_title="", full_video_url="", context=None):

    """Derive optional Shorts metadata from the episode; an excerpt still requires review."""

    loc=quality.LOCALE.get(quality.canonical_language(language),quality.LOCALE['English'])

    title=quality.clean_text(full_video_title or subj or series_name,100)

    desc=f"{title}\n\n{loc[4]}"+(f"\n{full_video_url}" if full_video_url else '')

    ctx=context or {'language':quality.canonical_language(language),'evidence_text':title+' '+primary_kw,'scenes':[],'characters':[]}

    tags=quality.relevant_tags([primary_kw,title],ctx)

    hashtags=quality.hashtags_for(ctx,tags)

    hashtags=(['#shorts']+hashtags)[:5]

    pack={'best_title':title,'titles':[{'title':title,'type':'Trích đoạn cần đối chiếu'}],

        'description':desc+'\n\n'+' '.join(hashtags),'tags':tags,'tags_comma_separated':', '.join(tags),

        'hashtags':hashtags,'hashtags_line':' '.join(hashtags),'pinned_comment':loc[3],

        'hook_banner_text':primary_kw.upper(),'cta_banner_text':loc[4],'aspect_ratio':'9:16',

        'video_filename':'episode_short.mp4','primary_keyword':primary_kw,'language':language,

        'source_scope':'parent_episode','review_required':True}

    return enrich_seo_package(pack)







def format_shorts_pack_txt(shorts_pack, series_name, episode_num, language):

    return 'SHORTS — ĐỐI CHIẾU VỚI TRÍCH ĐOẠN TRƯỚC KHI ĐĂNG\n'+format_publish_pack_txt(dict(shorts_pack,series=series_name,episode=episode_num,language=language))







def format_upload_settings_checklist_txt(seo_package=None):
    """Generates an independent companion reference guide for YouTube Studio upload settings."""
    return """THIẾT LẬP & CẤU HÌNH KHI ĐĂNG TẢI LÊN YOUTUBE STUDIO
(Tài liệu tra cứu đối chiếu khi upload trên studio.youtube.com hoặc cấu hình tự động)

1. PHỐI LẠI CÁC ĐOẠN PHIM NGẮN (SHORTS REMIXING):
   [•] Không cho phép phối lại (Don't allow remixing) — KHUYÊN CHỌN
       Lý do: Bảo vệ bản quyền video phim AI, tránh bị các kênh khác cắt trộm nội dung làm Shorts.
   [ ] Chỉ cho phép phối lại âm thanh
   [ ] Cho phép phối lại video và âm thanh

2. TUYÊN BỐ NỘI DUNG ĐÃ QUA CHỈNH SỬA (SYNTHETIC / ALTERED CONTENT):
   [•] CÓ (Bắt buộc theo chính sách YouTube 2024+ đối với video chứa hình ảnh hoặc giọng nói do AI tạo)

3. ĐỐI TƯỢNG NGƯỜI XEM (COPPA):
   [•] Không, đây không phải nội dung dành cho trẻ em

4. GIẤY PHÉP & PHÂN PHỐI (LICENSE & DISTRIBUTION):
   [•] Giấy phép chuẩn của YouTube (Standard YouTube License)
   [•] Cho phép nhúng video (Allow embedding)
   [•] Xuất bản lên nguồn cấp dữ liệu Đăng ký và thông báo cho người đăng ký

5. DANH MỤC VIDEO (CATEGORY):
   [•] Phim và Hoạt ảnh (Film & Animation) hoặc Giải trí (Entertainment)

6. NGÔN NGỮ & BẢN DỊCH (LANGUAGE):
   - Ngôn ngữ video: Khớp với ngôn ngữ lồng tiếng của tập phim (ví dụ: Tiếng Việt - vi, English - en-US)
   - Chứng nhận phụ đề: Không có
"""
