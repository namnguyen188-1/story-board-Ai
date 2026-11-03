from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json, hashlib, os
ROOT = Path(r"D:\STORYBOARD_AI\dist")
FILENAME = "Storyboard_AI_Studio_Pro_v1.3.0.zip"
PREVIOUS_FILENAME = "StoryboardAI-AutoSetup-TransferTest-20261018-FeatureSync-Setup.exe"
LEGACY_FILENAME = "StoryboardAI-AutoSetup-TransferTest-20261018-Setup.exe"
PATCH_FILENAME = "StoryboardAI-Primary-Code-Sync-20261018.zip"
BIND = ("100.88.57.89", 8765)
PACKAGE = ROOT / FILENAME
PATCH = ROOT / PATCH_FILENAME
MANIFEST = Path(__file__).with_name("latest.json")
class Handler(BaseHTTPRequestHandler):
    def send_file(self, path, content_type):
        size = path.stat().st_size
        start, end = 0, size-1
        rng = self.headers.get("Range")
        partial = False
        if rng and rng.startswith("bytes="):
            a, _, b = rng[6:].partition("-")
            start = int(a or 0)
            end = min(int(b) if b else size-1, size-1)
            if start < 0 or start >= size or end < start:
                self.send_error(416); return
            partial = True
        self.send_response(206 if partial else 200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(end-start+1))
        self.send_header("Accept-Ranges", "bytes")
        if partial:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.end_headers()
        if self.command == "HEAD": return
        with path.open("rb") as f:
            f.seek(start)
            left = end-start+1
            while left:
                chunk = f.read(min(1024*1024,left))
                if not chunk: break
                self.wfile.write(chunk); left -= len(chunk)
    def do_HEAD(self):
        self.dispatch()
    def do_GET(self):
        self.dispatch()
    def dispatch(self):
        if self.path == "/latest.json" and MANIFEST.is_file():
            self.send_file(MANIFEST, "application/json")
        elif self.path == "/" + FILENAME and PACKAGE.is_file():
            self.send_file(PACKAGE, "application/octet-stream")
        elif self.path in {"/" + PREVIOUS_FILENAME, "/" + LEGACY_FILENAME}:
            legacy_package = ROOT / self.path.lstrip("/")
            if legacy_package.is_file():
                self.send_file(legacy_package, "application/octet-stream")
            else:
                self.send_error(404)
        elif self.path == "/" + PATCH_FILENAME and PATCH.is_file():
            self.send_file(PATCH, "application/zip")
        else:
            self.send_error(404)
    def log_message(self, fmt, *args):
        print(fmt % args, flush=True)
if not PACKAGE.is_file():
    raise SystemExit(f"Installer missing: {PACKAGE}")
print(f"Update host bound only to Tailscale {BIND[0]}:{BIND[1]}", flush=True)
ThreadingHTTPServer(BIND, Handler).serve_forever()
