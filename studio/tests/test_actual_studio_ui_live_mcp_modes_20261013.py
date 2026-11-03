"""Real Studio Production GUI, Live Google Flow MCP, isolated disposable tab.
One paid image maximum per mode. No retries on errors/uncertain states.
"""
from pathlib import Path
import json,time,urllib.request,subprocess
from playwright.sync_api import sync_playwright
root=Path(r"D:\STORYBOARD_AI\studio")
url="http://127.0.0.1:8765"
cases=[("hand_color","STUDIO LIVE MCP Color UI QA 20261013"),
       ("whiteboard","STUDIO LIVE MCP Mono UI QA 20261013")]
prompt='''SHOT 1
FORMAT & STYLE: An 8-second continuous shot in a warm and original hand-drawn fantasy illustration.
SETTING: A peaceful riverside village, an old clock tower, green trees, a stone bridge and a bright blue kite in a gentle sunrise.
CAMERA: Fixed wide composition in a 16:9 frame; clear complete objects and no lettering, title, signs or logos.
TIMED ACTION: An illustrator draws the clock tower, bridge and trees. Colors and small details complete the scenery.
AUDIO:
Narration: "A gentle sunrise brightens the village as a kite floats past the tower."
CONSTRAINTS: Family friendly scene, no violence, realistic painted details, original imaginary artwork.
'''
def status():
 with urllib.request.urlopen(url+"/api/status",timeout=7) as h:return json.load(h)
assert not status()["running"],"STUDIO_PRODUCTION_ACTIVE_DO_NOT_START"
with sync_playwright() as pw:
 browser=pw.chromium.launch(channel="msedge",headless=True)
 for style,series in cases:
  assert not any((root/"productions").glob(series.replace(" ","-")+"*")),("EXISTING_EPISODE_NO_OVERWRITE",series)
  p=browser.new_page(viewport={"width":1440,"height":920})
  errors=[];responses=[];dialogs=[]
  p.on("pageerror",lambda err: errors.append(str(err)))
  p.on("response",lambda r:responses.append({"status":r.status,"url":r.url}) if r.url.endswith("/api/produce") else None)
  p.on("dialog",lambda dialog: (dialogs.append(dialog.message),dialog.dismiss()))
  p.goto(url,wait_until="domcontentloaded",timeout=20000)
  p.wait_for_function("state.statusReady && !state.isRunning",timeout=20000)
  p.locator("#inSeries").fill(series)
  p.locator("#inEpisode").fill("1")
  p.locator("#inGenre").select_option("whiteboard")
  p.locator("#inVisualStyle").select_option(style)
  p.locator("#inLanguage").select_option("English")
  p.locator("#inRegion").select_option("US")
  p.locator("#inVoice").select_option("auto")
  p.locator("#inImageSource").select_option("mcp_v2")
  p.locator("#inMcpModel").select_option("1")
  p.locator("#inMcpMaxImages").fill("1")
  p.locator("#inMcpVisualReuse").uncheck()
  p.locator("#inResolution").select_option("640x360")
  p.locator("#inMinutes").fill("0.1")
  p.locator("#inSceneSec").fill("8")
  p.locator("#inInputMode").select_option("script")
  p.locator("#inPrompt").fill(prompt)
  print("REAL_STUDIO_LIVE_CLICK",style,series,flush=True)
  p.locator("#btnLive").click(timeout=8000)
  p.wait_for_function("state.isRunning || state.currentSeries==="+json.dumps(series),timeout=25000)
  start=time.monotonic()
  previous=None
  while time.monotonic()-start<330:
   time.sleep(3)
   s=status()
   if s.get("stage")!=previous:
    print("LIVE_UI_STAGE",style,s.get("stage"),s.get("percent"),
          str(s.get("message",""))[:110],flush=True)
    previous=s.get("stage")
   if not s["running"]:break
  else:raise RuntimeError("LIVE_E2E_TIMEOUT_WITHOUT_AUTO_RETRY")
  if s.get("exit_code")!=0:
   print("LIVE_UI_FAILURE_LOG",json.dumps(s.get("recent_logs",[])[-22:],ensure_ascii=False),flush=True)
   raise RuntimeError("LIVE_E2E_FAIL_NO_RESUBMIT_"+style)
  assert s.get("final_video_url") and s.get("series")==series,(style,s)
  p.wait_for_function("state.loadedEpisodeData?.final_video_url && el.cinemaVideo.readyState>=2",timeout=20000)
  media=root/s["final_video_url"].split("?")[0].removeprefix("/media/")
  assert media.is_file(),media
  ep=media.parent
  manifest=json.loads((ep/"manifest.json").read_text(encoding="utf-8"))
  assert manifest["status"]=="PASS" and len(manifest["completed"])==1,manifest
  scene=ep/"scenes"/"scene_0001"
  job=json.loads((scene/"job.json").read_text(encoding="utf-8"))
  assert job["visual_style"]==style and job["image_provider"]=="mcp_v2"
  for f in ("image.png","audio.wav","final.mp4","subtitles.json"):
   assert (scene/f).stat().st_size>0, f
  probe=json.loads(subprocess.run(["ffprobe","-v","error","-show_entries",
    "stream=codec_type,codec_name,width,height:format=duration,size","-of","json",str(media)],
    capture_output=True,text=True,check=True,timeout=30).stdout)
  assert any(x["codec_type"]=="video" for x in probe["streams"])
  assert any(x["codec_type"]=="audio" for x in probe["streams"])
  assert responses[-1]["status"]==200 and not errors,(responses,errors)
  result={"status":"PASS","style":style,"mode":"GUI_LIVE_GOOGLE_FLOW_MCP",
          "series":series,"mp4_path":str(media),"mp4_bytes":media.stat().st_size,
          "duration":float(probe["format"]["duration"]),"actual_new_mcp_images_limit":1,
          "video_codec":next(x["codec_name"] for x in probe["streams"] if x["codec_type"]=="video"),
          "audio_codec":next(x["codec_name"] for x in probe["streams"] if x["codec_type"]=="audio")}
  (ep/"LIVE_GUI_E2E_QC.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
  print("ACTUAL_TOOL_MCP_LIVE_GUI_PASS",json.dumps(result,ensure_ascii=False),flush=True)
  p.close()
 browser.close()
print("ACTUAL_STUDIO_LIVE_MCP_TWO_STYLES_PASS",flush=True)
