from pathlib import Path
import subprocess,os,json,time,urllib.request
root=Path(r"D:\STORYBOARD_AI\studio")
url="http://127.0.0.1:8765/api/status"
def check():
 try:
  with urllib.request.urlopen(url,timeout=1.5) as f:
   return json.load(f)
 except Exception: return None
before=check()
if before:
 print("REFUSE_DUPLICATE_BACKEND",json.dumps({k:before.get(k) for k in ["running","stage"]}))
 raise SystemExit(2)
env=os.environ.copy()
env["STORYBOARD_NATIVE_WINDOW_OWNER"]="1"
exe=root/"runtime/python/pythonw.exe"
p=subprocess.Popen([str(exe),str(root/"desktop_app.py")],cwd=str(root),env=env,
  stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
  creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0),close_fds=True)
last=None
for i in range(35):
 time.sleep(0.5)
 last=check()
 if last:break
 if p.poll() is not None:break
result={"backend_pid":p.pid,"backend_process_alive":p.poll() is None,"http_ready":bool(last),
 "stage":last.get("stage") if last else None,"new_gui_window":False}
print(json.dumps(result))
if not last or p.poll() is not None:
 raise RuntimeError("BACKEND_RESTART_NOT_READY")
