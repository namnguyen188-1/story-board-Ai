from pathlib import Path
from PIL import Image
import sys,json,urllib.request,hashlib,time
root=Path(r"D:\STORYBOARD_AI\studio")
sys.path.insert(0,str(root))
from studio_mcp.image_backend import StoryboardImageTransport,validate_image_tool_readiness
import seo_packager
variant=sys.argv[1] if len(sys.argv)>1 else "land"
if variant not in ("land","short"):raise SystemExit("unknown variant")
ratio="16:9" if variant=="land" else "9:16"
w,h=(1536,864) if variant=="land" else (1080,1920)
base=root/"runtime/thumbnail_reliability_qa_20261108"/(variant+"_r2")
ep=base/"episode_001"
ep.mkdir(parents=True,exist_ok=True)
plan={"title":"EL PODER DEL SILENCIO ANTE EL RECHAZO","genre":"stoic",
      "bible":{"characters":[{"name":"Roman Stoic philosopher Marcus Aurelius"}]},
      "config":{"genre":"stoic"}}
pp=ep/"plan.json"
if not pp.exists():pp.write_text(json.dumps(plan,ensure_ascii=False),encoding="utf8")
status=json.load(urllib.request.urlopen("http://127.0.0.1:8765/api/status",timeout=7))
flow=json.load(urllib.request.urlopen("http://127.0.0.1:8765/api/flow/status",timeout=7))
if status.get("running") or flow.get("provider")!="mcp_v2" or not flow.get("ready"):
 raise RuntimeError("STUDIO_NOT_IDLE_OR_FLOW_NOT_READY")
expected=ep/("thumbnail_seo.jpg" if variant=="land" else "thumbnail_shorts.jpg")
if expected.exists():raise RuntimeError("TEST_OUTPUT_ALREADY_EXISTS_STOP")
backend=StoryboardImageTransport()
validate_image_tool_readiness(backend("health"),require_queue=True)
record={"variant":variant,"ratio":ratio,"model":"Nano Banana Pro","max_images":1,"fallback":False,
        "single_account":True,"attempts":1,"existing_issues_not_retried":True,
        "result":"NOT_STARTED"}
start=time.monotonic()
try:
 record["result"]="SUBMITTING_ONCE"
 res=seo_packager.generate_thumbnail_with_flow(
  episode_dir=ep,series_name="QA_STOIC_THUMB_20261108_"+variant.upper()+"_R2",genre="stoic",
  custom_hook=("PODER DEL SILENCIO" if variant=="land" else "SILENCIO PODER"),
  aspect_ratio=ratio,force_regenerate=False)
 record["generator_result"]=res
 record["elapsed_sec"]=round(time.monotonic()-start,2)
 if not res.get("ok"):raise RuntimeError("GENERATOR_FAILED: "+str(res.get("error")))
 if res.get("backend")!="mcp_v2":raise RuntimeError("NOT_NATIVE_MCP")
 with Image.open(expected) as im:
  im.verify()
 with Image.open(expected) as im:
  if im.format!="JPEG" or im.size!=(w,h):raise RuntimeError("MIME_OR_DIMENSION_MISMATCH")
 size=expected.stat().st_size
 if size>2_000_000:raise RuntimeError("THUMBNAIL_TOO_LARGE")
 record.update({"result":"PASS","image_bytes":size,"format":"JPEG",
                "dimensions":[w,h],"sha256":hashlib.sha256(expected.read_bytes()).hexdigest(),
                "path":str(expected)})
 cached=seo_packager.generate_thumbnail_with_flow(
  episode_dir=ep,series_name="QA_STOIC_THUMB_20261108_"+variant.upper()+"_R2",genre="stoic",
  custom_hook=("PODER DEL SILENCIO" if variant=="land" else "SILENCIO PODER"),
  aspect_ratio=ratio,force_regenerate=False)
 record["cache_no_resubmit"]=cached.get("backend")=="cached_existing"
 if not record["cache_no_resubmit"]:raise RuntimeError("CACHE_REUSE_FAILED")
except Exception as e:
 if record.get("result")!="PASS":record["result"]="FAIL"
 record["error_type"]=type(e).__name__
 record["error"]=str(e)[:700]
finally:
 base.mkdir(parents=True,exist_ok=True)
 (base/"live_result.json").write_text(json.dumps(record,ensure_ascii=False,indent=2,default=str),encoding="utf8")
 print("LIVE_THUMBNAIL_RESULT",json.dumps({k:v for k,v in record.items() if k!="generator_result"},ensure_ascii=False),flush=True)
