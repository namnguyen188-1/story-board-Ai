from pathlib import Path
import difflib,datetime
r=Path(r"D:\STORYBOARD_AI")
b=r/"tools"/"backups"/"continuity_20261026_142646"
s=r/"studio"
for sub in ["cinematic_engine/drama_orchestrator.py","cinematic_engine/drama_video_engine.py","muse_video_provider.py"]:
 orig=b/sub; now=s/sub
 print("\nFILE",sub,"BACKUP_EXISTS",orig.exists())
 if not orig.exists():continue
 a=orig.read_text(encoding="utf-8").splitlines()
 z=now.read_text(encoding="utf-8").splitlines()
 print("LINES",len(a),len(z),"MODIFIED",datetime.datetime.fromtimestamp(now.stat().st_mtime).isoformat())
 delta=list(difflib.unified_diff(a,z,fromfile="baseline",tofile="now",n=2))
 print("DIFF_LINES",len(delta))
 for line in delta[:250]:
  print(line[:230])
print("\nSKILL",list((s.parent/".agents"/"skills").glob("**/SKILL.md"))[:5])
