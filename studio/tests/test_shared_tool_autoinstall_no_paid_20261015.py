"""Zero-credit regression for auto-installing a real Google Flow shared Web Tool."""
from __future__ import annotations
import json
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from studio_mcp import accounts as _test_accounts
_test_auth_guard=patch.object(_test_accounts,"flow_auth_status",return_value={"authenticated":True,"auth_state":"AUTHENTICATED"})
_test_auth_guard.start()
from studio_mcp import auto_flow_manager as m
from studio_mcp import shared_tool_install as si
from studio_mcp.accounts import bundled_shared_tool_url
from studio_mcp.projects import project_url

TOOL="69da86fb-6c79-43d2-a387-ef47b0fda4db"
PROJECT="0a0fa44c-faab-435e-95c5-0265c89866c2"
assert bundled_shared_tool_url()==f"https://flow.google.com/shared/tool/{TOOL}"
print("VERIFIED_BUNDLED_SHARE_ID_PASS",flush=True)

with TemporaryDirectory(prefix="storyboard_shared_install_test_") as tmp:
    acc={"id":"unit_account","cdp_port":9460,"state_dir":tmp}
    db={"version":1,"active":None,"genres":{},"projects":[]}
    with patch.object(m,"verify_v2_baseline",return_value={"verified":True}),\
         patch.object(m,"any_running_production",return_value=False),\
         patch.object(m,"load",return_value=db),\
         patch.object(m,"connection_check",return_value={"connected":True}),\
         patch.object(m,"_pid_browser_for_account",return_value=1111),\
         patch.object(m,"tabs",return_value=[]),\
         patch.object(m,"unresolved_jobs",return_value=9),\
         patch.object(m,"register") as register,\
         patch.object(si,"install",return_value={
             "project_id":PROJECT,"tool_id":TOOL,"verified":True,
             "tool_url":project_url(PROJECT,TOOL),
         }) as install:
        result=m.ensure_ready("auto",account=acc)
        assert result["ready"] and result["code"]=="AUTO_FLOW_SHARED_TOOL_INSTALLED",result
        assert result["uncertain_receipts"]==9
        install.assert_called_once_with(acc)
        register.assert_called_once_with(acc,PROJECT+":"+TOOL,"Storyboard Director AI tự cài","auto")
        print("FIRST_ACCOUNT_AUTO_INSTALL_ROUTING_PASS",flush=True)
    m._READY_AT=0
    with patch.object(m,"verify_v2_baseline",return_value={"verified":True}),\
         patch.object(m,"any_running_production",return_value=False),\
         patch.object(m,"load",return_value=db),\
         patch.object(m,"connection_check",return_value={"connected":True}),\
         patch.object(m,"_pid_browser_for_account",return_value=1111),\
         patch.object(m,"tabs",return_value=[]),\
         patch.object(m,"unresolved_jobs",return_value=9),\
         patch.object(m,"register") as reg,\
         patch.object(si,"install",side_effect=si.SharedToolInstallError(
             "SHARED_INSTALL_V2_NATIVE_BRIDGE_NOT_READY")):
        result=m.ensure_ready("auto",account=acc)
        assert not result["ready"],result
        assert not reg.called
        print("INCOMPATIBLE_SHARED_TOOL_NEVER_REGISTERED_PASS",flush=True)
    # The Node worker has to fail before opening a browser or creating
    # a duplicate when the preceding project creation was uncertain.
    receipt=Path(tmp)/"auto_flow_shared_install.json"
    receipt.write_text(json.dumps({
        "state":"create_requested","tool_id":TOOL,
        "initiated_at":"2026-10-15T00:00:00Z"
    }),encoding="utf-8")
    node=Path(r"D:\STORYBOARD_AI\studio\studio_mcp\node")
    proc=subprocess.run([str(node/"node.exe"),str(node/"auto-flow-shared-install.mjs")],
        input=json.dumps({"port":9460,"share_url":bundled_shared_tool_url(),
                          "receipt_path":str(receipt),"reuse_project_id":""}),
        capture_output=True,text=True,encoding="utf-8",errors="replace",
        timeout=20,cwd=str(node))
    payload=json.loads(proc.stdout.strip().splitlines()[-1])
    assert proc.returncode!=0 and (
       payload.get("code")=="SHARED_INSTALL_REMOTE_CREATE_UNCERTAIN_NO_RETRY"),payload
    assert json.loads(receipt.read_text())["state"]=="create_requested"
    print("NO_DUPLICATE_REMOTE_PROJECT_AFTER_UNCERTAIN_CREATION_PASS",flush=True)

with patch("studio_mcp.accounts.find_account",return_value={"id":"unit_account"}),\
     patch("studio_mcp.accounts.connection_check",return_value={"connected":False}):
    m._CURRENT.update({"status":"READY","code":"AUTO_FLOW_READY",
                       "ready":True,"account_id":"unit_account"})
    snap=m.status()
    assert not snap["ready"] and snap["code"]=="AUTO_FLOW_CHROME_DISCONNECTED"
    print("NO_STALE_READY_WHEN_CHROME_DISCONNECTS_PASS",flush=True)

print("SHARED_TOOL_AUTO_INSTALL_NO_PAID_REGRESSION_PASS",flush=True)
