"""Isolation contract works before and after user registers a private tool URL; no generation."""
import os,sys
from pathlib import Path
home=Path(r"D:\STORYBOARD_AI\studio")
sys.path.insert(0,str(home))
from studio_mcp import accounts as base
from studio_mcp.transport import LocalFlowMcpTransport,_isolated,OUTPUT,NODE,PrivateMcpTransportError
from studio_flow_accounts import accounts,active,apply_worker_env,tool_url_for_active
from mcp_v2_images import preflight,StudioMcpImageError
reg=base.load_accounts()
assert len(reg["accounts"])>=1
default=base.find_account("default")
assert default["cdp_port"]==9550
assert ".storyboard-studio-private-chrome-default" in default["user_data_dir"]
assert ".storyboard-studio-private-state-default" in default["state_dir"]
for row in reg["accounts"]:
    _isolated(row)
    assert row["cdp_port"] not in (9333,9231)
print("ACCOUNTS_SEPARATE_PASS",len(reg["accounts"]),flush=True)
public_state=accounts()
assert "active_tool_url" not in public_state
current=tool_url_for_active()
assert public_state["tool_linked"] is bool(current)
if current:
    assert current.startswith("https://flow.google.com/") and "/project/" in current
    klass,models=preflight()
    assert len(models)==3
else:
    try:
        preflight()
        raise AssertionError("MCP must fail closed without private Flow tool URL")
    except StudioMcpImageError as exc:
        assert "TOOL_URL_REQUIRED" in str(exc),exc
print("NO_SHARED_WEB_TOOL_FALLBACK_PASS",flush=True)
try:
    LocalFlowMcpTransport()("flow_storyboard_native_image",
      {"action":"render_batch","tool_url":"https://flow.google.com/"})
    raise AssertionError("Must refuse mismatched URL before paid job")
except PrivateMcpTransportError as exc:
    assert "TOOL_URL_REQUIRED" in str(exc),exc
print("NO_PAID_JOB_WITH_WRONG_TOOL_PASS",flush=True)
info=apply_worker_env()
assert os.environ["FLOW_MCP_CDP_PORT"]==str(active()["cdp_port"])
assert os.environ["STORYBOARD_STUDIO_TOOL_URL"]==current
assert Path(os.environ["FLOW_MCP_USER_DATA_DIR"]).resolve()==Path(active()["user_data_dir"]).resolve()
assert "YOUTUBE_SEO_PRO_V2" not in str(OUTPUT)
assert "FLOW_MCP_SERVER" not in str(NODE)
for mod in sys.modules:
    assert not mod.startswith("auto_studio."),mod
print("PRIVATE_FLOW_CONFIG_FROZEN_PASS",flush=True)
print("PRIVATE_MCP_ISOLATION_E2E_OFFLINE_PASS",flush=True)
