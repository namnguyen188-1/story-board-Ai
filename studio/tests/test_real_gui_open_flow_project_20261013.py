"""Click actual Storyboard Settings > MCP > Mở dự án without HTTP mocks.
Assert server verifies visible Chrome window and correct Flow tool tab.
No image/credits/production.
"""
from playwright.sync_api import sync_playwright
import json,urllib.request,sys
from pathlib import Path
root=Path(r"D:\STORYBOARD_AI\studio")
sys.path.insert(0,str(root))
from studio_flow_accounts import active,_visible_chrome_window
from studio_mcp.accounts import _pid_browser_for_account
ref="7a7f7f89-c38d-4237-b4aa-ba499acd7507:642784b8-d39f-4e7b-b168-fe6218bbc45b"
with sync_playwright() as p:
 browser=p.chromium.launch(channel="msedge",headless=True)
 page=browser.new_page(viewport={"width":1450,"height":920})
 errors=[]
 responses=[]
 page.on("pageerror",lambda e:errors.append(str(e)))
 page.on("response",lambda r:responses.append(r) if r.url.endswith("/api/mcp/project") else None)
 page.goto("http://127.0.0.1:8765/",wait_until="domcontentloaded",timeout=15000)
 page.wait_for_function("state.statusReady",timeout=16000)
 page.evaluate("openModal(el.modalApiKey)")
 page.wait_for_function("!!flowProjectSnapshot && document.getElementById('mcpProjectSelect').options.length>=2",timeout=16000)
 page.locator("#mcpProjectSelect").select_option(ref)
 page.locator("#btnMcpOpenProject").click(timeout=8000)
 page.wait_for_function("document.getElementById('mcpProjectStatus').textContent.includes('Đã mở') || document.getElementById('mcpProjectStatus').textContent.includes('Lỗi')",timeout=17000)
 status=page.locator("#mcpProjectStatus").inner_text()
 assert status.startswith("Đã mở"),status
 assert len(responses)==1,responses
 data=responses[0].json()
 assert responses[0].status==200 and data["ok"],data
 result=data["result"]
 assert result["opened"] and result["window_visible"] and result["tool_tab_verified"],result
 assert not errors,errors
 browser.close()
with urllib.request.urlopen("http://127.0.0.1:8765/api/mcp/projects",timeout=7) as r:
 projects=json.load(r)
assert any(x["id"]==ref for x in projects["open_tabs"]),projects
row=active()
pid=_pid_browser_for_account(row)
assert pid and _visible_chrome_window(pid),pid
print("REAL_STUDIO_OPEN_PROJECT_GUI_E2E_PASS",
 json.dumps({"window_visible":True,"tool_tab_verified":True,
             "project_id":ref,"existing":result["existing"],
             "server_open_tabs":len(projects["open_tabs"]),
             "no_paid_calls":True},ensure_ascii=False),flush=True)
