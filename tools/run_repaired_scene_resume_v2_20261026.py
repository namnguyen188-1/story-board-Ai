"""Live, bounded E2E resume for two QC-failed Muse scenes after one-shot prompt repair."""
import os,sys,json,subprocess,time
from pathlib import Path
ROOT=Path(r"D:\STORYBOARD_AI\studio")
EP=ROOT/"productions"/"ho-t-h-nh-3d"/"episode_001"
OUT=ROOT/"diagnostics"/"E2E_REPAIR_20261026"
OUT.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT))
from series_studio import slug
from muse_accounts import get_ready_accounts
plan=json.loads((EP/"plan.json").read_text(encoding="utf-8-sig"))
qc=json.loads((EP/"episode_qc.json").read_text(encoding="utf-8"))
series=str(plan["config"]["series"])
assert slug(series)=="ho-t-h-nh-3d"
assert qc.get("status")=="FAILED_INCOMPLETE" and qc.get("missing_scenes")==[63,67],qc
assert len(get_ready_accounts())>=1
assert not (EP/"episode_final.mp4").is_file()
assert not (EP/"episode_001_final.mp4").is_file()
for n in (63,67):
    d=EP/"scenes"/f"scene_{n:04d}"
    data=json.loads((d/"muse_job.json").read_text(encoding="utf-8"))
    assert data.get("state")=="failed", (n,data.get("state"))
    assert data.get("cli_ack") is True
    assert not (d/"muse_clip.mp4").exists()
before={p.name:(p/"scene_final.mp4").stat().st_size for p in (EP/"scenes").glob("scene_[0-9][0-9][0-9][0-9]") if (p/"muse_clip.mp4").is_file() and (p/"scene_final.mp4").is_file()}
assert len(before)==88,len(before)
query = "@(Get-CimInstance Win32_Process | Where-Object { $_.Name -like 'python*' -and $_.CommandLine -like '*pipeline_router.py*' }).Count"
active_count = int(subprocess.check_output(["powershell", "-NoProfile", "-Command", query], timeout=12).decode().strip())
assert active_count == 0, f"ANOTHER_JOB_ACTIVE count={active_count}"
cmd=[str(ROOT/"runtime"/"python"/"python.exe"),"-u",str(ROOT/"pipeline_router.py"),"run",
    "--production-mode","cinematic_drama","--mode","live",
    "--series",series,"--episode","1","--prompt",str(plan["config"].get("prompt") or series),
    "--minutes","15","--scene-seconds","10","--workers","2","--size","720x1280",
    "--language","Vietnamese","--genre","animation","--visual-style","color_animation",
    "--image-provider","muse_video","--model","gemini-3.5-flash",
    "--subtitle-style","karaoke_viral","--subtitle-size","76",
    "--input-mode","idea","--resume","--no-shorts"]
with (OUT/"repair_v2_stdout.log").open("wb") as out,(OUT/"repair_v2_stderr.log").open("wb") as err:
    p=subprocess.Popen(cmd,cwd=str(ROOT),stdin=subprocess.DEVNULL,stdout=out,stderr=err,
                       env=dict(os.environ,PYTHONUTF8="1",PYTHONIOENCODING="utf-8"),
                       creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
manifest={"pid":p.pid,"launched_at":time.strftime("%Y-%m-%d %H:%M:%S"),
          "reason":"Resume two confirmed terminal no-video scenes; one revised prompt each",
          "scene_numbers":[63,67],"successful_scene_count_before":len(before),
          "output_log":str(OUT/"repair_v2_stdout.log"),
          "stderr_log":str(OUT/"repair_v2_stderr.log"),
          "status":"RUNNING"}
(OUT/"repair_v2_manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
print("REPAIR_V2_STARTED",p.pid,flush=True)
print("TARGET_SCENES",manifest["scene_numbers"],flush=True)
print("PRESERVED_VALID_SCENES",len(before),flush=True)
