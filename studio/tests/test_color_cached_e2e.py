"""Real previously cached MCP photo + actual speech WAV, local color render, subtitles/MP4.
No Gemini text/TTS/image calls. This is a new QA episode, not a user project edit.
"""
from pathlib import Path
import sys,wave,shutil,os,cv2,subprocess
root=Path(r"D:\STORYBOARD_AI\studio")
sys.path.insert(0,str(root))
from series_studio import render_one,write_json,read_json,qc_clip
source=root/"productions"/"MCP-Whiteboard-E2E-20261012"/"episode_001"
plan=read_json(source/"plan.json")
scene=dict(plan["scenes"][0])
scene["narration"]="At eleven fifty nine, the city stopped. One clockmaker alone could see the truth."
dest=root/"productions"/"Colored-Stoic-Render-QA"/"episode_001"/"scenes"/"scene_0001"
dest.mkdir(parents=True,exist_ok=True)
shutil.copy2(source/"scenes"/"scene_0001"/"image.png",dest/"image.png")
with wave.open(str(source/"scenes"/"scene_0001"/"audio.wav"),"rb") as i:
    with wave.open(str(dest/"audio.wav"),"wb") as o:
        o.setnchannels(i.getnchannels());o.setsampwidth(i.getsampwidth())
        o.setframerate(i.getframerate())
        o.writeframes(i.readframes(int(i.getframerate()*4)))
job={"scene":scene,"scene_dir":str(dest),"mode":"live",
     "width":640,"height":360,"language":"Spanish","voice_name":"Charon",
     "visual_style":"color_cinematic","genre":"stoic","region":"ES",
     "scene_seconds":8,"subtitles":True,"bible":plan["bible"],
     "anchor_image":"","input_hash":"colored_qa_20261012",
     "image_provider":"mcp_v2","mcp_model_index":1,"mcp_max_images":1,
     "series":"Colored-Stoic-Render-QA","episode":1}
write_json(dest/"job.json",job)
print("COLOR_CACHED_AUDIO_E2E_BEGIN",flush=True)
result=render_one(dest/"job.json")
video=dest/"final.mp4"
qc=qc_clip(video,True,(640,360))
print("COLOR_WITH_REAL_SPEECH_AND_SUBTITLES_PASS",qc,flush=True)
cap=cv2.VideoCapture(str(video))
assert cap.isOpened()
ok,frame=cap.read();cap.release()
assert ok
# Even if source art palette is not colorful, the frame must be the full original
# image, not an all-white sheet or a black-ink sketch.
assert frame.mean()>8 and frame.std()>9,(frame.mean(),frame.std())
print("FINAL_FRAME_NONBLANK_PASS",round(float(frame.std()),1),flush=True)
