"""Regression tests for standalone quoted speech in locked scene scripts."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from studio_input_modes import parse_locked_screenplay

class LockedQuotedNarrationTests(unittest.TestCase):
    def test_visual_description_and_quoted_speech_remain_separate(self):
        script = 'CẢNH 1:\nGóc máy rộng bên rừng.\n"Đừng mở cửa khi nghe tiếng gọi."'
        scene = parse_locked_screenplay(script, 8)[0]
        self.assertEqual(scene["narration"], "Đừng mở cửa khi nghe tiếng gọi.")
        self.assertEqual(scene["dialogue_beats"][0]["text"], scene["narration"])
        self.assertIn("Góc máy rộng", scene["description"])

    def test_multiple_quoted_lines_are_kept_in_order(self):
        script = 'SCENE 1\nThe two people meet.\n“Hello there.”\n"Good evening."'
        scene = parse_locked_screenplay(script)[0]
        self.assertEqual(scene["narration"], "Hello there. Good evening.")
        self.assertEqual([b["text"] for b in scene["dialogue_beats"]], ["Hello there.", "Good evening."])

    def test_explicit_silent_scene_stays_silent(self):
        script = 'CẢNH 1\nKhông có lời thoại.\n"Chữ trên tấm biển"'
        scene = parse_locked_screenplay(script)[0]
        self.assertEqual(scene["narration"], "")
        self.assertEqual(scene["dialogue_beats"], [])

    def test_quoted_visual_text_in_structured_scene_is_not_speech(self):
        script = 'SCENE 1\nCAMERA: A sign marked "STOP"\nAUDIO: No dialogue'
        self.assertEqual(parse_locked_screenplay(script)[0]["narration"], "")

    def test_long_quoted_line_not_cut(self):
        line = " ".join(["word"] * 100)
        self.assertEqual(parse_locked_screenplay('SCENE 1\nVisual description.\n"' + line + '"')[0]["narration"], line)

if __name__ == "__main__":
    unittest.main()
