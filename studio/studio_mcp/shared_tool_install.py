"""First-use installation of a verified shared Flow Tool in a Studio-owned account.

Uses real Google Flow UI: shared Tool -> choose known/new project -> Open.
Never reads credentials, spends image credits or touches the legacy V2 tree.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

from .accounts import (
    _pid_browser_for_account, any_running_production,
    bundled_shared_tool_url, connection_check,
)
from .transport import NODE, _isolated
from .v2_baseline import verify_v2_baseline


class SharedToolInstallError(RuntimeError):
    pass


def install(account, *, reuse_project_id=None, timeout=140):
    """Return only a project/tool pair VERIFIED through the private Chrome bridge.

    When reuse_project_id is None the Node worker creates at most ONE dedicated
    project, with a durable create_requested journal written before the click.
    A retry is allowed only after the project ID was recorded.
    """
    _isolated(account)
    verify_v2_baseline()
    if any_running_production():
        raise SharedToolInstallError("SHARED_INSTALL_PRODUCTION_BUSY")
    if not _pid_browser_for_account(account):
        raise SharedToolInstallError("SHARED_INSTALL_ACCOUNT_CHROME_REQUIRED")
    if connection_check(account["id"]).get("connected") is not True:
        raise SharedToolInstallError("SHARED_INSTALL_ACCOUNT_CDP_REQUIRED")
    if reuse_project_id is not None and not re.fullmatch(
            r"[a-fA-F0-9-]{36}", str(reuse_project_id)):
        raise SharedToolInstallError("SHARED_INSTALL_REUSE_ID_INVALID")
    share=bundled_shared_tool_url()
    tool_id=urlsplit(share).path.rsplit("/", 1)[-1].lower()
    journal=Path(account["state_dir"])/"auto_flow_shared_install.json"
    worker=NODE/"auto-flow-shared-install.mjs"
    node=NODE/("node.exe" if os.name=="nt" else "node")
    if not worker.is_file() or not node.is_file():
        raise SharedToolInstallError("SHARED_INSTALL_COMPONENT_MISSING")
    request={
        "port":account["cdp_port"],
        "share_url":share,
        "receipt_path":str(journal),
        "reuse_project_id":str(reuse_project_id or ""),
    }
    try:
        done=subprocess.run(
            [str(node), str(worker)], input=json.dumps(request),
            cwd=str(NODE), encoding="utf-8", errors="replace", text=True,
            capture_output=True, timeout=timeout,
            creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0),
        )
        payload=json.loads(done.stdout.strip().splitlines()[-1])
    except (OSError,subprocess.TimeoutExpired,ValueError,IndexError) as exc:
        raise SharedToolInstallError(
            "SHARED_INSTALL_REMOTE_UNCERTAIN_CHECK_JOURNAL") from exc
    if done.returncode or payload.get("verified") is not True:
        raise SharedToolInstallError(
            str(payload.get("code") or "SHARED_INSTALL_BRIDGE_NOT_VERIFIED"))
    from .projects import project_url
    expected=project_url(payload["project_id"],tool_id)
    if payload.get("tool_id")!=tool_id or payload.get("tool_url")!=expected:
        raise SharedToolInstallError("SHARED_INSTALL_IDENTITY_MISMATCH")
    return {"project_id":payload["project_id"],"tool_id":tool_id,
            "tool_url":expected,"verified":True}
