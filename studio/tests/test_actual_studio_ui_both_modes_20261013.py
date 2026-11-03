"""Unmocked actual Storyboard UI clicks, two styles in sequence.
Uses the Studio's Sản Xuất Test Offline button, not direct render_one.
Live MCP E2E is separately gated by real account and provider.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright
import urllib.request,json,time,subprocess,cv2,hashlib
root=Path(r"D:\STORYBOARD_AI\studio")
base="http://127.0.0.1:8765"
specs=[
 ("hand_color","E2E UI Real Fixed Color 20261013"),
 ("whiteboard","E2E UI Real Fixed Mono 20261013")
]
def state():
 with urllib.request.urlopen(base+"/api/status",timeout=8) as r:return json.load(r)
assert not state().get("running"),"A production already runs, no interference"
with sync_playwright() as pw:
 browser=pw.chromium.launch(channel="msedge",headless=True,args=["--autoplay-policy=no-user-gesture-required"])
 for style,series in specs:
  targetpart=series.replace(" ","-")
  assert not list((root/"productions").glob(targetpart+"*")),("Refusing duplicate production",targetpart)
  page=browser.new_page(viewport={"width":1440,"height":920})
  page_errors=[];requests=[]
  page.on("pageerror",lambda error:page_errors.append(str(error)))
  page.on("request",lambda req:requests.append((req.method,req.url)) if "/api/produce" in req.url else None)
  page.on("dialog",lambda dialog:dialog.dismiss())
  page.goto(base,wait_until="domcontentloaded",timeout=20000)
  page.wait_for_function("state.statusReady && !state.isRunning",timeout=12000)
  page.locator("#inSeries").fill(series)
  page.locator("#inEpisode").fill("1")
  page.locator("#inInputMode").select_option("idea")
  page.locator("#inPrompt").fill(
   "A friendly illustrator tells a short original story of a little riverside village "
   "with a clock tower and a bright kite at sunrise, step-by-step drawing on a whiteboard.")
  page.locator("#inMinutes").fill("0.1")
  page.locator("#inSceneSec").fill("8")
  page.locator("#inGenre").select_option("whiteboard")
  page.locator("#inVisualStyle").select_option(style)
  page.locator("#inLanguage").select_option("English")
  page.locator("#inRegion").select_option("US")
  page.locator("#inImageSource").select_option("mcp_v2")
  page.locator("#inResolution").select_option("640x360")
  page.locator("#inSubtitleStyle").select_option("karaoke_viral")
  print("ACTUAL_STUDIO_UI_CLICK_OFFLINE",style,series,flush=True)
  page.locator("#btnOffline").click(timeout=10000)
  try:
   page.wait_for_function("state.isRunning || state.currentSeries==="+json.dumps(series),timeout=16000)
  except Exception as exc:
   print("UI_RUN_START_DIAG",page.locator("#headerStatusText").inner_text(),
         page.locator("#toastContainer").all_inner_texts(),flush=True)
   raise
  elapsed=time.monotonic()
  prior=""
  while time.monotonic()-elapsed<160:
   time.sleep(2)
   s=state()
   stage=s.get("stage","")
   if stage!=prior:
    print("UI_TOOL_JOB",style,stage,s.get("percent"),flush=True)
    prior=stage
   if not s["running"]:break
  else:raise RuntimeError("STUDIO_UI_E2E_TIMEOUT_NO_RETRY")
  assert s.get("exit_code")==0 and s.get("final_video_url"),(style,s.get("recent_logs",[])[-16:])
  assert s.get("series")==series,(s.get("series"),series)
  page.wait_for_function("state.loadedEpisodeData?.final_video_url && el.cinemaVideo.readyState>=2",timeout=16000)
  playback=page.evaluate("""() => ({
    source:el.cinemaVideo.currentSrc,
    duration:el.cinemaVideo.duration,
    ready:el.cinemaVideo.readyState,
    sceneCards:document.querySelectorAll('.scene-card').length,
    selectedStyle:el.inVisualStyle.value
  })""")
  assert playback["ready"]>=2 and playback["sceneCards"]>=1,(style,playback)
  assert playback["selectedStyle"]==style,playback
  media=root/s["final_video_url"].split("?",1)[0].removeprefix("/media/")
  assert media.is_file(),media
  episode=media.parent
  plan=json.loads((episode/"manifest.json").read_text(encoding="utf-8"))
  assert plan["status"]=="PASS"
  job=json.loads((episode/"scenes"/"scene_0001"/"job.json").read_text(encoding="utf-8"))
  assert job["visual_style"]==style,(style,job["visual_style"])
  info=json.loads(subprocess.run(["ffprobe","-v","error","-show_entries","stream=codec_type,codec_name,width,height:format=duration,size","-of","json",str(media)],capture_output=True,text=True,timeout=25,check=True).stdout)
  assert any(x["codec_type"]=="video" for x in info["streams"])
  assert any(x["codec_type"]=="audio" for x in info["streams"])
  assert (episode/"scenes"/"scene_0001"/"subtitles.json").exists()
  assert requests and any(x[0]=="POST" for x in requests),requests
  assert not page_errors,page_errors
  report={"style":style,"mode":"REAL_STUDIO_UI_TEST_OFFLINE","status":"PASS",
          "series":series,"mp4":str(media),"bytes":media.stat().st_size,
          "duration":float(info["format"]["duration"]),"scene_count":playback["sceneCards"],
          "ui_playback":playback,"production_requests":len(requests),
          "new_google_flow_image_jobs":0}
  (episode/"ACTUAL_STUDIO_UI_E2E.json").write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
  print("ACTUAL_STUDIO_UI_MODE_PASS",json.dumps(report,ensure_ascii=False),flush=True)
  page.close()
 browser.close()
print("BOTH_UNMOCKED_STUDIO_UI_E2E_MODES_PASS",flush=True)
