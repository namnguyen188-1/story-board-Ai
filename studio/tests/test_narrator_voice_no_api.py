"""Offline regression for Gemini voice selector. NEVER calls a live API."""
import io,json,sys,tempfile,wave
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
studio=Path(r"D:\STORYBOARD_AI\studio")
sys.path.insert(0,str(studio))
sys.path.insert(0,str(studio/"engine"))
from studio_voices import validate_voice,VOICES
from series_studio import parser
from tools import tts
from html.parser import HTMLParser

class IdCollector(HTMLParser):
    def __init__(self):super().__init__();self.ids={}
    def handle_starttag(self,tag,attrs):
        if (key:=dict(attrs).get("id")):self.ids[key]=tag
html=IdCollector()
html.feed((studio/"web"/"index.html").read_text(encoding="utf-8"))
assert html.ids.get("inVoice")=="select"
js=(studio/"web"/"app.js").read_text(encoding="utf-8")
assert 'voice_name: el.inVoice ? el.inVoice.value : "Kore"' in js
for item in VOICES: assert validate_voice(item)==item
try:
    validate_voice("UNSAFE_OTHER_VOICE")
except ValueError: pass
else:raise AssertionError("invalid voice accepted")
cli=parser().parse_args(["run","--prompt","A complete test story", "--voice-name","Charon"])
assert cli.voice_name=="Charon"
print("UI_CLI_AND_WHITELIST_PASS",flush=True)

buf=io.BytesIO()
with wave.open(buf,"wb") as w:
    w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000)
    w.writeframes(b"\x00\x00"*4000)
pcm=buf.getvalue()
response=SimpleNamespace(candidates=[SimpleNamespace(content=SimpleNamespace(
    parts=[SimpleNamespace(inline_data=SimpleNamespace(data=pcm))]))])
calls=[]
class DummyModels:
    def generate_content(self,*,model,contents,config):
        calls.append({"model":model,"contents":contents,"config":config})
        return response
client=SimpleNamespace(models=DummyModels())
with tempfile.TemporaryDirectory(prefix="voice_qa_") as temp:
    with patch.object(tts.utils,"client",client),\
         patch.object(tts.utils,"GLOBAL_OUTPUT_DIR",temp):
        for voice in ("Kore","Charon","Orus","Puck"):
            path=tts.generate_tts_audio_tool_fn("This is a synthetic voice-selection test.",
                                                language="Spanish",voice_name=voice)
            assert Path(path).is_file(),path
            with wave.open(path,"rb") as w:
                assert w.getframerate()==24000
            assert calls[-1]["config"]["speech_config"]["voice_config"]["voice"]==voice
            assert calls[-1]["model"]=="gemini-3.8-flash-tts"
        assert len(calls)==4
print("NO_API_GEMINI_TTS_VOICE_ROUTING_PASS",flush=True)
print("TEST_TOTAL_VOICES",len(VOICES),flush=True)
