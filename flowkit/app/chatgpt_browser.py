"""Independent ChatGPT Web Browser Launcher & Multi-Account Manager for FlowKit & Storyboard AI.

Guarantees a 100% visible, foreground Chrome window on the active user desktop (WinSta0\\Default)
using Windows Interactive Task Launching (schtasks) + Win32 SetForegroundWindow.
Enforces mutual exclusion with Google Flow (port 9461) and between ChatGPT accounts to prevent
Chrome CDP conflicts and minimize RAM usage.
Supports Multi-Account registry (chatgpt_accounts.json) + automatic account rotation on quota limit.
"""
from __future__ import annotations

import asyncio
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from typing import Dict, Any, List, Optional, Tuple
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = ROOT.parent
PROFILES_ROOT = PROJECT_ROOT / "profiles"
CHATGPT_PROFILE = PROFILES_ROOT / "chatgpt_web"
ACCOUNTS_REGISTRY = PROFILES_ROOT / "chatgpt_accounts.json"
CDP_PORT = 9468
CHATGPT_PORT_MIN = 9468
CHATGPT_PORT_MAX = 9489
TARGET_URL = "https://chatgpt.com"
BAT_LAUNCHER = ROOT / "launch_chatgpt.bat"
TASK_NAME = "Storyboard_Launch_ChatGPT"

user32 = ctypes.windll.user32


def find_chrome_exe() -> str:
    candidates = [
        Path(os.environ.get("PROGRAMFILES", "C:/Program Files")) / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)")) / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/Application/chrome.exe",
    ]
    for c in candidates:
        if c.is_file():
            return str(c)
    return "chrome.exe"


def _is_port_alive(port: int, timeout: float = 1.2) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{int(port)}/json/version", timeout=timeout) as r:
            return r.status == 200
    except Exception:
        return False


def _is_port_in_use(port: int) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.4)
            return s.connect_ex(("127.0.0.1", int(port))) == 0
    except Exception:
        return False


def _read_profile_login_state(profile_dir: Path) -> Dict[str, Any]:
    state_file = profile_dir / "login_state.json"
    if state_file.is_file():
        try:
            data = json.loads(state_file.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return {}


def _write_profile_login_state(profile_dir: Path, patch: Dict[str, Any]) -> None:
    try:
        profile_dir.mkdir(parents=True, exist_ok=True)
        state_file = profile_dir / "login_state.json"
        cur = _read_profile_login_state(profile_dir)
        cur.update(patch)
        cur["updated_at"] = time.time()
        state_file.write_text(json.dumps(cur, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def _save_registry(reg: Dict[str, Any]) -> None:
    PROFILES_ROOT.mkdir(parents=True, exist_ok=True)
    reg["updated_at"] = time.time()
    ACCOUNTS_REGISTRY.write_text(json.dumps(reg, indent=2, ensure_ascii=False), encoding="utf-8")


def _ensure_registry() -> Dict[str, Any]:
    """Loads chatgpt_accounts.json or seeds Account #1 from the legacy chatgpt_web profile."""
    PROFILES_ROOT.mkdir(parents=True, exist_ok=True)
    reg: Optional[Dict[str, Any]] = None
    if ACCOUNTS_REGISTRY.is_file():
        try:
            loaded = json.loads(ACCOUNTS_REGISTRY.read_text(encoding="utf-8"))
            if isinstance(loaded, dict) and isinstance(loaded.get("accounts"), list) and loaded["accounts"]:
                reg = loaded
        except Exception:
            reg = None

    if reg is None:
        legacy_state = _read_profile_login_state(CHATGPT_PROFILE)
        reg = {
            "active_id": "cgpt_1",
            "accounts": [
                {
                    "id": "cgpt_1",
                    "label": "Tài khoản 1",
                    "profile_dir": str(CHATGPT_PROFILE),
                    "port": CDP_PORT,
                    "email": str(legacy_state.get("email") or ""),
                    "logged_in": bool(legacy_state.get("logged_in", False)),
                    "cooldown_until": 0,
                    "last_error": "",
                    "created_at": time.time(),
                }
            ],
        }
        _save_registry(reg)
        return reg

    changed = False
    now = time.time()
    accounts: List[Dict[str, Any]] = []
    for idx, acc in enumerate(reg.get("accounts", []), start=1):
        if not isinstance(acc, dict):
            changed = True
            continue
        acc_id = str(acc.get("id") or f"cgpt_{idx}")
        prof = Path(str(acc.get("profile_dir") or (CHATGPT_PROFILE if idx == 1 else PROFILES_ROOT / f"chatgpt_web_{idx}")))
        port = int(acc.get("port") or (CDP_PORT + idx - 1))
        st = _read_profile_login_state(prof)
        if st.get("logged_in") and not acc.get("logged_in"):
            acc["logged_in"] = True
            changed = True
        if st.get("email") and not acc.get("email"):
            acc["email"] = str(st["email"])
            changed = True
        cd_until = float(acc.get("cooldown_until") or 0)
        if cd_until and cd_until <= now:
            acc["cooldown_until"] = 0
            acc["last_error"] = ""
            changed = True
        acc.setdefault("label", f"Tài khoản {idx}")
        acc["id"] = acc_id
        acc["profile_dir"] = str(prof)
        acc["port"] = port
        acc.setdefault("email", "")
        acc.setdefault("logged_in", False)
        acc.setdefault("cooldown_until", 0)
        acc.setdefault("last_error", "")
        accounts.append(acc)

    if not accounts:
        ACCOUNTS_REGISTRY.unlink(missing_ok=True)
        return _ensure_registry()

    reg["accounts"] = accounts
    ids = {a["id"] for a in accounts}
    if reg.get("active_id") not in ids:
        reg["active_id"] = accounts[0]["id"]
        changed = True
    if changed:
        _save_registry(reg)
    return reg


def list_accounts() -> List[Dict[str, Any]]:
    return list(_ensure_registry().get("accounts", []))


def get_active_account() -> Dict[str, Any]:
    reg = _ensure_registry()
    active_id = reg.get("active_id")
    for acc in reg["accounts"]:
        if acc.get("id") == active_id:
            return dict(acc)
    return dict(reg["accounts"][0])


def get_active_profile() -> Tuple[Path, int, str]:
    acc = get_active_account()
    return Path(acc["profile_dir"]), int(acc["port"]), str(acc["id"])


def update_account_state(account_id: Optional[str] = None, **fields: Any) -> Dict[str, Any]:
    reg = _ensure_registry()
    target_id = account_id or reg.get("active_id")
    updated: Dict[str, Any] = {}
    for acc in reg["accounts"]:
        if acc.get("id") == target_id:
            for k, v in fields.items():
                if v is not None:
                    acc[k] = v
            prof = Path(acc["profile_dir"])
            profile_patch: Dict[str, Any] = {}
            if "logged_in" in fields:
                profile_patch["logged_in"] = bool(fields["logged_in"])
            if fields.get("email"):
                profile_patch["email"] = str(fields["email"])
            if profile_patch:
                _write_profile_login_state(prof, profile_patch)
            updated = dict(acc)
            break
    if updated:
        _save_registry(reg)
    return updated


def get_registered_ports() -> List[int]:
    ports = [int(a["port"]) for a in list_accounts() if a.get("port")]
    if CDP_PORT not in ports:
        ports.insert(0, CDP_PORT)
    return ports


def get_running_port() -> Optional[int]:
    """Returns the port of any currently alive ChatGPT Chrome instance."""
    _, active_port, _ = get_active_profile()
    if _is_port_alive(active_port):
        return active_port
    for p in get_registered_ports():
        if p != active_port and _is_port_alive(p):
            return p
    return None


def is_browser_alive(port: Optional[int] = None) -> bool:
    if port is not None:
        return _is_port_alive(int(port))
    return get_running_port() is not None


def _cdp_restore_window(port: Optional[int] = None, width: int = 1200, height: int = 850, left: int = 120, top: int = 80):
    """Use CDP Browser.setWindowBounds to un-minimize, position and resize Chrome window."""
    if port is None:
        port = get_running_port() or get_active_profile()[1]
    try:
        import websockets

        async def _do():
            with urllib.request.urlopen(f"http://127.0.0.1:{int(port)}/json/version", timeout=1.5) as r:
                v = json.loads(r.read().decode())
            ws_url = v.get("webSocketDebuggerUrl")
            if not ws_url:
                return
            async with websockets.connect(ws_url, close_timeout=2) as ws:
                await ws.send(json.dumps({"id": 1, "method": "Target.getTargets"}))
                res = json.loads(await ws.recv())
                pages = [t for t in res.get("result", {}).get("targetInfos", []) if t.get("type") == "page"]
                if not pages:
                    return
                target_id = pages[0]["targetId"]
                await ws.send(json.dumps({"id": 2, "method": "Browser.getWindowForTarget", "params": {"targetId": target_id}}))
                win_res = json.loads(await ws.recv())
                win_id = win_res.get("result", {}).get("windowId")
                if win_id:
                    await ws.send(json.dumps({
                        "id": 3,
                        "method": "Browser.setWindowBounds",
                        "params": {
                            "windowId": win_id,
                            "bounds": {
                                "left": left,
                                "top": top,
                                "width": width,
                                "height": height,
                                "windowState": "normal"
                            }
                        }
                    }))
                    await ws.recv()

        asyncio.run(_do())
    except Exception:
        pass


def _cdp_minimize_window(port: Optional[int] = None):
    """Use CDP Browser.setWindowBounds to minimize Chrome window to taskbar."""
    if port is None:
        port = get_running_port() or get_active_profile()[1]
    try:
        import websockets

        async def _do():
            with urllib.request.urlopen(f"http://127.0.0.1:{int(port)}/json/version", timeout=1.5) as r:
                v = json.loads(r.read().decode())
            ws_url = v.get("webSocketDebuggerUrl")
            if not ws_url:
                return
            async with websockets.connect(ws_url, close_timeout=2) as ws:
                await ws.send(json.dumps({"id": 1, "method": "Target.getTargets"}))
                res = json.loads(await ws.recv())
                pages = [t for t in res.get("result", {}).get("targetInfos", []) if t.get("type") == "page"]
                if not pages:
                    return
                target_id = pages[0]["targetId"]
                await ws.send(json.dumps({"id": 2, "method": "Browser.getWindowForTarget", "params": {"targetId": target_id}}))
                win_res = json.loads(await ws.recv())
                win_id = win_res.get("result", {}).get("windowId")
                if win_id:
                    await ws.send(json.dumps({
                        "id": 3,
                        "method": "Browser.setWindowBounds",
                        "params": {
                            "windowId": win_id,
                            "bounds": {
                                "windowState": "minimized"
                            }
                        }
                    }))
                    await ws.recv()

        asyncio.run(_do())
    except Exception:
        pass


def _get_port_chrome_pids(port: Optional[int]) -> set[int]:
    """Returns owning PID(s) listening on the target ChatGPT CDP port."""
    if os.name != "nt" or port is None:
        return set()
    try:
        ps = f"Get-NetTCPConnection -LocalPort {int(port)} -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess"
        out = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=3).stdout.strip()
        return {int(p) for p in out.split() if p.isdigit() and int(p) > 0}
    except Exception:
        return set()


def _enum_chatgpt_hwnds(port: Optional[int] = None) -> List[int]:
    """Finds top-level Chrome_WidgetWin_1 window handles owned by this ChatGPT CDP port (fallback: 'chatgpt' title)."""
    if os.name != "nt":
        return []
    target_pids = _get_port_chrome_pids(port) if port is not None else set()
    matched: List[int] = []

    def enum_cb(hwnd, _):
        if user32.IsWindow(hwnd):
            cls = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, cls, 256)
            if cls.value != "Chrome_WidgetWin_1":
                return True
            if target_pids:
                pid = wintypes.DWORD()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                if pid.value in target_pids:
                    matched.append(hwnd)
                    return True
            buf = ctypes.create_unicode_buffer(512)
            user32.GetWindowTextW(hwnd, buf, 512)
            t = buf.value.lower()
            if "chatgpt" in t or (not target_pids and t == "new tab - google chrome"):
                matched.append(hwnd)
        return True

    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    h_def = user32.OpenDesktopW("Default", 0, False, 0x01FF)
    if h_def:
        user32.EnumDesktopWindows(h_def, WNDENUMPROC(enum_cb), 0)
    else:
        user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
    return matched


def _hide_chatgpt_window(port: Optional[int] = None) -> int:
    """Hides the ChatGPT Chrome window offscreen & off taskbar (SW_HIDE) while keeping full DOM rendering alive."""
    if os.name != "nt":
        return 0
    if port is None:
        port = get_running_port() or get_active_profile()[1]
    hidden = 0
    for hwnd in _enum_chatgpt_hwnds(port=port):
        try:
            user32.ShowWindow(hwnd, 0)  # SW_HIDE
            hidden += 1
        except Exception:
            pass
    return hidden


def _force_show_chatgpt_window(port: Optional[int] = None):
    if os.name != "nt":
        return
    if port is None:
        port = get_running_port() or get_active_profile()[1]
    _cdp_restore_window(port=port)
    for hwnd in _enum_chatgpt_hwnds(port=port):
        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        user32.ShowWindow(hwnd, 5)  # SW_SHOW
        user32.SetWindowPos(hwnd, -1, 120, 80, 1200, 850, 0x0040)
        user32.SetWindowPos(hwnd, -2, 120, 80, 1200, 850, 0x0040)
        user32.SetForegroundWindow(hwnd)


def _close_port(port: int) -> bool:
    """Gracefully closes Chrome listening on a specific CDP port."""
    port = int(port)
    if not _is_port_alive(port, timeout=0.8):
        return False
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=1.5) as r:
            v = json.loads(r.read().decode())
        ws_url = v.get("webSocketDebuggerUrl")
        if ws_url:
            from websockets.sync.client import connect
            with connect(ws_url, open_timeout=2) as ws:
                ws.send(json.dumps({"id": 1, "method": "Browser.close"}))
                for _ in range(10):
                    time.sleep(0.25)
                    if not _is_port_alive(port, timeout=0.4):
                        break
                print(f"[CHATGPT_WEB] Đã đóng trình duyệt Chrome ChatGPT Web (Cổng {port}) qua CDP.")
                return True
    except Exception:
        pass

    try:
        ps = f"Get-NetTCPConnection -LocalPort {port} -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess"
        p = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=2).stdout.strip()
        for pid in p.split():
            if pid.isdigit() and int(pid) > 0:
                subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True)
                print(f"[CHATGPT_WEB] Đã dừng tiến trình Chrome ChatGPT (Cổng {port}, PID {pid}).")
                return True
    except Exception:
        pass
    return False


def close_chatgpt_browser(port: Optional[int] = None) -> bool:
    """Closes the specified ChatGPT CDP port or all registered ChatGPT Chrome instances."""
    if port is not None:
        return _close_port(int(port))
    closed_any = False
    seen = set()
    for p in get_registered_ports():
        if p in seen:
            continue
        seen.add(p)
        if _close_port(p):
            closed_any = True
    return closed_any


def open_chatgpt_browser(show: bool = True, account_id: Optional[str] = None) -> Dict[str, Any]:
    if account_id:
        select_chatgpt_account(account_id, close_others=True)
    profile_dir, cdp_port, acc_id = get_active_profile()
    acc = get_active_account()
    profile_dir.mkdir(parents=True, exist_ok=True)
    chrome_exe = find_chrome_exe()

    # 1. Mutual exclusion: Close Google Flow (port 9461) first
    try:
        from engine_orchestrator import close_engine_browser
        close_engine_browser("flow")
        time.sleep(0.4)
    except Exception:
        pass

    # 1.5 Close any OTHER ChatGPT account Chrome on a different port so only 1 runs cleanly
    for p in get_registered_ports():
        if p != cdp_port and _is_port_alive(p, timeout=0.6):
            _close_port(p)
            time.sleep(0.3)

    # 2. If active account browser is already running on cdp_port, show or hide as requested
    if _is_port_alive(cdp_port):
        print(f"[CHATGPT_WEB] Trình duyệt {acc.get('label', acc_id)} đang chạy trên cổng {cdp_port}.")
        if show:
            _force_show_chatgpt_window(port=cdp_port)
            msg = f"Đã đưa cửa sổ {acc.get('label', 'ChatGPT Web')} (Cổng {cdp_port}) lên màn hình."
        else:
            _hide_chatgpt_window(port=cdp_port)
            msg = f"Trình duyệt {acc.get('label', 'ChatGPT Web')} (Cổng {cdp_port}) đang chạy ẩn."
        return {
            "success": True,
            "port": cdp_port,
            "account_id": acc_id,
            "hidden": not show,
            "message": msg,
        }

    # 3. Ensure target port is clean
    try:
        ps = f"Get-NetTCPConnection -LocalPort {cdp_port} -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess"
        p = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=2).stdout.strip()
        for pid in p.split():
            if pid.isdigit() and int(pid) > 0:
                subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True)
                time.sleep(0.3)
    except Exception:
        pass

    # 4. Clean up any crash locks in profile_dir
    for lock_name in ("SingletonLock", "SingletonSocket", "SingletonCookie"):
        lk = profile_dir / lock_name
        if lk.exists():
            try:
                lk.unlink()
            except Exception:
                pass

    # 5. Launch Chrome directly via Popen (reliable across all PCs without schtasks/Admin)
    chrome_args = [
        chrome_exe,
        f"--user-data-dir={profile_dir}",
        f"--remote-debugging-port={cdp_port}",
        "--remote-debugging-address=127.0.0.1",
        "--remote-allow-origins=*",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-session-crashed-bubble",
        "--hide-crash-restore-bubble",
        "--disable-background-timer-throttling",
        "--disable-renderer-backgrounding",
        "--disable-backgrounding-occluded-windows",
        "--window-size=1200,850",
        "--window-position=120,80" if show else "--window-position=-32000,-32000",
        TARGET_URL,
    ]
    launched_direct = False
    try:
        creation_flags = 0x08000000 if (os.name == "nt" and not show) else 0
        subprocess.Popen(
            chrome_args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creation_flags,
        )
        launched_direct = True
    except Exception as exc:
        print(f"[CHATGPT_WEB] Direct Chrome Popen failed ({exc}), trying schtasks fallback...", flush=True)

    if not launched_direct:
        bg_flags = (
            "--disable-background-timer-throttling "
            "--disable-renderer-backgrounding "
            "--disable-backgrounding-occluded-windows "
        )
        if show:
            start_prefix = 'start ""'
            win_flags = '--window-size=1200,850 --window-position=120,80 '
        else:
            start_prefix = 'start "" /min'
            win_flags = '--window-size=1200,850 --window-position=-32000,-32000 '
        bat_content = (
            f'@echo off\n'
            f'{start_prefix} "{chrome_exe}" '
            f'--user-data-dir="{profile_dir}" '
            f'--remote-debugging-port={cdp_port} '
            f'--remote-debugging-address=127.0.0.1 '
            f'--no-first-run '
            f'--no-default-browser-check '
            f'--disable-session-crashed-bubble '
            f'--hide-crash-restore-bubble '
            f'{bg_flags}'
            f'{win_flags}'
            f'"{TARGET_URL}"\n'
        )
        BAT_LAUNCHER.parent.mkdir(parents=True, exist_ok=True)
        BAT_LAUNCHER.write_text(bat_content, encoding="utf-8")

        cmd_create = f'schtasks /create /tn "{TASK_NAME}" /tr "cmd.exe /c \\"{BAT_LAUNCHER}\\"" /sc ONCE /st 23:59 /f'
        subprocess.run(cmd_create, shell=True, capture_output=True)
        subprocess.run(f'schtasks /run /tn "{TASK_NAME}"', shell=True, capture_output=True)

    # 6. Wait for Chrome to listen and force foreground (or hide completely if show=False)
    for _ in range(25):
        time.sleep(0.5)
        if _is_port_alive(cdp_port):
            print(f"[CHATGPT_WEB] {acc.get('label', acc_id)} sẵn sàng trên cổng CDP {cdp_port}!")
            if show:
                _force_show_chatgpt_window(port=cdp_port)
            else:
                _hide_chatgpt_window(port=cdp_port)
                time.sleep(0.4)
                _hide_chatgpt_window(port=cdp_port)
            return {
                "success": True,
                "port": cdp_port,
                "account_id": acc_id,
                "hidden": not show,
                "message": (
                    f"Đã mở {acc.get('label', 'ChatGPT Web')} (chạy ẩn) trên cổng {cdp_port}!"
                    if not show
                    else f"Đã mở {acc.get('label', 'ChatGPT Web')} thành công trên cổng {cdp_port}!"
                ),
            }

    return {
        "success": True,
        "port": cdp_port,
        "account_id": acc_id,
        "message": f"Đã gửi lệnh mở {acc.get('label', 'ChatGPT Web')} (Cổng {cdp_port}).",
    }


def add_chatgpt_account(show: bool = True) -> Dict[str, Any]:
    """Creates a brand-new isolated Chrome profile + CDP port for another ChatGPT account and opens Chrome."""
    reg = _ensure_registry()
    accounts = reg["accounts"]
    used_ports = {int(a.get("port") or 0) for a in accounts}
    used_ids = {str(a.get("id") or "") for a in accounts}

    next_idx = len(accounts) + 1
    while f"cgpt_{next_idx}" in used_ids:
        next_idx += 1
    new_id = f"cgpt_{next_idx}"

    new_port = None
    for candidate in range(CDP_PORT + 1, CHATGPT_PORT_MAX + 1):
        if candidate not in used_ports and not _is_port_in_use(candidate):
            new_port = candidate
            break
    if new_port is None:
        return {"success": False, "error": "PORT_POOL_EXHAUSTED", "message": "Đã đạt giới hạn cổng trình duyệt ChatGPT."}

    new_profile = PROFILES_ROOT / f"chatgpt_web_{next_idx}"
    new_profile.mkdir(parents=True, exist_ok=True)
    new_acc = {
        "id": new_id,
        "label": f"Tài khoản {next_idx}",
        "profile_dir": str(new_profile),
        "port": new_port,
        "email": "",
        "logged_in": False,
        "cooldown_until": 0,
        "last_error": "",
        "created_at": time.time(),
    }
    accounts.append(new_acc)
    reg["active_id"] = new_id
    _save_registry(reg)
    _write_profile_login_state(new_profile, {"logged_in": False})

    res = open_chatgpt_browser(show=show)
    return {
        "success": bool(res.get("success", True)),
        "account": new_acc,
        "port": new_port,
        "account_id": new_id,
        "total_accounts": len(accounts),
        "message": f"Đã tạo hồ sơ {new_acc['label']} (Cổng {new_port}). Hãy đăng nhập tài khoản ChatGPT mới trên Chrome!",
    }


def select_chatgpt_account(account_id: str, close_others: bool = True) -> Dict[str, Any]:
    reg = _ensure_registry()
    target = next((a for a in reg["accounts"] if a.get("id") == account_id), None)
    if not target:
        return {"success": False, "error": f"Account {account_id} not found"}
    old_id = reg.get("active_id")
    reg["active_id"] = account_id
    _save_registry(reg)
    if close_others and old_id != account_id:
        for a in reg["accounts"]:
            if a.get("id") != account_id:
                p = int(a.get("port") or 0)
                if p and _is_port_alive(p, timeout=0.6):
                    _close_port(p)
    return {"success": True, "account": target}


def delete_chatgpt_account(account_id: Optional[str] = None) -> Dict[str, Any]:
    """Deletes the selected ChatGPT account & cleans its isolated profile directory."""
    import shutil
    reg = _ensure_registry()
    accounts = list(reg.get("accounts") or [])
    target_id = str(account_id or "").strip() or str(reg.get("active_id") or "")
    target = next((a for a in accounts if a.get("id") == target_id), None)
    if not target:
        return {"success": False, "error": f"Không tìm thấy tài khoản ChatGPT ({target_id})."}

    port = int(target.get("port") or 0)
    if port and _is_port_alive(port, timeout=0.8):
        _close_port(port)
        time.sleep(0.4)

    # Also ensure no Chrome process still holds target's profile_dir
    prof_str = str(target.get("profile_dir") or "")
    if os.name == "nt" and prof_str:
        try:
            ps = (
                "Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | "
                "Where-Object { $_.CommandLine -and $_.CommandLine.Contains($env:CGPT_DEL_PROF) -and $_.CommandLine -notmatch '--type=' } | "
                "Select-Object -ExpandProperty ProcessId"
            )
            env = dict(os.environ)
            env["CGPT_DEL_PROF"] = prof_str
            out = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=4, env=env).stdout.strip()
            for pid in out.split():
                if pid.isdigit() and int(pid) > 0:
                    subprocess.run(["taskkill", "/F", "/T", "/PID", pid], capture_output=True)
            if out:
                time.sleep(0.4)
        except Exception:
            pass

    if prof_str:
        try:
            prof_p = Path(prof_str).resolve()
            root_p = PROFILES_ROOT.resolve()
            if root_p in prof_p.parents and prof_p.name.lower().startswith("chatgpt_web") and prof_p.exists():
                for _ in range(3):
                    try:
                        shutil.rmtree(prof_p, ignore_errors=False)
                        break
                    except Exception:
                        time.sleep(0.25)
                shutil.rmtree(prof_p, ignore_errors=True)
        except Exception:
            pass

    remaining = [a for a in accounts if a.get("id") != target_id]
    reset_clean = False
    if not remaining:
        fresh_dir = PROFILES_ROOT / "chatgpt_web"
        fresh_acc = {
            "id": "cgpt_1",
            "label": "Tài khoản 1",
            "profile_dir": str(fresh_dir),
            "port": CDP_PORT,
            "email": "",
            "logged_in": False,
            "cooldown_until": 0,
            "last_error": "",
            "created_at": time.time(),
        }
        reg["accounts"] = [fresh_acc]
        reg["active_id"] = "cgpt_1"
        _save_registry(reg)
        _write_profile_login_state(fresh_dir, {"logged_in": False, "email": ""})
        reset_clean = True
    else:
        reg["accounts"] = remaining
        now_ts = time.time()
        next_acc = next(
            (a for a in remaining if a.get("logged_in") and float(a.get("cooldown_until") or 0) <= now_ts),
            next((a for a in remaining if a.get("logged_in")), remaining[0]),
        )
        reg["active_id"] = next_acc["id"]
        _save_registry(reg)

    active_now = get_active_account()
    msg = (
        "Đã xóa tài khoản ChatGPT cũ. Bấm '🌐 Đăng Nhập' để đăng nhập tài khoản khác!"
        if reset_clean
        else f"Đã xóa {target.get('label') or target_id}. Đang chuyển sang {active_now.get('label') or active_now.get('id')}."
    )
    return {
        "success": True,
        "deleted": target_id,
        "reset_clean": reset_clean,
        "active_id": active_now.get("id"),
        "active_label": active_now.get("label"),
        "total_accounts": len(reg["accounts"]),
        "message": msg,
    }


def rotate_chatgpt_account(reason: str = "", cooldown_seconds: int = 21600) -> Optional[Dict[str, Any]]:
    """Marks active ChatGPT account as rate-limited/invalid and switches to the next ready account."""
    reg = _ensure_registry()
    now = time.time()
    cur_id = reg.get("active_id")
    accounts = reg["accounts"]
    if len(accounts) <= 1:
        return None

    cur_idx = 0
    for i, a in enumerate(accounts):
        if a.get("id") == cur_id:
            cur_idx = i
            if cooldown_seconds > 0:
                a["cooldown_until"] = now + cooldown_seconds
            if reason:
                a["last_error"] = str(reason)[:240]
            break

    # Close current browser before switching
    close_chatgpt_browser()

    ordered = accounts[cur_idx + 1:] + accounts[:cur_idx]
    candidate = None
    for a in ordered:
        if float(a.get("cooldown_until") or 0) <= now and a.get("logged_in"):
            candidate = a
            break
    if candidate is None:
        # Second pass: accept any non-cooled-down account in case login_state.json wasn't cached yet
        for a in ordered:
            if float(a.get("cooldown_until") or 0) <= now:
                candidate = a
                break

    if candidate is None:
        _save_registry(reg)
        return None

    reg["active_id"] = candidate["id"]
    _save_registry(reg)
    print(
        f"[CHATGPT_WEB] ♻️ Tự động xoay từ {cur_id} sang {candidate.get('label')} (Cổng {candidate.get('port')}) | Lý do: {reason}",
        flush=True,
    )
    return dict(candidate)


def lock_chatgpt_browser():
    port = get_running_port() or get_active_profile()[1]
    _cdp_minimize_window(port)
    _hide_chatgpt_window(port)
    print(f"[CHATGPT_WEB] Đã ẩn cửa sổ ChatGPT Web (Cổng {port}) chạy ngầm an toàn.")


if __name__ == "__main__":
    if "--close" in sys.argv:
        close_chatgpt_browser()
    elif "--lock" in sys.argv:
        lock_chatgpt_browser()
    elif "--add" in sys.argv:
        print(json.dumps(add_chatgpt_account(show=True), indent=2, ensure_ascii=False))
    else:
        open_chatgpt_browser(show="--hide" not in sys.argv)
