# Storyboard AI MultiGPU — completed candidate verification (2026-10-15)

## Status: CANDIDATE PASS — COMMERCIAL RELEASE NOT YET APPROVED
Original StoryboardAI-Setup.exe, Setup_Storyboard_AI_Studio_Pro_v1.0.exe,
Storyboard_AI_Studio.exe, and all YouTube SEO Pro V2 sources remain unchanged.

### Tested
- Checkpoint: D:\STORYBOARD_AI\studio\checkpoints\MULTIGPU_BASELINE_20261015_164933
- Physical GPU on developer PC: NVIDIA GeForce RTX 3060 Ti, 8192 MB.
- Simulated GPU paths: 14/14 Python unit tests PASS (NVIDIA 3050/3060/4090; AMD; Intel; no discrete GPU).
- Source Python compiler and JS syntax: PASS.
- Bundled MCP pinned baseline: verified=True, version=0.3.1, v2_identical=38.
- Packaged Python, HTTP endpoint /api/gpu/status at isolated port 18765: PASS.
- Allowlisted source package: 12,213 files and 788,652,058 uncompressed bytes.
- Private runtime profiles, account databases, MCP outputs, and .env were not included in the candidate by the allowlist scanner.
- Inno Setup candidate build exit=0; setup size 185,751,440 bytes (177.15 MiB).
- Setup SHA-256: 1E73DA8EF5BB8935469BA98DF9A71E4947D4B5FE0BFDF3D935E6B1E81F55101F
- Silent install into separate D:\STORYBOARD_AI\_MULTIGPU_INSTALL_SMOKE: exit=0.
- Installed 9 critical file SHA-256 checks: all matched.
- Installed bundled Python detected NVIDIA and MCP baseline verified=True.
- Test uninstall exit=0; 2 generated Python bytecode caches cleaned. Temporary install folder removed.

### Deliverable on developer PC
D:\STORYBOARD_AI\dist\StoryboardAI-MultiGPU-Candidate-Setup.exe

### Outstanding release gates
- Fresh Windows machines with actual NVIDIA, AMD, Intel and no dedicated GPU not tested.
- Local ComfyUI runtime, drivers, PyTorch backend, SDXL checkpoints are optional external dependencies and not in this setup.
- AMD/Intel ComfyUI only when an already running compatible server is verified, otherwise choose cloud MCP/API.
- No real paid-provider E2E on new machine was executed.
- Compiler identified itself as "Non-commercial use only"; verify legal/commercial use rights before distribution.
- DO NOT label the candidate as broadly GPU-compatible local rendering, or declare sale-ready.

### Changed project source files
studio\gpu_capabilities.py (new)
studio\comfyui_image_provider.py
studio\web_server.py
studio\web\app.js
studio\web\index.html
package_distribution.py
New test/packaging scripts in Storyboard AI, no changes to V2.
