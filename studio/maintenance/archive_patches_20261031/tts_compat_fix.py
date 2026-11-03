from pathlib import Path
import py_compile, sys, tempfile, wave, io
root=Path(r"D:\STORYBOARD_AI\studio")
p=root/"engine"/"tools"/"tts.py"
s=p.read_text(encoding="utf-8")
line='                    "response_format":{"audio":{"mime_type":"AUDIO_L16","sample_rate":24000}},\n'
assert line in s
s=s.replace(line,"",1)
anchor='        if utils.save_pcm_to_wav(output_path, data):'
assert anchor in s
s=s.replace(anchor,
    '''        # Gemini 3.8 returns a complete WAV container by default;
        # older models may return headerless PCM. Support both safely.
        if data[:4] == b"RIFF" and data[8:12] == b"WAVE":
            with open(output_path, "wb") as f:
                f.write(data)
            print("TTS WAV generated:", output_path)
            return output_path

'''+anchor,1)
p.write_text(s,encoding="utf-8")
py_compile.compile(str(p),doraise=True)
print("TTS_AUDIO_CONTAINER_FIX_PASS")
sys.path.insert(0,str(root/"engine"))
from tools import tts, utils
print("REAL_ENGINE_IMPORT_PASS")
class Stub:
    def __init__(self,data):
        self.data=data
        self.config=None
    class Models:
        def __init__(self,outer): self.outer=outer
        def generate_content(self,**kw):
            self.outer.config=kw["config"]
            from types import SimpleNamespace
            return SimpleNamespace(candidates=[SimpleNamespace(
                content=SimpleNamespace(parts=[SimpleNamespace(
                    inline_data=SimpleNamespace(data=self.outer.data))]))])
    @property
    def models(self):
        return self.Models(self)
out=root/"tts_mock_test"
out.mkdir(exist_ok=True)
utils.set_output_dir(str(out))
raw=(b"\x00\x00" * 24000)
with io.BytesIO() as buffer:
    with wave.open(buffer,"wb") as wf:
        wf.setnchannels(1);wf.setsampwidth(2);wf.setframerate(24000)
        wf.writeframes(raw)
    valid_wav=buffer.getvalue()
for tag,payload in (("riff",valid_wav),("pcm",raw)):
    stub=Stub(payload)
    utils.client=stub
    path=tts.generate_tts_audio_tool_fn("This is a dummy audio test.",language="English")
    assert Path(path).is_file(),path
    with wave.open(path,"rb") as wf:
        assert wf.getframerate()==24000
        assert wf.getnframes()==24000, (tag,wf.getnframes())
    assert "response_format" not in stub.config
    assert stub.config["speech_config"]["voice_config"]["voice"]=="Kore"
    print("TTS_MOCK_PASS",tag,Path(path).name)
print("TTS_COMPAT_TESTS_PASS")
