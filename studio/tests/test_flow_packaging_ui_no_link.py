"""UI privacy: no Web Tool URL input, backend account metadata omits URL."""
from playwright.sync_api import sync_playwright
import json
from urllib.request import urlopen
with urlopen("http://127.0.0.1:8765/api/mcp/accounts",timeout=8) as response:
    payload=json.load(response)
assert "active_tool_url" not in payload, payload
assert "shared_url" not in payload,payload
assert "tool_linked" in payload
with sync_playwright() as pw:
    browser=pw.chromium.launch(channel="msedge",headless=True)
    page=browser.new_page(viewport={"width":1400,"height":940})
    errors=[]
    page.on("pageerror", lambda e:errors.append(str(e)))
    page.goto("http://127.0.0.1:8765/",wait_until="domcontentloaded")
    page.wait_for_function("state.statusReady",timeout=14000)
    page.evaluate("openModal(el.modalApiKey)")
    page.wait_for_function("document.getElementById('mcpAccountSelect').options.length>=1",timeout=12000)
    assert page.locator("#mcpPrivateToolUrl").count()==0
    assert page.locator("#btnMcpSaveToolUrl").count()==0
    assert page.locator("#mcpToolAutoStatus").count()==1
    assert "đã" in page.locator("#mcpToolAutoStatus").inner_text().lower() or "tích hợp" in page.locator("#mcpToolAutoStatus").inner_text().lower()
    html=page.locator("#modalApiKey").inner_text()
    assert "flow.google.com/shared/tool/" not in html
    assert "79dfa39d-8ec4-4ab7-aaa2-2be03bd1bdd0" not in html
    assert "69da86fb-6c79-43d2-a387-ef47b0fda4db" not in html
    assert "Lưu URL Web Tool" not in html
    assert page.locator("#btnMcpOpenLogin").count()==1
    assert page.locator("#btnMcpVerifyAccount").count()==1
    assert not errors, errors
    print("FLOW_PRIVATE_PACKAGING_UI_NO_LINK_E2E_PASS",flush=True)
    browser.close()
