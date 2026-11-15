import json,subprocess,hashlib,os
from pathlib import Path
root=Path(r"D:\STORYBOARD_AI\studio")
ep=root/"productions/stoi/episode_001"
ffprobe="ffprobe"
video=ep/"episode_final.mp4"
scenes=sorted((ep/"scenes").glob("scene_*/final.mp4"))
files=[video]+scenes
report={"series":"stoi","scene_count":len(scenes),"files":[],"pass_count":0,"error_count":0,"problems":[]}
for p in files:
 cmd=[ffprobe,"-v","error","-show_entries","format=duration,size:stream=codec_name,codec_type,width,height,r_frame_rate","-of","json",str(p)]
 try:
  r=subprocess.run(cmd,capture_output=True,text=True,encoding="utf8",errors="replace",timeout=25)
  j=json.loads(r.stdout) if r.returncode==0 else {}
  streams=j.get("streams",[])
  vids=[s for s in streams if s.get("codec_type")=="video"]
  auds=[s for s in streams if s.get("codec_type")=="audio"]
  row={"name":str(p.relative_to(ep)),"exists":p.is_file(),"bytes":p.stat().st_size if p.is_file() else 0,
       "duration":round(float(j.get("format",{}).get("duration",0)),3),
       "video":vids,"audio":auds,"ffprobe_rc":r.returncode}
  row["pass"]=bool(vids and auds and row["duration"]>0 and row["bytes"]>10000 and r.returncode==0)
 except Exception as e:row={"name":str(p.relative_to(ep)),"pass":False,"error":str(e)}
 report["files"].append(row)
 report["pass_count"]+=int(row["pass"])
 report["error_count"]+=int(not row["pass"])
total=report["files"][0].get("duration",0)
manifest=json.loads((ep/"manifest.json").read_text(encoding="utf8"))
plan=json.loads((ep/"plan.json").read_text(encoding="utf8"))
seo=json.loads((ep/"youtube_publish_pack.json").read_text(encoding="utf8"))
report["manifest_status"]=manifest.get("status")
report["target_seconds"]=round(float(manifest.get("target_minutes",0))*60,2)
report["duration_seconds"]=total
report["duration_ratio"]=round(total/max(1,report["target_seconds"]),3)
report["seo_is_short"]=seo.get("is_short")
report["seo_is_vertical_short"]=seo.get("is_vertical_short")
report["video_is_vertical"]=bool(report["files"][0]["video"] and report["files"][0]["video"][0].get("height",0)>report["files"][0]["video"][0].get("width",0))
report["passed"]=report["pass_count"]==len(files)
if report["duration_ratio"]>1.25:report["problems"].append("DURATION_OVERRUN")
if report["seo_is_short"] and not report["video_is_vertical"]:report["problems"].append("SEO_SHORTS_LABEL_VS_HORIZONTAL_VIDEO")
dest=root/"runtime/thumbnail_reliability_qa_20261108"
dest.mkdir(parents=True,exist_ok=True)
(dest/"stoi_media_qc.json").write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf8")
print(json.dumps({k:v for k,v in report.items() if k!="files"},ensure_ascii=False))
print("MEDIA",[(f["name"],f["pass"],f.get("duration"),f.get("video",[{}])[0].get("width"),f.get("video",[{}])[0].get("height")) for f in report["files"]])
