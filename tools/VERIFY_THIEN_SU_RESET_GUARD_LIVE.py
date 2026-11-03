import sys,json,time,datetime
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urlencode
sys.stdout.reconfigure(encoding="utf-8",errors="replace")
root=Path(r"D:\STORYBOARD_AI\studio")
ep=root/"productions"/"THI-N-S-HUY-N-PH-TR-N-QU"/"episode_001"
receipt=ep.parent/"EP01_VERIFY_RESET_GUARD_20261031.json"
if receipt.exists():raise RuntimeError("VERIFY_RESET_REQUEST_ALREADY_SUBMITTED")
b=json.loads((ep/"00_ASSET_PACK"/"asset_bible.json").read_text(encoding="utf-8"))
for kind in ("characters","locations","props"):
 for x in b[kind].values():
  folder=ep/"00_ASSET_PACK"/x["folder"]
  assert (folder/"muse_original_4views.png").is_file()
  assert all(Path(v["path"]).is_file() for v in x["views"].values())
assert len(json.loads((ep/"drama_plan.json").read_text(encoding="utf-8"))["scenes"])==66
url="http://127.0.0.1:8765"
s=json.load(urlopen(url+"/api/status",timeout=8))
q=json.loads((root/"production_queue.json").read_text(encoding="utf-8"))
assert not s["running"] and not q["active"] and not q["items"]
prompt=Path(r"D:\STORYBOARD_AI\tools\THIEN_SU_HUYEN_PHU_TRAN_QUY_EP01_IDEA_20261031.txt").read_text(encoding="utf-8")
body={"production_mode":"cinematic_drama","series":"THIÊN SƯ: HUYỀN PHÙ TRẤN QUỶ",
"episode":1,"input_mode":"idea","prompt":prompt,"mode":"live","minutes":11,"scene_seconds":10,
"genre":"psychological_horror","visual_style":"color_cinematic","language":"Vietnamese",
"size":"1280x720","image_provider":"muse_video","workers":2,"model":"gemini-3.5-flash",
"subtitle_style":"karaoke_viral","subtitle_size":58,"auto_upload":False,"resume":True}
receipt.write_text(json.dumps({"state":"SUBMISSION_UNCERTAIN","timestamp":datetime.datetime.now(datetime.timezone.utc).isoformat()},ensure_ascii=True),encoding="utf-8")
req=Request(url+"/api/produce",json.dumps(body,ensure_ascii=False).encode("utf-8"),
{"Content-Type":"application/json; charset=utf-8"},method="POST")
response=json.load(urlopen(req,timeout=40))
receipt.write_text(json.dumps({"state":"ACCEPTED","response":response},ensure_ascii=True),encoding="utf-8")
print("PRODUCTION_RESUME_ACCEPTED",response.get("status"),flush=True)
for i in range(70):
 time.sleep(2)
 st=json.load(urlopen(url+"/api/status",timeout=8))
 if i%5==0:print("LIVE_STAGE",st.get("stage"),"RUNNING",st.get("running"),flush=True)
 if not st["running"]:
  print("BEFORE_RESET",json.dumps({k:st.get(k) for k in ("stage","exit_code","awaiting_asset_review","series","episode")},ensure_ascii=True),flush=True)
  assert st.get("stage")=="AWAITING_ASSET_REVIEW" and st.get("exit_code")==20
  rr=Request(url+"/api/status/reset",b"{}",{"Content-Type":"application/json"},method="POST")
  reset=json.load(urlopen(rr,timeout=10))
  latest=json.load(urlopen(url+"/api/status",timeout=7))
  print("RESET_ENDPOINT_RESPONSE",reset.get("status"),flush=True)
  print("AFTER_RESET",json.dumps({k:latest.get(k) for k in ("stage","exit_code","awaiting_asset_review","series","episode")},ensure_ascii=True),flush=True)
  assert reset.get("status")=="REVIEW_PENDING"
  assert latest.get("stage")=="AWAITING_ASSET_REVIEW"
  receipt.write_text(json.dumps({"state":"PAUSE_AND_RESET_PASS","series":latest.get("series"),"episode":latest.get("episode"),"exit_code":latest.get("exit_code")},ensure_ascii=True,indent=2),encoding="utf-8")
  print("FULL_LIVE_REVIEW_PAUSE_AND_RESET_GUARD_PASS",flush=True)
  raise SystemExit(0)
print("JOB_NOT_FINISHED_WITHIN_POLLS_DO_NOT_RESUBMIT",flush=True)
