"""No-paid Auto Flow Manager routing / recovery tests; no user registry writes."""
import sys
from pathlib import Path
from unittest.mock import patch
from tempfile import TemporaryDirectory
sys.path.insert(0,r"D:\STORYBOARD_AI\studio")
from studio_mcp import accounts as _test_accounts
_test_auth_guard=patch.object(_test_accounts,"flow_auth_status",return_value={"authenticated":True,"auth_state":"AUTHENTICATED"})
_test_auth_guard.start()
from studio_mcp import auto_flow_manager as m
from studio_mcp import projects
from types import SimpleNamespace

a={"id":"default","cdp_port":9550,"state_dir":""}
ref1="7a7f7f89-c38d-4237-b4aa-ba499acd7507:642784b8-d39f-4e7b-b168-fe6218bbc45b"
ref2="ed57618a-88b4-4be3-a429-0e08c506f0fa:642784b8-d39f-4e7b-b168-fe6218bbc45b"
def item(ref):return {"id":ref,"project_id":ref.split(":")[0],"tool_id":ref.split(":")[1],"label":"known","genre":"whiteboard"}
db={"version":1,"active":ref1,"genres":{"whiteboard":ref1},"projects":[item(ref1),item(ref2)]}
with TemporaryDirectory() as tmp:
 a["state_dir"]=tmp
 with patch.object(m,"verify_v2_baseline",return_value={"verified":True}),\
      patch.object(m,"any_running_production",return_value=False),\
      patch.object(m,"load",return_value=db),\
      patch.object(m,"exact_tool_tab_count",return_value=1),\
      patch.object(m,"probe_v2_compatible_tool",return_value=True) as probe,\
      patch.object(m,"unresolved_jobs",return_value=0),\
      patch.object(m,"choose") as choose:
    r=m.ensure_ready("whiteboard",account=a)
    assert r["ready"] and r["project_id"]==ref1,r
    assert probe.call_count==1 and not choose.called
    print("AUTO_FLOW_REUSES_WORKING_SELECTED_V2_BRIDGE_PASS",flush=True)
 m._READY_AT=0  # force full routing instead of 4-minute verified reuse
 with patch.object(m,"verify_v2_baseline",return_value={"verified":True}),\
      patch.object(m,"any_running_production",return_value=False),\
      patch.object(m,"load",return_value=db),\
      patch.object(m,"exact_tool_tab_count",return_value=1),\
      patch.object(m,"unresolved_jobs",return_value=0),\
      patch.object(m,"choose") as choose,\
      patch.object(m,"probe_v2_compatible_tool") as probe:
    def filter_bad(acc,ref,**kwargs):
      if ref==ref1:raise projects.ProjectError("FLOW_V2_NATIVE_IMAGE_BRIDGE_MISSING")
      return True
    probe.side_effect=filter_bad
    r=m.ensure_ready("whiteboard",account=a)
    assert r["ready"] and r["project_id"]==ref2,r
    choose.assert_called_once_with(a,ref2,"whiteboard")
    print("AUTO_FLOW_FAILOVER_TO_OTHER_VERIFIED_PROJECT_PASS",flush=True)
 with patch.object(m,"verify_v2_baseline",return_value={"verified":True}),\
      patch.object(m,"any_running_production",return_value=False),\
      patch.object(m,"load",return_value={"version":1,"active":None,"genres":{},"projects":[]}),\
      patch.object(m,"connection_check",return_value={"connected":False}),\
      patch.object(m,"_pid_browser_for_account",return_value=None),\
      patch.object(m,"unresolved_jobs",return_value=0):
    r=m.ensure_ready("auto",allow_open=False,account=a)
    assert not r["ready"] and r["code"]=="AUTO_FLOW_LOGIN_REQUIRED",r
    print("AUTO_FLOW_REQUESTS_REAL_USER_LOGIN_WHEN_NEEDED_PASS",flush=True)
 with patch.object(m,"any_running_production",return_value=True),\
      patch.object(m,"verify_v2_baseline",return_value={"verified":True}):
    r=m.ensure_ready("auto",account=a)
    assert not r["ready"] and r["code"]=="AUTO_FLOW_PRODUCTION_BUSY",r
    print("AUTO_FLOW_DOES_NOT_SWITCH_DURING_PRODUCTION_PASS",flush=True)
 state=Path(tmp)/"auto_flow_status.json"
 assert state.is_file()
 assert all(x not in state.read_text(encoding="utf-8").lower() for x in ("cookie","password","prompt_text","token"))
 print("AUTO_FLOW_SAFE_STATE_PERSISTENCE_PASS",flush=True)
