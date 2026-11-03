from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(channel="msedge",headless=True)
    page=b.new_page(viewport={"width":1365,"height":870})
    errors=[]
    page.on("pageerror",lambda e:errors.append(str(e)))
    page.goto("http://127.0.0.1:8765/",wait_until="domcontentloaded")
    page.wait_for_function("state.statusReady",timeout=12000)
    page.evaluate("openModal(el.modalApiKey)")
    page.wait_for_function("document.getElementById('mcpAccountSelect').options.length > 0",timeout=12000)
    current=page.locator("#mcpPrivateToolUrl").input_value()
    assert current.startswith("https://flow.google.com/project/79dfa39d-8ec4-4ab7-aaa2-2be03bd1bdd0/tool/69da86fb-6c79-43d2-a387-ef47b0fda4db"),current
    print("SAVED_SHARED_URL_RESOLVED_AND_DISPLAYED_PASS",flush=True)
    page.locator("#btnMcpVerifyAccount").click()
    page.wait_for_function("document.getElementById('mcpAccountStatus').textContent.includes('Xác minh chức năng MCP thành công')",timeout=120000)
    assert not errors,errors
    print("STORYBOARD_PRIVATE_REAL_HEALTH_UI_E2E_PASS_NO_RENDER",flush=True)
    b.close()
