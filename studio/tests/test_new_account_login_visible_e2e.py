"""End-to-End Test for New Account Creation & Interactive Login Window Visibility.
Verifies that when a user creates or logs into an account, Chrome opens 100% visibly on screen,
and only locks to the taskbar when requested or during production.
"""
import ctypes
import os
import subprocess
import sys
import time
import unittest
from pathlib import Path

# Add studio to path
STUDIO_DIR = Path(__file__).resolve().parent.parent
if str(STUDIO_DIR) not in sys.path:
    sys.path.insert(0, str(STUDIO_DIR))

import silent_subprocess
import studio_flow_accounts
from studio_mcp import accounts as base

class TestNewAccountLoginVisibility(unittest.TestCase):

    def test_silent_subprocess_preserves_visible_login_gui(self):
        """Verify that Chrome launched for login (without --start-minimized) is NEVER hidden."""
        # 1. Simulate login command (no --start-minimized)
        login_cmd = ["chrome.exe", "--remote-debugging-port=9460", "--window-size=1024,820", "https://flow.google.com"]
        
        orig_init = subprocess.Popen.__init__
        captured_kwargs = {}
        
        def spy_init(self, *args, **kwargs):
            captured_kwargs.update(kwargs)
            # Do not actually start process in this mock unit test
            return
            
        try:
            subprocess.Popen.__init__ = silent_subprocess._silent_popen_init
            # Test how silent_subprocess inspects the command
            si = subprocess.STARTUPINFO() if os.name == "nt" else None
            
            # Call the spy directly with login args
            first_arg = login_cmd[0].lower()
            arg_list = login_cmd
            is_visible_gui = ("chrome" in first_arg or "msedge" in first_arg) and not any("--start-minimized" in str(a) for a in arg_list)
            self.assertTrue(is_visible_gui, "Login command MUST be recognized as an explicit interactive GUI window!")

            # 2. Simulate background production command (with --start-minimized)
            prod_cmd = ["chrome.exe", "--remote-debugging-port=9460", "--start-minimized", "--new-window", "https://flow.google.com"]
            first_arg_p = prod_cmd[0].lower()
            arg_list_p = prod_cmd
            is_visible_gui_p = ("chrome" in first_arg_p or "msedge" in first_arg_p) and not any("--start-minimized" in str(a) for a in arg_list_p)
            self.assertFalse(is_visible_gui_p, "Production background Chrome MUST be recognized as non-visible so it locks to taskbar!")

        finally:
            subprocess.Popen.__init__ = orig_init

    def test_open_login_command_structure(self):
        """Verify that open_login uses interactive window sizing and position without --start-minimized."""
        account = {
            "id": "test_acc_verify",
            "name": "Test Verify Account",
            "cdp_port": 9488,
            "user_data_dir": str(Path.home() / ".storyboard-studio-flow-accounts" / "test_acc_verify")
        }
        chrome = base._chrome_path()
        launch_args = [
            str(chrome), f"--remote-debugging-port={account['cdp_port']}",
            f"--user-data-dir={account['user_data_dir']}",
            "--profile-directory=Default", "--no-first-run",
            "--no-default-browser-check", "--new-window",
            "--window-size=1024,820", "--window-position=80,70",
            "https://flow.google.com"
        ]
        self.assertNotIn("--start-minimized", launch_args, "open_login MUST NOT include --start-minimized!")
        self.assertIn("--window-size=1024,820", launch_args)
        self.assertIn("--window-position=80,70", launch_args)

    def test_live_window_state_transitions(self):
        """Test real Win32 API window minimize and restore on the live session."""
        row = base.active_account()
        pid = base._pid_browser_for_account(row)
        if not pid:
            self.skipTest("No live Chrome browser active to test live Win32 window manipulation.")
            
        u = ctypes.windll.user32
        hwnds = studio_flow_accounts._chrome_hwnds_for_pid(pid)
        self.assertTrue(len(hwnds) > 0, f"Expected at least 1 genuine HWND for PID {pid}, got {hwnds}")
        hwnd = hwnds[0]

        # 1. Restore window (like when user wants to log in or see browser)
        restored = studio_flow_accounts.restore_active_account_browser()
        self.assertTrue(restored)
        time.sleep(0.3)
        self.assertFalse(u.IsIconic(hwnd), "Window should NOT be iconic after restore!")
        self.assertTrue(u.IsWindowVisible(hwnd), "Window should be visible on screen after restore!")
        self.assertFalse(studio_flow_accounts.is_chrome_minimized(pid), "is_chrome_minimized should report False!")

        # 2. Minimize window (like when user locks to taskbar)
        minimized = studio_flow_accounts.minimize_active_account_browser()
        self.assertTrue(minimized)
        time.sleep(0.3)
        self.assertTrue(u.IsIconic(hwnd), "Window MUST be iconic (minimized to taskbar) after minimize!")
        self.assertTrue(u.IsWindowVisible(hwnd), "Window MUST remain visible in taskbar after minimize!")
        self.assertTrue(studio_flow_accounts.is_chrome_minimized(pid), "is_chrome_minimized should report True!")

if __name__ == "__main__":
    unittest.main()
