#!/usr/bin/env python3
"""
Muse Bridge Server - Cổng kết nối trung gian giữa Muse CLI và AI Video Production Editor.
Hỗ trợ cả 2 chế độ:
1. Direct REST API (/api/generate, /api/status, /api/login)
2. ComfyUI Compatibility Layer (/prompt, /history, /view, /object_info)
   -> Giúp AI Video Production Editor cắm trực tiếp vào dùng ngay mà không cần sửa code giao diện!
"""

from __future__ import annotations
import os
import sys
import json
import time
import uuid
import mimetypes
import threading
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

# Đảm bảo import được các module từ studio/
_STUDIO_DIR = Path(__file__).resolve().parent
if str(_STUDIO_DIR) not in sys.path:
    sys.path.insert(0, str(_STUDIO_DIR))

import muse_accounts
import muse_video_provider

# Thư mục lưu trữ video xuất từ Bridge
OUTPUT_DIR = _STUDIO_DIR / "runtime" / "bridge_outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Bộ nhớ tạm lưu trữ lịch sử các job (cho ComfyUI emulation)
_JOBS: dict[str, dict] = {}
_LOCK = threading.Lock()


def get_media_dimensions(aspect_ratio: str = "16:9") -> tuple[int, int]:
    """Quy đổi tỉ lệ sang độ phân giải tiêu chuẩn của Muse."""
    if aspect_ratio == "9:16":
        return 720, 1280
    if aspect_ratio == "1:1":
        return 960, 960
    return 1280, 720  # Mặc định 16:9


def run_muse_render(prompt: str, aspect_ratio: str = "16:9", duration: int = 5,
                    reference_image: str | None = None, account_id: str | None = None) -> dict:
    """Gọi core render của Muse và lưu video vào OUTPUT_DIR."""
    width, height = get_media_dimensions(aspect_ratio)
    job_id = f"muse_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    out_dir = OUTPUT_DIR / job_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_img = out_dir / "frame.png"
    target_video = out_dir / "muse_clip.mp4"

    # Lấy tài khoản khả dụng
    target_acc = muse_accounts.get_account(account_id) if account_id else muse_accounts.get_account(muse_accounts.get_active_id())
    if not target_acc:
        accounts = muse_accounts.list_accounts()
        target_acc = accounts[0] if accounts else {"id": "default", "name": "Mặc định", "profile_home": None}

    acc_id = target_acc.get("id", "default")
    lock_name = f"muse_render_{acc_id}.lock" if acc_id != "default" else "muse_render.lock"

    # Xử lý reference image nếu là base64 data URI hoặc file path
    clean_ref_image = None
    if reference_image:
        if reference_image.startswith("data:") or len(reference_image) > 500:
            import base64
            ref_path = out_dir / "ref_input.png"
            b64_data = reference_image.split(",", 1)[-1]
            try:
                ref_path.write_bytes(base64.b64decode(b64_data))
                clean_ref_image = str(ref_path)
            except Exception as e:
                print(f"[MUSE_BRIDGE_WARN] Không thể giải mã reference image base64: {e}", flush=True)
                clean_ref_image = None
        elif Path(reference_image).is_file():
            clean_ref_image = str(Path(reference_image).resolve())
        else:
            print(f"[MUSE_BRIDGE_WARN] File reference image không tồn tại: {reference_image}, chuyển sang text-to-video", flush=True)

    req = {
        "output_image_path": str(out_img),
        "prompt": prompt,
        "width": width,
        "height": height,
        "duration": duration,
        "lock_path": str(_STUDIO_DIR / "runtime" / lock_name),
        "reference_image": clean_ref_image,
        "scene_image_path": clean_ref_image,
    }

    if target_acc.get("profile_home"):
        req["account_home"] = str(target_acc["profile_home"])
        req["account_id"] = acc_id
        if target_acc.get("cookies_file"):
            req["cookies_file"] = str(target_acc["cookies_file"])
        if target_acc.get("vm_id"):
            req["vm_id"] = target_acc.get("vm_id")

    print(f"[MUSE_BRIDGE] 🚀 Bắt đầu sinh video cho job '{job_id}' bằng tài khoản '{target_acc.get('name', acc_id)}'...", flush=True)
    res = muse_video_provider._worker("render", req, timeout=720)

    if not target_video.is_file():
        raise RuntimeError("MUSE_RENDER_FAILED: Muse hoàn thành nhưng không tìm thấy file video đầu ra.")

    # Tạo đường link công khai
    filename = f"{job_id}.mp4"
    dest_video = OUTPUT_DIR / filename
    if not dest_video.exists():
        import shutil
        shutil.copy2(target_video, dest_video)

    return {
        "job_id": job_id,
        "filename": filename,
        "path": str(dest_video),
        "width": width,
        "height": height,
        "duration": duration,
        "worker_result": res,
    }


class MuseBridgeHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Rút gọn log để console sạch sẽ
        sys.stderr.write(f"[MUSE_BRIDGE_HTTP] {self.command} {self.path} - {args[1]}\n")

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def _json_response(self, data: dict, status: int = 200):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        content_len = int(self.headers.get("Content-Length", 0))
        if content_len == 0:
            return {}
        raw = self.rfile.read(content_len).decode("utf-8")
        try:
            return json.loads(raw)
        except Exception:
            return {}

    # ==========================
    # GET ENDPOINTS
    # ==========================
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        # 1. Health check & status
        if path in ("/health", "/api/status"):
            conn_status = muse_video_provider.test_muse_connection()
            accounts = muse_accounts.list_accounts()
            self._json_response({
                "ok": True,
                "server": "Muse Bridge API Server v1.0",
                "connection": conn_status,
                "accounts": accounts,
                "active_account": muse_accounts.get_active_id()
            })
            return

        # 2. ComfyUI Object Info Emulation
        if path == "/object_info":
            # Giả lập để ComfyUI client của Editor tin rằng server sẵn sàng
            self._json_response({
                "CheckpointLoaderSimple": {"input": {"required": {"ckpt_name": [["wan2.2_5b.safetensors", "ltx_2.5.safetensors"]]}}},
                "CLIPTextEncode": {"input": {"required": {"text": ["STRING", {"multiline": True}]}}},
                "KSampler": {"input": {"required": {}}},
                "SaveImage": {"input": {"required": {}}}
            })
            return

        # 3. ComfyUI History Emulation
        if path.startswith("/history/"):
            prompt_id = path.split("/history/")[-1]
            with _LOCK:
                job = _JOBS.get(prompt_id)
            if not job:
                self._json_response({})
                return

            if job.get("status") == "complete":
                fn = job.get("filename", "")
                self._json_response({
                    prompt_id: {
                        "status": {"status_str": "success", "completed": True, "messages": []},
                        "outputs": {
                            "1": {
                                "videos": [{"filename": fn, "subfolder": "", "type": "output"}]
                            }
                        }
                    }
                })
            elif job.get("status") == "error":
                self._json_response({
                    prompt_id: {
                        "status": {
                            "status_str": "error",
                            "messages": [["execution_error", {"exception_message": job.get("error", "Lỗi sinh video")}]]
                        }
                    }
                })
            else:
                # Đang chạy
                self._json_response({
                    prompt_id: {
                        "status": {"status_str": "running", "completed": False}
                    }
                })
            return

        # 4. ComfyUI Queue Emulation
        if path == "/queue":
            running = []
            with _LOCK:
                for pid, j in _JOBS.items():
                    if j.get("status") == "running":
                        running.append([0, pid])
            self._json_response({"queue_running": running, "queue_pending": []})
            return

        # 5. Phục vụ file video tĩnh (/view hoặc /videos/<filename>)
        filename = None
        if path == "/view" and "filename" in query:
            filename = query["filename"][0]
        elif path.startswith("/videos/"):
            filename = path.replace("/videos/", "")

        if filename:
            file_path = OUTPUT_DIR / filename
            if file_path.is_file():
                self._serve_file(file_path)
                return
            else:
                self.send_error(404, "File not found")
                return

        self.send_error(404, "Endpoint not found")

    # ==========================
    # POST ENDPOINTS
    # ==========================
    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        body = self._read_json()

        # 1. Direct REST Generation: /api/generate
        if path == "/api/generate":
            prompt = body.get("prompt", "").strip()
            if not prompt:
                self._json_response({"ok": False, "error": "Prompt không được để trống"}, 400)
                return

            aspect_ratio = body.get("aspect_ratio", "16:9")
            duration = int(body.get("duration", 5))
            reference_image = body.get("reference_image")
            account_id = body.get("account_id")

            try:
                res = run_muse_render(
                    prompt=prompt,
                    aspect_ratio=aspect_ratio,
                    duration=duration,
                    reference_image=reference_image,
                    account_id=account_id
                )
                host = self.headers.get("Host", "127.0.0.1:8199")
                video_url = f"http://{host}/videos/{res['filename']}"
                self._json_response({
                    "ok": True,
                    "job_id": res["job_id"],
                    "video_url": video_url,
                    "video_path": res["path"],
                    "width": res["width"],
                    "height": res["height"],
                    "duration": res["duration"]
                })
            except Exception as e:
                self._json_response({"ok": False, "error": str(e)}, 500)
            return

        # 2. ComfyUI Emulation: /prompt
        if path == "/prompt":
            prompt_graph = body.get("prompt", {})
            prompt_id = body.get("client_id", f"comfy_{int(time.time())}")

            # Trích xuất prompt từ graph nodes
            extracted_prompt = ""
            for node_id, node_data in prompt_graph.items():
                if isinstance(node_data, dict) and node_data.get("class_type") == "CLIPTextEncode":
                    t = node_data.get("inputs", {}).get("text", "")
                    if t and len(t) > len(extracted_prompt):
                        extracted_prompt = t

            if not extracted_prompt:
                extracted_prompt = "Cinematic video scene, high quality, 8k"

            with _LOCK:
                _JOBS[prompt_id] = {"status": "running", "prompt": extracted_prompt, "started": time.time()}

            # Chạy render ngầm trong thread để không block HTTP
            def _async_render():
                try:
                    res = run_muse_render(prompt=extracted_prompt, duration=5)
                    with _LOCK:
                        _JOBS[prompt_id].update({
                            "status": "complete",
                            "filename": res["filename"],
                            "path": res["path"]
                        })
                except Exception as ex:
                    with _LOCK:
                        _JOBS[prompt_id].update({
                            "status": "error",
                            "error": str(ex)
                        })

            threading.Thread(target=_async_render, daemon=True).start()
            self._json_response({"prompt_id": prompt_id, "number": 1})
            return

        # 3. Kích hoạt đăng nhập Muse: /api/login/start
        if path == "/api/login/start":
            acc_id = body.get("account_id")
            acc_name = body.get("account_name")
            try:
                res = muse_video_provider.start_muse_login(account_id=acc_id, account_name=acc_name)
                self._json_response({"ok": True, "result": res})
            except Exception as e:
                self._json_response({"ok": False, "error": str(e)}, 500)
            return

        self.send_error(404, "Endpoint not found")

    def _serve_file(self, file_path: Path):
        """Phục vụ file video kèm hỗ trợ HTTP Range (cho phép tua video mượt mà)."""
        file_size = file_path.stat().st_size
        mime_type, _ = mimetypes.guess_type(str(file_path))
        mime_type = mime_type or "application/octet-stream"

        range_header = self.headers.get("Range")
        if range_header:
            # Parse Range: bytes=start-end
            try:
                ranges = range_header.replace("bytes=", "").split("-")
                start = int(ranges[0]) if ranges[0] else 0
                end = int(ranges[1]) if len(ranges) > 1 and ranges[1] else file_size - 1
                length = end - start + 1

                self.send_response(206)
                self.send_header("Content-Type", mime_type)
                self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
                self.send_header("Content-Length", str(length))
                self.send_header("Accept-Ranges", "bytes")
                self._send_cors_headers()
                self.end_headers()

                with open(file_path, "rb") as f:
                    f.seek(start)
                    self.wfile.write(f.read(length))
                return
            except Exception:
                pass

        self.send_response(200)
        self.send_header("Content-Type", mime_type)
        self.send_header("Content-Length", str(file_size))
        self.send_header("Accept-Ranges", "bytes")
        self._send_cors_headers()
        self.end_headers()

        with open(file_path, "rb") as f:
            self.wfile.write(f.read())


def start_server(port: int = 8199):
    server = ThreadingHTTPServer(("127.0.0.1", port), MuseBridgeHandler)
    print("=" * 65)
    print(f"🎬 MUSE BRIDGE SERVER ĐÃ SẴN SÀNG TẠI: http://127.0.0.1:{port}")
    print(f"• Direct REST API: POST http://127.0.0.1:{port}/api/generate")
    print(f"• ComfyUI Emulation: http://127.0.0.1:{port}")
    print(f"• Thư mục lưu video: {OUTPUT_DIR}")
    print("=" * 65)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nĐã dừng Muse Bridge Server.")
        server.server_close()


if __name__ == "__main__":
    port_arg = int(sys.argv[1]) if len(sys.argv) > 1 else 8199
    start_server(port_arg)
