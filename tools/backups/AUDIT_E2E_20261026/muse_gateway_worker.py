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

    def call(self, method, body=None):
        from muse_cli.cli import connect
        from muse_cli.gateway import AuthError
        # Only reads reconnect. Mutating session creation is never replayed.
        attempts = 3 if method in ("chat.history", "sessions.list", "fs.stat", "fs.read") else 1
        for attempt in range(attempts):
            try:
                if self.gateway is None:
                    self.gateway = connect(self.cfg)
                return self.gateway.call_json(method, body=body, timeout=30)
            except AuthError:
                self.close()
                raise RuntimeError("MUSE_AUTH_REQUIRED: Phiên Muse đã hết hạn hoặc chưa được lưu. Đăng nhập lại rồi kết nối Muse.") from None
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


def run_render(request, *, api=None, submit=None, poll_interval=10, timeout=600):
    from PIL import Image
    output = Path(request["output_image_path"]).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    receipt_path = output.parent / "muse_job.json"
    fingerprint = hashlib.sha256(json.dumps({k: request[k] for k in ("prompt", "width", "height", "duration")}, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    receipt = json.loads(receipt_path.read_text(encoding="utf-8")) if receipt_path.exists() else {}
    if receipt and receipt.get("fingerprint") != fingerprint:
        raise RuntimeError("MUSE_SCENE_INPUT_CHANGED: Cảnh có job Muse từ cấu hình khác. Hãy tạo tập mới để không ghi đè hoặc tạo trùng.")
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
        if not receipt:
            data = api.call("session.start", {"method": "/api/session/start", "params": {"origin": "fresh", "lifecycle": "persistent", "title": "Storyboard scene " + output.parent.name}})
            sid = data.get("session_id") or data.get("id") or (data.get("session") or {}).get("session_id") or (data.get("session") or {}).get("id")
            if not sid:
                raise RuntimeError("MUSE_SESSION_NOT_CREATED")
            receipt = {"fingerprint": fingerprint, "session_id": sid, "tag": "sbmuse" + uuid.uuid4().hex[:20], "state": "submission_uncertain", "account_vm_id": getattr(api, "account_vm_id", None)}
            # Intent is durable BEFORE sending; a killed sender is never replayed.
            atomic_json(receipt_path, receipt)
            divider = math.gcd(int(request["width"]), int(request["height"]))
            ratio = f"{int(request['width']) // divider}:{int(request['height']) // divider}"
            tag = receipt["tag"]
            prompt = (f"Run exactly one text-to-video scene job, ID {tag}. No user reference image is needed. "
                      f"Use media.generate_video once to create a short {request['duration']}-second video clip, composition ratio {ratio}, name {tag}_video. "
                      f"Preserve the character continuity, lighting, and action instructions. "
                      "Wait for actual tool completion. Return exact local video_path in the final visible reply. "
                      "Do not retry a failed generation or produce extra variants. Report tool failures accurately.\n" + request["prompt"])
            receipt["cli_ack"] = bool(submit(sid, prompt, tag))
            atomic_json(receipt_path, receipt)
        sid, tag = receipt["session_id"], receipt["tag"]
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            history = api.call("chat.history", {"session_id": sid, "limit": 60}).get("chat_events", [])
            sessions = api.call("sessions.list").get("sessions", [])
            session = next((s for s in sessions if s.get("session_id", s.get("id")) == sid), {})
            status = session.get("status")
            def visible(e):
                return (e.get("payload") or {}).get("display_text") or e.get("display_text") or ""
            accepted = any(e.get("event_name") == "message.user" and tag in visible(e) for e in history)
            text = "\n".join(visible(e) for e in history if e.get("event_name") == "message.assistant")
            if status in ("failed", "error", "cancelled", "canceled"):
                receipt["state"] = "failed"; atomic_json(receipt_path, receipt)
                raise RuntimeError("MUSE_REMOTE_FAILED: Muse báo job thất bại; không tự gửi lại.")
            if accepted:
                receipt["state"] = "accepted"; atomic_json(receipt_path, receipt)
            if accepted and text and status in ("completed", "idle"):
                paths = list(dict.fromkeys(workspace_path(p) for p in PATH_RE.findall(text)))
                videos = [p for p in paths if p.lower().endswith(".mp4") and tag in p]
                images = [p for p in paths if not p.lower().endswith(".mp4") and tag in p]
                if not videos:
                    videos = [p for p in paths if p.lower().endswith(".mp4")]
                if not images:
                    images = [p for p in paths if not p.lower().endswith(".mp4")]
                if not videos:
                    receipt["state"] = "failed"; atomic_json(receipt_path, receipt)
                    raise RuntimeError("MUSE_REMOTE_FAILED: Job kết thúc nhưng chưa có video gắn đúng mã cảnh.")
                receipt.update(video_remote=videos[0], image_remote=images[0] if images else None, state="downloading")
                atomic_json(receipt_path, receipt)
                break
            elif (not accepted or not text) and status in ("completed", "idle") and (time.monotonic() - (deadline - timeout)) > 30:
                receipt["state"] = "failed"; atomic_json(receipt_path, receipt)
                raise RuntimeError("MUSE_REMOTE_FAILED: Phiên Muse đã kết thúc nhưng không nhận được lệnh tạo video của cảnh này.")
            time.sleep(poll_interval)
        else:
            receipt["state"] = "failed"; atomic_json(receipt_path, receipt)
            raise RuntimeError("MUSE_JOB_TIMEOUT: Quá thời gian chờ Muse tạo video cho cảnh này.")

        clip = output.parent / "muse_clip.mp4"
        video = download(api, receipt["video_remote"], clip)
        video.update(inspect_video(clip))

        # Handle image: either download remote image if available, or extract frame 0.5s from the video
        if receipt.get("image_remote"):
            raw_image = output.parent / "muse_source.image"
            imeta = download(api, receipt["image_remote"], raw_image)
            with Image.open(raw_image) as im:
                im.verify()
            with Image.open(raw_image) as im:
                im.load()
                size = im.size
                temp = output.with_name(output.name + ".tmp")
                im.convert("RGB").save(temp, format="PNG")
            os.replace(temp, output)
            img_sha = digest(output)
            img_src_sha = imeta["sha256"]
            img_remote = receipt["image_remote"]
        else:
            # Direct Text-to-Video: extract base thumbnail directly from the generated video clip
            extracted = False
            try:
                import av
                with av.open(str(clip)) as container:
                    v_streams = [s for s in container.streams if s.type == "video"]
                    if v_streams:
                        target_sec = 0.5
                        stream = v_streams[0]
                        time_base = stream.time_base or (1 / 24)
                        container.seek(int(target_sec / time_base), stream=stream)
                        for frame in container.decode(stream):
                            im = frame.to_image()
                            im.convert("RGB").save(output, format="PNG")
                            size = im.size
                            extracted = True
                            break
            except Exception:
                pass

            if not extracted:
                import subprocess
                cmd_thumb = [
                    "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                    "-ss", "00:00:00.500", "-i", str(clip.resolve()),
                    "-vframes", "1", str(output.resolve())
                ]
                subprocess.run(cmd_thumb, check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                with Image.open(output) as im:
                    size = im.size

            img_sha = digest(output)
            img_src_sha = img_sha
            img_remote = None

        image = {"path": str(output), "remote_path": img_remote, "source_sha256": img_src_sha,
                 "sha256": img_sha, "bytes": output.stat().st_size, "width": size[0], "height": size[1]}
        expected = request["width"] / request["height"]
        if abs((video["width"] / video["height"]) / expected - 1) > .05:
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
    p.add_argument("action", choices=["status", "render", "auth-export", "verify-header"])
    p.add_argument("--request")
    args = p.parse_args()
    try:
        if args.action == "verify-header":
            from muse_login import _verify_candidate
            request = json.loads(Path(args.request).read_text(encoding="utf-8"))
            vm_id = _verify_candidate(request["header"])
            result = {"ok": True, "vm_id": vm_id, "status": "READY"}
        elif args.action == "auth-export":
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
            message = "MUSE_WORKER_FAILED: Chưa xác minh được kết quả. Job đã lưu không được tự gửi lại."
        print(json.dumps({"ok": False, "error": message}, ensure_ascii=False), flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
