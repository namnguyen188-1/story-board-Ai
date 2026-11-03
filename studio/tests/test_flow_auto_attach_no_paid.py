"""Read-only integration: bundled share auto-resolves only on private Chrome, no payments."""
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0,r"D:\STORYBOARD_AI\studio")
from studio_mcp import accounts as a
from studio_flow_accounts import accounts as public
TARGET="https://flow.google.com/project/79dfa39d-8ec4-4ab7-aaa2-2be03bd1bdd0/tool/69da86fb-6c79-43d2-a387-ef47b0fda4db"
SHARE="https://flow.google.com/shared/tool/69da86fb-6c79-43d2-a387-ef47b0fda4db"
assert a.bundled_shared_tool_url()==SHARE
assert a._matches_bundled_tool(TARGET)
assert not a._matches_bundled_tool("https://flow.google.com/project/79dfa39d-8ec4-4ab7-aaa2-2be03bd1bdd0/tool/00000000-0000-4000-8000-000000000000")
assert not a._matches_bundled_tool("https://evil.invalid/project/79dfa39d-8ec4-4ab7-aaa2-2be03bd1bdd0/tool/69da86fb-6c79-43d2-a387-ef47b0fda4db")
print("BUNDLED_SHARE_IDENTITY_PASS",flush=True)
state=public()
assert "active_tool_url" not in state
assert "shared_url" not in state
assert state["tool_linked"] is True
print("NO_URL_IN_UI_API_PASS",flush=True)
live=a.active_account()
with TemporaryDirectory(prefix="storyboard_private_flow_test_") as temp:
    account=dict(live)
    account["state_dir"]=temp
    assert not Path(temp,"studio_private_tool_url.json").exists()
    # Simulate a valid redirected tab in this account without requiring a live Google login.
    with patch.object(a,"_resolve_shared_tool_url",return_value=TARGET) as discovered:
        found=a.account_tool_url(account)
        discovered.assert_called_once_with(account,SHARE)
    assert found==TARGET, found
    assert Path(temp,"studio_private_tool_url.json").exists()
    assert a.account_tool_url(account)==TARGET
    print("AUTO_ATTACH_LOGIN_PROFILE_PASS",flush=True)
with TemporaryDirectory(prefix="storyboard_flow_negative_") as temp:
    account=dict(live)
    account["state_dir"]=temp
    with patch.object(a,"_resolve_shared_tool_url",side_effect=a.AccountError("NO_MATCH")):
        assert a.account_tool_url(account)==""
        assert not Path(temp,"studio_private_tool_url.json").exists()
    print("CANNOT_AUTO_ATTACH_OTHER_TOOL_PASS",flush=True)
print("FLOW_ONE_TIME_LOGIN_BINDING_NO_PAID_CALLS_PASS",flush=True)
