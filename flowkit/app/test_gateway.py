import asyncio
import importlib
import json
import os
from pathlib import Path
import tempfile
import time
import unittest


class StoreTests(unittest.TestCase):
    def test_restart_preserves_idempotency_and_requires_recovery(self):
        from store import Store, Conflict
        with tempfile.TemporaryDirectory() as folder:
            first = Store(Path(folder) / "jobs.sqlite")
            payload = {"provider": "flow", "prompt": "one"}
            job, reused = first.create(payload, "stable-key")
            self.assertFalse(reused)
            claimed = first.claim("flow")
            claimed["remote"] = {"workflows": [{"name": "accepted-id"}]}
            first.save(claimed)
            second = Store(Path(folder) / "jobs.sqlite")
            second.recover()
            same, reused = second.create(payload, "stable-key")
            self.assertTrue(reused)
            self.assertEqual(same["id"], job["id"])
            self.assertEqual(same["state"], "recovery_needed")
            self.assertEqual(same["remote"], claimed["remote"])
            self.assertIsNone(second.claim("flow"))
            with self.assertRaises(Conflict):
                second.create({**payload, "prompt": "different"}, "stable-key")


class GatewayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        os.environ["FLOWMUSE_ROOT"] = cls.temp.name
        for name in ("common", "providers", "gateway"):
            if name in __import__("sys").modules:
                del __import__("sys").modules[name]
        import common
        import gateway
        cls.gateway, cls.common = gateway, common
        cls.calls = 0

        async def fake_provider(job, checkpoint):
            cls.calls += 1
            folder = common.OUTPUTS / job["id"]
            folder.mkdir(parents=True, exist_ok=True)
            path = folder / "scene.png"
            from PIL import Image
            Image.new("RGB", (16, 16), "blue").save(path)
            job["artifacts"] = [common.artifact(job["id"], path, "image")]

        gateway.run_flow = fake_provider
        # Unit tests must not launch an actual browser or the production profile.
        # Browser lifecycle is separately covered by the live E2E suite.
        gateway.ensure_browser = lambda provider: True
        gateway.close_if_safe = lambda: {"closed": True, "reason": "TEST_STUB"}
        gateway.reconcile_once = lambda: {"requeued": 0}
        from fastapi.testclient import TestClient
        cls.client_context = TestClient(gateway.app)
        cls.client = cls.client_context.__enter__()
        cls.headers = {"X-API-Key": common.api_key()}

    @classmethod
    def tearDownClass(cls):
        cls.client_context.__exit__(None, None, None)
        cls.temp.cleanup()
        os.environ.pop("FLOWMUSE_ROOT", None)

    def test_01_auth_and_capability_validation(self):
        self.assertEqual(self.client.get("/v1/jobs").status_code, 401)
        body = {"provider": "muse", "kind": "image", "prompt": "test"}
        self.assertEqual(self.client.post("/v1/jobs", json=body, headers=self.headers).status_code, 422)

    def test_02_same_key_dispatches_once_and_download_is_protected(self):
        body = {"provider": "flow", "kind": "image", "prompt": "one image"}
        headers = {**self.headers, "Idempotency-Key": "same-job"}
        before = type(self).calls
        one = self.client.post("/v1/jobs", json=body, headers=headers)
        two = self.client.post("/v1/jobs", json=body, headers=headers)
        self.assertEqual(one.status_code, 202)
        self.assertEqual(one.json()["job_id"], two.json()["job_id"])
        self.assertTrue(two.json()["reused"])
        url = one.json()["status_url"]
        for _ in range(50):
            result = self.client.get(url, headers=self.headers).json()
            if result["state"] == "succeeded":
                break
            time.sleep(0.05)
        self.assertEqual(result["state"], "succeeded")
        self.assertEqual(type(self).calls, before + 1)
        file_url = result["artifacts"][0]["download_url"]
        self.assertEqual(self.client.get(file_url).status_code, 401)
        download = self.client.get(file_url, headers=self.headers)
        self.assertEqual(download.status_code, 200)
        self.assertTrue(download.content.startswith(b"\x89PNG"))
        self.assertEqual(self.client.post("/v1/jobs", json={**body, "prompt": "different"}, headers=headers).status_code, 409)

    def test_03_unknown_submission_cannot_be_resumed(self):
        job, _ = self.gateway.store.create({"provider": "flow"}, "uncertain-submit")
        job.update(state="recovery_needed", phase="video_submitting", remote={"image_id": "a-frame"})
        self.gateway.store.save(job)
        response = self.client.post("/v1/jobs/" + job["id"] + "/resume", headers=self.headers)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(self.gateway.store.get(job["id"])["state"], "recovery_needed")


if __name__ == "__main__":
    unittest.main(verbosity=2)
