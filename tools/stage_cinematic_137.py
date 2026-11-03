from pathlib import Path
import shutil,json,subprocess,sys
root=Path(r"D:\STORYBOARD_AI");dist=root/"dist"
for p in (root/"AGENTS.md",root/"studio/AGENTS.md",root/"studio/cinematic_engine/AGENTS.md"):
 if p.is_file(): print("AGENTS_INSTRUCTIONS",p,p.read_text(encoding="utf-8-sig"));raise SystemExit("Review instructions before staging")
target=dist/"Storyboard_AI_Studio_Pro_v1.3.7"
shutil.copytree(dist/"Storyboard_AI_Studio_Pro_v1.3.6",target,ignore=shutil.ignore_patterns("__pycache__","*.pyc"))
source=root/"studio/cinematic_engine"
shutil.copytree(source,target/"studio/cinematic_engine",ignore=shutil.ignore_patterns("__pycache__","*.pyc","*.bak","test_*","run_e2e_*",".env"))
repair=dist/"Cinematic_Core_Repair_v1.3.7"
shutil.copytree(target/"studio/cinematic_engine",repair/"studio/cinematic_engine")
version=json.loads((root/"studio/version.json").read_text(encoding="utf-8-sig"));version["version"]="1.3.7"
for folder in (target,repair):
 (folder/"studio/version.json").write_text(json.dumps(version,indent=2),encoding="utf-8")
zip_path=dist/"Storyboard_AI_Studio_Pro_v1.3.7.zip"
shutil.copy2(dist/"Storyboard_AI_Studio_Pro_v1.3.6.zip",zip_path)
subprocess.run([r"C:\Program Files\7-Zip\7z.exe","a","-tzip",str(zip_path),"studio/cinematic_engine","studio/version.json"],cwd=target,check=True,capture_output=True)
subprocess.run([r"C:\Program Files\7-Zip\7z.exe","a","-tzip",str(repair)+".zip","studio"],cwd=repair,check=True,capture_output=True)
print("STAGED_FULL_AND_COMPONENT",flush=True)
