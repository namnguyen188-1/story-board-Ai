import os, sys, subprocess, time
from pathlib import Path

ROOT = Path(r"D:\STORYBOARD_AI\studio")
EP = ROOT / "productions" / "ho-t-h-nh-3d" / "episode_001"
python_exe = ROOT / "runtime" / "python" / "python.exe"

plan_file = EP / "plan.json"
import json
plan = json.loads(plan_file.read_text(encoding="utf-8-sig"))
series = str(plan["config"]["series"])

cmd = [
    str(python_exe), "-u", str(ROOT / "pipeline_router.py"), "run",
    "--production-mode", "cinematic_drama",
    "--mode", "live",
    "--series", series,
    "--episode", "1",
    "--prompt", str(plan["config"].get("prompt") or series),
    "--minutes", "15",
    "--scene-seconds", "10",
    "--workers", "2",
    "--size", "720x1280",
    "--language", "Vietnamese",
    "--genre", "animation",
    "--visual-style", "color_animation",
    "--image-provider", "muse_video",
    "--model", "gemini-3.5-flash",
    "--subtitle-style", "karaoke_viral",
    "--subtitle-size", "76",
    "--input-mode", "idea",
    "--resume",
    "--no-shorts"
]

print("Launching pipeline router resume...")
env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
proc = subprocess.Popen(cmd, cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", env=env)

for line in proc.stdout:
    print(line, end="", flush=True)

proc.wait()
print(f"\nPipeline finished with exit code {proc.returncode}")
