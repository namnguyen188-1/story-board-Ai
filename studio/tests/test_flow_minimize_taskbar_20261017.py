"""Minimize the existing Chrome window without hiding it or changing focus."""
import sys, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import studio_flow_accounts as sf
class TaskbarTests(unittest.TestCase):
    def test_minimize_preserves_taskbar_window_without_restore_or_hide(self):
        with patch.object(sf,"_attach_desktop"), \
             patch.object(sf,"_chrome_hwnds_for_pid",return_value=[101,102]), \
             patch("ctypes.windll.user32.ShowWindow") as show:
            self.assertTrue(sf.minimize_chrome_window(123))
        self.assertEqual(show.call_args_list,[((101,7),),((102,7),)],
                         "Use SW_SHOWMINNOACTIVE=7 only; never SW_HIDE or focus activation")
    def test_no_owned_window_does_not_claim_success(self):
        with patch.object(sf,"_attach_desktop"), \
             patch.object(sf,"_chrome_hwnds_for_pid",return_value=[]), \
             patch("ctypes.windll.user32.ShowWindow") as show:
            self.assertFalse(sf.minimize_chrome_window(123))
            show.assert_not_called()
if __name__=="__main__":unittest.main()
