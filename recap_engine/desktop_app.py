"""Movie Recap Studio Pro - Native Windows Desktop Application Window.
Renders the complete Movie Recap Studio interface inside a standalone native desktop app window
powered by Edge/Chrome Chromium App Mode with automatic pywebview fallback and port management.
"""

from __future__ import annotations

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

# Auto-hide console window on Windows so only the clean Desktop App is visible
if os.name == "nt":
    try:
        import ctypes
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)  # SW_HIDE
    except Exception:
        pass

RECAP_DIR = Path(__file__).resolve().parent
PYTHON = sys.executable
PORT = 8095
URL = f"http://127.0.0.1:{PORT}"


def is_server_ready(timeout: float = 2.0) -> bool:
    """Checks if the Recap Engine server is responding."""
    for path in ("/api/status", "/"):
        try:
            req = urllib.request.Request(f"{URL}{path}", headers={"User-Agent": "DesktopApp"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status in (200, 204):
                    return True
        except Exception:
            pass
    return False


def get_pids_on_port(port: int) -> list[int]:
    """Finds PIDs listening on port 8095 on Windows."""
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
    """Kills any dead processes hanging on the port."""
    if is_server_ready():
        return

    pids = get_pids_on_port(port)
    if not pids:
        return

    current_pid = os.getpid()
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    for pid in pids:
        if pid != current_pid and pid > 0:
            print(f"[DESKTOP] Giải phóng port {port} (PID: {pid})...")
            try:
                subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True, creationflags=flags)
            except Exception:
                pass
    time.sleep(0.5)


def start_backend_server():
    """Starts backend server.py in background if not already running."""
    if is_server_ready():
        print(f"[DESKTOP] Server đã sẵn sàng tại: {URL}")
        return None

    cleanup_stale_port(PORT)

    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    server_script = RECAP_DIR / "server.py"

    env = os.environ.copy()
    env["PYTHONPATH"] = str(RECAP_DIR) + os.pathsep + env.get("PYTHONPATH", "")

    proc = subprocess.Popen(
        [PYTHON, "-u", str(server_script)],
        cwd=str(RECAP_DIR),
        env=env,
        creationflags=flags
    )

    # Wait for server to become responsive
    for _ in range(50):
        time.sleep(0.15)
        if is_server_ready():
            print(f"[DESKTOP] Server khởi động thành công tại: {URL}")
            return proc
        if proc.poll() is not None:
            break

    raise RuntimeError("RECAP_ENGINE_SERVER_FAILED_STARTUP")


def find_app_browser() -> str | None:
    """Finds installed Chromium browser supporting native clean --app mode."""
    candidates = [
        # Microsoft Edge (Pre-installed on 100% of Windows 10/11)
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%LocalAppData%\Microsoft\Edge\Application\msedge.exe"),
        # Google Chrome
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
        # Brave Browser
        os.path.expandvars(r"%ProgramFiles%\BraveSoftware\Brave-Browser\Application\brave.exe"),
        os.path.expandvars(r"%LocalAppData%\BraveSoftware\Brave-Browser\Application\brave.exe"),
    ]
    for p in candidates:
        if os.path.isfile(p):
            return p
    return None


def ensure_maximized_background():
    """Monitors startup and ensures the application window is fully maximized."""
    if os.name != "nt":
        return
    try:
        import ctypes
        SW_MAXIMIZE = 3
        for _ in range(40):
            time.sleep(0.2)
            def enum_cb(hwnd, extra):
                if ctypes.windll.user32.IsWindowVisible(hwnd):
                    length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        buff = ctypes.create_unicode_buffer(length + 1)
                        ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
                        title = buff.value
                        if any(k.lower() in title.lower() for k in ("Movie Recap", "Phim Review", "127.0.0.1:8095", "localhost:8095")):
                            ctypes.windll.user32.ShowWindow(hwnd, SW_MAXIMIZE)
                            ctypes.windll.user32.SetForegroundWindow(hwnd)
                            return False
                return True
            ENUM_WINDOWS_PROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
            cb = ENUM_WINDOWS_PROC(enum_cb)
            ctypes.windll.user32.EnumWindows(cb, 0)
    except Exception:
        pass


def open_desktop_window():
    """Opens Movie Recap Studio in a dedicated native desktop window."""
    browser = find_app_browser()
    if browser:
        print(f"[DESKTOP] Đang mở giao diện Desktop qua {Path(browser).name} (Native App Mode)...")
        profile_dir = RECAP_DIR / ".recap_desktop_profile"
        profile_dir.mkdir(parents=True, exist_ok=True)
        cmd = [
            browser,
            f"--app={URL}",
            f"--user-data-dir={profile_dir}",
            "--start-maximized",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-features=msHub,msEdgeAppModeAddressBar",
            "--app-id=MovieRecapStudioPro",
        ]
        try:
            # Khởi chạy cửa sổ ứng dụng ở chế độ hiển thị bình thường phóng to toàn màn hình
            proc = subprocess.Popen(cmd)
            threading.Thread(target=ensure_maximized_background, daemon=True).start()
            return proc
        except Exception as e:
            print(f"[DESKTOP] Lỗi khởi chạy Chromium App Mode ({e}), chuyển sang pywebview...")

    # Fallback to pywebview if available
    try:
        import webview
        print("[DESKTOP] Đang mở cửa sổ qua pywebview...")
        window = webview.create_window(
            title="🎬 Movie Recap Studio Pro v0.0.1 - Phim Review Bất Bại",
            url=URL,
            width=1480,
            height=920,
            resizable=True,
            min_size=(1100, 720),
            maximized=True
        )
        webview.start()
        return None
    except Exception as e:
        print(f"[DESKTOP] pywebview không khả dụng ({e})")

    # Fallback to default browser
    try:
        import webbrowser
        print(f"[DESKTOP] Mở trình duyệt mặc định: {URL}")
        webbrowser.open(URL)
        return None
    except Exception as e:
        pass

    raise RuntimeError("Không tìm thấy môi trường giao diện Desktop (cần Chrome hoặc Edge)!")


def main():
    print("=" * 60)
    print("🎬 KHỞI ĐỘNG MOVIE RECAP STUDIO PRO (DESKTOP APP)")
    print("=" * 60)

    # 1. Start backend server
    backend_proc = start_backend_server()

    # 2. Open native Desktop Window
    win_proc = open_desktop_window()

    if win_proc:
        t_start = time.time()
        try:
            win_proc.wait()
        except KeyboardInterrupt:
            pass
        finally:
            elapsed = time.time() - t_start
            if elapsed > 3.0:
                print("[DESKTOP] Cửa sổ đã được người dùng đóng, kết thúc ứng dụng.")
                if backend_proc:
                    try:
                        backend_proc.terminate()
                    except Exception:
                        pass
            else:
                # Trình duyệt Chromium ủy quyền cho tiến trình nền và thoát ngay, giữ server tiếp tục chạy
                print("[DESKTOP] Cửa sổ ứng dụng đang chạy ở chế độ Native App Mode.")
                if backend_proc:
                    try:
                        backend_proc.wait()
                    except KeyboardInterrupt:
                        backend_proc.terminate()


if __name__ == "__main__":
    main()
