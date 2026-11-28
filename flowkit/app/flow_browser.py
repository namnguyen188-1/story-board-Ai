"""Start or show the configured Flow browser, scoped to its dedicated profile."""

import json

import os

from pathlib import Path

import re

import subprocess

import sys

import time

import urllib.request

from urllib.parse import urlsplit

_APP_DIR = str(Path(__file__).resolve().parent)
if _APP_DIR not in sys.path:
    sys.path.insert(0, _APP_DIR)

from common import ROOT, STATE, settings





def machine():

    path = STATE / "machine.json"

    if not path.is_file():

        raise RuntimeError("FLOWKIT_MACHINE_PROFILE_NOT_CONFIGURED")

    cfg = json.loads(path.read_text(encoding="utf-8-sig"))

    # Dynamic sync with Storyboard AI Studio active account
    storyboard_db = ROOT.parent / "studio" / "runtime" / "storyboard_accounts.json"
    if storyboard_db.is_file():
        try:
            sb_data = json.loads(storyboard_db.read_text(encoding="utf-8"))
            active_id = sb_data.get("active")
            for acc in sb_data.get("accounts", []):
                if acc.get("id") == active_id:
                    sb_profile = Path(acc.get("user_data_dir", ""))
                    sb_port = int(acc.get("cdp_port", 9461))
                    if sb_profile.is_dir():
                        cfg["flow_profile"] = str(sb_profile)
                        cfg["debug_port"] = sb_port
                        try:
                            path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
                        except Exception:
                            pass
                    # Sync active project & tool URL to FlowKit settings.json
                    try:
                        state_dir = Path(acc.get("state_dir", ""))
                        tool_file = state_dir / "studio_private_tool_url.json"
                        if tool_file.is_file():
                            tool_data = json.loads(tool_file.read_text(encoding="utf-8"))
                            tool_url = tool_data.get("url", "").strip()
                            if tool_url and "/project/" in tool_url:
                                m = re.search(r"/project/([0-9a-f-]+)", tool_url)
                                proj_id = m.group(1) if m else ""
                                settings_file = ROOT / "settings.json"
                                if settings_file.is_file():
                                    s_cfg = json.loads(settings_file.read_text(encoding="utf-8"))
                                    changed = False
                                    if proj_id and s_cfg.get("flow_project_id") != proj_id:
                                        s_cfg["flow_project_id"] = proj_id
                                        changed = True
                                    if s_cfg.get("flow_webtool_url") != tool_url:
                                        s_cfg["flow_webtool_url"] = tool_url
                                        changed = True
                                    if s_cfg.get("flow_hidden_webtool_url") != tool_url:
                                        s_cfg["flow_hidden_webtool_url"] = tool_url
                                        changed = True
                                    if changed:
                                        settings_file.write_text(json.dumps(s_cfg, indent=2), encoding="utf-8")
                    except Exception:
                        pass
                    break
        except Exception:
            pass

    configured_profile = cfg.get("flow_profile")

    if not configured_profile or not cfg.get("debug_port"):

        raise RuntimeError("FLOWKIT_AUTHORIZED_PROFILE_NOT_CONFIGURED")

    profile = Path(configured_profile)

    # Never fall back to an empty/new Chrome profile when the signed-in profile

    # selected in machine.json is missing, moved, or temporarily unavailable.

    if not profile.is_dir():

        raise RuntimeError("FLOWKIT_AUTHORIZED_PROFILE_MISSING_DO_NOT_CREATE_NEW")

    chrome = next((p for p in [Path(cfg.get("chrome", "missing")),

        Path(os.environ.get("PROGRAMFILES", "C:/Program Files")) / "Google/Chrome/Application/chrome.exe",

        Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/Application/chrome.exe"] if p.is_file()), None)

    if chrome is None:

        raise RuntimeError("CHROME_NOT_INSTALLED")

    return chrome, profile, int(cfg.get("debug_port", 9223))





def _extension_live_on_tab(target_url):

    """Non-mutating ready check for a previously installed FlowKit extension.



    A cold Chrome session can connect its existing extension while CDP's

    Extensions.* commands are temporarily unavailable. Avoid reloading a

    working tab or installing another extension in that case.

    """

    cfg = settings()

    host = str(cfg.get("flow_url", "")).rstrip("/")

    try:

        with urllib.request.urlopen(host + "/health", timeout=2) as response:

            health = json.load(response)

        if not health.get("extension_connected"):

            return False

        with urllib.request.urlopen(host + "/api/ext/debug-tab", timeout=2) as response:

            page = json.load(response).get("result", {}).get("data", {})

        current = urlsplit(str(page.get("url") or ""))

        expected = urlsplit(target_url)

        return (current.scheme == expected.scheme == "https" and

                current.netloc == expected.netloc == "flow.google.com" and

                current.path == expected.path)

    except (OSError, ValueError, KeyError, TypeError):

        return False





def open_browser(show=False):

    chrome, profile, port = machine()

    STATE.mkdir(exist_ok=True)

    profile.mkdir(parents=True, exist_ok=True)

    flag = STATE / "flow_window" / "unlock.flag"

    flag.parent.mkdir(exist_ok=True)

    if show:

        flag.write_text("unlock", encoding="ascii")

    # Never clear a user-requested login unlock during background job startup.

    # Locking again is only done with the explicit tray menu action.

    cfg = settings()

    project_url = "https://flow.google.com/project/" + cfg["flow_project_id"]

    target_url = cfg.get("flow_hidden_webtool_url") or cfg.get("flow_webtool_url") or project_url

    parsed = urlsplit(target_url)

    if parsed.scheme != "https" or parsed.netloc != "flow.google.com" or not parsed.path.startswith("/project/"):

        raise RuntimeError("FLOW_WEBTOOL_URL_INVALID")

    args = [str(chrome), "--user-data-dir=" + str(profile), "--remote-debugging-address=127.0.0.1",

            "--remote-debugging-port=" + str(port), "--no-first-run", "--no-default-browser-check",

            "--hide-crash-restore-bubble", "--window-size=1100,800"]

    if not show:

        args.append("--window-position=-32000,-32000")

    # Reuse the exact authenticated Chrome instance. Chrome singleton calls with

    # a URL silently create an extra tab, even in the same existing profile.

    try:

        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=2) as response:

            json.load(response)

        browser_live = True

    except (OSError, ValueError):

        browser_live = False

    if browser_live:

        from browser_lifecycle import _owns_debug_port

        if not _owns_debug_port():

            raise RuntimeError("FLOWKIT_DEBUG_PORT_NOT_OWNED_BY_AUTHORIZED_PROFILE")

        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=3) as response:

            tabs = json.load(response)

        matching = [t for t in tabs if t.get("type") == "page" and t.get("url") == target_url]

        if len(matching) > 1:

            # Chrome session restore can open a duplicate of exactly the same

            # project. Preserve every unsaved/active shot; only collapse tabs

            # after the Web Tool Bridge confirms they are identical and idle.

            from browser_lifecycle import _normalize_restored_tabs

            _normalize_restored_tabs()

            with urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=3) as response:

                tabs = json.load(response)

            matching = [t for t in tabs if t.get("type") == "page" and t.get("url") == target_url]

        if len(matching) == 0:
            # Preserve every old tool and its unsaved results when switching versions.
            matching = _open_target_page(f"http://127.0.0.1:{port}", target_url)
        if len(matching) != 1:

            # Never launch another Chrome command or navigate login tabs.

            raise RuntimeError("FLOWKIT_AUTHORIZED_WEBTOOL_TAB_MISSING_OR_DUPLICATE")

    else:

        # The same profile might already be running but CDP could be starting

        # or unavailable. Detect that condition and NEVER launch a second copy.

        safe_profile = str(profile).replace("'", "''")

        probe = ("$p='" + safe_profile + "';"

                 "$items=@(Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | "

                 "Where-Object {$_.CommandLine -and $_.CommandLine.Contains($p) "

                 "-and $_.CommandLine -notmatch '\\s--type='});"

                 "Write-Output $items.Count")

        result = subprocess.run(["powershell.exe", "-WindowStyle", "Hidden", "-NoProfile", "-NonInteractive", "-Command", probe],

                                capture_output=True, text=True, timeout=12, creationflags=0x08000000)

        if result.returncode != 0 or not result.stdout.strip().isdigit():

            raise RuntimeError("FLOWKIT_PROFILE_PROCESS_CHECK_FAILED")

        if int(result.stdout.strip()) > 0:

            raise RuntimeError("FLOWKIT_AUTHORIZED_PROFILE_RUNNING_WITHOUT_DEBUG_PORT")

        subprocess.Popen(args + [target_url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=0x08000000)

    guard = ROOT / "app" / "flow_window_guard.ps1"

    subprocess.Popen(["powershell.exe", "-WindowStyle", "Hidden", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(guard),

                      "-BrowserProfile", str(profile)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=0x08000000)

    from extension_bootstrap import ensure_extension, ExtensionBootstrapError

    from common import atomic

    from store import Store

    def can_install():

        now = time.time()

        for job in Store(STATE / "jobs.sqlite").list(100):

            if job.get("provider") not in {"flow", "webtool"}:

                continue

            if job.get("state") == "running" and (now - job.get("updated_at", 0) < 60):

                if job.get("remote") or job.get("phase") not in {"new", "webtool_checking"}:

                    return False

        return True

    for attempt in range(30):

        # Cold-start reconnects can complete after Chrome starts CDP. If the

        # existing extension is already serving the approved project, do not

        # invoke Extensions.loadUnpacked or reload its active tab.

        if _extension_live_on_tab(target_url):

            print("FLOW_EXTENSION=reused_live")

            break

        try:

            extension = ensure_extension(port, ROOT / "extensions" / "flow", can_install=can_install)

            atomic(STATE / "flow_extension.json", extension)

            print("FLOW_EXTENSION=" + extension["mode"])

            break

        except ExtensionBootstrapError as error:

            if str(error) not in {

                "CHROME_EXTENSION_API_UNAVAILABLE",

                "CHROME_EXTENSION_API_TIMEOUT",

                "FLOW_EXTENSION_NOT_ENABLED",

            } or attempt == 29:

                raise

            time.sleep(1)

        except Exception:

            if attempt == 29:

                raise RuntimeError("FLOW_CHROME_DEBUG_ENDPOINT_UNAVAILABLE") from None

            time.sleep(0.5)

    if show:

        print("FLOW_LOGIN_WINDOW_OPEN: extension ready; sign in to Google Flow if needed")

        return

    # A cold Chrome start can briefly land on /about before Google restores sign-in.

    # One navigation after startup warms the same configured project; never submits media.

    for _ in range(12):

        try:

            tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=1))

            tab = next(t for t in tabs if t.get("type") == "page" and t.get("url", "").startswith("https://flow.google.com/"))

            if tab["url"].startswith(target_url):

                return

            if tab["url"] == "https://flow.google.com/about":

                time.sleep(2)

                from websockets.sync.client import connect

                with connect(tab["webSocketDebuggerUrl"], open_timeout=3) as ws:

                    ws.send(json.dumps({"id": 1, "method": "Page.navigate", "params": {"url": target_url}}))

                    ws.recv(timeout=5)

                return

        except Exception:

            pass

        time.sleep(0.5)







def _open_target_page(base, target_url):
    """Open the configured tool without navigating an unrelated existing tab."""
    from websockets.sync.client import connect
    from flow_webtool_direct import _cdp
    with urllib.request.urlopen(base + "/json/version", timeout=3) as response:
        browser = json.load(response)
    with connect(browser["webSocketDebuggerUrl"], open_timeout=4) as ws:
        _cdp(ws, 1, "Target.createTarget", {"url": target_url, "background": True})
    for _ in range(16):
        with urllib.request.urlopen(base + "/json", timeout=3) as response:
            tabs = json.load(response)
        matching = [t for t in tabs if t.get("type") == "page" and t.get("url") == target_url]
        if matching:
            return matching
        time.sleep(.5)
    return []

if __name__ == "__main__":

    open_browser(show="--show" in sys.argv)

