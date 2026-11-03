# Live, isolated one-scene E2E for Storyboard AI. No changes to published episodes.
import os, sys, json, shutil, subprocess, traceback, time, hashlib
from pathlib import Path
from datetime import datetime
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT=Path(r"D:\STORYBOARD_AI\studio")
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/"engine"))
os.environ["PATH"]=str(ROOT/"engine"/"bin")+os.pathsep+os.environ.get("PATH","")
from cinematic_engine.drama_asset_manager import get_primary_character_anchor,get_scene_character_anchors
from cinematic_engine.drama_video_engine import DramaVideoEngine
from cinematic_engine.drama_audio_engine import DramaAudioEngine
from cinematic_engine.drama_schema import CharacterProfile
from cinematic_engine.native_audio_subtitles import align_native_audio
mode=sys.argv[1] if len(sys.argv)>1 else "gemini"
assert mode in ("gemini","muse_video")
src=ROOT/"productions"/"DRAMA"/"episode_001"
dst=ROOT/"scratch"/"E2E_REFERENCE_VOICE_20261031"/mode/"episode_001"
scene_dir=dst/"scenes"/"scene_0001"
report_path=dst/"live_e2e_report.json"
start=time.time()
report={"mode":mode,"started":datetime.now().isoformat(),"status":"RUNNING","isolated":True,"source_episode":str(src)}
dst.mkdir(parents=True,exist_ok=True);scene_dir.mkdir(parents=True,exist_ok=True)
def save():
  report["elapsed_s"]=round(time.time()-start,1)
  report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
def marker(name, detail=None):
  report.setdefault("checks",{})[name]=detail if detail is not None else True
  print("E2E_CHECK",name,json.dumps(detail,ensure_ascii=False) if detail is not None else "PASS",flush=True);save()
try:
  plan=json.loads((src/"drama_plan.json").read_text(encoding="utf-8"))
  scene=dict(plan["scenes"][0]);scene["language"]="Vietnamese"
  src_assets=src/"00_ASSET_PACK"/"characters"
  dst_assets=dst/"00_ASSET_PACK"/"characters"
  shutil.copytree(src_assets,dst_assets,dirs_exist_ok=True)
  refs=get_scene_character_anchors(dst,scene["characters_present"])
  assert len(refs)>=2 and all(Path(x["image_path"]).is_file() for x in refs),refs
  char_name="Lan"
  primary=get_primary_character_anchor(dst,scene["characters_present"],char_name)
  assert primary is not None and primary.is_file()
  marker("character_reference_2_assets",{"names":[x.get("character_name") for x in refs],
      "primary":primary.name,"reference_sha256":hashlib.sha256(primary.read_bytes()).hexdigest()})
  cast={n: CharacterProfile(**x) for n,x in plan["cast"].items()}
  bible={"language":"Vietnamese","world":plan.get("logline",""),"characters":[{"name":n,"description":c.appearance_lock} for n,c in cast.items() if n!="Narrator"]}
  if mode=="gemini":
    # Full E2E from actual Gemini speech synthesis, not pre-existing audio.
    print("E2E_TTS_GENERATION_START",flush=True)
    audio=DramaAudioEngine(target_sample_rate=24000).assemble_scene_dialogue(scene, "Vietnamese", scene_dir, cast)
    assert Path(audio["master_audio_path"]).is_file() and audio["total_duration"]>2
    marker("real_tts_two_voices",{"duration":audio["total_duration"],"speakers":[b["speaker"] for b in audio["timeline"]["beats"]]})
  print("E2E_RENDER_BEGIN",mode,flush=True)
  outcome=DramaVideoEngine(fps=16).render_scene(scene=scene,scene_dir=scene_dir,aspect_ratio="16:9",
      cast_map=cast,reference_image_path=primary,image_provider=mode,bible=bible,
      width=1280,height=720,subtitle_style="karaoke_viral",subtitle_size=62,no_subtitles=False)
  final=Path(outcome["final_video_path"])
  assert final.is_file() and final.stat().st_size>40000
  ffprobe=str(ROOT/"engine"/"bin"/"ffprobe.exe")
  pr=subprocess.run([ffprobe,"-v","error","-show_entries","format=duration:stream=codec_type",
     "-of","json",str(final)],capture_output=True,text=True,check=True)
  media=json.loads(pr.stdout)
  kinds=[x["codec_type"] for x in media["streams"]]
  assert "video" in kinds and "audio" in kinds,kinds
  marker("actual_mp4_decodes",{"duration_s":float(media["format"]["duration"]),"size":final.stat().st_size,"streams":kinds})
  subs=json.loads((scene_dir/"subtitles.json").read_text(encoding="utf-8"))
  assert subs.get("timing_source")=="native-audio-v1",subs.keys()
  assert not subs.get("script_mismatch")
  assert len(subs.get("words",[]))>5
  marker("native_audio_aligned_subtitles",{"words":len(subs.get("words",[])),"timing":subs.get("timing_source"),"mismatch":subs.get("script_mismatch")})
  if mode=="gemini":
    proof=json.loads((scene_dir/"scene_base_reference.json").read_text(encoding="utf-8"))
    assert proof["reference_sha256"]==hashlib.sha256(primary.read_bytes()).hexdigest()
    marker("actual_image_reference_proof",{"method":proof["generation_source"],"reference_verified":True})
    if proof["generation_source"]!="gemini_character_identity_input":
      report["status"]="PARTIAL_REFERENCE_IMAGE_FALLBACK"
    else: report["status"]="PASS"
  else:
    receipt=json.loads((scene_dir/"muse_job.json").read_text(encoding="utf-8"))
    assert receipt.get("reference_images_uploaded") and len(receipt["reference_images_uploaded"])>=2
    marker("muse_uploaded_two_references",{"count":len(receipt["reference_images_uploaded"]),"remote_paths":receipt["reference_images_uploaded"]})
    report["status"]="PASS_TRANSPORT_ONLY_NOT_PROOF_OF_IMAGE_CONDITIONING"
  report["output_video"]=str(final)
except Exception as e:
  report["status"]="FAIL"
  report["error_code"]=str(e)[:600]
  report["trace"]=traceback.format_exc()[-5000:]
  print("E2E_FAILURE:",type(e).__name__,str(e),flush=True)
finally:
  report["finished"]=datetime.now().isoformat()
  save()
  print("E2E_RESULT",json.dumps({k:v for k,v in report.items() if k!="trace"},ensure_ascii=False),flush=True)
sys.exit(0 if report["status"].startswith("PASS") else 2)
