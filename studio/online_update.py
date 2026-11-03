"""One-click updater process and persistent progress for the local Studio UI."""
import ctypes
import hashlib
import json
import os
import subprocess
import threading
import time
from pathlib import Path

_lock = threading.RLock()
_processes = {}
ACTIVE = {"starting", "checking", "downloading", "verifying", "extracting", "installing", "restarting"}

def _paths(install_dir):
    key = hashlib.sha256(str(Path(install_dir).resolve()).lower().encode()).hexdigest()[:16]
    folder = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "StoryboardAI" / "Updater"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / ("online-" + key + ".json"), folder / ("online-" + key + ".log")

def _write(path, data):
    temp = path.with_name(path.name + ".tmp-python")
    temp.write_text(json.dumps(data), encoding="utf-8")
    os.replace(temp, path)

def _read(path):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return {"state": "idle", "percent": 0}

def _alive(pid):
    if not pid:
        return False
    if os.name == "nt":
        from ctypes import wintypes
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = kernel.OpenProcess(0x1000, False, int(pid))
        if not handle:
            return False
        try:
            code = wintypes.DWORD()
            return bool(kernel.GetExitCodeProcess(handle, ctypes.byref(code))) and code.value == 259
        finally:
            kernel.CloseHandle(handle)
    try:
        os.kill(int(pid), 0)
        return True
    except OSError:
        return False

def get_status(install_dir):
    with _lock:
        path, log = _paths(install_dir)
        data = _read(path)
        if data.get("state") in ACTIVE and data.get("pid"):
            process = _processes.get(str(path))
            alive = process.poll() is None if process is not None else _alive(data["pid"])
            if not alive:
                data.update(state="failed", message="Tien trinh cap nhat da dung truoc khi hoan tat.")
                _write(path, data)
        return data

def start_update(install_dir, updater):
    with _lock:
        current = get_status(install_dir)
        if current.get("state") in ACTIVE and _alive(current.get("pid")):
            return {"success": True, "message": "Updater already running"}
        root = Path(install_dir).resolve()
        script = Path(updater).resolve()
        if not root.is_dir() or not script.is_file():
            raise FileNotFoundError("Khong tim thay bo cap nhat Storyboard AI.")
        path, log = _paths(root)
        data = {"state": "starting", "percent": 0, "pid": 0, "updated_at": time.time()}
        _write(path, data)
        try:
            with log.open("wb") as output:
                process = subprocess.Popen(
                    ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script),
                     "-InstallDir", str(root), "-StatusFile", str(path), "-Yes"],
                    cwd=str(script.parent), stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), close_fds=True)
            _processes[str(path)] = process
            existing = _read(path)
            if not existing.get("pid"):
                existing["pid"] = process.pid
                _write(path, existing)
        except Exception:
            _write(path, {"state": "failed", "message": "Khong khoi dong duoc bo cap nhat.", "percent": 0})
            raise
        return {"success": True, "message": "Updater started"}
