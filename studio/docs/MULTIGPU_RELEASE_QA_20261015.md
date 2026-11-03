# Storyboard AI MultiGPU — implementation and release gates
Date: 2026-10-15
Root: D:\STORYBOARD_AI
Baseline: studio\checkpoints\MULTIGPU_BASELINE_20261015_164933

## Source changes
- studio/gpu_capabilities.py: new read-only GPU discovery (nvidia-smi, Win32_VideoController), NVIDIA/AMD/Intel/no-GPU classification.
- studio/comfyui_image_provider.py: portable ComfyUI path discovery with explicit STORYBOARD_COMFYUI_DIR override, embedded candidate paths and old D:\ComfyUI compatibility; compatibility preflight; no unconditional termination of listeners on port 8188.
- studio/web_server.py: /api/gpu/status; /api/config adds hardware/compatibility; local ComfyUI production returns 503 with an error when unsupported; no automatic paid fallback.
- studio/web/index.html, app.js: visible GPU status and neutral label instead of 'RTX 3060 Ti only.'
- package_distribution.py: avoids raw runtime profiles and includes gpu_capabilities.py.
- package_multigpu_candidate.py: separate allowlist packaging, not intended to replace existing installer.
- dist/MultiGPU-Candidate-Installer.iss: isolated candidate AppId and install directory.

## Verification evidence
- Production status before changes: COMPLETED, running=false. No production was interrupted.
- Real system detected NVIDIA GeForce RTX 3060 Ti, 8192 MB.
- studio/test_gpu_portability.py: 14/14 passing, deterministic mocked GPU/backend cases; no paid API calls.
- Candidate packaged Python 3.11 import and read-only GPU endpoint on isolated port 18765: PASS.
- Candidate JS node --check and Python compile: PASS.
- Staged release allowlist audit: PASS for known private files; excluded private account profiles, tokens, MCP receipts and productions.
- Source app and YouTube SEO Pro V2 untouched by GPU code except listed Storyboard changes.

## Important limitations
- AMD/Intel local ComfyUI NOT verified on real AMD/Intel machines. Requires separate compatible backend.
- ComfyUI / models and drivers are optional and not included in the package. Local RTX support needs matching GPU driver, CUDA runtime, compatible ComfyUI and checkpoint.
- No guarantee that lower-memory GPUs render 1280x720 SDXL; run a model preflight on each machine.
- No clean-machine installer E2E has yet been completed; DO NOT distribute at scale without this.
- Existing StoryboardAI-Setup.exe and Setup_Storyboard_AI_Studio_Pro_v1.0.exe were not overwritten.
- Installed Inno Setup compiler reported "Non-commercial use only"; review licensing before a commercial release.
- No switch from local GPU to paid API/Google Flow occurs automatically; user must choose source and configure credentials.

## Next release gate
Install candidate on fresh Windows 10 and 11 machines with a NVIDIA GPU, AMD GPU,
Intel Arc, and no dedicated GPU. Validate boot, ComfyUI provider availability,
MCP login isolated per customer, packager E2E, video playback, uninstall and upgrades.
