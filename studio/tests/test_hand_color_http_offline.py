"""Exercise real UI backend -> offline scene render -> subtitles -> concat."""
import json,time,urllib.request,urllib.parse
from pathlib import Path
base="http://127.0.0.1:8765"
status=json.load(urllib.request.urlopen(base+"/api/status"))
assert not status["running"],"must not interrupt another production"
body={"series":"Hand Color HTTP Offline QA","episode":1,"prompt":"A painter shows a colorful village.",
      "mode":"offline","minutes":0.1,"scene_seconds":8,"size":"640x360","workers":1,
      "input_mode":"idea","genre":"animation","visual_style":"hand_color",
      "language":"English","region":"US","voice_name":"Kore","image_provider":"gemini",
      "subtitle_style":"karaoke_viral"}
req=urllib.request.Request(base+"/api/produce",data=json.dumps(body).encode(),
    headers={"Content-Type":"application/json"},method="POST")
reply=json.load(urllib.request.urlopen(req))
print("HTTP_HAND_COLOR_ACCEPTED",reply.get("status"),flush=True)
for _ in range(45):
    time.sleep(1)
    status=json.load(urllib.request.urlopen(base+"/api/status"))
    if not status["running"]:break
else:raise RuntimeError("Offline HTTP QA did not finish in 45 seconds")
assert status.get("exit_code")==0,status.get("recent_logs")
root=Path(__file__).resolve().parent
url=status["final_video_url"]
assert url.startswith("/media/productions/")
video=root/urllib.parse.unquote(url.removeprefix("/media/"))
ep=video.parent
manifest=json.loads((ep/"manifest.json").read_text(encoding="utf-8"))
assert manifest["status"]=="PASS",manifest
assert video.exists()
job=json.loads((ep/"scenes"/"scene_0001"/"job.json").read_text(encoding="utf-8"))
assert job["visual_style"]=="hand_color"
print("HTTP_HAND_COLOR_OFFLINE_EPISODE_PASS",json.dumps(manifest["qc"]),flush=True)
