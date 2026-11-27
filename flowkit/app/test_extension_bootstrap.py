"""No paid requests. Chrome test uses a fresh profile and isolated bridge ports."""
import json
from pathlib import Path
import shutil
import subprocess
import time
import unittest
import urllib.request

from common import ROOT, STATE, atomic
from extension_bootstrap import ensure_extension, BrowserCDP, ExtensionBootstrapError
from flow_browser import machine


class ChromeInstallTest(unittest.TestCase):
    def test_fresh_profile_install_and_reuse(self):
        chrome, _, _ = machine()
        work = STATE / "extension_install_test"
        work.mkdir(exist_ok=True)
        directory = work / "extension"
        shutil.copytree(ROOT / "extensions" / "flow", directory, dirs_exist_ok=True)
        # This fixture must never connect to the live production bridge.
        background = directory / "background.js"
        background.write_text(background.read_text(encoding="utf-8").replace("127.0.0.1:9222", "127.0.0.1:19222").replace("127.0.0.1:8100", "127.0.0.1:18100"), encoding="utf-8")
        profile = work / "profile"
        self.assertFalse(profile.exists(), "Test requires a clean profile")
        process = subprocess.Popen([str(chrome), "--user-data-dir=" + str(profile), "--remote-debugging-address=127.0.0.1",
            "--remote-debugging-port=0", "--no-first-run", "--no-default-browser-check", "--window-position=-32000,-32000", "about:blank"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        port = None
        try:
            port_file = profile / "DevToolsActivePort"
            for _ in range(80):
                if port_file.is_file():
                    port = int(port_file.read_text().splitlines()[0])
                    break
                time.sleep(0.25)
            self.assertIsNotNone(port)
            cdp = BrowserCDP(port)
            before = cdp.call("Extensions.getExtensions").get("extensions", [])
            cdp.close()
            self.assertFalse(any(x.get("name") == "Flow Kit" for x in before))
            # Verify active-job protection before installation.
            with self.assertRaisesRegex(ExtensionBootstrapError, "FLOW_JOBS_ACTIVE"):
                ensure_extension(port, directory, can_install=lambda: False)
            installed = ensure_extension(port, directory)
            self.assertEqual(installed["mode"], "installed")
            self.assertTrue(installed["enabled"])
            second = ensure_extension(port, directory)
            self.assertEqual(second["mode"], "reused")
            self.assertEqual(second["id"], installed["id"])
            cdp = BrowserCDP(port)
            records = cdp.call("Extensions.getExtensions")["extensions"]
            cdp.close()
            self.assertEqual(sum(x.get("name") == "Flow Kit" and x.get("enabled") for x in records), 1)
            cdp = BrowserCDP(port)
            cdp.call("Browser.close")
            cdp.close()
            process.wait(timeout=15)
            port_file.unlink(missing_ok=True)
            process = subprocess.Popen([str(chrome), "--user-data-dir=" + str(profile),
                "--remote-debugging-address=127.0.0.1", "--remote-debugging-port=0", "--no-first-run",
                "--no-default-browser-check", "--window-position=-32000,-32000", "about:blank"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            port = None
            for _ in range(80):
                if port_file.is_file():
                    port = int(port_file.read_text().splitlines()[0])
                    break
                time.sleep(0.25)
            self.assertIsNotNone(port)
            restarted = ensure_extension(port, directory)
            self.assertIn(restarted["mode"], {"installed", "reused"})
            self.assertTrue(restarted["enabled"])
            self.assertEqual(restarted["id"], installed["id"])
            cdp = BrowserCDP(port)
            records = cdp.call("Extensions.getExtensions")["extensions"]
            cdp.close()
            self.assertEqual(sum(x.get("name") == "Flow Kit" and x.get("enabled") for x in records), 1)
            atomic(STATE / "extension_install_test.json", {"ok": True, "fresh_profile": True,
                "installed_without_ui": True, "enabled": True, "second_start_reused_same_id": True,
                "active_job_protection": True, "browser_restart_automatically_ready": True, "browser_restart_mode": restarted["mode"], "enabled_flow_extension_count": 1, "paid_requests": 0})
        finally:
            if port:
                try:
                    cdp = BrowserCDP(port)
                    cdp.call("Browser.close")
                    cdp.close()
                except Exception:
                    pass
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.terminate()
                process.wait(timeout=10)
            for attempt in range(30):
                try:
                    shutil.rmtree(work)
                    break
                except OSError:
                    time.sleep(0.5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
