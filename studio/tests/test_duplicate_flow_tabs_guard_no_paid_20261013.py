"""No-paid duplicate-tab safety contracts, without changing Chrome tabs."""
from unittest.mock import patch
from pathlib import Path
import sys,json
sys.path.insert(0,r"D:\STORYBOARD_AI\studio")
from studio_mcp import accounts,projects
row=accounts.active_account()
url=projects.url_for(row,"whiteboard")
assert url
from io import BytesIO
class Response:
    def __init__(self,pages):self.pages=pages
    def __enter__(self):return BytesIO(json.dumps(self.pages).encode())
    def __exit__(self,*a):pass
two=[{"type":"page","url":url},{"type":"page","url":url}]
other=[{"type":"page","url":url},{"type":"page","url":"https://flow.google.com/"}]
with patch("studio_mcp.transport._isolated"),\
     patch.object(projects,"urlopen",return_value=Response(two)),\
     patch.object(accounts,"connection_check",return_value={"connected":True}),\
     patch.object(accounts,"_pid_browser_for_account",return_value=112):
    assert projects.exact_tool_tab_count(row,url)==2
    with patch.object(accounts,"_require_idle"):
        outcome=accounts.verify_mcp_connection(row["id"],tool_url=url)
    assert not outcome["ok"] and outcome["reason"]=="FLOW_MCP_DUPLICATE_TOOL_TABS" and outcome["tab_count"]==2
    try:accounts.require_production_browser(account=row,tool_url=url)
    except accounts.AccountError as e:
        assert "MULTIPLE_TOOL_TABS" in str(e),str(e)
    else:raise AssertionError("Danger: duplicate tabs accepted by production")
    print("DUPLICATE_MCP_VERIFY_REASON_AND_NO_PAID_PRODUCTION_GUARD_PASS",flush=True)
with patch("studio_mcp.transport._isolated"),\
     patch.object(projects,"urlopen",return_value=Response(other)),\
     patch.object(accounts,"connection_check",return_value={"connected":True}),\
     patch.object(accounts,"_pid_browser_for_account",return_value=112):
    assert projects.exact_tool_tab_count(row,url)==1
    print("SINGLE_CORRECT_TAB_UNBLOCKED_PASS",flush=True)
print("NO_EXISTING_TAB_CHANGED_PASS",flush=True)
