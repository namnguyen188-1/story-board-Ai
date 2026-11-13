"""Pin each worker to the existing Google Flow tab; keep it open on release."""
from __future__ import annotations
import json,os,re,subprocess
from .accounts import _pid_browser_for_account
from .transport import _isolated,NODE
class ProductionTabError(RuntimeError):pass
EXE=NODE/("node.exe" if os.name=="nt" else "node")
SCRIPT=NODE/"production-job-tab.mjs"
def _call(account,url,action,target=None,*,timeout=75):
    _isolated(account)
    if not _pid_browser_for_account(account):
        raise ProductionTabError("FLOW_JOB_SESSION_CHROME_NOT_OWNED")
    if not EXE.is_file() or not SCRIPT.is_file():
        raise ProductionTabError("FLOW_JOB_SESSION_ADAPTER_MISSING")
    req={"account_id":account["id"],"action":action,"port":account["cdp_port"],"tool_url":url,"state_dir":account["state_dir"]}
    if target is not None:
        if not re.fullmatch(r"[a-fA-F0-9]{32}",target):
            raise ProductionTabError("FLOW_JOB_SESSION_TARGET_INVALID")
        req["target_id"]=target
    try:
        p=subprocess.run([str(EXE),str(SCRIPT)],input=json.dumps(req),
           text=True,capture_output=True,encoding="utf-8",errors="replace",
           cwd=str(NODE),timeout=timeout,
           creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        result=json.loads(p.stdout.strip().splitlines()[-1])
    except (OSError,subprocess.TimeoutExpired,IndexError,ValueError) as exc:
        raise ProductionTabError("FLOW_JOB_SESSION_BROWSER_UNAVAILABLE") from exc
    if p.returncode or result.get("ok") is not True:
        raise ProductionTabError(str(result.get("code") or "FLOW_JOB_SESSION_FAILED"))
    return result
def prepare(account,url):
    from .projects import exact_tool_tab_count,is_registered
    if not is_registered(account,url) or exact_tool_tab_count(account,url)!=1:
        raise ProductionTabError("FLOW_JOB_SESSION_ORIGINAL_TOOL_NOT_OPEN")
    target_id = _call(account,url,"create")["target_id"]
    try:
        from studio_flow_accounts import minimize_active_account_browser
        minimize_active_account_browser()
    except Exception:
        pass
    return target_id
def close_completed(account,url,target):
    return _call(account,url,"close",target,timeout=35)

def abandon_fresh(account,url,target):
    """Release a fresh borrowed session without closing the original tab."""
    return _call(account,url,"abandon",target,timeout=35)
