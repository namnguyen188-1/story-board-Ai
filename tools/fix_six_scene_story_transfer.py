import json,sys
from pathlib import Path
sys.path.insert(0,"D:/STORYBOARD_AI/studio")
from cinematic_engine.drama_asset_first import atomic_write,validate_assets
ep=Path("D:/STORYBOARD_AI/studio/scratch/multi_role_asset_first_e2e/episode_006")
pfile=ep/"drama_plan.json";plan=json.loads(pfile.read_text(encoding="utf-8"))
text="After leaving the living room, Minh picks up the red dossier from the wooden table, carries it securely to the company office and places it on the office oak desk before Scene 4 opens. Intentional sequence transition."
plan["scenes"][3]["transition_action"]=text
plan["scenes"][3]["transition_props"]=["ho_so"]
atomic_write(pfile,plan)
mfile=ep/"00_ASSET_PACK"/"asset_bible.json"
m=json.loads(mfile.read_text(encoding="utf-8"))
m["scenes"]["scene_0004"]["transition_action"]=text
m["scenes"]["scene_0004"]["transition_props"]=["ho_so"]
atomic_write(mfile,m)
q=validate_assets(ep,m)
print("CROSS_LOCATION_PROP_TRANSFER_CHECK",json.dumps(q["story_continuity"],ensure_ascii=False),flush=True)
assert q["story_continuity"]["status"]=="PASS_STRUCTURED"
assert len(q["story_continuity"]["authorized_transfers"])==1
