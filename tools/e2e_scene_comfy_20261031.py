"""Isolated real Storyboard cinematic scene render using local ComfyUI image + existing dialogue WAV."""
from pathlib import Path
from PIL import Image
import sys, shutil, json, hashlib, subprocess, time, traceback
ROOT=Path(r"D:\STORYBOARD_AI\studio")
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/"engine"))
sys.stdout.reconfigure(encoding="utf-8",errors="replace")
from cinematic_engine.drama_video_engine import DramaVideoEngine
from cinematic_engine.drama_schema import CharacterProfile
source=ROOT/"productions"/"DRAMA"/"episode_001"
voice=ROOT/"scratch"/"E2E_REFERENCE_VOICE_20261031"/"gemini"/"episode_001"/"scenes"/"scene_0001"/"dialogue_master.wav"
dest=ROOT/"scratch"/"E2E_REFERENCE_VOICE_20261031"/"comfy_scene"/"episode_001"
sc=dest/"scenes"/"scene_0001";sc.mkdir(parents=True,exist_ok=True)
report=dest/"local_image_scene_e2e.json"
plan=json.loads((source/"drama_plan.json").read_text(encoding="utf-8"))
scene=dict(plan["scenes"][0])
scene["language"]="Vietnamese"
cast={n:CharacterProfile(**v) for n,v in plan["cast"].items()}
shutil.copytree(source/"00_ASSET_PACK"/"characters",dest/"00_ASSET_PACK"/"characters",dirs_exist_ok=True)
assert voice.is_file(), "Expected real pre-rendered verified TTS dialogue_master.wav"
shutil.copy2(voice,sc/"dialogue_master.wav")
anchor=dest/"00_ASSET_PACK"/"characters"/"lan_turnaround.jpg"
started=time.time()
result={"status":"RUNNING","image_provider":"comfyui_sdxl_ipadapter","preserved_voice":str(voice)}
try:
   produced=DramaVideoEngine(fps=24).render_scene(scene,sc,aspect_ratio="16:9",cast_map=cast,
     reference_image_path=anchor,image_provider="comfyui",
     bible={"language":"Vietnamese"},width=1280,height=720,
     subtitle_style="karaoke_viral",subtitle_size=62,no_subtitles=False)
   video=Path(produced["final_video_path"])
   ffprobe=ROOT/"engine"/"bin"/"ffprobe.exe"
   info=json.loads(subprocess.run([str(ffprobe),"-v","error","-show_entries","stream=codec_type:format=duration",
      "-of","json",str(video)],capture_output=True,text=True,check=True).stdout)
   proof=json.loads((sc/"scene_base_reference.json").read_text(encoding="utf-8"))
   align=json.loads((sc/"subtitles.json").read_text(encoding="utf-8"))
   assert video.stat().st_size>250000,video
   assert set(x["codec_type"] for x in info["streams"])>={"video","audio"},info
   assert proof["generation_source"]=="comfyui_ipadapter"
   assert proof["secondary_reference_sha256"],proof
   assert not align["script_mismatch"] and len(align["words"])>5,align
   with Image.open(sc/"scene_base.png") as img:
      image_dims=img.size
      img.verify()
   result.update({"status":"PASS_TECHNICAL", "video":str(video),"bytes":video.stat().st_size,
         "duration_s":round(float(info["format"]["duration"]),3),"scene_image_dimensions":image_dims,
         "provider_proof":proof["generation_source"],"reference_count":1+len(proof["secondary_reference_sha256"]),
         "asr_words":len(align["words"]),"subtitle_mismatch":align["script_mismatch"]})
   print("LOCAL_COMFY_SCENE_E2E_PASS",json.dumps(result,ensure_ascii=False),flush=True)
except Exception as exc:
   result.update({"status":"FAIL","error":str(exc),"trace":traceback.format_exc()[-1800:]})
   print("LOCAL_COMFY_SCENE_E2E_FAIL",repr(exc),flush=True)
finally:
   result["elapsed_s"]=round(time.time()-started,1)
   report.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
