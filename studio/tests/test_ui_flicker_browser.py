"""Real Chromium UI and video playback: unchanged refresh must preserve media/DOM."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parent
with sync_playwright() as p:
    browser=p.chromium.launch(channel="msedge",headless=True,args=["--autoplay-policy=no-user-gesture-required"])
    page=browser.new_page(viewport={"width":1440,"height":900})
    errors=[]
    page.on("pageerror",lambda error:errors.append(str(error)))
    page.goto("http://127.0.0.1:8765",wait_until="domcontentloaded")
    # Existing real QA episode; no producer or external image/TTS calls.
    page.evaluate("""async () => {
        clearInterval(state.pollTimer);
        state.currentSeries='Hand-Color-HTTP-Offline-QA---Offline-Test';
        state.currentEpisode=1;
        await loadEpisodeDetails(state.currentSeries,1);
        window.testLoads=0;
        el.cinemaVideo.addEventListener('loadstart',()=>window.testLoads++);
    }""")
    page.wait_for_function("el.cinemaVideo.readyState >= 2")
    page.evaluate("""() => {
        window.testLoads=0; el.cinemaVideo.pause(); el.cinemaVideo.currentTime=2;
        window.testCard=document.querySelector('.scene-card');
    }""")
    page.wait_for_timeout(250)
    before=page.evaluate("el.cinemaVideo.currentTime")
    page.evaluate("""async () => {
        for(let i=0;i<4;i++) await loadEpisodeDetails(state.currentSeries,1);
    }""")
    page.wait_for_timeout(400)
    result=page.evaluate("""() => ({
        beforeCardPreserved:window.testCard===document.querySelector('.scene-card'),
        loads:window.testLoads,time:el.cinemaVideo.currentTime,paused:el.cinemaVideo.paused
    })""")
    print("BROWSER_REFRESH_RESULT",json.dumps(result),flush=True)
    assert result["beforeCardPreserved"],"unchanged poll replaced card DOM and forced image reload"
    assert result["loads"]==0,"same video was reloaded"
    assert abs(result["time"]-before)<.2,"preview playback position reset"
    assert result["paused"],"refresh restarted a paused preview"
    assert not errors,errors
    browser.close()
print("BROWSER_NO_FLICKER_PASS",flush=True)
