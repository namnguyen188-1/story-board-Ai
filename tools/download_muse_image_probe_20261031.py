import sys, json, traceback
from pathlib import Path
sys.path.insert(0,r"D:\STORYBOARD_AI\studio")
from muse_gateway_worker import GatewayAPI,download,workspace_path
from PIL import Image
base=Path(r"D:\STORYBOARD_AI\studio\scratch\multi_role_asset_first_e2e")
path="workspace/storyboard_preproduction/lan_4angle_sheet.png"
api=GatewayAPI()
try:
 print("MUSE_ASSET_REMOTE_STAT",api.call("fs.stat",{"path":path}),flush=True)
 target=base/"lan_4angle_sheet_from_muse.png"
 proof=download(api,path,target)
 with Image.open(target) as img:
  print("MUSE_ASSET_IMAGE_PROPERTIES",img.size,img.mode,flush=True)
  img.verify()
 print("MUSE_ASSET_IMAGE_DOWNLOAD_PASS",json.dumps(proof,ensure_ascii=False),flush=True)
 (base/"muse_image_proof.json").write_text(json.dumps(proof,ensure_ascii=False,indent=2),encoding="utf-8")
except Exception as e:
 print("MUSE_ASSET_IMAGE_DOWNLOAD_FAIL",type(e).__name__,str(e)[:350],flush=True)
finally:
 api.close()
