"""Create an un-published, reversible v1.3.12 update ZIP from verified 1.3.11.
Same launcher, same UI and dependencies; overlays only audited drama changes.
DO NOT publish or update installed application before full E2E pass.
"""
from pathlib import Path
import shutil,json,subprocess,zipfile,hashlib,sys
ROOT=Path(r"D:\STORYBOARD_AI")
STUDIO=ROOT/"studio"
DIST=ROOT/"dist"
BASE=DIST/"Storyboard_AI_Studio_Pro_v1.3.11.zip"
OUT=DIST/"Storyboard_AI_Studio_Pro_v1.3.12_CANDIDATE.zip"
STAGE=DIST/"_stage_multi_role_v1312"
SEVEN=Path(r"C:\Program Files\7-Zip\7z.exe")
assert BASE.is_file() and SEVEN.is_file()
assert not OUT.exists(),"Candidate already staged; do not overwrite without audit"
changes=[
"studio/cinematic_engine/drama_asset_first.py",
"studio/cinematic_engine/drama_asset_manager.py",
"studio/cinematic_engine/drama_orchestrator.py",
"studio/cinematic_engine/drama_video_engine.py",
"studio/cinematic_engine/drama_skill9.py",
"studio/cinematic_engine/drama_schema.py",
"studio/cinematic_engine/drama_planner.py",
"studio/cinematic_engine/drama_voice_director.py",
"studio/muse_asset_images.py",
"studio/muse_scene_image.py",
"studio/drama_preproduction_worker.py",
"studio/muse_video_provider.py",
"studio/muse_gateway_worker.py",
"studio/comfyui_image_provider.py",
"studio/comfyui_identity_refs.py",
"studio/tests/test_drama_asset_first_20261031.py",
".agents/skills/write-video-scene-prompts/references/MULTI_ROLE_ASSET_FIRST.md",
"studio/version.json",
]
for p in changes:
 src=ROOT/p; dst=STAGE/p
 if p=="studio/version.json":
  data=json.loads(src.read_text(encoding="utf-8-sig"))
  data.update(version="1.3.12",release_date="2026-10-31")
  dst.parent.mkdir(parents=True,exist_ok=True)
  dst.write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding="utf-8")
 else:
  if not src.is_file():raise FileNotFoundError(src)
  dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
print("UPDATER_PREPARED",len(changes),flush=True)
shutil.copyfile(BASE,OUT)
r=subprocess.run([str(SEVEN),"u","-tzip",str(OUT),*changes,"-y"],cwd=STAGE,
                 capture_output=True,text=True,timeout=300)
if r.returncode:raise RuntimeError("7ZIP_UPDATE_FAILED "+r.stderr[-1000:]+r.stdout[-900:])
with zipfile.ZipFile(BASE) as orig,zipfile.ZipFile(OUT) as cand:
 assert cand.testzip() is None
 old={e.filename:e for e in orig.infolist() if not e.is_dir()}
 new={e.filename:e for e in cand.infolist() if not e.is_dir()}
 assert len(new)==len([x for x in cand.infolist() if not x.is_dir()]),"Duplicate ZIP entries"
 assert not(set(old)-set(new)),"Missing baseline files"
 for path in set(old)-set(changes):
  assert (old[path].CRC,old[path].file_size)==(new[path].CRC,new[path].file_size),path
 for path in changes:
  assert cand.read(path)==(STAGE/path).read_bytes(),path
 assert json.loads(cand.read("studio/version.json"))["version"]=="1.3.12"
 # "Brand new EXE" not promised; launcher remains byte-identical.
 assert cand.read("Storyboard_AI_Studio.exe")==orig.read("Storyboard_AI_Studio.exe")
 assert "studio/runtime/muse/python/python.exe" in new
 assert "studio/web/app.js" in new and "studio/web/index.html" in new
 assert ".agents/skills/write-video-scene-prompts/SKILL.md" in new
 report={"status":"CANDIDATE_STAGED_NOT_PUBLISHED","version":"1.3.12",
          "file":str(OUT),"bytes":OUT.stat().st_size,
          "sha256":hashlib.file_digest(OUT.open("rb"),"sha256").hexdigest().upper(),
          "files":len(new),"overlay_files":changes,
          "base_version":"1.3.11","preserved_existing_exe":True,
          "requires_live_six_scene_e2e_and_regressions":True}
 p=DIST/"multi_role_v1312_candidate_report.json"
 p.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
 print("PACKAGING_CANDIDATE_COMPLETE",json.dumps({"file":str(OUT),"bytes":report["bytes"],
 "sha256":report["sha256"],"files":len(new),"updated":len(changes)},ensure_ascii=False),flush=True)
