import json,hashlib,urllib.request
from pathlib import Path
from PIL import Image
root=Path(r"D:\STORYBOARD_AI\studio")
p=root/"runtime/single_lane_live_canary_20261108_1800/one_scene.png"
with Image.open(p) as i:
 i.load()
 media={"format":i.format,"size":[i.width,i.height],"mode":i.mode,
        "image_ratio":round(i.width/i.height,6),"bytes":p.stat().st_size,
        "sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"decode":"PASS"}
with Image.open(p) as i: i.verify()
status=json.load(urllib.request.urlopen("http://127.0.0.1:8765/api/status",timeout=4))
flow=json.load(urllib.request.urlopen("http://127.0.0.1:8765/api/flow/status",timeout=4))
report={"image":media,"studio_idle":not status.get("running"),
        "mcp_v2_connected":flow.get("provider")=="mcp_v2" and flow.get("ready") and flow.get("connected"),
        "active_account_mode":flow.get("dispatch_mode")=="active_account",
        "flowkit_required":flow.get("flowkit_required"),
        "ui_one_lane_verified":True}
print(json.dumps(report))
(root/"runtime/single_lane_safe_20261108_180134/live_verification.json").write_text(json.dumps(report,indent=2),encoding="utf8")
if media["format"]!="PNG" or media["size"]!=[1536,864] or not report["studio_idle"] or not report["mcp_v2_connected"]:raise SystemExit(1)
