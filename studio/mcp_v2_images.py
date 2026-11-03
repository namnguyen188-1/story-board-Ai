"""Storyboard Studio image provider using FlowKit WebTool with legacy MCP fallback.

This adapter prioritizes the fast, robust FlowKit WebTool engine (http://127.0.0.1:18110),
with automatic fallback to Studio's private Flow Node MCP if FlowKit is unavailable.
"""
from __future__ import annotations
import os, sys, shutil, uuid, re
from pathlib import Path
from PIL import Image, ImageOps
from studio_mcp.transport import OUTPUT as PRODUCTION_ROOT
from studio_mcp.accounts import active_account, account_tool_url
MODELS = ("Nano Banana Pro", "Nano Banana 2 Lite", "Nano Banana 2.1")

class StudioMcpImageError(RuntimeError):
    pass

def preflight():
    try:
        from studio import flowkit_client
        if flowkit_client.is_flowkit_alive():
            return None, MODELS
    except Exception:
        pass
    from studio_mcp.image_backend import StoryboardImageBackend, IMAGE_MODELS
    runtime = Path(__file__).resolve().parent / "studio_mcp" / "node"
    if not (runtime / "studio-flow-rpc.mjs").is_file() or not (runtime / "dist" / "cli.js").is_file():
        raise StudioMcpImageError("STORYBOARD_PRIVATE_MCP_RUNTIME_MISSING")
    if not account_tool_url(active_account()):
        raise StudioMcpImageError("STORYBOARD_PRIVATE_FLOW_TOOL_URL_REQUIRED")
    return StoryboardImageBackend, IMAGE_MODELS

def clean_id(raw):
    val = re.sub(r"[^A-Za-z0-9_-]+", "-", str(raw)).strip("-")
    return val[:65] or "episode"

def make_image(prompt, output_path, *, series, episode, scene, max_new_images,
               model_index=1, fallback=False, transport=None, aspect_ratio="16:9"):
    """Exactly one image job per call; model fallback off by default.

    Prioritizes FlowKit WebTool (http://127.0.0.1:18110) for high-speed, reliable generation.
    Falls back to legacy Node MCP v2 if FlowKit is offline.
    """
    if not 1 <= int(max_new_images) <= 1000:
        raise StudioMcpImageError("MCP budget is not approved; specify 1..1000 image slots")
    if model_index not in (0, 1, 2):
        raise StudioMcpImageError("Unknown Studio MCP image model")
    if not 20 <= len(prompt.strip()) <= 20000:
        raise StudioMcpImageError("Invalid MCP image prompt")

    # 1. FlowKit WebTool Priority
    try:
        from studio import flowkit_client
        if flowkit_client.is_flowkit_alive() or flowkit_client.ensure_flowkit_running(max_wait_seconds=3):
            print(f"[FLOWKIT_PREFERRED] Routing scene {scene} to FlowKit WebTool...", flush=True)
            res = flowkit_client.generate_image(
                prompt=prompt,
                output_path=output_path,
                aspect_ratio=aspect_ratio,
                scene_num=scene
            )
            print(f"[FLOWKIT_IMAGE_PASS] scene={scene} bytes={Path(output_path).stat().st_size}", flush=True)
            return str(output_path)
    except Exception as e:
        print(f"[FLOWKIT_FALLBACK_TO_LEGACY_MCP] FlowKit notice: {e}, falling back to legacy MCP...", flush=True)

    # 2. Legacy MCP V2 Fallback
    klass, image_models = preflight()
    name = "storyboard_studio_mcp_" + clean_id(series) + "_ep" + str(int(episode)).zfill(3)
    scope = PRODUCTION_ROOT / name
    os.environ["STORYBOARD_MCP_APPROVED"] = "1"
    os.environ["STORYBOARD_MCP_MAX_NEW_IMAGES"] = str(int(max_new_images))
    backend = klass(scope, enabled=True, spending_approved=True, max_new_images=int(max_new_images),
                    model=image_models[model_index], fallback=fallback, transport=transport)
    scene_id = clean_id(series) + "_ep" + str(int(episode)) + "_scene_" + str(int(scene)).zfill(4)
    receipts = backend.render_one_queue([{
        "scene_id": scene_id, "prompt": prompt, "aspect_ratio": str(aspect_ratio or "16:9")
    }])
    if scene_id not in receipts:
        raise StudioMcpImageError("MCP image receipt missing")
    verified = receipts[scene_id]
    source = Path(str(verified["path"]))
    if not source.is_file():
        raise StudioMcpImageError("MCP returned missing media")
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as image:
        image.load()
        if image.width < 256 or image.height < 256:
            raise StudioMcpImageError("MCP image resolution too low")
        rgb = image.convert("RGB")
        is_vertical = (str(aspect_ratio).strip() == "9:16")
        target_r = 9 / 16 if is_vertical else 16 / 9
        target_size = (1080, 1920) if is_vertical else (1536, 864)
        if abs(rgb.width / rgb.height - target_r) > 0.04:
            rgb = ImageOps.fit(rgb, target_size, method=Image.Resampling.LANCZOS)
        else:
            rgb = rgb.resize(target_size, Image.Resampling.LANCZOS)
        temp = target.with_name(target.stem + "." + uuid.uuid4().hex + ".png")
        rgb.save(temp, format="PNG")
        os.replace(temp, target)
    print("[MCP_IMAGE_PASS] scene=" + str(scene) + " bytes=" + str(target.stat().st_size), flush=True)
    return str(target)
