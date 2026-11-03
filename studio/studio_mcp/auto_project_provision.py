"""Create at most one new Flow project per verified source, then register its V2 Tool.

No credentials, remote credit actions or implicit job resubmission.
Uncertain project creation is journaled and NEVER automatically retried.
"""
from __future__ import annotations
import json,os,re,subprocess
from datetime import datetime,timezone
from pathlib import Path
from .accounts import _pid_browser_for_account
from .transport import _isolated,NODE

class AutoProjectProvisionError(RuntimeError):
    pass

def _archive_if_registered(account):
    """Only rotate a verified creation journal after its project is registered."""
    receipt=Path(account["state_dir"])/"auto_flow_project_provision.json"
    if not receipt.is_file():
        return
    try:
        data=json.loads(receipt.read_text(encoding="utf-8"))
        ref=data["project_id"]+":"+data["source_tool_id"]
    except (OSError,KeyError,ValueError,TypeError):
        return
    if data.get("state")!="verified":
        return
    from .projects import load
    if not any(p["id"]==ref for p in load(account)["projects"]):
        return
    history=receipt.parent/"auto_flow_project_history"
    history.mkdir(parents=True,exist_ok=True)
    target=history/(data["project_id"]+".json")
    if target.exists():
        raise AutoProjectProvisionError("AUTO_FLOW_PROVISION_HISTORY_CONFLICT")
    from .accounts import _atomic_store
    _atomic_store(receipt,{**data,"state":"registered",
                           "registered_at":datetime.now(timezone.utc).isoformat()})
    os.replace(receipt,target)

def _daily_creation_cap(account):
    """Never proliferate projects when a Flow UI or service is repeatedly failing."""
    history=Path(account["state_dir"])/"auto_flow_project_history"
    recent=0
    for f in history.glob("*.json"):
        try:
            item=json.loads(f.read_text(encoding="utf-8"))
            stamp=item.get("initiated_at") or item.get("verified_at")
            if stamp:
                created=datetime.fromisoformat(stamp.replace("Z","+00:00"))
                if (datetime.now(timezone.utc)-created).total_seconds()<86400:
                    recent+=1
        except (OSError,ValueError,TypeError):
            continue
    if recent>=2:
        raise AutoProjectProvisionError("AUTO_FLOW_PROVISION_DAILY_SAFETY_LIMIT")

def provision(account,tool_id,*,timeout=105):
    _isolated(account)
    _archive_if_registered(account)
    _daily_creation_cap(account)
    if not re.fullmatch(r"[0-9a-fA-F-]{36}",str(tool_id)):
        raise AutoProjectProvisionError("AUTO_FLOW_PROVISION_BAD_TOOL_ID")
    if not _pid_browser_for_account(account):
        raise AutoProjectProvisionError("AUTO_FLOW_PROVISION_LOGIN_REQUIRED")
    receipt=Path(account["state_dir"])/"auto_flow_project_provision.json"
    script=NODE/"auto-flow-provision-project.mjs"
    exe=NODE/("node.exe" if os.name=="nt" else "node")
    if not script.is_file() or not exe.is_file():
        raise AutoProjectProvisionError("AUTO_FLOW_PROVISION_COMPONENT_MISSING")
    try:
        proc=subprocess.run([str(exe),str(script)],
             input=json.dumps({"port":account["cdp_port"],
                 "source_tool_id":tool_id,"receipt_path":str(receipt)}),
             cwd=str(NODE),text=True,encoding="utf-8",errors="replace",
             capture_output=True,timeout=timeout,
             creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        result=json.loads(proc.stdout.strip().splitlines()[-1])
    except (OSError,subprocess.TimeoutExpired,ValueError,IndexError) as exc:
        raise AutoProjectProvisionError("AUTO_FLOW_PROVISION_UNCERTAIN_NO_RETRY") from exc
    if proc.returncode or result.get("ok") is not True:
        raise AutoProjectProvisionError(str(result.get("code") or "AUTO_FLOW_PROVISION_FAILED"))
    if result.get("verified") is not True:
        raise AutoProjectProvisionError("AUTO_FLOW_PROVISION_NOT_VERIFIED")
    from .projects import project_url
    url=project_url(result["project_id"],tool_id)
    if url!=result.get("tool_url"):
        raise AutoProjectProvisionError("AUTO_FLOW_PROVISION_URL_MISMATCH")
    return {"url":url,"project_id":result["project_id"],
            "tool_id":tool_id,"verified":True}
