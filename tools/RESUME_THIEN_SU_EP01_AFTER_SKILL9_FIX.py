"""Resume the interrupted THIEN SU episode 1 via Storyboard AI API.
Existing 66-scene screenplay must be reused verbatim; submission one-shot.
"""
from pathlib import Path
from urllib import request,error
import json,datetime,sys
from series_studio import slug
root=Path(r"D:\STORYBOARD_AI\studio")
series="THIÊN SƯ: HUYỀN PHÙ TRẤN QUỶ"
ep=root/"productions"/slug(series)/"episode_001"
plan=ep/"drama_plan.json"
receipt=ep.parent/"EP01_RESUME_AFTER_SKILL9_FIX_RECEIPT.json"
if receipt.exists():
    print("RESUME_SUBMISSION_ALREADY_ATTEMPTED",receipt.read_text(encoding="utf-8")[:600],flush=True)
    raise SystemExit(0)
if not plan.is_file():raise RuntimeError("DO_NOT_RESUME_WITHOUT_SAVED_PLAN")
data=json.loads(plan.read_text(encoding="utf-8"))
if len(data.get("scenes") or [])!=66:raise RuntimeError("SAVED_PLAN_NOT_66_SCENES")
with request.urlopen("http://127.0.0.1:8765/api/status",timeout=8) as r:
    status=json.load(r)
queue=json.loads((root/"production_queue.json").read_text(encoding="utf-8"))
if status.get("running") or queue.get("active") or queue.get("items"):
    raise RuntimeError("PRODUCTION_IS_BUSY")
prompt=Path(r"D:\STORYBOARD_AI\tools\THIEN_SU_HUYEN_PHU_TRAN_QUY_EP01_IDEA_20261031.txt").read_text(encoding="utf-8")
body={
 "production_mode":"cinematic_drama","series":series,"episode":1,
 "prompt":prompt,"input_mode":"idea","minutes":11.0,"scene_seconds":10,
 "language":"Vietnamese","voice_name":"auto","speech_pacing":"normal",
 "genre":"psychological_horror","visual_style":"color_cinematic",
 "user_explicit_genre":True,"user_explicit_style":True,
 "mode":"live","image_provider":"muse_video","model":"gemini-3.5-flash",
 "size":"1280x720","workers":2,"subtitle_style":"karaoke_viral",
 "subtitle_size":58,"auto_upload":False,"resume":True
}
audit={"state":"UNCERTAIN_REQUEST_IN_FLIGHT","series":series,
       "episode":1,"saved_plan_scene_count":66,"reason":"corrected skill 9 sanitizer for scenes 50-51",
       "submitted_utc":datetime.datetime.now(datetime.timezone.utc).isoformat()}
receipt.write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding="utf-8")
try:
    req=request.Request("http://127.0.0.1:8765/api/produce",
        json.dumps(body,ensure_ascii=False).encode("utf-8"),
        {"Content-Type":"application/json; charset=utf-8"},method="POST")
    with request.urlopen(req,timeout=45) as r:
        result=json.load(r)
        audit.update(state="ACCEPTED" if r.status==200 and result.get("status")=="STARTED" else "CHECK_RESPONSE",
                     http_code=r.status,response=result)
except error.HTTPError as e:
    audit.update(state="REJECTED",http_code=e.code,response=e.read().decode("utf-8",errors="replace")[:1200])
except Exception as e:
    audit.update(state="UNCERTAIN_DO_NOT_RESUBMIT",error=str(e))
receipt.write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding="utf-8")
print("THIEN_SU_EP01_RESUME_AFTER_FIX",json.dumps(audit,ensure_ascii=False),flush=True)
