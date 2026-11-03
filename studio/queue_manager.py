"""Storyboard AI Studio - Production Queue Manager.
Enables sequential batch processing (cắm máy chạy qua đêm) for multiple episodes/videos.
Handles automatic queue progression, error resilience, retry options, and PC shutdown on finish.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
import uuid
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

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

STUDIO_DIR = Path(__file__).resolve().parent
QUEUE_FILE = STUDIO_DIR / "production_queue.json"
QUEUE_LOCK = threading.Lock()

SERVER_PORT = int(os.environ.get("STUDIO_PORT", 8765))


def get_server_port() -> int:
    global SERVER_PORT
    env_p = os.environ.get("STUDIO_PORT")
    if env_p and env_p.isdigit():
        return int(env_p)
    return SERVER_PORT


def set_server_port(port: int):
    global SERVER_PORT
    SERVER_PORT = int(port)
    os.environ["STUDIO_PORT"] = str(port)


def _default_queue() -> dict:
    return {
        "active": False,
        "current_job_id": None,
        "auto_next": True,
        "shutdown_on_complete": False,
        "items": []
    }


def load_queue() -> dict:
    """Loads queue state from disk with thread-safety."""
    with QUEUE_LOCK:
        if not QUEUE_FILE.is_file():
            data = _default_queue()
            try:
                QUEUE_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            except Exception:
                pass
            return data

        try:
            return json.loads(QUEUE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return _default_queue()


def save_queue(data: dict) -> None:
    """Saves queue state to disk atomically."""
    with QUEUE_LOCK:
        try:
            tmp = QUEUE_FILE.with_suffix(".tmp")
            tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            tmp.replace(QUEUE_FILE)
        except Exception as exc:
            print(f"[QUEUE_ERROR] Không thể lưu production_queue.json: {exc}", flush=True)


def get_queue_status() -> dict:
    """Returns the current queue status including counts and list of items."""
    q = load_queue()
    items = q.get("items", [])
    pending = [it for it in items if it.get("status") == "pending"]
    running = [it for it in items if it.get("status") == "running"]
    completed = [it for it in items if it.get("status") == "completed"]
    failed = [it for it in items if it.get("status") == "failed"]

    return {
        "ok": True,
        "active": bool(q.get("active", False)),
        "auto_next": bool(q.get("auto_next", True)),
        "shutdown_on_complete": bool(q.get("shutdown_on_complete", False)),
        "current_job_id": q.get("current_job_id"),
        "total_jobs": len(items),
        "pending_count": len(pending),
        "running_count": len(running),
        "completed_count": len(completed),
        "failed_count": len(failed),
        "items": items
    }


def add_job(config: dict, auto_activate: bool = False) -> dict:
    """Adds a single job config to the queue and places it in pending status."""
    q = load_queue()
    items = q.get("items", [])

    job_id = f"job_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    series = str(config.get("series", "My Series")).strip() or "My Series"
    episode = int(config.get("episode", 1))
    prod_mode = str(config.get("production_mode", "narrative")).strip().lower()
    img_prov = str(config.get("image_provider", "muse_video" if prod_mode == "cinematic_drama" else "mcp_v2"))
    input_mode = str(config.get("input_mode", "idea"))
    ref_url = str(config.get("reference_url", "")).strip()
    prompt = str(config.get("prompt", "")).strip()
    minutes = float(config.get("minutes", 2.0))

    # Sanitize and ensure valid visual_style, genre, region
    v_style = str(config.get("visual_style") or "").strip()
    if not v_style or v_style not in ("auto", "color_cinematic", "color_animation", "whiteboard", "hand_color", "flow_video", "colored_marker"):
        v_style = "flow_video" if prod_mode == "cinematic_drama" else "color_cinematic"
    config["visual_style"] = v_style

    if not config.get("genre"):
        config["genre"] = "family_drama" if prod_mode == "cinematic_drama" else "auto"
    if not config.get("region"):
        config["region"] = "auto"

    mode_label = "Phim Kịch Đa Vai (Muse AI)" if prod_mode == "cinematic_drama" else f"Thuyết Minh ({img_prov})"
    source_label = ref_url[:60] if input_mode == "link" and ref_url else prompt[:60] or f"Tập {episode}"
    title = f"{series} - Tập {episode} ({mode_label})"

    job = {
        "id": job_id,
        "series": series,
        "episode": episode,
        "title": title,
        "source_label": source_label,
        "production_mode": prod_mode,
        "image_provider": img_prov,
        "input_mode": input_mode,
        "minutes": minutes,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "started_at": None,
        "completed_at": None,
        "duration_seconds": 0,
        "error": None,
        "config": config
    }

    items.append(job)
    q["items"] = items

    # Only activate if explicitly requested or queue is already active
    if auto_activate and not q.get("active"):
        q["active"] = True

    save_queue(q)
    print(f"[QUEUE] Đã thêm công việc vào hàng chờ: {title} (ID: {job_id})", flush=True)

    # If queue is already active and nothing is currently running, dispatch next
    if q.get("active") and not q.get("current_job_id"):
        _dispatch_next_job()

    return {"ok": True, "job": job, "queue_status": get_queue_status()}


def bulk_add_jobs(raw_links: list[str] | str, base_config: dict) -> dict:
    """Takes a list of YouTube links or prompts and creates sequential episode jobs."""
    if isinstance(raw_links, str):
        lines = [line.strip() for line in raw_links.splitlines() if line.strip()]
    else:
        lines = [str(line).strip() for line in raw_links if str(line).strip()]

    if not lines:
        return {"ok": False, "error": "Danh sách link/ý tưởng trống."}

    q = load_queue()
    items = q.get("items", [])
    added = []

    start_ep = int(base_config.get("episode", 1))
    series = str(base_config.get("series", "Series Phim")).strip() or "Series Phim"
    prod_mode = str(base_config.get("production_mode", "cinematic_drama")).strip().lower()
    img_prov = "muse_video" if prod_mode == "cinematic_drama" else str(base_config.get("image_provider", "mcp_v2"))

    for idx, line in enumerate(lines):
        ep_num = start_ep + idx
        is_url = line.startswith("http://") or line.startswith("https://") or "youtube.com" in line or "youtu.be" in line

        job_cfg = dict(base_config)
        job_cfg["series"] = series
        job_cfg["episode"] = ep_num
        job_cfg["production_mode"] = prod_mode
        job_cfg["image_provider"] = img_prov

        v_style = str(job_cfg.get("visual_style") or "").strip()
        if not v_style or v_style not in ("auto", "color_cinematic", "color_animation", "whiteboard", "hand_color", "flow_video", "colored_marker"):
            v_style = "flow_video" if prod_mode == "cinematic_drama" else "color_cinematic"
        job_cfg["visual_style"] = v_style

        if not job_cfg.get("genre"):
            job_cfg["genre"] = "family_drama" if prod_mode == "cinematic_drama" else "auto"
        if not job_cfg.get("region"):
            job_cfg["region"] = "auto"

        if is_url:
            job_cfg["input_mode"] = "link"
            job_cfg["reference_url"] = line
            job_cfg["prompt"] = line
        else:
            job_cfg["input_mode"] = "idea"
            job_cfg["prompt"] = line

        job_id = f"job_{int(time.time())}_{idx+1:02d}_{uuid.uuid4().hex[:4]}"
        mode_label = "Phim Kịch Đa Vai (Muse)" if prod_mode == "cinematic_drama" else f"Thuyết Minh ({img_prov})"
        title = f"{series} - Tập {ep_num} ({mode_label})"

        job = {
            "id": job_id,
            "series": series,
            "episode": ep_num,
            "title": title,
            "source_label": line[:60],
            "production_mode": prod_mode,
            "image_provider": img_prov,
            "input_mode": job_cfg["input_mode"],
            "minutes": float(job_cfg.get("minutes", 2.0)),
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "started_at": None,
            "completed_at": None,
            "duration_seconds": 0,
            "error": None,
            "config": job_cfg
        }
        items.append(job)
        added.append(job)

    q["items"] = items
    save_queue(q)

    print(f"[QUEUE] Đã thêm hàng loạt {len(added)} công việc vào hàng chờ (Tập {start_ep} -> {start_ep + len(added) - 1})!", flush=True)

    # Only dispatch if queue is already active
    if q.get("active") and not q.get("current_job_id"):
        _dispatch_next_job()

    return {"ok": True, "count": len(added), "added": added, "queue_status": get_queue_status()}


def remove_job(job_id: str) -> dict:
    """Removes a job from queue by ID."""
    q = load_queue()
    items = q.get("items", [])
    new_items = []
    found = False

    for it in items:
        if it.get("id") == job_id:
            found = True
            if it.get("status") == "running":
                return {"ok": False, "error": "Không thể xóa công việc đang chạy. Hãy bấm Dừng trước."}
        else:
            new_items.append(it)

    if found:
        q["items"] = new_items
        if q.get("current_job_id") == job_id:
            q["current_job_id"] = None
        save_queue(q)
        return {"ok": True, "queue_status": get_queue_status()}

    return {"ok": False, "error": f"Không tìm thấy công việc {job_id}"}


def clear_queue(mode: str = "completed_failed") -> dict:
    """Clears completed or all pending jobs."""
    q = load_queue()
    items = q.get("items", [])

    if mode == "all":
        # Keep only currently running
        q["items"] = [it for it in items if it.get("status") == "running"]
    else:
        # Keep pending and running, remove completed and failed
        q["items"] = [it for it in items if it.get("status") in ("pending", "running")]

    save_queue(q)
    return {"ok": True, "queue_status": get_queue_status()}


def set_shutdown_on_complete(enabled: bool) -> dict:
    """Enables or disables automatic PC shutdown when queue completes."""
    q = load_queue()
    q["shutdown_on_complete"] = bool(enabled)
    save_queue(q)
    return {"ok": True, "shutdown_on_complete": q["shutdown_on_complete"]}


def start_queue() -> dict:
    """Activates the queue runner and dispatches the first pending job."""
    q = load_queue()
    q["active"] = True
    save_queue(q)

    print(f"[QUEUE] Đã kích hoạt chế độ chạy hàng chờ tự động!", flush=True)

    port = get_server_port()
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{port}/api/status")
        with urllib.request.urlopen(req, timeout=3) as r:
            st = json.loads(r.read())
            if st.get("running"):
                print(f"[QUEUE] Máy chủ đang bận sản xuất tập phim hiện tại. Hàng chờ sẽ tự động chạy tiếp khi xong.", flush=True)
                return {"ok": True, "message": "Hàng chờ đã kích hoạt; đang đợi tiến trình hiện tại hoàn tất.", "queue_status": get_queue_status()}
    except Exception:
        pass

    _dispatch_next_job()
    return {"ok": True, "message": "Đã bắt đầu xử lý hàng chờ!", "queue_status": get_queue_status()}


def pause_queue() -> dict:
    """Deactivates auto-progression. Current job will finish, but next job won't start."""
    q = load_queue()
    q["active"] = False
    save_queue(q)
    print(f"[QUEUE] Đã tạm dừng hàng chờ tự động. Tiến trình hiện tại vẫn sẽ hoàn thành bình thường.", flush=True)
    return {"ok": True, "message": "Đã tạm dừng hàng chờ.", "queue_status": get_queue_status()}


def _dispatch_next_job():
    """Finds the next pending job and triggers production via /api/produce with retry and 409 conflict backoff."""
    def _run():
        time.sleep(0.5)
        q = load_queue()
        if not q.get("active"):
            return

        items = q.get("items", [])
        next_job = None
        for it in items:
            if it.get("status") == "pending":
                next_job = it
                break

        if not next_job:
            print(f"\n=======================================================", flush=True)
            print(f"🎉 [QUEUE HOÀN TẤT] TẤT CẢ CÔNG VIỆC TRONG HÀNG CHỜ ĐÃ XONG!", flush=True)
            print(f"=======================================================\n", flush=True)
            q["active"] = False
            q["current_job_id"] = None
            save_queue(q)

            if q.get("shutdown_on_complete"):
                print(f"[QUEUE_SHUTDOWN] Cảnh báo: Tự động tắt máy trong 60 giây theo thiết lập của bạn...", flush=True)
                try:
                    subprocess.run(["shutdown", "/s", "/t", "60", "/c", "Storyboard AI Studio: Hàng chờ đã hoàn tất! Đang tự động tắt máy..."])
                except Exception as shut_err:
                    print(f"[QUEUE_SHUTDOWN_ERROR] {shut_err}", flush=True)
            return

        port = get_server_port()
        status_url = f"http://127.0.0.1:{port}/api/status"
        produce_url = f"http://127.0.0.1:{port}/api/produce"

        # Pre-check: wait until server is idle (running == False) before sending produce request
        for _wait_cycle in range(30):
            try:
                req = urllib.request.Request(status_url)
                with urllib.request.urlopen(req, timeout=3) as r:
                    st = json.loads(r.read())
                    if not st.get("running"):
                        break
            except Exception:
                pass
            time.sleep(2.0)

        # Normalize and guarantee valid style/genre before dispatch
        cfg = next_job.get("config", {})
        prod_m = str(cfg.get("production_mode") or next_job.get("production_mode") or "narrative").lower()
        if not cfg.get("visual_style") or cfg.get("visual_style") not in ("color_cinematic", "color_animation", "whiteboard", "hand_color", "flow_video", "colored_marker", "auto"):
            cfg["visual_style"] = "flow_video" if prod_m == "cinematic_drama" else "color_cinematic"
        if not cfg.get("genre"):
            cfg["genre"] = "family_drama" if prod_m == "cinematic_drama" else "auto"
        if not cfg.get("region"):
            cfg["region"] = "auto"
        next_job["config"] = cfg

        next_job["status"] = "running"
        next_job["started_at"] = datetime.now().isoformat()
        q["current_job_id"] = next_job["id"]
        save_queue(q)

        print(f"\n=======================================================", flush=True)
        print(f"🚀 [QUEUE TIẾP TỤC] BẮT ĐẦU CÔNG VIỆC: {next_job.get('title')}", flush=True)
        print(f"   Thời gian: {next_job.get('started_at')}", flush=True)
        print(f"=======================================================\n", flush=True)

        # Retry loop for POST /api/produce (handles 409 Conflict with backoff)
        success = False
        last_error = ""
        for post_attempt in range(1, 6):
            try:
                req_data = json.dumps(next_job["config"]).encode("utf-8")
                req = urllib.request.Request(
                    produce_url,
                    data=req_data,
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=20) as resp:
                    res_body = json.loads(resp.read().decode("utf-8", errors="replace"))
                    if res_body.get("error"):
                        raise RuntimeError(res_body.get("error"))
                    print(f"[QUEUE] Đã kích hoạt sản xuất thành công cho {next_job.get('title')}!", flush=True)
                    success = True
                    break
            except urllib.error.HTTPError as http_err:
                if http_err.code == 409:
                    print(f"[QUEUE] Máy chủ đang hoàn tất tập trước (409 Conflict), chờ 4s rồi thử lại lần {post_attempt}/5...", flush=True)
                    time.sleep(4.0)
                    continue
                else:
                    try:
                        err_text = http_err.read().decode("utf-8", errors="replace")
                        err_json = json.loads(err_text)
                        last_error = err_json.get("error", str(http_err))
                    except Exception:
                        last_error = str(http_err)
                    break
            except Exception as p_err:
                last_error = str(p_err)
                print(f"[QUEUE_RETRY] Lỗi kết nối máy chủ ({last_error}), chờ 3s thử lại lần {post_attempt}/5...", flush=True)
                time.sleep(3.0)

        if not success:
            print(f"[QUEUE_ERROR] Không thể khởi chạy công việc {next_job.get('title')}: {last_error}", flush=True)
            next_job["status"] = "failed"
            next_job["error"] = last_error
            next_job["completed_at"] = datetime.now().isoformat()
            q["current_job_id"] = None
            save_queue(q)

            # Move to next job after 5s delay so error doesn't halt the whole queue
            if q.get("active"):
                threading.Thread(target=_dispatch_next_job, daemon=True).start()

    threading.Thread(target=_run, daemon=True).start()


def on_job_completed(series: str, episode: int, exit_code: int, was_stopped: bool = False):
    """Callback invoked by web_server worker_thread when any episode production completes."""
    q = load_queue()
    items = q.get("items", [])
    cur_id = q.get("current_job_id")

    matched_job = None
    if cur_id:
        for it in items:
            if it.get("id") == cur_id:
                matched_job = it
                break

    if not matched_job:
        from series_studio import slug
        try:
            target_slug = slug(str(series or ""))
            ep_target = int(episode or 0)
            for it in items:
                it_slug = slug(str(it.get("series", "") or ""))
                it_ep = int(it.get("episode", 0) or 0)
                if it_slug == target_slug and it_ep == ep_target:
                    if it.get("status") in ("running", "pending"):
                        matched_job = it
                        break
        except Exception:
            pass

    if matched_job:
        now_iso = datetime.now().isoformat()
        matched_job["completed_at"] = now_iso
        if matched_job.get("started_at"):
            try:
                t_start = datetime.fromisoformat(matched_job["started_at"])
                t_end = datetime.fromisoformat(now_iso)
                matched_job["duration_seconds"] = int((t_end - t_start).total_seconds())
            except Exception:
                pass

        if was_stopped:
            matched_job["status"] = "cancelled"
            matched_job["error"] = "Người dùng đã dừng tiến trình."
        elif exit_code == 0:
            matched_job["status"] = "completed"
            matched_job["error"] = None
            # Auto-upload completed episode to YouTube if enabled
            if bool(matched_job.get("config", {}).get("auto_upload", False)):
                try:
                    import youtube_manager
                    from series_studio import slug
                    s_name = str(matched_job.get("series", ""))
                    ep_no = int(matched_job.get("episode", 1))
                    ep_dir = STUDIO_DIR / "productions" / slug(s_name) / f"episode_{ep_no:03d}"
                    if not ep_dir.is_dir():
                        for cand in (STUDIO_DIR / "productions").iterdir():
                            if cand.is_dir() and (cand.name.lower() == s_name.lower() or slug(cand.name) == slug(s_name)):
                                ep_dir = cand / f"episode_{ep_no:03d}"
                                break
                    if ep_dir.is_dir() and not (ep_dir / "youtube_uploaded.json").is_file():
                        print(f"\n[QUEUE_YOUTUBE] 🚀 Tự động đăng '{matched_job.get('title')}' lên YouTube...", flush=True)
                        yt_up = youtube_manager.auto_upload_episode(
                            episode_dir=ep_dir,
                            series_name=s_name,
                            language=str(matched_job.get("config", {}).get("language", "")),
                            privacy_status="unlisted"
                        )
                        if yt_up.get("ok"):
                            print(f"[QUEUE_YOUTUBE] 🎉 Đã tự động đăng thành công: {yt_up.get('video_url')}", flush=True)
                        else:
                            print(f"[QUEUE_YOUTUBE] Bỏ qua hoặc thông báo: {yt_up.get('reason') or yt_up.get('error')}", flush=True)
                except Exception as q_yt_e:
                    print(f"[QUEUE_YOUTUBE_WARN] Lỗi tự động tải lên YouTube: {q_yt_e}", flush=True)
        else:
            matched_job["status"] = "failed"
            matched_job["error"] = f"Tiến trình kết thúc với mã lỗi {exit_code}."

        q["current_job_id"] = None
        save_queue(q)

        print(f"[QUEUE] Công việc '{matched_job.get('title')}' đã kết thúc (Trạng thái: {matched_job.get('status')})", flush=True)

    # If queue is active and wasn't manually stopped, advance to next job after a short cooldown
    if q.get("active") and not was_stopped:
        def _cooldown_and_next():
            cooldown_sec = 6
            print(f"[QUEUE] Nghỉ {cooldown_sec} giây làm nguội hệ thống trước khi bắt đầu công việc tiếp theo...", flush=True)
            time.sleep(cooldown_sec)
            _dispatch_next_job()

        threading.Thread(target=_cooldown_and_next, daemon=True).start()
    elif was_stopped:
        q["active"] = False
        save_queue(q)


def retry_job(job_id: str) -> dict:
    """Resets a failed or cancelled job back to pending with resume enabled, and activates the queue."""
    q = load_queue()
    items = q.get("items", [])
    found_job = None
    for it in items:
        if it.get("id") == job_id:
            found_job = it
            it["status"] = "pending"
            it["error"] = None
            it["started_at"] = None
            it["completed_at"] = None
            if not isinstance(it.get("config"), dict):
                it["config"] = {}
            it["config"]["resume"] = True
            prod_m = str(it["config"].get("production_mode") or it.get("production_mode") or "narrative").lower()
            if not it["config"].get("visual_style") or it["config"].get("visual_style") not in ("color_cinematic", "color_animation", "whiteboard", "hand_color", "flow_video", "colored_marker", "auto"):
                it["config"]["visual_style"] = "flow_video" if prod_m == "cinematic_drama" else "color_cinematic"
            if not it["config"].get("genre"):
                it["config"]["genre"] = "family_drama" if prod_m == "cinematic_drama" else "auto"
            if not it["config"].get("region"):
                it["config"]["region"] = "auto"
            break

    if not found_job:
        return {"ok": False, "error": f"Không tìm thấy công việc {job_id}"}

    q["active"] = True
    save_queue(q)
    print(f"[QUEUE] 🔄 Đã kích hoạt chạy lại công việc '{found_job.get('title')}' (Chế độ Resume - Chạy tiếp cảnh thiếu).", flush=True)

    if not q.get("current_job_id"):
        _dispatch_next_job()

    return {"ok": True, "message": f"Đã đưa '{found_job.get('title')}' trở lại hàng chờ (chạy tiếp).", "queue_status": get_queue_status()}
