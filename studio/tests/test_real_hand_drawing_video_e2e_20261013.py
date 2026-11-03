"""Actual locally-rendered 2-scene hand-drawing full E2E through Studio HTTP.
No paid Google/Gemini/Flow calls. Produce a real MP4, WAV, and subtitles."""
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import unquote, quote
from datetime import datetime
import json,sys,time,subprocess
root=Path(r"D:\STORYBOARD_AI\studio")
series="E2E-Drawn-Video-Oct13-2026"
episode=root/"productions"/(series+"---Offline-Test")/"episode_001"
verify_only="--verify-only" in sys.argv
if not verify_only:
    assert not episode.exists(), "E2E sample already exists: refuse overwrite"
base="http://127.0.0.1:8765"
def get(path):
    with urlopen(base+path,timeout=7) as r:
        return json.load(r)
status=get("/api/status")
assert not status["running"],"Active production; do not collide"
req={
 "series":series,"episode":1,"prompt":"A young explorer draws a sunny village, follows a winding river, and finds a colorful kite. Original gentle animation.", 
 "input_mode":"idea","mode":"offline","minutes":0.2,"scene_seconds":8,
 "size":"640x360","workers":1,"image_provider":"gemini",
 "genre":"animation","visual_style":"hand_color","region":"VN",
 "language":"Vietnamese","voice_name":"auto",
 "subtitle_style":"karaoke_viral"
}
begin=time.monotonic()
if verify_only:
    print("VERIFY_EXISTING_MP4_NO_NEW_JOB",flush=True)
else:
    post=Request(base+"/api/produce",data=json.dumps(req).encode("utf-8"),
                 headers={"Content-Type":"application/json"},method="POST")
    with urlopen(post,timeout=10) as r: reply=json.load(r)
    assert reply.get("status")=="STARTED",reply
    print("REAL_DRAW_E2E_JOB_STARTED",flush=True)

    last=""
    while time.monotonic()-begin<230:
        time.sleep(2)
        s=get("/api/status")
        stage=s.get("stage","")
        if stage!=last:
            print("STAGE",stage,"PERCENT",s.get("percent"),"MESSAGE",s.get("message","")[:120],flush=True)
            last=stage
        if not s["running"]:
            assert s.get("exit_code")==0,("JOB_FAILED",s.get("recent_logs",[])[-20:])
            break
    else:raise TimeoutError("240s e2e timeout; do not auto-retry")
ep=get("/api/episode?series="+quote(episode.parent.name)+"&episode=1")
media=ep.get("final_video_url")
assert media and media.startswith("/media/productions/"),ep
video=root/unquote(media.removeprefix("/media/").split("?",1)[0])
assert video.is_file(),video
probe=subprocess.run(["ffprobe","-v","error","-show_entries",
 "stream=codec_type,codec_name,width,height:format=duration,size","-of","json",str(video)],
 capture_output=True,text=True,timeout=30,check=True)
info=json.loads(probe.stdout)
v=[v for v in info["streams"] if v["codec_type"]=="video"]
a=[a for a in info["streams"] if a["codec_type"]=="audio"]
assert len(v)==1 and len(a)==1
assert v[0]["width"]==640 and v[0]["height"]==360
assert float(info["format"]["duration"])>4
files=[episode/"plan.json",episode/"manifest.json",episode/"episode_final.mp4"]
for idx in (1,2):
    scene=episode/"scenes"/f"scene_{idx:04d}"
    files += [scene/"image.png",scene/"audio.wav",scene/"silent.mp4",scene/"final.mp4",
       scene/"subtitles.json"]
assert all(x.is_file() and x.stat().st_size>0 for x in files),[str(x) for x in files if not x.is_file()]
assert json.loads((episode/"manifest.json").read_text(encoding="utf-8"))["status"]=="PASS"
req_range=Request(base+media,headers={"Range":"bytes=0-1023"})
with urlopen(req_range,timeout=7) as resp:
    assert resp.status==206 and len(resp.read())==1024
print("REAL_DRAW_E2E_FINAL_MP4_PASS",json.dumps({
 "path":str(video),"format":info["format"],
 "video_stream":v[0],"audio_stream":a[0],
 "elapsed_seconds":round(time.monotonic()-begin,1),
 "scene_count":2,"media_files_verified":len(files),
 "http_range":"206 PASS","uses_paid_apis":False
},ensure_ascii=False),flush=True)
