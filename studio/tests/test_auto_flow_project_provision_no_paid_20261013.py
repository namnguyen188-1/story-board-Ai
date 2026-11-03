"""No-paid tests for automated creation/failover and uncertain creation receipts."""
import sys,os,json,subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
sys.path.insert(0,r"D:\STORYBOARD_AI\studio")
from studio_mcp import accounts as _test_accounts
_test_auth_guard=patch.object(_test_accounts,"flow_auth_status",return_value={"authenticated":True,"auth_state":"AUTHENTICATED"})
_test_auth_guard.start()
from studio_mcp import auto_flow_manager as af
from studio_mcp import auto_project_provision as ap
from studio_mcp import projects
source="7a7f7f89-c38d-4237-b4aa-ba499acd7507:642784b8-d39f-4e7b-b168-fe6218bbc45b"
new_id="1f806e0b-5184-448b-8ab4-eab64ee163f0"
tool_id="642784b8-d39f-4e7b-b168-fe6218bbc45b"
row={"id":"default","state_dir":"","cdp_port":9550}
db={"version":1,"active":source,"genres":{},"projects":[{"id":source,"project_id":source.split(":")[0],
    "tool_id":tool_id,"label":"source","genre":"auto"}]}
with TemporaryDirectory(prefix="autoflow_recovery_unit_") as td:
 row["state_dir"]=td
 (Path(td)/"auto_flow_last_verified.json").write_text(json.dumps({"account_id":"default","project_id":source}))
 def reject(*args,**kwargs):raise projects.ProjectError("FLOW_TOOL_UNAVAILABLE")
 with patch.object(af,"verify_v2_baseline",return_value={"verified":True}),\
    patch.object(af,"any_running_production",return_value=False),\
    patch.object(af,"load",return_value=db),\
    patch.object(af,"exact_tool_tab_count",return_value=1),\
    patch.object(af,"probe_v2_compatible_tool",side_effect=reject),\
    patch.object(af,"connection_check",return_value={"connected":True}),\
    patch.object(af,"_pid_browser_for_account",return_value=42),\
    patch.object(af,"tabs",return_value=[]),\
    patch.object(af,"unresolved_jobs",return_value=2),\
    patch.object(af,"register") as register,\
    patch.object(ap,"provision",return_value={"project_id":new_id,"tool_id":tool_id,"verified":True}) as prov:
    r=af.ensure_ready("auto",account=row)
    assert r["ready"] and r["code"]=="AUTO_FLOW_NEW_PROJECT_CREATED",r
    assert r["project_id"]==new_id+":"+tool_id
    assert r["uncertain_receipts"]==2
    prov.assert_called_once_with(row,tool_id)
    register.assert_called_once()
    print("FAILOVER_CREATES_ONE_VERIFIED_PROJECT_WITHOUT_OLD_JOB_RESUBMIT_PASS",flush=True)
 assert json.loads((Path(td)/"auto_flow_last_verified.json").read_text())["project_id"]==new_id+":"+tool_id
 print("LAST_VERIFIED_TOOL_IDENTITY_PERSISTENCE_PASS",flush=True)
 # Simulate an interrupted create transaction: Node must NEVER click create again.
 receipt=Path(td)/"auto_flow_project_provision.json"
 receipt.write_text(json.dumps({"state":"create_requested","source_tool_id":tool_id}))
 req={"port":9550,"source_tool_id":tool_id,"receipt_path":str(receipt)}
 exe=Path(r"D:\STORYBOARD_AI\studio\studio_mcp\node\node.exe")
 script=exe.parent/"auto-flow-provision-project.mjs"
 run=subprocess.run([str(exe),str(script)],input=json.dumps(req),
      capture_output=True,text=True,timeout=30,cwd=str(exe.parent))
 msg=json.loads(run.stdout.strip().splitlines()[-1])
 assert run.returncode!=0 and msg["code"]=="AUTO_FLOW_PROVISION_REMOTE_UNCERTAIN_NO_RECREATE",msg
 assert json.loads(receipt.read_text())["state"]=="create_requested"
 print("INTERRUPTED_PROJECT_CREATION_NO_AUTOMATIC_DUPLICATE_PASS",flush=True)
 # Daily cap protects Google Flow from accumulating unused projects.
 history=Path(td)/"auto_flow_project_history"
 history.mkdir(exist_ok=True)
 from datetime import datetime,timezone
 for i in range(2):
    (history/(str(i)+".json")).write_text(json.dumps({"initiated_at":datetime.now(timezone.utc).isoformat()}))
 try:ap._daily_creation_cap(row)
 except ap.AutoProjectProvisionError as exc:assert "DAILY_SAFETY_LIMIT" in str(exc)
 else:raise AssertionError("Missing daily creation cap")
 print("MAX_TWO_AUTOMATIC_FLOW_PROJECTS_PER_DAY_GUARD_PASS",flush=True)
print("AUTO_FLOW_PROJECT_CREATE_REGRESSION_NO_PAID_GREEN",flush=True)
