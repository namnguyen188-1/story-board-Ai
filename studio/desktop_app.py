"""Storyboard AI Studio Pro - Native Windows Desktop Application Window.
Renders the complete Studio interface inside a standalone desktop app window
powered by Edge/Chrome Chromium App Mode with automatic failover and port management.
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
PYTHON = sys.executable
PORT = 8765
URL = f"http://127.0.0.1:{PORT}"

ENGINE_BIN = STUDIO_DIR / "engine" / "bin"
if ENGINE_BIN.is_dir() and str(ENGINE_BIN) not in os.environ.get("PATH", ""):
    os.environ["PATH"] = str(ENGINE_BIN) + os.pathsep + os.environ.get("PATH", "")


def is_server_ready(timeout: float = 3.0) -> bool:
    """Checks if the Studio web server is responding."""
    try:
        with urllib.request.urlopen(f"{URL}/api/status", timeout=timeout) as resp:
            return resp.status == 200
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
    if is_server_ready():
        print(f"[LAUNCHER] May chu da san sang tai: {URL}")
        return None

    cleanup_stale_port(PORT)

    from web_server import start_server

    t = threading.Thread(target=start_server, args=(PORT,), daemon=True)
    t.start()

    # Wait for server to become responsive
    for _ in range(40):
        time.sleep(0.1)
        if is_server_ready():
            print(f"[LAUNCHER] May chu da khoi dong thanh cong tai: {URL}")
            return t

    raise RuntimeError("STORYBOARD_HTTP_BACKEND_FAILED_STARTUP")


def find_app_browser() -> str | None:
    """Finds an installed Chromium-based browser supporting clean native --app mode."""
    candidates = [
        # Google Chrome (best clean native app mode with zero address bar)
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
        # Microsoft Edge (Chromium)
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%LocalAppData%\Microsoft\Edge\Application\msedge.exe"),
        # Brave Browser
        os.path.expandvars(r"%ProgramFiles%\BraveSoftware\Brave-Browser\Application\brave.exe"),
        os.path.expandvars(r"%LocalAppData%\BraveSoftware\Brave-Browser\Application\brave.exe"),
    ]
    for p in candidates:
        if os.path.isfile(p):
            return p
    return None


def ensure_window_size_background(target_w: int = 1400, target_h: int = 850) -> None:
    """Monitors desktop app startup and snaps the window to exact target_w x target_h via Win32."""
    from web_server import resize_window_win32
    for _ in range(15):
        time.sleep(0.3)
        count = resize_window_win32(target_w, target_h)
        if count > 0:
            print(f"[LAUNCHER] Da can chinh cua so dung kich thuoc chuan: {target_w}x{target_h}")
            break


def open_desktop_window():
    """Opens the Studio UI in a dedicated native-like desktop window (App Mode)."""
    browser = find_app_browser()
    if browser:
        print(f"[LAUNCHER] Dang mo cua so ung dung qua: {Path(browser).name}")
        profile_dir = STUDIO_DIR / "runtime" / ".desktop_ui_profile"
        profile_dir.mkdir(parents=True, exist_ok=True)
        cmd = [
            browser,
            f"--app={URL}",
            f"--user-data-dir={profile_dir}",
            "--window-size=1400,850",
            "--window-position=50,30",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-features=msHub,msEdgeAppModeAddressBar",
            "--app-id=StoryboardAIStudioPro",
        ]
        try:
            proc = subprocess.Popen(cmd)
            return proc
        except Exception as e:
            print(f"[LAUNCHER] Loi khoi chay App Mode ({e})...")

    # This is a desktop application. Never pop up the default web browser
    # when an app-window executable isn't available.
    raise RuntimeError("STORYBOARD_DESKTOP_APP_BROWSER_NOT_FOUND")


def cleanup_all():
    """Cleans up background MCP and port listeners on app shutdown."""
    print("[DESKTOP_APP] Dọn dẹp tiến trình khi thoát...")
    try:
        cleanup_stale_port(PORT)
    except Exception:
        pass


def main():
    print("=" * 70)
    print("🎬 KHOI DONG STORYBOARD AI STUDIO PRO (DESKTOP APP)")
    print("=" * 70)

    # 1. Start or verify backend
    server_thread = start_backend_server()

    # 2. In EXE mode, only the native launcher owns the one Studio window.
    # It starts this UI only after the backend is confirmed healthy. Prevent
    # multiple Edge app-mode windows when a launcher or Python PID restarts.
    proc = None
    if os.environ.get("STORYBOARD_NATIVE_WINDOW_OWNER") != "1":
        proc = open_desktop_window()

    # 3. Actively snap window to exact 1400x850 at OS level
    threading.Thread(target=ensure_window_size_background, args=(1400, 850), daemon=True).start()

    print("\n" + "=" * 70)
    print("✨ STORYBOARD AI STUDIO PRO DANG HOAT DONG")
    print("=" * 70)
    print(f"🌐 Dia chi Studio:    {URL}")
    print("🖥️ Cua so ung dung:   Da mo truc tiep tren man hinh!")
    print("⚡ Tao anh GPU:       ComfyUI SDXL Lightning (Tu dong bat/tat On-Demand)")
    print("🎙️ Giong doc AI:      Edge-TTS & Gemini Audio Studio")
    print("🔑 Dieu phoi API:     Resilient Multi-Key Quota Failover")
    print("-" * 70)
    print("[LUU Y QUAN TRONG]:")
    print("  * Khi dong cua so ung dung, he thong se tu dong giai phong tai nguyen.")
    print("=" * 70 + "\n")

    # 4. The native EXE owns the backend lifetime. Edge/Chrome process exit
    # is NOT a reliable window-close event: Chromium may hand --app to an
    # existing browser and the subprocess returned by Popen can exit at once.
    # Never shut down Studio merely because this short-lived process exits.
    try:
        consecutive_fails = 0
        while True:
            time.sleep(3)
            if server_thread is not None and not server_thread.is_alive():
                print("[STUDIO_PRO] HTTP backend thread exited; supervisor will recover.")
                raise RuntimeError("STORYBOARD_HTTP_BACKEND_STOPPED")
            if not is_server_ready(timeout=4.0):
                consecutive_fails += 1
                if consecutive_fails >= 6:
                    print("[STUDIO_PRO] HTTP backend unresponsive for 18s; supervisor will recover.")
                    raise RuntimeError("STORYBOARD_HTTP_BACKEND_STOPPED")
            else:
                consecutive_fails = 0
    except KeyboardInterrupt:
        print("[STUDIO_PRO] User requested shutdown.")
    finally:
        # Do not kill a different listener or user Chrome on shutdown.
        sys.exit(0)


if __name__ == "__main__":
    main()
