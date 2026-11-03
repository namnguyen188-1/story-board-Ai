import sys,json
from pathlib import Path
sys.path.insert(0,"D:/STORYBOARD_AI/studio")
from cinematic_engine.drama_asset_first import atomic_write,bind_scene,validate_assets
ep=Path("D:/STORYBOARD_AI/studio/scratch/multi_role_asset_first_e2e/episode_006")
plan=json.loads((ep/"drama_plan.json").read_text(encoding="utf-8"))
assert validate_assets(ep)["status"]=="READY"
for sc in plan["scenes"]:
 n=sc["scene_number"]
 folder=ep/"scenes"/("scene_%04d"%n)
 proof_file=folder/"scene_master.json"
 p=json.loads(proof_file.read_text(encoding="utf-8"))
 assert p.get("source")=="Muse generated scene still"
 p.update(approved=True,reviewer="ChatGPT direct visual review of six Muse scene stills in montage",
          review_scope="isolated six-scene E2E still images only; moving-video continuity still unapproved",
          notes="Master rooms, cast clothing, prop ownership, and material checked; scene1 sofa and scene4 key visibility were selectively regenerated.")
 atomic_write(proof_file,p)
 b=bind_scene(ep,sc,verify_scene_image=True)
 print("SCENE_IMAGE_VISUAL_QC_APPROVED",n,b["binding_sha256"][:12],flush=True)
print("SIX_SCENE_IMAGES_READY_FOR_MUSE_I2V",flush=True)
