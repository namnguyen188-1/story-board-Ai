from pathlib import Path
import sys, json, tempfile
ROOT=Path(r"D:\STORYBOARD_AI\studio")
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/"engine"))
from cinematic_engine.drama_asset_manager import get_scene_character_anchors
from cinematic_engine.native_audio_subtitles import align_native_audio
from muse_gateway_worker import run_render

ep=ROOT/"productions"/"DRAMA"/"episode_001"
plan=json.loads((ep/"drama_plan.json").read_text(encoding="utf-8"))
scene=plan["scenes"][0]
names=scene.get("characters_present",[])
refs=get_scene_character_anchors(ep,names)
print("SCENE1_CHARACTERS:",names,flush=True)
print("SCENE1_REFERENCE_IMAGES:",[(p.get("character_name"),Path(p.get("image_path","")).is_file()) for p in refs],flush=True)
assert len(refs)>=2 and all(Path(r["image_path"]).is_file() for r in refs), "multi-character assets must exist"

with tempfile.TemporaryDirectory() as td:
    try:
        run_render({"output_image_path":str(Path(td)/"image.png"),"prompt":"test","width":1280,"height":720,"duration":10,
                    "reference_image":str(Path(td)/"missing_reference.jpg")})
        raise AssertionError("reference guard silently accepted missing image")
    except RuntimeError as exc:
        assert "MUSE_REFERENCE_MISSING" in str(exc), str(exc)
        print("MISSING_REFERENCE_FAIL_CLOSED: PASS",flush=True)

audio=ep/"scenes"/"scene_0001"/"dialogue_master.wav"
expected="\n".join(str(b.get("text","")) for b in scene.get("dialogue_beats",[]))
print("AUDIO:",audio.name,"expected_chars:",len(expected),flush=True)
result=align_native_audio(audio,expected,language="Vietnamese")
print("ACTUAL_AUDIO_QC:",json.dumps({"words":len(result.get("words",[])),"duration":result.get("duration"),
                   "script_mismatch":result.get("script_mismatch"),"transcript":str(result.get("transcript",""))[:400]},
                   ensure_ascii=False),flush=True)
print("REAL_AUDIO_CHECK_COMPLETED",flush=True)
