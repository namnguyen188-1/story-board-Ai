import sys, time, json, hashlib
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT=Path(r"D:\STORYBOARD_AI\studio")
sys.path.insert(0,str(ROOT))
from comfyui_image_provider import make_image
src=ROOT/"productions"/"DRAMA"/"episode_001"/"00_ASSET_PACK"/"characters"
dst=ROOT/"scratch"/"E2E_REFERENCE_VOICE_20261031"/"comfyui"
dst.mkdir(parents=True,exist_ok=True)
refs=[src/"lan_turnaround.jpg",src/"minh_turnaround.jpg"]
assert all(p.exists() for p in refs)
t=time.time()
print("COMFY_LIVE_IMAGE_TEST_START",flush=True)
try:
   pic=Path(make_image(
      "Cinematic realistic Vietnamese family drama, Minh and Lan argue in a luxury dimly lit apartment in rainy evening; both persons visible shoulder to waist, natural expressions, maintain two clearly distinct identities and costume from reference turnarounds; documentary cinema lighting, no text.",
      dst/"two_character_reference_scene.png",
      reference_path=refs[0],character_reference_paths=[str(refs[1])],
      visual_style="cinematic",genre="drama",width=768,height=448,timeout=175))
   from PIL import Image
   with Image.open(pic) as im:
      w,h=im.size;im.verify()
   proof={"status":"PASS_FILE","output":str(pic),"size":pic.stat().st_size,"resolution":[w,h],
          "references":[str(x) for x in refs],"hash":hashlib.sha256(pic.read_bytes()).hexdigest(),
          "duration_s":round(time.time()-t,1),"provider":"comfyui_sdxl_ipadapter"}
   print("COMFY_LIVE_IMAGE_PASS",json.dumps(proof,ensure_ascii=False),flush=True)
except Exception as exc:
   proof={"status":"FAIL","error":str(exc),"duration_s":round(time.time()-t,1)}
   print("COMFY_LIVE_IMAGE_FAIL",repr(exc),flush=True)
finally:
   (dst/"comfy_e2e.json").write_text(json.dumps(proof,ensure_ascii=False,indent=2),encoding="utf-8")
