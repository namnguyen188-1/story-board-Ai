"""FlowKit & Storyboard AI - Mutual-Exclusive On-Demand Engine Orchestrator.

Ensures strictly ONE browser engine runs at any time:
- "flow": Google Flow on CDP port 9461 (profile: runtime/flow_profile)
- "chatgpt": ChatGPT Web on CDP port 9468 (profile: runtime/chatgpt_profile)

Whenever one engine is called:
1. Automatically detects and closes the other engine via CDP Browser.close.
2. Starts or verifies the requested engine.
3. Never runs both browsers simultaneously, saving RAM, GPU, and eliminating confusion.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
import subprocess
import time
import urllib.request
from typing import Dict, Any, Optional

try:
    from websockets.sync.client import connect
except ImportError:
    connect = None

FLOW_PORT = 9461
CHATGPT_PORT = 9468
CHATGPT_RESERVED_PORTS = set(range(9468, 9490))
ROOT_FLOWKIT = Path(__file__).resolve().parent.parent
if not (ROOT_FLOWKIT / "app").is_dir():
    ROOT_FLOWKIT = Path("D:/FLOWKIT")
STUDIO_ACCOUNTS_DB = ROOT_FLOWKIT.parent / "studio" / "runtime" / "storyboard_accounts.json"
FLOWKIT_MACHINE_JSON = ROOT_FLOWKIT / "state" / "machine.json"


def is_port_alive(port: int, timeout: float = 1.5) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=timeout) as r:
            return r.status == 200
    except Exception:
        return False


def get_browser_ws_url(port: int) -> Optional[str]:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=1.5) as r:
            data = json.load(r)
            return data.get("webSocketDebuggerUrl")
    except Exception:
        return None


def _read_json_safe(path: Path) -> Dict[str, Any]:
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return {}


def _get_active_flow_port() -> int:
    sb = _read_json_safe(STUDIO_ACCOUNTS_DB)
    active_id = sb.get("active")
    for acc in sb.get("accounts", []) or []:
        if isinstance(acc, dict) and acc.get("id") == active_id and acc.get("cdp_port"):
            p = int(acc["cdp_port"])
            if p not in CHATGPT_RESERVED_PORTS:
                return p
    mach = _read_json_safe(FLOWKIT_MACHINE_JSON)
    if mach.get("debug_port"):
        p = int(mach["debug_port"])
        if p not in CHATGPT_RESERVED_PORTS:
            return p
    return FLOW_PORT


def _get_flow_ports() -> list[int]:
    ports: list[int] = []
    sb = _read_json_safe(STUDIO_ACCOUNTS_DB)
    active_id = sb.get("active")
    for acc in sb.get("accounts", []) or []:
        if isinstance(acc, dict) and acc.get("id") == active_id and acc.get("cdp_port"):
            p = int(acc["cdp_port"])
            if p not in CHATGPT_RESERVED_PORTS and p not in ports:
                ports.append(p)
    mach = _read_json_safe(FLOWKIT_MACHINE_JSON)
    if mach.get("debug_port"):
        p = int(mach["debug_port"])
        if p not in CHATGPT_RESERVED_PORTS and p not in ports:
            ports.append(p)
    for acc in sb.get("accounts", []) or []:
        if isinstance(acc, dict) and acc.get("cdp_port"):
            p = int(acc["cdp_port"])
            if p not in CHATGPT_RESERVED_PORTS and p not in ports:
                ports.append(p)
    for p in range(9460, 9468):
        if p not in ports:
            ports.append(p)
    return ports


def _find_alive_flow_ports() -> list[int]:
    return [p for p in _get_flow_ports() if is_port_alive(p, timeout=0.7)]


def _get_chatgpt_ports() -> list[int]:
    ports = [CHATGPT_PORT]
    try:
        import chatgpt_browser
        for p in chatgpt_browser.get_registered_ports():
            if int(p) not in ports:
                ports.append(int(p))
    except Exception:
        pass
    return ports


def _find_alive_chatgpt_ports() -> list[int]:
    found: list[int] = []
    try:
        import chatgpt_browser
        rp = chatgpt_browser.get_running_port()
        if rp and is_port_alive(int(rp), timeout=0.7):
            found.append(int(rp))
    except Exception:
        pass
    for p in _get_chatgpt_ports():
        if p not in found and is_port_alive(p, timeout=0.7):
            found.append(p)
    return found


def _find_alive_chatgpt_port() -> Optional[int]:
    alive = _find_alive_chatgpt_ports()
    return alive[0] if alive else None


def _close_cdp_port(port: int, label: str, wait_timeout: float = 4.0) -> bool:
    if not port or not is_port_alive(port, timeout=0.8):
        return True
    print(f"[ORCHESTRATOR] Dang tu dong dong trinh duyet {label} (Cong {port}) de giai phong RAM...", flush=True)
    ws_url = get_browser_ws_url(port)
    if ws_url and connect:
        try:
            with connect(ws_url, open_timeout=2) as ws:
                ws.send(json.dumps({"id": 1, "method": "Browser.close"}))
        except Exception:
            pass
    start = time.time()
    while time.time() - start < wait_timeout:
        if not is_port_alive(port, timeout=0.5):
            print(f"[ORCHESTRATOR] Da dong hoan toan trinh duyet {label} (Cong {port}).", flush=True)
            return True
        time.sleep(0.3)
    try:
        ps_cmd = f"Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess"
        proc = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True, timeout=3)
        for p in (proc.stdout or "").strip().split():
            if p.isdigit() and int(p) > 0:
                subprocess.run(["taskkill", "/F", "/T", "/PID", p], capture_output=True)
    except Exception:
        pass
    return not is_port_alive(port, timeout=0.5)


def close_engine_browser(engine_name: str, wait_timeout: float = 4.0) -> bool:
    """Gracefully closes all browsers of the specified engine via CDP Browser.close."""
    engine = engine_name.lower().strip()
    if engine in ("chatgpt", "openai"):
        try:
            import chatgpt_browser
            chatgpt_browser.close_chatgpt_browser()
        except Exception:
            pass
        ok = True
        for p in _find_alive_chatgpt_ports():
            if not _close_cdp_port(p, "CHATGPT", wait_timeout=wait_timeout):
                ok = False
        return ok
    if engine == "flow":
        ok = True
        for p in _find_alive_flow_ports():
            if not _close_cdp_port(p, "FLOW", wait_timeout=wait_timeout):
                ok = False
        return ok
    return True


def ensure_exclusive_engine(target_engine: str, show_window: bool = False) -> Dict[str, Any]:
    """Switches strictly to the target engine, shutting down the opposite one first."""
    target = target_engine.lower().strip()
    if target not in ("flow", "chatgpt", "openai"):
        raise ValueError(f"Unknown engine: {target_engine}. Must be 'flow' or 'chatgpt'.")

    # 1. Mutually exclusive shutdown of the other engine across ALL registered ports
    if target == "flow":
        if _find_alive_chatgpt_ports():
            close_engine_browser("chatgpt")
    else:
        if _find_alive_flow_ports():
            close_engine_browser("flow")

    # 2. Check and start the requested engine if not yet online
    if target == "flow":
        alive_flow = _find_alive_flow_ports()
        target_port = alive_flow[0] if alive_flow else _get_active_flow_port()
    else:
        try:
            import chatgpt_browser
            target_port = chatgpt_browser.get_active_profile()[1]
        except Exception:
            target_port = CHATGPT_PORT
    if is_port_alive(target_port):
        print(f"[ORCHESTRATOR] Trinh duyet {target.upper()} da san sang tren cong {target_port}.", flush=True)
        return {"ok": True, "engine": target, "port": target_port, "status": "already_running"}

    print(f"[ORCHESTRATOR] Tu dong khoi dong trinh duyet {target.upper()} tren cong {target_port}...", flush=True)

    py_bin = sys.executable or "python"
    if py_bin.lower().endswith("pythonw.exe"):
        cand_py = Path(py_bin).with_name("python.exe")
        if cand_py.is_file():
            py_bin = str(cand_py)

    if target == "chatgpt":
        chatgpt_py = ROOT_FLOWKIT / "app" / "chatgpt_browser.py"
        args = [py_bin, "-B", str(chatgpt_py)]
        if not show_window:
            args.append("--hide")
        subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    else:
        # Flow
        flow_py = ROOT_FLOWKIT / "app" / "flow_browser.py"
        subprocess.Popen([py_bin, "-B", str(flow_py), "--ensure"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))

    # Wait up to 22s for CDP port on cold Chrome start
    for _ in range(44):
        time.sleep(0.5)
        if is_port_alive(target_port):
            print(f"[ORCHESTRATOR] {target.upper()} da ket noi thanh cong tren cong {target_port}.", flush=True)
            return {"ok": True, "engine": target, "port": target_port, "status": "started"}

    return {"ok": False, "engine": target, "port": target_port, "error": "START_TIMEOUT"}


def close_all_engines() -> None:
    """Closes all browsers to free 100% RAM and GPU."""
    close_engine_browser("chatgpt")
    close_engine_browser("flow")
    print("[ORCHESTRATOR] Da giai phong toan bo trinh duyet va tai nguyen he thong.", flush=True)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "close_all":
            close_all_engines()
        elif cmd in ("flow", "chatgpt"):
            res = ensure_exclusive_engine(cmd, show_window="--show" in sys.argv)
            print(json.dumps(res, indent=2))
    else:
        print("Usage: python engine_orchestrator.py [flow|chatgpt|close_all] [--show]")
