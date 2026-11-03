"""No-paid Google login truthfulness, console suppression and auto-hide tests."""
import subprocess
from pathlib import Path
from unittest.mock import patch
from tempfile import TemporaryDirectory

from studio_mcp import accounts as a
from studio_mcp import auto_flow_manager as af
import studio_flow_accounts as flow

row=a.active_account()
with patch.object(a,"browser_probe",return_value={"connected":False}),\
     patch.object(a,"_pid_browser_for_account",return_value=0):
    state=a.flow_auth_status(row,force=True)
    assert state["authenticated"] is False and state["auth_state"]=="CHROME_DISCONNECTED"
    print("CDP_DOES_NOT_EQUAL_GOOGLE_LOGIN_PASS",flush=True)

af._CURRENT.clear()
af._CURRENT.update({"status":"READY","ready":True,
                    "account_id":row["id"],"code":"AUTO_FLOW_READY"})
with patch.object(a,"connection_check",return_value={"connected":True}),\
     patch.object(a,"flow_auth_status",return_value={
        "authenticated":False,"auth_state":"LOGIN_REQUIRED"}):
    s=af.status()
    assert s["ready"] is False and s["code"]=="AUTO_FLOW_LOGIN_REQUIRED",s
    print("LOGOUT_REVOKES_CACHED_MCP_READY_PASS",flush=True)

with TemporaryDirectory() as tmp:
    a.mark_manual_login("account_B",root=tmp)
    assert a.manual_login_active(root=tmp,account_id="account_B")
    assert not a.manual_login_active(root=tmp,account_id="account_A")
    print("LOGIN_MARKER_RESTRICTED_TO_SAME_ACCOUNT_PASS",flush=True)

with patch.object(af,"any_running_production",return_value=False),\
     patch.object(af,"active_account",return_value=row),\
     patch.object(a,"manual_login_active",return_value=True),\
     patch.object(af,"_pid_browser_for_account",return_value=123),\
     patch.object(a,"flow_auth_status",return_value={"authenticated":False}),\
     patch.object(af,"ensure_ready") as ensure,\
     patch.object(flow,"minimize_chrome_window") as mini:
    assert af.login_auto_finish_once()=="LOGIN_NOT_VERIFIED"
    assert not ensure.called and not mini.called
    print("NO_CHROME_HIDE_BEFORE_GOOGLE_LOGIN_PASS",flush=True)

with patch.object(af,"any_running_production",return_value=False),\
     patch.object(af,"active_account",return_value=row),\
     patch.object(a,"manual_login_active",return_value=True),\
     patch.object(af,"_pid_browser_for_account",return_value=123),\
     patch.object(a,"flow_auth_status",return_value={"authenticated":True}),\
     patch.object(af,"ensure_ready",return_value={"ready":False,"account_id":row["id"]}),\
     patch.object(flow,"minimize_chrome_window") as mini:
    assert af.login_auto_finish_once()=="MCP_NOT_READY"
    assert not mini.called
    print("NO_CHROME_HIDE_BEFORE_MCP_READY_PASS",flush=True)

with patch.object(af,"any_running_production",return_value=False),\
     patch.object(af,"active_account",return_value=row),\
     patch.object(a,"manual_login_active",return_value=True),\
     patch.object(af,"_pid_browser_for_account",return_value=123),\
     patch.object(a,"flow_auth_status",return_value={"authenticated":True}),\
     patch.object(af,"ensure_ready",return_value={"ready":True,"account_id":row["id"]}),\
     patch.object(flow,"minimize_chrome_window",return_value=True) as mini,\
     patch.object(a,"clear_manual_login") as clear:
    assert af.login_auto_finish_once()=="MINIMIZED_AFTER_VERIFIED_LOGIN"
    mini.assert_called_once_with(123)
    clear.assert_called_once()
    print("AUTO_HIDE_AFTER_GOOGLE_AND_MCP_PASS",flush=True)

source=Path(a.__file__).read_text(encoding="utf-8")
assert 'creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0)' in source
print("POWERSHELL_NO_CONSOLE_FLAG_PRESENT_PASS",flush=True)

with patch.object(af,"any_running_production",return_value=False),\
     patch.object(af,"active_account",return_value=row),\
     patch.object(a,"manual_login_active",return_value=False),\
     patch.object(af,"_pid_browser_for_account",return_value=456),\
     patch.object(a,"flow_auth_status",return_value={"authenticated":True}),\
     patch.object(af,"ensure_ready",return_value={"ready":True,"account_id":row["id"]}),\
     patch.object(flow,"minimize_chrome_window",return_value=True) as mini,\
     patch.object(a,"clear_manual_login") as clear:
    assert af.login_auto_finish_once(allow_unrequested=True)=="MINIMIZED_AFTER_VERIFIED_LOGIN"
    mini.assert_called_once_with(456)
    assert not clear.called
    print("DIRECT_CHROME_RELOGIN_AUTO_HIDES_WITHOUT_APP_LOGIN_CLICK_PASS",flush=True)

