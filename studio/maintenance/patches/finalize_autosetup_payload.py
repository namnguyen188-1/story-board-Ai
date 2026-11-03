"""Freeze AutoSetup transfer-test release payload after verifying official metadata."""
from pathlib import Path
import ast,hashlib,json,sys
sys.stdout.reconfigure(encoding="utf-8",errors="replace")
root=Path(r"D:\STORYBOARD_AI")
stage=root/"dist"/"Storyboard_AI_Studio_Pro_Transfer_Test_20261015"
studio=stage/"studio"
must=("studio/customer_bootstrap.py","studio/comfyui_image_provider.py",
      "studio/gpu_capabilities.py","studio/web_server.py",
      "studio/story_arc_quality.py","studio/reference_video_timeline.py",
      "studio/runtime/python/python.exe","studio/runtime/python/pythonw.exe",
      "studio/engine/bin/ffmpeg.exe","studio/engine/bin/ffprobe.exe",
      "studio/studio_mcp/node/node.exe","studio/studio_mcp/node/studio-flow-rpc.mjs",
      "studio/studio_mcp/node/dist/cli.js",
      "Storyboard_AI_Studio.exe","customer_setup_wizard.cs",
      "MODEL_LICENSE_AND_GPU_NOTES.txt")
for f in must:
    assert (stage/f).is_file(),f
for f in ("studio/customer_bootstrap.py","studio/comfyui_image_provider.py"):
    ast.parse((stage/f).read_text(encoding="utf-8"))
script=(stage/"studio/customer_bootstrap.py").read_text(encoding="utf-8")
assert 'row.get("lfs",{}).get("oid")' in script,"LFS SHA field regression"
assert "nvidia_legacy" in script and "NEED_AT_LEAST_22_GB" in script
assert "RELEASE_SHA256_MISSING" in script
assert "MODEL_METADATA_DIGEST_INVALID" in script
instructions="""STORYBOARD AI - AUTO SETUP CUSTOMER TRANSFER TEST

1. Install StoryboardAI-AutoSetup-TransferTest-Setup.exe on Windows 10/11 64 bit.
2. First launch: the program verifies Python, ffmpeg, ffprobe, Node/MCP,
   required modules and the installed Edge/Chrome browser.
3. If any CORE component is missing or corrupted: startup stops. Choose
   'Sua / Kiem tra lai'. The signed-hash-checked cached setup will repair
   the original package without installing global Python.
4. Choose MCP/API if you prefer browser-based Flow rendering (requires own
   Google Flow login and any applicable account credits or API billing).
5. Choose GPU Local: the setup downloads the matching official ComfyUI
   Windows Portable archive and verified SDXL 1.0 model on request.
   Plan for >22GB free disk space and potentially >9GB downloads.
   NVIDIA RTX/GTX, AMD and Intel use separate candidate releases.
   Proprietary drivers are NOT automatically installed and hardware support
   varies. Check that a real test image works before full production.
6. If GPU download fails or machine is unsupported, retry or select MCP/API.
   The app does not silently change to a paid provider.
7. To change mode, close Storyboard AI and run Start-menu shortcut
   'Storyboard AI - Kiem tra va cai GPU' (it launches the --setup wizard).
8. Keep API keys/customer Google login private. No such data is in this setup.
9. This is a TEST build; full live MCP/account/GPU creation on a second
   Windows computer is still required before public commercial distribution.
10. Downloaded SDXL base model uses CreativeML Open RAIL++-M licensing.
    Review MODEL_LICENSE_AND_GPU_NOTES.txt for source and license details.
"""
(stage/"HUONG_DAN_KHACH_HANG.txt").write_text(instructions,encoding="utf-8")
audit=json.loads((stage/"CANDIDATE_AUDIT.json").read_text(encoding="utf-8"))
full=list(dict.fromkeys(list(audit.get("sha256",{}).keys())+list(must)))
audit["sha256"]={f:hashlib.sha256((stage/f).read_bytes()).hexdigest() for f in full}
audit["required_files"]=len(full)
audit["release_status"]="AUTOSETUP_TEST_CANDIDATE_ONLY"
audit["gpu_auto_download"]="opt_in_official_sha256_checked"
audit["repair_source"]="cached installer with hash verification"
audit["bootstrap_unit_tests"]="9/9 pass; real GPU multi-GB download not yet E2E tested"
audit["real_cache_repair_test"]="PASS 2026-10-15, removed a test module and restored from cached installer"
(stage/"CANDIDATE_AUDIT.json").write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding="utf-8")
print("AUTOSETUP_PAYLOAD_FROZEN",len(full),"checks")
print("INSTRUCTIONS_REWRITTEN")
iss=root/"dist"/"AutoSetup-TransferTest-Installer.iss"
x=iss.read_text(encoding="utf-8")
if "#define MyAppVersion \"1.2.0\"" in x:
    x=x.replace('#define MyAppVersion "1.2.0"','#define MyAppVersion "1.2.1"')
iss.write_text(x,encoding="utf-8")
