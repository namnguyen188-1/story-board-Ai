"""Storyboard Director APP accounts: isolated Chrome sessions, safe selection.

A profile is a local browser identity, not a Google credential. This module
never copies/deletes cookies or changes the legacy V-Studio Chrome 149.
"""
from __future__ import annotations

import json
import os
import re
import socket
import subprocess
import time
import uuid
from pathlib import Path
try:
    import silent_subprocess
except Exception:
    pass
from urllib.request import urlopen
from urllib.parse import urlsplit,parse_qs

from .paths import app_root

def bundled_shared_tool_url():
    """Non-secret, vendor-provided Flow share entrypoint shipped with the app."""
    data=json.loads((Path(__file__).with_name("flow_tool.json")).read_text(encoding="utf-8"))
    value=str(data.get("share_url") or "")
    u=urlsplit(value)
    if (data.get("schema")!=1 or u.scheme!="https" or u.netloc!="flow.google.com"
            or u.query or u.fragment or
            not re.fullmatch(r"/shared/tool/[0-9a-fA-F-]{36}",u.path) or
            u.path.rsplit("/",1)[1].casefold()!=str(data.get("tool_id") or "").casefold()):
        raise AccountError("STORYBOARD_BUILTIN_FLOW_IDENTITY_INVALID")
    return value

def _matches_bundled_tool(url):
    try:
        return bool(_canonical_storyboard_tool_url(url) and
                    urlsplit(url).path.rsplit("/",1)[-1].casefold() ==
                    bundled_shared_tool_url().rsplit("/",1)[-1].casefold())
    except (ValueError,TypeError,OSError,AccountError):
        return False


APP_URL = ''  # Operator configures their own Google Flow APP link.\n\n
def _canonical_storyboard_tool_url(value):
    """Only accept Google Flow APP routes, never a general site/login URL."""
    try:
        u=urlsplit(str(value or ""))
        if u.scheme!="https" or u.netloc!="flow.google.com":
            return ""
        if not re.fullmatch(
            r"/(?:u/\d+/)?project/[0-9a-fA-F-]{36}/tool/[0-9a-fA-F-]{36}",
            u.path,
        ):
            return ""
        # The user-facing Google Flow URL often omits mode=APP, although its
        # embedded Flow app is already active. Both route spellings are valid.
        query=parse_qs(u.query,keep_blank_values=True)
        if query not in ({}, {"mode":["APP"]}):
            return ""
        return "https://flow.google.com"+u.path+("?mode=APP" if query else "")
    except (ValueError,TypeError):
        return ""


def account_tool_url(account):
    """Selected project per account, never the publisher's fixed project ID."""
    from .projects import url_for
    chosen=url_for(account)
    if chosen:
        return chosen
    path=Path(account["state_dir"])/"studio_private_tool_url.json"
    try:
        row=json.loads(path.read_text(encoding="utf-8"))
        stored=_canonical_storyboard_tool_url(row.get("url"))
        if stored and _matches_bundled_tool(stored):
            return stored
    except (OSError,ValueError,KeyError,TypeError,AttributeError):
        pass
    try:
        discovered=_resolve_shared_tool_url(account,bundled_shared_tool_url())
    except (AccountError,OSError,ValueError):
        return ""
    _atomic_store(path,{"url":discovered})
    return discovered


DEFAULT_ID = "default"
MAX_ACCOUNTS = 12
ENV_NAMES = (
    "FLOW_MCP_USER_DATA_DIR", "FLOW_MCP_PROFILE_DIRECTORY",
    "FLOW_MCP_CDP_PORT", "FLOW_MCP_STATE_DIR",
)


class AccountError(RuntimeError):
    pass


def registry_path(root=None):
    return Path(root or app_root()) / "runtime" / "storyboard_accounts.json"


def _default_account():
    home = Path.home()
    return {
        "id": DEFAULT_ID,
        "name": "Storyboard riêng (đăng nhập mới)",
        "user_data_dir": str(home / ".storyboard-studio-private-chrome-default"),
        "profile_directory": "Default",
        "cdp_port": 9550,
        "state_dir": str(home / ".storyboard-studio-private-state-default"),
    }


def _validate(row):
    if not isinstance(row, dict):
        raise AccountError("STORYBOARD_ACCOUNT_RECORD_INVALID")
    identifier = str(row.get("id") or "")
    if not re.fullmatch(r"(?:default|account_[0-9a-f]{12})", identifier):
        raise AccountError("STORYBOARD_ACCOUNT_ID_INVALID")
    name = str(row.get("name") or "").strip()
    if not name or len(name) > 65 or any(ord(c)<32 for c in name):
        raise AccountError("STORYBOARD_ACCOUNT_NAME_INVALID")
    directory = Path(str(row.get("user_data_dir") or ""))
    state_dir = Path(str(row.get("state_dir") or ""))
    if not directory.is_absolute() or not state_dir.is_absolute():
        raise AccountError("STORYBOARD_ACCOUNT_PATH_INVALID")
    if row.get("profile_directory") != "Default":
        raise AccountError("STORYBOARD_ACCOUNT_PROFILE_UNSUPPORTED")
    port = row.get("cdp_port")
    if type(port) is not int or not (1024 <= port <= 65535):
        raise AccountError("STORYBOARD_ACCOUNT_PORT_INVALID")
    return dict(row)


def _fresh():
    row = _default_account()
    return {"version": 1, "active": DEFAULT_ID, "accounts": [row]}


def _validate_registry(store):
    if not isinstance(store, dict) or store.get("version") != 1:
        raise AccountError("STORYBOARD_ACCOUNT_REGISTRY_INVALID")
    rows = [_validate(x) for x in store.get("accounts", [])]
    ids = [x["id"] for x in rows]
    paths = [str(Path(x["user_data_dir"]).resolve()).casefold() for x in rows]
    ports = [x["cdp_port"] for x in rows]
    states = [str(Path(x["state_dir"]).resolve()).casefold() for x in rows]
    if (not rows or len(rows)>MAX_ACCOUNTS
            or store.get("active") not in ids
            or len(set(ids)) != len(ids)
            or len(set(paths)) != len(paths)
            or len(set(ports)) != len(ports)
            or len(set(states)) != len(states)):
        raise AccountError("STORYBOARD_ACCOUNT_REGISTRY_CONFLICT")
    if DEFAULT_ID in ids:
        default = next(row for row in rows if row["id"]==DEFAULT_ID)
        baseline = _default_account()
        if any(str(default.get(k)) != str(baseline[k])
               for k in ("user_data_dir", "cdp_port", "state_dir", "profile_directory")):
            raise AccountError("STORYBOARD_DEFAULT_PROFILE_MUTATION_DENIED")
    return {"version":1, "active":store["active"], "accounts":rows}


def _atomic_store(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name+"."+uuid.uuid4().hex+".tmp")
    try:
        temp.write_text(json.dumps(payload,indent=2,ensure_ascii=False),encoding="utf-8")
        os.replace(temp,path)
    finally:
        temp.unlink(missing_ok=True)


def load_accounts(root=None):
    path = registry_path(root)
    if not path.exists():
        return _fresh()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise AccountError("STORYBOARD_ACCOUNT_REGISTRY_CORRUPT") from exc
    return _validate_registry(data)


def active_account(root=None):
    store = load_accounts(root)
    return next(dict(a) for a in store["accounts"] if a["id"]==store["active"])


def find_account(account_id, root=None):
    return next((dict(a) for a in load_accounts(root)["accounts"]
                 if a["id"] == str(account_id)), None)


def any_running_production(root=None):
    """Check ONLY Storyboard's own running job, not V2."""
    import sys
    ws = sys.modules.get("web_server")
    if ws is not None and hasattr(ws, "job_status"):
        try:
            return bool(ws.job_status.get("running"))
        except Exception:
            pass
    import urllib.request
    try:
        with urllib.request.urlopen("http://127.0.0.1:8765/api/status",timeout=2) as response:
            return bool(json.load(response).get("running"))
    except OSError:
        # No reachable Studio status => no production is running.
        return False


def _require_idle(root=None):
    if any_running_production(root):
        raise AccountError("STORYBOARD_PRIVATE_ACCOUNT_BUSY_OR_OFFLINE")


def add_account(name, root=None):
    root = Path(root or app_root())
    name = str(name or "").strip()
    if not name or len(name)>65 or any(ord(c)<32 for c in name):
        raise AccountError("STORYBOARD_ACCOUNT_NAME_INVALID")
    store = load_accounts(root)
    if len(store["accounts"]) >= MAX_ACCOUNTS:
        raise AccountError("STORYBOARD_ACCOUNT_LIMIT")
    ident = "account_"+uuid.uuid4().hex[:12]
    used_ports = {a["cdp_port"] for a in store["accounts"]}
    used_ports.add(9231) # Legacy V-Studio, NEVER share its CDP port.
    def port_unused(port_number):
        try:
            with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as sock:
                sock.settimeout(.12)
                return sock.connect_ex(("127.0.0.1",port_number)) != 0
        except OSError:
            return False
    port = next((p for p in range(9551, 9630)
                 if p not in used_ports and port_unused(p)), None)
    if port is None:
        raise AccountError("STORYBOARD_ACCOUNT_NO_FREE_CONFIGURED_PORT")
    directory = Path.home()/".google-flow-chrome-accounts"/ident
    state = Path.home()/".google-flow-mcp-accounts"/ident
    item = _validate({
        "id":ident,"name":name,"user_data_dir":str(directory),
        "profile_directory":"Default","cdp_port":port,"state_dir":str(state)})
    store["accounts"].append(item)
    _atomic_store(registry_path(root), _validate_registry(store))
    # Creating a profile is safe while another worker runs, but NOT selecting it.
    return item


def select_account(account_id, root=None):
    root = Path(root or app_root())
    store = load_accounts(root)
    if account_id == store["active"]:
        acc = find_account(account_id,root)
    elif not any(a["id"] == account_id for a in store["accounts"]):
        raise AccountError("STORYBOARD_ACCOUNT_NOT_FOUND")
    else:
        _require_idle(root)
        store["active"] = account_id
        _atomic_store(registry_path(root), _validate_registry(store))
        acc = find_account(account_id,root)
    try:
        if acc:
            m_path = Path("D:/FLOWKIT/state/machine.json")
            if m_path.parent.exists():
                chrome_exe = str(_chrome_path())
                m_path.write_text(json.dumps({
                    "chrome": chrome_exe,
                    "flow_profile": acc["user_data_dir"],
                    "debug_port": acc["cdp_port"]
                }, indent=2), encoding="utf-8")
    except Exception:
        pass
    return acc


def account_env(account=None, root=None):
    row = account or active_account(root)
    return {
        "FLOW_MCP_USER_DATA_DIR":row["user_data_dir"],
        "FLOW_MCP_PROFILE_DIRECTORY":row["profile_directory"],
        "FLOW_MCP_CDP_PORT":str(row["cdp_port"]),
        "FLOW_MCP_STATE_DIR":row["state_dir"],
    }


def freeze_worker_account(root=None, account_id=None):
    """Freeze at worker launch; inherited environment survives all Step 6-8 RPCs."""
    selection = find_account(account_id,root) if account_id else active_account(root)
    if selection is None:
        raise AccountError("STORYBOARD_FROZEN_ACCOUNT_NOT_FOUND")
    for key,value in account_env(selection).items():
        os.environ[key] = value
    os.environ["V2_STORYBOARD_ACCOUNT_ID"] = selection["id"]
    return selection


def _chrome_path():
    value = os.environ.get("FLOW_MCP_CHROME_PATH")
    if value and Path(value).is_file():
        return Path(value)
    
    prog_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    prog_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    
    candidates = [
        # Google Chrome
        Path(prog_files) / "Google" / "Chrome" / "Application" / "chrome.exe",
        Path(prog_files_x86) / "Google" / "Chrome" / "Application" / "chrome.exe",
        Path(local_app_data) / "Google" / "Chrome" / "Application" / "chrome.exe",
        # Microsoft Edge (Installed on 100% of Windows 10/11 machines)
        Path(prog_files_x86) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
        Path(prog_files) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
        Path(local_app_data) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
    ]
    for c in candidates:
        if c.is_file():
            return c
    return candidates[0]


def browser_probe(account):
    """Read-only CDP connection test; does not claim authenticated Google login."""
    account = _validate(account)
    port = account["cdp_port"]
    try:
        with urlopen("http://127.0.0.1:%d/json/version" % port,timeout=8.0) as r:
            if r.status != 200:
                return {"connected":False,"reason":"CDP_HTTP_ERROR","logged_in":None}
        with urlopen("http://127.0.0.1:%d/json/list" % port,timeout=8.0) as r:
            pages=json.loads(r.read(128000).decode("utf-8"))
        urls=[str(row.get("url") or "") for row in pages if isinstance(row,dict)]
        return {"connected":True,
                "tool_open":any(_canonical_storyboard_tool_url(u) for u in urls),
                "needs_signin":any("accounts.google.com" in u for u in urls),
                "logged_in":None, "reason":"BROWSER_CDP_READY_NOT_AUTH_PROOF"}
    except Exception:
        return {"connected":False, "reason":"BROWSER_NOT_RUNNING", "logged_in":None}


# Auth is distinct from CDP process connectivity. A browser may still
# answer /json/version after Google signs out. Cache short-lived read-only
# Google Flow home checks to avoid spawning Node on every HTTP poll.
_AUTH_CACHE = {}
_AUTH_LOCK = __import__("threading").Lock()
_FAIL_COUNTS = {}
_CONSECUTIVE_FAIL_THRESHOLD = 3


def flow_auth_status(account, *, force=False):
    """Prove Google Flow sign-in without accessing cookies or user identity.

    Fail closed: no "authenticated=True" unless a fresh Flow home displays
    its authenticated new-project control. Read-only Chrome CDP, zero credit.
    Includes a 3-consecutive-failure buffer to eliminate false alarms and flapping.
    """
    account=_validate(account)
    now=time.monotonic()
    key=(account["id"],account["cdp_port"])
    with _AUTH_LOCK:
        prior=_AUTH_CACHE.get(key)
        cache_ttl = 25.0 if (prior and prior[1].get("authenticated")) else 8.0
        if prior and not force and now-prior[0]<cache_ttl:
            return dict(prior[1])
    if not browser_probe(account).get("connected"):
        result={"authenticated":False,"auth_state":"CHROME_DISCONNECTED"}
    elif not _pid_browser_for_account(account):
        result={"authenticated":False,"auth_state":"CDP_PROFILE_MISMATCH"}
    else:
        from .transport import NODE
        executable=NODE/("node.exe" if os.name=="nt" else "node")
        script=NODE/"read-only-google-flow-auth.mjs"
        result={"authenticated":False,"auth_state":"CHECK_FAILED"}
        if executable.is_file() and script.is_file():
            try:
                done=subprocess.run(
                    [str(executable),str(script)],
                    input=json.dumps({"port":account["cdp_port"]}),
                    cwd=str(NODE),encoding="utf-8",errors="replace",
                    text=True,capture_output=True,timeout=24,
                    creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
                payload=json.loads(done.stdout.strip().splitlines()[-1])
                if done.returncode==0 and isinstance(payload,dict):
                    result={"authenticated":payload.get("authenticated") is True,
                            "auth_state":str(payload.get("auth_state") or "UNKNOWN")[:45]}
            except (OSError,ValueError,IndexError,subprocess.TimeoutExpired):
                result={"authenticated":False,"auth_state":"PROBE_TIMEOUT"}
    with _AUTH_LOCK:
        prior=_AUTH_CACHE.get(key)
        was_authenticated = bool(prior and prior[1].get("authenticated"))
        if result.get("authenticated"):
            _FAIL_COUNTS[key] = 0
            _AUTH_CACHE[key] = (time.monotonic(), dict(result))
            return dict(result)
        else:
            is_explicit_logout = (result.get("auth_state") == "LOGIN_REQUIRED")
            cur_fails = _FAIL_COUNTS.get(key, 0) + 1
            _FAIL_COUNTS[key] = cur_fails

            # 3-attempt buffer: if previously authenticated and hasn't failed 3 consecutive times,
            # and is not an explicit Google logout page, retain authenticated state (transient debounce).
            if was_authenticated and cur_fails < _CONSECUTIVE_FAIL_THRESHOLD and not is_explicit_logout:
                suppressed = dict(prior[1])
                suppressed["transient_retry"] = f"{cur_fails}/{_CONSECUTIVE_FAIL_THRESHOLD}"
                _AUTH_CACHE[key] = (time.monotonic() - 17.0, suppressed)
                return dict(suppressed)

            _AUTH_CACHE[key] = (time.monotonic(), dict(result))
            return dict(result)


_PID_CACHE = {}
_PID_LOCK = __import__("threading").Lock()

def _is_pid_alive(pid: int) -> bool:
    if not pid or pid <= 0:
        return False
    if os.name != "nt":
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False
    import ctypes
    from ctypes import wintypes
    try:
        handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
        if not handle:
            return False
        code = wintypes.DWORD()
        ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
        ctypes.windll.kernel32.CloseHandle(handle)
        return code.value == 259
    except Exception:
        return False

def _find_pid_by_cdp_port(port: int) -> int:
    if not port or port <= 0:
        return 0
    try:
        out = subprocess.run(
            ["netstat", "-ano", "-p", "tcp"],
            capture_output=True, text=True, timeout=3,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
        ).stdout
        for line in out.splitlines():
            if f":{port}" in line and "LISTENING" in line:
                parts = line.strip().split()
                if len(parts) >= 5 and parts[-1].isdigit():
                    pid = int(parts[-1])
                    if pid > 0 and _is_pid_alive(pid):
                        return pid
    except Exception:
        pass
    return 0

def _pid_browser_for_account(account):
    """Find only Chrome/Edge main process in this profile with microsecond in-memory caching."""
    if not isinstance(account, dict):
        return 0
    if os.name != "nt":
        return 0
    cache_key = account.get("id") or account.get("user_data_dir")
    now = time.monotonic()
    with _PID_LOCK:
        cached = _PID_CACHE.get(cache_key)
        if cached:
            cached_pid, cached_at = cached
            if cached_pid > 0 and _is_pid_alive(cached_pid):
                return cached_pid
            if cached_pid == 0 and (now - cached_at) < 2.0:
                return 0

    # Fast 30ms netstat lookup via CDP port
    port = account.get("cdp_port")
    if port:
        net_pid = _find_pid_by_cdp_port(port)
        if net_pid:
            with _PID_LOCK:
                _PID_CACHE[cache_key] = (net_pid, now)
            return net_pid

    user_data_dir = account.get("user_data_dir")
    if not user_data_dir or not Path(user_data_dir).exists():
        with _PID_LOCK:
            _PID_CACHE[cache_key] = (0, now)
        return 0

    try:
        ps = ("Get-CimInstance Win32_Process | "
              "Where-Object { ($_.Name -eq 'chrome.exe' -or $_.Name -eq 'msedge.exe') -and $_.CommandLine -notmatch '--type=' } | "
              "Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress")
        out = subprocess.run(
            ["powershell","-NoProfile","-Command",ps],
            capture_output=True,text=True,timeout=8,check=True,
            creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0),
        ).stdout.strip()
        values = json.loads(out) if out else []
        if isinstance(values,dict):
            values=[values]
        path = user_data_dir.casefold()
        for item in values:
            line=str(item.get("CommandLine") or "").casefold().replace('"','').replace("\'","")
            if ("--user-data-dir="+path) in line and "--type=" not in line:
                found_pid = int(item["ProcessId"])
                with _PID_LOCK:
                    _PID_CACHE[cache_key] = (found_pid, now)
                return found_pid
    except Exception:
        pass
    with _PID_LOCK:
        _PID_CACHE[cache_key] = (0, now)
    return 0


def _show_window(pid):
    if os.name != "nt" or not pid:
        return False
    import ctypes
    from ctypes import wintypes
    u=ctypes.windll.user32
    func=ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HWND,wintypes.LPARAM)
    found=[]
    def callback(hwnd, _):
        own=wintypes.DWORD()
        u.GetWindowThreadProcessId(hwnd,ctypes.byref(own))
        if own.value==pid:
            name=ctypes.create_unicode_buffer(96)
            u.GetClassNameW(hwnd,name,96)
            if name.value=="Chrome_WidgetWin_1":
                found.append(hwnd)
        return True
    u.EnumWindows(func(callback),0)
    if not found:
        return False
    u.ShowWindow(found[0],9)
    u.SetForegroundWindow(found[0])
    return True


def mark_manual_login(account_id, root=None):
    path = Path(root or app_root())/"runtime"/"storyboard_pet"/"manual_login.json"
    _atomic_store(path, {"account":str(account_id),"at":time.time()})


def manual_login_active(root=None, account_id=None):
    path = Path(root or app_root())/"runtime"/"storyboard_pet"/"manual_login.json"
    try:
        item=json.loads(path.read_text(encoding="utf-8"))
        same_account=(account_id is None or str(item.get("account"))==str(account_id))
        return same_account and time.time()-float(item.get("at") or 0)<900
    except Exception:
        return False


def clear_manual_login(root=None):
    path = Path(root or app_root())/"runtime"/"storyboard_pet"/"manual_login.json"
    path.unlink(missing_ok=True)


def open_account_login(account_id, root=None):
    """Operator-only manual login; NEVER open a URL in the old V-Studio profile."""
    row=find_account(account_id,root)
    if row is None:
        raise AccountError("STORYBOARD_ACCOUNT_NOT_FOUND")
    # Do not introduce an unexpected Chrome during production.
    _require_idle(root)
    chrome=_chrome_path()
    if not chrome.is_file():
        raise AccountError("STORYBOARD_CHROME_NOT_INSTALLED")
    if browser_probe(row)["connected"]:
        pid=_pid_browser_for_account(row)
        if not pid:
            raise AccountError("STORYBOARD_CDP_PORT_OCCUPIED_BY_UNKNOWN_BROWSER")
        _show_window(pid)
        mark_manual_login(row["id"],root)
        try:
            u_flag = Path("D:/FLOWKIT/state/flow_window/unlock.flag")
            u_flag.parent.mkdir(parents=True, exist_ok=True)
            u_flag.write_text("unlock", encoding="ascii")
        except Exception:
            pass
        return {"opened":True,"reused":True,"account":row["id"]}
    if _pid_browser_for_account(row):
        raise AccountError("STORYBOARD_BROWSER_STARTED_BUT_CDP_UNAVAILABLE")
    # Launch Chrome/Edge as interactive desktop GUI (never hide GUI window)
    flags = 0
    target_url = account_tool_url(row) or bundled_shared_tool_url() or "https://flow.google.com"
    subprocess.Popen([
        str(chrome),f'--remote-debugging-port={row["cdp_port"]}',
        f'--user-data-dir={row["user_data_dir"]}',
        "--profile-directory=Default","--no-first-run",
        "--no-default-browser-check",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
        "--disable-features=CalculateNativeWinOcclusion",
        "--window-size=900,760",
        "--window-position=80,70","--app="+target_url,
    ],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
       creationflags=flags)
    # Authentication is manual, never collect passwords or cookies.
    mark_manual_login(row["id"],root)
    return {"opened":True,"reused":False,"account":row["id"]}


def connection_check(account_id, root=None):
    """No paid generation: local browser visibility only."""
    row=find_account(account_id,root)
    if not row:
        raise AccountError("STORYBOARD_ACCOUNT_NOT_FOUND")
    # Detect foreign listeners (e.g. another Chrome) before accepting a CDP result.
    result=browser_probe(row)
    if result["connected"] and not _pid_browser_for_account(row):
        return {"connected":False,"reason":"CDP_PROFILE_MISMATCH","logged_in":None}
    return result


def require_production_browser(account=None,tool_url=None,*,allow_duplicate_for_isolated_job=False):
    """Read-only fail-fast guard: own Chrome + selected exact project/tool pair.

    Must run BEFORE Gemini/YouTube analysis or image budget submission.
    A saved project URL is not proof that Chrome is running or a tool tab exists.
    """
    row=account or active_account()
    state=connection_check(row["id"])
    if not state.get("connected"):
        raise AccountError("STORYBOARD_PRIVATE_BROWSER_NOT_CONNECTED")
    if not _pid_browser_for_account(row):
        raise AccountError("STORYBOARD_PRIVATE_CHROME_PROFILE_MISMATCH")
    from .projects import tabs, is_registered, exact_tool_tab_count, cleanup_duplicate_tool_tabs
    chosen=tool_url or account_tool_url(row)
    if not chosen or not is_registered(row,chosen):
        raise AccountError("FLOW_PROJECT_NOT_REGISTERED")

    # If there are orphan duplicate tabs and we are in single-tab mode, clean them up automatically
    if not allow_duplicate_for_isolated_job:
        cleanup_duplicate_tool_tabs(row, chosen)

    try:
        matches=[p for p in tabs(row) if
                 f"https://flow.google.com/project/{p['project_id']}/tool/{p['tool_id']}" ==
                 chosen.split("?",1)[0]]
    except (OSError,ValueError,TypeError) as exc:
        raise AccountError("STORYBOARD_PRIVATE_WEB_TOOL_NOT_OPEN") from exc

    count=exact_tool_tab_count(row,chosen)
    if count>1 and not allow_duplicate_for_isolated_job:
        cleanup_duplicate_tool_tabs(row, chosen)
        count=exact_tool_tab_count(row,chosen)
        if count>1:
            raise AccountError("STORYBOARD_PRIVATE_MULTIPLE_TOOL_TABS")

    if count<1 or (not allow_duplicate_for_isolated_job and len(matches)!=1) or (allow_duplicate_for_isolated_job and len(matches)<1):
        raise AccountError("STORYBOARD_PRIVATE_WEB_TOOL_NOT_OPEN")
    return chosen


def verify_mcp_connection(account_id, root=None, *, timeout=120, tool_url=None):
    """Read-only health against requested account and exact selected genre project."""
    row=find_account(account_id,root)
    if row is None:
        raise AccountError("STORYBOARD_ACCOUNT_NOT_FOUND")
    _require_idle(root)
    from .projects import is_registered
    link=tool_url or account_tool_url(row)
    if not link or not is_registered(row,link):
        return {"ok":False,"reason":"FLOW_PROJECT_NOT_SELECTED"}
    observed=connection_check(account_id,root)
    if not observed.get("connected"):
        return {"ok":False,"reason":observed.get("reason","BROWSER_NOT_CONNECTED")}
    if not flow_auth_status(row).get("authenticated"):
        return {"ok":False,"reason":"GOOGLE_FLOW_LOGIN_NOT_VERIFIED"}
    from .projects import exact_tool_tab_count, cleanup_duplicate_tool_tabs
    count=exact_tool_tab_count(row,link)
    if count>1:
        cleanup_duplicate_tool_tabs(row,link)
        count=exact_tool_tab_count(row,link)
    if count>1:
        return {"ok":False,"reason":"FLOW_MCP_DUPLICATE_TOOL_TABS","tab_count":count}
    if count<1:
        return {"ok":False,"reason":"FLOW_MCP_TOOL_TAB_NOT_OPEN","tab_count":0}
    from .transport import LocalFlowMcpTransport
    try:
        result=LocalFlowMcpTransport(timeout=timeout)(
           "flow_storyboard_native_image",{"action":"health","tool_url":link},
           account=row)
        for _ in range(3):
            if isinstance(result,dict) and isinstance(result.get("result"),dict):
                result=result["result"]
            else: break
        caps=set(result.get("capabilities") or [])
        ok=result.get("native") is True and result.get("sdk_image") is True and result.get("image_capability") is True and {"addToQueue","startImageProduction"}.issubset(caps)
        return {"ok":ok,"reason":"MCP_APP_CAPABILITIES_PASS" if ok else "MCP_APP_CAPABILITIES_MISSING"}
    except Exception as exc:
        return {"ok":False,"reason":str(exc)[:120]}

def _resolve_shared_tool_url(row, shared_url):
    """Resolve ONLY in the selected Studio-owned Chrome profile; never guess a project ID."""
    u=urlsplit(str(shared_url or "").strip())
    if (u.scheme!="https" or u.netloc!="flow.google.com"
            or not re.fullmatch(r"/shared/tool/[0-9a-fA-F-]{36}",u.path)
            or u.query or u.fragment):
        raise AccountError("STORYBOARD_PRIVATE_SHARED_TOOL_URL_INVALID")
    if not browser_probe(row).get("connected") or not _pid_browser_for_account(row):
        raise AccountError("STORYBOARD_PRIVATE_OPEN_SHARED_LINK_IN_STUDIO_CHROME")
    tool_id=u.path.rsplit("/",1)[1].casefold()
    try:
        with urlopen("http://127.0.0.1:%d/json/list" % row["cdp_port"],timeout=8.0) as response:
            pages=json.load(response)
    except (OSError,ValueError,TypeError) as exc:
        raise AccountError("STORYBOARD_PRIVATE_CHROME_TABS_UNAVAILABLE") from exc
    matches=[]
    for page in pages:
        if not isinstance(page,dict) or page.get("type")!="page":
            continue
        candidate=_canonical_storyboard_tool_url(page.get("url"))
        if candidate and urlsplit(candidate).path.rsplit("/",1)[-1].casefold()==tool_id:
            matches.append(candidate)
    if len(matches)!=1:
        raise AccountError("STORYBOARD_PRIVATE_OPEN_SHARED_LINK_IN_STUDIO_CHROME")
    return matches[0]

def refresh_account_tool_url(account):
    """Keep selected projects stable when several Flow tabs are open."""
    from .projects import url_for
    preferred=url_for(account)
    if preferred:
        return preferred
    try:
        current=_resolve_shared_tool_url(account,bundled_shared_tool_url())
    except (AccountError,OSError,ValueError):
        return account_tool_url(account)
    path=Path(account["state_dir"])/"studio_private_tool_url.json"
    try:
        saved=json.loads(path.read_text(encoding="utf-8")).get("url")
    except (OSError,ValueError,TypeError,AttributeError):
        saved=""
    if saved!=current:
        _atomic_store(path,{"url":current})
    return current

def save_tool_url(account_id, url, root=None):
    row=find_account(account_id,root)
    if row is None: raise AccountError("STORYBOARD_ACCOUNT_NOT_FOUND")
    _require_idle(root)
    raw=str(url or "").strip()
    link=_canonical_storyboard_tool_url(raw)
    if not link:
        link=_resolve_shared_tool_url(row,raw)
    if not _matches_bundled_tool(link):
        raise AccountError("STORYBOARD_ONLY_BUNDLED_TOOL_ALLOWED")
    path=Path(row["state_dir"])/"studio_private_tool_url.json"
    _atomic_store(path,{"url":link})
    return {"id":row["id"],"configured":True,"resolved_url":link}
