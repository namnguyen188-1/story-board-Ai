# -*- coding: utf-8 -*-
"""Final no-credit verification matrix. Isolated processes, no real uploads."""
import os,sys,json,subprocess,time
from pathlib import Path
ROOT=Path(r"D:\STORYBOARD_AI\studio")
PR=ROOT/"runtime"/"python"/"python.exe"
MU=ROOT/"runtime"/"muse"/"python"/"python.exe"
ROOT_PARENT=ROOT.parent
tests=ROOT/"tests"
def unit(name,python=PR):
 return [str(python),"-m","unittest","discover","-s",str(tests),"-p",name,"-q"]
checks=[
 ("Muse CLI facade",unit("test_muse_cli_provider.py")),
 ("Muse gateway receipts (10 cases)",unit("test_muse_gateway_worker.py",MU)),
 ("Muse login isolation (14 cases)",unit("test_muse_login.py")),
 ("Muse UI binding",unit("test_muse_video_integration.py")),
 ("9-field locked script",unit("test_muse_skill_input.py")),
 ("Series episode continuity",unit("test_episode_storyline.py")),
 ("SEO metadata and thumbnail",unit("test_seo_metadata.py")),
 ("SEO grounding",unit("test_seo_evidence.py")),
 ("SEO topic alignment",unit("test_topic_alignment.py")),
 ("vidIQ evidence + fallbacks",unit("test_vidiq_auto.py")),
 ("YouTube upload mock routes",unit("test_youtube_upload_routes.py")),
 ("International SEO standards",
   [str(PR),"-c",
    "import sys,unittest;sys.path.insert(0,r'D:\\STORYBOARD_AI');sys.path.insert(0,r'D:\\STORYBOARD_AI\\studio');suite=unittest.TestLoader().discover(r'D:\\STORYBOARD_AI\\studio\\tests',pattern='test_seo_international_standards.py');res=unittest.TextTestRunner(verbosity=0).run(suite);sys.exit(0 if res.wasSuccessful() else 1)"]),
 ("Story skill 2 episodes",[str(PR),str(tests/"test_skill_planner_e2e.py")]),
 ("All visual style prompts",[str(PR),str(ROOT_PARENT/"tools"/"tests"/"test_multi_role_style_menu_20261026.py")]),
 ("Failed 3s clip protection",[str(PR),str(ROOT_PARENT/"tools"/"tests"/"test_failclosed_muse_qc_20261026.py")]),
 ("Browser UI 2 viewport sizes",[str(PR),str(ROOT_PARENT/"tools"/"audit_real_browser_ui_20261026.py")])
]
env=os.environ.copy();env["PYTHONUTF8"]="1"
env["PYTHONPATH"]=str(ROOT_PARENT)+os.pathsep+str(ROOT)+os.pathsep+str(tests)
results=[]
for label,command in checks:
 try:
  cp=subprocess.run(command,cwd=str(ROOT_PARENT),env=env,stdout=subprocess.PIPE,
      stderr=subprocess.PIPE,encoding="utf-8",errors="replace",timeout=28)
  status="PASS" if cp.returncode==0 else "FAIL"
  failure=(cp.stderr+"\n"+cp.stdout)[-1100:] if status!="PASS" else ""
 except subprocess.TimeoutExpired:
  status="TIMEOUT";failure="Exceeded 28-second test cutoff"
 results.append({"test_group":label,"status":status,"failure":failure})
 print(status,label,flush=True)
out=ROOT/"diagnostics"/"audit_final_tests_20261026.json"
out.write_text(json.dumps({"groups":results,"pass":sum(t["status"]=="PASS" for t in results),
  "fail":sum(t["status"]!="PASS" for t in results),"note":"No live uploads/paid generation"},ensure_ascii=False,indent=2),encoding="utf-8")
print("FINAL_VERIFIED_GROUPS",sum(t["status"]=="PASS" for t in results),"/",len(results),flush=True)
