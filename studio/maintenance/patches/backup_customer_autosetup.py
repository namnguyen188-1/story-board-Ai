from pathlib import Path
from datetime import datetime
import shutil,hashlib,json
root=Path(r"D:\STORYBOARD_AI")
package=root/"dist"/"Storyboard_AI_Studio_Pro_Transfer_Test_20261015"
stamp=datetime.now().strftime("%Y%m%d_%H%M%S")
b=root/"studio"/"checkpoints"/("CUSTOMER_AUTOSETUP_"+stamp)
for f in ["launcher_src/Storyboard_AI_Studio.cs","dist/TransferTest-FULL-Installer.iss",
          "studio/comfyui_image_provider.py","studio/gpu_capabilities.py"]:
 p=root/f
 out=b/f;out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,out)
for f in ["launcher_transfer.cs","studio/desktop_app.py","studio/comfyui_image_provider.py"]:
 p=package/f
 if p.is_file():
  out=b/"stage"/f;out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,out)
print("BACKUP",b)
