"""Real Studio UI verify-click regression for duplicate populated Google Flow tabs.
Does not close tabs or generate media.
"""
from playwright.sync_api import sync_playwright
from pathlib import Path
with sync_playwright() as pw:
 browser=pw.chromium.launch(channel="msedge",headless=True)
 page=browser.new_page(viewport={"width":1440,"height":900})
 errors=[]
 page.on("pageerror",lambda err: errors.append(str(err)))
 page.goto("http://127.0.0.1:8765/",wait_until="domcontentloaded",timeout=18000)
 page.wait_for_function("state.statusReady && !state.isRunning",timeout=12000)
 page.locator("#inGenre").select_option("whiteboard")
 page.evaluate("openModal(el.modalApiKey)")
 page.wait_for_function("document.getElementById('mcpAccountSelect').options.length>0",timeout=12000)
 page.locator("#mcpAccountSelect").select_option("default")
 page.locator("#btnMcpVerifyAccount").click(timeout=10000)
 page.wait_for_function("document.getElementById('mcpAccountStatus').textContent.includes('2 tab cùng Web Tool')",timeout=16000)
 message=page.locator("#mcpAccountStatus").inner_text()
 assert "Studio không tự xóa ảnh hoặc prompt" in message,message
 assert not errors,errors
 print("ACTUAL_GUI_VERIFY_EXPLAINS_TWO_TABS_PASS",message,flush=True)
 browser.close()
