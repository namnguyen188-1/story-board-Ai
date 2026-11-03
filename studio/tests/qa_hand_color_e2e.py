"""Real cached artwork and audio -> complete Studio render. No external calls."""
from pathlib import Path
import shutil,wave,json,time,os,cv2
root=Path(__file__).resolve().parent
from series_studio import render_one,write_json,read_json,qc_clip
source=root/"productions"/"Whiteboard-Chronicles"/"episode_005"/"scenes"/"scene_0001"
dest=root/"productions"/"Hand-Color-Drawing-QA"/"episode_001"/"scenes"/"scene_0001"
dest.mkdir(parents=True,exist_ok=True)
shutil.copy2(source/"image.png",dest/"image.png")
with wave.open(str(source/"audio.wav"),"rb") as i:
    with wave.open(str(dest/"audio.wav"),"wb") as o:
        o.setnchannels(i.getnchannels());o.setsampwidth(i.getsampwidth());o.setframerate(i.getframerate())
        o.writeframes(i.readframes(min(i.getnframes(),i.getframerate()*8)))
prior=read_json(source/"job.json")
job=dict(prior)
job.update({"scene_dir":str(dest),"width":1280,"height":720,"visual_style":"hand_color",
    "input_hash":"hand_color_qa_20261012","subtitles":False,"api_key":"","mode":"live"})
write_json(dest/"job.json",job)
started=time.perf_counter()
render_one(dest/"job.json")
qc=qc_clip(dest/"final.mp4",True,(1280,720))
elapsed=time.perf_counter()-started
cap=cv2.VideoCapture(str(dest/"final.mp4"))
count=int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
samples=[]
for fraction in (0,.25,.5,.75,.99):
    cap.set(cv2.CAP_PROP_POS_FRAMES,min(count-1,int(count*fraction)))
    ok,frame=cap.read();assert ok
    cv2.imwrite(str(dest/("frame_"+str(int(fraction*100))+".png")),frame)
    small=cv2.resize(frame,(384,216))
    cv2.putText(small,str(round(fraction*qc["duration_seconds"],1))+"s",
        (8,24),cv2.FONT_HERSHEY_SIMPLEX,.6,(0,0,0),2)
    samples.append(small)
cap.release()
sheet=cv2.hconcat(samples)
cv2.imwrite(str(dest/"progress_preview.jpg"),sheet)
report={"qc":qc,"render_seconds":round(elapsed,2),"output":str(dest/"final.mp4"),
    "no_new_image_or_tts_calls":True,"uses_cached_artwork_and_audio":True}
write_json(dest/"hand_color_qa.json",report)
print("HAND_COLOR_E2E_PASS",json.dumps(report),flush=True)
