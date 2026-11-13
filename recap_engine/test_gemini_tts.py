import sys
from pathlib import Path
from google import genai
from google.genai import types

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import load_config

cfg = load_config()
client = genai.Client(api_key=cfg['gemini_keys'][0])

# Test gemini-2.5-flash-preview-tts or speech generation
tts_models = [
    "gemini-2.5-flash-preview-tts",
    "gemini-3.1-flash-tts-preview",
    "gemini-3.8-flash-tts",
    "gemini-2.5-flash"
]

for m in tts_models:
    try:
        print(f"Testing TTS model: {m}...")
        resp = client.models.generate_content(
            model=m,
            contents="Người đàn ông này vừa bước chân vào khách sạn.",
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name="Fenrir"
                        )
                    )
                )
            )
        )
        print(f"✅ Success with model {m}!")
        # Check parts for audio bytes
        for part in resp.candidates[0].content.parts:
            if part.inline_data:
                print(f"Audio mime_type: {part.inline_data.mime_type}, bytes: {len(part.inline_data.data)}")
                with open(r"D:\STORYBOARD_AI\recap_engine\test_gemini_voice.wav", "wb") as f:
                    f.write(part.inline_data.data)
                print("Saved audio to test_gemini_voice.wav")
                break
        break
    except Exception as e:
        print(f"❌ Failed with model {m}: {e}")
