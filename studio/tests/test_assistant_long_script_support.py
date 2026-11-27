import os
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

STUDIO_DIR = Path(__file__).resolve().parent.parent
if str(STUDIO_DIR) not in sys.path:
    sys.path.insert(0, str(STUDIO_DIR))

import assistant_9router
import freellmapi_provider
import series_studio
import tuansuapi_provider


class AssistantLongScriptSupportTests(unittest.TestCase):
    def test_detect_long_script_and_system_prompt_rules(self):
        is_long, mins = assistant_9router._detect_long_script_request(
            [{"role": "user", "content": "Hãy viết kịch bản dài 8 phút khoảng 20 cảnh chi tiết về gia tộc."}]
        )
        self.assertTrue(is_long)
        self.assertEqual(mins, 8.0)

        sys_prompt = assistant_9router._build_studio_system_prompt(
            genre="family_drama",
            language="Vietnamese",
            is_long=is_long,
            target_minutes=mins,
        )
        self.assertIn("8 phút", sys_prompt)
        self.assertIn("KHÔNG tóm tắt", sys_prompt)
        self.assertIn("Thời lượng ước tính", sys_prompt)

        is_cont, _ = assistant_9router._detect_long_script_request(
            [{"role": "user", "content": "Viết tiếp phần tiếp theo ngay sau cảnh cuối"}]
        )
        self.assertTrue(is_cont)

        is_short, mins_short = assistant_9router._detect_long_script_request(
            [{"role": "user", "content": "Gợi ý 3 tiêu đề thumbnail ngắn"}]
        )
        self.assertFalse(is_short)
        self.assertIsNone(mins_short)

    def test_chat_completion_passes_large_tokens_timeout_and_preserves_long_history(self):
        long_part_1 = "Cảnh 1 mở đầu " + ("chi tiết diễn biến kịch tính của gia tộc Vane. " * 260)
        self.assertGreater(len(long_part_1), 11000)
        captured = {}

        def fake_free_chat(clean_msgs, model=None, temperature=0.7, timeout=90.0, max_tokens=None):
            captured["clean_msgs"] = clean_msgs
            captured["timeout"] = timeout
            captured["max_tokens"] = max_tokens
            return "Phần 2 - Cảnh 12: Cao trào đối chất tại đại sảnh."

        with patch.object(assistant_9router, "is_router_running", return_value=False), \
             patch.object(assistant_9router, "_read_db_summary_and_key", return_value=({"active_providers": [], "total_connections": 0, "combos": []}, "")), \
             patch.object(freellmapi_provider, "get_config", return_value={"base_url": "http://127.0.0.1:31415/v1", "api_key": "k", "model": "auto", "mode": "fallback"}), \
             patch.object(freellmapi_provider, "is_running", return_value=True), \
             patch.object(freellmapi_provider, "generate_chat_completion", side_effect=fake_free_chat):
            os.environ.pop("STORYBOARD_FREELLMAPI_COOLDOWN_UNTIL", None)
            res = assistant_9router.chat_completion(
                messages=[
                    {"role": "user", "content": "Viết kịch bản dài 10 phút"},
                    {"role": "assistant", "content": long_part_1},
                    {"role": "user", "content": "Hãy viết tiếp phần 2 dài thêm"},
                ],
                genre="family_drama",
                language="Vietnamese",
                auto_start=False,
            )

        self.assertTrue(res.get("ok"), res)
        self.assertTrue(res.get("is_long"))
        self.assertGreaterEqual(captured["timeout"], 16.0)
        self.assertEqual(captured["max_tokens"], 8192)
        assistant_hist = next(m for m in captured["clean_msgs"] if m["role"] == "assistant")
        self.assertGreater(len(assistant_hist["content"]), 10000, "Must not clip long Part 1 at 8000 chars")

    def test_rejects_safety_classifier_stub_and_fails_over(self):
        self.assertFalse(assistant_9router._is_valid_assistant_reply("Safety: Safe\nCategories: None", "Hãy viết kịch bản tiếng Nhật 4 cảnh"))
        self.assertTrue(assistant_9router._is_valid_assistant_reply("Tiêu đề: Đêm Edo\nCảnh 1: Tiếng gió thổi qua hiên nhà.", "Viết kịch bản"))
        with patch.object(assistant_9router, "is_router_running", return_value=False), \
             patch.object(assistant_9router, "_read_db_summary_and_key", return_value=({"active_providers": [], "total_connections": 0, "combos": []}, "")), \
             patch.object(freellmapi_provider, "get_config", return_value={"base_url": "http://127.0.0.1:31415/v1", "api_key": "k", "model": "auto", "mode": "fallback"}), \
             patch.object(freellmapi_provider, "is_running", return_value=True), \
             patch.object(freellmapi_provider, "generate_chat_completion", return_value="Safety: Safe\nCategories: None"), \
             patch.object(assistant_9router, "_studio_ai_failover", return_value={"ok": True, "reply": "タイトル: 江戸の灯り\nCảnh 1: 夜風が吹く。", "backend": "tuansuapi", "model": "gemini-flash-3.8-fast"}):
            os.environ.pop("STORYBOARD_FREELLMAPI_COOLDOWN_UNTIL", None)
            res = assistant_9router.chat_completion(
                messages=[{"role": "user", "content": "Hãy viết kịch bản ngắn bằng tiếng Nhật"}],
                language="Japanese",
                auto_start=False,
            )
        self.assertTrue(res.get("ok"), res)
        self.assertEqual(res.get("backend"), "tuansuapi")
        self.assertIn("江戸", res.get("reply", ""))

    def test_providers_retry_without_max_tokens_on_http_400(self):
        payloads = []

        def make_resp(code, content="OK"):
            r = Mock()
            r.status_code = code
            r.text = "unsupported max_tokens" if code == 400 else "ok"
            r.json.return_value = {"choices": [{"message": {"content": content}}]}
            return r

        def fake_post(url, headers=None, json=None, timeout=None):
            payloads.append(dict(json or {}))
            if len(payloads) == 1:
                return make_resp(400)
            return make_resp(200, "Kịch bản đầy đủ")

        with patch.object(freellmapi_provider, "get_config", return_value={"base_url": "http://127.0.0.1:31415/v1", "api_key": "k", "model": "m", "mode": "fallback"}), \
             patch.object(freellmapi_provider, "ensure_running", return_value=True), \
             patch.object(freellmapi_provider.requests, "post", side_effect=fake_post):
            out_f = freellmapi_provider.generate_chat_completion([{"role": "user", "content": "hi"}], max_tokens=8192)
        self.assertEqual(out_f, "Kịch bản đầy đủ")
        self.assertEqual(payloads[0].get("max_tokens"), 8192)
        self.assertNotIn("max_tokens", payloads[1])

        payloads.clear()
        with patch.object(tuansuapi_provider, "get_gateway_config", return_value={"base_url": "https://tuansuapi.store/v1", "api_key": "k", "text_model": "gemini-flash-3.8-fast", "enabled": "1"}), \
             patch.object(tuansuapi_provider.requests, "post", side_effect=fake_post):
            out_t = tuansuapi_provider.generate_chat_completion([{"role": "user", "content": "hi"}], max_tokens=8192)
        self.assertEqual(out_t, "Kịch bản đầy đủ")
        self.assertEqual(payloads[0].get("max_tokens"), 8192)
        self.assertNotIn("max_tokens", payloads[1])

    def test_series_studio_preserves_full_long_premise_and_late_batches(self):
        script_15k = ("Mở đầu câu chuyện gia tộc. " * 250) + "ĐIỂM CAO TRÀO CUỐI TẬP: Di chúc thật được mở."
        self.assertGreater(len(script_15k), 6000)
        self.assertLess(len(script_15k), 20000)
        sliced = series_studio._slice_premise_for_batch(script_15k, batch_pos=12, batch_size=6, total_scenes=24)
        self.assertIn("ĐIỂM CAO TRÀO CUỐI TẬP: Di chúc thật được mở.", sliced)
        self.assertEqual(sliced, script_15k)

        mega_script = ("Mở đầu nhân vật A. " * 300) + ("Diễn biến giữa tập. " * 1100) + "TWIST_CUOI_CUC_MANH_30K"
        self.assertGreater(len(mega_script), 25000)
        late_slice = series_studio._slice_premise_for_batch(mega_script, batch_pos=30, batch_size=10, total_scenes=40)
        self.assertIn("Mở đầu nhân vật A.", late_slice)
        self.assertIn("TWIST_CUOI_CUC_MANH_30K", late_slice)

    def test_frontend_chat_ui_long_script_and_duration_sync_wired(self):
        html = (STUDIO_DIR / "web" / "index.html").read_text(encoding="utf-8")
        js = (STUDIO_DIR / "web" / "app.js").read_text(encoding="utf-8")
        self.assertIn('id="chatLanguageSelect"', html)
        self.assertIn("runAssistantQuickPreset('long_script')", html)
        self.assertIn("function _getChatSelectedLanguage", js)
        self.assertIn("function _estimateScriptStats", js)
        self.assertIn("cjkChars", js)
        self.assertIn("function _collectMergedAssistantScripts", js)
        self.assertIn("window.continueAssistantScript", js)
        self.assertIn("_assistantChatHistory.slice(-24)", js)

    def test_target_language_selection_honors_japanese_korean_and_vietnamese(self):
        k_jp, disp_jp = assistant_9router._resolve_target_script_language(
            "Japanese",
            [{"role": "user", "content": "Viết kịch bản câu chuyện Edo"}],
        )
        self.assertEqual(k_jp, "japanese")
        sys_jp = assistant_9router._build_studio_system_prompt(
            genre="jp_edo_sleepless",
            language="Japanese",
            is_long=True,
            target_minutes=6.0,
            resolved_lang_key=k_jp,
            resolved_lang_display=disp_jp,
        )
        self.assertIn("Tiếng Nhật (日本語)", sys_jp)
        self.assertNotIn("LUÔN trả lời, đặt tiêu đề, giải thích và mô tả cảnh bằng **TIẾNG VIỆT**", sys_jp)

        k_kr, disp_kr = assistant_9router._resolve_target_script_language(
            "Auto",
            [{"role": "user", "content": "Hãy viết kịch bản drama bằng tiếng Hàn"}],
        )
        self.assertEqual(k_kr, "korean")
        sys_kr = assistant_9router._build_studio_system_prompt(
            genre="kr_yadam_joseon",
            language="Korean",
            resolved_lang_key=k_kr,
            resolved_lang_display=disp_kr,
        )
        self.assertIn("Tiếng Hàn (한국어)", sys_kr)

        k_vi, disp_vi = assistant_9router._resolve_target_script_language(
            "Vietnamese",
            [{"role": "user", "content": "Viết kịch bản gia đình kịch tính"}],
        )
        self.assertEqual(k_vi, "vietnamese")
        self.assertEqual(disp_vi, "Tiếng Việt")


if __name__ == "__main__":
    unittest.main(verbosity=2)
