"""Storyboard AI Studio Pro - Native Desktop Application Window (Qt6 / PyQt6).
Renders the complete Studio interface inside a true native Windows Qt6 desktop window
with hardware acceleration, persistent profile storage, custom tray icon,
and seamless failover to WebView2 / Chromium App Mode.
"""
from __future__ import annotations

try:
    import silent_subprocess
except ImportError:
    pass

import os
import subprocess
import sys
import threading
import time
import urllib.request
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

# Auto-hide the black CMD/console window on Windows so only the clean Desktop App is visible
if os.name == "nt":
    try:
        import ctypes
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)  # SW_HIDE
    except Exception:
        pass

STUDIO_DIR = Path(__file__).resolve().parent
if str(STUDIO_DIR) not in sys.path:
    sys.path.insert(0, str(STUDIO_DIR))

PYTHON = sys.executable
PORT = 8765
URL = f"http://127.0.0.1:{PORT}"
ICON_PATH = STUDIO_DIR / "web" / "assets" / "storyboard_ai_icon.ico"
WEBVIEW_PROFILE_DIR = STUDIO_DIR / "runtime" / ".desktop_webview_profile"
QT6_PROFILE_DIR = STUDIO_DIR / "runtime" / ".desktop_qt6_profile"
LOG_FILE = STUDIO_DIR / "desktop_app.log"


def log_app(msg: str):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass


ENGINE_BIN = STUDIO_DIR / "engine" / "bin"
if ENGINE_BIN.is_dir() and str(ENGINE_BIN) not in os.environ.get("PATH", ""):
    os.environ["PATH"] = str(ENGINE_BIN) + os.pathsep + os.environ.get("PATH", "")


def is_server_ready(timeout: float = 0.5) -> bool:
    """Checks if the Studio web server is responding."""
    try:
        req = urllib.request.Request(f"{URL}/api/status", headers={"User-Agent": "StudioHealthCheck"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status in (200, 204)
    except Exception:
        return False


def get_pids_on_port(port: int) -> list[int]:
    """Finds PIDs listening on the specified port on Windows."""
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
        return list(pids)
    except Exception:
        return []


def cleanup_stale_port(port: int = PORT) -> None:
    """Kills any non-responsive processes occupying the port."""
    if is_server_ready():
        return

    pids = get_pids_on_port(port)
    if not pids:
        return

    current_pid = os.getpid()
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    for pid in pids:
        if pid != current_pid and pid > 0:
            print(f"[LAUNCHER] Giai phong tien trinh cu treo tren cong {port} (PID: {pid})...")
            try:
                subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True, creationflags=flags)
            except Exception:
                pass
    time.sleep(0.5)


def start_backend_server():
    """Starts the backend HTTP server in a separate background thread if not already running."""
    log_app("start_backend_server: kiem tra trang thai server...")
    if is_server_ready():
        log_app(f"May chu da san sang tai: {URL}")
        print(f"[LAUNCHER] May chu da san sang tai: {URL}")
        return None

    cleanup_stale_port(PORT)

    log_app("Khoi dong web_server.py trong background thread...")
    from web_server import start_server

    t = threading.Thread(target=start_server, args=(PORT,), daemon=True)
    t.start()

    # Wait for server to become responsive
    for i in range(50):
        time.sleep(0.1)
        if is_server_ready():
            log_app(f"May chu da khoi dong thanh cong tai {URL} sau {i*0.1:.2f}s")
            print(f"[LAUNCHER] May chu da khoi dong thanh cong tai: {URL}")
            return t

    log_app("LOI: May chu web_server khong phan hoi trong thoi gian cho!")
    raise RuntimeError("STORYBOARD_HTTP_BACKEND_FAILED_STARTUP")


# ==============================================================================
# 1. PRIMARY NATIVE DESKTOP UI: PyQt6 (Qt6 WebEngine)
# ==============================================================================

def run_qt6_desktop(url: str = URL):
    """Launches the full-featured Native Desktop Application window using Qt6 / PyQt6."""
    log_app("run_qt6_desktop: Bat dau khoi tao QApplication va PyQt6...")
    try:
        from PyQt6.QtWidgets import (
            QApplication,
            QMainWindow,
            QSystemTrayIcon,
            QMenu,
            QMessageBox,
        )
        from PyQt6.QtCore import QUrl, Qt
        from PyQt6.QtGui import QIcon, QColor, QAction
        from PyQt6.QtWebEngineWidgets import QWebEngineView
        from PyQt6.QtWebEngineCore import (
            QWebEngineSettings,
            QWebEngineProfile,
            QWebEnginePage,
            QWebEngineDownloadRequest,
        )
    except Exception as e:
        import traceback
        log_app(f"Loi import PyQt6: {e}\n{traceback.format_exc()}")
        raise

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    app.setApplicationName("Storyboard AI Studio Pro")
    app.setApplicationDisplayName("🎬 Storyboard AI Studio Pro - Native Qt6 Edition")

    if ICON_PATH.is_file():
        app.setWindowIcon(QIcon(str(ICON_PATH)))

    # Ensure profile directory exists for persistent cache and localStorage
    QT6_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    profile = QWebEngineProfile("StoryboardAIStudioProfile", app)
    profile.setPersistentStoragePath(str(QT6_PROFILE_DIR))
    profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies)

    class CustomWebPage(QWebEnginePage):
        def __init__(self, prof, parent_win):
            super().__init__(prof, parent_win)
            self._parent_win = parent_win

        def fullScreenRequested(self, request):
            request.accept()
            if request.toggleOn():
                self._parent_win.showFullScreen()
            else:
                self._parent_win.showNormal()

    class StudioMainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("🎬 Storyboard AI Studio Pro - Native Desktop Edition")
            if ICON_PATH.is_file():
                self.setWindowIcon(QIcon(str(ICON_PATH)))

            self.resize(1480, 920)
            self.setMinimumSize(1100, 700)
            self.setStyleSheet("QMainWindow { background-color: #080b11; }")

            # Center window on primary screen
            screen = QApplication.primaryScreen()
            if screen:
                geo = screen.availableGeometry()
                x = max(0, (geo.width() - 1480) // 2)
                y = max(0, (geo.height() - 920) // 2)
                self.move(x, y)

            # WebEngine Page & View
            self.page = CustomWebPage(profile, self)
            self.page.setBackgroundColor(QColor("#080b11"))

            self.browser = QWebEngineView(self)
            self.browser.setPage(self.page)
            self.setCentralWidget(self.browser)

            # WebEngine Settings
            s = self.browser.settings()
            s.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
            s.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
            s.setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)
            s.setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, True)
            s.setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
            s.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
            s.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
            s.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
            s.setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, True)

            # Handle file downloads (video exports, scripts, thumbnails)
            profile.downloadRequested.connect(self.on_download_requested)

            # DevTools window handle
            self._devtools_win = None

            # Setup system tray icon
            self.setup_tray()

            # Load Studio backend URL
            self.browser.load(QUrl(url))

        def on_download_requested(self, download_item: QWebEngineDownloadRequest):
            """Automatically routes downloads to User Downloads folder."""
            try:
                download_dir = Path.home() / "Downloads"
                fn = download_item.suggestedFileName() or "storyboard_export"
                download_item.setDownloadDirectory(str(download_dir))
                download_item.setDownloadFileName(fn)
                download_item.accept()
                if hasattr(self, "tray_icon") and self.tray_icon.isVisible():
                    self.tray_icon.showMessage(
                        "Storyboard AI Studio",
                        f"Đang tải tệp: {fn} về thư mục Downloads",
                        QSystemTrayIcon.MessageIcon.Information,
                        2500,
                    )
            except Exception:
                download_item.accept()

        def setup_tray(self):
            """Creates a system tray icon with quick controls."""
            if not QSystemTrayIcon.isSystemTrayAvailable():
                return

            self.tray_icon = QSystemTrayIcon(self)
            if ICON_PATH.is_file():
                self.tray_icon.setIcon(QIcon(str(ICON_PATH)))
            self.tray_icon.setToolTip("🎬 Storyboard AI Studio Pro (Đang chạy)")

            menu = QMenu(self)

            act_show = QAction("🎬 Mở Cửa Sổ Studio", self)
            act_show.triggered.connect(self.restore_window)
            menu.addAction(act_show)

            act_prod = QAction("📁 Mở Thư Mục Video (Productions)", self)
            act_prod.triggered.connect(self.open_productions)
            menu.addAction(act_prod)

            menu.addSeparator()

            act_exit = QAction("❌ Thoát Phần Mềm", self)
            act_exit.triggered.connect(self.quit_app)
            menu.addAction(act_exit)

            self.tray_icon.setContextMenu(menu)
            self.tray_icon.activated.connect(self.on_tray_activated)
            self.tray_icon.show()

        def on_tray_activated(self, reason):
            if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
                self.restore_window()

        def restore_window(self):
            self.showNormal()
            self.activateWindow()
            self.raise_()

        def open_productions(self):
            prod_dir = STUDIO_DIR / "productions"
            prod_dir.mkdir(parents=True, exist_ok=True)
            if os.name == "nt":
                os.startfile(str(prod_dir))
            else:
                subprocess.Popen(["xdg-open", str(prod_dir)])

        def toggle_devtools(self):
            """Opens Chromium DevTools for debugging."""
            if self._devtools_win is None:
                self._devtools_win = QMainWindow(self)
                self._devtools_win.setWindowTitle("🛠️ Storyboard AI Studio - DevTools")
                self._devtools_win.resize(960, 640)
                dev_view = QWebEngineView(self._devtools_win)
                self._devtools_win.setCentralWidget(dev_view)
                self.browser.page().setDevToolsPage(dev_view.page())

            if self._devtools_win.isVisible():
                self._devtools_win.hide()
            else:
                self._devtools_win.show()

        def keyPressEvent(self, event):
            key = event.key()
            if key == Qt.Key.Key_F11:
                if self.isFullScreen():
                    self.showNormal()
                else:
                    self.showFullScreen()
                event.accept()
            elif key == Qt.Key.Key_F5:
                self.browser.reload()
                event.accept()
            elif key == Qt.Key.Key_F12:
                self.toggle_devtools()
                event.accept()
            else:
                super().keyPressEvent(event)

        def quit_app(self):
            if hasattr(self, "tray_icon"):
                self.tray_icon.hide()
            self.close()
            QApplication.quit()

        def closeEvent(self, event):
            if hasattr(self, "tray_icon"):
                self.tray_icon.hide()
            event.accept()

    win = StudioMainWindow()
    win.show()

    print("[DESKTOP_APP] Cửa sổ Native Desktop Qt6 đã khởi chạy thành công!")
    sys.exit(app.exec())


# ==============================================================================
# 2. PRIMARY NATIVE DESKTOP UI: pywebview (EdgeChromium / WebView2)
# Native hardware H.264/AAC/MP4 decoding, zero codec constraints, high performance
# ==============================================================================

def prepare_webview_storage() -> Path:
    """Prepares and validates the WebView2 profile directory, clearing stale locks.
    If the primary profile is locked by another instance, automatically switches to a fallback profile
    to prevent WebView2 from failing to initialize (which causes a black screen).
    """
    WEBVIEW_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    lock_file = WEBVIEW_PROFILE_DIR / "EBWebView" / "Default" / "LOCK"
    if lock_file.is_file():
        try:
            lock_file.unlink()
            log_app("Da don dep file LOCK cu trong WEBVIEW_PROFILE_DIR.")
        except Exception as e:
            alt_dir = STUDIO_DIR / "runtime" / f".desktop_webview_profile_{os.getpid()}"
            alt_dir.mkdir(parents=True, exist_ok=True)
            log_app(f"WEBVIEW_PROFILE_DIR dang bi khoa ({e}), chuyen sang profile du phong: {alt_dir}")
            return alt_dir
    return WEBVIEW_PROFILE_DIR


def run_pywebview_desktop(url: str = URL):
    """Primary native desktop window using pywebview (EdgeChromium/WebView2).
    Includes an automatic watchdog: if the WebView2 control fails to render within 4s
    (e.g. black screen or initialization stall), the window is closed and execution
    falls back cleanly to Chromium App Mode without blocking the user.
    """
    import webview

    try:
        webview.settings["ALLOW_DOWNLOADS"] = True
        webview.settings["ALLOW_FILE_URLS"] = True
    except Exception:
        pass

    storage_path = prepare_webview_storage()

    window = webview.create_window(
        title="🎬 Storyboard AI Studio Pro - Native Desktop Edition",
        url=url,
        width=1480,
        height=920,
        resizable=True,
        min_size=(1100, 700),
        background_color="#080b11",
        text_select=True,
        zoomable=True,
    )

    webview.start(
        gui="edgechromium",
        private_mode=False,
        storage_path=str(storage_path),
        icon=str(ICON_PATH) if ICON_PATH.is_file() else None,
        debug=False,
    )


# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================

def main():
    log_app("===== KHOI DONG STORYBOARD AI STUDIO PRO (DESKTOP) =====")
    print("=" * 70)
    print("🎬 KHOI DONG STORYBOARD AI STUDIO PRO (NATIVE DESKTOP EDITION)")
    print("=" * 70)

    # 1. Start or verify backend HTTP server
    start_backend_server()

    print("\n" + "=" * 70)
    print("✨ STORYBOARD AI STUDIO PRO DANG HOAT DONG")
    print("=" * 70)
    print(f"🌐 Dia chi Studio:    {URL}")
    print("🖥️ Giao dien Desktop:  Edge Chromium WebView2 (Native Desktop Window)")
    print("⚡ Tao anh GPU:       ComfyUI SDXL Lightning (Tu dong bat/tat On-Demand)")
    print("🎙️ Giong doc AI:      Edge-TTS & Gemini Audio Studio")
    print("🔑 Dieu phoi API:     Resilient Multi-Key Quota Failover")
    print("-" * 70)
    print("[LUU Y QUAN TRONG]:")
    print("  * Khi dong cua so ung dung, he thong se tu dong giai phong tai nguyen.")
    print("=" * 70 + "\n")

    # 2. Launch Primary Desktop GUI: PyQt6 Native Desktop Window (Fast, rock-solid, direct Win32 display)
    try:
        log_app("Khoi chay Primary Desktop Engine: PyQt6 QtWebEngine...")
        print("[LAUNCHER] Khoi chay Native Desktop Engine: PyQt6 WebEngine...")
        run_qt6_desktop(URL)
        log_app("run_qt6_desktop ket thuc binh thuong.")
        return
    except Exception as e:
        import traceback
        log_app(f"PyQt6 gap loi ({e}). Chi tiet:\n{traceback.format_exc()}\nChuyen sang WebView2...")
        print(f"[LAUNCHER] PyQt6 that bai ({e}). Chuyen sang Edge Chromium WebView2...")

    # 3. Fallback: Edge Chromium WebView2 via pywebview (Native WinForms Desktop Window)
    try:
        log_app("Khoi chay Fallback: Edge Chromium WebView2 (pywebview)...")
        print("[LAUNCHER] Khoi chay Fallback: Edge Chromium WebView2...")
        run_pywebview_desktop(URL)
        log_app("run_pywebview_desktop ket thuc.")
        return
    except Exception as e:
        log_app(f"WebView2 that bai: {e}")
        print(f"[DESKTOP_APP] Khoi chay Native Desktop that bai: {e}")


if __name__ == "__main__":
    main()
