"""No-credit tests: project registration only accepts read-only V2 bridge probe."""
from pathlib import Path
from unittest.mock import patch,MagicMock
import json,sys
root=Path(r"D:\STORYBOARD_AI\studio")
sys.path.insert(0,str(root))
from studio_mcp import accounts,projects
row=accounts.active_account()
ref="7a7f7f89-c38d-4237-b4aa-ba499acd7507:642784b8-d39f-4e7b-b168-fe6218bbc45b"
item={"id":ref,"project_id":ref.split(":")[0],"tool_id":ref.split(":")[1]}
original={"version":1,"active":None,"genres":{},"projects":[]}
with patch.object(accounts,"_require_idle"),\
     patch.object(projects,"tabs",return_value=[item]),\
     patch.object(projects,"load",return_value=original),\
     patch.object(projects,"save") as save,\
     patch.object(projects,"probe_v2_compatible_tool") as probe:
    probe.return_value=True
    registered=projects.register(row,ref,"Whiteboard V2","whiteboard")
    assert registered["id"]==ref and save.call_count==1 and probe.call_count==1
    print("COMPATIBLE_PROJECT_REGISTERED_ONLY_AFTER_READONLY_PROBE_PASS",flush=True)
    probe.side_effect=projects.ProjectError("FLOW_V2_NATIVE_IMAGE_BRIDGE_MISSING")
    save.reset_mock()
    try:projects.register(row,ref,"Whiteboard incompatible","whiteboard")
    except projects.ProjectError as e:assert "BRIDGE_MISSING" in str(e)
    else:raise AssertionError("Unverified tool accepted")
    assert save.call_count==0
    print("INCOMPATIBLE_TOOL_REFUSED_BEFORE_PERSISTING_PASS",flush=True)
from types import SimpleNamespace
with patch.object(projects,"tabs",return_value=[item]),\
     patch.object(accounts,"_pid_browser_for_account",return_value=1410),\
     patch("studio_mcp.transport._isolated"),\
     patch("subprocess.run") as subprocess:
    subprocess.return_value=SimpleNamespace(
       stdout=json.dumps({"ok":True,"compatible":True})+"\n",returncode=0)
    assert projects.probe_v2_compatible_tool(row,ref)
    cmd=subprocess.call_args
    assert cmd.kwargs["input"]==json.dumps({"port":row["cdp_port"],
        "tool_url":"https://flow.google.com/project/"+item["project_id"]+"/tool/"+item["tool_id"]})
    print("PROBE_USES_EXACT_ACCOUNT_CDP_PORT_AND_EXACT_PROJECT_PASS",flush=True)
    subprocess.return_value=SimpleNamespace(stdout=json.dumps({"ok":False,"code":"missing"})+"\n",returncode=1)
    try:projects.probe_v2_compatible_tool(row,ref)
    except projects.ProjectError as e: assert "BRIDGE_MISSING" in str(e)
    else:raise AssertionError("Probe false positive")
    print("PROBE_REJECTS_SDK_MISSING_PASS",flush=True)
print("NO_PAID_REQUESTS_OR_REGISTRY_WRITES",flush=True)
