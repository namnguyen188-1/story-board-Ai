"""
HTTP API & Web Studio Server for Standalone Movie Recap Engine.
Runs on port 8095 completely isolated from Storyboard AI.
"""

import sys
from pathlib import Path
RECAP_ROOT = Path(__file__).resolve().parent
if str(RECAP_ROOT) not in sys.path:
    sys.path.insert(0, str(RECAP_ROOT))

import json
import re
import uuid
import threading
import time
import base64
from typing import Dict, Any

from aiohttp import web
import yt_dlp
from config import load_config, save_config, KeyRotator, get_safe_export_dir
from core.video_analyzer import VideoAnalyzer
from core.scriptwriter import RecapScriptwriter
from core.voice_engine import RecapVoiceEngine
from pipeline import MovieRecapPipeline

RECAP_ROOT = Path(__file__).resolve().parent
WEB_DIR = RECAP_ROOT / "web"
INDEX_FILE = WEB_DIR / "index.html"
EXPORT_DIR = get_safe_export_dir(load_config().get("export_dir"))

jobs: Dict[str, Dict[str, Any]] = {}


def cors_headers():
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization"
    }


async def handle_options(request):
    return web.Response(headers=cors_headers())


async def handle_index(request):
    if INDEX_FILE.is_file():
        content = INDEX_FILE.read_text(encoding="utf-8")
        return web.Response(text=content, content_type="text/html", headers=cors_headers())
    return web.Response(text="Web UI not found", status=404, headers=cors_headers())


async def handle_status(request):
    return web.json_response({
        "status": "ok",
        "app": "Movie Recap Studio",
        "port": 8095
    }, headers=cors_headers())


async def handle_get_config(request):
    cfg = load_config()
    safe_cfg = dict(cfg)
    # Mask keys for security if needed, or pass full for local dev
    return web.json_response(safe_cfg, headers=cors_headers())


async def handle_save_config(request):
    try:
        data = await request.json()
        cfg = load_config()
        cfg.update(data)
        save_config(cfg)
        return web.json_response({"status": "ok", "config": cfg}, headers=cors_headers())
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=400, headers=cors_headers())


async def handle_test_key(request):
    try:
        data = await request.json()
        key = data.get("key", "").strip()
        if not key:
            return web.json_response({"status": "error", "message": "API key trống!"}, status=400, headers=cors_headers())

        from google import genai
        from google.genai import types
        client = genai.Client(api_key=key, http_options=types.HttpOptions(timeout=10000))
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Hello! 1 word reply 'OK'."
        )
        return web.json_response({
            "status": "ok",
            "message": f"Kết nối thành công: {resp.text.strip()}"
        }, headers=cors_headers())
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=400, headers=cors_headers())


async def handle_test_keys(request):
    """Batch test multiple Gemini API keys concurrently with fast ping."""
    try:
        data = await request.json()
        raw_keys = data.get("keys", [])
        if isinstance(raw_keys, str):
            raw_keys = [k.strip() for k in raw_keys.splitlines() if k.strip()]

        if not raw_keys:
            return web.json_response({"status": "error", "message": "Danh sách key trống!"}, status=400, headers=cors_headers())

        from google import genai
        from google.genai import types
        import concurrent.futures

        def check_one(k):
            clean_k = re.sub(r"[^\x20-\x7E]", "", k).strip()
            if not clean_k or len(clean_k) < 20:
                return {"key": clean_k[:10] + "...", "status": "invalid", "message": "Độ dài key không hợp lệ"}

            models_to_test = ["gemini-2.5-flash", "gemini-3.5-flash", "gemini-flash-lite-latest"]
            last_err = ""
            for m_name in models_to_test:
                try:
                    c = genai.Client(api_key=clean_k, http_options=types.HttpOptions(timeout=8000))
                    res = c.models.generate_content(model=m_name, contents="ping")
                    if res and res.text:
                        return {"key": clean_k[:12] + "..." + clean_k[-4:], "status": "live", "message": f"Hoạt động tốt ({m_name})"}
                except Exception as e_m:
                    err_str = str(e_m)
                    last_err = err_str
                    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                        return {"key": clean_k[:12] + "..." + clean_k[-4:], "status": "quota_exceeded", "message": "Hết Quota ngày (429) - Hệ thống sẽ tự động dùng sau"}
                    if "API_KEY_INVALID" in err_str or "400" in err_str:
                        return {"key": clean_k[:12] + "..." + clean_k[-4:], "status": "invalid", "message": "Key không hợp lệ hoặc đã bị vô hiệu"}

            return {"key": clean_k[:12] + "..." + clean_k[-4:], "status": "error", "message": f"Lỗi: {last_err[:50]}"}

        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(8, max(1, len(raw_keys)))) as executor:
            futures = [executor.submit(check_one, k) for k in raw_keys]
            for f in futures:
                results.append(f.result())

        live_count = sum(1 for r in results if r["status"] == "live")
        return web.json_response({
            "status": "ok",
            "total": len(results),
            "live_count": live_count,
            "results": results
        }, headers=cors_headers())
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500, headers=cors_headers())


async def handle_delete_export(request):
    """Safely delete an exported video from recap_exports directory."""
    try:
        data = await request.json()
        filename = data.get("filename", "").strip()
        if not filename:
            return web.json_response({"status": "error", "message": "Thiếu tên file cần xóa"}, status=400, headers=cors_headers())

        target = (EXPORT_DIR / filename).resolve()
        # Security: Prevent directory traversal outside EXPORT_DIR
        if not str(target).startswith(str(EXPORT_DIR.resolve())):
            return web.json_response({"status": "error", "message": "Đường dẫn không hợp lệ"}, status=403, headers=cors_headers())

        if target.is_file():
            target.unlink()
            return web.json_response({"status": "ok", "message": f"Đã xóa thành công file {filename}"}, headers=cors_headers())
        return web.json_response({"status": "error", "message": f"File không tồn tại: {filename}"}, status=404, headers=cors_headers())
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500, headers=cors_headers())


async def handle_analyze_video(request):
    try:
        data = await request.json()
        video_path = data.get("video_path", "").strip()
        if not video_path or not Path(video_path).is_file():
            return web.json_response({"status": "error", "message": f"Không tìm thấy file: {video_path}"}, status=400, headers=cors_headers())

        analyzer = VideoAnalyzer(video_path)
        meta = analyzer.probe()
        shots = analyzer.generate_shot_list(total_recap_seconds=180.0, shot_duration=3.5)
        meta["sample_shots"] = shots[:10]
        meta["total_suggested_shots"] = len(shots)

        return web.json_response({"status": "ok", "metadata": meta}, headers=cors_headers())
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500, headers=cors_headers())


async def handle_fetch_url(request):
    try:
        data = await request.json()
        url = data.get("url", "").strip()
        if not url:
            return web.json_response({"status": "error", "message": "Link URL trống!"}, status=400, headers=cors_headers())

        dl_dir = EXPORT_DIR / "downloads"
        dl_dir.mkdir(parents=True, exist_ok=True)
        ydl_opts = {
            "outtmpl": str(dl_dir / "%(title).50s_%(id)s.%(ext)s"),
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "quiet": True,
            "no_warnings": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        analyzer = VideoAnalyzer(filename)
        meta = analyzer.probe()
        return web.json_response({"status": "ok", "metadata": meta, "video_path": filename}, headers=cors_headers())
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500, headers=cors_headers())


async def handle_generate_script(request):
    try:
        data = await request.json()
        writer = RecapScriptwriter()
        plot_context = data.get("plot_context", "").strip()
        story_idea = (data.get("story_idea") or data.get("custom_script") or "").strip()
        if story_idea and not story_idea.startswith("⏳"):
            plot_context = f"Ý TƯỞNG CỐT TRUYỆN YÊU CẦU TỪ NGƯỜI DÙNG:\n{story_idea}\n\n{plot_context}".strip()

        source_dur = 0.0
        v_path = data.get("source_video") or data.get("video_path")
        if v_path:
            p = find_video_file(v_path)
            if p.is_file():
                try:
                    analyzer = VideoAnalyzer(str(p))
                    meta = analyzer.probe()
                    source_dur = meta.get("duration", 0.0)
                    # If plot_context is empty or generic, perform deep visual scan
                    if not plot_context or plot_context.startswith("Tóm tắt cốt truyện: Phim xoay quanh"):
                        vscan = analyzer.deep_visual_scan(num_frames=6)
                        if vscan and vscan.get("plot_synopsis"):
                            vt_text = vscan.get("visual_timeline_text") or vscan["plot_synopsis"]
                            plot_context = f"DIỄN BIẾN HÀNH ĐỘNG THỰC TẾ TRÊN TỪNG KHUNG HÌNH (BẮT BUỘC KHỚP 100%):\n{vt_text}\n\nTỔNG QUAN:\n{vscan['plot_synopsis']}"
                except Exception as ex:
                    print(f"⚠️ handle_generate_script visual scan warning: {ex}")

        res = writer.generate_recap_script(
            movie_title=data.get("movie_title", "Phim Mới"),
            genre=data.get("genre", "Hành động"),
            target_minutes=int(data.get("target_minutes", 3)),
            plot_context=plot_context,
            user_aliases=data.get("character_aliases"),
            source_duration=source_dur,
            language=data.get("language", "vi")
        )
        return web.json_response({"status": "ok", "script": res}, headers=cors_headers())
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500, headers=cors_headers())


async def handle_preview_voice(request):
    try:
        data = await request.json()
        text = data.get("text", "Chào mừng bạn đến với kênh Review Phim!").strip()
        voice = data.get("voice", "Fenrir")
        speed = float(data.get("speed", 1.15))

        engine = RecapVoiceEngine()
        temp_audio = RECAP_ROOT / "temp_preview.mp3"
        duration = engine.generate_single_speech(text, str(temp_audio), voice_name=voice, speed=speed)

        audio_bytes = temp_audio.read_bytes()
        b64 = base64.b64encode(audio_bytes).decode("ascii")

        return web.json_response({
            "status": "ok",
            "duration": duration,
            "audio_base64": f"data:audio/mp3;base64,{b64}"
        }, headers=cors_headers())
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500, headers=cors_headers())


def find_video_file(path_str: str) -> Path:
    if not path_str:
        dl_dir = EXPORT_DIR / "downloads"
        if dl_dir.is_dir():
            dls = list(dl_dir.glob("*.mp4"))
            if dls:
                dls.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                return dls[0]
        return RECAP_ROOT / "demo_real_movie.mp4"

    try:
        p = Path(path_str)
        if p.is_file():
            return p
    except Exception:
        p = Path("video.mp4")

    # Search in RECAP_ROOT, demo_assets, and EXPORT_DIR
    search_dirs = [
        RECAP_ROOT,
        RECAP_ROOT / "demo_assets",
        EXPORT_DIR,
        EXPORT_DIR / "downloads",
    ]
    try:
        legacy_dl = Path(r"D:\STORYBOARD_AI\recap_exports\downloads")
        if legacy_dl.is_dir():
            search_dirs.append(legacy_dl)
    except Exception:
        pass
    for d in search_dirs:
        if not d.is_dir():
            continue
        try:
            if (d / path_str).is_file():
                return d / path_str
            if (d / p.name).is_file():
                return d / p.name
        except Exception:
            pass

    # Fuzzy normalization match (replaces fullwidth colons, pipes, spaces)
    clean_target = re.sub(r"[:|：｜\s_\-—]+", "", p.name.lower())
    if clean_target:
        for d in search_dirs:
            if not d.is_dir():
                continue
            for f in d.glob("*.mp4"):
                clean_f = re.sub(r"[:|：｜\s_\-—]+", "", f.name.lower())
                if clean_target == clean_f or (len(clean_target) > 5 and clean_target in clean_f):
                    return f

    return p


async def handle_upload_bgm(request):
    """Handles uploading a custom background music (.mp3, .wav, .m4a) file."""
    try:
        reader = await request.multipart()
        field = await reader.next()
        if not field or field.name != "file":
            return web.json_response({"ok": False, "error": "No file field found"}, status=400)
        
        filename = field.filename or "custom_bgm.mp3"
        ext = Path(filename).suffix.lower()
        if ext not in [".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"]:
            return web.json_response({"ok": False, "error": "Chỉ chấp nhận file âm thanh (.mp3, .wav, .m4a, .aac)"}, status=400)
        
        custom_bgm_dir = RECAP_ROOT / "web" / "assets" / "custom_bgm"
        custom_bgm_dir.mkdir(parents=True, exist_ok=True)
        
        safe_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', filename)
        save_path = custom_bgm_dir / safe_name
        
        with open(save_path, "wb") as f:
            while True:
                chunk = await field.read_chunk()
                if not chunk:
                    break
                f.write(chunk)
        
        print(f"🎵 [SERVER] Uploaded custom BGM: {save_path.name} ({save_path.stat().st_size} bytes)")
        return web.json_response({
            "ok": True,
            "bgm_path": str(save_path),
            "bgm_name": filename,
            "size_mb": round(save_path.stat().st_size / (1024 * 1024), 2)
        })
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)


async def handle_translate_script(request):
    """Translates movie recap script to another language via Gemini."""
    try:
        data = await request.json()
        script_text = data.get("script_text", "").strip()
        target_lang = data.get("target_lang", "en").strip()
        if not script_text:
            return web.json_response({"status": "error", "message": "Nội dung kịch bản trống"}, status=400, headers=cors_headers())

        writer = RecapScriptwriter()
        translated = writer.translate_script(script_text, target_lang=target_lang)
        return web.json_response({"status": "ok", "translated_script": translated, "target_lang": target_lang}, headers=cors_headers())
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500, headers=cors_headers())


async def handle_start_render(request):
    try:
        data = await request.json()
        job_id = f"job_{uuid.uuid4().hex[:8]}"

        # Safely resolve source video path
        source_video = data.get("source_video", "").strip()
        p = find_video_file(source_video)
        source_video = str(p.resolve())

        # Safely find matching subtitle if available (never leak demo_movie.srt to other movies)
        subtitle_file = None
        if p.with_suffix(".srt").is_file():
            subtitle_file = str(p.with_suffix(".srt").resolve())
        elif p.stem in ("demo_real_movie", "demo_movie") and (RECAP_ROOT / "demo_movie.srt").is_file():
            subtitle_file = str((RECAP_ROOT / "demo_movie.srt").resolve())

        jobs[job_id] = {
            "status": "running",
            "progress": 0.0,
            "message": "Đang khởi tạo tiến trình dựng video...",
            "result": None,
            "error": None
        }

        def run_job():
            try:
                print(f"\n🎬 [SERVER] Starting render job {job_id} for: {source_video}", flush=True)
                pipeline = MovieRecapPipeline()

                def update_progress(msg, pct):
                    jobs[job_id]["message"] = msg
                    jobs[job_id]["progress"] = round(pct, 1)
                    print(f"[{job_id}] [{pct:.1f}%] {msg}", flush=True)

                result = pipeline.run(
                    source_video=source_video,
                    movie_title=data.get("movie_title", "Review Phim"),
                    genre=data.get("genre", "Hành động"),
                    target_minutes=float(data.get("target_minutes", 3)),
                    aspect_ratio=data.get("aspect_ratio", "16:9"),
                    vertical_style=data.get("vertical_style", "blurred_background"),
                    voice_name=data.get("voice_name", "Fenrir"),
                    voice_speed=float(data.get("voice_speed", 1.15)),
                    user_aliases=data.get("character_aliases"),
                    subtitle_file=subtitle_file,
                    subtitle_config=data.get("subtitle_config"),
                    custom_script=data.get("story_idea") or data.get("custom_script"),
                    bgm_file=data.get("bgm_file"),
                    watermark_text=data.get("watermark_text"),
                    watermark_size=int(data.get("watermark_size", 38)),
                    watermark_color=data.get("watermark_color", "gold"),
                    watermark_motion=data.get("watermark_motion", "floating"),
                    cta_overlay=bool(data.get("cta_overlay", True)),
                    cta_text=data.get("cta_text"),
                    movie_audio_vol=float(data.get("movie_audio_vol", 0.10)),
                    bgm_volume=float(data.get("bgm_volume", 0.15)),
                    export_srt=bool(data.get("export_srt", True)),
                    export_thumbnails=bool(data.get("export_thumbnails", True)),
                    language=data.get("language", "vi"),
                    progress_callback=update_progress
                )

                jobs[job_id]["status"] = "completed"
                jobs[job_id]["progress"] = 100.0
                jobs[job_id]["message"] = "Hoàn thành xuất video thành công!"
                jobs[job_id]["result"] = result
                print(f"✅ [SERVER] Job {job_id} completed successfully!\n", flush=True)

            except Exception as e:
                import traceback
                traceback.print_exc()
                jobs[job_id]["status"] = "failed"
                jobs[job_id]["error"] = str(e)
                jobs[job_id]["message"] = f"Lỗi trong quá trình render: {e}"
                print(f"❌ [SERVER] Job {job_id} failed: {e}\n", flush=True)

        thread = threading.Thread(target=run_job, daemon=True)
        thread.start()

        return web.json_response({"status": "ok", "job_id": job_id}, headers=cors_headers())
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=400, headers=cors_headers())


async def handle_get_progress(request):
    job_id = request.match_info.get("job_id")
    if job_id not in jobs:
        return web.json_response({"status": "error", "message": "Không tìm thấy job"}, status=404, headers=cors_headers())
    return web.json_response(jobs[job_id], headers=cors_headers())


async def handle_list_videos(request):
    try:
        videos = []
        search_dirs = [
            (EXPORT_DIR / "downloads", "Đã tải về"),
            (RECAP_ROOT, "Thư mục gốc")
        ]
        seen = set()
        for d, label in search_dirs:
            if not d.is_dir():
                continue
            for p in d.glob("*.mp4"):
                if p.name.startswith("recap_") or p.name.startswith("temp_"):
                    continue
                if p.name in seen:
                    continue
                seen.add(p.name)
                try:
                    stat = p.stat()
                    is_dl = "downloads" in p.parts
                    import urllib.parse
                    quoted_name = urllib.parse.quote(p.name)
                    videos.append({
                        "name": p.name,
                        "path": str(p.resolve()),
                        "size_mb": round(stat.st_size / (1024 * 1024), 2),
                        "folder": label,
                        "url": f"/exports/downloads/{quoted_name}" if is_dl else f"/source/{quoted_name}"
                    })
                except Exception:
                    pass
        return web.json_response({"status": "ok", "videos": videos}, headers=cors_headers())
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500, headers=cors_headers())


async def handle_get_exports(request):
    try:
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        files = []
        import urllib.parse
        for p in EXPORT_DIR.glob("**/*.mp4"):
            # Bỏ qua các file phim gốc tải tạm trong thư mục downloads
            if "downloads" in p.parts:
                continue
            try:
                stat = p.stat()
                rel = p.relative_to(EXPORT_DIR).as_posix()
                quoted_rel = urllib.parse.quote(rel)
                
                # Check companion files (.srt, .txt, thumbnails)
                has_srt = p.with_suffix(".srt").is_file()
                srt_rel = p.with_suffix(".srt").relative_to(EXPORT_DIR).as_posix() if has_srt else None
                has_txt = p.with_suffix(".txt").is_file()
                txt_rel = p.with_suffix(".txt").relative_to(EXPORT_DIR).as_posix() if has_txt else None
                
                # Find any generated thumbnails
                thumbs = []
                for th in sorted(p.parent.glob(f"{p.stem}_thumb_*.jpg")):
                    try:
                        th_rel = th.relative_to(EXPORT_DIR).as_posix()
                        thumbs.append(f"/exports/{urllib.parse.quote(th_rel)}")
                    except Exception:
                        pass

                files.append({
                    "name": p.name,
                    "rel_path": rel,
                    "url": f"/exports/{quoted_rel}",
                    "full_path": str(p),
                    "size_mb": round(stat.st_size / (1024 * 1024), 2),
                    "mtime": stat.st_mtime,
                    "time_str": time.strftime("%d/%m/%Y %H:%M:%S", time.localtime(stat.st_mtime)),
                    "has_srt": has_srt,
                    "srt_url": f"/exports/{urllib.parse.quote(srt_rel)}" if srt_rel else None,
                    "has_txt": has_txt,
                    "txt_url": f"/exports/{urllib.parse.quote(txt_rel)}" if txt_rel else None,
                    "thumbnails": thumbs
                })
            except Exception:
                pass
        files.sort(key=lambda x: x["mtime"], reverse=True)
        return web.json_response({"status": "ok", "exports": files, "export_dir": str(EXPORT_DIR)}, headers=cors_headers())
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500, headers=cors_headers())


async def handle_open_folder(request):
    try:
        data = await request.json()
        target = data.get("path")
        action = data.get("action", "select")
        folder = EXPORT_DIR
        if target:
            p = Path(target)
            if p.is_file():
                if action == "play":
                    import os
                    os.startfile(str(p))
                    return web.json_response({"status": "ok", "action": "played", "file": str(p)}, headers=cors_headers())
                else:
                    # On Windows, open explorer and highlight the exact file
                    subprocess.Popen(["explorer", f"/select,{p}"], creationflags=WIN_NO_WINDOW)
                    return web.json_response({"status": "ok", "action": "selected", "file": str(p)}, headers=cors_headers())
            elif p.is_dir():
                folder = p
        import os
        os.startfile(str(folder))
        return web.json_response({"status": "ok", "folder": str(folder)}, headers=cors_headers())
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500, headers=cors_headers())


async def handle_get_current_script(request):
    try:
        video_stem = request.query.get("video_stem", "").strip().lower()
        if not video_stem:
            return web.json_response({"status": "empty", "message": "Chưa chọn video"}, headers=cors_headers())

        script_files = list(EXPORT_DIR.glob("**/recap_script.json"))
        if not script_files:
            return web.json_response({"status": "empty", "message": "Chưa có file kịch bản"}, headers=cors_headers())

        script_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        selected_script = None
        for sf in script_files:
            parent_dir = sf.parent
            exported_vids = list(parent_dir.glob("*.mp4"))
            # Match against exported video filenames or check script metadata
            if any(video_stem in v.name.lower() for v in exported_vids):
                selected_script = sf
                break
            try:
                with open(sf, "r", encoding="utf-8") as f:
                    s_data = json.load(f)
                s_title = (s_data.get("title") or "").lower()
                if video_stem in s_title or s_title in video_stem:
                    selected_script = sf
                    break
            except Exception:
                pass

        if not selected_script:
            return web.json_response({"status": "empty", "message": "Chưa có kịch bản cho video này"}, headers=cors_headers())

        with open(selected_script, "r", encoding="utf-8") as f:
            data = json.load(f)
        return web.json_response({"status": "ok", "script": data}, headers=cors_headers())
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500, headers=cors_headers())


async def handle_get_movie_info(request):
    try:
        video_file = RECAP_ROOT / "demo_real_movie.mp4"
        srt_file = RECAP_ROOT / "demo_movie.srt"
        meta = {
            "title": "Âm Mưu Ngày Cưới Của Thợ Trang Điểm",
            "filename": "demo_real_movie.mp4",
            "rel_url": "/source/demo_real_movie.mp4",
            "full_path": str(video_file),
            "duration": 1382.4,
            "duration_hms": "00:23:02",
            "size_mb": 55.0,
            "width": 1920,
            "height": 1080,
            "has_srt": srt_file.exists()
        }
        return web.json_response({"status": "ok", "movie": meta}, headers=cors_headers())
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500, headers=cors_headers())


async def handle_auto_scan(request):
    try:
        data = {}
        if request.can_read_body:
            try:
                data = await request.json()
            except Exception:
                pass
        video_path = data.get("video_path")
        enable_visual = data.get("enable_visual_scan", True)
        p = find_video_file(video_path)
        analyzer = VideoAnalyzer(str(p.resolve()))
        res = analyzer.auto_scan_and_configure(enable_visual_scan=enable_visual)
        return web.json_response(res, headers=cors_headers())
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500, headers=cors_headers())


def create_app():
    app = web.Application()
    app.router.add_route("OPTIONS", "/{tail:.*}", handle_options)
    app.router.add_get("/", handle_index)
    app.router.add_get("/api/status", handle_status)
    app.router.add_get("/api/config", handle_get_config)
    app.router.add_post("/api/config", handle_save_config)
    app.router.add_post("/api/test-key", handle_test_key)
    app.router.add_post("/api/test-keys", handle_test_keys)
    app.router.add_post("/api/fetch-url", handle_fetch_url)
    app.router.add_post("/api/analyze", handle_analyze_video)
    app.router.add_get("/api/scan-auto", handle_auto_scan)
    app.router.add_post("/api/scan-auto", handle_auto_scan)
    app.router.add_post("/api/script/generate", handle_generate_script)
    app.router.add_post("/api/script/translate", handle_translate_script)
    app.router.add_post("/api/bgm/upload", handle_upload_bgm)
    app.router.add_get("/api/script/current", handle_get_current_script)
    app.router.add_get("/api/movie/info", handle_get_movie_info)
    app.router.add_post("/api/voice/preview", handle_preview_voice)
    app.router.add_post("/api/render", handle_start_render)
    app.router.add_get("/api/progress/{job_id}", handle_get_progress)
    app.router.add_get("/api/videos/list", handle_list_videos)
    app.router.add_get("/api/exports", handle_get_exports)
    app.router.add_post("/api/exports/delete", handle_delete_export)
    app.router.add_post("/api/open-folder", handle_open_folder)

    # Static file serving for exports and source videos
    global EXPORT_DIR
    try:
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        EXPORT_DIR = RECAP_ROOT / "exports"
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    app.router.add_static("/exports/", path=str(EXPORT_DIR), show_index=True)
    app.router.add_static("/source/", path=str(RECAP_ROOT), show_index=True)
    (WEB_DIR / "assets").mkdir(parents=True, exist_ok=True)
    app.router.add_static("/assets/", path=str(WEB_DIR / "assets"), show_index=False)

    return app


if __name__ == "__main__":
    app = create_app()
    print("🚀 Movie Recap Studio Server starting on http://localhost:8095", flush=True)
    web.run_app(app, host="0.0.0.0", port=8095)
