import json,sys
from pathlib import Path
sys.path.insert(0,"D:/STORYBOARD_AI/studio")
from cinematic_engine.drama_asset_first import build_manifest,validate_assets,atomic_write
root=Path("D:/STORYBOARD_AI/studio/scratch/multi_role_asset_first_e2e")
src=root/"episode_006";dst=root/"episode_007"
dst.mkdir(parents=True,exist_ok=True)
plan=json.loads((src/"drama_plan.json").read_text(encoding="utf-8"))
plan["episode_num"]=7
atomic_write(dst/"drama_plan.json",plan)
m=build_manifest(dst,plan)
q=validate_assets(dst,m)
print("CROSS_EPISODE_APPROVED_MASTER_REUSE",json.dumps(q,ensure_ascii=False),flush=True)
assert q["status"]=="READY",q
import pathlib
print("NO_FRESH_GENERATION_REQUIRED",len(m["characters"])+len(m["locations"])+len(m["props"]),flush=True)
