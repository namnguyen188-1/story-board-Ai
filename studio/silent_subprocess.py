"""Silent Subprocess Enforcer for Storyboard AI Studio on Windows.
Guarantees ZERO console window flashing, zero CMD flickers, and zero PowerShell popups
across all background operations, yt_dlp, ffmpeg, ffprobe, and Python subroutines,
while preserving visible GUI interactive windows (like Google login and desktop app).
"""
from __future__ import annotations

import os
import sys
import subprocess

CREATE_NO_WINDOW = 0x08000000
STARTF_USESHOWWINDOW = 0x00000001
SW_HIDE = 0

_orig_popen_init = subprocess.Popen.__init__

def _silent_popen_init(self, *args, **kwargs):
    if sys.platform == "win32":
        cmd_args = args[0] if args else kwargs.get("args")
        is_explicit_visible_gui = False
        if cmd_args:
            first_arg = str(cmd_args[0] if isinstance(cmd_args, (list, tuple)) else cmd_args).lower()
            arg_list = cmd_args if isinstance(cmd_args, (list, tuple)) else [str(cmd_args)]
            # If launching Chrome/Edge WITHOUT --start-minimized, it is an explicit interactive GUI window (e.g. login)
            if ("chrome" in first_arg or "msedge" in first_arg) and not any("--start-minimized" in str(a) for a in arg_list):
                is_explicit_visible_gui = True

        if not is_explicit_visible_gui:
            flags = kwargs.get("creationflags", 0)
            flags |= CREATE_NO_WINDOW
            kwargs["creationflags"] = flags

            si = kwargs.get("startupinfo")
            if si is None:
                si = subprocess.STARTUPINFO()
                si.dwFlags |= STARTF_USESHOWWINDOW
                si.wShowWindow = SW_HIDE
                kwargs["startupinfo"] = si
            else:
                if not (si.dwFlags & STARTF_USESHOWWINDOW):
                    si.dwFlags |= STARTF_USESHOWWINDOW
                    si.wShowWindow = SW_HIDE

    return _orig_popen_init(self, *args, **kwargs)

def patch_silent_subprocess():
    """Globally hooks subprocess.Popen so all Windows subroutines run with zero visible windows."""
    if sys.platform == "win32":
        if getattr(subprocess.Popen, "_is_silenced", False):
            return
        subprocess.Popen.__init__ = _silent_popen_init
        subprocess.Popen._is_silenced = True

        try:
            import yt_dlp.utils
            if hasattr(yt_dlp.utils, "Popen"):
                si = subprocess.STARTUPINFO()
                si.dwFlags |= STARTF_USESHOWWINDOW
                si.wShowWindow = SW_HIDE
                yt_dlp.utils.Popen._startupinfo = si
        except Exception:
            pass

# Auto-apply on import
patch_silent_subprocess()
