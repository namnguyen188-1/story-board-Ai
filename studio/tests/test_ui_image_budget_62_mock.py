"""Chromium E2E: choose 62 with explicit confirmation OR 20 reused, mock /api/produce."""
from playwright.sync_api import sync_playwright
import json
with sync_playwright() as p:
    browser=p.chromium.launch(channel="msedge",headless=True)
    page=browser.new_page(viewport={"width":1400,"height":900})
    posts=[];errors=[];dialogs=[]
    page.on("pageerror",lambda e:errors.append(str(e)))
    def intercept(route):
        posts.append(json.loads(route.request.post_data))
        route.fulfill(status=200,content_type="application/json",
                      body='{"status":"STARTED","job":{"running":true}}')
    page.route("**/api/produce",intercept)
    page.goto("http://127.0.0.1:8765/",wait_until="domcontentloaded")
    page.wait_for_function("state.statusReady && !state.isRunning",timeout=13000)
    page.locator("#inInputMode").select_option("idea")
    page.locator("#inPrompt").fill("Original fictional philosophical story set on a seaside mountain.")
    page.locator("#inMinutes").fill("25.8")
    page.locator("#inSceneSec").fill("25")
    page.locator("#inMcpMaxImages").fill("20")
    page.locator("#inImageSource").select_option("mcp_v2")
    page.locator("#inMcpVisualReuse").uncheck()
    page.evaluate("updateImageBudgetHint()")
    assert "62 cảnh" in page.locator("#imageBudgetHint").inner_text()
    assert "chỉ duyệt 20 ảnh" in page.locator("#imageBudgetHint").inner_text()
    page.once("dialog",lambda dlg:(dialogs.append(dlg.message),dlg.accept()))
    page.locator("#btnLive").click()
    assert len(dialogs)==1
    assert "credit" in dialogs[0].lower()
    assert page.locator("#inMcpMaxImages").input_value()=="62"
    assert not posts, "Confirmation must not start paid job"
    print("UI_62_CREDIT_EXPLICIT_REAPPROVAL_NO_POST_PASS",flush=True)

    page.locator("#inMcpMaxImages").fill("20")
    page.locator("#inMcpVisualReuse").check()
    page.evaluate("updateImageBudgetHint()")
    assert "42 cảnh" in page.locator("#imageBudgetHint").inner_text()
    page.locator("#btnLive").click()
    page.wait_for_timeout(500)
    assert len(posts)==1, {"posts":posts,"errors":errors,"hint":page.locator("#imageBudgetHint").inner_text()}
    assert posts[0]["mcp_max_images"]==20
    assert posts[0]["mcp_visual_policy"]=="reuse"
    assert abs(posts[0]["minutes"]-25.8)<.001
    assert posts[0]["scene_seconds"]==25
    print("UI_20_IMAGE_REUSE_POST_WIRED_MOCK_PASS",flush=True)
    assert not errors,errors
    browser.close()
print("UI_IMAGE_BUDGET_E2E_NO_PAID_PASS",flush=True)
