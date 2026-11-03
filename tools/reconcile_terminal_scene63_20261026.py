"""Verify terminal remote state before local mutation; NEVER submits Muse jobs."""
import json,os,sys
from pathlib import Path
ROOT=Path(r"D:\STORYBOARD_AI\studio")
sys.path.insert(0,str(ROOT))
from muse_accounts import list_accounts,get_account_profile_home
from muse_gateway_worker import GatewayAPI,PATH_RE,atomic_json
scene_dir=ROOT/"productions"/"ho-t-h-nh-3d"/"episode_001"/"scenes"/"scene_0063"
receipt_path=scene_dir/"muse_job.json"
r=json.loads(receipt_path.read_text(encoding="utf-8"))
assert r.get("state")=="accepted", r.get("state")
acc=next(a for a in list_accounts() if a.get("ready") and a.get("vm_id")==r.get("account_vm_id"))
os.environ["USERPROFILE"]=str(get_account_profile_home(acc["id"]))
api=GatewayAPI()
try:
    sess=next((s for s in api.call("sessions.list").get("sessions",[]) if s.get("session_id",s.get("id"))==r["session_id"]),{})
    assert sess.get("status")=="completed", sess.get("status")
    ev=api.call("chat.history",{"session_id":r["session_id"],"limit":60}).get("chat_events",[])
    def vis(e):return str((e.get("payload") or {}).get("display_text") or e.get("display_text") or "")
    assert any(e.get("event_name")=="message.user" and r["tag"] in vis(e) for e in ev),"no accepted tag"
    txt="\n".join(vis(e) for e in ev if e.get("event_name")=="message.assistant")
    assert txt.strip(),"no assistant completion"
    videos=[p for p in PATH_RE.findall(txt) if p.lower().endswith(".mp4")]
    assert not videos,"video exists; do not mark failed"
    low=txt.lower()
    assert not any(word in low for word in ("cannot help","can't assist","content policy","safety policy","moderation","i cannot","refused","policy violation","bị từ chối")), "possible refusal, don't retry"
    r["state"]="failed"
    r["terminal_reason"]="no_video_after_completion"
    r["terminal_verified_by"]="read_only_remote_session_check"
    atomic_json(receipt_path,r)
    print("SCENE_63_REMOTE_COMPLETED_NO_VIDEO_CONFIRMED",flush=True)
    print("LOCAL_RECEIPT_SET_FAILED_WITH_REASON",flush=True)
finally:
    api.close()
