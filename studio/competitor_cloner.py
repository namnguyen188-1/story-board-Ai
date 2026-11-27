"""Competitor Video Character Cloning Engine for Storyboard AI Studio Pro.
Extracts character visual DNA, wardrobe, appearance locks, and art style from reference
YouTube videos using V2's vision analysis architecture.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from PIL import Image

try:
    import silent_subprocess
except Exception:
    pass

STUDIO_DIR = Path(__file__).resolve().parent
ROOT_DIR = STUDIO_DIR.parent
CLONES_CACHE_DIR = STUDIO_DIR / "character_clones"
CLONES_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def patch_running_server() -> bool:
    """Hot-patches sys.modules['__main__'].StudioRequestHandler in memory to add /api/episode/seo."""
    try:
        import sys, urllib.parse, json, re
        from pathlib import Path
        handler_cls = None
        for mod_name in ["__main__", "web_server"]:
            mod = sys.modules.get(mod_name)
            if mod and hasattr(mod, "StudioRequestHandler"):
                handler_cls = getattr(mod, "StudioRequestHandler")
                main_mod = mod
                break
        if not handler_cls:
            # search all loaded modules
            for mod in list(sys.modules.values()):
                if hasattr(mod, "StudioRequestHandler"):
                    handler_cls = getattr(mod, "StudioRequestHandler")
                    main_mod = mod
                    break
        if not handler_cls:
            print("[HOT_PATCH] StudioRequestHandler not found in any module!", flush=True)
            return False
        if getattr(handler_cls, "_live_flow_status_patched", False):
            return True

        orig_do_GET = handler_cls.do_GET
        orig_do_POST = handler_cls.do_POST

        def patched_do_GET(self):
            parsed = urllib.parse.urlsplit(self.path)

            if parsed.path == "/api/status":
                try:
                    js = getattr(main_mod, "job_status", {})
                    if js.get("stage") == "GENERATING_IMAGES" and js.get("running"):
                        mcp_out = STUDIO_DIR / "runtime" / "private_mcp_outputs"
                        subdirs = sorted(mcp_out.glob("storyboard_studio_mcp_*"), key=lambda p: p.stat().st_mtime, reverse=True)
                        if subdirs:
                            count = len(list(subdirs[0].glob("*.jpg")))
                            total = js.get("total_scenes") or 138
                            if count > 0:
                                pct = min(44, 28 + int((count / total) * 16))
                                js["percent"] = max(js.get("percent", 28), pct)
                                js["message"] = f"Đang vẽ ảnh qua Google Flow: {count}/{total} ảnh hoàn tất ({int(count/total*100)}%)..."
                except Exception:
                    pass

            if parsed.path == "/api/competitor/channels":
                try:
                    import competitor_harvester
                    return self.end_json({"ok": True, "channels": competitor_harvester.list_saved_channels()})
                except Exception as exc:
                    return self.end_json({"ok": False, "error": str(exc)}, 500)

            if parsed.path == "/api/competitor/channel":
                try:
                    import competitor_harvester
                    query = urllib.parse.parse_qs(parsed.query)
                    key = query.get("key", [""])[0]
                    data = competitor_harvester.load_channel_videos(key)
                    if data:
                        return self.end_json({"ok": True, "data": data})
                    return self.end_json({"ok": False, "error": "Kênh không tồn tại"}, 404)
                except Exception as exc:
                    return self.end_json({"ok": False, "error": str(exc)}, 500)

            if parsed.path == "/api/competitor/scan":
                try:
                    import competitor_harvester
                    query = urllib.parse.parse_qs(parsed.query)
                    ch = query.get("channel", [""])[0]
                    lim = int(query.get("limit", ["100"])[0])
                    tab = query.get("tab", ["videos"])[0]
                    sort_by = query.get("sort", ["views_desc"])[0]
                    res = competitor_harvester.scan_channel(ch, limit=lim, tab=tab, sort_by=sort_by)
                    return self.end_json(res)
                except Exception as exc:
                    return self.end_json({"success": False, "error": str(exc)}, 500)

            return orig_do_GET(self)

        def patched_do_POST(self):
            return orig_do_POST(self)

            if parsed.path == "/api/competitor/scan":
                content_len = int(self.headers.get("Content-Length", 0))
                raw_body = self.rfile.read(content_len) if content_len > 0 else b"{}"
                try:
                    body = json.loads(raw_body.decode("utf-8"))
                except Exception:
                    body = {}
                try:
                    import competitor_harvester
                    ch = str(body.get("channel_url", "")).strip()
                    lim = int(body.get("limit", 100))
                    tab = str(body.get("tab", "videos")).strip()
                    sort_by = str(body.get("sort", "views_desc")).strip()
                    res = competitor_harvester.scan_channel(ch, limit=lim, tab=tab, sort_by=sort_by)
                    return self.end_json(res)
                except Exception as exc:
                    return self.end_json({"success": False, "error": str(exc)}, 500)

            return orig_do_POST(self)

        handler_cls.do_GET = patched_do_GET
        handler_cls.do_POST = patched_do_POST
        handler_cls._live_flow_status_patched = True
        print("[HOT_PATCH] StudioRequestHandler hot-patched with Competitor Harvester successfully!", flush=True)
        return True
    except Exception as exc:
        print(f"[HOT_PATCH_ERROR] {exc}", flush=True)
        return False

# Auto-execute hot-patch if running in web server process
try:
    patch_running_server()
except Exception:
    pass


def extract_youtube_video_id(url: str) -> str:
    """Extracts clean 11-char YouTube ID from any valid format (watch, shorts, embed, youtu.be)."""
    clean_url = str(url or "").strip()
    p = urllib.parse.urlsplit(clean_url)
    host = (p.hostname or "").lower()
    vid = ""
    if host in ("youtu.be", "www.youtu.be"):
        vid = p.path.strip("/").split("/")[0]
    elif "youtube.com" in host:
        seg = p.path.strip("/").split("/")
        if seg and seg[0] == "watch":
            vid = urllib.parse.parse_qs(p.query).get("v", [""])[0]
        elif seg and seg[0] in ("shorts", "embed", "live") and len(seg) > 1:
            vid = seg[1]
    if not vid or not re.fullmatch(r"[A-Za-z0-9_-]{11}", vid):
        # Fallback regex
        m = re.search(r"(?:v=|\/shorts\/|\/embed\/|youtu\.be\/)([A-Za-z0-9_-]{11})", clean_url)
        if m:
            vid = m.group(1)
        else:
            raise ValueError(f"Không thể trích xuất ID video từ liên kết: {url}")
    return vid


def download_reference_thumbnail(video_id: str, output_path: Path) -> Path | None:
    """Downloads highest available thumbnail resolution (maxresdefault or hqdefault)."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.is_file() and output_path.stat().st_size > 3000:
        return output_path

    urls = [
        f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
        f"https://img.youtube.com/vi/{video_id}/sddefault.jpg",
        f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
    ]
    for thumb_url in urls:
        try:
            req = urllib.request.Request(thumb_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = resp.read()
                # YouTube returns a 1097-byte blank image placeholder for missing maxresdefault
                if len(data) > 2500:
                    output_path.write_bytes(data)
                    return output_path
        except Exception:
            continue
    return None


def extract_video_keyframes(canonical: str, video_id: str, duration_minutes: float = 2.0) -> list[Path]:
    """Downloads low-res video stream via yt_dlp and extracts 4 in-video keyframes across duration."""
    import subprocess
    frames_dir = CLONES_CACHE_DIR / f"{video_id}_frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    existing = sorted(frames_dir.glob("frame_*.jpg"))
    if len(existing) >= 2:
        return existing

    tmp_video = frames_dir / "sample.mp4"
    if not tmp_video.is_file() or tmp_video.stat().st_size < 10000:
        try:
            import yt_dlp
            ydl_opts = {
                "format": "160/worstvideo[ext=mp4]/worst",
                "outtmpl": str(tmp_video),
                "quiet": True,
                "no_warnings": True,
                "socket_timeout": 12,
                "windows_hide_console": True,
                "nocheckcertificate": True,
                "extractor_args": {"youtube": {"player_client": ["android", "ios", "web"]}},
            }
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([canonical])
            except Exception as dl_err:
                proxy_url = None
                try:
                    from muse_accounts import get_all_accounts, get_account_proxy
                    accs = get_all_accounts()
                    for acc in accs:
                        p = get_account_proxy(acc.get("id"))
                        if p:
                            proxy_url = p
                            break
                except Exception:
                    pass
                if proxy_url:
                    print(f"[CLONER] Retrying yt_dlp download with proxy...", flush=True)
                    ydl_opts["proxy"] = proxy_url
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([canonical])
                else:
                    raise dl_err
        except Exception as e:
            print(f"[CLONER] Error downloading lowres video stream: {e}", flush=True)

    if not tmp_video.is_file():
        return []

    # Extract 4 keyframes spread across video duration
    dur_sec = max(float(duration_minutes or 2.0) * 60.0, 30.0)
    timestamps = [
        max(5, int(dur_sec * 0.05)),
        max(15, int(dur_sec * 0.20)),
        max(30, int(dur_sec * 0.45)),
        max(60, int(dur_sec * 0.70)),
    ]
    results = []
    si = subprocess.STARTUPINFO()
    si.dwFlags |= getattr(subprocess, "STARTF_USESHOWWINDOW", 1)
    si.wShowWindow = getattr(subprocess, "SW_HIDE", 0)
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)

    for idx, sec in enumerate(timestamps, 1):
        out_f = frames_dir / f"frame_{idx:02d}_{sec}s.jpg"
        if not out_f.is_file():
            cmd = ["ffmpeg", "-y", "-ss", str(sec), "-i", str(tmp_video), "-vframes", "1", "-q:v", "2", str(out_f)]
            subprocess.run(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                startupinfo=si,
                creationflags=flags,
            )
        if out_f.is_file() and out_f.stat().st_size > 1000:
            results.append(out_f)
    return results


def make_contact_sheet(frame_paths: list[Path], output_path: Path) -> Path:
    """Stitches extracted video frames into a 2x2 contact sheet for multi-frame Gemini Vision analysis."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    imgs = []
    for p in frame_paths[:4]:
        try:
            imgs.append(Image.open(p).convert("RGB"))
        except Exception:
            pass
    if not imgs:
        return output_path
    w, h = 640, 360
    resized = [im.resize((w, h), Image.Resampling.LANCZOS) for im in imgs]
    sheet = Image.new("RGB", (w * 2, h * 2))
    positions = [(0, 0), (w, 0), (0, h), (w, h)]
    for pos, im in zip(positions, resized):
        sheet.paste(im, pos)
    sheet.save(output_path, "JPEG", quality=90)
    return output_path


def call_vision_dna_analysis(image_path: Path, video_title: str = "", video_desc: str = "") -> dict:
    """Analyzes character identity and visual world using V2's smart_vision_json or Resilient Gemini Vision."""
    prompt = f"""You are an elite Cinematography & Visual DNA Analyst for film and digital video production.
CRITICAL MANDATE:
Analyze the ACTUAL IN-VIDEO FOOTAGE provided in these real sampled video frames (Title: "{video_title}").
DO NOT rely on YouTube clickbait thumbnails, channel avatars, or exaggerated 3D title text.
Inspect the real subjects, visual medium, art style, wardrobe, materials, and atmosphere from the actual video frames.

GENRE & SUBJECT ANALYSIS GUIDELINES:
1. Genre & Medium Identification:
   - Identify the TRUE genre and medium from the frames:
     * 'family_drama': Modern contemporary drama, live-action human actors/characters, suburban homes, interiors, everyday modern clothing, dramatic interpersonal conflict (HOA, family, legal, revenge).
     * 'western': American frontier/ranch drama, rustic ranch environments, open pastures, fences, barns, western denim/plaid/hats/workwear.
     * 'stoic': Classical Greco-Roman philosophical cinematography. Features dignified ancient philosophers and scholars with natural human skin tones in classical robes/togas, contemplative thinkers writing on papyrus in candlelit studies, figures by misty lakes and colonnades, as well as classical monuments and sculptures. Rich atmospheric chiaroscuro lighting, moody cinematic compositions.
     * 'animation': 2D/3D animated film, stylized cartoon/anime characters, vibrant expressive scenes.
     * 'whiteboard': Professional hand-drawn whiteboard illustrations, black ink line art on clean white background.
     * 'action': High-octane action thriller, tactical gear, dynamic camera angles, cinematic intensity.
     * 'history': Historical period drama, authentic period costumes and historical sets.
     * 'documentary': Photographic documentary or essay style, realistic cinematic lighting and environments.

2. Subject / Character Continuity & Faithful Cloning:
   - Observe and describe ONLY actual visual evidence from the footage.
   - CRITICAL SUBJECT CLASSIFICATION:
     * If the footage features a living human, actor, or scholar (e.g. Marcus Aurelius, Seneca, or modern actor in clothing/toga): classify as a LIVING HUMAN with natural human skin tones and organic textile wardrobe. NEVER classify a living person as a stone statue!
     * If the footage features a classical fine-art painting: preserve the painted fine-art medium.
     * For 'stoic' / Classical Greco-Roman philosophy: Protagonist is a MONUMENTAL HEROIC CARVED CARRARA MARBLE STATUE of Marcus Aurelius. Noble chiseled stone features, intricately sculpted curly marble hair and textured beard, wise contemplative stone gaze (carved stone eyes without biological pupils), broad sculpted stone shoulders draped in an authentic Roman stone toga cascading across one shoulder with a circular imperial brooch medallion. Completely unbroken anatomy with intact carved stone arms. NEVER render as living human flesh, NEVER modern actor with real skin pores, NEVER flesh tones, NEVER bodybuilder cosplay.
      * Wardrobe for Stoic genre: Signature draped Carrara marble classical toga with circular imperial brooch medallion, cascading elegantly over sculpted stone shoulders.
      * Dynamic Framing: Prioritize heroic medium shots, contemplative 3/4 stone portraits, and grand atmospheric ancient Roman imperial colonnades, Corinthian marble columns, and Acropolis ruins under dramatic golden chiaroscuro rim lighting.
      * ABSOLUTE CARRARA MARBLE STATUE RULE FOR STOIC: The protagonist MUST ALWAYS be an authentic monumental classical Carrara marble statue of Marcus Aurelius. Completely unbroken stone anatomy with intact carved arms; strictly never living human flesh, never real skin pores, never biological human actors, never tabletop pedestals!
   - If some sampled images show a statue and others show people or landscapes, report distinct observed subject types without forcing every frame to be a statue.

Return JSON only with these exact keys:
{{
  "character_name": "Specific primary character name or persona (e.g. 'Defiant Suburban Homeowner', 'Modern Hospital Nurse', 'Marcus Aurelius', 'Elderly Father')",
  "apparent_age": "e.g. 'Mid-40s', 'Late 50s', 'Classical Monumental Figure', 'Elderly'",
  "gender": "e.g. 'Male', 'Female', 'Male sculpture', 'Non-binary'",
  "appearance_lock": "EXHAUSTIVE physical traits of primary character: age, skin undertone, facial markers/scars, bone structure, hairstyle, and physique.",
  "wardrobe_lock": "EXACT clothing and accessories of primary character.",
  "characters": [
    {{
      "name": "Character Name or Persona (e.g. 'Marcus Aurelius', 'Roman Senator / Rival', 'Linh', 'Mysterious Old Hermit')",
      "role": "'protagonist', 'antagonist', or 'supporting'",
      "apparent_age": "e.g. '24 years old', '65 years old'",
      "gender": "'Male', 'Female', etc.",
      "appearance_lock": "Exhaustive facial landmarks, permanent identifying markers (scars, moles), hair architecture, and body build.",
      "wardrobe_lock": "Exact immutable wardrobe, materials, colors, and key props."
    }}
  ],
  "art_style": "EXACT visual medium and cinematography: e.g. 'Photorealistic contemporary cinematic 16:9 drama film with natural three-point lighting and suburban exterior', 'Moody 16:9 historical drama film', 'Vibrant 2D animation'.",
  "immutable_rules": "Strict continuity rules across all characters: maintain distinct faces, immutable wardrobes per scene, and cinematic lighting without black crush.",
  "clone_prompt": "High-fidelity positive prompt faithfully cloning the observed subjects, wardrobe, camera angle, lighting, and visual medium of the video footage (e.g. contemporary live-action drama, historical film, whiteboard, or 3D animation).",
  "story_premise": "Core narrative, conflict, or dramatic premise observed in the video footage",
  "suggested_genre": "Best matching genre: one of 'family_drama', 'western', 'stoic', 'documentary', 'whiteboard', 'action', 'animation', 'history'"
}}
"""
    # Use the Studio's own Gemini key pool. Never import YouTube SEO Pro V2.
    # 2. Resilient Gemini Vision Fallback
    try:
        from resilient_gemini import ResilientClient, get_all_api_keys
        from google import genai
        from google.genai import types

        keys = get_all_api_keys()
        if not keys:
            raise RuntimeError("No Gemini API keys configured.")

        client = ResilientClient(api_keys=keys[:2])
        img_bytes = Path(image_path).read_bytes()

        for model_name in ("gemini-flash-lite-latest", "gemini-3.5-flash", "gemini-3.8-flash"):
            try:
                resp = client.models.generate_content(
                    model=model_name,
                    contents=[
                        types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"),
                        prompt
                    ],
                    config={"response_mime_type": "application/json"}
                )
                data = json.loads(resp.text)
                if isinstance(data, dict) and data.get("character_name"):
                    data["vision_verified"]=True
                    return data
            except Exception:
                continue
    except Exception as e:
        print(f"[CLONER] Gemini Vision fallback failed: {e}")

    # 3. Safe fallback if network / keys unavailable
    return {
        "character_name": "Protagonist",
        "apparent_age": "Adult",
        "gender": "Unknown",
        "appearance_lock": "Distinctive facial features, clear expressive eyes, consistent haircut and hair color",
        "wardrobe_lock": "Signature outfit matching video genre with consistent colors and cut",
        "art_style": "Cinematic visual storytelling",
        "immutable_rules": "Maintain identical face, hair, and clothing in every scene",
        "clone_prompt": "Cinematic protagonist with consistent facial features and signature clothing",
        "story_premise": video_title or "Reference video storyline",
        "suggested_genre": "documentary",
        "vision_verified":False
    }


def map_to_canonical_visual_style(art_style: str, genre: str = "documentary") -> str:
    """Maps descriptive vision art style or raw text to one of the studio's canonical visual styles."""
    s = str(art_style or "").lower().strip()
    try:
        from studio_modes import STYLES, GENRES
    except Exception:
        STYLES = {"auto", "color_cinematic", "color_animation", "whiteboard", "hand_color", "flow_video", "colored_marker"}
        GENRES = {}

    if s in STYLES and s != "auto":
        return s
    if any(k in s for k in ("whiteboard", "bảng trắng", "sketch", "black ink")):
        return "whiteboard"
    if any(k in s for k in ("marker", "bút dạ", "after skool")):
        return "colored_marker"
    if any(k in s for k in ("statue", "tượng", "sculpture", "marble", "classical sculpture", "roman statue")):
        return "color_cinematic"
    if any(k in s for k in ("anim", "cartoon", "disney", "pixar", "anime", "manga", "3d animation", "3d cartoon")):
        return "color_animation"
    if any(k in s for k in ("hand color", "tô màu")):
        return "hand_color"
    if any(k in s for k in ("flow_video", "flow", "video gen", "runway", "luma", "sora", "kling")):
        return "flow_video"
    if any(k in s for k in ("cinematic", "photorealistic", "photo", "film", "drama", "realistic", "live action", "portrait", "3d render")):
        return "color_cinematic"
    if genre in GENRES:
        return GENRES[genre][1]
    return "color_cinematic"


def analyze_competitor_character(url: str) -> dict:
    """Full pipeline: validates URL, fetches thumbnail, extracts character DNA, and prepares clone bundle."""
    patch_running_server()
    if str(url or "").strip().startswith("__hotpatch__"):
        return {"ok": True, "hotpatch": True, "message": "Server StudioRequestHandler hot-patched with /api/episode/seo"}

    from studio_input_modes import youtube_url, inspect_youtube_reference

    canonical = youtube_url(url)
    video_id = extract_youtube_video_id(canonical)
    cache_file = CLONES_CACHE_DIR / f"{video_id}_dna_verified_v2.json"
    thumb_file = CLONES_CACHE_DIR / f"{video_id}_anchor.jpg"

    # Step 1: Base metadata (duration, language, region, voice)
    base_info = inspect_youtube_reference(canonical)
    title = base_info.get("title", "")
    author = base_info.get("author", "")

    # Step 2: Download thumbnail as fallback, and extract IN-VIDEO KEYFRAMES as primary evidence
    download_reference_thumbnail(video_id, thumb_file)
    video_frames = extract_video_keyframes(canonical, video_id, duration_minutes=base_info.get("duration_minutes", 2.0))
    contact_sheet = None
    if video_frames:
        contact_sheet = make_contact_sheet(video_frames, CLONES_CACHE_DIR / f"{video_id}_contact_sheet.jpg")
        primary_visual = contact_sheet if contact_sheet.is_file() else video_frames[0]
        anchor_visual = str(video_frames[0])
    else:
        primary_visual = thumb_file
        anchor_visual = str(thumb_file) if thumb_file.exists() else ""

    # The cached flag whole_video_verified is not proof. Reject false-positive
    # three-point metadata timelines and all generic scene placeholders.
    from reference_video_timeline import analyze_youtube_timeline
    from clone_integrity import valid_reference
    timeline_file = CLONES_CACHE_DIR / f"{video_id}_timeline_verified_v2.json"
    timeline_data = {}
    if timeline_file.is_file():
        try:
            cached = json.loads(timeline_file.read_text(encoding="utf-8"))
            if valid_reference(cached,duration_minutes=base_info.get("duration_minutes",0)):
                timeline_data = cached
            else:
                print("[CLONER] Cached reference timeline rejected by strict validation",flush=True)
        except (OSError, ValueError, TypeError):
            pass
    if not timeline_data:
        is_short_vid = bool(base_info.get("is_short") or float(base_info.get("duration_minutes") or 0) <= 2.5)
        local_video = CLONES_CACHE_DIR / f"{video_id}_frames" / "sample.mp4"

        # FAST PATH FOR SHORTS: We already downloaded sample.mp4 locally in 2 seconds!
        # analyze_local_sampled_timeline runs on real extracted frames in ~3 seconds.
        if is_short_vid and local_video.is_file() and local_video.stat().st_size > 10000:
            try:
                from reference_local_timeline import analyze_local_sampled_timeline
                timeline_data = analyze_local_sampled_timeline(
                    local_video, float(base_info.get("duration_minutes") or 0),
                    CLONES_CACHE_DIR / f"{video_id}_local_timeline",
                    model="gemini-flash-lite-latest"
                )
                if valid_reference(timeline_data, duration_minutes=base_info.get("duration_minutes", 0)):
                    tmp = timeline_file.with_suffix(".tmp")
                    tmp.write_text(json.dumps(timeline_data, ensure_ascii=False, indent=2), encoding="utf-8")
                    tmp.replace(timeline_file)
                    print(f"[CLONER] Fast-path local timeline analyzed successfully for short video ({len(timeline_data.get('timeline', []))} points).", flush=True)
            except Exception as short_exc:
                print(f"[CLONER] Short local video analysis fallback: {short_exc}", flush=True)

        if not timeline_data:
            try:
                analyzed = analyze_youtube_timeline(canonical, base_info.get("duration_minutes", 0), models=("gemini-flash-lite-latest", "gemini-3.5-flash"))
                if not valid_reference(analyzed, duration_minutes=base_info.get("duration_minutes", 0)):
                    raise RuntimeError("SOURCE_TIMELINE_DID_NOT_PASS_VERIFICATION")
                timeline_data = analyzed
                tmp = timeline_file.with_suffix(".tmp")
                tmp.write_text(json.dumps(timeline_data, ensure_ascii=False, indent=2), encoding="utf-8")
                tmp.replace(timeline_file)
            except Exception as exc:
                print(f"[CLONER] URL video analysis unavailable: {type(exc).__name__}", flush=True)
                if local_video.is_file() and local_video.stat().st_size > 10000:
                    try:
                        from reference_local_timeline import analyze_local_sampled_timeline
                        timeline_data = analyze_local_sampled_timeline(
                            local_video, float(base_info.get("duration_minutes") or 0),
                            CLONES_CACHE_DIR / f"{video_id}_local_timeline",
                            model="gemini-flash-lite-latest"
                        )
                        if valid_reference(timeline_data, duration_minutes=base_info.get("duration_minutes", 0)):
                            tmp = timeline_file.with_suffix(".tmp")
                            tmp.write_text(json.dumps(timeline_data, ensure_ascii=False, indent=2), encoding="utf-8")
                            tmp.replace(timeline_file)
                    except Exception as fallback_exc:
                        print(f"[CLONER] Local sampled video unavailable: {type(fallback_exc).__name__}", flush=True)
                        timeline_data = {
                            "timeline": [],
                            "whole_video_verified": False,
                            "global_visual_style": "unverified",
                            "video_analysis_model": "unverified",
                            "reference_error": "CLONE_REFERENCE_VIDEO_ANALYSIS_UNAVAILABLE"
                        }

    # Step 3: Check cache or run vision analysis on real video footage
    dna = None
    if cache_file.exists():
        try:
            cached_dna = json.loads(cache_file.read_text(encoding="utf-8"))
            is_stale_human = any(kw in str(cached_dna).lower() for kw in ("living human", "sun-kissed bronze skin", "natural human skin", "live-action actor"))
            if is_stale_human:
                print(f"[CLONER] Bỏ qua cache nhân vật cũ dạng người thật trong {cache_file.name}. Kích hoạt làm mới Tượng Đá Cẩm Thạch...", flush=True)
                dna = None
            elif (cached_dna.get("character_name") and
                    cached_dna.get("in_video_verified") and
                    cached_dna.get("vision_verified")):
                dna = cached_dna
        except Exception:
            pass

    # Extract character DNA if not cached
    if not dna:
        if primary_visual and Path(primary_visual).exists():
            dna = call_vision_dna_analysis(Path(primary_visual), video_title=title)
            if isinstance(dna, dict):
                dna["in_video_verified"] = bool(video_frames and dna.get("vision_verified"))
        else:
            dna = {
                "character_name": "Protagonist",
                "appearance_lock": "Detailed consistent character design",
                "wardrobe_lock": "Signature costume",
                "art_style": base_info.get("visual_style", "color_cinematic"),
                "immutable_rules": "Preserve identity across all scenes",
                "clone_prompt": "High quality character reference",
                "story_premise": title,
                "suggested_genre": base_info.get("genre", "documentary"),
                "in_video_verified": False,
            }

        # Save cache
        try:
            cache_file.write_text(json.dumps(dna, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    # Format human-friendly summary for UI
    detected_genre = dna.get("suggested_genre", base_info.get("genre", "documentary"))
    if detected_genre == "stoic" or base_info.get("genre") == "stoic" or "estoic" in title.lower() or "stoic" in title.lower():
        detected_genre = "stoic"
        dna["suggested_genre"] = "stoic"
        dna["character_name"] = "Marcus Aurelius (Heroic Monumental Carrara Marble Statue)"
        dna["appearance_lock"] = "Heroic monumental classical carved Carrara marble statue of Roman emperor Marcus Aurelius. Cold white-grey Carrara marble stone texture with authentic delicate chisel marks, noble contemplative stone gaze (carved stone eyes without biological pupils), intricately sculpted curly marble hair and textured Roman beard, broad muscular sculpted stone shoulders, and complete unbroken carved stone anatomy."
        dna["wardrobe_lock"] = "Classical Roman imperial draped stone toga cascading gracefully across one sculpted shoulder, fastened with a circular carved stone imperial brooch medallion."
        dna["clone_prompt"] = (
            "Cinematic 16:9 composition, heroic medium shot torso framing. "
            "Monumental heroic classical carved Carrara marble statue of Roman emperor and Stoic philosopher Marcus Aurelius. "
            "Pure cold white-grey Carrara marble stone texture, noble chiseled features, contemplative stone eyes, intricately sculpted curly hair and full stone beard. "
            "Powerful broad sculpted stone shoulders and torso draped in an authentic classical Roman stone toga with a circular brooch medallion. "
            "Dramatic golden chiaroscuro rim lighting outlining the marble contours, volumetric golden light, atmospheric ancient Roman colonnade and distant Acropolis ruins at golden hour dusk with floating embers. "
            "Masterpiece, 8k resolution, authentic classical antiquity marble sculpture, completely inanimate solid stone. "
            "Strictly single statue, completely unbroken anatomy, no living human flesh, no real skin pores, no biological human actor, no tabletop pedestal."
        )
        dna["art_style"] = "Cinematic 16:9 classical antiquity fine art with dramatic golden chiaroscuro rim lighting, cold white Carrara marble statues, ancient Roman ruins, and rich atmospheric dusk grading."
        dna["immutable_rules"] = "Maintain the subject strictly as an unbroken monumental carved Carrara marble statue of Marcus Aurelius; cold white stone texture; noble carved features; draped stone toga with circular brooch; medium shot torso framing; strictly never living human flesh, never real skin pores, never flesh tones, never biological human actors."
        # Update cache file with hardened stoic marble statue DNA
        try:
            cache_file.write_text(json.dumps(dna, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass
    char_name = dna.get("character_name", "Nhân vật chính")
    char_app = dna.get("appearance_lock", "")
    char_attire = dna.get("wardrobe_lock", "")
    art_style = dna.get("art_style", base_info.get("visual_style", "color_cinematic"))

    visual_beat_summary = " | ".join(
        f"{int(p.get('timestamp_seconds',0))}s:{p.get('shot_type','')}:{str(p.get('subject',''))[:80]}"
        for p in timeline_data.get("timeline",[])[:6] if isinstance(p,dict))
    cloned_prompt = (
        f"[THAM KHẢO: {title}]\n"
        f"• Nhân vật chính: {char_name}\n"
        f"• Diện mạo khóa: {char_app}\n"
        f"• Trang phục khóa: {char_attire}\n"
        f"• Bút pháp gốc: {art_style}\n"
        f"• Cốt truyện: {dna.get('story_premise', title)}\n"
        f"• Nhịp hình từ video: {visual_beat_summary or 'VIDEO CHƯA XÁC MINH'}"
    )

    detected_genre = dna.get("suggested_genre", base_info.get("genre", "documentary"))
    genre_series_map = {
        "stoic": "stoi",
        "family_drama": "drama",
        "western": "western",
        "animation": "animation",
        "whiteboard": "whiteboard",
        "action": "action",
        "history": "history",
        "documentary": "documentary",
    }
    suggested_series = genre_series_map.get(detected_genre) or "Series"

    return {
        **base_info,
        **timeline_data,
        "genre": detected_genre,
        "suggested_series": suggested_series,
        "visual_style": map_to_canonical_visual_style(art_style, detected_genre),
        "art_style_description": art_style,
        "character": dna,
        "anchor_image": anchor_visual,
        "contact_sheet": str(contact_sheet) if contact_sheet and contact_sheet.is_file() else "",
        "in_video_verified": bool(video_frames),
        "cloned_prompt_suggestion": cloned_prompt,
        "cloned_character_summary": f"👤 {char_name}: {char_app[:90]}... (Trang phục: {char_attire[:70]}...)",
    }