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


def log_app(msg: str):
    try:
        log_file = RECAP_ROOT / "recap_app.log"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass


def is_server_ready(timeout: float = 1.0) -> bool:
    for path in ("/api/status", "/"):
        try:
            req = urllib.request.Request(f"{URL}{path}", headers={"User-Agent": "DesktopHealthCheck"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status in (200, 204):
                    return True
        except Exception:
            pass
    return False


def cleanup_stale_port(port: int = PORT) -> None:
    """Kills any dead processes hanging on the port."""
    if is_server_ready():
        return
    try:
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        out = subprocess.check_output(["netstat", "-ano", "-p", "tcp"], text=True, errors="ignore", creationflags=flags)
        pids = set()
        for line in out.splitlines():
            line = line.strip()
            if f":{port}" in line and "LISTENING" in line.upper():
                parts = line.split()
                if len(parts) >= 5:
                    try:
                        pids.add(int(parts[-1]))
                    except ValueError:
                        pass
        current_pid = os.getpid()
        for pid in pids:
            if pid != current_pid and pid > 0:
                subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True, creationflags=flags)
        if pids:
            time.sleep(0.5)
    except Exception:
        pass


def start_backend_server():
    log_app("start_backend_server() entered")
    try:
        if is_server_ready():
            log_app("Server already ready")
            return None

        log_app("Running cleanup_stale_port...")
        cleanup_stale_port(PORT)
        log_app("cleanup_stale_port finished")

        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        server_script = RECAP_ROOT / "server.py"

        env = os.environ.copy()
        env["PYTHONPATH"] = str(RECAP_ROOT) + os.pathsep + env.get("PYTHONPATH", "")

        log_app(f"Spawning server.py: {PYTHON} {server_script}")
        proc = subprocess.Popen(
            [PYTHON, "-u", str(server_script)],
            cwd=str(RECAP_ROOT),
            env=env,
            creationflags=flags
        )
        log_app(f"server.py spawned with PID: {proc.pid}")
        for i in range(80):
            time.sleep(0.15)
            if is_server_ready():
                log_app(f"Server became ready after {i*0.15:.2f}s")
                return proc
            if proc.poll() is not None:
                log_app(f"server.py terminated early with code {proc.poll()}")
                break
        return proc
    except Exception as e:
        log_app(f"EXCEPTION in start_backend_server: {e}")
        return None


def get_icon_path() -> Path | None:
    candidates = [
        RECAP_ROOT / "web" / "assets" / "recap_icon.ico",
        RECAP_ROOT / "web" / "assets" / "storyboard_ai_icon.ico",
        RECAP_ROOT.parent / "studio" / "web" / "assets" / "storyboard_ai_icon.ico",
    ]
    for p in candidates:
        if p.is_file():
            return p
    return None


def run_webview2_desktop(server_proc=None):
    """Launches high-performance native desktop window with full H.264 hardware video decoding."""
    import webview

    icon_path = get_icon_path()
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
        maximized=True,
        background_color="#070a12"
    )

    try:
        webview.start(
            gui="edgechromium",
            private_mode=False,
            storage_path=str(profile_dir),
            icon=str(icon_path) if icon_path else None
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

    icon_path = get_icon_path()
    if icon_path:
        app.setWindowIcon(QIcon(str(icon_path)))

    win = QMainWindow()
    win.setWindowTitle("🎬 Movie Recap Studio Pro v0.0.1 - Phim Review Bất Bại")
    win.resize(1480, 920)
    win.setMinimumSize(1100, 720)
    if icon_path:
        win.setWindowIcon(QIcon(str(icon_path)))

    browser = QWebEngineView(win)
    win.setCentralWidget(browser)

    settings = browser.settings()
    settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
    settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
    settings.setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)

    browser.load(QUrl(URL))
    win.showMaximized()

    try:
        sys.exit(app.exec())
    finally:
        if server_proc:
            try:
                server_proc.terminate()
            except Exception:
                pass


def run_edge_app_mode(server_proc=None):
    """Windows Native Edge/Chromium App Mode (100% available on all Windows 10/11)."""
    from desktop_app import find_app_browser
    browser_exe = find_app_browser()
    if not browser_exe:
        import webbrowser
        webbrowser.open(URL)
        return

    profile_dir = RECAP_ROOT / ".recap_desktop_profile"
    profile_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        browser_exe,
        f"--app={URL}",
        f"--user-data-dir={profile_dir}",
        "--start-maximized",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-features=msHub,msEdgeAppModeAddressBar",
        "--app-id=MovieRecapStudioPro",
    ]
    # Khởi chạy cửa sổ ứng dụng ở chế độ hiển thị bình thường (KHÔNG dùng CREATE_NO_WINDOW)
    proc = subprocess.Popen(cmd)
    t_start = time.time()
    try:
        proc.wait()
    finally:
        elapsed = time.time() - t_start
        if elapsed > 3.0:
            if server_proc:
                try:
                    server_proc.terminate()
                except Exception:
                    pass
        else:
            if server_proc:
                try:
                    server_proc.wait()
                except KeyboardInterrupt:
                    server_proc.terminate()


def main():
    log_app("Starting main()...")
    proc = start_backend_server()
    log_app(f"start_backend_server returned proc={proc}")

    # 1. Try native WebView2 (EdgeChromium) for 100% video codec compatibility (H.264/AAC)
    try:
        log_app("Attempting run_webview2_desktop...")
        run_webview2_desktop(server_proc=proc)
        log_app("run_webview2_desktop exited normally")
        return
    except Exception as e:
        log_app(f"run_webview2_desktop failed: {e}")

    # 2. Try PyQt6 fallback
    try:
        log_app("Attempting run_qt6_fallback...")
        run_qt6_fallback(server_proc=proc)
        log_app("run_qt6_fallback exited normally")
        return
    except Exception as e:
        log_app(f"run_qt6_fallback failed: {e}")

    # 3. Try Windows Native Edge/Chromium App Mode (100% available on all Windows 10/11)
    try:
        log_app("Attempting run_edge_app_mode...")
        run_edge_app_mode(server_proc=proc)
        log_app("run_edge_app_mode exited normally")
        return
    except Exception as e:
        log_app(f"run_edge_app_mode failed: {e}")

    # 4. Ultimate fallback: open in default browser
    try:
        log_app("Attempting default browser open...")
        import webbrowser
        webbrowser.open(URL)
    except Exception as e:
        log_app(f"webbrowser.open failed: {e}")


if __name__ == "__main__":
    main()
