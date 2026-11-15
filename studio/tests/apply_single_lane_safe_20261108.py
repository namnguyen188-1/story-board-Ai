from pathlib import Path
import hashlib,json,os,subprocess,sys,time,urllib.request,shutil
root=Path(r"D:\STORYBOARD_AI\studio")
status=json.load(urllib.request.urlopen("http://127.0.0.1:8765/api/status",timeout=5))
queue=json.loads((root/"production_queue.json").read_text(encoding="utf8"))
if status.get("running") or queue.get("active") or queue.get("items"):
 raise RuntimeError("STOP_UNSAFE_ACTIVE_PRODUCTION_OR_QUEUE")
checkpoint=root/"runtime"/("single_lane_safe_"+time.strftime("%Y%m%d_%H%M%S"))
checkpoint.mkdir(parents=True,exist_ok=False)
names=["web/index.html","web/app.js","web_server.py"]
original={}
replacements={
 "web/index.html":[
  ('class="btn btn-secondary btn-xs worker-chip" data-val="1"','class="btn btn-secondary btn-xs worker-chip active-chip" data-val="1"'),
  ('class="btn btn-secondary btn-xs worker-chip active-chip" data-val="4"','class="btn btn-secondary btn-xs worker-chip" data-val="4"'),
  ('<input type="hidden" id="inWorkers" value="4">','<input type="hidden" id="inWorkers" value="1">'),
  ('data-val="2" onclick="setWorkerThreads(2)"','data-val="2" disabled title="Chế độ an toàn: 1 luồng" onclick="setWorkerThreads(2)"'),
  ('data-val="4" onclick="setWorkerThreads(4)"','data-val="4" disabled title="Chế độ an toàn: 1 luồng" onclick="setWorkerThreads(4)"'),
  ('data-val="6" onclick="setWorkerThreads(6)"','data-val="6" disabled title="Chế độ an toàn: 1 luồng" onclick="setWorkerThreads(6)"'),
  ('data-val="8" onclick="setWorkerThreads(8)"','data-val="8" disabled title="Chế độ an toàn: 1 luồng" onclick="setWorkerThreads(8)"')],
 "web/app.js":[
  ('const savedWorkers = localStorage.getItem("storyboard_workers");','const savedWorkers = "1";\n  try { localStorage.setItem("storyboard_workers", "1"); } catch (err) {}'),
  ('const t = Math.min(Math.max(1, parseInt(threads, 10) || 2), 16);','const t = 1; // single-lane stability mode'),
  ('workers: parseInt(el.inWorkers ? el.inWorkers.value : "4", 10) || 4','workers: 1'),
  ('const workers = parseInt(el.inWorkers ? el.inWorkers.value : "4", 10) || 4;','const workers = 1;'),
  ('setWorkerThreads(4);','setWorkerThreads(1);')],
 "web_server.py":[
  ('workers = int(body.get("workers", 0) or 0) or 4','workers = 1  # Temporary single-lane stability mode'),
  ('workers = min(max(1, workers), 16)  # Support up to 16 workers for high-core workstations (e.g. 56 threads)','workers = 1  # Enforce one scene-worker for all API clients and queued jobs')]
}
try:
 for name in names:
  p=root/name
  data=p.read_bytes()
  original[name]=data
  dest=checkpoint/name
  dest.parent.mkdir(parents=True,exist_ok=True)
  dest.write_bytes(data)
 for name in names:
  p=root/name
  raw=original[name]
  for old,new in replacements[name]:
   a,b=old.encode("utf8"),new.encode("utf8")
   count=raw.count(a)
   if name=="web/app.js" and old.startswith("workers: parseInt("):
    expected=2
   else: expected=1
   if count!=expected:raise ValueError(f"unexpected pattern {name}: {old[:45]}, count={count}, expected={expected}")
   raw=raw.replace(a,b)
  temp=p.with_suffix(p.suffix+".single-lane-tmp")
  temp.write_bytes(raw)
  os.replace(temp,p)
 checks=[
 [r"C:\Program Files\nodejs\node.exe","--check",str(root/"web/app.js")],
 [str(root/"runtime/python/python.exe"),"-B","-X","utf8","-c","from pathlib import Path;compile(Path(r'D:\STORYBOARD_AI\studio\web_server.py').read_bytes(),r'D:\STORYBOARD_AI\studio\web_server.py','exec')"]
 ]
 for cmd in checks:
  done=subprocess.run(cmd,cwd=root,capture_output=True,text=True,encoding="utf8",errors="replace",timeout=45)
  print("CHECK",cmd[-1][:85],done.returncode,(done.stdout+done.stderr)[:450])
  if done.returncode:raise RuntimeError("syntax check failed")
 s=(root/"web_server.py").read_text(encoding="utf8")
 a=(root/"web/app.js").read_text(encoding="utf8")
 h=(root/"web/index.html").read_text(encoding="utf8")
 assert s.count('workers = 1  # Enforce one scene-worker for all API clients and queued jobs')==1
 assert 'workers: 1,' in a and a.count('workers: 1')==2 and 'const workers = 1;' in a
 assert 'id="inWorkers" value="1"' in h and h.count('disabled title="Chế độ an toàn: 1 luồng"')==4
 report={"result":"PATCHED_AND_SYNTAX_VERIFIED","machine":"DESKTOP-EE8BGVF","checkpoint":str(checkpoint),
         "files":[{"file":n,"backup_sha256":hashlib.sha256(original[n]).hexdigest(),"after_sha256":hashlib.sha256((root/n).read_bytes()).hexdigest()} for n in names],
         "production_running_at_change":False,"queue_active_at_change":False,"generation_submitted":False}
 (checkpoint/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf8")
 print(json.dumps(report,ensure_ascii=True))
except Exception as exc:
 for name,data in original.items():
  (root/name).write_bytes(data)
 print("ROLLED_BACK",type(exc).__name__,str(exc))
 raise
