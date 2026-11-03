"""Reproducible Storyboard 1.3.12 FINAL CANDIDATE update ZIP from approved base 1.3.11.
Never modifies running installation or published GitHub latest.json.
"""
from pathlib import Path
import json,hashlib,zipfile,shutil,subprocess
root=Path("D:/STORYBOARD_AI");dist=root/"dist"
base=dist/"Storyboard_AI_Studio_Pro_v1.3.11.zip"
out=dist/"Storyboard_AI_Studio_Pro_v1.3.12_RC2.zip"
stage=dist/"_stage_multi_role_v1312_RC2"
seven=Path("C:/Program Files/7-Zip/7z.exe")
changes=[
"studio/cinematic_engine/drama_asset_first.py",
"studio/cinematic_engine/drama_aspect_repair.py",
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
"studio/drama_asset_review_api.py",
"studio/web_server.py",
"studio/web/drama_asset_review.js",
"studio/web/index.html",
"studio/tests/test_drama_asset_first_20261031.py",
"studio/tests/test_drama_six_scene_continuity_20261031.py",
".agents/skills/write-video-scene-prompts/references/MULTI_ROLE_ASSET_FIRST.md",
"studio/version.json",
]
assert base.is_file() and seven.is_file()
if out.exists():raise RuntimeError("FINAL_CANDIDATE_ALREADY_EXISTS_DO_NOT_OVERWRITE")
for path in changes:
 src=root/path;dst=stage/path
 if not src.is_file():raise FileNotFoundError(src)
 dst.parent.mkdir(parents=True,exist_ok=True)
 if path=="studio/version.json":
  data=json.loads(src.read_text(encoding="utf-8-sig"))
  data.update(version="1.3.12",release_date="2026-10-31")
  dst.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
 else:shutil.copy2(src,dst)
shutil.copy2(base,out)
cmd=[str(seven),"u","-tzip",str(out),*changes,"-y"]
r=subprocess.run(cmd,cwd=stage,capture_output=True,text=True,timeout=180)
if r.returncode:raise RuntimeError("ZIP_PATCH_FAILED: "+r.stderr[-600:]+r.stdout[-400:])
with zipfile.ZipFile(base) as old,zipfile.ZipFile(out) as new:
 assert new.testzip() is None
 a={i.filename:i for i in old.infolist() if not i.is_dir()}
 b={i.filename:i for i in new.infolist() if not i.is_dir()}
 assert len(b)==len([i for i in new.infolist() if not i.is_dir()]),"DUPLICATE_ENTRIES"
 assert not(set(a)-set(b)), "BASE_FILES_MISSING"
 for f in set(a)-set(changes):
  assert a[f].CRC==b[f].CRC and a[f].file_size==b[f].file_size, "BASE_CHANGED_"+f
 for f in changes:
  assert new.read(f)==(stage/f).read_bytes(), "OVERLAY_MISMATCH_"+f
 assert json.loads(new.read("studio/version.json"))["version"]=="1.3.12"
 assert new.read("Storyboard_AI_Studio.exe")==old.read("Storyboard_AI_Studio.exe")
 assert "studio/web/app.js" in b
 assert "studio/runtime/muse/python/python.exe" in b
 assert "studio/drama_asset_review_api.py" in b
 assert "studio/cinematic_engine/drama_aspect_repair.py" in b
 size=out.stat().st_size
 sha=hashlib.file_digest(out.open("rb"),"sha256").hexdigest().upper()
 report={"status":"RELEASE_CANDIDATE_TESTED_NOT_PUBLISHED",
         "version":"1.3.12","file":str(out),"bytes":size,"sha256":sha,
         "files_in_package":len(b),"changed_files":changes,
         "base_release":"v1.3.11","retains_original_launcher_exe":True,
         "retains_original_published_latest_json":True,
         "6_real_video_scene_e2e":"ASSEMBLED_TECHNICALLY",
         "moving_scene_visual_qc":"MANUAL_REVIEW_REQUIRED",
         "aspect_adapted_scenes":[3,4,6],
         "github_published":False,
         "secondary_PC_updated":False}
 (dist/"Storyboard_1_3_12_RC2_report.json").write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
 print("STORYBOARD_V1312_RC_PACKAGING_PASS",json.dumps({"file":str(out),"bytes":size,
 "sha256":sha,"files":len(b),"overlay":len(changes)},ensure_ascii=False),flush=True)
