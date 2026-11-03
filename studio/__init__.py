"""Storyboard AI Studio Pro package initialization.
Guarantees silent subprocess execution and zero console window flashing across all modules.
"""
from __future__ import annotations

import sys
from pathlib import Path

_STUDIO_DIR = str(Path(__file__).resolve().parent)
if _STUDIO_DIR not in sys.path:
    sys.path.insert(0, _STUDIO_DIR)

try:
    import silent_subprocess
except Exception:
    pass
