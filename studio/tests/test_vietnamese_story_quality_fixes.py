"""Regression tests for Vietnamese storytelling quality, language isolation, TTS failover/consistency, and pacing."""
from __future__ import annotations

import json
import math
import struct
import sys
import tempfile
import unittest
import wave
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

STUDIO = Path(__file__).resolve().parent.parent
ENGINE = STUDIO / "engine"
for _p in (str(STUDIO), str(ENGINE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _write_tone_wav(path: Path, lead_s: float, tone_s: float, tail_s: float, sr: int = 24000) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lead_n = int(sr * lead_s)
    tone_n = int(sr * tone_s)
    tail_n = int(sr * tail_s)
    frames = bytearray()
    frames.extend(b"\x00\x00" * lead_n)
    for i in range(tone_n):
        val = int(12000 * math.sin(2 * math.pi * 220.0 * (i / sr)))
        frames.extend(struct.pack("<h", val))
    frames.extend(b"\x00\x00" * tail_n)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(bytes(frames))


class VietnameseStoryQualityTests(unittest.TestCase):
    def test_no_spanish_es_substring_leak_in_vietnamese_or_asian_languages(self):
        from tools.kinetic_stickers import extract_kinetic_stickers_from_subtitles
        from tools.tts import resolve_lang_code
        from tools.word_aligner import resolve_voice_and_rates
        from seo_packager import _lang_display_name, format_upload_settings_checklist_txt
        import series_studio as studio
        import shorts_extractor as sx

        subs = [
            {"start": 0.5, "end": 4.0, "text": "Tiền bạc tài sản và công lý không thể mua được lòng người."},
        ]
        stickers_vi = extract_kinetic_stickers_from_subtitles(subs, language="Vietnamese")
        self.assertTrue(stickers_vi)
        badges = [s["badge"] for s in stickers_vi]
        self.assertTrue(any("TÀI SẢN" in b or "CÔNG LÝ" in b for b in badges), badges)
        self.assertFalse(any("RIQUEZA" in b or "JUSTICIA" in b for b in badges), badges)

        # Verify 'es' inside 'Japanese'/'Chinese'/'Portuguese'/'Indonesian' never flips to Spanish
        for non_es in ("Vietnamese", "Japanese", "Chinese", "Portuguese", "Indonesian"):
            self.assertNotEqual(resolve_lang_code(non_es), "es", non_es)
            self.assertNotEqual(_lang_display_name(non_es), "Spanish", non_es)
            stickers_other = extract_kinetic_stickers_from_subtitles(
                [{"start": 0.5, "end": 3.0, "text": "money wealth justice"}],
                language=non_es,
            )
            self.assertFalse(any("RIQUEZA" in s["badge"] for s in stickers_other), non_es)

        # Spanish must still map to Spanish cleanly
        self.assertEqual(resolve_lang_code("Spanish"), "es")
        self.assertEqual(_lang_display_name("Spanish"), "Spanish")
        self.assertIn("Mã chuẩn YouTube: vi", format_upload_settings_checklist_txt({"language": "Vietnamese"}))
        self.assertIn("Mã chuẩn YouTube: es", format_upload_settings_checklist_txt({"language": "Spanish"}))

        voice_edge, _, _ = resolve_voice_and_rates("Charon", "Vietnamese", "normal")
        self.assertEqual(voice_edge, "vi-VN-NamMinhNeural")

        # Short Vietnamese drama preserves ending cliffhanger without Spanish or promo boilerplate
        scenes_short = [{"scene_number": i, "narration": f"Câu thoại cảnh {i}."} for i in range(1, 7)]
        res_short = studio.inject_spoken_cta_into_scenes(scenes_short, language="Vietnamese", genre="documentary")
        joined = " ".join(s["narration"] for s in res_short)
        self.assertNotIn("Suscríbete", joined)
        self.assertNotIn("¿Qué opinas", joined)

        # Longer Stoic Vietnamese still injects Vietnamese (not Spanish!) CTA cleanly
        scenes_long = [{"scene_number": i, "narration": f"Bài học khắc kỷ {i}."} for i in range(1, 11)]
        res_long = studio.inject_spoken_cta_into_scenes(scenes_long, language="Vietnamese", genre="stoic")
        joined_long = " ".join(s["narration"] for s in res_long)
        self.assertIn("Đăng ký kênh", joined_long)
        self.assertNotIn("Suscríbete", joined_long)

        # Shorts extractor language helpers
        self.assertEqual(sx.get_language_banners("Vietnamese")[0], "SỰ THẬT BỊ PHƠI BÀY")
        self.assertEqual(sx.get_language_banners("Spanish")[0], "EL ARTE DEL SILENCIO")

    def test_sanitize_audio_duration_trims_trailing_and_leading_dead_air(self):
        from tools.tts import sanitize_audio_duration

        with tempfile.TemporaryDirectory() as td:
            wav = Path(td) / "sample.wav"
            _write_tone_wav(wav, lead_s=0.45, tone_s=1.40, tail_s=0.95)
            sanitize_audio_duration(str(wav))
            with wave.open(str(wav), "rb") as wf:
                new_dur = wf.getnframes() / wf.getframerate()
            # Must cut excessive 0.45s lead + 0.95s tail down tightly while preserving 1.40s speech
            self.assertGreater(new_dur, 1.35)
            self.assertLess(new_dur, 1.85)

    def test_gemini_tts_key_pool_scans_past_three_exhausted_keys_and_persists_cooldowns(self):
        import resilient_gemini as rg

        class Quota429(Exception):
            code = 429

        keys = [f"AIzaSyTestKey000{i}_123456" for i in range(6)]
        calls = []

        class FakeModels:
            def __init__(self, key):
                self.key = key

            def generate_content(self, *, model, **kwargs):
                calls.append(self.key)
                if self.key in keys[:4]:
                    raise Quota429("Quota exceeded for metric: generate_content_free_tier_requests")
                return SimpleNamespace(text="ok_audio_from_key_5")

        with tempfile.TemporaryDirectory() as td:
            cd_file = Path(td) / "cooldowns.json"
            with patch.object(rg, "TTS_COOLDOWN_FILE", cd_file):
                rc = rg.ResilientClient(api_keys=keys)
                for k in keys:
                    rc._client_cache[k] = SimpleNamespace(models=FakeModels(k))

                cfg = SimpleNamespace(response_modalities=["AUDIO"])
                res = rc.models.generate_content(model="gemini-2.5-flash-preview-tts", contents="Xin chao", config=cfg)
                self.assertEqual(res.text, "ok_audio_from_key_5")
                self.assertEqual(calls, keys[:5], "Must NOT stop at 3 quota fails; must reach key #5")

                # New subprocess client should put cooled keys[0..3] behind fresh keys[4..5]
                calls.clear()
                rc2 = rg.ResilientClient(api_keys=keys)
                for k in keys:
                    rc2._client_cache[k] = SimpleNamespace(models=FakeModels(k))
                res2 = rc2.models.generate_content(model="gemini-2.5-flash-preview-tts", contents="Xin chao 2", config=cfg)
                self.assertEqual(res2.text, "ok_audio_from_key_5")
                self.assertEqual(calls[0], keys[4], "Must skip cooled keys immediately in fresh process")

    def test_voice_consistency_unifies_mixed_episode_engines(self):
        import series_studio as studio
        import tools

        with tempfile.TemporaryDirectory() as td:
            ep = Path(td) / "ep1"
            for idx, eng in ((1, "gemini"), (2, "edge_tts")):
                sdir = ep / "scenes" / f"scene_{idx:04d}"
                sdir.mkdir(parents=True)
                wav = sdir / "audio.wav"
                _write_tone_wav(wav, lead_s=0.05, tone_s=1.0, tail_s=0.1)
                (sdir / "audio.wav.engine.json").write_text(json.dumps({"engine": eng}), encoding="utf-8")
                (sdir / "job.json").write_text(
                    json.dumps({"language": "Vietnamese", "voice_name": "Charon", "subtitle_style": "none"}),
                    encoding="utf-8",
                )
                # Minimal dummy mp4 placeholder so silent_p check runs cleanly via mocked merge
                (sdir / "silent.mp4").write_bytes(b"0" * 1024)
                (sdir / "final.mp4").write_bytes(b"old_final")

            scenes = [
                {"scene_number": 1, "narration": "Cảnh một mở đầu."},
                {"scene_number": 2, "narration": "Cảnh hai nối tiếp."},
            ]
            args = SimpleNamespace(mode="live", language="Vietnamese", voice_name="Charon")

            synth_calls = []

            def fake_tts(text, language="Vietnamese", voice_name="Charon", **kw):
                synth_calls.append(text)
                out = Path(tools.utils.GLOBAL_OUTPUT_DIR) / "unified.wav"
                _write_tone_wav(out, lead_s=0.05, tone_s=1.0, tail_s=0.1)
                Path(str(out) + ".engine.json").write_text(json.dumps({"engine": "edge_tts"}), encoding="utf-8")
                return str(out)

            def fake_merge(silent_p, audio_p, merged_p):
                Path(merged_p).write_bytes(b"merged_unified")
                return str(merged_p)

            with patch.object(tools, "generate_tts_audio_tool_fn", side_effect=fake_tts), \
                 patch.object(tools, "merge_audio_video_tool_fn", side_effect=fake_merge):
                studio._enforce_episode_tts_voice_consistency(ep, scenes, args, 1280, 720)

            self.assertEqual(len(synth_calls), 1)
            eng1 = json.loads((ep / "scenes/scene_0001/audio.wav.engine.json").read_text(encoding="utf-8"))["engine"]
            self.assertEqual(eng1, "edge_tts")
            self.assertEqual((ep / "scenes/scene_0001/final.mp4").read_bytes(), b"merged_unified")

    def test_sound_design_multiact_under_60s_and_sfx_boundaries(self):
        import studio_sound_design as ssd

        with tempfile.TemporaryDirectory() as td:
            t = Path(td)
            bgm_out = t / "bgm_45s.wav"
            sfx_out = t / "sfx_45s.wav"
            ok_bgm = ssd.build_multiact_soundtrack(45.0, STUDIO / "engine", bgm_out)
            ok_sfx = ssd.compose_cinematic_sfx_stem(45.0, [12.0], STUDIO / "engine", sfx_out, scene_boundaries=[8.2, 16.0, 24.5, 33.1])
            self.assertTrue(ok_bgm and bgm_out.is_file() and bgm_out.stat().st_size > 10000)
            self.assertTrue(ok_sfx and sfx_out.is_file() and sfx_out.stat().st_size > 10000)


if __name__ == "__main__":
    unittest.main()
