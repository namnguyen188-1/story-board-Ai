"""Real Chromium UI regression, no production files are changed."""
import json
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser=p.chromium.launch(channel="msedge",headless=True)
    page=browser.new_page(viewport={"width":1400,"height":900})
    errors=[]
    page.on("pageerror", lambda e: errors.append(str(e)))
    called=[]
    def fake_manage(route):
        called.append(json.loads(route.request.post_data))
        route.fulfill(status=200,content_type="application/json",
                      body=json.dumps({"status":"TRASHED","id":"fake"},ensure_ascii=False))
    page.route("**/api/productions/manage",fake_manage)
    page.goto("http://127.0.0.1:8765/",wait_until="domcontentloaded")
    page.wait_for_function("state.statusReady",timeout=15000)
    page.locator("#btnOpenProductions").click()
    page.wait_for_function("gallerySnapshot.stats.projects === 26",timeout=20000)
    assert page.locator(".gallery-project").count()==2,"default main only"
    assert page.locator("#gallerySummary").inner_text().find("24 dự án thử nghiệm")>=0
    print("UI_MAIN_ONLY_PASS",page.locator(".gallery-project").count(),flush=True)

    page.locator("#galleryFilter").select_option("test")
    assert page.locator(".gallery-project").count()==24,"test list"
    print("UI_TEST_GROUP_PASS",page.locator(".gallery-project").count(),flush=True)

    page.locator("#gallerySearch").fill("hand-color")
    filtered=page.locator(".gallery-project").count()
    assert 1<=filtered<24, filtered
    print("UI_SEARCH_PASS",filtered,flush=True)

    page.locator("#gallerySearch").fill("")
    page.locator("#galleryFilter").select_option("main")
    page.locator("#gallerySort").select_option("size")
    cards=page.locator(".gallery-project")
    assert cards.count()==2
    page.once("dialog",lambda dialog:dialog.dismiss())
    page.locator('button[data-gallery-action="trash-project"]').first.click()
    assert not called,"cancel should not send POST"
    print("UI_CANCEL_SAFE_PASS",flush=True)

    page.locator("#galleryFilter").select_option("trash")
    assert page.locator(".gallery-project").count()==0, "recycle bin initially empty"
    print("UI_EMPTY_TRASH_PASS",flush=True)

    page.locator("#galleryFilter").select_option("main")
    page.once("dialog",lambda dialog:dialog.accept())
    first=page.locator('button[data-gallery-action="trash-episode"]').first
    original_series=first.get_attribute("data-series")
    original_episode=first.get_attribute("data-episode")
    first.click()
    page.wait_for_function("galleryBusy === false",timeout=15000)
    assert called and called[0]=={"action":"trash","series":original_series,"episode":original_episode},called
    print("UI_DELETE_WIRED_MOCK_PASS",called[0],flush=True)

    assert not errors,errors
    print("GALLERY_BROWSER_E2E_PASS",flush=True)
    browser.close()
