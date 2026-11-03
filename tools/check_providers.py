import sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
import re

html = Path(r"D:\STORYBOARD_AI\studio\web\index.html").read_text(encoding="utf-8")
for m in re.finditer(r'<select[^>]*id=["\'][^"\']*(?:provider|image)[^"\']*["\'][^>]*>.*?</select>', html, re.S | re.I):
    print("Found select:")
    print(m.group(0))

for m in re.finditer(r'<option[^>]*value=["\'][^"\']+["\'][^>]*>.*?</option>', html, re.I):
    if any(k in m.group(0).lower() for k in ["flow", "muse", "comfy", "tuanstor"]):
        print("Option:", m.group(0))
