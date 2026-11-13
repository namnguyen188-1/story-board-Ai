"""Auto Flow Manager for Storyboard AI (never reads or changes V2).

Reusable account-owned Chrome profiles, V2-compatible app discovery, and
explicit safe recovery. No paid image/video request or Google auth bypass.
"""
from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime,timezone
from pathlib import Path

from .accounts import (AccountError, active_account, connection_check, _pid_browser_for_account,
                       _atomic_store, any_running_production)
from .projects import (load, tabs, project_url, probe_v2_compatible_tool,
                       choose, register, exact_tool_tab_count, cleanup_duplicate_tool_tabs, ProjectError)
from .v2_baseline import verify_v2_baseline, BaselineDriftError

_LOCK=threading.RLock()
_READY_AT=0.0
_CURRENT={"status":"WAITING","code":"AUTO_FLOW_NOT_RUN","ready":False,
          "account_id":None,"project_id":None}
_UNCERTAIN_STATES={"submit_uncertain","submitted_uncertain"}

def _set(account,code,ready=False,project_id=None,detail="",**extra):
    result={"status":"READY" if ready else "ACTION_REQUIRED",
            "code":code,"ready":bool(ready),
            "account_id":account["id"],"project_id":project_id,
            "detail":detail[:150],
            "updated_utc":datetime.now(timezone.utc).isoformat(),**extra}
    global _READY_AT
    _CURRENT.clear()
    _CURRENT.update(result)
    _READY_AT=time.monotonic() if ready else 0.0
    # Store only benign connection state. Never cookies, prompts or credentials.
    _atomic_store(Path(account["state_dir"])/"auto_flow_status.json",result)
    if ready and project_id:
        # Keep a last-known-good tool identity even if a later outage changes
        # auto_flow_status to ACTION_REQUIRED. IDs only; no session secrets.
        _atomic_store(Path(account["state_dir"])/"auto_flow_last_verified.json",
            {"account_id":account["id"],"project_id":project_id,
             "verified_utc":result["updated_utc"]})
    return dict(result)

def status():
    """Never show a cached READY when its own Chrome CDP went offline."""
    if any_running_production():
        try:
            account=active_account()
            data=load(account)
            return {"status":"READY","code":"AUTO_FLOW_PRODUCTION_BUSY","ready":True,
                    "account_id":account.get("id"),"project_id":data.get("active"),
                    "detail":"Đang sản xuất; Web Tool đang hoạt động ổn định.",
                    "updated_utc":datetime.now(timezone.utc).isoformat()}
        except Exception:
            pass
    snapshot=dict(_CURRENT)
    if not snapshot.get("account_id") or not snapshot.get("ready"):
        try:
            account=active_account()
            disk_p=Path(account["state_dir"])/"auto_flow_status.json"
            if disk_p.is_file():
                disk_data=json.loads(disk_p.read_text(encoding="utf-8"))
                if disk_data.get("account_id")==account.get("id"):
                    snapshot=disk_data
        except Exception:
            pass
    if snapshot.get("ready"):
        from .accounts import find_account,connection_check,flow_auth_status
        try:
            account=find_account(snapshot.get("account_id"))
            healthy=bool(account and connection_check(account["id"]).get("connected"))
            authentication=(flow_auth_status(account) if healthy else
                            {"authenticated":False,"auth_state":"CHROME_DISCONNECTED"})
        except (OSError,ValueError,TypeError):
            healthy=False
            authentication={"authenticated":False,"auth_state":"CHECK_FAILED"}
        if not healthy:
            return {**snapshot,"ready":False,"status":"ACTION_REQUIRED",
                    "code":"AUTO_FLOW_CHROME_DISCONNECTED",
                    "detail":"Chrome Google Flow đã ngắt; cần tự kết nối lại."}
        if not authentication.get("authenticated"):
            return {**snapshot,"ready":False,"status":"ACTION_REQUIRED",
                    "code":"AUTO_FLOW_LOGIN_REQUIRED",
                    "detail":"Cần xác minh đăng nhập Google Flow; Chrome/CDP chưa đủ."}
        if authentication.get("transient_retry"):
            snapshot["transient_retry"] = authentication["transient_retry"]
        try:
            from .accounts import manual_login_active
            if manual_login_active(account_id=account["id"]):
                login_auto_finish_once()
        except Exception:
            pass
    return snapshot

def unresolved_jobs(root=None):
    """Report count only; never resubmit a job with uncertain remote receipt."""
    root=Path(root) if root else Path(__file__).resolve().parent.parent
    files=(root/"runtime"/"private_mcp_outputs").glob(
        "*/.storyboard_image_jobs/*.json")
    count=0
    for file in files:
        try:
            if json.loads(file.read_text(encoding="utf-8")).get("state") in _UNCERTAIN_STATES:
                count+=1
        except (OSError,ValueError,TypeError):
            continue
    return count

def _attempt(account, genre="auto", *, allow_open=True):
    from studio_flow_accounts import open_project,open_login
    from .projects import selected
    # Fail closed if runtime differs from pinned V2 or production already active.
    verify_v2_baseline()
    data=load(account)
    if any_running_production():
        return _set(account,"AUTO_FLOW_PRODUCTION_BUSY",ready=False,
                    project_id=data.get("active") or _CURRENT.get("project_id"),
                    detail="Đang sản xuất; Web Tool đang hoạt động ổn định.")
    from .accounts import flow_auth_status
    has_chrome = bool(connection_check(account["id"]).get("connected") and _pid_browser_for_account(account))
    if has_chrome:
        login=flow_auth_status(account)
        if not login.get("authenticated"):
            return _set(account,"AUTO_FLOW_LOGIN_REQUIRED",
                        detail="Chrome đang chờ đăng nhập Google Flow hoặc xác minh lại.",
                        uncertain_receipts=unresolved_jobs())
    elif not allow_open:
        return _set(account,"AUTO_FLOW_CHROME_DISCONNECTED",
                    detail="Chrome Google Flow chưa mở; hãy bấm Đăng nhập / Hiện Google Flow.",
                    uncertain_receipts=unresolved_jobs())
    prefer=data["genres"].get(genre) if genre!="auto" else None
    candidate_errors=[]
    uncertain=unresolved_jobs()

    # Pass 1: Check if ANY registered project is ALREADY OPEN in Chrome tabs (0 windows opened).
    choices=[]
    for ref in (prefer,data["active"],*[p["id"] for p in data["projects"]]):
        if ref and ref not in choices:
            choices.append(ref)
    for ref in choices:
        entry=next((p for p in data["projects"] if p["id"]==ref),None)
        if entry is None:continue
        url=project_url(entry["project_id"],entry["tool_id"])
        c=exact_tool_tab_count(account,url)
        if c>1:
            cleanup_duplicate_tool_tabs(account,url)
            c=exact_tool_tab_count(account,url)
        if c==1:
            try:
                probe_v2_compatible_tool(account,ref,timeout=30)
                if data["active"]!=ref or (genre not in ("auto",None)
                    and data["genres"].get(genre)!=ref):
                    choose(account,ref,genre if genre!="auto" else None)
                pid=_pid_browser_for_account(account)
                if pid:
                    from studio_flow_accounts import minimize_chrome_window
                    minimize_chrome_window(pid)
                return _set(account,"AUTO_FLOW_READY",True,ref,
                            "Web Tool tương thích MCP V2 đã xác minh.",
                            uncertain_receipts=unresolved_jobs())
            except Exception as exc:
                candidate_errors.append(type(exc).__name__+":"+str(exc)[:65])

    # Pass 2: Discover a compatible Tool already open in THIS account, without
    # registering unrelated Flow tools or guessing a tool ID from a URL.
    if connection_check(account["id"]).get("connected") and _pid_browser_for_account(account):
        known={p["id"] for p in data["projects"]}
        for tab in tabs(account):
            ref=tab["id"]
            u=project_url(tab["project_id"],tab["tool_id"])
            c=exact_tool_tab_count(account,u)
            if c>1:
                cleanup_duplicate_tool_tabs(account,u)
                c=exact_tool_tab_count(account,u)
            if ref in known or c!=1:
                continue
            try:
                probe_v2_compatible_tool(account,ref,timeout=30)
                register(account,ref,"Web Tool V2 tự xác minh",genre if genre!="auto" else "auto")
                return _set(account,"AUTO_FLOW_DISCOVERED_COMPATIBLE_TOOL",True,ref,
                            "Đã xác minh và liên kết Web Tool đang mở.",
                            uncertain_receipts=unresolved_jobs())
            except Exception as exc:
                candidate_errors.append(type(exc).__name__+":"+str(exc)[:65])

    # Pass 3: If allow_open is True, open EXACTLY ONE single target project (never loop and open multiple!).
    if allow_open:
        target_ref = prefer or data.get("active") or (data["projects"][0]["id"] if data.get("projects") else None)
        if target_ref:
            entry = next((p for p in data["projects"] if p["id"]==target_ref),None)
            if entry is not None:
                url = project_url(entry["project_id"],entry["tool_id"])
                try:
                    c=exact_tool_tab_count(account,url)
                    if c>1:
                        cleanup_duplicate_tool_tabs(account,url)
                        c=exact_tool_tab_count(account,url)
                    if c<1:
                        open_project(account,target_ref)
                        c=exact_tool_tab_count(account,url)
                    if c==1:
                        probe_v2_compatible_tool(account,target_ref,timeout=30)
                        if data["active"]!=target_ref or (genre not in ("auto",None)
                            and data["genres"].get(genre)!=target_ref):
                            choose(account,target_ref,genre if genre!="auto" else None)
                        pid=_pid_browser_for_account(account)
                        if pid:
                            from studio_flow_accounts import minimize_chrome_window
                            minimize_chrome_window(pid)
                        return _set(account,"AUTO_FLOW_READY",True,target_ref,
                            "Web Tool tương thích MCP V2 đã xác minh.",
                            uncertain_receipts=unresolved_jobs())
                except Exception as exc:
                    candidate_errors.append(type(exc).__name__+":"+str(exc)[:65])

    # Pass 4: Cold-start or outdated account: install the verified public Web Tool
    # through the official Google Flow Share -> Project -> Open UI.
    # Runs when no compatible project is ready, even if legacy projects exist.
    if (allow_open and
            connection_check(account["id"]).get("connected") and
            _pid_browser_for_account(account)):
        try:
            from .shared_tool_install import install,SharedToolInstallError
            reuse_id = None
            target_ref = prefer or data.get("active") or (data["projects"][0]["id"] if data.get("projects") else None)
            if target_ref and ":" in target_ref:
                reuse_id = target_ref.split(":")[0]
            deployed = install(account, reuse_project_id=reuse_id) if reuse_id else install(account)
            ref=deployed["project_id"]+":"+deployed["tool_id"]
            register(account,ref,"Storyboard Director AI tự cài",
                     genre if genre!="auto" else "auto")
            return _set(account,"AUTO_FLOW_SHARED_TOOL_INSTALLED",True,ref,
                        "Đã mở Web Tool chia sẻ và xác minh MCP trong dự án riêng.",
                        uncertain_receipts=unresolved_jobs())
        except Exception as exc:
            code=str(exc)[:105]
            candidate_errors.append("SHARED_INSTALL:"+code)
            if ("SHARED_INSTALL_SIGNIN_OR_PROJECT_CREATE_REQUIRED" in code or
                    "SHARED_INSTALL_ACCOUNT_CHROME_REQUIRED" in code):
                return _set(account,"AUTO_FLOW_LOGIN_REQUIRED",
                            detail="Google Flow cần người dùng đăng nhập tài khoản Chrome riêng.")
            if ("SHARED_INSTALL_REMOTE_CREATE_UNCERTAIN" in code or
                    "SHARED_INSTALL_CREATE_RESULT_UNCERTAIN" in code):
                return _set(account,"AUTO_FLOW_SHARED_CREATE_UNCERTAIN",
                            detail="Chưa chắc Google đã tạo dự án; không tự tạo lần hai.")

            # Never label an incompatible shared Web Tool as READY.
    # Last resort: create ONE new Google Flow project only from a previously
    # verified Tool ID. The new project MUST pass the native V2 image bridge
    # probe before registration. Durable receipts block duplicate creation.
    if (allow_open and connection_check(account["id"]).get("connected")
            and _pid_browser_for_account(account)):
        prior=Path(account["state_dir"])/"auto_flow_last_verified.json"
        try:
            historical=json.loads(prior.read_text(encoding="utf-8"))
            earlier_ref=historical.get("project_id")
            source=next((p for p in data["projects"] if p["id"]==earlier_ref),None)
            if historical.get("account_id")==account["id"] and source:
                from .auto_project_provision import provision,AutoProjectProvisionError
                if len(data["projects"])>=48:
                    raise ProjectError("FLOW_PROJECT_LIMIT")
                result=provision(account,source["tool_id"])
                ref=result["project_id"]+":"+result["tool_id"]
                registered=register(account,ref,"Auto Flow - dự án tự tạo",
                                    genre if genre!="auto" else "auto")
                return _set(account,"AUTO_FLOW_NEW_PROJECT_CREATED",True,ref,
                            "Đã tạo và xác minh dự án Google Flow tương thích V2.",
                            uncertain_receipts=unresolved_jobs())
        except Exception as exc:
            candidate_errors.append("PROVISION:"+str(exc)[:90])
    if not connection_check(account["id"]).get("connected"):
        return _set(account,"AUTO_FLOW_LOGIN_REQUIRED",
                    detail="Mở Chrome Google Flow riêng và đăng nhập nếu được yêu cầu.",
                    uncertain_receipts=unresolved_jobs())
    return _set(account,"AUTO_FLOW_COMPATIBLE_TOOL_REQUIRED",
                detail="Không tìm thấy Web Tool có cầu nối MCP V2 đã xác minh.",
                uncertain_receipts=unresolved_jobs(),
                checked_projects=len(choices),
                checked_candidates=len(candidate_errors))

def ensure_ready(genre="auto", *, allow_open=True, account=None):
    """Idempotent connection resolver; no paid calls or image-queue resets."""
    account=account or active_account()
    if not _LOCK.acquire(timeout=55):
        return {**status(),"code":"AUTO_FLOW_CHECK_IN_PROGRESS","ready":False}
    try:
        # Fast verified reuse during consecutive productions. The new
        # per-production tab is independently checked for SDK/queue readiness.
        from .accounts import flow_auth_status
        if (_CURRENT.get("ready") and _CURRENT.get("account_id")==account["id"] and
                flow_auth_status(account).get("authenticated") and
                _READY_AT and time.monotonic()-_READY_AT<240 and
                not any_running_production()):
            ref=_CURRENT.get("project_id")
            data=load(account)
            if (genre=="auto" or data["genres"].get(genre)==ref) and ref and any(
                p["id"]==ref for p in data["projects"]):
                from .projects import project_url
                p=next(p for p in data["projects"] if p["id"]==ref)
                url=project_url(p["project_id"],p["tool_id"])
                c=exact_tool_tab_count(account,url)
                if c>1:
                    cleanup_duplicate_tool_tabs(account,url)
                    c=exact_tool_tab_count(account,url)
                if c==1:
                    verify_v2_baseline()
                    return dict(_CURRENT)
        return _attempt(account,genre,allow_open=allow_open)
    except (BaselineDriftError,ProjectError,AccountError,ValueError,OSError) as exc:
        return _set(account,"AUTO_FLOW_SAFETY_BLOCKED",detail=str(exc))
    except Exception as exc:
        return _set(account,"AUTO_FLOW_CHECK_FAILED",detail=type(exc).__name__)
    finally:
        try:
            _LOCK.release()
        except RuntimeError:
            pass

def boot_once():
    """Called in background when the Studio server starts, never as a paid task."""
    try:
        time.sleep(1.2)  # allow HTTP status server to start accepting connections
        account = active_account()
        has_chrome = bool(connection_check(account["id"]).get("connected") and _pid_browser_for_account(account))
        if not has_chrome:
            print("[AUTO_FLOW] Tự động bật Chrome Google Flow ngầm khi mở Studio...", flush=True)
            ensure_ready("auto", allow_open=True, account=account)
        else:
            ensure_ready("auto", allow_open=False, account=account)
    except Exception as exc:
        print(f"[AUTO_FLOW] Khởi động Chrome ngầm thông báo: {exc}", flush=True)

def login_auto_finish_loop():
    """Disabled: FlowKit handles all browser operations directly without loops."""
    return


def login_auto_finish_once(*, allow_unrequested=False):
    """Disabled: FlowKit handles all browser operations directly without loops."""
    return "FLOWKIT_ACTIVE"


def start_bootstrap():
    """Disabled: MCP V2 bootstrap replaced by FlowKit."""
    return None
