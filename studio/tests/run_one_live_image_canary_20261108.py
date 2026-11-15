import json,sys,time,traceback
from pathlib import Path
root=Path(r"D:\STORYBOARD_AI\studio")
sys.path.insert(0,str(root))
from studio_mcp.accounts import active_account,account_tool_url
from studio_mcp.auto_flow_manager import ensure_ready
from studio_mcp.production_tab import prepare,abandon_fresh
from studio_mcp.transport import LocalFlowMcpTransport
from studio_mcp.image_backend import StoryboardImageTransport,validate_image_tool_readiness
from mcp_v2_images import make_image
import urllib.request
status=json.load(urllib.request.urlopen("http://127.0.0.1:8765/api/status",timeout=4))
if status.get("running"):raise RuntimeError("PRODUCTION_BUSY_NO_LIVE_TEST")
account=active_account();url=account_tool_url(account)
ready=ensure_ready("auto",allow_open=False,account=account)
if not ready.get("ready"):raise RuntimeError("MCP_NOT_READY_NO_SUBMIT "+str(ready.get("code")))
out=root/"runtime"/"single_lane_live_canary_20261108_1800"
out.mkdir(parents=True,exist_ok=True)
target=None
report={"account_id":account["id"],"account_ready":True,"session_prepared":False,
        "image_submitted":False,"image_generated":False,"model":"Nano Banana 2 Lite","max_new_images":1,
        "fallback":False,"aspect_ratio":"16:9","other_accounts_used":False,
        "output_path":str(out/"one_scene.png")}
try:
 target=prepare(account,url)
 report["session_prepared"]=True
 mcp=LocalFlowMcpTransport(timeout=240,target_id=target)
 h=mcp("flow_storyboard_native_image",{"action":"health","tool_url":url},account=account)
 h=h.get("result",h)
 validate_image_tool_readiness(h,require_queue=True,scoped_production_target=target)
 prompt=("Create exactly one entirely original cinematic photorealistic image, horizontal 16:9: "
         "a small weathered wooden sailboat with a vivid red triangular sail drifting over a calm deep-blue ocean "
         "at golden sunrise; distant rocky cliffs, delicate morning mist, gentle golden reflections. "
         "The boat occupies the left third of the frame and the sun rises on the right. "
         "Wide establishing composition, realistic natural color and detail, no people. "
         "Do not add text, typography, watermarks or logos. Generate a single still image.")
 report["image_submitted"]=True
 path=make_image(prompt,out/"one_scene.png",series="ONE_LANE_SAFE_CANARY_20261108_1800",
        episode=1,scene=1,max_new_images=1,model_index=1,fallback=False,aspect_ratio="16:9",
        transport=StoryboardImageTransport(mcp=mcp,tool_url=url))
 p=Path(path);report["image_generated"]=p.is_file() and p.stat().st_size>1000
 report["bytes"]=p.stat().st_size
except Exception as exc:
 report["error_type"]=type(exc).__name__
 report["error"]=str(exc)[:1150]
finally:
 if target:
  try:
   release=abandon_fresh(account,url,target)
   report["existing_tab_preserved"]=bool(release.get("kept"))
  except Exception as e:report["release_error"]=type(e).__name__
 report_path=out/"result.json"
 report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf8")
 print(json.dumps(report,ensure_ascii=True))
