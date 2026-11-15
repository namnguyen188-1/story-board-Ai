import sys,shutil,json,hashlib,time,traceback
from pathlib import Path
from PIL import Image
root=Path(r"D:\STORYBOARD_AI\studio")
sys.path.insert(0,str(root))
from seo_packager import generate_thumbnail_image,generate_shorts_thumbnail_cover
ep=root/"productions/stoi/episode_001"
out=root/"runtime/thumbnail_reliability_qa_20261108/offline_previews"
out.mkdir(parents=True,exist_ok=True)
items=[
 ("land_gold","land","PODER DEL SILENCIO",1),
 ("land_mind","land","DOMINA TU MENTE",3),
 ("short_power","short","SILENCIO PODER",2),
 ("short_mind","short","MENTE INVENCIBLE",4)
]
summary={"count":len(items),"ok":0,"errors":0,"images":[],"provider":"local_existing_stoi_scene","google_flow_calls":0}
for name,kind,hook,num in items:
 t=time.perf_counter()
 src=ep/"scenes"/f"scene_{num:04d}"/"image.png"
 copied=out/(name+"_source.png")
 shutil.copy2(src,copied)
 dest=out/(name+".jpg")
 try:
  if dest.exists():raise RuntimeError("DESTINATION_ALREADY_EXISTS")
  if kind=="land":
   generated=generate_thumbnail_image(copied,dest,hook_text=hook,genre="stoic")
   expected=(1280,720)
  else:
   generated=generate_shorts_thumbnail_cover(copied,dest,hook_text=hook,genre="stoic")
   expected=(1080,1920)
  with Image.open(dest) as im:im.verify()
  with Image.open(dest) as im:
   typ=im.format
   dims=im.size
  if typ!="JPEG" or dims!=expected:raise RuntimeError("ENCODING_OR_ASPECT_MISMATCH")
  length=dest.stat().st_size
  if length>2_000_000:
   with Image.open(dest) as im:
    im.convert("RGB").save(dest,"JPEG",quality=85,optimize=True)
   length=dest.stat().st_size
   if length>2_000_000:raise RuntimeError("YOUTUBE_LIMIT_EXCEEDED")
  row={"name":name,"status":"PASS","bytes":length,"format":typ,"dimensions":list(dims),
       "sha256":hashlib.sha256(dest.read_bytes()).hexdigest(),"path":str(dest),
       "elapsed_sec":round(time.perf_counter()-t,2)}
  summary["ok"]+=1
 except Exception as ex:
  row={"name":name,"status":"FAIL","error":str(ex)[:500],"elapsed_sec":round(time.perf_counter()-t,2)}
  summary["errors"]+=1
 summary["images"].append(row)
 print(json.dumps(row,ensure_ascii=False),flush=True)
(out/"offline_preview_report.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf8")
print("SUMMARY",json.dumps({k:v for k,v in summary.items() if k!="images"},ensure_ascii=False))
