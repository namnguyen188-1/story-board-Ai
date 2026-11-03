import concurrent.futures,sys,json,time
from pathlib import Path
sys.path.insert(0,"D:/STORYBOARD_AI/studio")
from muse_scene_image import generate_scene
ep=Path("D:/STORYBOARD_AI/studio/scratch/multi_role_asset_first_e2e/episode_006")
plan=json.loads((ep/"drama_plan.json").read_text(encoding="utf-8"))
def scene_job(sc):
 n=sc["scene_number"]
 print("SCENE_IMAGE_MUSE_START",n,flush=True)
 try:
  x=generate_scene(ep,sc,timeout_s=270)
  print("SCENE_IMAGE_MUSE_RESULT",n,x["status"],flush=True)
  return {"scene":n,"status":x["status"],"file":x["scene_image_path"]}
 except Exception as e:
  print("SCENE_IMAGE_MUSE_BLOCKED",n,str(e),flush=True)
  return {"scene":n,"status":"BLOCKED","error":str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 results=list(pool.map(scene_job,plan["scenes"]))
print("ALL_SIX_SCENE_IMAGE_RESULTS",json.dumps(results,ensure_ascii=False),flush=True)
(ep/"six_scene_images_report.json").write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding="utf-8")
