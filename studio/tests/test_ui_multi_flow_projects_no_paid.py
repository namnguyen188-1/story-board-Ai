"""Headless browser verifies real Studio's project manager and mocked safe registration."""
from playwright.sync_api import sync_playwright
import json
with sync_playwright() as pw:
    browser=pw.chromium.launch(channel="msedge",headless=True)
    page=browser.new_page(viewport={"width":1390,"height":950})
    errors=[];posts=[]
    page.on("pageerror",lambda e:errors.append(str(e)))
    page.goto("http://127.0.0.1:8765/",wait_until="domcontentloaded")
    page.wait_for_function("state.statusReady",timeout=16000)
    page.evaluate("openModal(el.modalApiKey)")
    page.wait_for_function("!!flowProjectSnapshot && document.getElementById('mcpProjectSelect').options.length>=1",timeout=13000)
    assert page.locator("#mcpProjectSelect").count()==1
    assert page.locator("#mcpOpenProjectTab").count()==1
    assert page.locator("#mcpGenreBind").count()==1
    assert page.locator("#btnMcpRegisterProject").count()==1
    assert page.locator("#btnMcpSwitchProject").count()==1
    assert page.locator("#btnMcpOpenProject").count()==1
    assert page.locator("#mcpPrivateToolUrl").count()==0
    print("REAL_PROJECT_MANAGER_CONTROLS_PASS",flush=True)

    a="a48a51c1-a8a7-4b54-81a2-8789f7bc4c1f:8fbef6e9-a6e4-4b21-a8b0-0be7a559273d"
    b="79dfa39d-8ec4-4ab7-aaa2-2be03bd1bdd0:69da86fb-6c79-43d2-a387-ef47b0fda4db"
    def mock_get(route):
        result={
          "active":a,"genres":{"stoic":a,"family_drama":b},
          "projects":[{"id":a,"label":"Stoicism ES","genre":"stoic"},
                      {"id":b,"label":"Family Drama","genre":"family_drama"}],
          "open_tabs":[{"id":a,"project_id":a.split(":")[0],"tool_id":a.split(":")[1]},
                       {"id":b,"project_id":b.split(":")[0],"tool_id":b.split(":")[1]}]}
        route.fulfill(status=200,content_type="application/json",body=json.dumps(result))
    def mock_post(route):
        obj=json.loads(route.request.post_data)
        posts.append(obj)
        route.fulfill(status=200,content_type="application/json",body=json.dumps({"ok":True,"result":{"id":obj["project_id"]},"projects":{}}))
    page.route("**/api/mcp/projects",mock_get)
    page.route("**/api/mcp/project",mock_post)
    page.evaluate("loadMcpProjects()")
    page.wait_for_function("document.getElementById('mcpProjectSelect').options.length===2",timeout=6000)
    page.locator("#mcpGenreBind").select_option("stoic")
    page.locator("#mcpOpenProjectTab").select_option(a)
    page.locator("#mcpProjectName").fill("Stoicism ES")
    page.locator("#btnMcpRegisterProject").click()
    page.wait_for_function("document.getElementById('mcpProjectStatus').textContent.includes('Đã lưu')",timeout=6000)
    assert len(posts)==1 and posts[0]=={"action":"register","project_id":a,"name":"Stoicism ES","genre":"stoic"},posts
    page.locator("#mcpGenreBind").select_option("family_drama")
    page.locator("#mcpProjectSelect").select_option(b)
    page.locator("#btnMcpSwitchProject").click()
    page.wait_for_function("document.getElementById('mcpProjectStatus').textContent.includes('Đã chọn')",timeout=6000)
    assert posts[1]["action"]=="select" and posts[1]["project_id"]==b and posts[1]["genre"]=="family_drama"
    page.locator("#mcpProjectSelect").select_option(b)
    page.locator("#btnMcpOpenProject").click()
    page.wait_for_function("document.getElementById('mcpProjectStatus').textContent.includes('Đã mở')",timeout=6000)
    assert posts[2]["action"]=="open" and posts[2]["project_id"]==b
    assert not errors,errors
    print("PROJECT_SWITCH_AND_REGISTER_BUTTONS_MOCK_PASS",flush=True)
    browser.close()
print("UI_MULTI_FLOW_NO_PAID_E2E_PASS",flush=True)
