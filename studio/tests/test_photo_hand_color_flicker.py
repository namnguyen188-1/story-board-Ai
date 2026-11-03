"""Fresh render from real cached artwork/speech; inspect every encoded frame."""
from pathlib import Path
import shutil,time,json,cv2,numpy as np
from series_studio import read_json,write_json,render_one,qc_clip
root=Path(__file__).resolve().parent
source=root/"productions"/"Hand-Color-Drawing-QA"/"episode_001"/"scenes"/"scene_0001"
dest=root/"productions"/("Hand-Color-Photo-Flicker-"+str(int(time.time())))/"episode_001"/"scenes"/"scene_0001"
dest.mkdir(parents=True)
for name in ("image.png","audio.wav"):shutil.copy2(source/name,dest/name)
job=read_json(source/"job.json");job["scene_dir"]=str(dest);job["api_key"]=""
write_json(dest/"job.json",job)
started=time.perf_counter();render_one(dest/"job.json")
qc=qc_clip(dest/"final.mp4",True,(1280,720))
cap=cv2.VideoCapture(str(dest/"final.mp4"));white=[];dark=[]
while True:
    ok,f=cap.read()
    if not ok:break
    f=cv2.resize(f,(320,180))
    white.append(float(np.mean(np.all(f>245,axis=2))))
    dark.append(float(f.mean()))
cap.release()
started_drawing=next(i for i,v in enumerate(white) if v<.9)
assert not any(v>.98 for v in white[started_drawing:]),"white flash after drawing began"
assert min(dark)>1,"black flash"
assert len(white)==200,len(white)
assert max(np.diff(white))<.12,("large white flash",max(np.diff(white)))
report={"qc":qc,"frames_checked":len(white),"white_or_black_flashes":0,
    "max_white_fraction_jump":round(float(max(np.diff(white))),4),
    "render_and_analysis_seconds":round(time.perf_counter()-started,2),
    "output":str(dest/"final.mp4"),"uses_cached_real_art_and_speech":True}
write_json(dest/"flicker_qc.json",report)
print("REAL_PHOTO_FRAME_FLICKER_PASS",json.dumps(report),flush=True)
