from pathlib import Path
import shutil,json
root=Path(r"D:\STORYBOARD_AI")
p=root/"make_secure_release.py";s=p.read_text(encoding="utf-8-sig")
shutil.copy2(p,root/"backups/make_secure_release-before-muse.py")
s=s.replace('VERSION = "1.3.5"','VERSION = "1.3.6"')
extra='''
def copy_muse_runtime():
    source = STUDIO_DIR / "runtime" / "muse"
    target = TARGET_DIR / "studio" / "runtime" / "muse"
    for required in ("python/python.exe", "python/python312.dll", "agent-browser.exe"):
        if not (source / required).is_file():
            raise RuntimeError("Missing Muse runtime: " + required)
    target.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source / "python", target / "python",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copy2(source / "agent-browser.exe", target / "agent-browser.exe")
    for license_file in source.glob("agent-browser-LICENSE*"):
        shutil.copy2(license_file, target / license_file.name)
    log_ok("Bundled isolated Muse runtime and login helper; no account profiles.")

'''
s=s.replace("def sanitize_and_inject_clean_templates():",extra+"def sanitize_and_inject_clean_templates():")
s=s.replace("        copy_core_studio()\n","        copy_core_studio()\n        copy_muse_runtime()\n")
s=s.replace('"One-click updates without hidden Windows confirmation dialogs.",','"Include the isolated Muse core and login helper on every updated PC.",')
s=s.replace('"Show download and installation progress in the update button.",','"Resolve Muse runtime paths independently of the developer computer.",')
s=s.replace('"Prevent duplicate updates and preserve local accounts and projects."','"Preserve the existing interface, local accounts and projects."')
p.write_text(s,encoding="utf-8")
# Separate repair asset avoids downloading unchanged media engine on the existing Korean install.
repair=root/"dist/Muse_Runtime_Repair_v1.3.6"
(repair/"studio").mkdir(parents=True,exist_ok=False)
for name in ("muse_video_provider.py","muse_login.py"):
 shutil.copy2(root/"studio"/name,repair/"studio"/name)
shutil.copytree(root/"studio/runtime/muse",repair/"studio/runtime/muse",
 ignore=shutil.ignore_patterns("__pycache__","*.pyc"))
print("RELEASE_AND_REPAIR_STAGED",flush=True)
