"""No-credential/no-generation tests for Studio's account settings endpoints."""
from __future__ import annotations
import json,sys,threading,urllib.request,urllib.error
from pathlib import Path
from http.server import HTTPServer
from unittest.mock import patch
studio=Path(r"D:\STORYBOARD_AI\studio")
sys.path.insert(0,str(studio))
import studio_flow_accounts as acc
from web_server import StudioRequestHandler
from html.parser import HTMLParser
class IDs(HTMLParser):
    def __init__(self):super().__init__();self.ids=set()
    def handle_starttag(self,tag,attrs):
        for key,value in attrs:
            if key=="id":self.ids.add(value)
parser=IDs()
parser.feed((studio/"web"/"index.html").read_text(encoding="utf-8"))
required={"mcpAccountSelect","mcpNewAccountName","mcpAccountStatus",
"btnMcpOpenLogin","btnMcpCheckAccount","btnMcpVerifyAccount","btnMcpAddAccount"}
assert required <= parser.ids,required-parser.ids
print("MCP_SETTINGS_DOM_PASS",flush=True)
acc.select("default")
listing=acc.accounts()
assert listing["accounts"] and listing["active"]=="default",listing.get("active")
assert all(set(x)=={"id","name","active"} for x in listing["accounts"])
assert not any("password" in str(x).lower() or "cookie" in str(x).lower() for x in listing["accounts"])
print("MCP_STUDIO_REGISTRY_ISOLATION_PASS",len(listing["accounts"]),flush=True)
server=HTTPServer(("127.0.0.1",0),StudioRequestHandler)
thread=threading.Thread(target=server.serve_forever,daemon=True)
thread.start()
addr="http://127.0.0.1:"+str(server.server_address[1])
def get(uri):
    with urllib.request.urlopen(addr+uri,timeout=4) as r:
        return json.load(r)
def post(action,origin=None,**kwargs):
    headers={"Content-Type":"application/json"}
    if origin:headers["Origin"]=origin
    request=urllib.request.Request(addr+"/api/mcp/account",data=json.dumps({"action":action,**kwargs}).encode(),
                               headers=headers,method="POST")
    try:
        with urllib.request.urlopen(request,timeout=5) as r:
            return (r.status,json.load(r))
    except urllib.error.HTTPError as e:
        return (e.code,json.loads(e.read().decode("utf-8")))
try:
    records=get("/api/mcp/accounts")
    assert records["active"]=="default" and records["accounts"]
    print("HTTP_LIST_MCP_ACCOUNTS_PASS",flush=True)
    status,data=post("check",account_id="default")
    assert status==200 and data["ok"] and "connected" in data["result"]
    print("HTTP_BROWSER_STATUS_PASS connected="+str(data["result"]["connected"]),flush=True)
    status,data=post("login",origin="https://untrusted.invalid",account_id="default")
    assert status==403
    print("ACCOUNT_CROSS_ORIGIN_BLOCK_PASS",flush=True)
    status,data=post("unsupported",account_id="default")
    assert status==400
    print("UNSUPPORTED_ACCOUNT_ACTION_GUARD_PASS",flush=True)
    with patch.object(acc,"create",return_value={"id":"account_123456789abc","name":"Test Account"}) as create, \
         patch.object(acc,"select",return_value={"id":"account_123456789abc","name":"Test Account"}) as select:
        status,data=post("create",name="Test Account")
        assert status==200 and data["ok"] and data["result"]["id"]=="account_123456789abc"
        assert create.called and select.call_args.args[0]=="account_123456789abc"
        print("NEW_ACCOUNT_AUTO_SELECT_PASS",flush=True)
finally:
    server.shutdown()
print("MCP_ACCOUNT_ENDPOINT_TESTS_PASS no_real_login_no_image_generation",flush=True)
