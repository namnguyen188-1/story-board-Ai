import sys,json
from pathlib import Path
sys.path.insert(0,"D:/STORYBOARD_AI/studio")
import muse_accounts
for n in (1,2,3,4,5,6):
 acc=muse_accounts.get_account_for_scene(n)
 print("ACCOUNT_ID",n,(acc or {}).get("id"),flush=True)
base=Path("D:/STORYBOARD_AI/studio/scratch/multi_role_asset_first_e2e/episode_006")
p=json.loads((base/"drama_plan.json").read_text(encoding="utf-8"))
for scene in p["scenes"]:
 n=scene["scene_number"]
 folder=base/"scenes"/("scene_%04d"%n)
 subs=folder/"subtitles.json"
 text=subs.read_text(encoding="utf-8")[:700] if subs.is_file() else "NOT_FOUND"
 print("SUBS",n,"EXPECTED",[(b["speaker"],b["text"]) for b in scene.get("dialogue_beats",[])],"ACTUAL",text,flush=True)
