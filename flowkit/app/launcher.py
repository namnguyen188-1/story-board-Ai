"""Portable launch: starts this kit's services only; never imports Storyboard."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

from common import ROOT, STATE, MUSE, INSTANCE_ID, api_key, rebase_muse_profiles, settings


def probe(url):
    try:
        with urllib.request.urlopen(url, timeout=3) as response:
            return json.load(response)
    except Exception:
        return None


def spawn(args, name, cwd, env):
    STATE.mkdir(exist_ok=True)
    log = (STATE / (name + ".log")).open("ab")
    flags = (0x08000000 | 0x00000008 | 0x00000200) if os.name == "nt" else 0
    if os.name == "nt":
        try:
            process = subprocess.Popen(args, cwd=str(cwd), env=env, stdout=log, stderr=log,
                                       creationflags=flags | 0x01000000)
            (STATE / (name + ".pid")).write_text(str(process.pid), encoding="ascii")
            return process
        except OSError:
            pass
    process = subprocess.Popen(args, cwd=str(cwd), env=env, stdout=log, stderr=log,
                               creationflags=flags)
    (STATE / (name + ".pid")).write_text(str(process.pid), encoding="ascii")
    return process


def main():
    cfg = settings()
    api_key(); rebase_muse_profiles()
    (STATE / "flow").mkdir(exist_ok=True)
    # Media browser starts on a claimed job, never while writing a script.
    if cfg.get('browser_mode', 'on_demand') == 'always_on':
        from flow_browser import open_browser
        open_browser()
    env = os.environ.copy()
    env.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8", PATH=str(ROOT / "bin") + os.pathsep + env.get("PATH", ""))
    if not probe(cfg["flow_url"] + "/health"):
        flow_env = {**env, "FLOW_AGENT_DIR": str(STATE / "flow"), "FLOW_PROJECT_ID": cfg["flow_project_id"],
                    "API_HOST": "127.0.0.1", "API_PORT": "18100", "WS_HOST": "127.0.0.1", "WS_PORT": "9232"}
        spawn([sys.executable, "-B", "-m", "uvicorn", "agent.main:app", "--host", "127.0.0.1", "--port", "18100", "--no-access-log"],
              "flow_engine", ROOT / "engines" / "flowkit", flow_env)
    url = f"http://127.0.0.1:{cfg['api_port']}"
    if "--serve" in sys.argv or "--direct" in sys.argv or "--daemon" in sys.argv:
        import uvicorn
        sys.path.insert(0, str(ROOT / "app"))
        os.chdir(str(ROOT / "app"))
        (STATE / "orchestrator.pid").write_text(str(os.getpid()), encoding="ascii")
        uvicorn.run("gateway:app", host=cfg["api_host"], port=int(cfg["api_port"]), log_level="info")
        return

    current = probe(url + "/health")
    if current and (current.get("service") != "flow-muse-orchestrator" or current.get("instance_id") != INSTANCE_ID):
        raise RuntimeError("API_PORT_IN_USE")
    if not current:
        spawn([sys.executable, "-B", "-m", "uvicorn", "gateway:app", "--host", cfg["api_host"], "--port", str(cfg["api_port"]), "--no-access-log"],
              "orchestrator", ROOT / "app", env)
    for _ in range(40):
        if probe(url + "/health"):
            print("API_READY=" + url, flush=True)
            if "--daemon" in sys.argv or "--serve" in sys.argv or "-d" in sys.argv:
                try:
                    while True:
                        time.sleep(2)
                except (KeyboardInterrupt, SystemExit):
                    break
            return
        time.sleep(0.25)
    raise RuntimeError("API_START_FAILED_SEE_STATE_LOG")


if __name__ == "__main__":
    main()
