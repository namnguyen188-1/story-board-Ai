"""Regression & E2E verification for:
1) Zero-spam single-thumbnail guarantee (no polling / concurrent / duplicate ChatGPT prompts).
2) /api/episode/seo read_only & mid-production guards + parse_progress corruption guard.
3) /api/produce flowkit & cinematic_drama routing without spurious 409 blockers.
4) Real end-to-end offline video creation through pipeline_router.py.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

STUDIO_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = STUDIO_DIR.parent
for p in (str(ROOT_DIR), str(STUDIO_DIR), str(STUDIO_DIR / "engine"), str(ROOT_DIR / "flowkit" / "app")):
    if p not in sys.path:
        sys.path.insert(0, p)

import seo_packager as seo  # noqa: E402
import web_server  # noqa: E402
import chatgpt_webtool  # noqa: E402


class VideoWorkflowAndNoSpamE2ETests(unittest.TestCase):
    def _make_episode(self, root: Path, series: str = "TestSeries", ep: int = 1) -> Path:
        ep_dir = root / "productions" / series / f"episode_{ep:03d}"
        ep_dir.mkdir(parents=True, exist_ok=True)
        plan = {
            "config": {
                "series": series,
                "episode": ep,
                "language": "English",
                "genre": "drama",
                "image_provider": "comfyui",
            },
            "title": "Cold Discipline on the Frontier",
            "logline": "A frontier cook stands firm in a sudden blizzard.",
            "bible": {
                "characters": [
                    {
                        "name": "Matthew",
                        "appearance": "Bearded frontier rider",
                        "attire": "Leather western jacket and hat",
                    }
                ]
            },
            "scenes": [
                {
                    "scene_number": i,
                    "summary": f"Frontier scene {i} during blizzard.",
                    "narration": f"In scene {i}, the storm deepens across the wooden ranch.",
                }
                for i in range(1, 4)
            ],
        }
        (ep_dir / "plan.json").write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
        for i in range(1, 4):
            sd = ep_dir / "scenes" / f"scene_{i:04d}"
            sd.mkdir(parents=True, exist_ok=True)
            (sd / "result.json").write_text(json.dumps({"qc": {"duration_seconds": 12.0}}), encoding="utf-8")
            Image.new("RGB", (1280, 720), (30 * i, 60, 120)).save(sd / "image.png")
        return ep_dir

    def test_single_thumbnail_and_concurrency_no_spam(self):
        calls = []

        def fake_chatgpt(prompt, output_path, timeout_seconds=180):
            calls.append(str(output_path))
            out_p = Path(output_path)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (1536, 1024), (24, 32, 48)).save(out_p, format="PNG")
            return {
                "ok": True,
                "output_file": str(out_p),
                "backend": "chatgpt_web",
                "width": 1536,
                "height": 1024,
            }

        mock_content = (
            {
                "primary_keyword": "frontier blizzard",
                "titles": [
                    {"type": "High-CTR", "title": "Cold Discipline 1"},
                    {"type": "Curiosity Hook", "title": "Cold Discipline 2"},
                    {"type": "Authority Rule", "title": "Cold Discipline 3"},
                ],
                "description_hook": "A frontier cook stands firm.",
                "story_synopsis": "A frontier cook stands firm in a sudden blizzard.",
                "tags": ["frontier", "blizzard"],
                "hashtags": ["#frontier"],
                "thumbnail_hook_text": "RACE AGAINST ICE",
                "pinned_comment": "",
            },
            {"method": "mock_grounded"},
            False,
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ep_dir = self._make_episode(root)
            with patch.object(seo, "STUDIO_DIR", root), \
                 patch.object(seo, "_load_or_create_content", return_value=mock_content), \
                 patch("engine_orchestrator.ensure_exclusive_engine", return_value={"ok": True, "engine": "chatgpt"}), \
                 patch.object(chatgpt_webtool, "generate_thumbnail_via_chatgpt_web", side_effect=fake_chatgpt), \
                 patch.dict(os.environ, {"STORYBOARD_OFFLINE": "1"}, clear=False):
                # 1) Five concurrent callers simulate pollStatus + background triggers at once
                results = []
                errors = []

                def worker():
                    try:
                        r = seo.generate_seo_package(
                            episode_dir=ep_dir,
                            series_name="TestSeries",
                            episode_num=1,
                            language="English",
                            genre="drama",
                            force_regenerate=True,
                            explicit_regen=False,
                        )
                        results.append(r)
                    except Exception as exc:
                        errors.append(exc)

                threads = [threading.Thread(target=worker) for _ in range(5)]
                for t in threads:
                    t.start()
                for t in threads:
                    t.join(timeout=60)

                self.assertFalse(errors, f"Unexpected errors: {errors}")
                self.assertEqual(len(results), 5)
                self.assertEqual(len(calls), 1, f"Expected strictly 1 ChatGPT call across 5 concurrent callers, got {len(calls)}")

                # 2) Automated end-of-episode call with force_regenerate=True & explicit_regen=False must NOT re-call ChatGPT
                r2 = seo.generate_seo_package(
                    episode_dir=ep_dir,
                    series_name="TestSeries",
                    episode_num=1,
                    language="English",
                    genre="drama",
                    force_regenerate=True,
                    explicit_regen=False,
                )
                self.assertEqual(len(calls), 1, "Automated caller must reuse same-plan AI thumbnail")
                self.assertTrue(Path(r2["thumbnail_file"]).is_file())

                # 3) Explicit user regenerate button MUST be allowed to generate +1
                r3 = seo.generate_seo_package(
                    episode_dir=ep_dir,
                    series_name="TestSeries",
                    episode_num=1,
                    language="English",
                    genre="drama",
                    force_regenerate=True,
                    explicit_regen=True,
                )
                self.assertEqual(len(calls), 2, "Explicit user regen must generate once cleanly")
                self.assertTrue(Path(r3["thumbnail_file"]).is_file())

    def test_parse_progress_ignores_interleaved_4824(self):
        web_server.job_status["total_scenes"] = 48
        web_server.job_status["current_scene"] = 24
        web_server.parse_progress("SCENE_START 27/4824")
        self.assertEqual(web_server.job_status["total_scenes"], 48)
        web_server.parse_progress("SCENE_START 27/48")
        self.assertEqual(web_server.job_status["total_scenes"], 48)
        self.assertEqual(web_server.job_status["current_scene"], 27)

    def test_offline_video_pipeline_e2e(self):
        py_exe = STUDIO_DIR / "runtime" / "python" / "python.exe"
        self.assertTrue(py_exe.is_file(), f"Missing portable python: {py_exe}")
        series = "WorkflowVerifyE2E - Offline Test"
        ep_dir = STUDIO_DIR / "productions" / "WorkflowVerifyE2E---Offline-Test" / "episode_001"
        for leftover in (
            STUDIO_DIR / "productions" / "workflowverifye2e",
            STUDIO_DIR / "productions" / "workflowverifye2e-offline-test",
            ep_dir.parent,
        ):
            if leftover.exists():
                shutil.rmtree(leftover, ignore_errors=True)
        try:
            cmd = [
                str(py_exe),
                "-u",
                str(STUDIO_DIR / "pipeline_router.py"),
                "run",
                "--production-mode",
                "narrative",
                "--mode",
                "offline",
                "--series",
                series,
                "--episode",
                "1",
                "--prompt",
                "A samurai walks calmly through falling bamboo leaves at dawn.",
                "--minutes",
                "0.15",
                "--scene-seconds",
                "5",
                "--size",
                "640x360",
                "--language",
                "English",
                "--genre",
                "drama",
                "--image-provider",
                "comfyui",
                "--no-shorts",
                "--no-auto-upload",
            ]
            proc = subprocess.run(cmd, cwd=str(STUDIO_DIR), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
            self.assertEqual(proc.returncode, 0, f"Offline pipeline failed:\nSTDOUT:\n{proc.stdout[-2000:]}\nSTDERR:\n{proc.stderr[-1500:]}")
            final_mp4 = ep_dir / "episode_final.mp4"
            self.assertTrue(final_mp4.is_file() and final_mp4.stat().st_size > 10000, f"Missing/empty final mp4: {final_mp4}")
            self.assertIn("EPISODE_RESULT", proc.stdout)
        finally:
            if ep_dir.parent.exists():
                shutil.rmtree(ep_dir.parent, ignore_errors=True)

    def test_http_seo_readonly_and_produce_routing(self):
        import urllib.request
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ep_dir = self._make_episode(root, series="HttpTestSeries", ep=1)
            prod_root = root / "productions"
            seo_calls = []
            launched_cmds = []

            def fake_gen_seo(*args, **kwargs):
                seo_calls.append(kwargs)
                return {"ok": True, "best_title": "Mock Title"}

            def fake_worker(cmd, *args, **kwargs):
                launched_cmds.append(list(cmd))
                web_server.job_status["running"] = False

            srv = web_server.ThreadedHTTPServer(("127.0.0.1", 0), web_server.StudioRequestHandler)
            port = srv.server_address[1]
            t = threading.Thread(target=srv.serve_forever, daemon=True)
            t.start()
            old_running = web_server.job_status.get("running", False)
            old_series = web_server.job_status.get("series")
            old_ep = web_server.job_status.get("episode")
            try:
                with patch.object(web_server, "PRODUCTIONS_DIR", prod_root), \
                     patch.object(seo, "generate_seo_package", side_effect=fake_gen_seo), \
                     patch.object(web_server, "worker_thread", side_effect=fake_worker):
                    # A) read_only=1 on missing pack returns pending without generating
                    with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/episode/seo?series=HttpTestSeries&episode=1&read_only=1", timeout=5) as r:
                        d1 = json.loads(r.read().decode("utf-8"))
                    self.assertTrue(d1.get("pending"), f"Expected pending on read_only=1: {d1}")
                    self.assertEqual(len(seo_calls), 0)

                    # B) Passive GET while same episode is running returns pending without generating
                    web_server.job_status.update({"running": True, "series": "HttpTestSeries", "episode": 1})
                    with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/episode/seo?series=HttpTestSeries&episode=1", timeout=5) as r:
                        d2 = json.loads(r.read().decode("utf-8"))
                    self.assertTrue(d2.get("pending") and d2.get("producing"), f"Expected pending+producing while running: {d2}")
                    self.assertEqual(len(seo_calls), 0)
                    web_server.job_status["running"] = False

                    # C) POST /api/produce with image_provider='flowkit' must NOT be blocked by legacy AUTO_FLOW_NOT_READY
                    req_fk = urllib.request.Request(
                        f"http://127.0.0.1:{port}/api/produce",
                        data=json.dumps({
                            "series": "HttpFlowkitTest",
                            "episode": 1,
                            "prompt": "A quiet Zen garden at dawn under pine trees.",
                            "mode": "live",
                            "image_provider": "flowkit",
                            "minutes": 1.0,
                            "scene_seconds": 8,
                            "mcp_max_images": 10,
                        }).encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    with urllib.request.urlopen(req_fk, timeout=10) as r:
                        res_fk = json.loads(r.read().decode("utf-8"))
                    self.assertEqual(res_fk.get("status"), "STARTED", f"flowkit failed to start: {res_fk}")
                    time.sleep(0.2)

                    # D) POST /api/produce with production_mode='cinematic_drama' & no image_provider must NOT trap in 409 MUSE_AUTH_REQUIRED
                    web_server.job_status["running"] = False
                    req_dr = urllib.request.Request(
                        f"http://127.0.0.1:{port}/api/produce",
                        data=json.dumps({
                            "series": "HttpDramaTest",
                            "episode": 1,
                            "prompt": "A lone sheriff confronts corruption in a frontier town.",
                            "mode": "live",
                            "production_mode": "cinematic_drama",
                            "minutes": 1.0,
                            "scene_seconds": 10,
                        }).encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    with urllib.request.urlopen(req_dr, timeout=10) as r:
                        res_dr = json.loads(r.read().decode("utf-8"))
                    self.assertEqual(res_dr.get("status"), "STARTED", f"cinematic_drama failed to start: {res_dr}")
                    time.sleep(0.2)
                    self.assertGreaterEqual(len(launched_cmds), 2)

                    # E) Incomplete existing episode + conflicting new prompt must return 409 EPISODE_CONFLICT
                    # WITHOUT launching mcp_v2 Chrome or overwriting old prompt
                    import urllib.error
                    import studio_mcp.accounts as sm_accounts
                    import studio_mcp.transport as sm_transport
                    import studio_mcp.auto_flow_manager as sm_afm
                    req_conflict = urllib.request.Request(
                        f"http://127.0.0.1:{port}/api/produce",
                        data=json.dumps({
                            "series": "HttpTestSeries",
                            "episode": 1,
                            "prompt": "A completely different astronaut rescue story in deep space.",
                            "mode": "live",
                            "image_provider": "mcp_v2",
                            "minutes": 1.0,
                            "scene_seconds": 8,
                            "mcp_max_images": 10,
                        }).encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    with patch.object(sm_accounts, "active_account", return_value={"id": "acc_test", "profile_dir": "D:/STORYBOARD_AI/studio/flow_accounts/account_test"}), \
                         patch.object(sm_accounts, "account_tool_url", return_value="https://labs.google/fx/tools/flow/project/test"), \
                         patch.object(sm_transport, "_isolated", return_value=True), \
                         patch.object(sm_afm, "ensure_ready", side_effect=AssertionError("Must fail with EPISODE_CONFLICT before Chrome launch")):
                        with self.assertRaises(urllib.error.HTTPError) as ctx_err:
                            urllib.request.urlopen(req_conflict, timeout=5)
                    self.assertEqual(ctx_err.exception.code, 409)
                    err_body = json.loads(ctx_err.exception.read().decode("utf-8"))
                    self.assertEqual(err_body.get("code"), "EPISODE_CONFLICT", f"Unexpected error body: {err_body}")
            finally:
                web_server.job_status.update({"running": old_running, "series": old_series, "episode": old_ep})
                srv.shutdown()
                srv.server_close()

    def test_chatgpt_timeout_rotates_and_fallback_renders_local_cover(self):
        import chatgpt_browser
        attempts = []

        def fake_once(prompt, out_file, timeout_seconds=180):
            attempts.append(timeout_seconds)
            if len(attempts) == 1:
                return {"ok": False, "error": "IMAGE_GENERATION_TIMEOUT"}
            out_file.parent.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (1024, 1536), (18, 26, 44)).save(out_file, format="PNG")
            return {"ok": True, "output_file": str(out_file), "backend": "chatgpt_web", "width": 1024, "height": 1536}

        with tempfile.TemporaryDirectory() as tmp:
            out_img = Path(tmp) / "rot_thumb.png"
            with patch.object(chatgpt_browser, "list_accounts", return_value=[{"id": "cgpt_2"}, {"id": "cgpt_3"}]), \
                 patch.object(chatgpt_browser, "rotate_chatgpt_account", return_value={"id": "cgpt_2", "label": "TK 2", "port": 9469}) as m_rot, \
                 patch.object(chatgpt_browser, "close_chatgpt_browser", return_value=None), \
                 patch.object(chatgpt_webtool, "_acquire_chatgpt_global_lock", return_value=True), \
                 patch.object(chatgpt_webtool, "_release_chatgpt_global_lock", return_value=None), \
                 patch.object(chatgpt_webtool, "_generate_once", side_effect=fake_once):
                res = chatgpt_webtool.generate_thumbnail_via_chatgpt_web("Test cover", out_img, timeout_seconds=30)
            self.assertTrue(res.get("ok"), res)
            self.assertEqual(len(attempts), 2)
            m_rot.assert_called_once()

        # When ALL ChatGPT accounts fail and ComfyUI is offline, must fall back to local scene 3D typography cover
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ep_dir = self._make_episode(root, series="FallbackSeries", ep=1)
            # Replace solid placeholder with realistic textured frame (>5 KB)
            grad = Image.effect_noise((1080, 1920), 64).convert("RGB")
            grad.save(ep_dir / "scenes" / "scene_0001" / "image.png")
            with patch.object(seo, "STUDIO_DIR", root), \
                 patch("engine_orchestrator.ensure_exclusive_engine", return_value={"ok": True}), \
                 patch.object(chatgpt_webtool, "generate_thumbnail_via_chatgpt_web", return_value={"ok": False, "error": "IMAGE_GENERATION_TIMEOUT"}), \
                 patch("comfyui_image_provider.ensure_server", side_effect=RuntimeError("ComfyUI offline")):
                th_res = seo.generate_thumbnail_with_flow(
                    episode_dir=ep_dir,
                    series_name="FallbackSeries",
                    genre="stoic",
                    hook_text="DOMINA TU ADVERSIDAD",
                    aspect_ratio="9:16",
                    force_regenerate=True,
                    explicit_regen=True,
                )
            self.assertTrue(th_res.get("ok"), th_res)
            self.assertTrue(Path(th_res["thumbnail_file"]).is_file(), th_res)

    def test_landscape_thumbnail_prompts_forbid_black_split_panels(self):
        import thumbnail_studio
        captured_prompts = []

        def fake_cgpt(prompt, out_file, timeout_seconds=180):
            captured_prompts.append(prompt)
            out_file.parent.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (1536, 1024), (195, 130, 72)).save(out_file, format="PNG")
            return {"ok": True, "output_file": str(out_file), "backend": "chatgpt_web"}

        forbidden_phrases = (
            "STRICT 50/50 SPLIT",
            "dark high-contrast negative space",
            "in deep shadow",
            "dark chiaroscuro horizon",
        )
        for idx, g_name in enumerate(("drama", "western", "stoic", "whiteboard", "documentary"), start=1):
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                ep_dir = self._make_episode(root, series=f"Thumb_{g_name}", ep=idx)
                plan_path = ep_dir / "plan.json"
                plan_obj = json.loads(plan_path.read_text(encoding="utf-8"))
                plan_obj["genre"] = g_name
                plan_path.write_text(json.dumps(plan_obj), encoding="utf-8")
                with patch.object(seo, "STUDIO_DIR", root), \
                     patch("engine_orchestrator.ensure_exclusive_engine", return_value={"ok": True}), \
                     patch.object(chatgpt_webtool, "generate_thumbnail_via_chatgpt_web", side_effect=fake_cgpt):
                    got = seo.generate_thumbnail_with_flow(
                        episode_dir=ep_dir,
                        series_name=f"Thumb_{g_name}",
                        genre=g_name,
                        hook_text="NEVER BEG FOR RESPECT",
                        aspect_ratio="16:9",
                        engine="chatgpt_web",
                        force_regenerate=True,
                        explicit_regen=True,
                    )
                self.assertTrue(got.get("ok"), got)
        self.assertEqual(len(captured_prompts), 5)
        for p_txt in captured_prompts:
            self.assertIn("SEAMLESS SINGLE CONTINUOUS 16:9 SCENE", p_txt)
            self.assertIn("NO solid black half", p_txt)
            for bad in forbidden_phrases:
                self.assertNotIn(bad, p_txt, f"Unexpected black/split phrasing {bad!r} in prompt")

        for g_name in ("stoic", "family_drama", "western", "documentary", "action", "history", "psychological_horror"):
            locked_p = thumbnail_studio.build_locked_thumbnail_prompt(g_name, title="Test Story", char_desc="hero")
            self.assertIn("single continuous environment edge-to-edge", locked_p)
            for bad in ("dark negative space", "empty dark space", "deep black high-contrast negative space", "deep obsidian atmospheric negative space"):
                self.assertNotIn(bad.lower(), locked_p.lower())

    def test_local_ambient_backdrop_preserves_scenic_brightness(self):
        import numpy as np
        import thumbnail_studio
        warm_scene = Image.new("RGB", (1280, 720), (220, 140, 60))
        out = thumbnail_studio._apply_ambient_text_backdrop(
            warm_scene, text_on_left=True, genre="drama", target_w=1280, target_h=720
        )
        arr = np.array(out, dtype=np.float32)
        left_strip_mean_r = float(arr[:, :300, 0].mean())
        self.assertGreater(left_strip_mean_r, 165.0, f"Backdrop overly darkened left strip R={left_strip_mean_r}")

    def test_chatgpt_chrome_launches_hidden_when_show_false_and_visible_when_show_true(self):
        import subprocess
        import chatgpt_browser

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bat = root / "launch_chatgpt.bat"
            prof = root / "prof_1"
            fake_acc = {"id": "cgpt_t", "label": "Test TK", "profile_dir": str(prof), "port": 9485}
            with patch.object(chatgpt_browser, "BAT_LAUNCHER", bat), \
                 patch.object(chatgpt_browser, "get_active_profile", return_value=(prof, 9485, "cgpt_t")), \
                 patch.object(chatgpt_browser, "get_active_account", return_value=fake_acc), \
                 patch.object(chatgpt_browser, "get_registered_ports", return_value=[9485]), \
                 patch.object(chatgpt_browser, "_is_port_alive", side_effect=[False, True, False, True]), \
                 patch.object(chatgpt_browser, "_hide_chatgpt_window") as m_hide, \
                 patch.object(chatgpt_browser, "_force_show_chatgpt_window") as m_show, \
                 patch.object(subprocess, "run"), \
                 patch("time.sleep"):
                res_hidden = chatgpt_browser.open_chatgpt_browser(show=False)
                bat_hidden = bat.read_text(encoding="utf-8")
                self.assertTrue(res_hidden.get("hidden"), res_hidden)
                self.assertIn('start "" /min', bat_hidden)
                self.assertIn("--window-position=-32000,-32000", bat_hidden)
                self.assertIn("--disable-background-timer-throttling", bat_hidden)
                self.assertGreaterEqual(m_hide.call_count, 1)
                self.assertEqual(m_show.call_count, 0)

                m_hide.reset_mock()
                m_show.reset_mock()
                res_vis = chatgpt_browser.open_chatgpt_browser(show=True)
                bat_vis = bat.read_text(encoding="utf-8")
                self.assertFalse(res_vis.get("hidden"), res_vis)
                self.assertNotIn('start "" /min', bat_vis)
                self.assertIn("--window-position=120,80", bat_vis)
                self.assertEqual(m_show.call_count, 1)
                self.assertEqual(m_hide.call_count, 0)

    def test_chatgpt_deletes_temporary_chat_only_after_image_saved(self):
        import io
        import chatgpt_browser

        buf = io.BytesIO()
        Image.new("RGB", (512, 512), (200, 140, 80)).save(buf, format="PNG")
        valid_png = buf.getvalue()
        assert len(valid_png) > 500 or True

        # Ensure >= 5000 bytes PNG using noise so _validate_image_bytes passes realistically
        buf2 = io.BytesIO()
        Image.effect_noise((512, 512), 50).convert("RGB").save(buf2, format="PNG")
        valid_png = buf2.getvalue()
        self.assertGreater(len(valid_png), 5000)

        fake_tab = {"webSocketDebuggerUrl": "ws://127.0.0.1:9485/page/1", "url": "https://chatgpt.com/"}

        def fake_cdp(ws_url, method, params=None, msg_id=None, timeout=20.0):
            expr = (params or {}).get("expression", "")
            if "composerLen" in expr:
                return {"result": {"result": {"value": {"found": True, "complete": True, "src": "https://oaiusercontent.com/gen.png", "width": 1024, "height": 576, "isStreaming": False, "hasNewTurn": True, "composerLen": 0, "combinedText": "", "pageTextTail": ""}}}}
            if "cx:" in expr or "selectNodeContents" in expr:
                return {"result": {"result": {"value": {"ok": True, "cx": 400, "cy": 350}}}}
            if "imgs:" in expr:
                return {"result": {"result": {"value": {"imgs": [], "msgCount": 0}}}}
            if "sendBtn" in expr:
                return {"result": {"result": {"value": {"ok": True}}}}
            return {"result": {"result": {"value": 120}}}

        with tempfile.TemporaryDirectory() as tmp:
            out_ok = Path(tmp) / "thumb_ok.png"
            with patch.object(chatgpt_browser, "get_active_profile", return_value=(Path(tmp), 9485, "cgpt_t")), \
                 patch.object(chatgpt_browser, "_hide_chatgpt_window") as m_hide, \
                 patch.object(chatgpt_browser, "update_account_state"), \
                 patch.object(chatgpt_webtool, "get_chatgpt_tab", return_value=fake_tab), \
                 patch.object(chatgpt_webtool, "_ensure_fresh_chat"), \
                 patch.object(chatgpt_webtool, "check_chatgpt_login_status", return_value={"ok": True, "logged_in": True, "email": "a@b.c"}), \
                 patch.object(chatgpt_webtool, "_get_top_conversation_id", return_value="prev_conv_1"), \
                 patch.object(chatgpt_webtool, "execute_cdp_command", side_effect=fake_cdp), \
                 patch.object(chatgpt_webtool, "_extract_image_bytes", return_value=valid_png), \
                 patch.object(chatgpt_webtool, "_cleanup_generated_conversation", return_value="conv_temp_123") as m_del, \
                 patch("time.sleep"):
                res_ok = chatgpt_webtool._generate_once("Test prompt clean", out_ok, timeout_seconds=30)
            self.assertTrue(res_ok.get("ok"), res_ok)
            self.assertEqual(res_ok.get("deleted_conversation_id"), "conv_temp_123")
            m_del.assert_called_once()
            self.assertGreaterEqual(m_hide.call_count, 2)

            out_fail = Path(tmp) / "thumb_fail.png"
            with patch.object(chatgpt_browser, "get_active_profile", return_value=(Path(tmp), 9485, "cgpt_t")), \
                 patch.object(chatgpt_browser, "_hide_chatgpt_window"), \
                 patch.object(chatgpt_browser, "update_account_state"), \
                 patch.object(chatgpt_webtool, "get_chatgpt_tab", return_value=fake_tab), \
                 patch.object(chatgpt_webtool, "_ensure_fresh_chat"), \
                 patch.object(chatgpt_webtool, "check_chatgpt_login_status", return_value={"ok": True, "logged_in": True, "email": "a@b.c"}), \
                 patch.object(chatgpt_webtool, "_get_top_conversation_id", return_value="prev_conv_1"), \
                 patch.object(chatgpt_webtool, "execute_cdp_command", side_effect=fake_cdp), \
                 patch.object(chatgpt_webtool, "_extract_image_bytes", return_value=None), \
                 patch.object(chatgpt_webtool, "_cleanup_generated_conversation") as m_del_fail, \
                 patch("time.sleep"):
                res_fail = chatgpt_webtool._generate_once("Test prompt clean", out_fail, timeout_seconds=30)
            self.assertFalse(res_fail.get("ok"))
            self.assertIn("DOWNLOAD_FAILED", res_fail.get("error", ""))
            m_del_fail.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
