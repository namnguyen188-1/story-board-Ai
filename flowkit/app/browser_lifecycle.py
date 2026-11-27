"""On-demand lifetime control for FlowKit's PRIVATE Chrome profile only.







The API & Flow extension broker remain available to accept requests.  The browser



starts only when the 'flow' or 'webtool' workers actually claim a media job.



No media request is replayed, and an in-flight/uncertain job prevents shutdown.



"""



from __future__ import annotations



import json



from pathlib import Path



import subprocess



import threading



import time



import urllib.request







from common import ROOT, STATE, settings



from store import Store







_LOCK = threading.RLock()



_LEASES = 0



_LAST_ACTIVITY = time.monotonic()



_STARTED_AT = time.monotonic()



_ACTIVE_PROVIDERS = {"flow", "webtool"}











class BrowserBusy(RuntimeError):



    pass











def _machine():



    from flow_browser import machine



    return machine()











def _debug(port):



    try:



        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=2) as r:



            return json.load(r)



    except Exception:



        return None











def _owns_debug_port():



    """Refuse to close a browser unless the port is owned by our exact profile."""



    chrome, profile, port = _machine()



    ps = (



        f"$c=Get-NetTCPConnection -LocalPort {port} -State Listen -ErrorAction SilentlyContinue "



        "| Select-Object -First 1; "



        "if(-not $c){exit 2}; "



        "$p=Get-CimInstance Win32_Process -Filter ('ProcessId='+$c.OwningProcess); "



        "if(-not $p){exit 3}; "



        "$p.CommandLine"



    )



    try:



        result = subprocess.run(



            ["powershell.exe", "-WindowStyle", "Hidden", "-NoProfile", "-NonInteractive", "-Command", ps],



            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=8, text=True, creationflags=0x08000000)



        command = (result.stdout or "").lower().replace('"', '').replace("'", "")



        check = "--user-data-dir=" + str(profile).lower()



        return result.returncode == 0 and check in command and "chrome.exe" in command



    except Exception:



        return False











def _pending_jobs():



    jobs = Store(STATE / "jobs.sqlite").list(10000)



    active = [j for j in jobs if j["provider"] in _ACTIVE_PROVIDERS



              and j["state"] in ("queued", "running")]



    # An old remote submission with no confirmed media/job ID may remain in



    # recovery_needed for auditing. An explicitly reviewed, parked job cannot



    # be resumed or resubmitted; it need not hold the browser open forever.



    unresolved_blocking = [j for j in jobs if j["provider"] in _ACTIVE_PROVIDERS



                  and j["state"] == "recovery_needed"



                  and j.get("browser_hold") is not False]



    return len(active), len(unresolved_blocking)











def _chrome_active():



    _, _, port = _machine()



    return _debug(port) is not None











def _webtool_busy():



    """Conservatively refuse browser close if tool render state is unknown."""



    from flow_browser import machine



    _, _, port = machine()



    try:



        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json",timeout=3) as r:



            pages = json.load(r)



        cfg = settings()



        tools = {cfg.get("flow_hidden_webtool_url"),cfg.get("flow_webtool_url")}



        targets = [



            p for p in pages



            if p.get("type") == "page" and (



                p.get("url") in tools or



                "69da86fb-6c79-43d2-a387-ef47b0fda4db" in p.get("url", "") or



                ("flow.google.com" in p.get("url", "") and "/tool/" in p.get("url", ""))



            )



        ]



        if not targets:



            return False



        from flow_webtool_direct import WebToolAdapter



        for p in targets:



            mode = "hidden" if p["url"] == cfg.get("flow_hidden_webtool_url") else "active"



            # No DOM/Bridge means state cannot be trusted. Do not close.



            state = WebToolAdapter(mode).status()



            if state.get("processing") or any(



                q["status"] in ("generating", "queued") or



                (q["status"] == "pending" and q["id"] != "shot_1")



                for q in state.get("queue", [])



            ):



                return True



            # Never lose a completed video that was not saved by FlowKit.



            finished = [q for q in state.get("queue", []) if q.get("has_video") or q.get("has_image")]



            if finished:



                from common import OUTPUTS



                jobs = Store(STATE / "jobs.sqlite").list(10000)



                for shot in finished:



                    saved = any(



                        j["provider"] == "webtool" and j["state"] == "succeeded"



                        and j.get("remote", {}).get("shot_id") == shot["id"]



                        and any(a.get("name") == ("scene.png" if shot.get("has_image") else "video.mp4") and



                            (OUTPUTS / j["id"] / a["name"]).is_file() and



                            (OUTPUTS / j["id"] / a["name"]).stat().st_size == a.get("bytes")



                            for a in j.get("artifacts", []))



                        for j in jobs



                    )



                    if not saved:



                        return True



        return False



    except Exception:



        return True











def _stop_guard():



    """Stop only the FlowKit tray/window guard. Never stop unrelated tools."""



    pid_file = STATE / "flow_window" / "guard.pid"



    if not pid_file.exists():



        return



    try:



        pid = int(pid_file.read_text(encoding="utf-8").strip())



    except (ValueError,OSError):



        return



    # The pid file is untrusted; double-check the exact project path and process.



    expected_path = str(ROOT / "app" / "flow_window_guard.ps1").replace("'", "''")



    ps = (f"$p=Get-CimInstance Win32_Process -Filter 'ProcessId={pid}';"



          f"if($p -and $p.Name -eq 'powershell.exe' -and "



          f"$p.CommandLine -like '*{expected_path}*' "



          f"-and $p.CommandLine -like '*-BrowserProfile*'){{Stop-Process -Id {pid} -Force; 'STOPPED'}}")



    result = subprocess.run(["powershell.exe", "-WindowStyle", "Hidden", "-NoProfile", "-NonInteractive", "-Command", ps],



                            capture_output=True, text=True, timeout=9, creationflags=0x08000000)



    if "STOPPED" in result.stdout:



        pid_file.unlink(missing_ok=True)











def begin_use():



    global _LEASES, _LAST_ACTIVITY



    with _LOCK:



        _LEASES += 1



        _LAST_ACTIVITY = time.monotonic()











def end_use():



    global _LEASES, _LAST_ACTIVITY



    with _LOCK:



        _LEASES = max(0, _LEASES - 1)



        _LAST_ACTIVITY = time.monotonic()











def ensure_browser(provider="webtool"):



    """Call for an actual claimed media job; never during script writing."""



    global _LAST_ACTIVITY



    with _LOCK:



        _LAST_ACTIVITY = time.monotonic()



        from flow_browser import open_browser



        open_browser(show=False)



        if not _chrome_active():



            raise BrowserBusy("CHROME_DID_NOT_START")



        last_error = None



        for attempt in range(24):



            try:



                _normalize_restored_tabs()



                if provider == "webtool":



                    from flow_webtool_direct import WebToolAdapter



                    WebToolAdapter("hidden").status()



                return True



            except Exception as error:



                last_error = str(error)



                time.sleep(2)



        raise BrowserBusy("WEBTOOL_NOT_READY_AFTER_COLD_START: " + str(last_error))











def status():



    cfg = settings()



    with _LOCK:



        active, blocked_unresolved = _pending_jobs()



        all_unresolved = sum(1 for j in Store(STATE / "jobs.sqlite").list(10000)



            if j["provider"] in _ACTIVE_PROVIDERS and j["state"] == "recovery_needed")



        running = _chrome_active()



        _, profile, port = _machine()



        idle = max(0, round(time.monotonic() - _LAST_ACTIVITY))



        return {



            "mode": cfg.get("browser_mode", "on_demand"),



            "browser_running": running,



            "chrome_debug_port": port,



            "webtool_url": cfg.get("flow_hidden_webtool_url"),



            "active_jobs": active,



            "unresolved_jobs": all_unresolved,



            "browser_blocking_unresolved_jobs": blocked_unresolved,



            "parked_for_review_jobs": all_unresolved - blocked_unresolved,



            "worker_leases": _LEASES,



            "idle_seconds": idle,



            "idle_close_seconds": int(cfg.get("browser_idle_close_seconds", 90)),



            "manual_login_unlocked": (STATE / "flow_window" / "unlock.flag").exists(),



            "last_lifecycle_error": last_error(),



            "policy": {



                "scriptwriting": "Chrome/Web Tool not required",



                "production": "Open hidden Chrome on first claimed job",



                "rendering": "Keep same browser and tab until output is verified",



                "finished": "Close only when all media jobs are safe and idle timeout expires",



                "recovery": "Do not automatically resubmit an unknown remote outcome"



            }



        }











def close_if_safe(force=False):



    """May be called by an idle task or an explicit authorized user action."""



    global _LAST_ACTIVITY



    with _LOCK:



        cfg = settings()



        if cfg.get("browser_mode","on_demand") != "on_demand":



            return {"closed":False,"reason":"NOT_ON_DEMAND"}



        if _LEASES:



            return {"closed":False,"reason":"WORKER_USING_BROWSER"}



        active, unresolved = _pending_jobs()



        if active or unresolved:



            return {"closed":False,"reason":"JOBS_ACTIVE_OR_RECOVERY_NEEDED",



                    "active_jobs":active,"unresolved_jobs":unresolved}



        if (STATE/"flow_window"/"unlock.flag").exists():



            return {"closed":False,"reason":"LOGIN_WINDOW_UNLOCKED"}



        idle_limit = max(30, int(cfg.get("browser_idle_close_seconds",90)))



        if not force and (time.monotonic()-_LAST_ACTIVITY)<idle_limit:



            return {"closed":False,"reason":"WAITING_IDLE_TIMEOUT"}



        if not _chrome_active():



            # Old on-demand guard should never launch a missing browser.



            return {"closed":True,"reason":"ALREADY_STOPPED"}



        if _webtool_busy():



            return {"closed":False,"reason":"WEBTOOL_RENDER_ACTIVE_OR_UNKNOWN"}



        if not _owns_debug_port():



            return {"closed":False,"reason":"CHROME_PROFILE_OWNERSHIP_UNVERIFIED"}



        # Shut down guard before browser, to prevent the old running guard



        # from re-opening Chrome during the transition to on-demand.



        _stop_guard()



        _, _, port = _machine()



        version = _debug(port)



        if not version:



            return {"closed":True,"reason":"ALREADY_STOPPED"}



        from websockets.sync.client import connect



        try:



            with connect(version["webSocketDebuggerUrl"],open_timeout=5) as ws:



                ws.send(json.dumps({"id":1,"method":"Browser.close"}))



        except Exception:



            pass  # Chrome typically closes its CDP socket before replying.



        for _ in range(15):



            if not _chrome_active():



                _LAST_ACTIVITY=time.monotonic()



                return {"closed":True,"reason":"IDLE_SHUTDOWN"}



            time.sleep(.3)



        return {"closed":False,"reason":"BROWSER_CLOSE_NOT_CONFIRMED"}











def _normalize_restored_tabs():



    """Cold Chrome can restore an old Web Tool tab AND open an identical new tab.







    Keep exactly one only if EVERY duplicate is idle and its Bridge responds.



    Never kill a tab with a generating or unknown production state.



    """



    from websockets.sync.client import connect



    from flow_webtool_direct import _cdp, _evaluate



    cfg = settings()



    target = cfg.get("flow_hidden_webtool_url")



    if not target:



        return



    _,_,port = _machine()



    base = f"http://127.0.0.1:{port}"



    with urllib.request.urlopen(base + "/json",timeout=4) as resp:



        tabs = json.load(resp)



    duplicates = [p for p in tabs if p.get("type")=="page" and p.get("url")==target]



    if len(duplicates)<2:



        return



    if (STATE/"flow_window"/"unlock.flag").exists():



        raise BrowserBusy("DUPLICATE_WEBTOOLS_LOGIN_UNLOCKED")



    with urllib.request.urlopen(base + "/json/version",timeout=4) as resp:



        browser = json.load(resp)



    with connect(browser["webSocketDebuggerUrl"],open_timeout=5) as ws:



        infos = _cdp(ws,1,"Target.getTargets").get("targetInfos",[])



    snapshots = []



    for tab in duplicates:



        children = [t["targetId"] for t in infos if t.get("type")=="iframe"



                    and t.get("parentFrameId")==tab["id"]]



        apps = [p for p in tabs if p.get("id") in children



                and "usercontent.goog" in p.get("url","")]



        found = None



        for app in apps:



            try:



                with connect(app["webSocketDebuggerUrl"],open_timeout=5) as ws:



                    value = _evaluate(ws,3,r"""(()=>{let b=window.__STORYBOARD_MCP__;



                     return b?{processing:!!b.isProcessing,



                       items:b.queue?.map(x=>({id:String(x.id),status:x.status,



                         hasVideo:!!x.rawBase64}))||[],



                       statuses:b.queue?.map(x=>x.status)||[],



                       completed:b.queue?.filter(x=>x.status==='completed'&&!!x.rawBase64).length||0}:null})()""")



                if value:



                    found=value



                    break



            except Exception:



                continue



        if found is None or found["processing"] or any(



            s in ("generating","queued") for s in found["statuses"]):



            raise BrowserBusy("DUPLICATE_WEBTOOL_STATE_UNKNOWN_OR_ACTIVE")



        snapshots.append((tab,found))



    # Never discard distinct queued work or unique completed assets.



    snapshots.sort(key=lambda a:(a[1]["completed"],len(a[1]["items"])),reverse=True)



    keeper_items = {q["id"]:q for q in snapshots[0][1]["items"]}



    for _, snapshot in snapshots[1:]:



        for shot in snapshot["items"]:



            retained = keeper_items.get(shot["id"])



            if not retained:



                raise BrowserBusy("DUPLICATE_TAB_HAS_UNIQUE_UNSAVED_SHOT")



            if shot["status"] == "completed" and shot["hasVideo"] and (



                retained["status"] != "completed" or not retained["hasVideo"]



            ):



                raise BrowserBusy("DUPLICATE_TAB_HAS_UNIQUE_COMPLETED_VIDEO")



            if shot["status"] == "pending" and retained["status"] not in ("pending", "completed"):



                raise BrowserBusy("DUPLICATE_TAB_HAS_UNRESOLVED_PENDING_SHOT")



    keep = snapshots[0][0]["id"]



    with connect(browser["webSocketDebuggerUrl"],open_timeout=5) as ws:



        for number,(tab,_) in enumerate(snapshots[1:],10):



            if tab["id"]==keep:



                continue



            result = _cdp(ws,number,"Target.closeTarget",{"targetId":tab["id"]})



            if not result.get("success"):



                raise BrowserBusy("WEBTOOL_DUPLICATE_TAB_CLOSE_FAILED")











def record_error(reason):



    """Persist diagnostic *class name only*: no cookies, tokens, prompts or URLs."""



    from common import atomic



    clean="".join(c for c in str(reason) if c.isalnum() or c in "_-")[:96]



    try:



        atomic(STATE/"browser_last_error.json",{"error":clean or "UNKNOWN","at":time.time()})



    except OSError:



        pass











def last_error():



    p=STATE/"browser_last_error.json"



    if not p.is_file():



        return None



    try:



        return json.loads(p.read_text(encoding="utf-8"))



    except (ValueError,OSError):



        return {"error":"ERROR_RECORD_UNREADABLE"}



