from pathlib import Path
import subprocess,hashlib,json,os
root=Path(r"D:\STORYBOARD_AI\studio");p=root/"studio_mcp/image_backend.py"
cp=root/"runtime/single_lane_safe_20261108_180134"
backup=cp/"studio_mcp/image_backend.py";backup.parent.mkdir(parents=True,exist_ok=True)
before=p.read_bytes()
if backup.exists():
 if backup.read_bytes()!=before:raise RuntimeError("BACKUP_MISMATCH")
else:backup.write_bytes(before)
s=before.decode("utf8")
try:
 begin=s.index('                if old.get("fingerprint") != fp:')
 end=s.index('            entries.append((sid, fp, job, old))',begin)
 replacement='''                if old.get("fingerprint") != fp:
                    # An unresolved Google submission must not be overwritten.
                    if old.get("state") != "completed":
                        raise StoryboardImageError("STORYBOARD_IMAGE_UNCERTAIN_INPUT_CHANGE_NO_RESUBMIT")
                    self._journal(sid).unlink(missing_ok=True)
                    old = None
                elif old.get("state") == "completed":
                    results[sid] = self._verify(old.get("receipt"), job)
'''
 s=s[:begin]+replacement+s[end:]
 begin=s.index('            if unresolved:',s.index('        uncertain = ['))
 end=s.index('        new = [',begin)
 replacement='''            if unresolved:
                # Preserve the original journals and reserved slots. No automatic resubmit.
                raise StoryboardImageError("STORYBOARD_IMAGE_UNCERTAIN_NO_RESUBMIT")

'''
 s=s[:begin]+replacement+s[end:]
 tmp=p.with_suffix(".py.single-lane-tmp");tmp.write_bytes(s.encode("utf8"));os.replace(tmp,p)
 for name in ("test_single_lane_no_resubmit_20261108.py","test_flowkit_removed_offline.py"):
  cmd=[str(root/"runtime/python/python.exe"),"-B","-X","utf8",str(root/"tests"/name)]
  r=subprocess.run(cmd,cwd=root,capture_output=True,text=True,encoding="utf8",errors="replace",timeout=55)
  print(name,"exit",r.returncode,(r.stdout+r.stderr)[-3300:])
  if r.returncode:raise RuntimeError("REGRESSION_FAILED_"+name)
 report={"result":"NO_AUTO_RESUBMIT_GUARD_PASS","path":str(p),"backup":str(backup),
 "before_sha256":hashlib.sha256(before).hexdigest(),"after_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),
 "tests":["test_single_lane_no_resubmit_20261108.py","test_flowkit_removed_offline.py"],"generation_submitted":False}
 (cp/"no_auto_resubmit_report.json").write_text(json.dumps(report,indent=2),encoding="utf8")
 print(json.dumps(report,ensure_ascii=True))
except Exception as e:
 p.write_bytes(before);print("ROLLBACK",str(e));raise
