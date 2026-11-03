"""Storyboard AI single Google login + no duplicate UI paths. No credits."""
from pathlib import Path
from html.parser import HTMLParser
from unittest.mock import patch
from types import SimpleNamespace
import studio_flow_accounts as sf
from studio_mcp import projects

root=Path(r"D:\STORYBOARD_AI\studio")
html=(root/"web"/"index.html").read_text(encoding="utf-8")
js=(root/"web"/"app.js").read_text(encoding="utf-8")
py=(root/"studio_flow_accounts.py").read_text(encoding="utf-8")
class Parser(HTMLParser):
    def __init__(self):super().__init__();self.tags=[]
    def handle_starttag(self,tag,attrs):
        if tag=="button":self.tags.append(dict(attrs))
dom=Parser();dom.feed(html)
ids=[t.get("id") for t in dom.tags]
assert ids.count("robotBtnGoogleLogin")==1
assert ids.count("btnMcpOpenLogin")==1
assert all(x not in ids for x in (
 "robotBtnOpenDirectTab","robotBtnRestoreChrome","robotBtnMinimizeChrome",
 "robotBtnReconnect","btnMcpOpenDirectTab","btnMcpToggleWindow"))
assert 'onclick="robotLoginOnly()"' in html
assert 'window.open(url, "_blank")' not in js
assert "window.robotOpenDirectTab = window.robotLoginOnly" in js
assert "studioGoogleLoginBusy" in js
print("UI_SINGLE_GOOGLE_LOGIN_NO_EDGE_POPUPS_PASS",flush=True)

account=sf.active()
launched=[]
def capture(cmd,**kw):
    launched.append(cmd)
    return SimpleNamespace(pid=4711,poll=lambda:None)
with patch.object(sf.base,"_require_idle"),\
     patch.object(sf.base,"_chrome_path",return_value=Path(__file__)),\
     patch.object(sf.base,"browser_probe",return_value={"connected":True}),\
     patch.object(sf.base,"_pid_browser_for_account",return_value=4711),\
     patch.object(sf,"_show_chrome_window",return_value=True),\
     patch.object(sf.base,"mark_manual_login"),\
     patch.object(sf.subprocess,"Popen",side_effect=capture):
    for _ in range(3):
        result=sf.open_login(account["id"])
        assert result["reused"]
assert not launched,"Repeated login must not open extra Chrome windows"
print("THREE_CONSECUTIVE_LOGIN_CLICKS_REUSE_SAME_WINDOW_PASS",flush=True)

assert '"--new-tab",url' in py
assert '"--profile-directory=Default","--new-window",url' not in py
print("EXISTING_PROFILE_OPENS_PROJECT_IN_TAB_NOT_WINDOW_PASS",flush=True)
