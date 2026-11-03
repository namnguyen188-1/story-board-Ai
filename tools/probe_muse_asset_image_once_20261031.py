"""One and only one real Muse image capability E2E attempt; no automatic retry."""
import json,subprocess,os,datetime
from pathlib import Path
s=Path(r"D:\STORYBOARD_AI\studio\scratch\multi_role_asset_first_e2e")
s.mkdir(parents=True,exist_ok=True)
receipt=s/"muse_image_probe_receipt.json"
session_id="7225beb8-2b0d-4e10-b45d-b9bdef2664fb"
if receipt.exists():
 print("ALREADY_SUBMITTED",receipt.read_text(encoding="utf-8")[:2000],flush=True)
 raise SystemExit(0)
request=("Storyboard AI asset generation test. Please use the real image generation tool if available to CREATE EXACTLY ONE high-quality 4-angle CHARACTER TURNAROUND SHEET image file, 16:9, containing FOUR DISTINCT VIEWS of ONE AND THE SAME fictional adult Vietnamese woman named Lan: front full-body, 3/4 left full-body, exact side profile full-body, and rear full-body. She is 34 with warm ivory skin, sharp oval face, small mole beneath her left eye, shoulder-length jet-black hair with crisp side part, beige trench coat over dark burgundy knitted turtleneck, matching pants and shoes. Neutral grey studio backdrop, same face and outfit, accurate anatomy, non-graphic, not a silhouette, not four duplicate photographs. Save resulting actual generated JPG/PNG into workspace under storyboard_preproduction/lan_4angle_sheet.png if possible, and reply ONLY with the real local image file path (not a link or a text description). Do not generate video, do not retry automatically, do not invent a path if image tool unavailable; say IMAGE_TOOL_NOT_AVAILABLE.")
receipt.write_text(json.dumps({"status":"SUBMISSION_UNCERTAIN","session_id":session_id,
 "request":request,"utc":datetime.datetime.now(datetime.timezone.utc).isoformat()},ensure_ascii=False,indent=2),encoding="utf-8")
env=os.environ.copy()
env.update(MUSE_NO_UPDATE_CHECK="1",PYTHONUTF8="1",PYTHONIOENCODING="utf-8")
p=subprocess.run([r"D:\STORYBOARD_AI\studio\runtime\muse\python\python.exe","-m","muse_cli","send",request,"--thread",session_id,"--wait","1"],env=env,capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=100)
print("MUSE_IMAGE_SUBMIT_RETURN",p.returncode,p.stdout[:1200],p.stderr[:450],flush=True)
receipt.write_text(json.dumps({"status":"SENT" if p.returncode==0 else "UNKNOWN",
 "session_id":session_id,"reply":p.stdout[:1200],"error":p.stderr[:400]},ensure_ascii=False,indent=2),encoding="utf-8")
