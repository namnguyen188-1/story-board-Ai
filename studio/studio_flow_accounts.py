"""Studio-owned Google Flow account profiles, with private backend and registry.

Each Studio account is stored in D:/STORYBOARD_AI/studio/runtime/ (NOT V2).
Passwords, cookies and session tokens are never read, copied or logged.
"""
from __future__ import annotations
import os,sys,uuid,socket,subprocess,time,ctypes,json
from pathlib import Path
HOME=Path(__file__).resolve().parent
from studio_mcp import accounts as base
from studio_mcp.transport import _isolated

def accounts():
    store=base.load_accounts(HOME)
    active=store["active"]
    return {"active":active,"tool_linked":bool(base.account_tool_url(base.active_account(HOME))),"accounts":[
        {"id":row["id"],"name":row["name"],"active":row["id"]==active}
        for row in store["accounts"]]}

def active():
    return base.active_account(HOME)

def select(identifier):
    return base.select_account(identifier,HOME)

def create(name):
    name=str(name or "").strip()
    if not name or len(name)>65 or any(ord(c)<32 for c in name):
        raise base.AccountError("ACCOUNT_NAME_INVALID")
    store=base.load_accounts(HOME)
    if len(store["accounts"])>=base.MAX_ACCOUNTS:
        raise base.AccountError("ACCOUNT_LIMIT_REACHED")
    ident="account_"+uuid.uuid4().hex[:12]
    # V2's new-account range is 9340-9450. Studio has a disjoint range.
    used={int(a["cdp_port"]) for a in store["accounts"]}
    def free_port(port):
        with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as sock:
            sock.settimeout(.15)
            return sock.connect_ex(("127.0.0.1",port))!=0
    port=next((p for p in range(9460,9540) if p not in used and free_port(p)),None)
    if port is None:
        raise base.AccountError("NO_UNUSED_STUDIO_PROFILE_PORT")
    folder=Path(__file__).resolve().parent/"flow_accounts"/ident
    state=Path.home()/".storyboard-studio-flow-mcp"/ident
    row={"id":ident,"name":name,"user_data_dir":str(folder),
         "profile_directory":"Default","cdp_port":port,"state_dir":str(state)}
    store["accounts"].append(row)
    base._atomic_store(base.registry_path(HOME),base._validate_registry(store))
    return {"id":ident,"name":name}

def _attach_desktop():
    if os.name!="nt":
        return
    u=ctypes.windll.user32
    try:
        hwinsta = u.OpenWindowStationW("WinSta0", False, 0x037F)
        if hwinsta:
            u.SetProcessWindowStation(hwinsta)
        h_desk = u.OpenInputDesktop(0, False, 0x01FF) or u.OpenDesktopW("Default", 0, False, 0x01FF)
        if h_desk:
            u.SetThreadDesktop(h_desk)
    except Exception:
        pass

def _visible_chrome_window(pid):
    """Return a truly visible Chrome window HWND, not merely a running process."""
    if os.name!="nt" or not pid:
        return None
    _attach_desktop()
    u=ctypes.windll.user32
    for hwnd in _chrome_hwnds_for_pid(pid):
        if u.IsWindowVisible(hwnd) and not u.IsIconic(hwnd):
            return hwnd
    return None

_last_manual_restore_time = 0.0

def _show_chrome_window(pid):
    global _last_manual_restore_time
    _last_manual_restore_time = time.time()
    if os.name!="nt" or not pid:
        return False
    _attach_desktop()
    u=ctypes.windll.user32
    hwnds=_chrome_hwnds_for_pid(pid)
    success=False
    if hwnds:
        for hwnd in hwnds:
            try:
                # Clear any clipping region so the full window is restored
                u.SetWindowRgn(hwnd, 0, True)
                u.ShowWindowAsync(hwnd, 9)  # SW_RESTORE
                u.ShowWindow(hwnd, 5)       # SW_SHOW
                u.ShowWindow(hwnd, 9)
                u.SetForegroundWindow(hwnd)
                success=True
            except OSError:
                pass
    return success

def restore_chrome_window(pid):
    """Restores Chrome window from hidden/taskbar to screen."""
    return _show_chrome_window(pid)

def _get_managed_studio_pids(home=None):
    """Return strictly the PIDs of browser processes launched/managed by Storyboard MCP accounts."""
    pids = set()
    try:
        store = base.load_accounts(home or HOME)
        for row in store.get("accounts", []):
            p = base._pid_browser_for_account(row)
            if p:
                pids.add(int(p))
    except Exception:
        pass
    return pids

def _chrome_hwnds_for_pid(pid=None):
    """Return ONLY genuine Chromium browser windows belonging strictly to Studio-managed accounts."""
    if os.name!="nt":
        return []
    u=ctypes.windll.user32
    windows=[]
    target_pid = int(pid) if pid else 0
    if target_pid:
        allowed_pids = {target_pid}
    else:
        allowed_pids = _get_managed_studio_pids()
    if not allowed_pids:
        return []

    desktops = []
    h_def = u.OpenDesktopW("Default", 0, False, 0x10000000)
    if h_def:
        desktops.append((h_def, True))
    h_curr = u.GetThreadDesktop(ctypes.windll.kernel32.GetCurrentThreadId())
    if h_curr and h_curr != h_def:
        desktops.append((h_curr, False))

    for hDesk, should_close in desktops:
        def callback(hwnd, unused):
            owner = ctypes.c_ulong()
            u.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
            if owner.value not in allowed_pids:
                return 1
            cls_buf = ctypes.create_unicode_buffer(128)
            u.GetClassNameW(hwnd, cls_buf, 128)
            cls_name = cls_buf.value
            if cls_name in ("Chrome_WidgetWin_0", "Base_PowerMessageWindow", "IME", "MSCTFIME UI", "Chrome_StatusTrayWindow"):
                return 1
            if cls_name and "Chrome_WidgetWin" not in cls_name:
                return 1
            title_buf = ctypes.create_unicode_buffer(512)
            u.GetWindowTextW(hwnd, title_buf, 512)
            title = title_buf.value
            if "Storyboard AI Studio" in title:
                return 1
            if hwnd not in windows:
                windows.append(hwnd)
            return 1

        cb_type = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p)
        u.EnumDesktopWindows(hDesk, cb_type(callback), 0)
        if should_close:
            u.CloseDesktop(hDesk)

    return windows

def minimize_chrome_window(pid=None):
    """Keep Chrome running, neatly minimized on the Windows Taskbar."""
    if os.name != "nt":
        return False
    _attach_desktop()
    u = ctypes.windll.user32
    hwnds = _chrome_hwnds_for_pid(pid)
    success = False
    if hwnds:
        for hwnd in hwnds:
            try:
                # Remove any clipping region so the window is normal
                u.SetWindowRgn(hwnd, 0, True)
                # SW_SHOWMINNOACTIVE (7) minimizes window to taskbar without taking focus
                u.ShowWindow(hwnd, 7)
                success = True
            except OSError:
                pass
    return success

def lock_chrome_minimized_async(pid=None, home=None, delays=(0.05, 0.15, 0.3, 0.6, 1.0, 1.5, 2.5, 4.0, 6.0, 8.0)):
    """Keep Chrome minimized on the taskbar across asynchronous tab events."""
    import threading
    start_ts = time.time()
    def _runner():
        target_pid = pid
        if not target_pid:
            row = base.active_account(home or HOME)
            target_pid = base._pid_browser_for_account(row) if row else None
        if not target_pid:
            return
        for d in delays:
            time.sleep(d)
            if _last_manual_restore_time > start_ts:
                return  # User manually restored window; do not minimize back
            try:
                minimize_chrome_window(target_pid)
            except Exception:
                pass
    threading.Thread(target=_runner, daemon=True).start()

def lock_chrome_during_production(stop_event, pid=None, interval=0.5, home=None):
    """Continuously ensures Chrome stays minimized on the taskbar during a production run.
    Uses SW_SHOWMINNOACTIVE (7) so it stays on the taskbar without taking focus.
    """
    import threading
    def _guard():
        target_pid = pid
        while not stop_event.is_set():
            if not target_pid:
                row = base.active_account(home or HOME)
                target_pid = base._pid_browser_for_account(row) if row else None
            if target_pid:
                try:
                    if not is_chrome_minimized(target_pid):
                        minimize_chrome_window(target_pid)
                except Exception:
                    pass
            stop_event.wait(interval)
    t = threading.Thread(target=_guard, daemon=True, name="ProductionTaskbarChromeLock")
    t.start()
    return t

_HEARTBEAT_THREAD = None
_HEARTBEAT_LOCK = __import__("threading").Lock()

def start_flow_heartbeat(home=None):
    """Anti-sleep background heartbeat for Google Flow Chrome instances."""
    global _HEARTBEAT_THREAD
    with _HEARTBEAT_LOCK:
        if _HEARTBEAT_THREAD and _HEARTBEAT_THREAD.is_alive():
            return
        def _worker():
            import urllib.request
            while True:
                time.sleep(25.0)
                try:
                    row = base.active_account(home or HOME)
                    if not row:
                        continue
                    port = row.get("cdp_port")
                    pid = base._pid_browser_for_account(row)
                    if not pid or not port:
                        continue
                    # Lightweight keepalive ping to Chrome CDP socket
                    url = f"http://127.0.0.1:{port}/json/list"
                    req = urllib.request.Request(url, headers={"User-Agent": "StoryboardFlowHeartbeat/1.0"})
                    with urllib.request.urlopen(req, timeout=3.0) as resp:
                        pass
                except Exception:
                    pass
        import threading
        _HEARTBEAT_THREAD = threading.Thread(target=_worker, name="GoogleFlowAntiSleepHeartbeat", daemon=True)
        _HEARTBEAT_THREAD.start()

def is_chrome_minimized(pid=None):
    if os.name!="nt":
        return False
    _attach_desktop()
    u=ctypes.windll.user32
    hwnds=_chrome_hwnds_for_pid(pid)
    if not hwnds:
        return False
    return all((not u.IsWindowVisible(hwnd) or u.IsIconic(hwnd)) for hwnd in hwnds)

def minimize_active_account_browser(home=None):
    row=base.active_account(home or HOME)
    pid=base._pid_browser_for_account(row)
    res = False
    if pid:
        res = minimize_chrome_window(pid)
        lock_chrome_minimized_async(pid, home=home)
    # Also minimize by title in case PID was delayed or multi-window
    res = minimize_chrome_window(None) or res
    return res

def restore_active_account_browser(home=None):
    global _last_manual_restore_time
    _last_manual_restore_time = time.time()
    row=base.active_account(home or HOME)
    pid=base._pid_browser_for_account(row)
    if pid and restore_chrome_window(pid):
        return True
    hwnds = _chrome_hwnds_for_pid(None)
    if hwnds:
        _attach_desktop()
        u = ctypes.windll.user32
        for hwnd in hwnds:
            u.ShowWindowAsync(hwnd, 9)
            u.ShowWindow(hwnd, 5)
            u.ShowWindow(hwnd, 9)
            u.SetForegroundWindow(hwnd)
        return True
    return False

def _only_google_flow_pages(account):
    """Do not close an invisible browser which may hold unrelated user tabs."""
    from urllib.request import urlopen
    from urllib.parse import urlsplit
    try:
        with urlopen("http://127.0.0.1:%d/json/list" %
                     account["cdp_port"], timeout=8.0) as response:
            pages=json.load(response)
        hosts=[urlsplit(p.get("url","")).hostname or ""
               for p in pages if isinstance(p,dict) and p.get("type")=="page"]
        return bool(hosts) and all(host in {
             "flow.google.com","omnibox-popup.top-chrome","chrome",
             "chrome-untrusted","newtab",""} for host in hosts)
    except (OSError,ValueError,KeyError):
        return False

def _close_invisible_google_flow(account,pid):
    """Gracefully close ONLY this isolated, windowless Flow Chrome process."""
    _isolated(account)
    if _visible_chrome_window(pid):
        raise base.AccountError("CANNOT_RESTART_VISIBLE_CHROME")
    if not _only_google_flow_pages(account):
        raise base.AccountError(
           "GOOGLE_FLOW_HIDDEN_BROWSER_HAS_OTHER_TABS: mở lại Chrome thủ công.")
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser=p.chromium.connect_over_cdp(
                "http://127.0.0.1:%d"%account["cdp_port"],timeout=8000)
            browser.new_browser_cdp_session().send("Browser.close")
    except Exception as exc:
        raise base.AccountError("CANNOT_REOPEN_HIDDEN_BROWSER") from exc
    for _ in range(35):
        if not base._pid_browser_for_account(account):
            return
        time.sleep(.2)
    raise base.AccountError("HIDDEN_CHROME_DID_NOT_CLOSE")

def open_login(identifier):
    """Open visible interactive Chrome for manual Google Flow sign-in.

    A process/CDP connection alone does NOT prove a user-visible window or login.
    """
    account=base.find_account(identifier,HOME)
    if account is None:
        raise base.AccountError("STORYBOARD_ACCOUNT_NOT_FOUND")
    _isolated(account)
    base._require_idle(HOME)
    chrome=base._chrome_path()
    if not chrome.is_file():
        raise base.AccountError("GOOGLE_CHROME_NOT_INSTALLED")
    observed=base.browser_probe(account)
    pid=base._pid_browser_for_account(account)
    if observed["connected"] and pid and _show_chrome_window(pid):
        # One browser window per Studio account. Do not open a second Chrome
        # window or new Tool tab when the user only asks to sign in.
        # Auto Flow resolves and registers the Tool independently after login.
        base.mark_manual_login(identifier,HOME)
        return {"opened":True,"window_visible":True,"reused":True,
                "account":identifier,"signin_required":True}
    if observed["connected"] and pid:
        _show_chrome_window(pid)
        base.mark_manual_login(identifier,HOME)
        return {"opened":True,"window_visible":True,"reused":True,
                "account":identifier,"signin_required":True}
    elif pid:
        # A process with the correct profile but no usable CDP is not a
        # license to launch a duplicate browser/window. Keep its tabs safe.
        raise base.AccountError("FLOW_CHROME_PROFILE_CDP_OFFLINE: hãy kiểm tra hoặc đóng Chrome này trước khi mở lại.")
    account_dir=Path(account["user_data_dir"])
    account_dir.mkdir(parents=True,exist_ok=True)
    launch_args = [
        str(chrome),"--remote-debugging-port="+str(account["cdp_port"]),
        "--user-data-dir="+str(account_dir),
        "--profile-directory=Default","--no-first-run",
        "--no-default-browser-check","--new-window",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
        "--disable-features=CalculateNativeWinOcclusion,AutomaticTabDiscarding,IntensiveWakeUpThrottling,HighEfficiencyModeTier1",
        "--window-size=516,450","--window-position=1389,575",
        base.account_tool_url(account) or base.bundled_shared_tool_url() or "https://flow.google.com"
    ]
    start_flow_heartbeat(HOME)
    proc=subprocess.Popen(launch_args,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    for _ in range(40):
        if _show_chrome_window(proc.pid):
            base.mark_manual_login(identifier,HOME)
            return {"opened":True,"window_visible":True,"reused":False,
                    "account":identifier,"signin_required":True}
        if proc.poll() is not None:
            break
        time.sleep(.2)
    base.mark_manual_login(identifier,HOME)
    return {"opened":True,"window_visible":True,"reused":False,
            "account":identifier,"signin_required":True}


def _confirmed_visible_project(account, ref, *, wait_seconds=10):
    """Confirm real CDP tool tab exists; do not force unminimize if running quietly."""
    from studio_mcp.projects import tabs
    deadline=time.monotonic()+wait_seconds
    while True:
        pid=base._pid_browser_for_account(account)
        if pid and any(item["id"]==ref for item in tabs(account)):
            return True
        if time.monotonic()>=deadline:
            return False
        time.sleep(.4)


def open_project(account, ref):
    """Open one registered Flow project, VERIFY tab; never touch V2."""
    from studio_mcp.projects import load,project_url,ProjectError,tabs
    _isolated(account)
    base._require_idle(HOME)
    entry=next((p for p in load(account)["projects"] if p["id"]==ref),None)
    if entry is None:
        raise ProjectError("FLOW_PROJECT_NOT_REGISTERED")
    url=project_url(entry["project_id"],entry["tool_id"])
    chrome=base._chrome_path()
    if not chrome.is_file():
        raise base.AccountError("GOOGLE_CHROME_NOT_INSTALLED")
    state=base.connection_check(account["id"],HOME)
    pid=base._pid_browser_for_account(account)
    from studio_mcp.projects import exact_tool_tab_count
    if exact_tool_tab_count(account,url)>1:
        raise base.AccountError("FLOW_MCP_DUPLICATE_TOOL_TABS: hãy giữ một tab sau khi lưu công việc trong tab còn lại.")
    if state.get("connected"):
        if not pid:
            raise base.AccountError("FLOW_CDP_PROFILE_MISMATCH")
        # Never duplicate an already-open tool; MCP requires exactly one tab.
        if any(p["id"]==ref for p in tabs(account)):
            return {"opened":True,"window_visible":True,
                    "tool_tab_verified":True,"existing":True,"project_id":ref}
        # Reuse the existing account Chrome window; only add a Tool tab.
        argv=[str(chrome),"--user-data-dir="+str(account["user_data_dir"]),
              "--profile-directory=Default","--new-tab",url]
    else:
        if pid:
            raise base.AccountError(
                "FLOW_CHROME_PROFILE_CDP_OFFLINE: Chrome còn chạy nhưng cổng điều khiển mất kết nối.")
        argv=[str(chrome),"--remote-debugging-port="+str(account["cdp_port"]),
              "--user-data-dir="+str(account["user_data_dir"]),
              "--profile-directory=Default","--no-first-run",
              "--start-minimized",
              "--disable-background-timer-throttling",
              "--disable-backgrounding-occluded-windows",
              "--disable-renderer-backgrounding",
              "--disable-features=CalculateNativeWinOcclusion,AutomaticTabDiscarding,IntensiveWakeUpThrottling,HighEfficiencyModeTier1",
              "--new-window",url]
    start_flow_heartbeat(HOME)
    flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    subprocess.Popen(argv,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=flags)
    # Immediately minimize to taskbar so window never floats on screen
    time.sleep(0.3)
    init_pid = base._pid_browser_for_account(account) or pid
    if init_pid:
        minimize_chrome_window(init_pid)
        lock_chrome_minimized_async(init_pid)
    # Wait for tab condition without popping window
    if not _confirmed_visible_project(account,ref,wait_seconds=15):
        raise base.AccountError(
            "FLOW_PROJECT_WINDOW_NOT_VISIBLE_OR_TAB_NOT_READY: "
            "Chrome chưa hiển thị đúng Web Tool; hãy bấm Mở đăng nhập Google Flow.")
    current_pid = base._pid_browser_for_account(account) or pid
    if current_pid:
        minimize_chrome_window(current_pid)
        lock_chrome_minimized_async(current_pid)
    return {"opened":True,"window_visible":False,
            "tool_tab_verified":True,"existing":False,"project_id":ref}


def check(identifier):
    state=base.connection_check(identifier,HOME)
    account=base.find_account(identifier,HOME)
    auth=(base.flow_auth_status(account) if account else
          {"authenticated":False,"auth_state":"ACCOUNT_NOT_FOUND"})
    state["logged_in"]=bool(auth.get("authenticated"))
    state["auth_state"]=auth.get("auth_state","UNKNOWN")
    if account and state.get("connected") and state["logged_in"]:
        base.refresh_account_tool_url(account)
    pid=base._pid_browser_for_account(account) if account else 0
    visible=bool(pid and (_visible_chrome_window(pid) or is_chrome_minimized(pid)))
    state["window_visible"]=visible
    if state.get("connected") and not state["logged_in"]:
        state["reason"]="GOOGLE_LOGIN_NOT_VERIFIED"
    elif state.get("connected") and not visible:
        state["reason"]="CHROME_CONNECTED_BUT_WINDOW_HIDDEN"
    return state


def verify(identifier,genre="auto"):
    from studio_mcp.projects import url_for
    account=base.find_account(identifier,HOME)
    if account is None:raise base.AccountError("STORYBOARD_ACCOUNT_NOT_FOUND")
    return base.verify_mcp_connection(identifier,HOME,tool_url=url_for(account,genre))

def apply_worker_env():
    # Called BEFORE the first Google Flow MCP request in a dedicated Studio
    # worker. Do not export V2_STORYBOARD_ACCOUNT_ID (belongs to V2 registry).
    row=active()
    _isolated(row)
    env=base.account_env(row)
    os.environ.update(env)
    for key in tuple(os.environ):
        if key.startswith(("V2_FLOW_","V2_STORYBOARD_")): os.environ.pop(key,None)
    from studio_mcp.projects import is_registered
    frozen=os.environ.get("STORYBOARD_FROZEN_PROJECT_URL","")
    if frozen and not is_registered(row,frozen):
        raise base.AccountError("STORYBOARD_FROZEN_PROJECT_NOT_REGISTERED")
    os.environ["STORYBOARD_STUDIO_TOOL_URL"]=frozen or base.account_tool_url(row)
    return {"id":row["id"],"name":row["name"]}

def set_tool_url(identifier, url):
    row = base.find_account(identifier, HOME)
    if row is None:
        raise base.AccountError("STORYBOARD_ACCOUNT_NOT_FOUND")
    _isolated(row)
    return base.save_tool_url(identifier,url,HOME)

def tool_url_for_active():
    return base.account_tool_url(base.active_account(HOME))
