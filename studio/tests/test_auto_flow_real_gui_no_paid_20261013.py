"""Actual Studio GUI Auto Flow Manager + project routing E2E, no image spend."""
from playwright.sync_api import sync_playwright
import urllib.request,json
url="http://127.0.0.1:8765"
def get(path):
 with urllib.request.urlopen(url+path,timeout=8) as r:return json.load(r)
s=get("/api/status")
assert s["running"] is False
a=get("/api/mcp/auto/status")
assert a["ready"] and a["code"]=="AUTO_FLOW_READY",a
with sync_playwright() as pw:
 b=pw.chromium.launch(channel="msedge",headless=True)
 p=b.new_page(viewport={"width":1440,"height":940})
 errors=[];requests=[]
 p.on("pageerror",lambda e:errors.append(str(e)))
 p.on("response",lambda r:requests.append(r) if r.url.endswith("/api/mcp/auto") else None)
 p.goto(url,wait_until="domcontentloaded",timeout=20000)
 p.wait_for_function("state.statusReady && !state.isRunning",timeout=15000)
 p.evaluate("openModal(el.modalApiKey)")
 p.wait_for_function("document.getElementById('autoFlowManagerStatus').textContent.includes('MCP V2')",timeout=20000)
 print("AUTO_FLOW_STATUS_RENDERED_IN_REAL_STUDIO",p.locator("#autoFlowManagerStatus").inner_text(),flush=True)
 p.locator("#btnAutoFlowReconnect").click(timeout=12000)
 p.wait_for_function("document.getElementById('autoFlowManagerStatus').textContent.includes('MCP V2')",timeout=100000)
 assert requests and requests[-1].status==200,[(r.status,r.url) for r in requests]
 assert requests[-1].json().get("ready") is True
 assert not errors,errors
 print("AUTO_FLOW_GUI_RECONNECT_CLICKS_AND_VERIFIES_PASS",flush=True)
 b.close()
assert get("/api/status")["running"] is False
print("NO_PAID_ACTIONS_STUDIO_IDLE_PASS",flush=True)
