"""Read-only remote verification, then update terminal local Muse receipts safely."""
import sys,os,json
from pathlib import Path
ROOT=Path(r"D:\STORYBOARD_AI\studio")
sys.path.insert(0,str(ROOT))
from muse_accounts import list_accounts,get_account_profile_home
from muse_gateway_worker import GatewayAPI,PATH_RE,atomic_json
EP=ROOT/"productions"/"ho-t-h-nh-3d"/"episode_001"
profiles=list_accounts()
for n in (63,67):
    d=EP/"scenes"/f"scene_{n:04d}"
    rp=d/"muse_job.json"
    receipt=json.loads(rp.read_text(encoding="utf-8"))
    if (d/"muse_clip.mp4").is_file() or receipt.get("state")=="complete":
        print("SCENE",n,"HAS_VERIFIED_CLIP_OR_COMPLETE_SKIP",flush=True);continue
    acc=next((a for a in profiles if a.get("ready") and a.get("vm_id")==receipt.get("account_vm_id")),None)
    if not acc:
        print("SCENE",n,"NO_ACCOUNT_MATCH_PRESERVED",flush=True);continue
    os.environ["USERPROFILE"]=str(get_account_profile_home(acc["id"]))
    api=GatewayAPI()
    try:
        sid,tag=receipt["session_id"],receipt["tag"]
        sessions=api.call("sessions.list").get("sessions",[])
        found=next((s for s in sessions if s.get("session_id",s.get("id"))==sid),{})
        if found.get("status") not in ("completed","idle"):
            print("SCENE",n,"REMOTE_STILL_NOT_TERMINAL_PRESERVED",flush=True);continue
        ev=api.call("chat.history",{"session_id":sid,"limit":60}).get("chat_events",[])
        def visible(e): return str((e.get("payload") or {}).get("display_text") or e.get("display_text") or "")
        assert any(e.get("event_name")=="message.user" and tag in visible(e) for e in ev), "Remote job tag not confirmed"
        text="\n".join(visible(e) for e in ev if e.get("event_name")=="message.assistant")
        if not text.strip():
            print("SCENE",n,"NO_REPLY_YET_PRESERVED",flush=True);continue
        if any(p.lower().endswith(".mp4") for p in PATH_RE.findall(text)):
            print("SCENE",n,"VIDEO_POSSIBLY_AVAILABLE_NEEDS_DOWNLOAD_PRESERVED",flush=True);continue
        low=text.lower()
        reason=("integrity_check_failed" if "integrity_check_failed" in low
                else "no_video_review_required" if any(term in low for term in (
                    "different take","content policy","safety policy","refused",
                    "moderation","cannot help","can't assist"))
                else "no_video_after_completion")
        receipt["state"]="failed"
        receipt["terminal_reason"]=reason
        receipt["terminal_verified_by"]="remote_status_and_history"
        atomic_json(rp,receipt)
        print("SCENE",n,"VERIFIED_TERMINAL_FAILED",reason,flush=True)
    except Exception as e:
        print("SCENE",n,"UNCONFIRMED_PRESERVED",type(e).__name__,flush=True)
    finally:api.close()
