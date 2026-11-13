"""Silent Subprocess Enforcer for Storyboard AI Studio & FlowKit on Windows.
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
            arg_list = list(cmd_args) if isinstance(cmd_args, (list, tuple)) else [str(cmd_args)]
            
            # Interactive Chrome/Edge for login or desktop browser: only if NOT headless/off-screen/minimized
            is_offscreen = any("--window-position=-32000" in str(a) or "--start-minimized" in str(a) or "--headless" in str(a) for a in arg_list)
            if ("chrome" in first_arg or "msedge" in first_arg) and not is_offscreen:
                is_explicit_visible_gui = True

            # If PowerShell is invoked, ensure -WindowStyle Hidden is passed
            if "powershell" in first_arg and isinstance(cmd_args, list):
                if not any("-windowstyle" in str(a).lower() for a in arg_list):
                    new_args = [cmd_args[0], "-WindowStyle", "Hidden"] + cmd_args[1:]
                    if args:
                        args = (new_args,) + args[1:]
                    else:
                        kwargs["args"] = new_args

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
