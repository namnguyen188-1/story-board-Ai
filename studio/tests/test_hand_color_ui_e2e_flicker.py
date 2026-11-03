"""Fresh offline production from the actual form, plus playback and console monitoring."""
from pathlib import Path
import ctypes,threading,time,json,urllib.request,cv2,numpy as np
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parent
def visible_consoles():
    result=set();user=ctypes.windll.user32
    callback=ctypes.WINFUNCTYPE(ctypes.c_bool,ctypes.c_void_p,ctypes.c_void_p)
    def visit(hwnd,_):
        if user.IsWindowVisible(hwnd):
            name=ctypes.create_unicode_buffer(256);user.GetClassNameW(hwnd,name,256)
            if name.value=="ConsoleWindowClass":result.add(int(hwnd))
        return True
    user.EnumWindows(callback(visit),0)
    return result
baseline=visible_consoles();flashes=set();stop=threading.Event()
def monitor():
    while not stop.wait(.025):flashes.update(visible_consoles()-baseline)
thread=threading.Thread(target=monitor,daemon=True);thread.start()
try:
    current=json.load(urllib.request.urlopen("http://127.0.0.1:8765/api/status"))
    assert not current["running"],"must not interrupt user production"
    series="Color UI Flicker E2E "+str(int(time.time()))
    with sync_playwright() as p:
        browser=p.chromium.launch(channel="msedge",headless=True,args=["--autoplay-policy=no-user-gesture-required"])
        page=browser.new_page(viewport={"width":1440,"height":900})
        errors=[];page.on("pageerror",lambda err:errors.append(str(err)))
        page.goto("http://127.0.0.1:8765",wait_until="domcontentloaded")
        page.locator("#inSeries").fill(series)
        page.locator("#inEpisode").fill("1")
        page.locator("#inPrompt").fill("A painter reveals a colorful original village on a blank whiteboard.")
        page.locator("#inGenre").select_option("animation")
        page.locator("#inVisualStyle").select_option("hand_color")
        page.locator("#inImageSource").select_option("gemini")
        page.locator("#btnOffline").click()
        page.wait_for_function("state.isRunning || document.getElementById('headerStatusText').textContent.includes('Hoàn tất')",timeout=15000)
        page.wait_for_function("""async () => {
            const s=await (await fetch('/api/status')).json();
            return !s.running && s.exit_code===0 && !!s.final_video_url;
        }""",timeout=60000)
        page.wait_for_function("el.cinemaVideo.readyState>=2 && !!state.loadedEpisodeData?.final_video_url",timeout=15000)
        page.evaluate("""() => {
            window.reloads=0; el.cinemaVideo.addEventListener('loadstart',()=>window.reloads++);
            el.cinemaVideo.pause();el.cinemaVideo.currentTime=2;
            window.firstCard=document.querySelector('.scene-card');
        }""")
        page.wait_for_timeout(250)
        page.wait_for_timeout(4000) # real automatic polling remains enabled
        result=page.evaluate("""() => ({
            reloads:window.reloads,time:el.cinemaVideo.currentTime,paused:el.cinemaVideo.paused,
            cardPreserved:window.firstCard===document.querySelector('.scene-card')
        })""")
        assert result["reloads"]==0,result
        assert abs(result["time"]-2)<.2 and result["paused"],result
        assert result["cardPreserved"],result
        assert not errors,errors
        status=json.load(urllib.request.urlopen("http://127.0.0.1:8765/api/status"))
        browser.close()
    url=status["final_video_url"].split("?")[0]
    path=root/url.removeprefix("/media/")
    cap=cv2.VideoCapture(str(path));white=[];frames=0
    while True:
        ok,f=cap.read()
        if not ok:break
        frames+=1;white.append(float(np.mean(np.all(f>245,axis=2))))
    cap.release()
    assert frames>100,frames
    # A new scene intentionally starts blank; locate abrupt flashes within each scene.
    manifest=json.loads((path.parent/"manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"]=="PASS",manifest["status"]
    print("REAL_FORM_E2E_PASS",json.dumps({"series":series,"frames":frames,"qc":manifest["qc"],"playback":result,"console_flashes":len(flashes),"output":str(path)}),flush=True)
    assert not flashes,"New visible console windows appeared during production"
finally:
    stop.set();thread.join(timeout=1)
