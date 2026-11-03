from pathlib import Path
import shutil, hashlib, json, datetime
root=Path(r"D:\STORYBOARD_AI\studio")
files=["cinematic_engine/drama_asset_manager.py","cinematic_engine/drama_orchestrator.py","cinematic_engine/drama_video_engine.py","cinematic_engine/drama_skill9.py","cinematic_engine/drama_schema.py","cinematic_engine/drama_planner.py","muse_video_provider.py","muse_gateway_worker.py","comfyui_image_provider.py","comfyui_identity_refs.py","web/app.js","web/index.html","web_server.py"]
base=Path(r"D:\STORYBOARD_AI\tools\backups\multi_role_asset_first_20261031")
base.mkdir(parents=True,exist_ok=True)
manifest={}
for s in files:
 p=root/s; dst=base/s;dst.parent.mkdir(parents=True,exist_ok=True)
 if p.is_file():
  shutil.copy2(p,dst)
  manifest[s]={"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"bytes":p.stat().st_size}
src=Path(r"D:\STORYBOARD_AI\.agents\skills\write-video-scene-prompts\SKILL.md")
dst=base/"skill"/"SKILL.md";dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
manifest["skill/SKILL.md"]={"sha256":hashlib.sha256(src.read_bytes()).hexdigest()}
(base/"MANIFEST.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
print("BACKUP_PASS",str(base),"FILES",len(manifest))
