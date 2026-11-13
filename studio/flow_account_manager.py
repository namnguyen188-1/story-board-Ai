"""FlowKit Google Flow Account and Window Manager for Storyboard AI Studio.



Handles Chrome window lifecycle, user authentication detection, and seamless

transition into background Web Tool mode without screen jumping or legacy MCP loops.

Guarantees Chrome opens visibly on the interactive user desktop across all Windows machines.

"""

from __future__ import annotations

try:
    import silent_subprocess
except ImportError:
    pass




import json

import logging

import os

import subprocess

import sys

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





def _resolve_flowkit_root() -> Path:

    try:

        from flowkit_client import _resolve_flowkit_root as _fk_root

        return _fk_root()

    except Exception:

        env_p = os.environ.get("FLOWKIT_ROOT", "").strip()

        candidates = [

            Path(env_p) if env_p else None,

            Path(__file__).resolve().parent.parent / "FLOWKIT",

            Path(__file__).resolve().parent / "flowkit",

            Path("D:/FLOWKIT"),

            Path("C:/FLOWKIT"),

        ]

        for c in candidates:

            if c and c.is_dir() and (c / "app").is_dir():

                return c

        return Path("D:/FLOWKIT")





FLOWKIT_ROOT = _resolve_flowkit_root()

FLOW_ACCOUNTS_DIR = Path(__file__).resolve().parent / "flow_accounts"

ACCOUNTS_DB_FILE = Path(__file__).resolve().parent / "runtime" / "storyboard_accounts.json"

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

    """Dynamically locate Google Chrome executable across all drives and registry keys."""

    # 1. Check Windows Registry App Paths (most accurate for user-specific & system installs)

    if os.name == "nt":

        try:

            import winreg

            for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):

                try:

                    with winreg.OpenKey(hive, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe") as key:

                        val, _ = winreg.QueryValueEx(key, "")

                        if val and os.path.isfile(val):

                            return val

                except Exception:

                    pass

        except Exception:

            pass



    # 2. Check standard directory locations across possible drives

    candidates = [

        r"C:\Program Files\Google\Chrome\Application\chrome.exe",

        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",

        r"D:\Program Files\Google\Chrome\Application\chrome.exe",

        r"D:\Program Files (x86)\Google\Chrome\Application\chrome.exe",

        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),

        os.path.expandvars(r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"),

        os.path.expandvars(r"%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe"),

    ]

    for p in candidates:

        if p and os.path.isfile(p):

            return p



    # 3. Check where.exe chrome

    try:

        res = subprocess.run(["where.exe", "chrome"], capture_output=True, text=True, timeout=2, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000))

        if res.returncode == 0:

            first_p = res.stdout.splitlines()[0].strip()

            if os.path.isfile(first_p):

                return first_p

    except Exception:

        pass



    # 4. Fallback to Microsoft Edge if Chrome is not installed

    try:

        edge_paths = [

            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",

            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",

            os.path.expandvars(r"%PROGRAMFILES(X86)%\Microsoft\Edge\Application\msedge.exe"),

            os.path.expandvars(r"%PROGRAMFILES%\Microsoft\Edge\Application\msedge.exe"),

        ]

        for ep in edge_paths:

            if os.path.isfile(ep):

                return ep

    except Exception:

        pass



    return "chrome.exe"





def _find_pid_by_port(port: int) -> int:

    """Find PID listening on a TCP port using netstat."""

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

                        return p

    except Exception:

        pass

    return 0





def _kill_chrome_on_port(port: int = 9461):

    """Cleanly terminate any existing Chrome process on the debug port."""

    try:

        pid = _find_pid_by_port(port)

        if pid > 0:

            if os.name == "nt":

                subprocess.run(

                    ["taskkill", "/F", "/T", "/PID", str(pid)],

                    capture_output=True, timeout=3,

                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)

                )

            time.sleep(0.5)

    except Exception as e:

        logger.warning(f"Error killing Chrome on port {port}: {e}")





def _bring_window_to_front_win32(port: int = 9461):

    """Bring the Chrome window to the foreground on the active user desktop."""

    try:

        import ctypes

        from ctypes import wintypes

        user32 = ctypes.windll.user32



        pid_target = _find_pid_by_port(port)



        HWND_TOPMOST = -1

        HWND_NOTOPMOST = -2

        SWP_NOSIZE = 0x0001

        SWP_NOMOVE = 0x0002

        SWP_SHOWWINDOW = 0x0040



        hwnds = []

        def enum_cb(hwnd, lparam):

            if user32.IsWindow(hwnd):

                pid = wintypes.DWORD()

                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

                if pid_target > 0 and pid.value == pid_target:

                    hwnds.append(hwnd)

                else:

                    buf = ctypes.create_unicode_buffer(512)

                    user32.GetWindowTextW(hwnd, buf, 512)

                    t = buf.value.lower()

                    if ("restore pages" in t):

                        user32.PostMessageW(hwnd, 0x0010, 0, 0)

                    elif ("chrome" in t or "google" in t or "đăng nhập" in t or "sign in" in t):

                        hwnds.append(hwnd)

            return True



        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

        cb_func = WNDENUMPROC(enum_cb)



        # 1. Try EnumWindows

        user32.EnumWindows(cb_func, 0)



        # 2. Try OpenDesktopW with safe non-admin permissions (DESKTOP_READOBJECTS | DESKTOP_ENUMERATE = 0x0041)

        try:

            hDesk = user32.OpenDesktopW("Default", 0, False, 0x0041)

            if hDesk:

                user32.EnumDesktopWindows(hDesk, cb_func, 0)

                user32.CloseDesktop(hDesk)

        except Exception:

            pass



        for hwnd in hwnds:

            user32.ShowWindow(hwnd, 9)  # SW_RESTORE

            user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)

            user32.SetWindowPos(hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)

            user32.SetForegroundWindow(hwnd)

    except Exception as e:

        logger.warning(f"Could not bring window to front: {e}")



    # Also instruct via CDP Page.bringToFront if listening

    if is_port_listening(port):

        try:

            req = urllib.request.Request(f"http://127.0.0.1:{port}/json")

            with urllib.request.urlopen(req, timeout=1.5) as resp:

                tabs = json.loads(resp.read().decode("utf-8"))

            p_tab = next((t for t in tabs if t.get("type") == "page"), None)

            if p_tab and p_tab.get("webSocketDebuggerUrl"):

                from websockets.sync.client import connect

                with connect(p_tab["webSocketDebuggerUrl"], open_timeout=1.5) as ws:

                    ws.send(json.dumps({"id": 1, "method": "Page.bringToFront"}))

                    ws.recv()

        except Exception:

            pass





def _launch_chrome_interactive(chrome_exe: str, profile_dir: Path, port: int, initial_url: str):

    """Launch Chrome directly in the user's interactive desktop.

    

    Guarantees the window opens physically and visibly on the monitor,

    without Session 0 isolation, UAC blocks, or invisible background states.

    """

    profile_dir.mkdir(parents=True, exist_ok=True)

    profile_str = str(profile_dir.resolve()).replace("/", "\\")



    # Clean terminate any stuck Chrome process on this port first

    _kill_chrome_on_port(port)



    # Arguments for Chrome

    args = [

        f"--user-data-dir={profile_str}",

        f"--remote-debugging-port={port}",

        "--remote-debugging-address=127.0.0.1",

        "--no-first-run",

        "--no-default-browser-check",

        "--disable-session-crashed-bubble",

        "--disable-blink-features=AutomationControlled",

        "--window-size=1100,800",

        "--window-position=80,80",

        initial_url

    ]



    # Write launch batch file as manual runner backup (UTF-8)

    bat_file = FLOW_ACCOUNTS_DIR / f"launch_flow_{port}.bat"

    FLOW_ACCOUNTS_DIR.mkdir(parents=True, exist_ok=True)

    cmd_line = (

        "@echo off\r\n"

        "chcp 65001 >nul\r\n"

        f'start "" "{chrome_exe}" '

        f'--user-data-dir="{profile_str}" '

        f'--remote-debugging-port={port} '

        '--remote-debugging-address=127.0.0.1 '

        '--no-first-run '

        '--no-default-browser-check '

        '--disable-session-crashed-bubble '

        '--disable-blink-features=AutomationControlled '

        '--window-size=1100,800 '

        '--window-position=80,80 '

        f'"{initial_url}"\r\n'

    )

    try:

        bat_file.write_text(cmd_line, encoding="utf-8")

    except Exception:

        pass



    # Launch Chrome directly in current interactive session

    # 1. Try standard subprocess.Popen

    launched = False

    try:

        subprocess.Popen(

            [chrome_exe] + args,

            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000),

            close_fds=True

        )

        launched = True

        logger.info(f"Launched interactive Chrome via Popen: {chrome_exe} port={port}")

    except Exception as e:

        logger.warning(f"Popen launch failed: {e}")



    # 2. If Popen failed, try native Windows ShellExecuteW (SW_SHOWNORMAL = 1)

    if not launched:

        try:

            import ctypes

            args_str = " ".join([f'"{a}"' if " " in a else a for a in args])

            ctypes.windll.shell32.ShellExecuteW(None, "open", chrome_exe, args_str, None, 1)

            launched = True

            logger.info(f"Launched interactive Chrome via ShellExecuteW: {chrome_exe}")

        except Exception as e2:

            logger.error(f"ShellExecuteW failed: {e2}")



    # 3. Fallback: run the bat file via os.startfile

    if not launched:

        try:

            subprocess.Popen([chrome_exe] + args, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000), close_fds=True)

        except Exception as e3:

            logger.error(f"os.startfile failed: {e3}")



    time.sleep(1.5)

    _set_chrome_visibility_win32(port=port, show=True)

    _bring_window_to_front_win32(port)





def _set_chrome_visibility_win32(port: int = 9461, show: bool = True):

    """Hide or show Chrome window physically on the Default desktop.

    

    When show=False: calls SW_HIDE (0) so Chrome vanishes completely from Desktop AND Taskbar!

    When show=True: calls SW_RESTORE (9) and SetForegroundWindow so it reappears for login.

    """

    try:

        import ctypes

        from ctypes import wintypes



        user32 = ctypes.windll.user32

        target_pids = set()



        # Check netstat for port

        p_listen = _find_pid_by_port(port)

        if p_listen > 0:

            target_pids.add(p_listen)



        if not target_pids:

            return



        def enum_cb(hwnd, lparam):

            if user32.IsWindow(hwnd):

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



        # Enumerate via EnumWindows

        user32.EnumWindows(cb_func, 0)



        # Enumerate via OpenDesktopW if accessible (0x0041 = DESKTOP_READOBJECTS | DESKTOP_ENUMERATE)

        try:

            h_def = user32.OpenDesktopW("Default", 0, False, 0x0041)

            if h_def:

                user32.EnumDesktopWindows(h_def, cb_func, 0)

                user32.CloseDesktop(h_def)

        except Exception:

            pass



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



    try:

        from websockets.sync.client import connect

    except Exception:

        return ""



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

    """Check tabs and live auth cookies on port to accurately detect Google Flow authentication."""

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



        # Check if Google session cookies rotation is active

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

                    signing_in = False

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



            # 1. Update storyboard_accounts.json with detected email

            try:

                if ACCOUNTS_DB_FILE.is_file() and email:

                    data = json.loads(ACCOUNTS_DB_FILE.read_text(encoding="utf-8"))

                    accounts = data.get("accounts", [])

                    matched = False

                    for acc in accounts:

                        if acc.get("cdp_port") == port or acc.get("id") == _LOGIN_STATE.get("last_account_id"):

                            acc["email"] = email

                            acc["name"] = f"TK ({email.split('@')[0]})"

                            matched = True

                            break

                    if not matched and accounts:

                        accounts[0]["email"] = email

                    data["accounts"] = accounts

                    ACCOUNTS_DB_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

            except Exception as e_acc:

                logger.warning(f"Could not update account DB with email: {e_acc}")



            # 2. Update machine.json if present

            try:

                machine_file = FLOWKIT_ROOT / "state" / "machine.json"

                if machine_file.is_file():

                    m_data = json.loads(machine_file.read_text(encoding="utf-8-sig"))

                    m_data["logged_in"] = True

                    m_data["email"] = email

                    machine_file.write_text(json.dumps(m_data, indent=2), encoding="utf-8")

            except Exception:

                pass



            # 3. If not on web tool URL, navigate to it

            if not status["on_webtool"]:

                try:

                    n_req = urllib.request.Request(

                        f"http://127.0.0.1:{port}/json/new?{urllib.parse.quote(DEFAULT_TARGET_URL)}",

                        method="PUT"

                    )

                    urllib.request.urlopen(n_req, timeout=3.0)

                except Exception as e:

                    logger.warning(f"Could not open web tool tab: {e}")



            # 4. Wait 2 seconds for Web Tool Bridge extension to hook into the tab

            time.sleep(2.0)



            # 5. AUTO-HIDE COMPLETELY: Both from screen and taskbar via SW_HIDE (0)

            set_chrome_window_state(port=port, state="hidden")

            _set_chrome_visibility_win32(port=port, show=False)



            # 6. Final state update

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
    """Open the existing active MCP V2 account for manual sign-in."""
    from studio_flow_accounts import active, open_login
    result = open_login(active()["id"])
    return {**result, "success": bool(result.get("opened")), "provider": "mcp_v2"}





def add_new_account() -> Dict[str, Any]:
    """Create an MCP account only on the user's explicit Add Account action."""
    from studio_flow_accounts import create, open_login
    row = create("Google Flow " + time.strftime("%Y%m%d-%H%M%S"))
    result = open_login(row["id"])
    return {**result, "success": bool(result.get("opened")), "provider": "mcp_v2"}





def _sanitize_accounts_db():

    """Sanitize account paths on secondary machine to ensure portability."""

    if not ACCOUNTS_DB_FILE.is_file():

        return

    try:

        data = json.loads(ACCOUNTS_DB_FILE.read_text(encoding="utf-8"))

        changed = False

        for a in data.get("accounts", []):

            udd = a.get("user_data_dir", "")

            if "thean" in udd.lower() and not os.path.exists(r"C:\Users\thean"):

                new_udd = str(FLOW_ACCOUNTS_DIR / a["id"]).replace("/", "\\")

                a["user_data_dir"] = new_udd

                a["state_dir"] = str(FLOW_ACCOUNTS_DIR / f"{a['id']}_state").replace("/", "\\")

                changed = True

        if changed:

            ACCOUNTS_DB_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

    except Exception:

        pass





def activate_account(account_id: Optional[str] = None, cdp_port: Optional[int] = None) -> bool:
    """Activate a specific account by ID or CDP port, updating both machine.json and storyboard_accounts.json."""
    if not ACCOUNTS_DB_FILE.is_file():
        return False
    try:
        data = json.loads(ACCOUNTS_DB_FILE.read_text(encoding="utf-8"))
        accounts = data.get("accounts", [])
        target = None
        for a in accounts:
            if account_id and a.get("id") == account_id:
                target = a
                break
            if cdp_port and a.get("cdp_port") == cdp_port:
                target = a
                break
        if not target:
            return False

        # 1. Update storyboard_accounts.json active
        data["active"] = target["id"]
        ACCOUNTS_DB_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

        # 2. Update machine.json in FlowKit
        machine_file = FLOWKIT_ROOT / "state" / "machine.json"
        machine_file.parent.mkdir(parents=True, exist_ok=True)
        m_data = {
            "chrome": _chrome_exe_path(),
            "flow_profile": str(target.get("user_data_dir", "")).replace("/", "\\"),
            "debug_port": int(target.get("cdp_port", 9461))
        }
        machine_file.write_text(json.dumps(m_data, indent=2), encoding="utf-8")
        logger.info(f"[FLOW_ACCOUNT] Activated account {target.get('name')} (port {target.get('cdp_port')})")
        return True
    except Exception as exc:
        logger.error(f"[FLOW_ACCOUNT] Failed to activate account: {exc}")
        return False


def rotate_to_next_account(failed_port: Optional[int] = None, failed_id: Optional[str] = None, reason: str = "") -> dict[str, Any]:
    """Rotation Hook: Automatically rotate to the next available live account in storyboard_accounts.json.
    
    Triggered when an account hits quota, rate limits, abnormal activity blocks, or repetitive failures.
    """
    if not ACCOUNTS_DB_FILE.is_file():
        return {}
    try:
        data = json.loads(ACCOUNTS_DB_FILE.read_text(encoding="utf-8"))
        accounts = data.get("accounts", [])
        if not accounts:
            return {}

        # Determine currently failing account port/id
        curr_id = failed_id or data.get("active")
        curr_port = failed_port
        if not curr_port:
            for a in accounts:
                if a.get("id") == curr_id:
                    curr_port = a.get("cdp_port")
                    break

        # Filter candidate live accounts
        live_accounts = []
        for a in accounts:
            port = a.get("cdp_port")
            if port and is_port_listening(port):
                live_accounts.append(a)

        if not live_accounts:
            logger.warning("[FLOWKIT_HOOK_ROTATION] No live Chrome accounts detected to rotate to.")
            return {}

        # If only 1 account is live and it's the failing one, do not force-launch unverified dormant accounts mid-batch
        if len(live_accounts) == 1 and curr_port and live_accounts[0].get("cdp_port") == curr_port:
            logger.warning(f"[FLOWKIT_HOOK_ROTATION] Only 1 account is live (port {curr_port}). Will allow seamless API failover.")
            return {}

        # Find current index in live accounts
        curr_idx = -1
        for idx, a in enumerate(live_accounts):
            if (curr_port and a.get("cdp_port") == curr_port) or (curr_id and a.get("id") == curr_id):
                curr_idx = idx
                break

        # Select next in circular order
        next_idx = (curr_idx + 1) % len(live_accounts)
        next_acc = live_accounts[next_idx]

        # If next is still the failing one, cannot rotate to the same port
        if curr_port and next_acc.get("cdp_port") == curr_port:
            logger.warning(f"[FLOWKIT_HOOK_ROTATION] Cannot rotate: Next account is identical to current failing port {curr_port}.")
            return {}

        ok = activate_account(next_acc["id"])
        if ok:
            print(f"[FLOWKIT_HOOK_ROTATION] 🔄 Đã xoay tài khoản: từ cổng {curr_port} sang {next_acc.get('name')} (cổng {next_acc.get('cdp_port')})! Lý do: {reason}", flush=True)
            return next_acc
        return {}
    except Exception as exc:
        logger.error(f"[FLOWKIT_HOOK_ROTATION] Exception during rotation: {exc}")
        return {}


def get_flow_account_for_scene(scene_number: int, exclude_ids: list[str] | None = None) -> dict[str, Any]:

    """Select the best account for generating a scene using Round-Robin across all ACTUALLY LIVE ready accounts."""

    if not ACCOUNTS_DB_FILE.is_file():

        return {}

    try:

        data = json.loads(ACCOUNTS_DB_FILE.read_text(encoding="utf-8"))

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
    """Read native connection/auth state without starting any background service."""
    from studio_mcp.accounts import (active_account, load_accounts, account_tool_url,
                                     connection_check, flow_auth_status)
    try:
        account = active_account()
        from studio_mcp.transport import _isolated
        _isolated(account)
        store = load_accounts()
        state = connection_check(account["id"])
        auth = flow_auth_status(account) if state.get("connected") else {}
        connected = bool(state.get("connected"))
        authenticated = bool(auth.get("authenticated"))
        ready = connected and authenticated and bool(account_tool_url(account))
        return {
            "provider": "mcp_v2", "flowkit_required": False,
            "ready": ready, "connected": connected, "logged_in": authenticated,
            "email": account.get("email", ""), "emails": [],
            "accounts": store.get("accounts", []), "active_id": account["id"],
            "total_accounts": len(store.get("accounts", [])),
            "ready_accounts": int(ready), "dispatch_mode": "active_account",
            "badge_text": "MCP V2: đã kết nối" if ready else "MCP V2: chưa sẵn sàng",
            "badge_type": "success" if ready else "warning",
            "status_text": ("MCP V2 đã kết nối; trạng thái tạo nội dung cần kiểm tra riêng."
                            if ready else "Mở tài khoản MCP V2 và kiểm tra đăng nhập Google Flow."),
            "watcher_active": False
        }
    except Exception as exc:
        return {"provider": "mcp_v2", "flowkit_required": False, "ready": False,
                "connected": False, "logged_in": False, "ready_accounts": 0,
                "total_accounts": 0, "emails": [], "email": "", "accounts": [],
                "badge_text": "MCP V2: cần kiểm tra", "badge_type": "warning",
                "status_text": str(exc), "watcher_active": False}
