"""Storyboard AI Studio Pro - Engine Orchestrator Bridge.
Proxies to D:/FLOWKIT/app/engine_orchestrator.py cleanly using importlib to prevent name shadowing.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FLOWKIT_ORCH = PROJECT_ROOT / "flowkit" / "app" / "engine_orchestrator.py"
if not FLOWKIT_ORCH.is_file():
    FLOWKIT_ORCH = Path("D:/FLOWKIT/app/engine_orchestrator.py")

if FLOWKIT_ORCH.is_file():
    spec = importlib.util.spec_from_file_location("flowkit_engine_orchestrator_core", FLOWKIT_ORCH)
    _core = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(_core)

    is_port_alive = _core.is_port_alive
    get_browser_ws_url = _core.get_browser_ws_url
    close_engine_browser = _core.close_engine_browser
    ensure_exclusive_engine = _core.ensure_exclusive_engine
    close_all_engines = _core.close_all_engines
    _get_active_flow_port = _core._get_active_flow_port
    _find_alive_flow_ports = _core._find_alive_flow_ports
    _find_alive_chatgpt_ports = _core._find_alive_chatgpt_ports
    FLOW_PORT = _core.FLOW_PORT
    CHATGPT_PORT = _core.CHATGPT_PORT
else:
    FLOW_PORT = 9461
    CHATGPT_PORT = 9468
    def is_port_alive(port): return False
    def get_browser_ws_url(port): return None
    def close_engine_browser(name, wait_timeout=4.0): return True
    def ensure_exclusive_engine(name, show_window=False): return {"ok": False, "error": "FLOWKIT_NOT_FOUND"}
    def close_all_engines(): pass
    def _get_active_flow_port(): return FLOW_PORT
    def _find_alive_flow_ports(): return []
    def _find_alive_chatgpt_ports(): return []

__all__ = [
    "is_port_alive",
    "get_browser_ws_url",
    "close_engine_browser",
    "ensure_exclusive_engine",
    "close_all_engines",
    "_get_active_flow_port",
    "_find_alive_flow_ports",
    "_find_alive_chatgpt_ports",
    "FLOW_PORT",
    "CHATGPT_PORT",
]
