"""Read-only regression: browser missing must reject BEFORE any Gemini/Flow job."""
from pathlib import Path
import sys, json, urllib.request, urllib.error, hashlib
from unittest.mock import patch
root=Path(r"D:\STORYBOARD_AI\studio")
sys.path.insert(0,str(root))
from studio_mcp import accounts as mcp
row=mcp.active_account()
assert row["cdp_port"]==9550
live_connected=bool(mcp.connection_check(row["id"]).get("connected"))
with patch.object(mcp,"connection_check",return_value={"connected":False,"reason":"BROWSER_NOT_RUNNING"}):
    try:
        mcp.require_production_browser(row)
        raise AssertionError("Closed Chrome should always fail.")
    except mcp.AccountError as exc:
        assert str(exc)=="STORYBOARD_PRIVATE_BROWSER_NOT_CONNECTED",str(exc)
print("MOCKED_CLOSED_STUDIO_CHROME_DETECTED_PASS",flush=True)
expected=mcp.account_tool_url(row)
assert expected and mcp._matches_bundled_tool(expected)
with patch.object(mcp,"connection_check",return_value={"connected":True}),\
     patch.object(mcp,"_pid_browser_for_account",return_value=1000),\
     patch.object(mcp,"_resolve_shared_tool_url",return_value=expected):
    assert mcp.require_production_browser(row)==expected
print("VALID_PRIVATE_FLOW_TAB_ACCEPTS_PASS",flush=True)
with patch.object(mcp,"connection_check",return_value={"connected":True}),\
     patch.object(mcp,"_pid_browser_for_account",return_value=1000),\
     patch.object(mcp,"_resolve_shared_tool_url",side_effect=mcp.AccountError("NO_MATCH")):
    try:
        mcp.require_production_browser(row)
        raise AssertionError("Should reject wrong browser tab")
    except mcp.AccountError as exc:
        assert str(exc)=="STORYBOARD_PRIVATE_WEB_TOOL_NOT_OPEN"
print("WRONG_FLOW_TAB_REJECTED_PASS",flush=True)

# Never POST an actual production when the user's own Chrome is open.
# The isolated mocked branch above remains safe in every environment.
if live_connected:
    print("HTTP_REAL_NEGATIVE_TEST_SKIPPED_BROWSER_CURRENTLY_OPEN",flush=True)
    raise SystemExit(0)

url="http://127.0.0.1:8765/api/produce"
inbox=root/"inbox"
before={p.name for p in inbox.glob("web_prompt_*.txt")}
payload={
 "series":"Whiteboard Chronicles","episode":1,
 "prompt":"https://www.youtube.com/watch?v=HIBI6y1HcIs",
 "reference_url":"https://www.youtube.com/watch?v=HIBI6y1HcIs",
 "input_mode":"link", "minutes":25.8,"scene_seconds":25,
 "language":"Spanish","voice_name":"Charon",
 "genre":"stoic","visual_style":"color_cinematic","region":"ES",
 "model":"gemini-3.8-flash","size":"1920x1080",
 "image_provider":"mcp_v2","mcp_max_images":62,
 "mcp_visual_policy":"unique","mode":"live"
}
req=urllib.request.Request(url,data=json.dumps(payload).encode("utf-8"),
 headers={"Content-Type":"application/json"},method="POST")
try:
    urllib.request.urlopen(req,timeout=14)
    raise AssertionError("Studio started expensive production with closed Chrome")
except urllib.error.HTTPError as exc:
    result=json.loads(exc.read())
    assert exc.code==409,(exc.code,result)
    assert result.get("code")=="STORYBOARD_PRIVATE_BROWSER_NOT_CONNECTED",result
    assert result.get("recovery")=="OPEN_STORYBOARD_FLOW_LOGIN_AND_VERIFY"
    assert "Google Flow" in result.get("error","")
assert before=={p.name for p in inbox.glob("web_prompt_*.txt")}
with urllib.request.urlopen("http://127.0.0.1:8765/api/status",timeout=7) as res:
    s=json.load(res)
assert s["running"] is False
print("HTTP_GEMINI_AND_FLOW_JOB_NOT_STARTED_WHEN_BROWSER_CLOSED_PASS",flush=True)
