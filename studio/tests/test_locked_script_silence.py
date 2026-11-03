from pathlib import Path
import sys,shutil,wave
root=Path(r"D:\STORYBOARD_AI\studio")
sys.path.insert(0,str(root))
from series_studio import render_one,write_json,qc_clip
dest=root/"productions"/"Locked-Script-Silence-QA"/"episode_001"/"scenes"/"scene_0001"
dest.mkdir(parents=True,exist_ok=True)
shutil.copy2(root/"mcp_image_test_result"/"city_lost_time_mcp_scene_001.jpg",dest/"image.png")
job={"scene":{"scene_number":1,"summary":"Silent cinema","narration":"",
              "script_seconds":3,
              "description":"A silent landscape under evening sunlight",
              "visual_setup":"Wide film shot"},
     "scene_dir":str(dest),"mode":"live","width":640,"height":360,
     "language":"Vietnamese","voice_name":"Kore","visual_style":"color_cinematic",
     "genre":"family_drama","region":"VN","scene_seconds":3,
     "subtitles":True,"bible":{"characters":[],"visual_style":"full color"},
     "anchor_image":"","input_hash":"locked_silent_20261012",
     "image_provider":"mcp_v2","mcp_model_index":1,"mcp_max_images":1,
     "series":"Locked-Script-Silence-QA","episode":1}
write_json(dest/"job.json",job)
render_one(dest/"job.json")
with wave.open(str(dest/"audio.wav"),"rb") as a:
    duration=a.getnframes()/a.getframerate()
    assert 2.9<duration<3.1,duration
qc=qc_clip(dest/"final.mp4",True,(640,360))
assert 2.9<qc["duration_seconds"]<3.4
assert not (dest/"subtitles.json").exists()
print("LOCKED_SCRIPT_SILENT_SCENE_COLOR_E2E_PASS",qc,flush=True)
