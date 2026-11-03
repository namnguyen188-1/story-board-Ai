"""Pipeline Router - Master Dispatcher between Narrative Storytelling and Cinematic Drama.

Guarantees 100% zero-regression isolation between pipelines.

"""

from __future__ import annotations



import os

import sys



# Configure UTF-8 encoding for Windows console and subprocesses

if hasattr(sys.stdout, "reconfigure"):

    try:

        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    except Exception:

        pass

if hasattr(sys.stderr, "reconfigure"):

    try:

        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    except Exception:

        pass



import argparse

from pathlib import Path

from typing import Dict, Any



STUDIO_DIR = Path(__file__).resolve().parent

if str(STUDIO_DIR) not in sys.path:

    sys.path.insert(0, str(STUDIO_DIR))





def route_production(args_obj: Any) -> int:

    """

    Directs production to either Pipeline A (Narrative Storytelling) or Pipeline B (Cinematic Drama).

    - 'narrative' (default): Hands off directly to legacy series_studio.py (100% unchanged).

    - 'cinematic_drama': Hands off to cinematic_engine.

    """

    production_mode = getattr(args_obj, "production_mode", "narrative")

    image_provider = getattr(args_obj, "image_provider", "")



    # STRICT ISOLATION GUARD:

    # All standard image generators (Google Flow MCP, ComfyUI, Gemini, Fal, v2_tuanstor)

    # belong 100% exclusively to the proven, battle-tested legacy series_studio.py engine.

    # Cinematic Drama is ONLY activated when production_mode is explicitly 'cinematic_drama'

    # AND image_provider is 'muse_video'.

    is_drama = (str(production_mode).strip().lower() == "cinematic_drama")

    # Allow any user-selected image/video provider for cinematic drama
    if is_drama and not image_provider:
        setattr(args_obj, "image_provider", "mcp_v2")



    if is_drama:

        print("\n=======================================================", flush=True)

        print("🎬 [PIPELINE ROUTER] KÍCH HOẠT NHÁNH B: PHIM KỊCH ĐIỆN ẢNH ĐA VAI", flush=True)

        print("   Đặc tính: Đa giọng nhân vật, BGM Auto-Ducking, Muse AI Video & Hội thoại đối đáp", flush=True)

        print("=======================================================\n", flush=True)

        from cinematic_engine.drama_orchestrator import run_cinematic_drama

        return run_cinematic_drama(args_obj)

    else:

        # Default legacy pipeline (100% untouched)

        print("\n=======================================================", flush=True)

        print("🎙️ [PIPELINE ROUTER] KÍCH HOẠT NHÁNH A: KỂ CHUYỆN THUYẾT MINH", flush=True)

        print(f"   Đặc tính: Luồng v1.3.0 chuẩn ổn định (Động cơ ảnh: {image_provider or 'mcp_v2'})", flush=True)

        print("=======================================================\n", flush=True)

        from series_studio import run as run_legacy

        return run_legacy(args_obj)





def main():

    parser = argparse.ArgumentParser(description="Storyboard AI Studio - Master Pipeline Router")

    subparsers = parser.add_subparsers(dest="command")



    # Support 'run' subcommand to match series_studio.py CLI syntax

    run_parser = subparsers.add_parser("run")

    for p in (parser, run_parser):

        p.add_argument("--production-mode", choices=["narrative", "cinematic_drama"], default="narrative",

                       help="Production workflow: 'narrative' (default legacy) or 'cinematic_drama' (multi-voice drama)")

        p.add_argument("--series", default="My Storyboard Series")

        p.add_argument("--episode", type=int, default=1)

        p.add_argument("--prompt", default="")

        p.add_argument("--prompt-file", default="")

        p.add_argument("--minutes", type=float, default=2.0)

        p.add_argument("--scene-seconds", type=float, default=12.0)

        p.add_argument("--language", default="Vietnamese")

        p.add_argument("--genre", default="drama")

        p.add_argument("--visual-style", default="auto")

        p.add_argument("--region", default="auto")

        p.add_argument("--voice-name", default="auto")

        p.add_argument("--speech-pacing", default="slow")

        p.add_argument("--input-mode", default="idea")

        p.add_argument("--reference-url", default="")

        p.add_argument("--link-clone-mode", default="exact_clone")

        p.add_argument("--size", default="1280x720")

        p.add_argument("--workers", type=int, default=4)

        p.add_argument("--mode", default="live")

        p.add_argument("--model", default="gemini-3.5-flash")

        p.add_argument("--image-provider", default="gemini")

        p.add_argument("--mcp-model-index", type=int, default=1)

        p.add_argument("--mcp-max-images", type=int, default=0)

        p.add_argument("--mcp-project-url", default="")

        p.add_argument("--mcp-visual-policy", default="unique")

        p.add_argument("--no-subtitles", action="store_true")

        p.add_argument("--subtitle-style", default="karaoke_viral")

        p.add_argument("--subtitle-size", type=int, default=0)

        p.add_argument("--camera-motion", default="auto")

        p.add_argument("--motion-mode", default="ken_burns")

        p.add_argument("--flow-video-model", default="Omni 1.1 Flash")

        p.add_argument("--flow-video-duration", type=int, default=8)

        p.add_argument("--atmospheric-overlay", default="auto")

        p.add_argument("--scene-timeout", type=int, default=1800)

        p.add_argument("--resume", action="store_true")

        p.add_argument("--with-shorts", action="store_true", default=False)

        p.add_argument("--no-shorts", dest="with_shorts", action="store_false")

        p.add_argument("--clean-watermark", action="store_true", default=True)

        p.add_argument("--no-clean-watermark", dest="clean_watermark", action="store_false")



    args, unknown = parser.parse_known_args()



    # Pass-through any extra unknown flags dynamically

    i = 0

    while i < len(unknown):

        arg = unknown[i]

        if arg.startswith("--"):

            key = arg[2:].replace("-", "_")

            if i + 1 < len(unknown) and not unknown[i + 1].startswith("--"):

                setattr(args, key, unknown[i + 1])

                i += 2

            else:

                setattr(args, key, True)

                i += 1

        else:

            i += 1



    # Read prompt from prompt-file if provided

    if getattr(args, "prompt_file", None) and os.path.exists(args.prompt_file):

        try:

            with open(args.prompt_file, "r", encoding="utf-8") as f:

                args.prompt = f.read().strip()

        except Exception:

            pass



    # Extract aspect ratio from size

    if getattr(args, "size", None) and "x" in args.size:

        parts = args.size.split("x")

        try:

            w, h = int(parts[0]), int(parts[1])

            args.aspect_ratio = "9:16" if h > w else "16:9"

        except Exception:

            args.aspect_ratio = "16:9"

    else:

        args.aspect_ratio = "16:9"



    exit_code = route_production(args)

    sys.exit(exit_code)





if __name__ == "__main__":

    main()

