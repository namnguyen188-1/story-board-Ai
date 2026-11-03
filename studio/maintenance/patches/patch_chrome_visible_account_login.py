"""Permanent Studio Chrome window visibility/repair fix.
Only writes Studio code; no V2 patch or account/session data mutation.
"""
from pathlib import Path
import shutil,datetime,py_compile
file=Path(r"D:\STORYBOARD_AI\studio\studio_flow_accounts.py")
backup=file.parent/"checkpoints"/("chrome_visible_login_"+datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
backup.mkdir(parents=True,exist_ok=True)
shutil.copy2(file,backup/file.name)
s=file.read_text(encoding="utf-8")
s=s.replace("import os,sys,uuid,socket,subprocess","import os,sys,uuid,socket,subprocess,time,ctypes,json",1)
start=s.index("def open_login(identifier):")
end=s.index("\ndef check(identifier):",start)
block='''def _visible_chrome_window(pid):
    """Return a truly visible Chrome window HWND, not merely a running process."""
    if os.name!="nt" or not pid:
        return None
    u=ctypes.windll.user32
    cb_type=ctypes.WINFUNCTYPE(ctypes.c_bool,ctypes.c_void_p,ctypes.c_void_p)
    windows=[]
    @cb_type
    def callback(hwnd,unused):
        owner=ctypes.c_ulong()
        u.GetWindowThreadProcessId(hwnd,ctypes.byref(owner))
        if owner.value==pid and u.IsWindowVisible(hwnd):
            windows.append(hwnd)
        return True
    u.EnumWindows(callback,0)
    return windows[0] if windows else None

def _show_chrome_window(pid):
    hwnd=_visible_chrome_window(pid)
    if hwnd:
        try:
            u=ctypes.windll.user32
            u.ShowWindow(hwnd,9)  # SW_RESTORE
            u.SetForegroundWindow(hwnd)  # best effort, Windows may prevent focus
        except OSError:
            pass
    return bool(hwnd)

def _only_google_flow_pages(account):
    """Do not close an invisible browser which may hold unrelated user tabs."""
    from urllib.request import urlopen
    from urllib.parse import urlsplit
    try:
        with urlopen("http://127.0.0.1:%d/json/list" %
                     account["cdp_port"], timeout=3) as response:
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
    if account["id"]=="default" or _visible_chrome_window(pid):
        raise base.AccountError("CANNOT_RESTART_VISIBLE_OR_SHARED_CHROME")
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
    base._require_idle(HOME)
    if identifier=="default":
        # Shared legacy browser must never be stopped/restarted by Studio.
        info=base.open_account_login(identifier,HOME)
        pid=base._pid_browser_for_account(account)
        if not _show_chrome_window(pid):
            raise base.AccountError(
                "DEFAULT_BROWSER_NOT_VISIBLE: kiểm tra cửa sổ Chrome tài khoản V2.")
        return dict(info,window_visible=True,signin_required=True)
    chrome=base._chrome_path()
    if not chrome.is_file():
        raise base.AccountError("GOOGLE_CHROME_NOT_INSTALLED")
    observed=base.browser_probe(account)
    pid=base._pid_browser_for_account(account)
    if observed["connected"] and pid and _show_chrome_window(pid):
        base.mark_manual_login(identifier,HOME)
        return {"opened":True,"window_visible":True,"reused":True,
                "account":identifier,"signin_required":True}
    if observed["connected"] and pid:
        # Old --app browser is alive but had no window. This is exactly the bug
        # observed on 2026-10-12. Restart only if there are no unrelated tabs.
        _close_invisible_google_flow(account,pid)
    elif pid:
        raise base.AccountError(
            "CHROME_PROFILE_RUNNING_WITHOUT_CDP: close this profile manually.")
    account_dir=Path(account["user_data_dir"])
    account_dir.mkdir(parents=True,exist_ok=True)
    proc=subprocess.Popen([
        str(chrome),"--remote-debugging-port="+str(account["cdp_port"]),
        "--user-data-dir="+str(account_dir),
        "--profile-directory=Default","--no-first-run",
        "--no-default-browser-check","--new-window",
        "--window-size=900,760","--window-position=80,70",
        "https://flow.google.com/"
    ],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    for _ in range(40):
        if _show_chrome_window(proc.pid):
            base.mark_manual_login(identifier,HOME)
            return {"opened":True,"window_visible":True,"reused":False,
                    "account":identifier,"signin_required":True}
        if proc.poll() is not None:
            break
        time.sleep(.2)
    raise base.AccountError(
       "GOOGLE_FLOW_CHROME_NO_VISIBLE_WINDOW: hồ sơ đã lưu, "
       "nhưng Chrome chưa hiển thị; vui lòng thử Mở đăng nhập lần nữa.")

'''
s=s[:start]+block+s[end:]
file.write_text(s,encoding="utf-8")
py_compile.compile(str(file),doraise=True)
print("CHROME_VISIBILITY_AND_HIDDEN_PROFILE_RECOVERY_PATCH_PASS",flush=True)
print("CHECKPOINT",backup,flush=True)
