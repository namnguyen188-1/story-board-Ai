"""
Movie Recap Studio Pro - Native Desktop Application (Qt6 / WebView2).
- 100% Native Desktop Window with zero browser URL bar or browser tabs
- Native Hardware-Accelerated H.264/AAC/MP4 Video Playback via Edge Chromium / WebView2 Engine
- Hosts full-featured Movie Recap Studio interface with Dual Monitors, AI Scriptwriter,
  Gemini TTS Voiceover, Draggable Subtitles, Fair-Use Anti-Content-ID filters,
  and export management.
"""

from __future__ import annotations
import os
import sys
import time
import subprocess
import urllib.request
import ctypes
from pathlib import Path

# Ensure recap_engine root is in sys.path
RECAP_ROOT = Path(__file__).resolve().parent
if str(RECAP_ROOT) not in sys.path:
    sys.path.insert(0, str(RECAP_ROOT))

PORT = 8095
URL = f"http://127.0.0.1:{PORT}"
PYTHON = sys.executable

# Auto-hide console window on Windows so only the clean Desktop App is visible
if os.name == "nt":
    try:
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)
    except Exception:
        pass


def is_server_ready(timeout: float = 1.0) -> bool:
    for path in ("/api/status", "/"):
        try:
            req = urllib.request.Request(f"{URL}{path}")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status in (200, 204):
                    return True
        except Exception:
            pass
    return False


def start_backend_server():
    if is_server_ready():
        return None

    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    server_script = RECAP_ROOT / "server.py"
    proc = subprocess.Popen(
        [PYTHON, "-u", str(server_script)],
        cwd=str(RECAP_ROOT),
        creationflags=flags
    )
    for _ in range(40):
        time.sleep(0.15)
        if is_server_ready():
            return proc
    return proc


def run_webview2_desktop(server_proc=None):
    """Launches high-performance native desktop window with full H.264 hardware video decoding."""
    import webview

    icon_path = Path(r"D:\STORYBOARD_AI\studio\web\assets\storyboard_ai_icon.ico")
    profile_dir = RECAP_ROOT / ".recap_desktop_profile"
    profile_dir.mkdir(parents=True, exist_ok=True)

    try:
        webview.settings["ALLOW_DOWNLOADS"] = True
        webview.settings["ALLOW_FILE_URLS"] = True
    except Exception:
        pass

    window = webview.create_window(
        title="🎬 Movie Recap Studio Pro v0.0.1 - Phim Review Bất Bại",
        url=URL,
        width=1480,
        height=920,
        resizable=True,
        min_size=(1100, 720),
        background_color="#070a12"
    )

    try:
        webview.start(
            gui="edgechromium",
            private_mode=False,
            storage_path=str(profile_dir),
            icon=str(icon_path) if icon_path.is_file() else None
        )
    finally:
        if server_proc:
            try:
                server_proc.terminate()
            except Exception:
                pass


def run_qt6_fallback(server_proc=None):
    """Fallback PyQt6 window if WebView2 is unavailable."""
    from PyQt6.QtWidgets import QApplication, QMainWindow
    from PyQt6.QtCore import QUrl
    from PyQt6.QtGui import QIcon
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import QWebEngineSettings

    app = QApplication(sys.argv)
    app.setApplicationName("Movie Recap Studio Pro")

    icon_path = Path(r"D:\STORYBOARD_AI\studio\web\assets\storyboard_ai_icon.ico")
    if icon_path.is_file():
        app.setWindowIcon(QIcon(str(icon_path)))

    win = QMainWindow()
    win.setWindowTitle("🎬 Movie Recap Studio Pro v0.0.1 - Phim Review Bất Bại")
    win.resize(1480, 920)
    win.setMinimumSize(1100, 720)
    if icon_path.is_file():
        win.setWindowIcon(QIcon(str(icon_path)))

    browser = QWebEngineView(win)
    win.setCentralWidget(browser)

    settings = browser.settings()
    settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
    settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
    settings.setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)

    browser.load(QUrl(URL))
    win.show()

    try:
        sys.exit(app.exec())
    finally:
        if server_proc:
            try:
                server_proc.terminate()
            except Exception:
                pass


def main():
    proc = start_backend_server()

    # 1. Try native WebView2 (EdgeChromium) for 100% video codec compatibility (H.264/AAC)
    try:
        run_webview2_desktop(server_proc=proc)
        return
    except Exception as e:
        print(f"[DESKTOP] WebView2 unavailable ({e}), trying PyQt6 fallback...")

    # 2. Try PyQt6 fallback
    try:
        run_qt6_fallback(server_proc=proc)
        return
    except Exception as e:
        print(f"[DESKTOP] PyQt6 fallback unavailable ({e}), trying Edge/Chrome App Mode...")

    # 3. Try Windows Native Edge/Chromium App Mode (100% available on all Windows 10/11)
    try:
        from desktop_app import find_app_browser, run_native_app_window
        browser_exe = find_app_browser()
        if browser_exe:
            run_native_app_window(browser_exe, server_proc=proc)
            return
    except Exception as e:
        print(f"[FATAL] Could not launch desktop interface: {e}")

    if proc:
        proc.terminate()


if __name__ == "__main__":
    main()
