"""Create a fresh project bundle without copying jobs, API keys, or outputs."""
import argparse
import json
from pathlib import Path
import shutil
import socket
from common import ROOT, atomic, settings


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def clone(target, project_id=None):
    target = Path(target).expanduser().resolve()
    if target == ROOT or target.is_relative_to(ROOT) or ROOT.is_relative_to(target):
        raise ValueError("Choose a separate sibling folder")
    if target.exists():
        raise FileExistsError("Destination must not exist")
    def ignore(folder, names):
        omitted = {"__pycache__", ".git", "*.pyc"}
        if Path(folder) == ROOT:
            omitted.update({"state", "outputs", "runtime", "COPY_MANIFEST.json"})
        return [n for n in names if n in omitted or n.endswith(".pyc")]
    shutil.copytree(ROOT, target, ignore=ignore)
    cfg = settings()
    cfg["api_port"] = free_port()
    if project_id:
        import uuid
        cfg["flow_project_id"] = str(uuid.UUID(project_id))
    atomic(target / "settings.json", cfg)
    (target / "state").mkdir()
    (target / "outputs").mkdir()
    # Local browser bridge can be reused on this machine; invalid paths fall back on other hosts.
    machine = ROOT / "state" / "machine.json"
    if machine.is_file():
        shutil.copy2(machine, target / "state" / "machine.json")
    atomic(target / "PROJECT_COPY.json", {"fresh_jobs": True, "api_port": cfg["api_port"],
           "flow_project_id": cfg["flow_project_id"], "browser_bridge": "shared local Flow engine",
           "muse_session": "private copied account; sign in again if expired"})
    print("PROJECT_FOLDER=" + str(target))
    print("API_URL=http://127.0.0.1:" + str(cfg["api_port"]))
    return target


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("target", nargs="?")
    parser.add_argument("--project-id")
    args = parser.parse_args()
    target = args.target or input("Thu muc du an moi (duong dan day du): ").strip().strip('"')
    clone(target, args.project_id)
