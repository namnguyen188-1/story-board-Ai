"""No-credential smoke for customer onboarding: login opens bundled tool, URL remains absent from UI."""
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
import sys
sys.path.insert(0,r"D:\STORYBOARD_AI\studio")
import studio_flow_accounts as flow
from studio_mcp import accounts as private
account=flow.active()
assert account["id"]=="default"
launches=[]
def capture(command,**kwargs):
    launches.append(command)
    return SimpleNamespace(pid=987654,poll=lambda:None)
with patch.object(flow.base,"_require_idle",return_value=None),\
     patch.object(flow.base,"_chrome_path",return_value=Path(r"D:\STORYBOARD_AI\studio\studio_mcp\dummy_chrome.exe")) as chrome,\
     patch.object(Path,"is_file",return_value=True),\
     patch.object(flow.base,"browser_probe",return_value={"connected":False}),\
     patch.object(flow.base,"account_tool_url",return_value=""),\
     patch.object(flow.base,"_pid_browser_for_account",return_value=0),\
     patch.object(flow,"_show_chrome_window",return_value=True),\
     patch.object(flow.base,"mark_manual_login",return_value=None),\
     patch.object(flow.subprocess,"Popen",side_effect=capture):
    result=flow.open_login("default")
assert result["opened"] and len(launches)==1
assert launches[0][-1]==private.bundled_shared_tool_url(), launches
assert "--remote-debugging-port=9550" in launches[0]
assert "--user-data-dir="+account["user_data_dir"] in launches[0]
print("FIRST_LOGIN_OPENS_BUILTIN_SHARE_NOT_V2_PASS",flush=True)

# Existing browser without the expected tool: Login must reuse the same window.
launches.clear()
with patch.object(flow.base,"_require_idle",return_value=None),\
     patch.object(flow.base,"_chrome_path",return_value=Path(r"D:\STORYBOARD_AI\studio\studio_mcp\dummy_chrome.exe")) as chrome,\
     patch.object(Path,"is_file",return_value=True),\
     patch.object(flow.base,"browser_probe",return_value={"connected":True}),\
     patch.object(flow.base,"_pid_browser_for_account",return_value=43210),\
     patch.object(flow,"_show_chrome_window",return_value=True),\
     patch.object(flow.base,"account_tool_url",return_value=""),\
     patch.object(flow.base,"mark_manual_login",return_value=None),\
     patch.object(flow.subprocess,"Popen",side_effect=capture):
    result=flow.open_login("default")
assert result["reused"] and len(launches)==0, "Login must reuse own Chrome without creating a second window"
print("EXISTING_OWN_CHROME_NO_DUPLICATE_WINDOW_PASS",flush=True)
