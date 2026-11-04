"""Offline edge cases for native-audio karaoke and VAD anchors.
All files are in disposable temporary directories; no service calls.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

STUDIO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STUDIO))
sys.path.insert(0, str(STUDIO / "engine"))

from cinematic_engine.native_audio_subtitles import validate_vad_anchor
from tools.video_subtitle import generate_styled_ass


class NativeSubtitleEdgeCases(unittest.TestCase):
    def test_empty_vad_rejects_words(self):
        with self.assertRaisesRegex(RuntimeError, "WORD_IN_SILENCE"):
            validate_vad_anchor([{"word": "test", "start": 0.4, "end": 0.7}], [])

    def test_word_in_second_speech_window_is_accepted(self):
        speech = [{"start": 0.1, "end": 0.8}, {"start": 6.7, "end": 7.2}]
        word = {"word": "test", "start": 6.75, "end": 6.9}
        self.assertEqual(validate_vad_anchor([word], speech), [word])

    def _render(self, native, style, words):
        payload = {"subtitles": [{"start": 1.0, "end": 2.0, "text": " ".join(w["word"] for w in words), "words": words}]}
        if native:
            payload["timing_source"] = "native-audio-v1"
        with tempfile.TemporaryDirectory(prefix="subtitle_qa_") as directory:
            root = Path(directory)
            (root / "subtitles.json").write_text(json.dumps(payload), encoding="utf-8")
            generate_styled_ass(str(root / "subtitles.json"), str(root / "out.ass"), subtitle_style=style, enable_stickers=False)
            return [line for line in (root / "out.ass").read_text(encoding="utf-8").splitlines() if line.startswith("Dialogue:")]

    def test_native_karaoke_five_words_never_shows_future_words(self):
        words = [
            {"word": s, "start": 1.0 + 0.2 * i, "end": 1.2 + 0.2 * i}
            for i, s in enumerate(["One", "Two", "Three", "Four", "Five"])
        ]
        events = self._render(True, "karaoke_viral", words)
        self.assertEqual(len(events), 5)
        self.assertIn("One", events[0])
        self.assertNotIn("Two", events[0])
        self.assertNotIn("Four", events[2])
        self.assertIn("Four", events[3])
        self.assertIn("Five", events[4])
        self.assertNotIn("One", events[4])  # chunk boundary reset

    def test_legacy_karaoke_retains_full_chunk_look(self):
        words = [
            {"word": s, "start": 1.0 + 0.2 * i, "end": 1.2 + 0.2 * i}
            for i, s in enumerate(["One", "Two", "Three"])
        ]
        events = self._render(False, "karaoke_viral", words)
        self.assertEqual(len(events), 3)
        self.assertIn("Three", events[0])

    def test_native_missing_word_timings_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="subtitle_qa_") as directory:
            root = Path(directory)
            (root / "subtitles.json").write_text(json.dumps({
                "timing_source": "native-audio-v1",
                "subtitles": [{"start": 0.0, "end": 2.0, "text": "A phrase"}]
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "SUBTITLE_ALIGNMENT_WORD_TIMINGS_MISSING"):
                generate_styled_ass(str(root / "subtitles.json"), str(root / "out.ass"), enable_stickers=False)


if __name__ == "__main__":
    unittest.main(verbosity=2)
