"""Resume only the saved THIEN SU 66-scene plan to verify review pause.
No AI re-planning; no repeat master generation because all 17 sheets exist.
One POST only; receipt prevents duplicate submits.
"""
from pathlib import Path
from urllib import request,error
from collections import Counter
import json,time,datetime
root=Path(r"D:\STORYBOARD_AI\studio")
ep=root/"productions"/"THI-N-S-HUY-N-PH-TR-N-QU"/"episode_001"
receipt=ep.parent/"EP01_VERIFY_GRACEFUL_REVIEW_PAUSE_20261031.json"
if receipt.exists():
 print("ALREADY_ATTEMPTED",receipt.read_text(encoding="utf-8")[:800],flush=True)
 raise SystemExit(0)
assert len(json.loads((ep/"drama_plan.json").read_text(encoding="utf-8"))["scenes"])==66
qc=json.loads((ep/"00_ASSET_PACK"/"asset_qc.json").read_text(encoding="utf-8"))
assert len(qc["blocked"])==17 and set(x["reason"] for x in qc["blocked"])=={"AWAITING_VISUAL_APPROVAL"}
for kind in ("characters","locations","props"):
 for item in json.loads((ep/"00_ASSET_PACK"/"asset_bible.json").read_text(encoding="utf-8"))[kind].values():
  folder=ep/"00_ASSET_PACK"/item["folder"]
  assert (folder/"muse_original_4views.png").is_file()
  assert all(Path(meta["path"]).is_file() for meta in item["views"].values())
with request.urlopen("http://127.0.0.1:8765/api/status",timeout=7) as rr:
 current=json.load(rr)
queue=json.loads((root/"production_queue.json").read_text(encoding="utf-8"))
assert not current.get("running") and not queue["active"] and not queue["items"]
prompt=Path(r"D:\STORYBOARD_AI\tools\THIEN_SU_HUYEN_PHU_TRAN_QUY_EP01_IDEA_20261031.txt").read_text(encoding="utf-8")
payload={
 "production_mode":"cinematic_drama","series":"THIÊN SƯ: HUYỀN PHÙ TRẤN QUỶ","episode":1,
 "input_mode":"idea","prompt":prompt,"mode":"live","minutes":11,"scene_seconds":10,
 "genre":"psychological_horror","visual_style":"color_cinematic","language":"Vietnamese",
 "size":"1280x720","image_provider":"muse_video","workers":2,"model":"gemini-3.5-flash",
 "subtitle_style":"karaoke_viral","subtitle_size":58,"voice_name":"auto",
 "auto_upload":False,"resume":True
}
state={"state":"SUBMISSION_UNCERTAIN","utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
       "real_master_images_preserved":17,"saved_plan_scenes":66}
receipt.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding="utf-8")
try:
 body=json.dumps(payload,ensure_ascii=False).encode("utf-8")
 req=request.Request("http://127.0.0.1:8765/api/produce",body,
                    {"Content-Type":"application/json; charset=utf-8"},method="POST")
 with request.urlopen(req,timeout=45) as rr:
  reply=json.load(rr)
  state.update(state="ACCEPTED" if reply.get("status")=="STARTED" else "UNEXPECTED_REPLY",
               http_code=rr.status,response=reply)
except Exception as ex:
 state.update(state="UNCERTAIN_NO_RESUBMIT",error=str(ex))
receipt.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding="utf-8")
print("LIVE_RESUME_REQUEST",json.dumps({k:v for k,v in state.items() if k!="response"},ensure_ascii=False),flush=True)
if state["state"]!="ACCEPTED":raise SystemExit(1)
# Poll until intentional pause; no repeated POST.
for index in range(90):
 time.sleep(2)
 try:
  with request.urlopen("http://127.0.0.1:8765/api/status",timeout=6) as rr:
   s=json.load(rr)
 except Exception as exc:
  print("STATUS_TEMPORARY_READ_FAILURE",str(exc),flush=True);continue
 if index%6==0:
  print("LIVE_PROGRESS",json.dumps({k:s.get(k) for k in ("running","stage","percent","message","exit_code")},ensure_ascii=False),flush=True)
 if not s.get("running"):
  state.update(final_stage=s.get("stage"),final_exit_code=s.get("exit_code"),
               final_message=s.get("message"))
  receipt.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding="utf-8")
  print("LIVE_RESUME_FINAL",json.dumps({k:state.get(k) for k in ("final_stage","final_exit_code","final_message")},ensure_ascii=False),flush=True)
  raise SystemExit(0 if s.get("stage")=="AWAITING_ASSET_REVIEW" and s.get("exit_code")==20 else 2)
print("LIVE_JOB_STILL_RUNNING_NO_RETRY",flush=True)
