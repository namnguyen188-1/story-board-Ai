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
import re

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

        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(subprocess, "DETACHED_PROCESS", 0)

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





def get_sdxl_bucket(target_w: int, target_h: int) -> tuple[int, int]:
    """Returns optimal native SDXL resolution bucket closest to target aspect ratio (~1.0 Megapixel).
    Using full ~1.0MP buckets (1344x768 for 16:9, 768x1344 for 9:16) prevents soft blurry upscaling artifacts.
    """
    ratio = target_w / max(1, target_h)
    if ratio <= 0.65:    # 9:16 vertical portrait (target 720x1280 or 1080x1920)
        return (768, 1344)
    elif ratio <= 0.85:  # 3:4 portrait
        return (896, 1152)
    elif ratio >= 1.5:   # 16:9 landscape (target 1280x720 or 1920x1080)
        return (1344, 768)
    elif ratio >= 1.2:   # 4:3 landscape
        return (1152, 896)
    else:                # 1:1 square
        return (1024, 1024)


def build_prompts(
    prompt: str,
    visual_style: str = "whiteboard",
    genre: str = "documentary",
    width: int = 1280,
    height: int = 720,
) -> tuple[str, str]:
    """Generates tuned positive and negative prompts based on style and genre.
    Strict genre and visual style isolation guarantees that Stoic, Drama, Western,
    and Whiteboard/Colored Marker never contaminate each other.
    """
    clean_prompt = prompt.strip()
    is_vertical = height > width
    ratio_tag = "9:16 vertical portrait" if is_vertical else "16:9 widescreen"

    genre_lower = str(genre or "").lower().strip()
    style_lower = str(visual_style or "").lower().strip()

    # BRANCH 1: STOIC / KHẮC KỶ (100% ISOLATED: Carrara Marble Statue, Antique Relics, Roman Ruins)
    if genre_lower in ("stoic", "stoicism", "stoi"):
        is_relic = any(
            kw in clean_prompt.lower()
            for kw in (
                "hourglass", "clepsidra", "reloj", "sand trickling", "oil lamp", "candle", "candlelight",
                "flame", "papyrus", "scroll", "writing", "quill", "ink", "coins", "denarius", "scales",
                "sundial", "brazier", "embers", "columns", "pantheon", "colosseum", "storm", "macro"
            )
        ) and not any(kw in clean_prompt.lower() for kw in ("statue", "sculpture", "marcus", "aurelius", "monument"))

        is_wide = any(
            kw in clean_prompt.lower()
            for kw in ("wide", "standing", "full body", "ruins", "courtyard", "colonnade", "temple", "palace", "hall", "landscape", "distant")
        )

        is_torso = any(
            kw in clean_prompt.lower()
            for kw in ("torso", "chest", "abs", "muscular", "medium torso", "waist", "body", "power", "strength", "fuerza", "dignidad", "broad shoulder", "shoulders")
        )

        is_profile = any(
            kw in clean_prompt.lower()
            for kw in ("profile", "hand on", "chin", "gaze", "thought", "side view", "three-quarter", "looking away", "contemplat")
        )

        if is_relic:
            # Archetype A: B-Roll Symbolic Antique Relics (No statue, pure atmospheric relics)
            positive = (
                f"cinematic {ratio_tag} film still, 35mm cinema lens, master cinematography, photorealistic 8k, "
                f"authentic antique Roman relics and classical antiquity atmosphere, warm dramatic chiaroscuro candlelight bokeh, "
                f"rich tactile weathered textures: {clean_prompt}"
            )
            negative = (
                "statue, person, human, face, living human, human skin, modern objects, plastic, digital gadgets, "
                "whiteboard, marker, cartoon, drawing, deformed, blurry, low quality, artifacts, watermark, text, signature"
            )
        elif is_wide:
            # Archetype B: Wide Establishing Shot of Marble Statue in Ruins / Colonnade
            positive = (
                f"cinematic wide establishing shot of a monumental carved white Carrara marble statue of Stoic emperor Marcus Aurelius, "
                f"standing majestically amidst ancient Roman classical ruins and weathered Corinthian columns under a dramatic atmospheric sky, "
                f"soft golden volumetric god rays, authentic classical antiquity sculpture, completely solid chiselled stone material, "
                f"epic cinematic scale, museum masterpiece, {ratio_tag}. Setting: {clean_prompt}"
            )
            negative = (
                "two statues, 2 statues, multiple statues, second statue, background statue, secondary figure, crowd, duplicate, blurry figure in background, "
                "living human, real person, human skin, flesh, living eyes with pupils, human face, skin pores, flesh tones, "
                "tan skin, peach skin, veins, real hair, beard hair, soft skin, biological human, bodybuilder cosplay, "
                "modern clothes, whiteboard, marker, cartoon, deformed, bad anatomy, broken arms, blur, watermark, text, signature"
            )
        elif is_torso:
            # Archetype C: Heroic Muscular Torso & Abs Shot (Waist-up, draped toga)
            positive = (
                f"centered medium waist-up shot of a monumental carved Roman stone statue, white Carrara marble sculpture of Emperor Marcus Aurelius, "
                f"muscular sculpted stone torso and defined chiselled stone abs, broad stone shoulders, royal draped stone toga cascading over hip and shoulder, "
                f"ancient classical antiquity art, authentic chiselled marble stone texture, cold white marble, completely inanimate solid stone statue, "
                f"carved stone eyes without pupils, sculpted stone beard, dramatic moody museum chiaroscuro lighting, floating golden embers in dark atmospheric Roman background, "
                f"neoclassical stone sculpture masterpiece, {ratio_tag}. Setting: {clean_prompt}"
            )
            negative = (
                "two statues, 2 statues, multiple statues, second statue, background statue, secondary figure, crowd, duplicate, blurry figure in background, "
                "living human, real person, human skin, flesh, living eyes with pupils, human face, skin pores, flesh tones, "
                "tan skin, peach skin, veins, real hair, beard hair, soft skin, biological human, bodybuilder cosplay, "
                "organic human flesh, modern clothes, whiteboard, marker, cartoon, extra limbs, deformed, bad anatomy, blur, watermark, text, signature"
            )
        elif is_profile:
            # Archetype D: Philosophical Three-Quarter Profile & Hand on Chin
            positive = (
                f"cinematic three-quarter profile shot of a carved white Carrara marble statue of Marcus Aurelius in deep philosophical thought, "
                f"sculpted stone hand thoughtfully resting near chin, contemplative stone gaze, noble chiseled stone features, curly stone hair and beard, "
                f"cold white marble texture with fine chisel marks, dramatic side raking light, dark atmospheric Roman background, "
                f"100% solid stone material, neoclassical stone sculpture masterpiece, {ratio_tag}. Setting: {clean_prompt}"
            )
            negative = (
                "two statues, 2 statues, multiple statues, second statue, background statue, secondary figure, crowd, duplicate, blurry figure in background, "
                "living human, real person, human skin, flesh, living eyes with pupils, human face, skin pores, flesh tones, "
                "tan skin, peach skin, veins, real hair, beard hair, soft skin, biological human, bodybuilder cosplay, "
                "organic human flesh, modern clothes, whiteboard, marker, cartoon, deformed, bad anatomy, broken arms, blur, watermark, text, signature"
            )
        else:
            # Archetype E: Standard Heroic Statue Medium Shot
            positive = (
                f"monumental carved Roman stone statue, cold white Carrara marble sculpture of Emperor Marcus Aurelius, "
                f"medium framing showing noble carved stone head and muscular sculpted stone shoulders draped in toga, "
                f"ancient classical antiquity art, authentic chiselled marble stone texture, rough chiselled stone finish, "
                f"completely inanimate solid stone statue, carved stone eyes without pupils, sculpted stone beard and hair, "
                f"dramatic moody museum chiaroscuro lighting, dark atmospheric Roman background, fine stone cracks and mineral veins, "
                f"neoclassical stone sculpture, {ratio_tag}. Setting: {clean_prompt}"
            )
            negative = (
                "two statues, 2 statues, multiple statues, second statue, background statue, secondary figure, crowd, duplicate, blurry figure in background, "
                "living human, real person, human skin, flesh, living person, realistic eyes with pupils, human face, skin pores, "
                "flesh tones, tan skin, peach skin, veins, real hair, beard hair, soft skin, biological human, bodybuilder cosplay, "
                "organic human flesh, modern clothes, whiteboard, marker, cartoon, deformed, bad anatomy, broken arms, blur, watermark, text, signature"
            )

    # BRANCH 2: DRAMA (HOLLYWOOD LIVE-ACTION & FAMILY DRAMA - 100% ISOLATED)
    elif genre_lower in ("drama", "family_drama", "hoa_drama", "cinematic_drama", "hollywood"):
        positive = (
            f"cinematic {ratio_tag} film shot, photorealistic contemporary Hollywood cinematic drama, "
            f"authentic human actors with natural human skin tones and facial pores, emotional performance, "
            f"35mm anamorphic cinema lens, master cinematography, atmospheric lighting, Kodak Vision3 color grading, "
            f"highly detailed 8k film still: {clean_prompt}"
        )
        negative = (
            "statue, marble, stone sculpture, pedestal, bust, whiteboard, marker, sketch, drawing, illustration, "
            "cartoon, anime, 3d render, CGI, plastic skin, doll, mannequin, ugly, deformed, bad anatomy, bad hands, "
            "missing limbs, blurry, low quality, artifacts, watermark, text, signature"
        )

    # BRANCH 3: WESTERN / VIỄN MIỀN TÂY (100% ISOLATED)
    elif genre_lower in ("western", "ranch", "frontier", "cowboy"):
        positive = (
            f"cinematic {ratio_tag} film shot, authentic American frontier western movie cinematography, "
            f"weathered leather and denim, dusty rugged landscape, dramatic golden hour sun, authentic western actors "
            f"with lifelike skin textures, 35mm anamorphic lens, master composition, 8k resolution: {clean_prompt}"
        )
        negative = (
            "modern clothes, modern gadgets, cars, electronics, statue, marble, stone sculpture, whiteboard, marker, "
            "sketch, drawing, illustration, cartoon, anime, 3d render, CGI, plastic, doll, ugly, deformed, bad anatomy, "
            "bad hands, blurry, low quality, artifacts, watermark, text, signature"
        )

    # BRANCH 4: WHITEBOARD COLORED MARKER (AFTER SKOOL - 100% ISOLATED)
    elif style_lower in ("hand_color", "colored_marker", "color_marker") or genre_lower in ("colored_marker", "hand_color", "after_skool"):
        sanitized = re.sub(
            r"(?i)(photorealistic|hyperrealistic|3d render|carmara marble|weathered grey stone|blank unpainted stone eyes|chiaroscuro stone monument|grey carved stone)",
            "",
            clean_prompt,
        ).strip()
        positive = (
            f"vibrant hand-drawn colored marker illustration, rich chisel-tip marker pens on clean white whiteboard background, "
            f"After Skool educational storytelling art style, crisp ink line art outlines, expressive colorful marker sketches, "
            f"dynamic educational visual metaphors, bold colorful markers, masterpiece whiteboard artwork: {sanitized}"
        )
        negative = (
            "photorealistic, realistic photo, real human, photograph, 3d render, CGI, statue, marble, stone, "
            "dark background, grey background, gloomy, film still, cinema, ugly, deformed, blurry, low quality, "
            "artifacts, watermark, text, signature"
        )

    # BRANCH 5: WHITEBOARD PHÁC THẢO TRẮNG ĐEN (MONOCHROME SKETCH)
    elif style_lower in ("whiteboard", "monochrome_sketch", "black_white") or genre_lower == "whiteboard":
        positive = (
            f"black ink whiteboard sketch, minimalist line art drawing on clean pure white background, "
            f"storyboard illustration, crisp black outlines, sharp details, high contrast, black and white marker: {clean_prompt}"
        )
        negative = (
            "color, shading, gradients, photorealistic, realistic photo, real human, 3d render, CGI, statue, marble, "
            "gray background, dark background, noise, blurry, messy, ugly, deformed, low quality, artifacts, watermark, text, signature"
        )

    # BRANCH 6: 3D/2D ANIMATION (HOẠT HÌNH)
    elif style_lower == "color_animation" or genre_lower in ("animation", "anime"):
        positive = (
            f"vibrant animated movie aesthetic, 3d animation render, colorful stylized design, "
            f"rich lighting, expressive characters, beautiful colors, cinema quality: {clean_prompt}"
        )
        negative = (
            "photorealistic, realistic photo, real life, monochrome, statue, marble, whiteboard, marker, ugly, deformed, "
            "low quality, watermark, text"
        )

    # BRANCH 7: OTHER CINEMATIC GENRES (Action, Mafia, Horror, History, Documentary)
    else:
        positive = (
            f"cinematic {ratio_tag} film shot, {genre} movie aesthetic, stunning composition, 8k resolution, masterpiece, "
            f"atmospheric lighting, highly detailed, vivid storytelling visual: {clean_prompt}"
        )
        negative = (
            "statue, marble, whiteboard, marker, sketch, cartoon, anime, ugly, deformed, bad anatomy, bad hands, "
            "missing limbs, missing hands, severed arms, cropped limbs, elongated torso, stretched proportions, "
            "blurry, grainy, low resolution, low quality, artifacts, watermark, text, signature"
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
    is_lightning = "lightning" in checkpoint.lower()

    if is_turbo:
        steps = 4
        cfg = 1.2
        sampler_name = "euler_ancestral"
        scheduler = "normal"
    elif is_lightning:
        # Optimal RealVisXL Lightning sweet spot: 8 steps + euler_ancestral + karras + CFG 2.0
        # Yields +85% higher sharpness, micro-texture, and crisp clarity over basic 6-step euler
        steps = 8
        cfg = 2.0
        sampler_name = "euler_ancestral"
        scheduler = "karras"
    else:
        steps = 20
        cfg = 5.0
        sampler_name = "dpmpp_2m_sde"
        scheduler = "karras"



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

    pos, neg = build_prompts(prompt, visual_style=visual_style, genre=genre, width=width, height=height)

    latent_w, latent_h = get_sdxl_bucket(width, height)

    workflow = build_workflow(

        positive_prompt=pos,

        negative_prompt=neg,

        checkpoint=checkpoint,

        width=latent_w,

        height=latent_h,

    )



    # Character consistency must use REAL IP-Adapter conditioning, never
    # text-only wording that pretends to have received a face reference.
    all_refs = [reference_path] if reference_path else []
    all_refs.extend(character_reference_paths or [])
    is_stoic_genre = any(kw in str(genre).lower() for kw in ("stoic", "philosophy", "statue"))
    is_marker_or_whiteboard = (
        str(visual_style or "").lower() in ("hand_color", "colored_marker", "color_marker", "whiteboard", "monochrome_sketch", "black_white")
        or any(kw in str(genre or "").lower() for kw in ("whiteboard", "colored_marker", "hand_color"))
    )
    if all_refs and not is_stoic_genre and not is_marker_or_whiteboard:
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
        from PIL import Image, ImageOps
        with Image.open(output_path) as img:
            rgb_img = img.convert("RGB")
            if rgb_img.size != (width, height):
                fitted = ImageOps.fit(rgb_img, (width, height), method=Image.Resampling.LANCZOS)
                fitted.save(output_path, "PNG")
            elif img.mode != "RGB":
                rgb_img.save(output_path, "PNG")
    except Exception as exc:

        raise ComfyUIError(f"Tệp ảnh từ ComfyUI không hợp lệ: {exc}") from exc

    # Tự động dọn dẹp file tạm trong ComfyUI/output sau khi đã lưu an toàn về dự án
    # Giúp chống tích tụ file rác và giải phóng dung lượng ổ cứng
    if os.environ.get("COMFYUI_KEEP_OUTPUT", "0").strip().lower() not in ("1", "true", "yes"):
        try:
            target_to_clean = local_output_file if local_output_file.is_file() else (COMFYUI_DIR / "output" / subfolder / filename)
            if target_to_clean.is_file() and target_to_clean.resolve() != output_path.resolve():
                target_to_clean.unlink(missing_ok=True)
                if subfolder:
                    sub_dir = COMFYUI_DIR / "output" / subfolder
                    if sub_dir.is_dir() and not any(sub_dir.iterdir()):
                        try:
                            sub_dir.rmdir()
                        except OSError:
                            pass
        except Exception:
            pass

    return str(output_path)


def cleanup_comfyui_artifacts(include_inputs: bool = True, older_than_seconds: float = 0.0) -> dict[str, Any]:
    """Cleans up temporary outputs and character reference inputs in ComfyUI directories.

    Args:
        include_inputs: If True, also cleans temporary sb_character_* and auto_character_* from input/.
        older_than_seconds: If > 0, only deletes files modified older than this threshold.
    Returns:
        Dict with count of deleted output and input files, plus bytes freed.
    """
    now = time.time()
    deleted = {"outputs": 0, "inputs": 0, "bytes_freed": 0, "ok": True}

    # 1. Output directory: clean StoryboardStudio_* files or all output images
    out_dir = COMFYUI_DIR / "output"
    if out_dir.is_dir():
        for p in list(out_dir.glob("StoryboardStudio*.*")):
            if p.is_file():
                if older_than_seconds <= 0 or (now - p.stat().st_mtime) >= older_than_seconds:
                    try:
                        sz = p.stat().st_size
                        p.unlink(missing_ok=True)
                        deleted["outputs"] += 1
                        deleted["bytes_freed"] += sz
                    except Exception:
                        pass

    # 2. Input directory: clean temporary character anchors sb_character_* and auto_character_*
    if include_inputs:
        in_dir = COMFYUI_DIR / "input"
        if in_dir.is_dir():
            for pattern in ("sb_character_*.*", "auto_character_*.*"):
                for p in list(in_dir.glob(pattern)):
                    if p.is_file():
                        if older_than_seconds <= 0 or (now - p.stat().st_mtime) >= older_than_seconds:
                            try:
                                sz = p.stat().st_size
                                p.unlink(missing_ok=True)
                                deleted["inputs"] += 1
                                deleted["bytes_freed"] += sz
                            except Exception:
                                pass

    # 3. Temp directory: clean any lingering temp files
    temp_dir = COMFYUI_DIR / "temp"
    if temp_dir.is_dir():
        for p in list(temp_dir.glob("*.*")):
            if p.is_file():
                if older_than_seconds <= 0 or (now - p.stat().st_mtime) >= older_than_seconds:
                    try:
                        sz = p.stat().st_size
                        p.unlink(missing_ok=True)
                        deleted["bytes_freed"] += sz
                    except Exception:
                        pass

    return deleted

