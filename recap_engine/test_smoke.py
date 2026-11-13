import sys
from pathlib import Path

recap_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(recap_dir))

import config

cfg = config.load_config()
print(f"✅ Config OK: {len(cfg.get('gemini_keys', []))} keys loaded. Default model: {cfg.get('model_name')}")
print(f"Export dir: {cfg.get('export_dir')}")

rotator = config.KeyRotator(cfg.get("gemini_keys", []))
print(f"Key rotator ready. Current key prefix: {rotator.get_current_key()[:10]}...")
