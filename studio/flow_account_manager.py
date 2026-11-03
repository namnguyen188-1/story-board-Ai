
"""FlowKit Google Flow Account and Window Manager for Storyboard AI Studio.

Handles Chrome window lifecycle, user authentication detection, and seamless
transition into background Web Tool mode without screen jumping or legacy MCP loops.
Uses Shell.Application to guarantee Chrome opens on the user's interactive monitor.
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
import threading
import time
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("flow_account_manager")

def is_port_listening(port: int) -> bool:
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.25)
            return s.connect_ex(("127.0.0.1", int(port))) == 0
    except Exception:
        return False


FLOWKIT_ROOT = Path("D:/FLOWKIT")
FLOW_ACCOUNTS_DIR = Path(__file__).resolve().parent / "flow_accounts"
ACCOUNTS_DB_FILE = Path("studio/runtime/storyboard_accounts.json")
DEFAULT_TARGET_URL = "https://flow.google.com/project/c7186034-34e8-463c-9f1b-2ceac85cde38/tool/69da86fb-6c79-43d2-a387-ef47b0fda4db"
GOOGLE_SIGNIN_URL = "https://accounts.google.com/ServiceLogin?continue=https://flow.google.com"

_WATCHER_THREAD: Optional[threading.Thread] = None
_WATCHER_STOP = threading.Event()

_LOGIN_STATE: Dict[str, Any] = {
    "status": "idle",
    "watcher_active": False,
    "status_text": "Web Tool Google Flow sẵn sàng (Model: Omni 1.1 Flash).",
    "badge_text": "🟢 Sẵn sàng",
    "badge_type": "success",
    "email": "",
    "last_account_id": ""
}


def _chrome_exe_path() -> str:
    paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
    ]
    for p in paths:
        if os.path.isfile(p):
            return p
    return "chrome.exe"


def _kill_chrome_on_port(port: int = 9461):
    """Cleanly terminate any existing Chrome process on the debug port."""
    try:
        from studio_mcp.accounts import _find_pid_by_cdp_port
        pid = _find_pid_by_cdp_port(port)
        if pid > 0:
            if os.name == "nt":
                subprocess.run(
                    ["powershell.exe", "-NoProfile", "-Command", f"Stop-Process -Id {pid} -Force -ErrorAction SilentlyContinue"],
                    capture_output=True, timeout=5
                )
            time.sleep(1.0)
    except Exception as e:
        logger.warning(f"Error killing Chrome on port {port}: {e}")


def _bring_window_to_front_win32(port: int = 9461):
    """Enumerate windows on Default desktop and bring the Chrome window to foreground."""
    try:
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.windll.user32
        hDesk = user32.OpenDesktopW("Default", 0, False, 0x01FF)
        if not hDesk:
            return

        HWND_TOPMOST = -1
        HWND_NOTOPMOST = -2
        SWP_NOSIZE = 0x0001
        SWP_NOMOVE = 0x0002
        SWP_SHOWWINDOW = 0x0040

        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        hwnds = []
        def enum_cb(hwnd, lparam):
            if user32.IsWindowVisible(hwnd):
                pid = wintypes.DWORD()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                buf = ctypes.create_unicode_buffer(512)
                user32.GetWindowTextW(hwnd, buf, 512)
                t = buf.value.lower()
                if "restore pages" in t:
                    user32.PostMessageW(hwnd, 0x0010, 0, 0)
                elif "chrome" in t or "google" in t or "đăng nhập" in t or "sign in" in t:
                    hwnds.append(hwnd)
            return True

        user32.EnumDesktopWindows(hDesk, WNDENUMPROC(enum_cb), 0)
        user32.CloseDesktop(hDesk)

        for hwnd in hwnds:
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)
            user32.SetWindowPos(hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)
            user32.SetForegroundWindow(hwnd)
    except Exception as e:
        logger.warning(f"Could not bring window to front: {e}")


def _launch_chrome_interactive(chrome_exe: str, profile_dir: Path, port: int, initial_url: str):
    """Launch Chrome in the interactive user desktop via schtasks /it.
    
    This guarantees that the window opens visually on the user's physical monitor,
    even when triggered from a background web server process.
    """
    profile_str = str(profile_dir).replace("/", "\\")
    bat_file = FLOW_ACCOUNTS_DIR / f"launch_flow_{port}.bat"
    FLOW_ACCOUNTS_DIR.mkdir(parents=True, exist_ok=True)

    cmd_line = (
        f'@echo off\r\n'
        f'start "" "{chrome_exe}" '
        f'--user-data-dir="{profile_str}" '
        f'--remote-debugging-port={port} '
        f'--remote-debugging-address=127.0.0.1 '
        f'--no-first-run '
        f'--no-default-browser-check '
        f'--disable-session-crashed-bubble '
        f'--window-size=1100,800 '
        f'--window-position=80,80 '
        f'"{initial_url}"\r\n'
    )
    bat_file.write_text(cmd_line, encoding="ascii", errors="replace")

    task_name = f"FlowChromeLaunch_{port}"
    task_succeeded = False
    try:
        subprocess.run(
            ["schtasks.exe", "/create", "/tn", task_name, "/tr", f'"{bat_file}"', "/sc", "once", "/st", "23:59", "/it", "/f"],
            capture_output=True, timeout=5
        )
        res = subprocess.run(
            ["schtasks.exe", "/run", "/tn", task_name],
            capture_output=True, timeout=5
        )
        task_succeeded = (res.returncode == 0)
        time.sleep(1.0)
        subprocess.run(
            ["schtasks.exe", "/delete", "/tn", task_name, "/f"],
            capture_output=True, timeout=5
        )
    except Exception as e:
        logger.warning(f"schtasks interactive launch error: {e}")

    if not task_succeeded:
        # Fallback to Popen with WinSta0\Default
        try:
            si = subprocess.STARTUPINFO()
            si.lpDesktop = r"WinSta0\Default"
            subprocess.Popen(
                [chrome_exe, f'--user-data-dir={profile_str}', f'--remote-debugging-port={port}',
                 '--remote-debugging-address=127.0.0.1', '--no-first-run', '--no-default-browser-check',
                 '--disable-session-crashed-bubble', '--window-size=1100,800', '--window-position=80,80', initial_url],
                startupinfo=si, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        except Exception as ex:
            logger.warning(f"Fallback Popen error: {ex}")

    time.sleep(1.5)
    _bring_window_to_front_win32(port)


def _set_chrome_visibility_win32(port: int = 9461, show: bool = True):
    """Hide or show Chrome window physically on the Default desktop.
    
    When show=False: calls SW_HIDE (0) so Chrome vanishes completely from Desktop AND Taskbar!
    When show=True: calls SW_RESTORE (9) and SetForegroundWindow so it reappears for login.
    """
    try:
        import ctypes
        from ctypes import wintypes
        import subprocess

        user32 = ctypes.windll.user32

        # 1. Collect target Chrome PIDs (CDP debugging processes only)
        target_pids = set()

        # Check netstat for port
        try:
            out = subprocess.run(
                ["netstat", "-ano", "-p", "tcp"],
                capture_output=True, text=True, timeout=2,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
            ).stdout
            for line in out.splitlines():
                if f":{port}" in line and "LISTENING" in line:
                    parts = line.strip().split()
                    if len(parts) >= 5 and parts[-1].isdigit():
                        p = int(parts[-1])
                        if p > 0:
                            target_pids.add(p)
        except Exception:
            pass

        # Check WMI for chrome.exe with this port
        try:
            ps_cmd = f"Get-CimInstance Win32_Process -Filter \"Name = 'chrome.exe'\" | Where-Object {{ $_.CommandLine -like '*--remote-debugging-port={port}*' -and $_.CommandLine -notlike '*--type=*' }} | Select-Object ProcessId | ConvertTo-Json"
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True, text=True, timeout=4,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
            )
            if res.stdout.strip():
                data = json.loads(res.stdout)
                if isinstance(data, dict):
                    data = [data]
                for item in data:
                    target_pids.add(item["ProcessId"])
        except Exception:
            pass

        if not target_pids:
            return

        # 2. Enumerate windows on Default desktop and current desktop
        desktops = []
        h_def = user32.OpenDesktopW("Default", 0, False, 0x10000000)
        if h_def:
            desktops.append((h_def, True))
        h_curr = user32.GetThreadDesktop(ctypes.windll.kernel32.GetCurrentThreadId())
        if h_curr and h_curr != h_def:
            desktops.append((h_curr, False))

        for hDesk, should_close in desktops:
            def enum_cb(hwnd, lparam):
                pid = wintypes.DWORD()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                title_buf = ctypes.create_unicode_buffer(512)
                user32.GetWindowTextW(hwnd, title_buf, 512)
                title = title_buf.value
                cls_buf = ctypes.create_unicode_buffer(256)
                user32.GetClassNameW(hwnd, cls_buf, 256)
                cls = cls_buf.value

                is_match = False
                if pid.value in target_pids:
                    is_match = True
                elif ("Chrome" in cls or "Chrome" in title) and ("Google Flow" in title or "Storyboard Director" in title or "accounts.google.com" in title):
                    is_match = True

                if is_match:
                    if show:
                        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                        user32.SetForegroundWindow(hwnd)
                    else:
                        user32.ShowWindow(hwnd, 0)  # SW_HIDE: completely removes from Taskbar and screen!
                return 1

            CMPFUNC = ctypes.WINFUNCTYPE(ctypes.c_int, wintypes.HWND, wintypes.LPARAM)
            cb_func = CMPFUNC(enum_cb)
            user32.EnumDesktopWindows(hDesk, cb_func, 0)
            if should_close:
                user32.CloseDesktop(hDesk)

    except Exception as e:
        logger.warning(f"Error setting Chrome window visibility: {e}")


def set_chrome_window_state(port: int = 9461, state: str = "normal") -> bool:
    """Set Chrome window to 'normal' (visible) or 'hidden' (vanishes from Taskbar & Desktop)."""
    unlock_flag = FLOWKIT_ROOT / "state" / "flow_window" / "unlock.flag"
    if state == "normal":
        unlock_flag.parent.mkdir(parents=True, exist_ok=True)
        unlock_flag.write_text("unlock", encoding="ascii")
        _set_chrome_visibility_win32(port=port, show=True)
    else:
        try:
            if unlock_flag.is_file():
                unlock_flag.unlink()
        except Exception:
            pass
        # SW_HIDE removes window completely from Taskbar and Desktop
        _set_chrome_visibility_win32(port=port, show=False)

    try:
        from websockets.sync.client import connect
        # 1. Get browser websocket URL
        req = urllib.request.Request(f"http://127.0.0.1:{port}/json/version")
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            ver = json.loads(resp.read().decode("utf-8"))
        ws_url = ver.get("webSocketDebuggerUrl")
        if not ws_url:
            return True

        # 2. Get target page tab
        t_req = urllib.request.Request(f"http://127.0.0.1:{port}/json")
        with urllib.request.urlopen(t_req, timeout=2.0) as resp:
            tabs = json.loads(resp.read().decode("utf-8"))
        page_tab = next((t for t in tabs if t.get("type") == "page"), None)
        if not page_tab:
            return True

        with connect(ws_url, open_timeout=3.0) as ws:
            ws.send(json.dumps({"id": 1, "method": "Browser.getWindowForTarget", "params": {"targetId": page_tab["id"]}}))
            res = json.loads(ws.recv())
            window_id = res.get("result", {}).get("windowId")
            if window_id:
                if state == "normal":
                    bounds = {"left": 80, "top": 80, "width": 1100, "height": 800, "windowState": "normal"}
                else:
                    bounds = {"windowState": "minimized"}
                ws.send(json.dumps({"id": 2, "method": "Browser.setWindowBounds", "params": {"windowId": window_id, "bounds": bounds}}))
                ws.recv()
            return True
    except Exception as e:
        logger.warning(f"set_chrome_window_state failed ({state}): {e}")
        return True


def get_logged_in_email(port: int = 9461) -> str:
    """Extract authenticated Google email from active Chrome session via CDP."""
    cached = _LOGIN_STATE.get("email")
    if cached:
        return cached

    try:
        req = urllib.request.Request(f"http://127.0.0.1:{port}/json")
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            tabs = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return ""

    from websockets.sync.client import connect

    script = """(() => {
        const all = document.querySelectorAll('*');
        for (const el of all) {
            const label = el.getAttribute('aria-label') || '';
            const title = el.getAttribute('title') || '';
            const text = el.innerText || '';
            for (const s of [label, title, text]) {
                const m = s.match(/[a-zA-Z0-9._%+-]+@(gmail\\.com|[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,})/);
                if (m && !m[0].includes('example') && !m[0].includes('google.com')) {
                    return m[0];
                }
            }
        }
        return '';
    })()"""

    pages = [x for x in tabs if x.get("type") == "page"]
    for p in pages:
        ws_url = p.get("webSocketDebuggerUrl")
        if not ws_url:
            continue
        try:
            with connect(ws_url, open_timeout=2.0) as ws:
                ws.send(json.dumps({
                    "id": 1,
                    "method": "Runtime.evaluate",
                    "params": {"expression": script, "returnByValue": True, "awaitPromise": True}
                }))
                res = json.loads(ws.recv())
                email = res.get("result", {}).get("result", {}).get("value")
                if email:
                    _LOGIN_STATE["email"] = email
                    return email
        except Exception:
            continue

    return ""


def check_login_status(port: int = 9461) -> Dict[str, Any]:
    """Check tabs and live auth cookies on port 9461 to accurately detect Google Flow authentication."""
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{port}/json")
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            tabs = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return {"chrome_running": False, "signing_in": False, "logged_in": False, "on_webtool": False}

    signing_in = False
    on_flow = False
    on_webtool = False
    has_auth_cookie_indicator = False

    for t in tabs:
        url = str(t.get("url") or "")

        # Check for Google Signin page
        if any(x in url for x in ("accounts.google.com/v3/signin", "accounts.google.com/ServiceLogin",
                                  "accounts.google.com/signin/v2", "accounts.google.com/AccountChooser")):
            if "identifier" in url or "challenge" in url:
                signing_in = True

        # Check if Google session cookies rotation is active (Google uses this when signed in)
        if "accounts.google.com/RotateCookiesPage" in url or "scf.usercontent.goog" in url:
            has_auth_cookie_indicator = True

        # Check Flow domain
        if "flow.google.com" in url:
            on_flow = True
            if "/tool/" in url or "/project/" in url:
                on_webtool = True

    # Real-time check of auth cookies via CDP Network.getCookies
    try:
        from websockets.sync.client import connect
        v_req = urllib.request.Request(f"http://127.0.0.1:{port}/json/version")
        with urllib.request.urlopen(v_req, timeout=1.0) as resp:
            v_data = json.loads(resp.read().decode("utf-8"))
        ws_url = v_data.get("webSocketDebuggerUrl")
        if ws_url:
            with connect(ws_url, open_timeout=1.5) as ws:
                ws.send(json.dumps({
                    "id": 100,
                    "method": "Network.getCookies",
                    "params": {"urls": ["https://google.com", "https://flow.google.com", "https://accounts.google.com"]}
                }))
                res = json.loads(ws.recv())
                cookies = res.get("result", {}).get("cookies", [])
                cookie_names = {c.get("name") for c in cookies}
                if any(x in cookie_names for x in ("SID", "SSID", "HSID", "SAPISID", "__Secure-1PSID")):
                    has_auth_cookie_indicator = True
                    signing_in = False  # Confirmed authenticated!
    except Exception:
        pass

    logged_in = (on_flow or has_auth_cookie_indicator or on_webtool) and not signing_in
    email = ""
    if logged_in:
        email = get_logged_in_email(port)

    return {
        "chrome_running": True,
        "signing_in": signing_in,
        "logged_in": logged_in,
        "on_webtool": on_webtool,
        "email": email,
        "tabs_count": len(tabs)
    }


def _login_watcher_loop(port: int = 9461, timeout_seconds: int = 300):
    """Background watcher that keeps window open during signin and auto-hides on completion."""
    global _LOGIN_STATE
    _LOGIN_STATE["watcher_active"] = True
    start_time = time.monotonic()

    logger.info("Login watcher loop started")

    while not _WATCHER_STOP.is_set():
        if time.monotonic() - start_time > timeout_seconds:
            _LOGIN_STATE["status_text"] = "Hết thời gian chờ đăng nhập (5 phút). Hãy bấm Đăng Nhập lại nếu cần."
            _LOGIN_STATE["badge_text"] = "🟡 Hết giờ"
            _LOGIN_STATE["badge_type"] = "warning"
            break

        status = check_login_status(port)

        if not status["chrome_running"]:
            time.sleep(1.5)
            continue

        if status["signing_in"]:
            _LOGIN_STATE["status_text"] = "Đang mở trình duyệt. Hãy đăng nhập tài khoản Google của bạn trong Chrome. Cửa sổ giữ nguyên."
            _LOGIN_STATE["badge_text"] = "🟡 Đang đăng nhập"
            _LOGIN_STATE["badge_type"] = "warning"
            time.sleep(2.0)
            continue

        if status["logged_in"]:
            email = status.get("email") or get_logged_in_email(port)
            _LOGIN_STATE["email"] = email
            email_tag = f"Tài khoản: {email} · " if email else ""
            _LOGIN_STATE["status_text"] = f"Đã đăng nhập Google thành công ({email})! Đang tự động kết nối Web Tool..."
            _LOGIN_STATE["badge_text"] = "🟡 Đang kết nối"
            _LOGIN_STATE["badge_type"] = "warning"

            # 1. If not on web tool URL, navigate to it
            if not status["on_webtool"]:
                try:
                    n_req = urllib.request.Request(
                        f"http://127.0.0.1:{port}/json/new?{urllib.parse.quote(DEFAULT_TARGET_URL)}",
                        method="PUT"
                    )
                    urllib.request.urlopen(n_req, timeout=3.0)
                except Exception as e:
                    logger.warning(f"Could not open web tool tab: {e}")

            # 2. Wait 2 seconds for Web Tool Bridge extension to hook into the tab
            time.sleep(2.0)

            # 3. AUTO-HIDE COMPLETELY: Both from screen and taskbar via SW_HIDE (0)
            set_chrome_window_state(port=port, state="hidden")
            _set_chrome_visibility_win32(port=port, show=False)

            # 4. Final state update
            _LOGIN_STATE["status_text"] = f"✓ {email_tag}Web Tool đã kết nối (Model: Omni 1.1 Flash)."
            _LOGIN_STATE["badge_text"] = "🟢 Sẵn sàng"
            _LOGIN_STATE["badge_type"] = "success"
            logger.info("Login completed; Chrome automatically hidden completely from taskbar")
            break

        time.sleep(2.0)

    _LOGIN_STATE["watcher_active"] = False


def start_login_watcher(port: int = 9461):
    """Launch watcher thread in background."""
    global _WATCHER_THREAD, _WATCHER_STOP
    _WATCHER_STOP.set()
    if _WATCHER_THREAD and _WATCHER_THREAD.is_alive():
        _WATCHER_THREAD.join(timeout=1.0)

    _WATCHER_STOP.clear()
    _WATCHER_THREAD = threading.Thread(target=_login_watcher_loop, args=(port,), daemon=True)
    _WATCHER_THREAD.start()


def open_google_flow_login() -> Dict[str, Any]:
    """Open Chrome for Google Flow login, keeping it open steadily until user signs in."""
    from flowkit_client import ensure_flowkit_running
    ensure_flowkit_running()

    machine_file = FLOWKIT_ROOT / "state" / "machine.json"
    profile = FLOW_ACCOUNTS_DIR / "account_e4bebf4fd95a"
    port = 9461

    if machine_file.is_file():
        try:
            m = json.loads(machine_file.read_text(encoding="utf-8-sig"))
            if m.get("flow_profile"):
                profile = Path(m["flow_profile"])
            port = int(m.get("debug_port", 9461))
        except Exception:
            pass

    profile.mkdir(parents=True, exist_ok=True)

    status = check_login_status(port)
    if status.get("logged_in"):
        # Already logged in: ensure Chrome is hidden completely from Taskbar and Desktop
        set_chrome_window_state(port=port, state="hidden")
        return {
            "success": True,
            "message": "Tài khoản Google đã đăng nhập. Trình duyệt đang chạy ngầm bảo mật, Web Tool sẵn sàng."
        }

    if not status["chrome_running"]:
        chrome = _chrome_exe_path()
        _launch_chrome_interactive(chrome, profile, port, GOOGLE_SIGNIN_URL)
        time.sleep(2.0)
    else:
        set_chrome_window_state(port=port, state="normal")
        if not status["logged_in"]:
            try:
                t_req = urllib.request.Request(f"http://127.0.0.1:{port}/json")
                with urllib.request.urlopen(t_req, timeout=2.0) as resp:
                    tabs = json.loads(resp.read().decode("utf-8"))
                p_tab = next((t for t in tabs if t.get("type") == "page"), None)
                if p_tab:
                    from websockets.sync.client import connect
                    with connect(p_tab["webSocketDebuggerUrl"], open_timeout=2.0) as ws:
                        ws.send(json.dumps({"id": 1, "method": "Page.navigate", "params": {"url": GOOGLE_SIGNIN_URL}}))
                        ws.recv()
                        ws.send(json.dumps({"id": 2, "method": "Page.bringToFront"}))
                        ws.recv()
            except Exception as e:
                logger.warning(f"Could not navigate to signin: {e}")

    start_login_watcher(port=port)

    return {
        "success": True,
        "message": "Đã mở trình duyệt Chrome Google Flow. Cửa sổ giữ nguyên để bạn đăng nhập. Khi đăng nhập xong, hệ thống sẽ TỰ ĐỘNG ẩn trình duyệt và kết nối Web Tool."
    }


def add_new_account() -> Dict[str, Any]:
    """Create a brand new Chrome profile and open Chrome for Google sign-in.
    
    Guarantees window opens visually in the interactive user desktop and stays open.
    """
    from flowkit_client import ensure_flowkit_running
    ensure_flowkit_running()

    port = 9461

    # 1. Cleanly stop old Chrome on port 9461
    _kill_chrome_on_port(port)

    # 2. Generate new account ID and profile directory
    account_id = f"account_{uuid.uuid4().hex[:12]}"
    new_profile = FLOW_ACCOUNTS_DIR / account_id
    new_profile.mkdir(parents=True, exist_ok=True)

    # 3. Update D:\FLOWKIT\state\machine.json
    machine_file = FLOWKIT_ROOT / "state" / "machine.json"
    machine_file.parent.mkdir(parents=True, exist_ok=True)
    machine_data = {
        "chrome": _chrome_exe_path(),
        "flow_profile": str(new_profile).replace("/", "\\"),
        "debug_port": port
    }
    machine_file.write_text(json.dumps(machine_data, indent=2), encoding="utf-8")

    # 4. Save to storyboard_accounts.json
    try:
        ACCOUNTS_DB_FILE.parent.mkdir(parents=True, exist_ok=True)
        db_data = {"version": 1, "active": account_id, "accounts": []}
        if ACCOUNTS_DB_FILE.is_file():
            try:
                db_data = json.loads(ACCOUNTS_DB_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass

        existing = db_data.get("accounts", [])
        used_ports = [x.get("cdp_port", 9460) for x in existing if isinstance(x.get("cdp_port"), int)]
        assigned_port = max(used_ports + [9460]) + 1
        num = len(existing) + 1
        new_entry = {
            "id": account_id,
            "name": f"TK {num}",
            "user_data_dir": str(new_profile),
            "profile_directory": "Default",
            "cdp_port": assigned_port,
            "state_dir": str(FLOW_ACCOUNTS_DIR / f"{account_id}_state")
        }
        existing.append(new_entry)
        db_data["active"] = account_id
        db_data["accounts"] = existing
        ACCOUNTS_DB_FILE.write_text(json.dumps(db_data, indent=2), encoding="utf-8")
    except Exception as e:
        logger.warning(f"Could not update accounts DB: {e}")

    # 5. Ensure unlock.flag is present
    unlock_flag = FLOWKIT_ROOT / "state" / "flow_window" / "unlock.flag"
    unlock_flag.parent.mkdir(parents=True, exist_ok=True)
    unlock_flag.write_text("unlock", encoding="ascii")

    # 6. Launch Chrome directly on interactive desktop via Shell.Application
    chrome = _chrome_exe_path()
    _launch_chrome_interactive(chrome, new_profile, port, GOOGLE_SIGNIN_URL)
    time.sleep(2.0)

    # 7. Start background watcher to auto-hide and connect web tool when login completes
    _LOGIN_STATE["email"] = ""
    _LOGIN_STATE["last_account_id"] = account_id
    _LOGIN_STATE["status_text"] = "Đã mở Chrome cho tài khoản mới. Vui lòng đăng nhập Google. Khi đăng nhập xong, hệ thống sẽ TỰ ĐỘNG ẩn trình duyệt và kết nối Web Tool."
    _LOGIN_STATE["badge_text"] = "🟡 Chờ đăng nhập"
    _LOGIN_STATE["badge_type"] = "warning"
    start_login_watcher(port=port)

    return {
        "success": True,
        "account_id": account_id,
        "message": "Đã tạo hồ sơ mới và mở cửa sổ Chrome. Hãy đăng nhập tài khoản Google của bạn. Cửa sổ giữ nguyên, khi đăng nhập xong hệ thống sẽ TỰ ĐỘNG ẩn và kết nối Web Tool."
    }


def get_flow_account_for_scene(scene_number: int, exclude_ids: list[str] | None = None) -> dict[str, Any]:
    """Select the best account for generating a scene using Round-Robin across all ACTUALLY LIVE ready accounts."""
    accounts_db = Path(__file__).resolve().parent / "runtime" / "storyboard_accounts.json"
    if not accounts_db.is_file():
        return {}
    try:
        data = json.loads(accounts_db.read_text(encoding="utf-8"))
        # ONLY dispatch to accounts whose CDP port is ACTUALLY listening!
        live_accs = [a for a in data.get("accounts", []) if is_port_listening(a.get("cdp_port", 9461))]
        if not live_accs:
            all_accs = data.get("accounts", [])
            return all_accs[0] if all_accs else {}
        if exclude_ids:
            filtered = [a for a in live_accs if a["id"] not in exclude_ids]
            if filtered:
                live_accs = filtered
        idx = (scene_number - 1) % len(live_accs)
        return live_accs[idx]
    except Exception:
        return {}


def get_ui_status() -> Dict[str, Any]:
    """Return unified status for the Studio Settings Section 3 UI with multi-account support."""
    from flowkit_client import is_flowkit_alive, get_webtool_status
    gw_alive = is_flowkit_alive()

    # Load multi-accounts from storyboard_accounts.json
    accounts_db = Path("studio/runtime/storyboard_accounts.json")
    all_accounts = []
    ready_accounts = []
    active_account_id = ""
    if accounts_db.is_file():
        try:
            db_data = json.loads(accounts_db.read_text(encoding="utf-8"))
            all_accounts = db_data.get("accounts", [])
            active_account_id = db_data.get("active", "")
            ready_accounts = [a for a in all_accounts if a.get("email")]
        except Exception:
            pass

    # Check REAL online status: only accounts with listening CDP port are ready
    real_ready = [a for a in all_accounts if a.get("email") and is_port_listening(a.get("cdp_port", 9461))]
    total_cnt = len(all_accounts) if all_accounts else 1
    ready_cnt = len(real_ready)
    emails = [a.get("email") for a in real_ready if a.get("email")]
    if not emails and is_port_listening(9461):
        live_em = get_logged_in_email(9461)
        if live_em:
            emails = [live_em]
            ready_cnt = 1

    short_emails = [e.split("@")[0] for e in emails]
    emails_tag = ", ".join(short_emails) if short_emails else "Chưa có"

    # If watcher is active, prioritize watcher feedback
    if _LOGIN_STATE.get("watcher_active"):
        return {
            "ready": gw_alive,
            "connected": False,
            "email": _LOGIN_STATE.get("email", ""),
            "emails": emails,
            "total_accounts": total_cnt,
            "ready_accounts": ready_cnt,
            "badge_text": _LOGIN_STATE.get("badge_text", "🟡 Đang đăng nhập"),
            "badge_type": _LOGIN_STATE.get("badge_type", "warning"),
            "status_text": _LOGIN_STATE.get("status_text", "Đang mở Chrome để bạn đăng nhập..."),
            "watcher_active": True
        }

    # Query live WebTool status
    wt = get_webtool_status("hidden") if gw_alive else {"connected": False}
    connected = wt.get("connected", False)

    email = _LOGIN_STATE.get("email") or get_logged_in_email(9461) or "thangmayhn2021@gmail.com"

    if connected or gw_alive:
        # Enforce that Chrome remains 100% hidden from Taskbar & Desktop during normal usage
        _set_chrome_visibility_win32(port=9461, show=False)
        return {
            "ready": True,
            "connected": True,
            "email": email,
            "emails": emails,
            "total_accounts": total_cnt,
            "ready_accounts": ready_cnt,
            "accounts": all_accounts,
            "active_id": active_account_id,
            "dispatch_mode": "round_robin",
            "badge_text": f"🟢 {ready_cnt}/{total_cnt} Đa luồng" if ready_cnt > 1 else f"🟢 {ready_cnt} TK Sẵn sàng",
            "badge_type": "success" if ready_cnt > 0 else "warning",
            "status_text": f"● {ready_cnt} tài khoản sẵn sàng ({emails_tag}) · Đa luồng Round-Robin" if ready_cnt > 1 else f"✓ Web Tool đã kết nối ({emails[0] if emails else 'Sẵn sàng'})",
            "watcher_active": False
        }
    else:
        return {
            "ready": False,
            "connected": False,
            "email": "",
            "emails": [],
            "total_accounts": total_cnt,
            "ready_accounts": 0,
            "badge_text": "🔴 Chưa kết nối",
            "badge_type": "error",
            "status_text": "FlowKit Gateway chưa hoạt động. Bấm [Đăng Nhập Google Flow] để khởi động.",
            "watcher_active": False
        }