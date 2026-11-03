from pathlib import Path
import sys,json
p=Path(r"D:\STORYBOARD_AI\studio")
sys.path.insert(0,str(p))
import muse_accounts
from muse_video_provider import format_real_acting_prompt
lst=muse_accounts.get_ready_accounts()
reg=muse_accounts.load_registry()
print("READY_MUSE_ACCOUNT_COUNT",len(lst),"TOTAL_REGISTERED",len(reg.get("accounts") or []),"DISPATCH_MODE",reg.get("dispatch_mode"))
p1=p/"productions"/"ho-t-h-nh"/"episode_001"/"drama_plan.json"
if p1.exists():
 j=json.loads(p1.read_text(encoding="utf-8"))
 print("EXISTING_PLAN_KEYS", sorted(j.keys()))
 print("CAST_SIZE",len(j.get("cast") or {}))
 print("FIRST_CAST_HAS_APPEARANCE",bool(next(iter((j.get("cast") or {}).values()),{}).get("appearance_lock") or next(iter((j.get("cast") or {}).values()),{}).get("appearance")))
 print("FIRST_SCENE_KEYS",sorted((j.get("scenes") or [{}])[0].keys()))
