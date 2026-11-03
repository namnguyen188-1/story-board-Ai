from pathlib import Path
import ast
p=Path(r"D:\STORYBOARD_AI\dist\Storyboard_AI_Studio_Pro_Transfer_Test_20261015\studio\comfyui_image_provider.py")
s=p.read_text(encoding="utf-8")
def patch(a,b):
 global s
 n=s.count(a)
 if n!=1:raise RuntimeError("Expected exactly one fragment, found %s: %r"%(n,a[:60]))
 s=s.replace(a,b,1)
patch('        STUDIO_DIR / "runtime" / "comfyui",',
      '        STUDIO_DIR / "runtime" / "comfyui" / "portable" / "ComfyUI",\n        STUDIO_DIR / "runtime" / "comfyui",')
patch('COMFYUI_VENV_PYTHON = COMFYUI_VENV_PYTHONW if COMFYUI_VENV_PYTHONW.is_file() else (COMFYUI_DIR / ".venv" / "Scripts" / "python.exe")',
'''_PORTABLE_PYTHON = COMFYUI_DIR.parent / "python_embeded" / "python.exe"
COMFYUI_VENV_PYTHON = (_PORTABLE_PYTHON if _PORTABLE_PYTHON.is_file() else
    COMFYUI_VENV_PYTHONW if COMFYUI_VENV_PYTHONW.is_file() else
    (COMFYUI_DIR / ".venv" / "Scripts" / "python.exe"))''')
patch('    elif installed and gpu["vendor"]=="nvidia":',
'''    elif installed and _PORTABLE_PYTHON.is_file() and (
            COMFYUI_DIR.parent / ".storyboard_gpu_install.json").is_file():
        try:
            marker=json.loads((COMFYUI_DIR.parent / ".storyboard_gpu_install.json").read_text(encoding="utf-8"))
        except (OSError,ValueError):
            marker={}
        if marker.get("vendor")==gpu["vendor"]:
            status = "local_verified_vendor"
            reason = "Verified portable release for GPU vendor; actual render still requires E2E testing."
        else:
            status = "backend_not_verified"
            reason = "Portable GPU runtime mismatches detected hardware."
    elif installed and gpu["vendor"]=="nvidia":''')
patch('status in ("ready_server","local_nvidia")',
      'status in ("ready_server","local_nvidia","local_verified_vendor")')
patch('[str(COMFYUI_VENV_PYTHON), "main.py", "--listen", "127.0.0.1", "--port", "8188"],',
'''([str(COMFYUI_VENV_PYTHON), "-s", "main.py", "--windows-standalone-build",
              "--listen", "127.0.0.1", "--port", "8188"] if _PORTABLE_PYTHON.is_file() else
             [str(COMFYUI_VENV_PYTHON), "main.py", "--listen", "127.0.0.1", "--port", "8188"]),''')
patch('    "sd_xl_turbo_1.0_fp16.safetensors",',
      '    "sd_xl_turbo_1.0_fp16.safetensors",\n    "sd_xl_base_1.0.safetensors",')
patch('''    is_turbo = "turbo" in checkpoint.lower()
    steps = 4 if is_turbo else 6
    cfg = 1.2 if is_turbo else 1.8
    sampler_name = "euler_ancestral" if is_turbo else "euler"
    scheduler = "normal" if is_turbo else "sgm_uniform"''',
'''    is_turbo = "turbo" in checkpoint.lower()
    is_base = "xl_base" in checkpoint.lower()
    steps = 25 if is_base else (4 if is_turbo else 6)
    cfg = 6.5 if is_base else (1.2 if is_turbo else 1.8)
    sampler_name = "euler_ancestral" if is_turbo else "euler"
    scheduler = "normal" if (is_turbo or is_base) else "sgm_uniform"''')
ast.parse(s,filename=str(p));p.write_text(s,encoding="utf-8")
print("PORTABLE_PROVIDER_PATCH_PASS")
