import concurrent.futures,sys,json
from pathlib import Path
sys.path.insert(0,"D:/STORYBOARD_AI/studio")
from cinematic_engine.drama_aspect_repair import normalize_3_2
base=Path("D:/STORYBOARD_AI/studio/scratch/multi_role_asset_first_e2e/episode_006/scenes")
def go(n):
 try:
  result=normalize_3_2(base/("scene_%04d"%n))
  print("MUSE_ASPECT_REPAIRED",n,json.dumps(result,ensure_ascii=False),flush=True)
 except Exception as e:print("MUSE_ASPECT_REPAIR_FAILED",n,str(e),flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(go,(3,4,6)))
