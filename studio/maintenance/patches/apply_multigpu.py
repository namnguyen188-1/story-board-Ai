from pathlib import Path
import ast
root=Path(r"D:\STORYBOARD_AI")
def edit(rel,old,new,check=True):
 p=root/rel;t=p.read_text(encoding="utf-8")
 n=t.count(old)
 if n!=1:raise RuntimeError("Replace count {} for {} {}".format(n,rel,old[:70]))
 z=t.replace(old,new,1)
 if check and p.suffix==".py":ast.parse(z)
 p.write_text(z,encoding="utf-8")
 print("PATCH",rel,old.splitlines()[0][:70])
 return z
p="studio/comfyui_image_provider.py"
edit(p,'COMFYUI_DIR = Path(r"D:\\ComfyUI")',"""STUDIO_DIR = Path(__file__).resolve().parent
def discover_comfy_dir() -> Path:
    configured = os.environ.get("STORYBOARD_COMFYUI_DIR", "").strip()
    candidates = ([Path(configured).expanduser()] if configured else []) + [
        STUDIO_DIR / "runtime" / "comfyui",
        STUDIO_DIR.parent / "ComfyUI",
        Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Programs" / "ComfyUI",
        Path(r"D:\\ComfyUI"),
    ]
    for candidate in candidates:
        if (candidate / "main.py").is_file():
            return candidate
    return candidates[0]

COMFYUI_DIR = discover_comfy_dir()""")
edit(p,'PID_FILE = Path(r"D:\\STORYBOARD_AI\\studio\\scratch\\comfyui.pid")',
     'PID_FILE = STUDIO_DIR / "scratch" / "comfyui.pid"')
edit(p,'def is_ready(host: str = COMFYUI_HOST, timeout: float = 0.4) -> bool:',
"""def compatibility_status(host: str = COMFYUI_HOST) -> dict:
    from gpu_capabilities import detect_gpu
    hardware = detect_gpu()
    server = is_ready(host, timeout=0.25)
    installed = is_installed()
    gpu = hardware["primary"]
    if server:
        status = "ready_server"
        reason = "ComfyUI server responding; verify the active checkpoint."
    elif installed and gpu["vendor"]=="nvidia":
        status = "local_nvidia"
        reason = "Verify installed CUDA PyTorch and ComfyUI model."
    elif installed:
        status = "backend_not_verified"
        reason = "Install a matching AMD/Intel backend or use cloud options."
    else:
        status = "not_installed"
        reason = "ComfyUI not installed; MCP or configured API may be used."
    return {"state":status,"reason":reason,"can_attempt_local":status in ("ready_server","local_nvidia"),
            "server_ready":server,"installed":installed,"host":host,
            "comfyui_dir":str(COMFYUI_DIR),"gpu":gpu}

def is_ready(host: str = COMFYUI_HOST, timeout: float = 0.4) -> bool:""")
edit(p,'    if not is_installed():\n        return False\n\n    # Launch ComfyUI completely',
'''    if not is_installed():
        return False
    if not compatibility_status(host)["can_attempt_local"]:
        print("[ComfyUI] GPU backend unverified; select configured MCP/API or a supported ComfyUI server.", flush=True)
        return False

    # Launch ComfyUI completely''')
edit(p,'GPU RTX 3060 Ti...', 'GPU tương thích...')
edit(p,'Tự động bật ComfyUI trên GPU RTX 3060 Ti để tạo ảnh',
       'Tự động bật ComfyUI với GPU đã xác minh để tạo ảnh')
t=(root/p).read_text(encoding="utf-8")
a=t.index('    # 3. Kill any remaining listener process on port 8188')
b=t.index('    # 4. Wait for confirmation that port 8188 is down',a)
t=t[:a]+'    # Never stop arbitrary processes on port 8188: only recorded owned PIDs.\n'+t[b:]
ast.parse(t);(root/p).write_text(t,encoding="utf-8")
print("PATCH",p,"remove unconditional port kill")
edit("studio/web_server.py",'"comfyui_ready": comfyui_ready,',
''' "comfyui_ready": comfyui_ready,
                "gpu": __import__("gpu_capabilities").detect_gpu()["primary"],
                "comfy_compatibility": __import__("comfyui_image_provider").compatibility_status(),''')
edit("studio/web_server.py",'        elif path == "/api/comfyui/status":',
'''        elif path == "/api/gpu/status":
            from gpu_capabilities import detect_gpu
            from comfyui_image_provider import compatibility_status
            return self.end_json({"ok":True,"hardware":detect_gpu(),"comfyui":compatibility_status()})

        elif path == "/api/comfyui/status":''')
edit("studio/web_server.py",
'''                    from comfyui_image_provider import is_installed as comfy_installed
                    if not comfy_installed():
                        return self.end_json({
                            "code": "COMFYUI_NOT_INSTALLED",
                            "error": "Không tìm thấy ComfyUI tại D:\\\\ComfyUI. Vui lòng kiểm tra cài đặt.",
                        }, 503)''',
'''                    from comfyui_image_provider import compatibility_status
                    compat = compatibility_status()
                    if not compat["can_attempt_local"]:
                        return self.end_json({
                            "code": "COMFYUI_BACKEND_UNAVAILABLE",
                            "error": "ComfyUI GPU chưa được xác minh. Hãy dùng MCP/API đã cấu hình hoặc cài backend tương thích.",
                            "compatibility": compat,
                            "production_started": False,
                        }, 503)''')
edit("studio/web/index.html",
     '⚡ GPU Render Tự Động (Tối ưu RTX 3060 Ti / SDXL)',
     '⚡ GPU Render Nội Bộ (Tự kiểm tra GPU / ComfyUI)')
edit("studio/web/index.html",'          <!-- MCP / VEO 3 OPTIONS BOX -->',
'''          <p id="gpuCompatibilityStatus" role="status" style="margin:6px 0 8px;color:#94a3b8;font-size:.73rem;line-height:1.5;">
            Đang kiểm tra GPU và ComfyUI...
          </p>
          <!-- MCP / VEO 3 OPTIONS BOX -->''')
edit("studio/web/app.js",'    const elComfy = document.getElementById("statusComfyUI");',
'''    const gpuNode = document.getElementById("gpuCompatibilityStatus");
    if (gpuNode) {
      const gpu = data.gpu || {};
      const co = data.comfy_compatibility || {};
      const label = gpu.name ? gpu.name + (gpu.vram_mb ? " (" + gpu.vram_mb + " MB VRAM)" : "") : "Chưa nhận diện GPU";
      const captions = {
        ready_server: "ComfyUI đang chạy; cần xác minh model",
        local_nvidia: "NVIDIA CUDA: cần kiểm thử backend và VRAM",
        backend_not_verified: "Chưa xác minh backend GPU; hãy dùng MCP/API đã cấu hình",
        not_installed: "Chưa cài ComfyUI; có thể dùng MCP/API đã cấu hình"
      };
      gpuNode.textContent = "GPU: " + label + " • " + (captions[co.state] || "Chưa xác nhận tương thích");
    }
    const elComfy = document.getElementById("statusComfyUI");''',False)
edit("package_distribution.py",'    "comfyui_image_provider.py",',
     '    "comfyui_image_provider.py",\n    "gpu_capabilities.py",')
edit("package_distribution.py",'    "studio_mcp",\n    "runtime",',
     '    "studio_mcp",')
edit("package_distribution.py",'    # 3. Create empty clean productions and scratch folders',
'''    # Include only interpreter bytes, never private accounts, profiles, logs,
    # production receipts or other developer runtime data.
    runtime_python = STUDIO_DIR / "runtime" / "python"
    if runtime_python.is_dir():
        shutil.copytree(runtime_python, studio_target / "runtime" / "python",
                        dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.log", "*.jsonl", ".env"))
        print("  + Clean portable Python runtime (no developer profiles)")

    # 3. Create empty clean productions and scratch folders''')
print("MULTIGPU_SOURCE_PATCH_COMPLETE")
