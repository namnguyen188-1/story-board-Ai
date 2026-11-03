"""One-shot live scene generation resume. Never restart master generation."""
import sys,json,datetime
from pathlib import Path
from urllib.request import Request,urlopen
sys.path.insert(0,r"D:\STORYBOARD_AI\studio")
from cinematic_engine.drama_asset_first import validate_assets,bind_scene
root=Path(r"D:\STORYBOARD_AI\studio")
ep=root/"productions"/"THI-N-S-HUY-N-PH-TR-N-QU"/"episode_001"
receipt=ep.parent/"EP01_RUN_AFTER_17_MASTER_APPROVAL.json"
assert not receipt.exists(),"ALREADY_SUBMITTED_DO_NOT_RETRY"
q=validate_assets(ep)
assert q["status"]=="READY",q["blocked"]
plan=json.loads((ep/"drama_plan.json").read_text(encoding="utf-8"))
assert len(plan["scenes"])==66
reference=bind_scene(ep,plan["scenes"][0],verify_scene_image=False)
print("SCENE_001_ASSET_BINDING_PASS",reference["binding_sha256"],flush=True)
base="http://127.0.0.1:8765"
current=json.load(urlopen(base+"/api/status",timeout=8))
queue=json.loads((root/"production_queue.json").read_text(encoding="utf-8"))
assert current.get("running")==False and not queue["active"] and not queue["items"]
payload={"production_mode":"cinematic_drama","series":"THIÊN SƯ: HUYỀN PHÙ TRẤN QUỶ",
 "episode":1,"input_mode":"idea",
 "prompt":Path(r"D:\STORYBOARD_AI\tools\THIEN_SU_HUYEN_PHU_TRAN_QUY_EP01_IDEA_20261031.txt").read_text(encoding="utf-8"),
 "mode":"live","minutes":11,"scene_seconds":10,"genre":"psychological_horror",
 "visual_style":"color_cinematic","language":"Vietnamese",
 "size":"1280x720","image_provider":"muse_video","workers":2,
 "model":"gemini-3.5-flash","subtitle_style":"karaoke_viral","subtitle_size":58,
 "auto_upload":False,"resume":True}
r={"state":"UNCONFIRMED","requested_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),
   "scene_count":66,"asset_qc":"READY","master_groups":17}
receipt.write_text(json.dumps(r,ensure_ascii=True,indent=2),encoding="utf-8")
try:
 req=Request(base+"/api/produce",json.dumps(payload,ensure_ascii=False).encode("utf-8"),
             {"Content-Type":"application/json;charset=utf-8"},method="POST")
 with urlopen(req,timeout=40) as resp:
  data=json.load(resp)
  r.update(http_code=resp.status,state="ACCEPTED" if data.get("status")=="STARTED" else "RESPONSE_CHECK",
           response=data)
except Exception as exc:
 r.update(state="UNCERTAIN_NO_RESUBMIT",error=str(exc))
receipt.write_text(json.dumps(r,ensure_ascii=True,indent=2),encoding="utf-8")
print("THIEN_SU_ACTUAL_PRODUCTION_SUBMISSION",
 json.dumps({k:v for k,v in r.items() if k!="response"},ensure_ascii=True),flush=True)
