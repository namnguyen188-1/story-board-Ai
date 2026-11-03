"""One-scene isolated production-quality asset-first E2E staging:
- Lan 4 actual rendered angles from confirmed Muse image
- location + prop planned and status-blocked pending actual image and QC
No user production episode overwritten.
"""
from pathlib import Path
import json,sys,shutil
root=Path(r"D:\STORYBOARD_AI\studio")
sys.path.insert(0,str(root))
from cinematic_engine.drama_asset_first import build_manifest,validate_assets,atomic_write,sha
from muse_asset_images import _import_sheet
dest=root/"scratch"/"multi_role_asset_first_e2e"/"episode_001"
source=root/"scratch"/"multi_role_asset_first_e2e"/"lan_4angle_sheet_from_muse.png"
cast={"Lan":{"appearance_lock":"Vietnamese woman age 34, oval face, warm ivory skin, small mole under left eye, shoulder-length black hair side part","attire":"beige trench coat, dark burgundy knitted turtleneck, burgundy trousers and footwear"}}
scene={"scene_number":1,"setting":"Vietnamese family living room, warm beige walls, one grey fabric couch on the west wall, a wooden coffee table in front of the couch, one window behind the couch, right-hand entrance door",
"summary":"Lan stands by the grey couch holding a black smartphone, confronting a person offscreen",
"visual_setup":"Wide shot of Lan standing beside gray fabric sofa, her black phone in the left hand, wooden coffee table and window in background",
"start_state":"Lan stands beside couch holding phone in left hand, door shut",
"end_state":"Lan keeps phone in left hand, maintains position near couch",
"characters_present":["Lan"],"props_required":["dien_thoai"],
"dialogue_beats":[{"speaker":"Lan","text":"Anh đã giấu em điều gì?","action":"Lan raises her black smartphone"}]}
plan={"series_name":"AssetFirst E2E Lab","title":"Lan in living room","episode_num":1,
 "genre":"family_drama","cast":cast,"scenes":[scene],"language":"Vietnamese"}
dest.mkdir(parents=True,exist_ok=True)
atomic_write(dest/"drama_plan.json",plan)
manifest=build_manifest(dest,plan)
lan=manifest["characters"]["lan"]
folder=dest/"00_ASSET_PACK"/lan["folder"]
shutil.copy2(source,folder/"muse_original_4views.png")
result=_import_sheet(folder/"muse_original_4views.png",lan,"characters",folder,folder/"muse_sheet_receipt.json",already_downloaded=True)
print("LAN_4VIEW_IMPORTED",result["images"],flush=True)
report=validate_assets(dest,manifest)
print("ASSET_PREFLIGHT",json.dumps(report,ensure_ascii=False),flush=True)
print("STAGING_EPISODE",dest,flush=True)
