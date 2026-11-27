"""Shared safe loader for east_asia_story_lab.studio_bridge inside Studio."""
from __future__ import annotations

from pathlib import Path
import sys
from typing import Optional

_CACHED_BRIDGE = None
_TRIED = False


def get_ea_bridge():
    """Returns east_asia_story_lab.studio_bridge if available, else None without breaking Studio."""
    global _CACHED_BRIDGE, _TRIED
    if _TRIED:
        return _CACHED_BRIDGE
    _TRIED = True
    try:
        root_dir = Path(__file__).resolve().parent.parent
        if str(root_dir) not in sys.path:
            sys.path.insert(0, str(root_dir))
        from east_asia_story_lab import studio_bridge
        _CACHED_BRIDGE = studio_bridge
    except Exception:
        _CACHED_BRIDGE = None
    return _CACHED_BRIDGE
