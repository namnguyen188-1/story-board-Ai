from pathlib import Path
import re,json
p=Path(r"D:\STORYBOARD_AI\studio\studio_mcp")
print("NODE REFERENCES (module paths, no secrets):")
refs=set()
for py in p.glob("*.py"):
 t=py.read_text(encoding="utf-8")
 for m in re.finditer(r'["\\x27]([A-Za-z0-9_.-]+\\.mjs)["\\x27]',t):
  refs.add((py.name,m.group(1)))
for item in sorted(refs):print(*item)
cfg=p/"node"/"studio-flow-config.json"
if cfg.exists():
 try:
  d=json.loads(cfg.read_text(encoding="utf-8"))
  print("STUDIO FLOW CONFIG TOP KEYS",list(d) if isinstance(d,dict) else type(d).__name__)
  for k,v in (d.items() if isinstance(d,dict) else []):
   print("config field",k, "type",type(v).__name__, "items",len(v) if isinstance(v,(dict,list)) else "redacted")
 except Exception as e:print("cfg invalid",type(e).__name__)
print("MCP NODE RUNTIME:")
for name in ("dist/cli.js","dist/index.js","node.exe","auto-flow-shared-install.mjs",
             "auto-flow-provision-project.mjs","studio-flow-rpc.mjs","node_modules"):
 print(name,(p/"node"/name).exists())
