import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from core.voice_engine import RecapVoiceEngine

engine = RecapVoiceEngine()
print("Engine initialized with voice:", engine.default_voice)

out_file = r"D:\STORYBOARD_AI\recap_engine\test_engine_voice.mp3"
text = "Người đàn ông này vừa bước chân vào khách sạn thì cả băng đảng sát thủ đều phải cúi đầu né tránh."

duration = engine.generate_single_speech(text, out_file, voice_name="Fenrir", speed=1.15)
print(f"✅ Generated single speech! File: {out_file}, Duration: {duration}s")
