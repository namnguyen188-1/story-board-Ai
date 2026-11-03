import sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
import re

html = Path(r"D:\STORYBOARD_AI\studio\web\index.html").read_text(encoding="utf-8")
for m in re.finditer(r'<option[^>]*value="([^"]+)"[^>]*>(.*?)</option>', html, re.I):
    val, text = m.group(1), m.group(2)
    if any(k in text.lower() or k in val.lower() for k in ["chuyện", "kể", "story", "narrat", "mode", "drama", "nhánh"]):
        print(f"{val} -> {text.strip()}")

for m in re.finditer(r'<select[^>]*id="([^"]+)"[^>]*>', html, re.I):
    if any(k in m.group(1).lower() for k in ["mode", "production", "type"]):
        print("Select ID:", m.group(1))
