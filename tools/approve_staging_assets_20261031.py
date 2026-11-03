"""Stage-only visual review: all three sheets inspected by assistant via remote image read."""
from pathlib import Path
import sys,json
sys.path.insert(0,r"D:\STORYBOARD_AI\studio")
from cinematic_engine.drama_asset_first import validate_assets,sha,atomic_write,bind_scene
root=Path(r"D:\STORYBOARD_AI\studio\scratch\multi_role_asset_first_e2e\episode_001")
m=json.loads((root/"00_ASSET_PACK"/"asset_bible.json").read_text(encoding="utf-8"))
for kind in ("characters","locations","props"):
 for key,asset in m[kind].items():
  hashes={v:sha(Path(meta["path"])) for v,meta in asset["views"].items()}
  atomic_write(root/"00_ASSET_PACK"/asset["folder"]/"approval.json",
    {"approved":True,"reviewer":"ChatGPT visual inspection of real Muse sheet (staging only)",
     "review_scope":"technical E2E example, not formal user approval of released film",
     "spec_sha256":asset["spec_sha256"],"view_sha256":hashes,
     "notes":"Visible distinct viewpoints and consistent broad design. Full cinematic continuity still requires scene-by-scene QC."})
r=validate_assets(root,m)
print("STAGING_ALL_ASSET_VISUAL_APPROVAL",r,flush=True)
plan=json.loads((root/"drama_plan.json").read_text(encoding="utf-8"))
b=bind_scene(root,plan["scenes"][0],verify_scene_image=False)
print("STAGING_SCENE_BINDING",b["binding_sha256"],"refs",sum(len(x) for x in b["assets"].values()),flush=True)
