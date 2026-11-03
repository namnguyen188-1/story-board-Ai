import sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path

server = Path(r"D:\STORYBOARD_AI\studio\web_server.py").read_text(encoding="utf-8")
idx = server.find('prod_mode = str(body.get("production_mode"')
if idx != -1:
    print(server[idx:idx+3000])
