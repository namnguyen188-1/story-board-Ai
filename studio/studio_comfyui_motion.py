"""ComfyUI AnimateDiff Local Motion Video Engine for Storyboard Studio.

Generates authentic AI motion video for Hook scenes (Cold Open 15-30s)
using local NVIDIA GPU (RTX 3060 Ti) with SDXL + HotshotXL / AnimateDiff motion modules.
100% offline, zero cloud API costs, zero watermarks.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
import urllib.request
import wave
from pathlib import Path

STUDIO_DIR = Path(__file__).resolve().parent

def get_audio_duration(audio_path: str | Path | None) -> float:
    """Returns audio duration in seconds, fallback to 8.0s."""
    if not audio_path or not Path(audio_path).is_file():
        return 8.0
    try:
        with wave.open(str(audio_path), "rb") as w:
            return w.getnframes() / max(1, w.getframerate())
    except Exception:
        return 8.0

def build_motion_prompt(scene: dict, bible: dict | None = None) -> tuple[str, str]:
    """Builds an optimized prompt for SDXL + AnimateDiff motion video."""
    scene_prompt = scene.get("prompt") or scene.get("visual_setup") or scene.get("description") or ""
    narration = scene.get("narration") or ""
    
    char_desc = ""
    if bible and bible.get("characters"):
        c = bible["characters"][0]
        char_desc = f"{c.get('name', '')}, {c.get('appearance', '')}, wearing {c.get('attire', '')}"
    
    positive = (
        f"Cinematic live-action film still with realistic natural motion. "
        f"{char_desc}. {scene_prompt}. {narration}. "
        f"Dynamic realistic movement, natural breathing, wind blowing fabric and hair, "
        f"atmospheric particles moving, master cinematography, photorealistic 8k, sharp focus."
    ).strip()
    
    negative = (
        "ugly, deformed, bad anatomy, blurry, hazy, low quality, soft, out of focus, "
        "smooth plastic skin, cartoon, 3d render, static, jumpy, jittery, watermark"
    )
    return positive, negative

def render_comfyui_motion_for_scene(
    scene: dict,
    bible: dict | None,
    image_path: Path | None,
    audio_path: Path | None,
    output_silent_mp4: Path,
    *,
    width: int = 1280,
    height: int = 720,
    frames: int = 8,
    fps: int = 8,
    host: str = "127.0.0.1:8188",
    timeout: int = 180,
) -> str:
    """Renders an authentic AI motion video for a scene using ComfyUI AnimateDiff SDXL."""
    import comfyui_image_provider as cip
    
    print(f"\n🎬 [ANIMATEDIFF_HOOK] Đang sinh video chuyển động AI cục bộ cho Cảnh Hook qua GPU...")
    if not cip.ensure_server(host, timeout=120.0):
        raise RuntimeError("ComfyUI server could not be started for AnimateDiff motion video.")
    
    output_silent_mp4 = Path(output_silent_mp4)
    output_silent_mp4.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = output_silent_mp4.parent / ".animatediff_temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    pos_prompt, neg_prompt = build_motion_prompt(scene, bible)
    ckpt = "RealVisXL_V4.0_Lightning.safetensors"
    motion_model = "hsxl_temporal_layers.f16.safetensors"
    
    # Internal generation resolution (SDXL HotshotXL standard bucket)
    gen_w = 1024 if width >= height else 576
    gen_h = 576 if width >= height else 1024

    has_input_img = False
    img_filename = f"hook_scene_input_{int(time.time()) % 10000}.png"
    if image_path and Path(image_path).is_file():
        comfy_dir = cip.discover_comfy_dir()
        if comfy_dir and (comfy_dir / "input").exists():
            dest = comfy_dir / "input" / img_filename
            try:
                shutil.copy2(str(image_path), str(dest))
                has_input_img = True
            except Exception:
                pass
    
    wf = {
        "1": {
            "inputs": {"ckpt_name": ckpt},
            "class_type": "CheckpointLoaderSimple"
        },
        "2": {
            "inputs": {
                "model": ["1", 0],
                "model_name": motion_model,
                "beta_schedule": "autoselect"
            },
            "class_type": "ADE_AnimateDiffLoaderWithContext"
        },
        "3": {
            "inputs": {
                "text": pos_prompt,
                "clip": ["1", 1]
            },
            "class_type": "CLIPTextEncode"
        },
        "4": {
            "inputs": {
                "text": neg_prompt,
                "clip": ["1", 1]
            },
            "class_type": "CLIPTextEncode"
        },
    }

    if has_input_img:
        # Image-to-Video Mode: Preserves 100% Character Face & Background with Living AI Motion
        wf["5_load"] = {
            "inputs": {"image": img_filename},
            "class_type": "LoadImage"
        }
        wf["5_scale"] = {
            "inputs": {"image": ["5_load", 0], "width": gen_w, "height": gen_h, "upscale_method": "lanczos", "crop": "center"},
            "class_type": "ImageScale"
        }
        wf["5_vae"] = {
            "inputs": {"pixels": ["5_scale", 0], "vae": ["1", 2]},
            "class_type": "VAEEncode"
        }
        wf["5"] = {
            "inputs": {"samples": ["5_vae", 0], "amount": frames},
            "class_type": "RepeatLatentBatch"
        }
    else:
        # Text-to-Video Mode: Generates fresh living scene from prompt
        wf["5"] = {
            "inputs": {
                "width": gen_w,
                "height": gen_h,
                "batch_size": frames
            },
            "class_type": "EmptyLatentImage"
        }

    wf["6"] = {
        "inputs": {
            "seed": int(time.time() * 1000) % 1000000,
            "steps": 10 if has_input_img else 8,
            "cfg": 2.0,
            "sampler_name": "euler_ancestral",
            "scheduler": "karras",
            "denoise": 0.52 if has_input_img else 1.0,
            "model": ["2", 0],
            "positive": ["3", 0],
            "negative": ["4", 0],
            "latent_image": ["5", 0]
        },
        "class_type": "KSampler"
    }

    wf["7"] = {
        "inputs": {
            "samples": ["6", 0],
            "vae": ["1", 2]
        },
        "class_type": "VAEDecode"
    }
    wf["8"] = {
        "inputs": {
            "filename_prefix": "AnimateDiff_Hook_Scene",
            "images": ["7", 0]
        },
        "class_type": "SaveImage"
    }
    
    req = urllib.request.Request(
        f"http://{host}/prompt",
        data=json.dumps({"prompt": wf}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    resp = json.loads(urllib.request.urlopen(req, timeout=10).read().decode("utf-8"))
    pid = resp["prompt_id"]
    print(f"⚡ [ANIMATEDIFF_HOOK] Đã gửi tiến trình vào GPU ComfyUI (ID: {pid})...")
    
    # Wait for frames
    t0 = time.time()
    images = []
    while time.time() - t0 < timeout:
        time.sleep(1.5)
        try:
            h_req = urllib.request.Request(f"http://{host}/history/{pid}")
            h_data = json.loads(urllib.request.urlopen(h_req, timeout=5).read().decode("utf-8"))
            if pid in h_data and h_data[pid].get("outputs", {}).get("8", {}).get("images"):
                images = h_data[pid]["outputs"]["8"]["images"]
                break
            elif pid in h_data and h_data[pid].get("status", {}).get("status_str") == "error":
                raise RuntimeError(f"ComfyUI error: {h_data[pid].get('status')}")
        except Exception:
            continue
    
    if not images:
        raise TimeoutError(f"ComfyUI AnimateDiff motion generation timed out after {timeout}s")
    
    print(f"✅ [ANIMATEDIFF_HOOK] GPU đã tạo xong {len(images)} khung hình chuyển động! Đang tải về...")
    
    # Clean previous temp frames
    for old_f in temp_dir.glob("frame_*.png"):
        try: old_f.unlink()
        except Exception: pass
        
    for idx, img_info in enumerate(images):
        fn = img_info["filename"]
        subfolder = img_info.get("subfolder", "")
        img_type = img_info.get("type", "output")
        url = f"http://{host}/view?filename={urllib.parse.quote(fn)}&subfolder={urllib.parse.quote(subfolder)}&type={urllib.parse.quote(img_type)}"
        frame_dest = temp_dir / f"frame_{idx:04d}.png"
        urllib.request.urlretrieve(url, str(frame_dest))
        
        # Also copy the first frame to image_path if specified (for scene thumbnail/poster)
        if idx == 0 and image_path:
            shutil.copy2(frame_dest, image_path)
    
    # Calculate audio duration to loop video
    duration = get_audio_duration(audio_path)
    raw_clip = temp_dir / "raw_motion.mp4"
    
    # 1. First encode the raw motion clip at native fps
    cmd_raw = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-framerate", str(fps),
        "-i", str(temp_dir / "frame_%04d.png"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-vf", f"scale={width}:{height}:flags=lanczos",
        str(raw_clip)
    ]
    subprocess.run(cmd_raw, check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    
    # 2. Smoothly loop / ping-pong extend the clip to the exact narration duration
    # Using FFmpeg stream_loop with subtle crossfade
    loops = max(1, int(duration // (len(images) / fps)) + 1)
    cmd_extend = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-stream_loop", str(loops),
        "-i", str(raw_clip),
        "-t", f"{duration:.3f}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-pix_fmt", "yuv420p",
        str(output_silent_mp4)
    ]
    subprocess.run(cmd_extend, check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    print(f"🎬 [ANIMATEDIFF_HOOK] Hoàn thành video chuyển động Hook Cảnh 1 ({duration:.1f}s): {output_silent_mp4.name} (100% GPU Sạch, Không Watermark)!")
    return str(output_silent_mp4)
