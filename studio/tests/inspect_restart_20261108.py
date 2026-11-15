from pathlib import Path
import re
p=Path(r"D:\STORYBOARD_AI\studio\desktop_app.py")
s=p.read_text(encoding="utf8",errors="replace").splitlines()
for i,x in enumerate(s):
 if any(t in x for t in ("web_server", "Popen", "restart", "server_proc", "subprocess", "supervisor", "127.0.0.1:8765")):
  print("\n--",i+1,"--")
  for j in range(max(0,i-2),min(len(s),i+7)):
   if s[j].strip():print(str(j+1)+": "+s[j][:200])
