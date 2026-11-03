"""Portable, read-only GPU capability detection for Storyboard AI.
No GPU/driver installation and no automatic paid-provider switching.
"""
from __future__ import annotations
import csv, io, json, os, subprocess, shutil
from functools import lru_cache

CREATE_NO_WINDOW=getattr(subprocess,"CREATE_NO_WINDOW",0)

def _run(command:list[str],timeout=4):
    try:
        p=subprocess.run(command,capture_output=True,text=True,timeout=timeout,
                         creationflags=CREATE_NO_WINDOW,errors="replace")
        return p.stdout.strip() if p.returncode==0 else ""
    except (OSError,subprocess.TimeoutExpired):
        return ""

def classify(vendor:str,vram_mb:int|None=None)->dict:
    name=(vendor or "").lower()
    if any(k in name for k in ("nvidia","geforce","quadro","tesla","rtx","gtx")):
        kind="nvidia"
    elif any(k in name for k in ("amd","radeon","advanced micro","rx 6","rx 7","rx 9")):
        kind="amd"
    elif any(k in name for k in ("intel","arc graphics","uhd graphics","iris")):
        kind="intel"
    elif name.strip():
        kind="unknown"
    else: kind="none"
    mem=max(0,int(vram_mb or 0))
    if kind=="nvidia":
        mode="cuda" if mem>=6000 else ("cuda_lowvram" if mem>=3500 else "verify_cuda")
        suggestion="local_optional"
        reason=("NVIDIA CUDA can be used with a compatible PyTorch/ComfyUI setup. "
                "Runtime and model loading must be verified before production.")
    elif kind in ("amd","intel"):
        mode="external_comfy_optional"
        suggestion="cloud_or_verified_external"
        reason=("AMD/Intel local rendering needs a matching supported backend; "
                "never install NVIDIA CUDA wheels for this GPU.")
    else:
        mode="cloud"
        suggestion="cloud"
        reason="Use configured Google Flow MCP or API; no compatible local render backend is confirmed."
    return {"vendor":kind,"vram_mb":mem if mem else None,
            "local_mode":mode,"recommendation":suggestion,"reason":reason}

def _normalize(raw):
    if not raw:return []
    if isinstance(raw,dict):raw=[raw]
    result=[]
    for item in raw:
        if not isinstance(item,dict):continue
        name=str(item.get("Name") or item.get("name") or "").strip()
        if not name:continue
        rawmem=item.get("AdapterRAM",0)
        try:vram=int(rawmem)//(1024*1024)
        except (ValueError,TypeError):vram=0
        # Windows AdapterRAM is 32-bit, unreliable for modern 4GB+ GPUs.
        if vram>=4000:vram=0
        entry={"name":name,**classify(name,vram)}
        result.append(entry)
    return result

def detect_from_outputs(nvidia_smi:str="",windows_json:str="")->dict:
    gpus=[]
    if windows_json:
        try:gpus=_normalize(json.loads(windows_json))
        except (TypeError,ValueError):pass
    if nvidia_smi:
        for row in csv.reader(io.StringIO(nvidia_smi)):
            if len(row)<2:continue
            name=row[0].strip()
            try:mem=int(float(row[1].strip().split()[0]))
            except (ValueError,TypeError,IndexError):mem=0
            if not name:continue
            entry={"name":name,**classify("NVIDIA "+name,mem)}
            match=next((x for x in gpus if x["vendor"]=="nvidia"),None)
            if match:match.update(entry)
            else:gpus.insert(0,entry)
    # Prefer a NVIDIA CUDA candidate; others need a verified external backend.
    order={"nvidia":0,"amd":1,"intel":2,"unknown":3,"none":4}
    gpus.sort(key=lambda x:(order.get(x["vendor"],4),-(x["vram_mb"] or 0)))
    selected=gpus[0] if gpus else {"name":"Không phát hiện","vendor":"none",**classify("",0)}
    return {"gpus":gpus,"primary":selected,"local_gpu_candidate":selected["vendor"]=="nvidia",
            "requires_local_setup":True,
            "cloud_available_by_gpu":True,
            "note":"This hardware report alone does not prove local ComfyUI compatibility."}

def _detect_from_registry():
    gpus = []
    if os.name != "nt":
        return gpus
    try:
        import winreg
        guid_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}")
        for i in range(25):
            try:
                subkey_name = winreg.EnumKey(guid_key, i)
                if subkey_name.isdigit():
                    sk = winreg.OpenKey(guid_key, subkey_name)
                    desc, _ = winreg.QueryValueEx(sk, "DriverDesc")
                    desc = (desc or "").strip()
                    if desc and not any(k in desc.lower() for k in ("basic render", "remote display", "vnc", "citrix", "virtual")):
                        gpus.append({"Name": desc, "AdapterRAM": 0})
            except OSError:
                break
    except Exception:
        pass
    return gpus

@lru_cache(maxsize=1)
def detect_gpu()->dict:
    nv=""
    smi=shutil.which("nvidia-smi")
    if not smi and os.name == "nt":
        candidates = [
            os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), r"System32\nvidia-smi.exe"),
            os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), r"NVIDIA Corporation\NVSMI\nvidia-smi.exe"),
        ]
        for c in candidates:
            if os.path.isfile(c):
                smi = c
                break
    if smi:nv=_run([smi,"--query-gpu=name,memory.total","--format=csv,noheader,nounits"],3)
    win=""
    if os.name=="nt":
        ps=shutil.which("powershell") or shutil.which("pwsh")
        if ps:
            win=_run([ps,"-NoProfile","-NonInteractive","-Command",
                "Get-CimInstance Win32_VideoController | Select-Object Name,AdapterRAM | ConvertTo-Json -Compress"],6)
        if not win:
            reg_gpus = _detect_from_registry()
            if reg_gpus:
                win = json.dumps(reg_gpus)
    return detect_from_outputs(nv,win)

def simplify_gpu_name(raw: str) -> str:
    import re
    s = (raw or "").strip()
    m = re.search(r'(RTX\s+[0-9]{4}(?:\s*Ti|\s*Super)?)', s, re.I)
    if m: return m.group(1).strip()
    m = re.search(r'(GTX\s+[0-9]{3,4}(?:\s*Ti|\s*Super)?)', s, re.I)
    if m: return m.group(1).strip()
    m = re.search(r'(RX\s+[0-9]{4}(?:\s*XT)?)', s, re.I)
    if m: return m.group(1).strip()
    m = re.search(r'(Arc\s+[A-Z0-9]+)', s, re.I)
    if m: return m.group(1).strip()
    clean = re.sub(r'NVIDIA|GeForce|AMD|Radeon|Graphics|Laptop GPU|\(R\)|\(TM\)', '', s).strip()
    return clean[:18].strip() or "GPU AI"

def simplify_cpu_name(raw: str) -> str:
    import re
    s = (raw or "").strip()
    m = re.search(r'(Xeon(?:\(R\))?\s+(?:CPU\s+)?[A-Z0-9\-]+)', s, re.I)
    if m:
        cleaned = re.sub(r'\(R\)|\bCPU\b', ' ', m.group(1))
        return re.sub(r'\s+', ' ', cleaned).strip()
    m = re.search(r'(Core(?:\(TM\))?\s+i[3579](?:-[A-Z0-9]+)?)', s, re.I)
    if m:
        cleaned = re.sub(r'\(TM\)', ' ', m.group(1))
        return re.sub(r'\s+', ' ', cleaned).strip()
    m = re.search(r'(Ryzen\s+[3579](?:\s+[A-Z0-9]+)?)', s, re.I)
    if m: return m.group(1).strip()
    clean = re.sub(r'\(R\)|\(TM\)|Processor|@.*$|CPU', ' ', s)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean[:18].strip() or "CPU"

def detect_cpu() -> dict:
    import platform
    cpu_name = ""
    if os.name == "nt":
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
            cpu_name = winreg.QueryValueEx(key, "ProcessorNameString")[0].strip()
        except Exception:
            pass
    if not cpu_name:
        cpu_name = platform.processor() or platform.machine() or "CPU"
    threads = os.cpu_count() or 4
    return {
        "name": cpu_name,
        "short": simplify_cpu_name(cpu_name),
        "threads": threads
    }

def get_hardware_specs() -> dict:
    cpu_info = detect_cpu()
    gpu_data = detect_gpu()
    gpu_primary = gpu_data.get("primary", {})
    gpu_short = simplify_gpu_name(gpu_primary.get("name", ""))
    threads = cpu_info.get("threads", os.cpu_count() or 4)
    return {
        "cpu": cpu_info,
        "cpu_name": cpu_info.get("name", "CPU"),
        "cpu_short": cpu_info.get("short", "CPU"),
        "cpu_threads": threads,
        "gpu": gpu_primary,
        "gpu_name": gpu_primary.get("name", "GPU Tăng Tốc"),
        "gpu_short": gpu_short,
        "summary": f"{cpu_info.get('short', 'CPU')} ({threads} Luồng) + {gpu_short}"
    }

if __name__=="__main__":
    print(json.dumps(get_hardware_specs(),ensure_ascii=False,indent=2))
