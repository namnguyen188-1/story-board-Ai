"""Actual Studio AI Produce button E2E: one live MCP request must fail-fast 409,
before plan creation or paid reservations, preserving user's Flow prompt.
"""
from pathlib import Path
import json,time,urllib.request,urllib.parse
from playwright.sync_api import sync_playwright
root=Path(r"D:\STORYBOARD_AI\studio")
series="Queue Guard GUI QA 20261013 1458"
target=root/"productions"/"Queue-Guard-GUI-QA-20261013-1458"/"episode_001"
assert not target.exists(),"Must not overwrite production"
def status():
 with urllib.request.urlopen("http://127.0.0.1:8765/api/status",timeout=8) as r:return json.load(r)
assert status()["running"] is False
inbox=root/"inbox"
before={p.name for p in inbox.glob("web_prompt_*.txt")}
speech='''SHOT 1
FORMAT & STYLE: An 8-second continuous original family-friendly hand-drawn scene.
SETTING: A riverside village with a tiny clock tower, a stone bridge and a yellow kite.
CAMERA: Fixed wide 16:9 composition, watercolor image without logos or text.
TIMED ACTION: The illustrator draws the clock tower and bridge as the sun rises.
AUDIO:
Narration: "A new morning arrives as the clock tower welcomes a gentle breeze."
CONSTRAINTS: Original art, no real individuals, no violent content.
'''
with sync_playwright() as pw:
 browser=pw.chromium.launch(channel="msedge",headless=True)
 page=browser.new_page(viewport={"width":1440,"height":920})
 alerts=[];exceptions=[];responses=[]
 page.on("dialog",lambda dialog:(alerts.append(dialog.message),dialog.dismiss()))
 page.on("pageerror",lambda e:exceptions.append(str(e)))
 page.on("response",lambda r:responses.append(r) if r.url.endswith("/api/produce") else None)
 page.goto("http://127.0.0.1:8765",wait_until="domcontentloaded",timeout=20000)
 page.wait_for_function("state.statusReady && !state.isRunning",timeout=15000)
 page.locator("#inSeries").fill(series)
 page.locator("#inEpisode").fill("1")
 page.locator("#inGenre").select_option("whiteboard")
 page.locator("#inVisualStyle").select_option("whiteboard")
 page.locator("#inLanguage").select_option("English")
 page.locator("#inRegion").select_option("US")
 page.locator("#inImageSource").select_option("mcp_v2")
 page.locator("#inMcpModel").select_option("1")
 page.locator("#inMcpMaxImages").fill("1")
 page.locator("#inMcpVisualReuse").uncheck()
 page.locator("#inResolution").select_option("640x360")
 page.locator("#inMinutes").fill("0.1")
 page.locator("#inSceneSec").fill("8")
 page.locator("#inInputMode").select_option("script")
 page.locator("#inPrompt").fill(speech)
 print("CLICK_LIVE_GUI_UNMOCKED_WITH_POPULATED_USER_FLOW_QUEUE",flush=True)
 page.locator("#btnLive").click(timeout=9000)
 page.wait_for_function("!state.submitting",timeout=85000)
 assert responses,"Expected a real /api/produce HTTP request"
 res=responses[-1]
 payload=res.json()
 assert res.status==409,(res.status,payload)
 assert payload.get("code")=="MCP_QUEUE_PREFLIGHT_BLOCKED",payload
 assert payload.get("reason")=="STORYBOARD_IMAGE_TOOL_QUEUE_STALE_NO_SUBMIT",payload
 assert payload.get("production_started") is False
 assert alerts and "Web Tool" in alerts[-1],alerts
 assert not exceptions,exceptions
 assert page.locator("#inPrompt").input_value()==speech
 print("ACTUAL_GUI_409_FASTFAIL",json.dumps({"http":res.status,"reason":payload["reason"],"dialog":alerts[-1][:155]},ensure_ascii=False),flush=True)
 browser.close()
after={p.name for p in inbox.glob("web_prompt_*.txt")}
assert after==before,("Unexpected API prompt inbox writes",after-before)
assert not target.exists(),"A blocked job must not create a production"
assert status()["running"] is False
print("REAL_UI_E2E_NO_SCRIPT_API_NO_MCP_PAID_JOURNAL_PASS",flush=True)
