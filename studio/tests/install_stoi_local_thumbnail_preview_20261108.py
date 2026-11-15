import json,urllib.request,hashlib,os,shutil
from pathlib import Path
from PIL import Image
r=Path(r"D:\STORYBOARD_AI\studio")
ep=r/"productions/stoi/episode_001"
src=r/"runtime/thumbnail_reliability_qa_20261108/offline_previews"
status=json.load(urllib.request.urlopen("http://127.0.0.1:8765/api/status",timeout=4))
if status.get("running"):raise RuntimeError("STOP_ACTIVE_PRODUCTION")
items=[
 ("land_gold.jpg","thumbnail_seo.jpg",(1280,720)),
 ("short_power.jpg","thumbnail_shorts.jpg",(1080,1920))
]
report={"series":"stoi","created":[],"skipped":[],"source":"existing_scene_local_overlay",
        "flow_requests":0,"youtube_upload":False,"metadata_modified":False,
        "production_running":False}
for source,name,dims in items:
 a=src/source;b=ep/name
 with Image.open(a) as im:
  im.verify()
 with Image.open(a) as im:
  if im.format!="JPEG" or im.size!=dims or a.stat().st_size>2_000_000:
   raise RuntimeError("INVALID_QA_IMAGE_"+name)
 if b.exists():
  report["skipped"].append(name)
  continue
 with a.open("rb") as inp,b.open("xb") as out:
  shutil.copyfileobj(inp,out)
  out.flush();os.fsync(out.fileno())
 if hashlib.sha256(a.read_bytes()).digest()!=hashlib.sha256(b.read_bytes()).digest():
  b.unlink(missing_ok=True);raise RuntimeError("COPY_HASH_MISMATCH")
 report["created"].append({"name":name,"path":str(b),"bytes":b.stat().st_size,
  "sha256":hashlib.sha256(b.read_bytes()).hexdigest()})
dest=r/"runtime/thumbnail_reliability_qa_20261108/installed_into_stoi.json"
dest.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf8")
print(json.dumps(report,ensure_ascii=False))
