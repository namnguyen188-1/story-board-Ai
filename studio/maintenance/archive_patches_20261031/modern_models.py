from pathlib import Path
import py_compile
root=Path(r"D:\STORYBOARD_AI\studio")
c=root/"engine"/"config.py"
s=c.read_text(encoding="utf-8")
required={
'MODEL_NAME = "gemini-2.5-pro"':'MODEL_NAME = "gemini-3.8-flash"',
'IMAGE_GEN_MODEL = "gemini-3-pro-image"':'IMAGE_GEN_MODEL = "gemini-nano-banana-2.1"',
'TTS_MODEL = "gemini-3.1-flash-tts-preview"':'TTS_MODEL = "gemini-3.8-flash-tts"'
}
for before,after in required.items():
    assert before in s, before
    s=s.replace(before,after,1)
c.write_text(s,encoding="utf-8")

voice=root/"engine"/"tools"/"tts.py"
t=voice.read_text(encoding="utf-8")
needle='''        response = utils.client.models.generate_content(
            model=TTS_MODEL,
            contents=prompt_text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=speech_config,
            )
        )
'''
assert needle in t
repl='''        if TTS_MODEL.startswith("gemini-3.8"):
            # Current Gemini 3.8 TTS: explicitly request raw PCM to avoid
            # putting an extra WAV header around an already packaged WAV.
            response = utils.client.models.generate_content(
                model=TTS_MODEL,
                contents=[{"role":"user","parts":[{
                    "text":text,
                    "speech_metadata":{"style":"Natural, expressive, confident and coherent storytelling in "+language}
                }]}],
                config={
                    "response_modalities":["AUDIO"],
                    "response_format":{"audio":{"mime_type":"AUDIO_L16","sample_rate":24000}},
                    "speech_config":{"voice_config":{"voice":"Kore"}}
                }
            )
        else:
'''+"".join("    "+line+"\n" for line in needle.rstrip().split("\n"))
t=t.replace(needle,repl,1)
voice.write_text(t,encoding="utf-8")

a=root/"series_studio.py"
s=a.read_text(encoding="utf-8")
assert 'default="gemini-2.5-pro"' in s
a.write_text(s.replace('default="gemini-2.5-pro"','default="gemini-3.8-flash"'),encoding="utf-8")
g=root/"studio_gui.py"
s=g.read_text(encoding="utf-8")
assert '"gemini-2.5-pro"' in s
g.write_text(s.replace('"gemini-2.5-pro"','"gemini-3.8-flash"'),encoding="utf-8")
for file in (c,voice,a,g):
    py_compile.compile(str(file),doraise=True)
print("MODERN_MODELS_PATCHED_AND_COMPILED")
