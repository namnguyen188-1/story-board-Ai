"""Pure parser regression for explicit 3-digit skill scene numbering.

This module imports only the worktree's parser, writes no production files,
and never starts external providers.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from studio_input_modes import parse_locked_screenplay

BODY = "FORMAT & STYLE:\nCinematic shot.\nAUDIO:\nNarrator: \"A new scene begins.\""


class SkillSceneNumbering(unittest.TestCase):
    def test_consecutive_explicit_ids_are_preserved(self):
        script = "SCENE_001 — 00:00–00:08\n" + BODY + "\nSCENE_002 — 00:08–00:16\n" + BODY
        self.assertEqual([s["scene_number"] for s in parse_locked_screenplay(script)], [1, 2])

    def test_missing_first_scene_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "SCENE_SEQUENCE_INVALID"):
            parse_locked_screenplay("SCENE_002 — 00:08–00:16\n" + BODY)

    def test_gap_fails_closed(self):
        script = "SCENE_001\n" + BODY + "\nSCENE_003\n" + BODY
        with self.assertRaisesRegex(ValueError, "SCENE_SEQUENCE_INVALID"):
            parse_locked_screenplay(script)

    def test_duplicate_fails_closed(self):
        script = "SCENE_001\n" + BODY + "\nSCENE_001\n" + BODY
        with self.assertRaisesRegex(ValueError, "SCENE_SEQUENCE_INVALID"):
            parse_locked_screenplay(script)

    def test_legacy_shot_header_stays_compatible(self):
        script = "SHOT 2\nA landscape scene without any spoken dialogue."
        self.assertEqual(parse_locked_screenplay(script)[0]["scene_number"], 1)

    def test_legacy_vietnamese_header_stays_compatible(self):
        script = "CẢNH 2\nMột cảnh quay trong ngôi nhà."
        self.assertEqual(parse_locked_screenplay(script)[0]["scene_number"], 1)

    def test_unstructured_prose_still_auto_segments(self):
        self.assertEqual(parse_locked_screenplay("Một ngày dài trôi qua trong thung lũng.")[0]["scene_number"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
