"""Launch script for Storyboard AI Studio Pro.
Starts the background server and opens the browser.
"""
import os
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

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
PYTHON = sys.executable
SERVER_SCRIPT = STUDIO_DIR / "web_server.py"
URL = "http://127.0.0.1:8765"

def is_server_running():
    try:
        with urllib.request.urlopen(f"{URL}/api/config", timeout=1) as resp:
            return resp.status == 200
    except Exception:
        return False

def main():
    if is_server_running():
        print(f"[LAUNCH] Server is already running at {URL}. Opening browser...")
        webbrowser.open(URL)
        return

    print("=" * 60)
    print("STORYBOARD AI STUDIO PRO (v2.5)")
    print(f"Address: {URL}")
    print("=" * 60)

    # Launch server
    from web_server import start_server
    import threading

    t = threading.Thread(target=start_server, args=(8765,), daemon=True)
    t.start()

    # Wait for server to be responsive
    for _ in range(15):
        time.sleep(0.3)
        if is_server_running():
            break

    print(f"Đang mở trình duyệt tại {URL}...")
    webbrowser.open(URL)

    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nĐã đóng Storyboard AI Studio Pro.")

if __name__ == "__main__":
    main()
