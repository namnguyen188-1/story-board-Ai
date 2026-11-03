"""Style switch must rebuild video while keeping existing artwork and audio."""
from pathlib import Path
import shutil,hashlib,cv2,os
from series_studio import read_json,write_json,render_one
root=Path(__file__).resolve().parent
src=root/"productions"/"Hand-Color-Drawing-QA"/"episode_001"/"scenes"/"scene_0001"
dest=root/"productions"/"Hand-Color-Cache-QA"/"episode_001"/"scenes"/"scene_0001"
dest.mkdir(parents=True,exist_ok=True)
for name in ("image.png","audio.wav"):shutil.copy2(src/name,dest/name)
job=read_json(src/"job.json");job["scene_dir"]=str(dest);job["width"]=640;job["height"]=360
before={name:hashlib.sha256((dest/name).read_bytes()).hexdigest() for name in ("image.png","audio.wav")}
for style in ("hand_color","color_cinematic","hand_color"):
    job["visual_style"]=style;write_json(dest/"job.json",job);render_one(dest/"job.json")
    cap=cv2.VideoCapture(str(dest/"final.mp4"));ok,f=cap.read();cap.release();assert ok
    if style=="hand_color":assert f.mean()>248,f.mean()
    else:assert f.mean()<240,f.mean()
    assert read_json(dest/"render_style.json")["visual_style"]==style
    print("STYLE_SWITCH_PASS",style,flush=True)
after={name:hashlib.sha256((dest/name).read_bytes()).hexdigest() for name in before}
assert before==after
print("ARTWORK_AUDIO_PRESERVED_PASS",flush=True)
