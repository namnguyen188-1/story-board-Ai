"""Legacy MCP settings regression updated for invisible auto-binding."""
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser=p.chromium.launch(channel="msedge",headless=True)
    page=browser.new_page(viewport={"width":1400,"height":900})
    errors=[]
    page.on("pageerror",lambda e:errors.append(str(e)))
    page.goto("http://127.0.0.1:8765/",wait_until="domcontentloaded")
    page.wait_for_function("state.statusReady",timeout=15000)
    page.evaluate("openModal(el.modalApiKey)")
    page.wait_for_function("document.getElementById('mcpAccountSelect').options.length>=1",timeout=10000)
    assert "V2 hiện có" not in page.locator("#mcpAccountSelect").inner_text()
    assert page.locator("#mcpPrivateToolUrl").count()==0
    assert page.locator("#btnMcpSaveToolUrl").count()==0
    assert page.locator("#mcpToolAutoStatus").count()==1
    assert page.locator("#btnMcpOpenLogin").count()==1
    assert page.locator("#btnMcpVerifyAccount").count()==1
    assert "flow.google.com/shared/tool/" not in page.locator("#modalApiKey").inner_text()
    assert not errors,errors
    print("MCP_SETTINGS_PRIVATE_AUTO_BIND_UI_PASS",flush=True)
    browser.close()
