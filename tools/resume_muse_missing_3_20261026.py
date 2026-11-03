# -*- coding: utf-8 -*-
"""Resume existing user's damaged episode, keep 87 valid clips, no publishing."""
import json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(r"D:\STORYBOARD_AI\studio")
EP=ROOT/"productions"/"ho-t-h-nh-3d"/"episode_001"
QA=ROOT/"diagnostics"/"E2E_REPAIR_20261026"
plan=json.loads((EP/"plan.json").read_text(encoding="utf-8-sig"))
name=plan["config"]["series"]
state=json.loads((EP/"episode_qc.json").read_text(encoding="utf-8"))
assert state["status"]=="FAILED_INCOMPLETE",state
assert [x["scene"] for x in state["issues"]]==[11,63,67],state
assert (QA/"episode_001_final_BEFORE_REPAIR.mp4").is_file()
sys.path.insert(0,str(ROOT))
import muse_accounts
from series_studio import slug
assert slug(name)=="ho-t-h-nh-3d",slug(name)
assert len(muse_accounts.get_ready_accounts()) >= 3
cmd=[
 str(ROOT/"runtime"/"python"/"python.exe"),"-u",
 str(ROOT/"pipeline_router.py"),"run",
 "--production-mode","cinematic_drama",
 "--series",name,"--episode","1",
 "--prompt",str(plan["config"].get("prompt") or name),
 "--minutes","15", "--scene-seconds","10",
 "--language","Vietnamese","--genre","animation",
 "--visual-style","color_animation","--size","720x1280",
 "--workers","6","--image-provider","muse_video",
 "--input-mode","idea","--model","gemini-3.8-flash",
 "--subtitle-style","karaoke_viral","--subtitle-size","76",
 "--resume","--no-shorts"
]
QA.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,PYTHONUTF8="1",PYTHONIOENCODING="utf-8")
with (QA/"repair_stdout.log").open("wb") as out, (QA/"repair_stderr.log").open("wb") as err:
 p=subprocess.Popen(cmd,cwd=str(ROOT),stdout=out,stderr=err,env=env,
                    stdin=subprocess.DEVNULL,
                    creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
report={"pid":p.pid,"state":"RUNNING","series":name,"missing_scenes":[11,63,67],
        "started":time.strftime("%Y-%m-%d %H:%M:%S"),
        "logs":[str(QA/"repair_stdout.log"),str(QA/"repair_stderr.log")]}
(QA/"repair_manifest.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print("REPAIR_STARTED_PID",p.pid,flush=True)
print("MISSING_SCENES",report["missing_scenes"],flush=True)
