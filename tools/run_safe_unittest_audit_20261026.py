# -*- coding: utf-8 -*-
"""Isolated, bounded unittest audit; never runs tests with live paid providers."""
import json, os, subprocess, sys, time
from pathlib import Path
ROOT=Path(r"D:\STORYBOARD_AI\studio")
OUT=ROOT/"diagnostics"/"audit_unit_results_20261026.json"
LOG=ROOT/"diagnostics"/"audit_unit_details_20261026.log"
PATTERNS=[
"test_muse_cli_provider.py", "test_muse_gateway_worker.py",
"test_muse_skill_input.py","test_muse_video_integration.py",
"test_episode_storyline.py","test_seo_metadata.py",
"test_seo_evidence.py","test_seo_review.py","test_seo_generation.py",
"test_seo_international_standards.py","test_vidiq_auto.py",
"test_topic_alignment.py","test_youtube_upload_routes.py",
"test_locked_duration_guard.py","test_locked_script_silence.py",
"test_retry_503.py","test_mcp_provider_lock.py","test_scene_budget_62_no_credit.py",
"test_private_mcp_node_guards.py","test_resume_retry_windowless.py",
]
env=os.environ.copy()
env["PYTHONPATH"]=str(ROOT)+os.pathsep+str(ROOT.parent)+os.pathsep+str(ROOT/"tests")
env["PYTHONUTF8"]="1"
results=[]
with LOG.open("w",encoding="utf-8") as f:
 for name in PATTERNS:
  start=time.monotonic()
  args=[sys.executable,"-m","unittest","discover","-s",str(ROOT/"tests"),"-p",name,"-v"]
  try:
   p=subprocess.run(args,cwd=str(ROOT),capture_output=True,text=True,encoding="utf-8",
                    errors="replace",env=env,timeout=22)
   status="PASS" if p.returncode==0 else "FAIL"
   detail=p.stdout+"\n"+p.stderr
  except subprocess.TimeoutExpired:
   status="TIMEOUT";detail="TIMEOUT: 22 seconds"
  elapsed=round(time.monotonic()-start,2)
  results.append({"test_file":name,"status":status,"seconds":elapsed,
                  "failure_tail":detail[-1600:] if status!="PASS" else ""})
  f.write("\n===== "+name+" : "+status+" =====\n"+detail[-7000:]+"\n");f.flush()
  OUT.write_text(json.dumps({"test_count":len(results),"results":results},
                            ensure_ascii=False,indent=2),encoding="utf-8")
  print(status,name,elapsed,flush=True)
print("SUMMARY",json.dumps({"PASS":sum(x["status"]=="PASS" for x in results),
                           "FAIL":sum(x["status"]=="FAIL" for x in results),
                           "TIMEOUT":sum(x["status"]=="TIMEOUT" for x in results)},ensure_ascii=False),flush=True)
