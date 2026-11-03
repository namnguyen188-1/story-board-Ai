"""No-network contract: project open never claims success before exact tab + visible Chrome."""
import sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,r"D:\STORYBOARD_AI\studio")
import studio_flow_accounts as sf
from studio_mcp import projects
row=sf.active()
ref="7a7f7f89-c38d-4237-b4aa-ba499acd7507:642784b8-d39f-4e7b-b168-fe6218bbc45b"
url=projects.project_url(*ref.split(":"))
from types import SimpleNamespace
entries=[{"id":ref,"project_id":ref.split(":")[0],"tool_id":ref.split(":")[1]}]
def bundle(**overrides):
 base=[
 patch.object(sf,"_isolated"),
 patch.object(sf.base,"_require_idle"),
 patch.object(projects,"load",return_value={"projects":entries}),
 patch.object(sf.base,"_chrome_path",return_value=Path(sys.executable)),
 patch.object(sf.base,"_pid_browser_for_account",return_value=137),
 patch.object(sf.base,"connection_check",return_value={"connected":True}),
 patch.object(projects,"tabs",return_value=entries),
 patch.object(sf,"_confirmed_visible_project",return_value=True),
 patch.object(sf.subprocess,"Popen",return_value=SimpleNamespace(pid=137))
 ]
 return base
from contextlib import ExitStack
with ExitStack() as stack:
 mocks=[stack.enter_context(x) for x in bundle()]
 result=sf.open_project(row,ref)
 assert result["opened"] is True and result["window_visible"] and result["tool_tab_verified"] and result["existing"]
 assert mocks[-1].call_count==0,"Existing tab must not duplicate"
 print("OPEN_EXISTING_TAB_VISIBILITY_CONFIRMED_PASS",flush=True)
with ExitStack() as stack:
 mocks=[stack.enter_context(x) for x in bundle()]
 mocks[-2].return_value=False
 try:sf.open_project(row,ref)
 except sf.base.AccountError as e:assert "CHROME_HIDDEN" in str(e)
 else:raise AssertionError("Hidden window incorrectly reported as opened")
 print("HIDDEN_CHROME_NO_FALSE_SUCCESS_PASS",flush=True)
with ExitStack() as stack:
 mocks=[stack.enter_context(x) for x in bundle()]
 with patch.object(projects,"tabs",return_value=[]):
  result=sf.open_project(row,ref)
 assert result["opened"] is True and result["window_visible"] and not result["existing"]
 assert mocks[-1].call_count==1,"Expect exactly one app Chrome launch"
 print("NEW_CHROME_TAB_VERIFIED_BEFORE_SUCCESS_PASS",flush=True)
with ExitStack() as stack:
 mocks=[stack.enter_context(x) for x in bundle()]
 with patch.object(projects,"tabs",return_value=[]):
  mocks[-2].return_value=False
  try:sf.open_project(row,ref)
  except sf.base.AccountError as e:assert "WINDOW_NOT_VISIBLE_OR_TAB_NOT_READY" in str(e)
  else:raise AssertionError("False success on invisible/invalid tab")
 assert mocks[-1].call_count==1
 print("LAUNCH_FAILED_NO_FALSE_SUCCESS_PASS",flush=True)
