"""Chromium read-only reload failed 62-scene episode, without image or Gemini API."""
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(channel="msedge",headless=True)
    page=b.new_page(viewport={"width":1400,"height":900})
    errors=[];network_mutations=[]
    page.on("pageerror",lambda e:errors.append(str(e)))
    def deny(route):
        network_mutations.append(route.request.url)
        route.fulfill(status=409,content_type="application/json",
           body='{"error":"NO_MOCK_PAID_PRODUCTION"}')
    page.route("**/api/produce",deny)
    # UI-only mock of idle status; never pauses or changes actual active production.
    page.route("**/api/status",lambda route:route.fulfill(status=200,
        content_type="application/json",body='{"running":false,"stage":"IDLE","percent":0,"recent_logs":[],"series":"","episode":0}'))
    page.goto("http://127.0.0.1:8765/",wait_until="domcontentloaded")
    page.wait_for_function("state.statusReady",timeout=15000)
    page.locator("#btnOpenProductions").click()
    page.wait_for_function("gallerySnapshot.stats.episodes >= 1",timeout=15000)
    page.locator("#galleryFilter").select_option("all")
    # Multiple incomplete episodes legitimately exist; resume the intended saved stoic project.
    resume=page.locator("section.gallery-project").filter(has_text="ESTOICISMO").locator('button[data-gallery-action="resume"]')
    assert resume.count()==1, "The intended stoic episode should remain resumable"
    resume.click()
    page.wait_for_function('el.inSeries.value.includes("ESTOICISMO") && el.inMinutes.value === "25.8"',timeout=16000)
    assert page.locator("#inSceneSec").input_value()=="25"
    assert page.locator("#inInputMode").input_value()=="link"
    assert page.locator("#inGenre").input_value()=="stoic"
    assert page.locator("#inVisualStyle").input_value()=="hand_color"
    assert page.locator("#inLanguage").input_value()=="Spanish"
    assert page.locator("#inMcpVisualReuse").is_checked() is False
    assert "62 cảnh" in page.locator("#imageBudgetHint").inner_text()
    assert not network_mutations and not errors,(network_mutations,errors)
    print("GALLERY_RECOVER_SAVED_62_SCENES_PREPOPULATED_NO_PAID_E2E_PASS",flush=True)
    b.close()
