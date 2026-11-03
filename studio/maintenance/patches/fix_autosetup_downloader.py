from pathlib import Path
import ast
p=Path(r"D:\STORYBOARD_AI\dist\Storyboard_AI_Studio_Pro_Transfer_Test_20261015\studio\customer_bootstrap.py")
s=p.read_text(encoding="utf-8")
def patch(a,b):
 global s
 assert s.count(a)==1,(s.count(a),a[:60])
 s=s.replace(a,b,1)
patch('''ASSET_NAMES={"nvidia":"ComfyUI_windows_portable_nvidia.7z",
             "amd":"ComfyUI_windows_portable_amd.7z",
             "intel":"ComfyUI_windows_portable_intel.7z"}''',
'''ASSET_NAMES={"nvidia":"ComfyUI_windows_portable_nvidia.7z",
             "nvidia_legacy":"ComfyUI_windows_portable_nvidia_cu126.7z",
             "amd":"ComfyUI_windows_portable_amd.7z",
             "intel":"ComfyUI_windows_portable_intel.7z"}
def gpu_variant(local):
    name=str(local.get("gpu") or "").upper()
    if local.get("vendor")=="nvidia" and ("GTX" in name or "GT " in name):
        return "nvidia_legacy"
    return local.get("vendor")''')
patch('''        with urllib.request.urlopen(req,timeout=90) as response:
            if start and response.status!=206:
                tmp.unlink(missing_ok=True);start=0
            written=start
            with tmp.open("ab" if start else "wb") as out:
                next_report=written+64*1024*1024
                while True:
                    data=response.read(1024*1024)
                    if not data:break
                    written+=len(data)
                    if written>size:raise RuntimeError("DOWNLOAD_EXCEEDS_VERIFIED_SIZE")
                    out.write(data)
                    if written>=next_report:
                        event("PROGRESS",f"Downloaded {written//(1024**2)}/{size//(1024**2)} MiB")
                        next_report+=64*1024*1024
''',
'''        try:
            with urllib.request.urlopen(req,timeout=90) as response:
                if start and response.status!=206:
                    tmp.unlink(missing_ok=True);start=0
                written=start
                with tmp.open("ab" if start else "wb") as out:
                    next_report=written+64*1024*1024
                    while True:
                        data=response.read(1024*1024)
                        if not data:break
                        written+=len(data)
                        if written>size:raise RuntimeError("DOWNLOAD_EXCEEDS_VERIFIED_SIZE")
                        out.write(data)
                        if written>=next_report:
                            event("PROGRESS",f"Downloaded {written//(1024**2)}/{size//(1024**2)} MiB")
                            next_report+=64*1024*1024
        except OSError as exc:
            event("STEP",f"Connection interrupted; retry {attempt+1}/3: {type(exc).__name__}")
            time.sleep(2)
            continue
''')
start=s.index('    if local["vendor"] not in ASSET_NAMES:',s.index("def install_local():"))
end=s.index('    event("STEP","Reading verified SDXL model metadata")',start)
replace='''    variant=gpu_variant(local)
    if variant not in ASSET_NAMES:
        raise RuntimeError("GPU_NOT_SUPPORTED_FOR_AUTOINSTALL")
    if local["vendor"]=="nvidia" and (local.get("vram_mb") or 0) and local["vram_mb"]<3500:
        raise RuntimeError("GPU_VRAM_TOO_LOW_FOR_AUTOMATED_SDXL")
    root=HERE/"runtime"/"comfyui"
    disk=shutil.disk_usage(root.parent)
    if disk.free<22*1024**3:
        raise RuntimeError("NEED_AT_LEAST_22_GB_FREE_FOR_GPU_RUNTIME_AND_MODEL")
    stable=root/"portable"
    marker_file=stable/".storyboard_gpu_install.json"
    reuse=False
    if (stable/"ComfyUI"/"main.py").is_file() and (stable/"python_embeded"/"python.exe").is_file():
        try:marker=json.loads(marker_file.read_text(encoding="utf-8"))
        except (OSError,ValueError):marker={}
        if marker.get("vendor")!=local["vendor"]:
            raise RuntimeError("EXISTING_GPU_PORTABLE_BACKEND_UNVERIFIED")
        reuse=True
        event("STEP","Existing verified ComfyUI runtime found; resuming model setup")
    elif stable.exists():
        raise RuntimeError("GPU_PORTABLE_INSTALL_INCOMPLETE_REVIEW")
    if not reuse:
        event("STEP","Checking official ComfyUI release for "+variant)
        asset=release_asset(fetch_json(API_URL),variant)
        cache=HERE/"runtime"/"download_cache"
        archive=cache/ASSET_NAMES[variant]
        event("STEP","Downloading official verified GPU runtime "+str(asset["version"]))
        download_checked(asset["url"],archive,asset["bytes"],asset["digest"])
        incoming=root.parent/("comfyui_install_pending")
        marker=incoming/".storyboard_owned_partial_install"
        if incoming.exists():
            if not marker.is_file():
                raise RuntimeError("PREVIOUS_GPU_INSTALL_UNVERIFIED")
            shutil.rmtree(incoming)
        incoming.mkdir(parents=True)
        marker.write_text("StoryboardAI customer setup",encoding="utf-8")
        event("STEP","Extracting and validating ComfyUI portable runtime")
        extract_checked(archive,incoming)
        folders=list(incoming.rglob("ComfyUI/main.py"))
        match=next((p.parent for p in folders if (p.parent.parent/"python_embeded"/"python.exe").is_file()),None)
        if match is None:raise RuntimeError("GPU_PORTABLE_RUNTIME_LAYOUT_INVALID")
        root.mkdir(parents=True,exist_ok=True)
        match.parent.rename(stable)
        (stable/".storyboard_gpu_install.json").write_text(json.dumps({
            "vendor":local["vendor"],"asset_sha256":asset["digest"],
            "release":asset["version"]},ensure_ascii=False,indent=2),encoding="utf-8")
        shutil.rmtree(incoming,ignore_errors=True)
'''
s=s[:start]+replace+s[end:]
patch('row.get("lfs",{}).get("sha256")!=MODEL_SHA','row.get("lfs",{}).get("oid")!=MODEL_SHA')
ast.parse(s,filename=str(p))
p.write_text(s,encoding="utf-8")
print("AUTOSETUP_PATCHED",len(s.splitlines()))
