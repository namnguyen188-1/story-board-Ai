import subprocess,sys,time,json
from pathlib import Path
root=Path(r"D:\STORYBOARD_AI\studio")
exe=str(root/"runtime/python/python.exe")
cases=[("thumbnail",root/"tests/test_thumbnail_qa_20261108.py",8),
       ("no_resubmit",root/"tests/test_single_lane_no_resubmit_20261108.py",2)]
cycles=20
r={"cycles":cycles,"cases":{},"total_cases":0,"all_passed":True,"mode":"mock_only","flow_paid_calls":0}
start=time.perf_counter()
for label,p,each in cases:
 results=[]
 for i in range(cycles):
  proc=subprocess.run([exe,"-B","-X","utf8",str(p)],cwd=root,capture_output=True,
       text=True,encoding="utf8",errors="replace",timeout=25)
  ok=proc.returncode==0 and f"Ran {each} tests" in (proc.stdout+proc.stderr)
  results.append(ok)
  if not ok:
   r["all_passed"]=False
   r[label+"_error"]=(proc.stdout+proc.stderr)[-1000:]
   break
 r["cases"][label]={"cycles_run":len(results),"tests_per_cycle":each,
                    "passed":sum(results)*each,"failed_cycles":results.count(False)}
 r["total_cases"]+=sum(results)*each
 print(label,"PASS",sum(results),"/",len(results),"cycles",flush=True)
 if not r["all_passed"]:break
r["duration_sec"]=round(time.perf_counter()-start,2)
out=root/"runtime/thumbnail_reliability_qa_20261108/mock_stress_results.json"
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(r,indent=2,ensure_ascii=False),encoding="utf8")
print("MOCK_STRESS",json.dumps(r,ensure_ascii=False))
