"""Regression tests for Flow & ChatGPT account switch/delete & HTTP guards (isolated temp dirs, no real profile mutation)."""
from __future__ import annotations

import json
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch

STUDIO_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = STUDIO_DIR.parent
for p in (str(STUDIO_DIR), str(ROOT_DIR / "flowkit" / "app")):
    if p not in sys.path:
        sys.path.insert(0, p)

import web_server  # noqa: E402
import studio_flow_accounts as sfa  # noqa: E402
import flow_account_manager as fam  # noqa: E402
import chatgpt_browser as cb  # noqa: E402
import chatgpt_account_manager as cam  # noqa: E402


class AccountDeleteAndSwitchTests(unittest.TestCase):
    def test_flow_delete_multi_and_last_account_resets_cleanly(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home = root / "studio"
            (home / "runtime").mkdir(parents=True, exist_ok=True)
            acc1_dir = home / "flow_accounts" / "account_111111111111"
            acc2_dir = home / "flow_accounts" / "account_222222222222"
            st1_dir = root / "state1"
            st2_dir = root / "state2"
            for d in (acc1_dir, acc2_dir, st1_dir, st2_dir):
                d.mkdir(parents=True, exist_ok=True)
            (acc1_dir / "marker.txt").write_text("old_cookie", encoding="utf-8")

            reg = {
                "version": 1,
                "active": "account_111111111111",
                "accounts": [
                    {
                        "id": "account_111111111111",
                        "name": "Flow 1",
                        "user_data_dir": str(acc1_dir),
                        "profile_directory": "Default",
                        "cdp_port": 9461,
                        "state_dir": str(st1_dir),
                    },
                    {
                        "id": "account_222222222222",
                        "name": "Flow 2",
                        "user_data_dir": str(acc2_dir),
                        "profile_directory": "Default",
                        "cdp_port": 9462,
                        "state_dir": str(st2_dir),
                    },
                ],
            }
            reg_file = home / "runtime" / "storyboard_accounts.json"
            reg_file.write_text(json.dumps(reg), encoding="utf-8")

            with patch.object(sfa, "HOME", home), \
                 patch.object(sfa, "_sync_machine_json"), \
                 patch("engine_orchestrator.close_engine_browser"), \
                 patch.object(sfa.base, "any_running_production", return_value=False), \
                 patch.object(sfa.base, "_pid_browser_for_account", return_value=0), \
                 patch.object(sfa.base, "_find_pid_by_cdp_port", return_value=0):
                # Delete active Flow 1 -> deletes folder under flow_accounts and activates Flow 2
                res1 = sfa.delete_account("account_111111111111", root=home)
                self.assertTrue(res1["ok"])
                self.assertEqual(res1["active"], "account_222222222222")
                self.assertFalse(res1["reset_clean"])
                self.assertFalse(acc1_dir.exists(), "Deleted Flow 1 profile dir must be removed")

                # Delete last remaining Flow 2 -> creates fresh clean replacement slot
                res2 = sfa.delete_account("account_222222222222", root=home)
                self.assertTrue(res2["ok"])
                self.assertTrue(res2["reset_clean"])
                self.assertEqual(res2["remaining"], 1)
                self.assertNotEqual(res2["active"], "account_222222222222")
                self.assertFalse(acc2_dir.exists(), "Deleted Flow 2 profile dir must be removed")
                after = json.loads(reg_file.read_text(encoding="utf-8"))
                self.assertEqual(len(after["accounts"]), 1)
                self.assertEqual(after["accounts"][0]["name"], "Google Flow (Mới)")

    def test_chatgpt_delete_multi_and_last_account_resets_cleanly(self):
        with tempfile.TemporaryDirectory() as tmp:
            prof_root = Path(tmp) / "profiles"
            p1 = prof_root / "chatgpt_web"
            p2 = prof_root / "chatgpt_web_2"
            p1.mkdir(parents=True, exist_ok=True)
            p2.mkdir(parents=True, exist_ok=True)
            (p1 / "cookies.db").write_text("old_session", encoding="utf-8")
            reg_path = prof_root / "chatgpt_accounts.json"
            reg_data = {
                "active_id": "cgpt_2",
                "accounts": [
                    {"id": "cgpt_1", "label": "Tài khoản 1", "profile_dir": str(p1), "port": 9468, "email": "a@example.com", "logged_in": True, "cooldown_until": 0, "last_error": ""},
                    {"id": "cgpt_2", "label": "Tài khoản 2", "profile_dir": str(p2), "port": 9469, "email": "b@example.com", "logged_in": True, "cooldown_until": 0, "last_error": ""},
                ],
            }
            reg_path.write_text(json.dumps(reg_data), encoding="utf-8")

            with patch.object(cb, "PROFILES_ROOT", prof_root), \
                 patch.object(cb, "CHATGPT_PROFILE", p1), \
                 patch.object(cb, "ACCOUNTS_REGISTRY", reg_path), \
                 patch.object(cb, "_is_port_alive", return_value=False):
                r1 = cb.delete_chatgpt_account("cgpt_2")
                self.assertTrue(r1["success"])
                self.assertEqual(r1["active_id"], "cgpt_1")
                self.assertFalse(r1["reset_clean"])
                self.assertFalse(p2.exists())

                r2 = cb.delete_chatgpt_account("cgpt_1")
                self.assertTrue(r2["success"])
                self.assertTrue(r2["reset_clean"])
                self.assertEqual(r2["active_id"], "cgpt_1")
                self.assertEqual(r2["total_accounts"], 1)
                self.assertFalse((p1 / "cookies.db").exists(), "Old session must be wiped cleanly")
                st = json.loads((p1 / "login_state.json").read_text(encoding="utf-8"))
                self.assertFalse(st["logged_in"])

    def test_http_delete_and_running_guard(self):
        srv = web_server.ThreadedHTTPServer(("127.0.0.1", 0), web_server.StudioRequestHandler)
        port = srv.server_address[1]
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        old_run = web_server.job_status.get("running", False)
        try:
            # Running guard returns 409 for both delete endpoints
            web_server.job_status["running"] = True
            for route in ("/api/flow/delete_account", "/api/chatgpt/delete_account"):
                req = urllib.request.Request(
                    f"http://127.0.0.1:{port}{route}",
                    data=json.dumps({"account_id": "x"}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with self.assertRaises(urllib.error.HTTPError) as ctx:
                    urllib.request.urlopen(req, timeout=5)
                self.assertEqual(ctx.exception.code, 409)

            # Idle calls delegate cleanly to managers
            web_server.job_status["running"] = False
            with patch.object(fam, "delete_flow_account", return_value={"success": True, "deleted": "acc1", "message": "ok"}) as m_flow, \
                 patch.object(cam, "delete_chatgpt_account_ui", return_value={"success": True, "deleted": "cgpt_1", "message": "ok"}) as m_cgpt:
                r_f = urllib.request.urlopen(urllib.request.Request(
                    f"http://127.0.0.1:{port}/api/flow/delete_account",
                    data=json.dumps({"account_id": "acc1"}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                ), timeout=5)
                self.assertEqual(json.loads(r_f.read())["deleted"], "acc1")
                m_flow.assert_called_once_with(account_id="acc1")

                r_c = urllib.request.urlopen(urllib.request.Request(
                    f"http://127.0.0.1:{port}/api/chatgpt/delete_account",
                    data=json.dumps({"account_id": "cgpt_1"}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                ), timeout=5)
                self.assertEqual(json.loads(r_c.read())["deleted"], "cgpt_1")
                m_cgpt.assert_called_once_with("cgpt_1")
        finally:
            web_server.job_status["running"] = old_run
            srv.shutdown()
            srv.server_close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
