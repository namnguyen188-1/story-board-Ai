import sys,json
from pathlib import Path
sys.path.insert(0,r"D:\STORYBOARD_AI\studio")
from cinematic_engine.drama_asset_first import bind_scene,atomic_write
p=Path(r"D:\STORYBOARD_AI\studio\scratch\multi_role_asset_first_e2e\episode_001")
sc=p/"scenes"/"scene_0001";f=sc/"scene_master.json"
a=json.loads(f.read_text(encoding="utf-8"))
a["approved"]=True
a["reviewer"]="ChatGPT visual inspection of Muse scene still (isolated staging only)"
a["review_notes"]="Character wearing consistent beige coat; same family living room geometry, gray sofa and wood table; black phone visible. Movie-frame continuity pending video QC."
atomic_write(f,a)
scene=json.loads((p/"drama_plan.json").read_text(encoding="utf-8"))["scenes"][0]
b=bind_scene(p,scene,verify_scene_image=True)
print("MUSE_SCENE_STILL_APPROVED_FOR_E2E",b["binding_sha256"],flush=True)
