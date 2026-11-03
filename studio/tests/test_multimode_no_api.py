"""Regression for all new modes. No network calls, no image API credits, no Gemini charges."""
from pathlib import Path
import sys,json,tempfile,io,wave,threading,urllib.request,urllib.error
from unittest.mock import patch
from types import SimpleNamespace
from http.server import HTTPServer
root=Path(r"D:\STORYBOARD_AI\studio")
sys.path.insert(0,str(root))
from studio_input_modes import parse_locked_screenplay,youtube_url,analyze_reference
from studio_modes import resolve_genre,resolve_style,voice_for,tts_style
from mcp_v2_batch import image_prompt
from studio_color_render import create_silence,color_video
from series_studio import parser,produce_plan,ffprobe
from web_server import StudioRequestHandler
from studio_voices import VOICES
from PIL import Image
assert resolve_style("auto","stoic")=="color_cinematic"
assert resolve_style("auto","animation")=="color_animation"
assert resolve_style("auto","whiteboard")=="whiteboard"
assert voice_for("Spanish","stoic","ES","auto")=="Charon"
assert voice_for("Vietnamese","family_drama","VN","auto")=="Aoede"
assert "Spain Spanish" in tts_style("Spanish","stoic","ES")
assert "Mexican Spanish" in tts_style("Spanish","stoic","MX")
assert voice_for("English","stoic","US","Puck")=="Puck"
print("LANGUAGE_GENRE_COUNTRY_VOICE_PASS",flush=True)

saved=root/"productions"/"Whiteboard-Chronicles"/"episode_003"/"plan.json"
raw=json.loads(saved.read_text(encoding="utf-8"))["config"]["prompt"]
scenes=parse_locked_screenplay(raw)
assert len(scenes)==8,len(scenes)
assert scenes[0]["script_seconds"]==8
assert "vi phạm" in scenes[0]["narration"]
assert not scenes[5]["narration"].strip()
assert "Không thể" in scenes[6]["narration"]
assert scenes[2]["narration"]!=scenes[0]["narration"]
print("EIGHT_SHOT_LOCKED_SCRIPT_AND_DIALOGUE_PASS",flush=True)

with tempfile.TemporaryDirectory(prefix="studio_modes_") as tmp:
    directory=Path(tmp)/"serial"
    ep=directory/"episode_001"
    args=parser().parse_args(["run","--input-mode","script","--mode","live",
       "--series","Original HOA Script","--episode","1","--minutes","1",
       "--scene-seconds","8","--genre","family_drama","--visual-style","color_cinematic",
       "--region","VN","--voice-name","Kore",
       "--prompt","placeholder"])
    plan=produce_plan(args,directory,ep,raw)
    assert plan["scene_count"]==8
    assert plan["scenes"][0]["narration"]==scenes[0]["narration"]
    assert "Ethan" not in json.dumps(plan["bible"])
    plan_again=produce_plan(args,directory,ep,raw)
    assert plan_again["fingerprint"]==plan["fingerprint"]
    print("LOCKED_PLAN_NO_GEMINI_NO_STALE_BIBLE_PASS",flush=True)

assert youtube_url("https://youtu.be/9hE5-98ZeCg")=="https://www.youtube.com/watch?v=9hE5-98ZeCg"
assert youtube_url("https://www.youtube.com/shorts/9hE5-98ZeCg")=="https://www.youtube.com/watch?v=9hE5-98ZeCg"
for invalid in ["http://youtube.com/watch?v=9hE5-98ZeCg",
                "https://youtube.com.evil.test/watch?v=9hE5-98ZeCg",
                "https://127.0.0.1/private",
                "https://www.youtube.com/playlist?list=abc"]:
    try:youtube_url(invalid)
    except ValueError:pass
    else:raise AssertionError("unsafe URL accepted")
calls=[]
class Models:
    def generate_content(self,**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(text=json.dumps({
            "genre":"stoic","primary_language":"Spanish",
            "hook_technique":"Reflective question",
            "new_original_story_seed":"A new fictional student's journey into practical stoic resilience",
            "scene_pacing":"Patient","visual_style":"realistic marble art",
            "narrative_structure":"hook, problem, insight, action"}))
a=analyze_reference(SimpleNamespace(models=Models()),"gemini-3.8-flash",
                    "https://youtu.be/9hE5-98ZeCg")
assert a["genre"]=="stoic" and len(calls)==1
assert "youtube.com/watch?v=" in repr(calls[0]["contents"]).lower()
print("YOUTUBE_URL_AND_MOCK_VIDEO_ANALYSIS_PASS",flush=True)

bible={"production_genre":"stoic","visual_style_mode":"color_cinematic",
       "characters":[{"name":"Marcus","appearance":"historically plausible Roman marble sculpture"}],
       "visual_style":"photorealistic"}
prompt=image_prompt({"description":"Marcus Aurelius contemplates beneath a stone arch",
                     "visual_setup":"Wide low-angle shot"},bible)
assert "marble" in prompt.lower()
assert "whiteboard ink" not in prompt.lower()
print("COLORED_MCP_IMAGE_PROMPT_PASS",flush=True)

with tempfile.TemporaryDirectory(prefix="studio_cinematic_") as tmp:
    t=Path(tmp)
    source=root/"mcp_image_test_result"/"city_lost_time_mcp_scene_001.jpg"
    assert source.exists(),"previous validated MCP reference image missing"
    audio=t/"silence.wav"
    create_silence(audio,2.2)
    with wave.open(str(audio),"rb") as w:
        assert abs(w.getnframes()/w.getframerate()-2.2)<.1
    video=t/"colored.mp4"
    color_video(source,audio,video,640,360,fps=10)
    meta,duration=ffprobe(video)
    assert 2.15<duration<2.6,duration
    assert meta["streams"][0]["width"]==640
    print("REAL_COLOR_IMAGE_TO_VIDEO_LOCAL_PASS",round(duration,2),flush=True)

# Local requests explicitly malformed: service must reject before any AI job.
server=HTTPServer(("127.0.0.1",0),StudioRequestHandler)
t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
try:
    url="http://127.0.0.1:"+str(server.server_port)+"/api/produce"
    def bad(body):
        request=urllib.request.Request(url,data=json.dumps(body).encode(),
              headers={"Content-Type":"application/json"},method="POST")
        try:
            urllib.request.urlopen(request,timeout=3)
        except urllib.error.HTTPError as e:
            return e.code,json.loads(e.read().decode("utf-8"))
        raise AssertionError("Invalid request unexpectedly started a job")
    assert bad({"input_mode":"link","reference_url":"https://bad.example/path"})[0]==400
    assert bad({"input_mode":"script","prompt":"Please make a 1 minute video."})[0]==400
    assert bad({"input_mode":"idea","prompt":"Valid idea","genre":"not-a-genre"})[0]==400
    print("BACKEND_INPUT_VALIDATION_NO_API_PASS",flush=True)
finally:
    server.shutdown()
print("ALL_MULTIMODE_REGRESSIONS_PASS",flush=True)
