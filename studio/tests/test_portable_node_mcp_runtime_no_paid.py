"""Verify transport prefers bundled Node without contacting Flow or using credit."""
import sys
from unittest.mock import patch
from types import SimpleNamespace
from pathlib import Path
sys.path.insert(0,r"D:\STORYBOARD_AI\studio")
from studio_mcp import accounts
from studio_mcp import transport
expected=str(transport.NODE/"node.exe")
assert Path(expected).is_file()
calls=[]
def fake_run(cmd,**kw):
    calls.append((cmd,kw))
    return SimpleNamespace(returncode=0,stdout='{"ok":true,"result":{"result":{"native":true}}}\n')
account=accounts.active_account()
url=accounts.account_tool_url(account)
assert url and accounts._matches_bundled_tool(url)
with patch.object(accounts,"connection_check",return_value={"connected":True}),\
     patch.object(transport.subprocess,"run",side_effect=fake_run):
    result=transport.LocalFlowMcpTransport(timeout=1)("flow_storyboard_native_image",
                    {"action":"health","tool_url":url},account=account)
assert result.get("result",{}).get("native") is True
assert len(calls)==1 and calls[0][0][0]==expected,calls
assert calls[0][1]["env"]["STORYBOARD_MCP_APPROVED"]=="0"
assert calls[0][1]["env"]["FLOW_MCP_CDP_PORT"]=="9550"
assert str(transport.OUTPUT) in calls[0][1]["env"]["STORYBOARD_MCP_OUTPUT_ROOT"]
print("PORTABLE_NODE_USED_NO_V2_NO_SPEND_PASS",flush=True)
