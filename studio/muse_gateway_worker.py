"""Saved-session gateway worker with durable receipts and binary download resume.
Runs in the Muse virtualenv, independently of Studio's Python dependencies.
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
import os
import re
import math
import subprocess
import sys
import time
import uuid
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from urllib.parse import unquote

PATH_RE = re.compile(r"(?:/home/hatch)?/workspace/[A-Za-z0-9_./%+\-]+\.(?:webp|png|jpe?g|mp4)", re.I)


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    with temp.open("w", encoding="utf-8") as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.flush(); os.fsync(f.fileno())
    os.replace(temp, path)


def digest(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def workspace_path(path):
    path = unquote(path)
    if path.startswith("/home/hatch/workspace/"):
        path = "workspace/" + path[len("/home/hatch/workspace/"):]
    elif path.startswith("/workspace/"):
        path = path[1:]
    if not path.startswith("workspace/") or ".." in PurePosixPath(path).parts or "\\" in path or ":" in path:
        raise ValueError("MUSE_INVALID_OUTPUT_PATH")
    return path


@contextmanager
def render_lock(path, timeout=900):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    f = path.open("a+b")
    f.seek(0, os.SEEK_END)
    if not f.tell():
        f.write(b"0"); f.flush()
    acquired = False
    deadline = time.monotonic() + timeout
    try:
        while not acquired:
            f.seek(0)
            try:
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
            except OSError:
                if time.monotonic() >= deadline:
                    raise RuntimeError("MUSE_QUEUE_BUSY: Có cảnh Muse khác đang xử lý; chạy tiếp sau.")
                time.sleep(1)
        yield
    finally:
        if acquired:
            f.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        f.close()


class GatewayAPI:
    def __init__(self):
        from muse_cli.cli import load_config
        self.cfg = load_config()
        self.gateway = None

    @property
    def account_vm_id(self):
        return self.gateway.vm_id if self.gateway else None

    def _connect(self):
        if self.gateway is not None:
            return
        from muse_cli.cli import connect, load_cookies
        from muse_cli.gateway import fetch_session_info, fetch_access_token, _hatch_headers
        from curl_cffi import requests as rq
        cookies_file = self.cfg.get("cookies_file")
        if cookies_file and os.path.exists(cookies_file):
            try:
                cookies = load_cookies(cookies_file)
                info = fetch_session_info(cookies)
                if info.get("vm_state") == "SUSPENDED":
                    at = fetch_access_token(cookies)
                    vm_id = info.get("vm_id") or self.cfg.get("vm_id")
                    rq.post("https://muse.ai/api/hatch/vm/wake",
                            headers=_hatch_headers(cookies, at),
                            json={"vm_id": vm_id, "retry_count": 0},
                            impersonate="chrome", timeout=15)
                    for _ in range(12):
                        time.sleep(2)
                        fresh = fetch_session_info(cookies)
                        if fresh.get("vm_state") == "RUNNING":
                            break
            except Exception:
                pass
        self.gateway = connect(self.cfg)

    def call(self, method, body=None):
        from muse_cli.gateway import AuthError, GatewayError
        # Only reads reconnect. Mutating session creation is never replayed.
        attempts = 3 if method in ("chat.history", "sessions.list", "fs.stat", "fs.read") else 1
        for attempt in range(attempts):
            try:
                if self.gateway is None:
                    self._connect()
                return self.gateway.call_json(method, body=body, timeout=30)
            except AuthError:
                self.close()
                raise RuntimeError("MUSE_AUTH_REQUIRED: Phiên Muse đã hết hạn hoặc chưa được lưu. Đăng nhập lại rồi kết nối Muse.") from None
            except GatewayError as ge:
                self.close()
                if hasattr(ge, "payload") and isinstance(ge.payload, str) and ge.payload.startswith("MUSE_"):
                    raise RuntimeError(ge.payload) from None
                raise RuntimeError(str(ge)) from None
            except Exception:
                self.close()
                if attempt + 1 == attempts:
                    raise RuntimeError("MUSE_CONNECTION_INTERRUPTED: Chưa nhận phản hồi gateway. Chạy tiếp để kiểm tra job đã lưu.") from None
                time.sleep(2 * (attempt + 1))

    def close(self):
        if self.gateway:
            self.gateway.close()
            self.gateway = None


def submit_once(sid, prompt, tag):
    env = os.environ.copy()
    env.update(MUSE_NO_UPDATE_CHECK="1", PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    try:
        p = subprocess.run([sys.executable, "-m", "muse_cli", "send", prompt, "--thread", sid, "--wait", "1"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=90,
                           env=env, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return p.returncode == 0 and json.loads(p.stdout).get("sent") is True
    except (ValueError, subprocess.TimeoutExpired):
        return False


def download(api, remote_path, target):
    remote_path = workspace_path(remote_path)
    target = Path(target)
    stat = api.call("fs.stat", {"path": remote_path})
    if stat.get("kind") != "file" or not 0 < stat.get("size", 0) < 256 * 1024 * 1024:
        raise RuntimeError("MUSE_INVALID_FILE")
    part = target.with_suffix(target.suffix + ".part")
    sidecar = part.with_suffix(".part.json")
    identity = {"path": remote_path, "size": stat["size"], "modified_ms": stat.get("modified_ms")}
    try:
        old = json.loads(sidecar.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        old = None
    if old != identity or (part.exists() and part.stat().st_size > stat["size"]):
        part.unlink(missing_ok=True)
    atomic_json(sidecar, identity)
    offset = part.stat().st_size if part.exists() else 0
    with part.open("ab") as f:
        while offset < stat["size"]:
            d = api.call("fs.read", {"path": remote_path, "offset": offset, "len": 2097152})
            raw = base64.b64decode(d["data_base64"], validate=True)
            if d.get("offset") != offset or len(raw) != d.get("len") or not raw or offset + len(raw) > stat["size"]:
                raise RuntimeError("MUSE_INVALID_DOWNLOAD_CHUNK")
            if bool(d.get("eof")) != (offset + len(raw) == stat["size"]):
                raise RuntimeError("MUSE_INVALID_DOWNLOAD_EOF")
            f.write(raw); f.flush(); os.fsync(f.fileno())
            offset += len(raw)
    after = api.call("fs.stat", {"path": remote_path})
    if (after.get("size"), after.get("modified_ms")) != (stat["size"], stat.get("modified_ms")):
        part.unlink(missing_ok=True)
        raise RuntimeError("MUSE_REMOTE_FILE_CHANGED")
    os.replace(part, target)
    sidecar.unlink(missing_ok=True)
    return {"remote_path": remote_path, "path": str(target), "bytes": target.stat().st_size, "sha256": digest(target)}


def inspect_video(path):
    import av
    result = {"video_frames_decoded": 0, "audio_frames_decoded": 0}
    with av.open(str(path)) as c:
        videos = list(c.streams.video)
        if len(videos) != 1:
            raise RuntimeError("MUSE_INVALID_VIDEO_STREAMS")
        v = videos[0]
        v.codec_context.options = {"err_detect": "explode"}
        duration = float(v.duration * v.time_base) if v.duration is not None else float(c.duration / av.time_base)
        result.update(width=v.width, height=v.height, duration_seconds=duration,
                      fps=float(v.average_rate) if v.average_rate else None,
                      audio_codecs=[a.codec_context.name for a in c.streams.audio])
        for packet in c.demux():
            for frame in packet.decode():
                if isinstance(frame, av.VideoFrame):
                    result["video_frames_decoded"] += 1
                elif isinstance(frame, av.AudioFrame):
                    result["audio_frames_decoded"] += 1
    expected = round(duration * result["fps"]) if result["fps"] else 0
    if not 0.5 <= duration <= 120 or not result["video_frames_decoded"] or (expected and abs(result["video_frames_decoded"] - expected) > 1):
        raise RuntimeError("MUSE_VIDEO_DECODE_FAILED")
    return result


def needs_cinematic_letterbox(source_width, source_height, target_width, target_height):
    if min(source_width, source_height, target_width, target_height) <= 0:
        return False
    source_ratio = float(source_width) / float(source_height)
    target_ratio = float(target_width) / float(target_height)
    return (
        abs(source_ratio / target_ratio - 1) > .05
        and 2.30 <= source_ratio <= 2.50
        and 1.70 <= target_ratio <= 1.90
    )


def letterbox_cinematic_video(path, target_width, target_height):
    import shutil
    path = Path(path)
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("MUSE_FFMPEG_MISSING: ffmpeg không có trong PATH.")
    target_width, target_height = int(target_width), int(target_height)
    temp = path.with_name(path.stem + ".letterbox.tmp.mp4")
    video_filter = (
        f"scale={target_width}:{target_height}:force_original_aspect_ratio=decrease:force_divisible_by=2,"
        f"pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2:color=black"
    )
    try:
        proc = subprocess.run(
            [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(path),
             "-map", "0:v:0", "-map", "0:a?", "-vf", video_filter,
             "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(temp)],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.TimeoutExpired):
        temp.unlink(missing_ok=True)
        raise RuntimeError("MUSE_ASPECT_CONFORM_FAILED: Không thể chuyển clip điện ảnh sang khung cảnh.") from None
    if proc.returncode != 0 or not temp.is_file() or temp.stat().st_size == 0:
        temp.unlink(missing_ok=True)
        detail = (proc.stderr or "").strip()[-300:]
        suffix = ": " + detail if detail else ""
        raise RuntimeError("MUSE_ASPECT_CONFORM_FAILED" + suffix)
    os.replace(temp, path)


def run_render(request, *, api=None, submit=None, poll_interval=10, timeout=600):
    from PIL import Image, ImageOps
    output = Path(request["output_image_path"]).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    receipt_path = output.parent / "muse_job.json"
    fingerprint = hashlib.sha256(json.dumps({k: request[k] for k in ("prompt", "width", "height", "duration")}, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    receipt = json.loads(receipt_path.read_text(encoding="utf-8")) if receipt_path.exists() else {}
    if receipt and receipt.get("fingerprint") != fingerprint:
        raise RuntimeError("MUSE_SCENE_INPUT_CHANGED: Cảnh có job Muse từ cấu hình khác. Hãy tạo tập mới để không ghi đè hoặc tạo trùng.")
    if receipt.get("state") in ("video_retry_ready", "video_retry_pending"):
        raise RuntimeError("MUSE_MANUAL_VIDEO_RECOVERY_REQUIRED: auto retry disabled for this independent tool.")
    if receipt.get("state") == "failed":
        # Fail closed: only a deliberate recovery action may create another remote job.
        raise RuntimeError("MUSE_REMOTE_FAILED: Job Muse cũ đã thất bại; không tự tạo lại.")
    if receipt.get("state") == "complete":
        result = receipt["result"]
        if all(Path(m["path"]).is_file() and digest(m["path"]) == m["sha256"] for m in (result["image"], result["video"])):
            return result
    own_api = api is None
    api = api or GatewayAPI()
    submit = submit or submit_once
    try:
        created_now = False

        def build_scene_prompt(tag):
            divider = math.gcd(int(request["width"]), int(request["height"]))
            ratio = f"{int(request['width']) // divider}:{int(request['height']) // divider}"
            return (f"Run exactly one image-to-video scene job, ID {tag}. No user reference image is needed. "
                    f"First use media.generate_image once to create the scene image, composition ratio {ratio}, name {tag}_image. "
                    f"Then use media.generate_video once with that exact returned local image path as a kind=image entry, name {tag}_video. "
                    f"Aim for a short {request['duration']}-second clip. Preserve the image composition. "
                    "Wait for actual tool completion. Return exact local image_path and video_path in the final visible reply. "
                    "Do not retry a failed generation or produce extra variants. Report tool failures accurately.\n" + request["prompt"])

        def build_video_retry_prompt(tag, image_tool_path):
            return (f"Run exactly one video-only recovery, ID {tag}. Do not call media.generate_image. "
                    f"Use this exact existing local image path as a kind=image entry for media.generate_video: {image_tool_path}. "
                    f"Create a {request['duration']}-second video named {tag}_video, preserving the image composition. "
                    "Wait for actual tool completion and return the exact image_path and video_path. "
                    "If video generation fails, report the error accurately and do not retry.")

        if not receipt:
            data = api.call("session.start", {"method": "/api/session/start", "params": {"origin": "fresh", "lifecycle": "persistent", "title": "Muse Film Studio scene " + output.parent.name}})
            sid = data.get("session_id") or data.get("id") or (data.get("session") or {}).get("session_id") or (data.get("session") or {}).get("id")
            if not sid:
                raise RuntimeError("MUSE_SESSION_NOT_CREATED")
            receipt = {"fingerprint": fingerprint, "session_id": sid, "tag": "mfs" + uuid.uuid4().hex[:20], "state": "submission_uncertain", "account_vm_id": getattr(api, "account_vm_id", None)}
            # Intent is durable BEFORE sending; a killed sender is never replayed.
            atomic_json(receipt_path, receipt)
            created_now = True
            tag = receipt["tag"]
            receipt["cli_ack"] = bool(submit(sid, build_scene_prompt(tag), tag))
            atomic_json(receipt_path, receipt)
        if not created_now and receipt.get("cli_ack") is False:
            raise RuntimeError("MUSE_NEGATIVE_ACK: remote state uncertain; auto-resubmission disabled.")
        sid, original_tag = receipt["session_id"], receipt["tag"]
        tag = original_tag
        assistant_after_seq = 0

        def begin_video_retry():
            nonlocal tag, assistant_after_seq
            image_remote = receipt.get("image_remote")
            image_tool_path = receipt.get("image_tool_path")
            if not image_remote or not image_tool_path:
                raise RuntimeError("MUSE_VIDEO_RETRY_INPUT_MISSING: Thiếu ảnh Muse đã xác minh để thử lại riêng phần video.")
            if receipt.get("video_retry_attempted"):
                raise RuntimeError("MUSE_VIDEO_RETRY_ALREADY_ATTEMPTED: Lượt khôi phục video đã được gửi; tiếp tục theo dõi session cũ.")
            prior_history = api.call("chat.history", {"session_id": sid, "limit": 60}).get("chat_events", [])
            assistant_after_seq = max((int(e.get("seq") or 0) for e in prior_history), default=0)
            tag = receipt.get("video_retry_tag") or (original_tag + "v1")
            receipt.update(state="video_retry_pending", video_retry_attempted=True,
                           video_retry_tag=tag, video_retry_baseline_seq=assistant_after_seq,
                           video_retry_reason="terminal_integrity_check_failed")
            atomic_json(receipt_path, receipt)
            receipt["video_retry_cli_ack"] = bool(submit(sid, build_video_retry_prompt(tag, image_tool_path), tag))
            atomic_json(receipt_path, receipt)

        if receipt.get("state") == "video_retry_ready":
            begin_video_retry()
        elif receipt.get("state") == "video_retry_pending":
            if not receipt.get("video_retry_attempted") or not receipt.get("video_retry_tag"):
                raise RuntimeError("MUSE_VIDEO_RETRY_RECEIPT_INVALID")
            tag = receipt["video_retry_tag"]
            assistant_after_seq = int(receipt.get("video_retry_baseline_seq") or 0)

        # An explicit negative CLI acknowledgement may be retried once, but only
        # on the same session after the gateway proves it is terminal and empty.
        # Persist the attempt first so a crash can never trigger a duplicate retry.
        if (
            not created_now
            and receipt.get("state") == "submission_uncertain"
            and receipt.get("cli_ack") is False
            and not receipt.get("same_session_retry_attempted")
        ):
            history_before_retry = api.call("chat.history", {"session_id": sid, "limit": 60}).get("chat_events", [])
            sessions_before_retry = api.call("sessions.list").get("sessions", [])
            session_before_retry = next((s for s in sessions_before_retry if s.get("session_id", s.get("id")) == sid), {})
            if session_before_retry.get("status") == "completed" and isinstance(history_before_retry, list) and not history_before_retry:
                receipt["same_session_retry_attempted"] = True
                receipt["same_session_retry_reason"] = "empty_completed_session_after_negative_ack"
                atomic_json(receipt_path, receipt)
                receipt["cli_ack"] = bool(submit(sid, build_scene_prompt(tag), tag))
                atomic_json(receipt_path, receipt)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            history = api.call("chat.history", {"session_id": sid, "limit": 60}).get("chat_events", [])
            sessions = api.call("sessions.list").get("sessions", [])
            session = next((s for s in sessions if s.get("session_id", s.get("id")) == sid), {})
            status = session.get("status")
            def visible(e):
                return (e.get("payload") or {}).get("display_text") or e.get("display_text") or ""
            accepted = any(e.get("event_name") == "message.user" and tag in visible(e) for e in history)
            text = "\n".join(
                visible(e) for e in history
                if e.get("event_name") == "message.assistant"
                and (assistant_after_seq <= 0 or int(e.get("seq") or 0) > assistant_after_seq)
            )
            if status in ("failed", "error", "cancelled", "canceled"):
                receipt["state"] = "failed"; atomic_json(receipt_path, receipt)
                raise RuntimeError("MUSE_REMOTE_FAILED: Muse báo job thất bại; không tự gửi lại.")
            if accepted:
                receipt["state"] = "video_retry_pending" if receipt.get("video_retry_attempted") else "accepted"
                atomic_json(receipt_path, receipt)
            if accepted and text and status in ("completed", "idle"):
                raw_paths = list(dict.fromkeys(PATH_RE.findall(text)))
                path_pairs = [(raw, workspace_path(raw)) for raw in raw_paths]
                if receipt.get("video_retry_attempted"):
                    images = [receipt["image_remote"]] if receipt.get("image_remote") else []
                    videos = [path for raw, path in path_pairs if raw.lower().endswith(".mp4")]
                else:
                    images = [path for raw, path in path_pairs if not raw.lower().endswith(".mp4") and receipt["tag"] in raw]
                    videos = [path for raw, path in path_pairs if raw.lower().endswith(".mp4") and tag in raw]
                if images and not videos and "integrity_check_failed" in text.lower() and not receipt.get("video_retry_attempted"):
                    image_tool_path = next((raw for raw, path in path_pairs if not raw.lower().endswith(".mp4") and receipt["tag"] in raw), None)
                    receipt.update(image_remote=images[0], image_tool_path=image_tool_path,
                                   state="video_retry_ready", remote_error="integrity_check_failed")
                    atomic_json(receipt_path, receipt)
                    raise RuntimeError("MUSE_VIDEO_RECOVERY_REQUIRES_SEPARATE_APPROVAL: automatic video retry disabled.")
                if not images or not videos:
                    if images:
                        image_tool_path = next((raw for raw, path in path_pairs if not raw.lower().endswith(".mp4") and receipt["tag"] in raw), None)
                        receipt.update(image_remote=images[0], image_tool_path=image_tool_path)
                    receipt["state"] = "failed"
                    receipt["remote_error"] = "MUSE_REMOTE_FAILED: missing tagged image/video paths"
                    atomic_json(receipt_path, receipt)
                    raise RuntimeError("MUSE_REMOTE_FAILED: Job kết thúc nhưng chưa có đủ ảnh/video mang mã cảnh.")
                receipt.update(image_remote=images[0], video_remote=videos[0], state="downloading")
                atomic_json(receipt_path, receipt)
                break
            time.sleep(poll_interval)
        else:
            raise RuntimeError("MUSE_JOB_PENDING: Job chưa có kết quả xác minh; chạy tiếp để theo dõi job cũ.")
        raw_image = output.parent / "muse_source.image"
        imeta = download(api, receipt["image_remote"], raw_image)
        with Image.open(raw_image) as im:
            im.verify()
        with Image.open(raw_image) as im:
            im.load()
            source_size = im.size
            target_size = (int(request["width"]), int(request["height"]))
            image_to_save = im.convert("RGB")
            fit_mode = "none"
            if needs_cinematic_letterbox(source_size[0], source_size[1], *target_size):
                fitted = ImageOps.contain(image_to_save, target_size, method=Image.Resampling.LANCZOS)
                canvas = Image.new("RGB", target_size, (0, 0, 0))
                canvas.paste(fitted, ((target_size[0] - fitted.width) // 2,
                                      (target_size[1] - fitted.height) // 2))
                image_to_save = canvas
                fit_mode = "cinematic_letterbox"
            size = image_to_save.size
            temp = output.with_name(output.name + ".tmp")
            image_to_save.save(temp, format="PNG")
        os.replace(temp, output)
        image = {"path": str(output), "remote_path": receipt["image_remote"], "source_sha256": imeta["sha256"],
                 "sha256": digest(output), "bytes": output.stat().st_size, "width": size[0], "height": size[1],
                 "source_width": source_size[0], "source_height": source_size[1], "aspect_fit": fit_mode}
        clip = output.parent / "muse_clip.mp4"
        video = download(api, receipt["video_remote"], clip)
        video.update(inspect_video(clip))
        if needs_cinematic_letterbox(video["width"], video["height"], request["width"], request["height"]):
            video.update(source_width=video["width"], source_height=video["height"],
                         source_bytes=video["bytes"], source_sha256=video["sha256"],
                         aspect_fit="cinematic_letterbox")
            letterbox_cinematic_video(clip, request["width"], request["height"])
            video.update(inspect_video(clip))
            video.update(bytes=clip.stat().st_size, sha256=digest(clip))
        expected = request["width"] / request["height"]
        if any(abs((m["width"] / m["height"]) / expected - 1) > .05 for m in (image, video)):
            raise RuntimeError("MUSE_ASPECT_MISMATCH: Tệp Muse không đúng tỷ lệ cảnh, không dùng thay bằng ảnh tĩnh.")
        result = {"ok": True, "session_id": sid, "image": image, "video": video}
        receipt.update(state="complete", result=result)
        atomic_json(receipt_path, receipt)
        return result
    finally:
        if own_api:
            api.close()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["status", "render", "auth-export"])
    p.add_argument("--request")
    args = p.parse_args()
    try:
        if args.action == "auth-export":
            from muse_login import export_session
            request = json.loads(Path(args.request).read_text(encoding="utf-8"))
            with render_lock(request["lock_path"], timeout=0):
                result = export_session(request["port"], request["productions_dir"], account_id=request.get("account_id"))
        elif args.action == "status":
            request = json.loads(Path(args.request).read_text(encoding="utf-8")) if args.request else {}
            if request.get("account_home"):
                os.environ["USERPROFILE"] = str(request["account_home"])
            api = GatewayAPI()
            try:
                d = api.call("sessions.list")
                if not isinstance(d.get("sessions"), list):
                    raise RuntimeError("MUSE_STATUS_INVALID")
                result = {"ok": True, "status": "READY", "message": "Đã xác minh phiên Muse trên máy. Sẵn sàng tạo ảnh và video."}
            finally:
                api.close()
        else:
            request = json.loads(Path(args.request).read_text(encoding="utf-8"))
            if request.get("account_home"):
                os.environ["USERPROFILE"] = str(request["account_home"])
            with render_lock(request["lock_path"], timeout=600):
                result = run_render(request)
        print(json.dumps(result, ensure_ascii=False), flush=True)
        return 0
    except Exception as exc:
        # Arbitrary upstream errors may contain authentication URLs or headers.
        message = str(exc)
        if not message.startswith("MUSE_"):
            if "MUSE_" in message:
                idx = message.find("MUSE_")
                message = message[idx:].rstrip("'\"")
            else:
                message = "MUSE_WORKER_FAILED: Chưa xác minh được kết quả. Job đã lưu không được tự gửi lại."
        print(json.dumps({"ok": False, "error": message}, ensure_ascii=False), flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
