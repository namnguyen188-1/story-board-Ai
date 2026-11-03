from pathlib import Path
import os,sys,hashlib,shutil,json,datetime
root=Path(r"D:\STORYBOARD_AI")
dist=root/"dist"
archive=root/"_ARCHIVE"/"OLDER_INSTALLERS_20261015"
report=Path(__file__).with_name("CLEANUP_DIST_20261015.json")
latest=dist/"StoryboardAI-AutoSetup-TransferTest-Setup.exe"
expected="D1B864B73623E49F42DE47F9AFBDEA0E61A2C737FB4E04A03F8C16BD45AD6E10"
old_stage=["Storyboard_AI_Studio_Pro_v1.0","Storyboard_AI_Studio_Pro_MultiGPU_Candidate"]
old_delete=["Setup_Storyboard_AI_Studio_Pro_v1.0.exe",
            "StoryboardAI-MultiGPU-Candidate-Setup.exe"]
old_archive=["StoryboardAI-Setup.exe","StoryboardAI-TransferTest-FULL-Setup.exe",
             "Storyboard_AI_Studio_Pro_v1.0.zip","MultiGPU-Candidate-Installer.iss",
             "TransferTest-FULL-Installer.iss",
             "StoryboardAI-TransferTest-FULL-SHA256.txt",
             "TRANSFER_TEST_README_20261015.txt"]
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(4*1024*1024),b""):h.update(b)
 return h.hexdigest().upper()
def check(p,parent):
 if p.is_symlink() or p.resolve().parent!=parent.resolve():raise RuntimeError("UNSAFE "+str(p))
 if not p.exists():raise RuntimeError("MISSING "+str(p))
def stats_dir(d):
 size=0;num=0
 for b,dirs,files in os.walk(d,followlinks=False):
  for n in dirs:
   if (Path(b)/n).is_symlink():raise RuntimeError("SYMLINK "+str(n))
  for n in files:
   f=Path(b)/n
   if f.is_symlink():raise RuntimeError("SYMLINK "+str(f))
   num+=1;size+=f.stat().st_size
 return num,size
assert latest.is_file() and sha(latest)==expected,"CURRENT_SETUP_CHECKSUM_FAIL"
assert (dist/"Storyboard_AI_Studio_Pro_Transfer_Test_20261015").is_dir()
assert (dist/"AutoSetup-TransferTest-Installer.iss").is_file()
assert (root/"Storyboard_AI_Studio.exe").is_file()
duplicate=root/"dist.zip"
zipbackup=dist/"Storyboard_AI_Studio_Pro_v1.0.zip"
assert duplicate.is_file() and sha(duplicate)==sha(zipbackup),"DUPLICATE_ZIP_MISMATCH"
actions=[];freed=0;archived=0
for name in old_archive:
 src=dist/name;check(src,dist)
 dest=archive/name
 assert not dest.exists(),"ARCHIVE_COLLISION "+str(dest)
 num=src.stat().st_size
 actions.append({"action":"archive","source":str(src),"destination":str(dest),
                 "bytes":num,"sha256":sha(src)})
 archived+=num
for name in old_delete:
 src=dist/name;check(src,dist);num=src.stat().st_size
 actions.append({"action":"delete_exe","source":str(src),"bytes":num,"sha256":sha(src)})
 freed+=num
for name in old_stage:
 src=dist/name;check(src,dist);assert src.is_dir()
 for sub in ("studio/productions","studio/scratch"):
  p=src/sub
  if p.exists() and any(p.rglob("*")):raise RuntimeError("USER_DATA_IN_OLD_STAGE "+str(p))
 assert not (src/"studio/.env").exists(),"SENSITIVE_SOURCE"
 count,sz=stats_dir(src)
 actions.append({"action":"delete_staging","source":str(src),"bytes":sz,"files":count})
 freed+=sz
actions.append({"action":"delete_duplicate_zip","source":str(duplicate),
                "bytes":duplicate.stat().st_size,"sha256":sha(duplicate)})
freed+=duplicate.stat().st_size
result={"time":datetime.datetime.now().isoformat(),"latest_sha256":expected,
        "actions":actions,"status":"PREPARED","completed":[],
        "estimated_freed_mb":round(freed/1048576,1),
        "estimated_archived_mb":round(archived/1048576,1)}
report.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
print("SAFE_PLAN",len(actions),"FREE_MB",round(freed/1048576,1),
      "ARCHIVE_MB",round(archived/1048576,1),flush=True)
if "--execute" in sys.argv:
 archive.mkdir(parents=True,exist_ok=True)
 for item in actions:
  p=Path(item["source"]);kind=item["action"]
  if kind=="archive":
   target=Path(item["destination"]);p.rename(target)
   assert sha(target)==item["sha256"],"ARCHIVE_CORRUPTED"
  elif kind=="delete_exe":
   check(p,dist);assert sha(p)==item["sha256"];p.unlink()
  elif kind=="delete_staging":
   check(p,dist);shutil.rmtree(p)
  elif kind=="delete_duplicate_zip":
   assert sha(p)==sha(archive/"Storyboard_AI_Studio_Pro_v1.0.zip")
   p.unlink()
  result["completed"].append(item["source"])
  result["status"]="IN_PROGRESS"
  report.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
  print(kind,p.name,flush=True)
 assert sha(latest)==expected
 assert (dist/"Storyboard_AI_Studio_Pro_Transfer_Test_20261015").is_dir()
 result["status"]="PASS"
 report.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
 print("CLEANUP_PASS",result["estimated_freed_mb"],"MB",flush=True)
