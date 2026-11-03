"""Media-ingest/render acceptance using a previously verified MCP image.

NO new MCP submission, NO AI text/TTS/image API calls.
Reuses the first episode's existing WAV to test local film construction.
"""
import sys,os,shutil
from pathlib import Path
from PIL import Image,ImageOps
root=Path(__file__).parent
sys.path.insert(0,str(root))
from series_studio import render_one,write_json,read_json,qc_clip,own_api_key
source=root/"productions"/"Whiteboard-Chronicles"/"episode_001"
plan=read_json(source/"plan.json")
scene=plan["scenes"][0]
path=root/"productions"/"MCP-Studio-Render-QA"/"episode_001"/"scenes"/"scene_0001"
path.mkdir(parents=True,exist_ok=True)
image=path/"image.png"
fixture=root/"mcp_image_test_result"/"city_lost_time_mcp_scene_001.jpg"
assert fixture.is_file()
with Image.open(fixture) as original:
    rgb=ImageOps.pad(original.convert("RGB"),(1536,864),color="white",
                     method=Image.Resampling.LANCZOS)
    rgb.save(image,"PNG")
audio=path/"audio.wav"
shutil.copy2(source/"scenes"/"scene_0001"/"audio.wav",audio)
job={"scene":scene,"scene_dir":str(path),"mode":"live",
     "width":1280,"height":720,"language":"English",
     "subtitles":True,"bible":plan["bible"],
     "anchor_image":"","input_hash":"qa_mcp_real_image_cached_audio",
     "image_provider":"mcp_v2","mcp_model_index":1,"mcp_max_images":1,
     "series":"MCP-Studio-Render-QA","episode":1}
write_json(path/"job.json",job)
# Model is never called since both image and WAV already exist.
os.environ["GEMINI_API_KEY"]=own_api_key()
print("REAL_MCP_IMAGE_INGEST_START",flush=True)
render_one(path/"job.json")
qc=qc_clip(path/"final.mp4",True,(1280,720))
print("REAL_MCP_IMAGE_LOCAL_VIDEO_PASS",qc,flush=True)
print("FILE",path/"final.mp4",flush=True)
