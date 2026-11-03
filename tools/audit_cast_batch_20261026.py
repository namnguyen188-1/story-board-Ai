from pathlib import Path
import json
root=Path(r"D:\STORYBOARD_AI\studio\productions")
for p in sorted(root.glob("*/episode_*/drama_plan.json"),key=lambda x:x.stat().st_mtime,reverse=True)[:28]:
 try:
  d=json.loads(p.read_text(encoding="utf-8"))
  chars=d.get("cast") or {}
  ss=d.get("scenes") or []
  print(p.parent.parent.name,p.parent.name,"genre",d.get("genre"),"input",d.get("input_mode"),"cast",len(chars),"scenes",len(ss),
   "appearance_keys",list(next(iter(chars.values()),{}).keys())[:8])
 except Exception as e:print(type(e).__name__)
