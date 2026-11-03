"""No-Gemini locked-dialogue overflow guard test."""
import sys,shutil,wave
from pathlib import Path
root=Path(r"D:\STORYBOARD_AI\studio")
sys.path.insert(0,str(root))
from series_studio import render_one,write_json
scene_dir=root/"productions"/"Locked-Audio-Duration-Guard-QA"/"episode_001"/"scenes"/"scene_0001"
scene_dir.mkdir(parents=True,exist_ok=True)
src=root/"productions"/"MCP-Whiteboard-E2E-20261012"/"episode_001"/"scenes"/"scene_0001"
shutil.copy2(src/"image.png",scene_dir/"image.png")
shutil.copy2(src/"audio.wav",scene_dir/"audio.wav")
with wave.open(str(scene_dir/"audio.wav"),"rb") as a:
    secs=a.getnframes()/a.getframerate()
assert secs>12,secs
job={"scene":{"scene_number":1,"locked_script":True,"script_seconds":8,
              "summary":"locked long voice","narration":"A fictional long line",
              "description":"A full color scene from an original story"},
     "scene_dir":str(scene_dir),"mode":"live","width":640,"height":360,
     "language":"Spanish","voice_name":"Charon","genre":"stoic",
     "visual_style":"color_cinematic","region":"ES","scene_seconds":8,
     "subtitles":True,"bible":{"characters":[]},"anchor_image":"",
     "input_hash":"locked_audio_overrun",
     "image_provider":"mcp_v2","mcp_model_index":1,"mcp_max_images":1,
     "series":"Locked-Audio-Duration-Guard-QA","episode":1}
write_json(scene_dir/"job.json",job)
try:
    render_one(scene_dir/"job.json")
except RuntimeError as exc:
    assert "LOCKED_SCRIPT_DIALOGUE_TOO_LONG" in str(exc),str(exc)[:180]
    assert not (scene_dir/"final.mp4").exists()
    print("LOCKED_8S_DIALOGUE_OVERLONG_BLOCK_PASS",round(secs,1),flush=True)
else:raise AssertionError("Expected blocked overlong scripted audio")
