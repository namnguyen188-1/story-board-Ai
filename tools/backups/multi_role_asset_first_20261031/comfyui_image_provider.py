"""ComfyUI Local Image Provider for Storyboard Studio Pro.



Generates high-speed images (1.5 - 2.5s per image) using local NVIDIA GPU (RTX 3060 Ti)

and ComfyUI SDXL Lightning / Turbo checkpoints.

"""

from __future__ import annotations



import json

import os

import shutil

import subprocess

import sys

import time

import urllib.error

import urllib.parse

import urllib.request

from pathlib import Path

from PIL import Image



COMFYUI_HOST = os.environ.get("COMFYUI_HOST", "127.0.0.1:8188")

STUDIO_DIR = Path(__file__).resolve().parent

def discover_comfy_dir() -> Path:

    configured = os.environ.get("STORYBOARD_COMFYUI_DIR", "").strip()

    candidates = ([Path(configured).expanduser()] if configured else []) + [

        Path(r"C:\ComfyUI"),

        STUDIO_DIR / "runtime" / "comfyui" / "portable" / "ComfyUI",

        STUDIO_DIR / "runtime" / "comfyui",

        STUDIO_DIR.parent / "ComfyUI",

        Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Programs" / "ComfyUI",

        Path(r"D:\ComfyUI"),

    ]

    for candidate in candidates:

        if (candidate / "main.py").is_file():

            return candidate

    return candidates[0]



COMFYUI_DIR = discover_comfy_dir()

COMFYUI_VENV_PYTHONW = COMFYUI_DIR / ".venv" / "Scripts" / "pythonw.exe"

_STANDARD_VENV_PYTHON = COMFYUI_DIR / "venv" / "Scripts" / "python.exe"

COMFYUI_VENV_PYTHON = (

    COMFYUI_VENV_PYTHONW if COMFYUI_VENV_PYTHONW.is_file() else

    COMFYUI_DIR / ".venv" / "Scripts" / "python.exe"

)

if not COMFYUI_VENV_PYTHON.is_file() and _STANDARD_VENV_PYTHON.is_file():

    COMFYUI_VENV_PYTHON = _STANDARD_VENV_PYTHON



PREFERRED_CHECKPOINTS = [

    "RealVisXL_V4.0_Lightning.safetensors",

    "sd_xl_turbo_1.0_fp16.safetensors",

]



class ComfyUIError(RuntimeError):

    pass





PID_FILE = STUDIO_DIR / "scratch" / "comfyui.pid"





def is_installed() -> bool:

    """Checks if ComfyUI directory, venv, and main.py exist."""

    return COMFYUI_VENV_PYTHON.is_file() and (COMFYUI_DIR / "main.py").is_file()





def compatibility_status(host: str = COMFYUI_HOST) -> dict:

    from gpu_capabilities import detect_gpu

    hardware = detect_gpu()

    server = is_ready(host, timeout=2.0)

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



def is_ready(host: str = COMFYUI_HOST, timeout: float = 2.0) -> bool:

    """Checks if ComfyUI REST API is running and responding."""

    try:

        url = f"http://{host}/system_stats"

        req = urllib.request.Request(url, headers={"User-Agent": "StoryboardStudio/1.0"})

        with urllib.request.urlopen(req, timeout=timeout) as resp:

            return resp.status == 200

    except Exception:

        return False





def ensure_server(host: str = COMFYUI_HOST, timeout: float = 240.0) -> bool:

    """Ensures ComfyUI is running, starting it automatically if needed."""

    if is_ready(host, timeout=1.0):

        return True



    if not is_installed():

        return False

    if not compatibility_status(host)["can_attempt_local"]:

        print("[ComfyUI] GPU backend unverified; select configured MCP/API or a supported ComfyUI server.", flush=True)

        return False



    # Launch ComfyUI completely in the background without any console window

    PID_FILE.parent.mkdir(parents=True, exist_ok=True)

    try:

        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

        startupinfo = None

        if os.name == "nt":

            startupinfo = subprocess.STARTUPINFO()

            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            startupinfo.wShowWindow = 0  # SW_HIDE

        log_path = STUDIO_DIR / "scratch" / "comfyui.log"

        log_path.parent.mkdir(parents=True, exist_ok=True)

        log_file = open(log_path, "a", encoding="utf-8", errors="replace")

        proc = subprocess.Popen(

            [str(COMFYUI_VENV_PYTHON), "main.py", "--listen", "127.0.0.1", "--port", "8188"],

            cwd=str(COMFYUI_DIR),

            stdout=log_file,

            stderr=log_file,

            creationflags=flags,

            startupinfo=startupinfo,

        )

        PID_FILE.write_text(str(proc.pid), encoding="utf-8")

        if os.name == "nt":

            try:

                import ctypes

                u = ctypes.windll.user32

                cb_type = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

                @cb_type

                def _cb(hwnd, _):

                    owner = ctypes.c_ulong()

                    u.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))

                    if owner.value == proc.pid:

                        u.ShowWindow(hwnd, 0)

                    return True

                u.EnumWindows(_cb, 0)

            except Exception:

                pass

    except Exception as exc:

        print(f"[ComfyUI] Không thể tự động khởi động ComfyUI: {exc}", file=sys.stderr)

        return False



    t0 = time.time()

    last_log = t0

    while time.time() - t0 < timeout:

        time.sleep(0.8)

        if is_ready(host, timeout=1.0):

            return True

        if time.time() - last_log >= 10.0:

            elapsed = int(time.time() - t0)

            print(f"[ComfyUI] Loading AI model into GPU VRAM... ({elapsed}s)", flush=True)

            last_log = time.time()

    return False





def stop_server(host: str = COMFYUI_HOST, timeout: float = 6.0) -> bool:

    """Stops ComfyUI, unloads models from GPU VRAM, and frees system resources."""

    # 1. Ask ComfyUI to immediately free memory and unload models from VRAM

    try:

        url = f"http://{host}/free"

        req = urllib.request.Request(

            url,

            data=json.dumps({"unload_models": True, "free_memory": True}).encode("utf-8"),

            headers={"Content-Type": "application/json", "User-Agent": "StoryboardStudio/1.0"},

        )

        urllib.request.urlopen(req, timeout=1.5)

    except Exception:

        pass



    # 2. Kill recorded PID if tracked

    if PID_FILE.is_file():

        try:

            pid = int(PID_FILE.read_text(encoding="utf-8").strip())

            subprocess.run(

                ["taskkill", "/F", "/T", "/PID", str(pid)],

                capture_output=True,

                timeout=5,

                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),

            )

        except Exception:

            pass

        try:

            PID_FILE.unlink(missing_ok=True)

        except Exception:

            pass



    # Never stop arbitrary processes on port 8188: only recorded owned PIDs.

    # 4. Wait for confirmation that port 8188 is down

    t0 = time.time()

    while time.time() - t0 < timeout:

        if not is_ready(host, timeout=0.5):

            return True

        time.sleep(0.3)

    return not is_ready(host, timeout=0.5)





class ComfyUISession:

    """Context manager for on-demand ComfyUI lifecycle during production."""



    def __init__(self, timeout: float = 180.0, auto_stop: bool = True):

        self.timeout = timeout

        self.auto_stop = auto_stop

        self.was_running_initially = False



    def __enter__(self):

        self.was_running_initially = is_ready()

        if not self.was_running_initially:

            print("[ComfyUI] Starting ComfyUI with GPU to generate images...", flush=True)

            if not ensure_server(timeout=self.timeout):

                raise ComfyUIError("Cannot start ComfyUI at http://127.0.0.1:8188")

            print("[ComfyUI] ComfyUI server ready!", flush=True)

        return self



    def __exit__(self, exc_type, exc_val, exc_tb):

        if self.auto_stop and not self.was_running_initially:

            print("[ComfyUI] Production complete. Stopping ComfyUI and releasing GPU VRAM...", flush=True)

            stop_server()

            print("[ComfyUI] ComfyUI stopped successfully. GPU in idle power-saving mode.", flush=True)







def get_active_checkpoint(host: str = COMFYUI_HOST) -> str:

    """Detects available checkpoint, selecting SDXL Lightning or Turbo."""

    try:

        url = f"http://{host}/object_info/CheckpointLoaderSimple"

        req = urllib.request.Request(url, headers={"User-Agent": "StoryboardStudio/1.0"})

        with urllib.request.urlopen(req, timeout=2.0) as resp:

            data = json.loads(resp.read().decode("utf-8"))

            available = data.get("CheckpointLoaderSimple", {}).get("input", {}).get("required", {}).get("ckpt_name", [[]])[0]

            for pref in PREFERRED_CHECKPOINTS:

                if pref in available:

                    return pref

            if available:

                return available[0]

    except Exception:

        pass

    # Fallback checking disk

    ckpt_dir = COMFYUI_DIR / "models" / "checkpoints"

    for pref in PREFERRED_CHECKPOINTS:

        if (ckpt_dir / pref).is_file():

            return pref

    return PREFERRED_CHECKPOINTS[0]





def build_prompts(prompt: str, visual_style: str = "whiteboard", genre: str = "documentary") -> tuple[str, str]:

    """Generates tuned positive and negative prompts based on style and genre."""

    clean_prompt = prompt.strip()



    is_statue = any(

        kw in clean_prompt.lower()

        for kw in ("statue", "sculpture", "tượng", "monument", "carrara marble", "stone figure", "carved stone")

    )



    if visual_style == "whiteboard":

        positive = (

            f"black ink whiteboard sketch, minimalist line art drawing on clean pure white background, "

            f"storyboard illustration, crisp black outlines, sharp details, high contrast, black and white marker: "

            f"{clean_prompt}"

        )

        negative = (

            "color, shading, gradients, photorealistic, 3d render, CGI, gray background, dark background, "

            "noise, blurry, messy, ugly, deformed, low quality, artifacts, watermark, text, signature"

        )

    elif visual_style == "hand_color":

        import re

        sanitized = re.sub(

            r"(?i)\b(photorealistic|hyperrealistic|3d render|carmara marble|weathered grey stone|blank unpainted stone eyes|chiaroscuro stone monument|grey carved stone)\b",

            "",

            clean_prompt,

        ).strip()

        positive = (

            f"vibrant hand-drawn colored sketch, rich marker and watercolor illustration, "

            f"expressive color palette, warm lighting, artistic coloring on white paper, "

            f"crisp outlines, colorful storyboard frame, masterpiece artwork: {sanitized}"

        )

        negative = (

            "photorealistic, 3d render, CGI, monochrome, greyscale, black and white, dark, dull, gloomy, "

            "ugly, deformed, blurry, low quality, artifacts, watermark, text, signature"

        )

    elif visual_style == "color_animation":

        positive = (

            f"vibrant animated movie aesthetic, 3d animation render, colorful stylized design, "

            f"rich lighting, expressive characters, beautiful colors, cinema quality: {clean_prompt}"

        )

        negative = (

            "photorealistic, realistic photo, real life, monochrome, ugly, deformed, low quality, watermark, text"

        )

    elif is_statue or genre == "stoic":

        positive = (

            f"Cinematic live-action 16:9 historical epic film still, heroic Roman philosopher emperor (Marcus Aurelius archetype), "

            f"hyper-muscular chiseled Greek demigod physique, massive broad shoulders, thick muscular neck, sculpted pectoral chest muscles, striated deltoids, powerful vascular arms, weathered sun-kissed bronze skin with realistic pores, intense piercing dark eyes with living expressive pupils, "

            f"distinguished salt-and-pepper curly hair and thick groomed beard, royal crimson red draped toga (chlamys) draped across one shoulder leaving sculpted muscular chest and arm bare, "

            f"standing in ancient Roman forum with illuminated marble pillars, sweeping view of distant Acropolis at twilight, "

            f"dramatic chiaroscuro lighting, warm amber golden key light, deep sapphire teal shadows, soft volumetric rim glow, "

            f"photorealistic 8k, master cinematography, shot on 35mm lens: {clean_prompt}"

        )

        negative = (

            "scrawny, skinny, frail, weak, unmuscular, flat chest, narrow shoulders, lifeless stone statue, severed bust, tabletop pedestal, blank carved eyes, white stone skin, statue stand, "

            "zombie, deformed, cartoon, 3d cgi render, anime, modern clothes, t-shirt, plastic, blurry, low quality, "

            "ugly, bad anatomy, bad eyes, extra limbs, watermark, text, signature"

        )

    else:  # color_cinematic, anime, noir, or other movie genres

        positive = (

            f"cinematic film shot, {genre} movie aesthetic, stunning composition, 8k resolution, masterpiece, "

            f"atmospheric lighting, highly detailed, vivid storytelling visual: {clean_prompt}"

        )

        negative = (

            "ugly, deformed, bad anatomy, bad hands, missing limbs, blurry, grainy, low resolution, "

            "low quality, artifacts, watermark, text, signature"

        )



    return positive, negative





def build_workflow(

    positive_prompt: str,

    negative_prompt: str,

    checkpoint: str,

    width: int = 1280,

    height: int = 720,

    seed: int | None = None,

) -> dict:

    """Builds a ComfyUI prompt workflow optimized for SDXL Lightning/Turbo."""

    if seed is None:

        seed = int(time.time_ns() % 1_000_000_000)



    is_turbo = "turbo" in checkpoint.lower()

    steps = 4 if is_turbo else 6

    cfg = 1.2 if is_turbo else 1.8

    sampler_name = "euler_ancestral" if is_turbo else "euler"

    scheduler = "normal" if is_turbo else "sgm_uniform"



    return {

        "3": {

            "inputs": {

                "seed": seed,

                "steps": steps,

                "cfg": cfg,

                "sampler_name": sampler_name,

                "scheduler": scheduler,

                "denoise": 1.0,

                "model": ["4", 0],

                "positive": ["6", 0],

                "negative": ["7", 0],

                "latent_image": ["5", 0],

            },

            "class_type": "KSampler",

        },

        "4": {

            "inputs": {

                "ckpt_name": checkpoint,

            },

            "class_type": "CheckpointLoaderSimple",

        },

        "5": {

            "inputs": {

                "width": width,

                "height": height,

                "batch_size": 1,

            },

            "class_type": "EmptyLatentImage",

        },

        "6": {

            "inputs": {

                "text": positive_prompt,

                "clip": ["4", 1],

            },

            "class_type": "CLIPTextEncode",

        },

        "7": {

            "inputs": {

                "text": negative_prompt,

                "clip": ["4", 1],

            },

            "class_type": "CLIPTextEncode",

        },

        "8": {

            "inputs": {

                "samples": ["3", 0],

                "vae": ["4", 2],

            },

            "class_type": "VAEDecode",

        },

        "9": {

            "inputs": {

                "filename_prefix": "StoryboardStudio",

                "images": ["8", 0],

            },

            "class_type": "SaveImage",

        },

    }





def make_image(

    prompt: str,

    output: str | Path,

    reference_path: str | Path | None = None,

    *,

    character_reference_paths: list[str] | None = None,

    visual_style: str = "whiteboard",

    genre: str = "documentary",

    width: int = 1280,

    height: int = 720,

    host: str = COMFYUI_HOST,

    timeout: int = 90,

) -> str:

    """Generates an image via ComfyUI and saves it to output path.



    Returns the absolute string path to the saved image.

    """

    output_path = Path(output).resolve()

    output_path.parent.mkdir(parents=True, exist_ok=True)



    if not is_ready(host):

        if not ensure_server(host, timeout=180.0):

            raise ComfyUIError(

                f"ComfyUI không phản hồi tại http://{host}. Hãy bật ComfyUI trên máy của bạn."

            )



    checkpoint = get_active_checkpoint(host)

    pos, neg = build_prompts(prompt, visual_style=visual_style, genre=genre)



    workflow = build_workflow(

        positive_prompt=pos,

        negative_prompt=neg,

        checkpoint=checkpoint,

        width=width,

        height=height,

    )



    # Character consistency must use REAL IP-Adapter conditioning, never
    # text-only wording that pretends to have received a face reference.
    all_refs = [reference_path] if reference_path else []
    all_refs.extend(character_reference_paths or [])
    if all_refs:
        from comfyui_identity_refs import apply_character_references
        workflow = apply_character_references(workflow, all_refs, COMFYUI_DIR, host)

    # Submit prompt to ComfyUI

    submit_url = f"http://{host}/prompt"

    body = json.dumps({"prompt": workflow}).encode("utf-8")

    req = urllib.request.Request(

        submit_url,

        data=body,

        headers={"Content-Type": "application/json", "User-Agent": "StoryboardStudio/1.0"},

    )



    try:

        with urllib.request.urlopen(req, timeout=10) as resp:

            res_data = json.loads(resp.read().decode("utf-8"))

            prompt_id = res_data.get("prompt_id")

            if not prompt_id:

                raise ComfyUIError("ComfyUI không trả về prompt_id")

    except Exception as exc:

        raise ComfyUIError(f"Gửi yêu cầu tạo ảnh tới ComfyUI thất bại: {exc}") from exc



    # Poll history for completion

    t0 = time.time()

    history_url = f"http://{host}/history/{prompt_id}"

    image_info = None



    while time.time() - t0 < timeout:

        time.sleep(0.4)

        try:

            h_req = urllib.request.Request(history_url, headers={"User-Agent": "StoryboardStudio/1.0"})

            with urllib.request.urlopen(h_req, timeout=5) as h_resp:

                hist = json.loads(h_resp.read().decode("utf-8"))

                if prompt_id in hist:

                    outputs = hist[prompt_id].get("outputs", {})

                    for node_id, node_data in outputs.items():

                        images = node_data.get("images", [])

                        if images:

                            image_info = images[0]

                            break

                    if image_info:

                        break

        except Exception:

            pass



    if not image_info:

        raise ComfyUIError(f"Tạo ảnh qua ComfyUI quá thời gian chờ ({timeout}s).")



    # Fetch output image

    filename = image_info["filename"]

    subfolder = image_info.get("subfolder", "")

    type_ = image_info.get("type", "output")



    # First check direct local disk copy (faster than HTTP)

    local_output_file = COMFYUI_DIR / "output" / subfolder / filename

    if local_output_file.is_file():

        shutil.copy2(local_output_file, output_path)

    else:

        # Fallback to HTTP download

        query = urllib.parse.urlencode({"filename": filename, "subfolder": subfolder, "type": type_})

        view_url = f"http://{host}/view?{query}"

        v_req = urllib.request.Request(view_url, headers={"User-Agent": "StoryboardStudio/1.0"})

        with urllib.request.urlopen(v_req, timeout=15) as v_resp:

            output_path.write_bytes(v_resp.read())



    # Ensure valid RGB image

    try:

        with Image.open(output_path) as img:

            if img.mode != "RGB":

                rgb_img = img.convert("RGB")

                rgb_img.save(output_path, "PNG")

    except Exception as exc:

        raise ComfyUIError(f"Tệp ảnh từ ComfyUI không hợp lệ: {exc}") from exc



    return str(output_path)

