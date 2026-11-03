# -*- coding: utf-8 -*-
"""Read-only media and published-pack audit of actual finished Muse production."""
import sys, json, subprocess, statistics, hashlib, os
from pathlib import Path
STUDIO=Path(r"D:\STORYBOARD_AI\studio")
EP=STUDIO/"productions"/"ho-t-h-nh-3d"/"episode_001"
FF=STUDIO/"engine"/"bin"/"ffprobe.exe"
LOG=STUDIO/"diagnostics"/"audit_media_e2e_20261026.json"
def probe(path):
    args=[str(FF),"-v","error","-show_entries","format=duration,size:stream=codec_type,codec_name,width,height,sample_rate","-of","json",str(path)]
    return json.loads(subprocess.check_output(args,timeout=12,stderr=subprocess.STDOUT).decode("utf-8","replace"))
dirs=sorted((EP/"scenes").glob("scene_[0-9][0-9][0-9][0-9]"))
result={"series":"Hải Triều Ký","episode":1,"scene_count":len(dirs),"all_results_pass":True,
"scene_status":{},"scenes_missing_video":[],"duration_details":[],"video_codec":None,"audio_codec":None}
durs=[]
for i,d in enumerate(dirs,1):
    video=d/"scene_final.mp4"
    state_file=d/"result.json"
    if not video.exists():
        result["scenes_missing_video"].append(d.name)
    try:
        x=json.loads(state_file.read_text(encoding="utf-8-sig"))
        status=x.get("status","UNKNOWN")
    except Exception:
        status="NO_VALID_RESULT"
    result["scene_status"][status]=result["scene_status"].get(status,0)+1
    if status!="PASS":result["all_results_pass"]=False
    if video.exists():
        try:
            x=probe(video)
            dur=float(x.get("format",{}).get("duration",0))
            durs.append(dur)
            result["duration_details"].append({"scene":i,"duration":round(dur,3)})
            if dur < 8.5 or dur > 10.5:
                print("SCENE_DURATION_OUTLIER",i,round(dur,3),flush=True)
        except Exception as e:
            print("PROBE_ERROR",i,str(e)[:100],flush=True)
            result["scenes_missing_video"].append(d.name+":probe_failed")
master=EP/"episode_001_final.mp4"
if master.exists():
    x=probe(master)
    result["master_duration_s"]=round(float(x["format"]["duration"]),3)
    result["master_size_mb"]=round(int(x["format"]["size"])/1048576,2)
    result["streams"]=x.get("streams")
if durs:
    result["scene_sum_s"]=round(sum(durs),3)
    result["shortest_scene_s"]=round(min(durs),3)
    result["longest_scene_s"]=round(max(durs),3)
    result["mean_scene_s"]=round(statistics.mean(durs),3)
    result["concat_delta_s"]=round(result.get("master_duration_s",0)-sum(durs),3)
pack_path=EP/"youtube_publish_pack.json"
if pack_path.exists():
    pack=json.loads(pack_path.read_text(encoding="utf-8-sig"))
    result["publish_pack_exists"]=True
    result["publish_pack_keys"]=sorted(pack.keys())
    result["has_titles"]=bool(pack.get("titles") or pack.get("best_title") or pack.get("title"))
    result["thumbnail_exists"]=(EP/"thumbnail_seo.jpg").exists()
    result["disclosure"]=pack.get("contains_synthetic_media","UNSPECIFIED")
LOG.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
for k in ["scene_count","all_results_pass","scene_status","scenes_missing_video","scene_sum_s","master_duration_s","concat_delta_s","shortest_scene_s","longest_scene_s","master_size_mb","publish_pack_exists","has_titles","thumbnail_exists","disclosure"]:
 print(k,":",result.get(k),flush=True)
print("STORED",LOG,flush=True)
