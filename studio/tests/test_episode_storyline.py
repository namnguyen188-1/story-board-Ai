import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from episode_storyline import build_episode_context


def seed(base, index, prompt, genre="stoic", mode="idea"):
    directory = base / f"episode_{index:03d}"
    directory.mkdir(parents=True, exist_ok=True)
    data = {
        "config": {"prompt": prompt, "genre": genre, "input_mode": mode},
        "bible": {"core_moral_theme": "Freedom from external approval"},
        "scenes": [
            {"summary": "Separate external events from internal responses", "narration": "We can choose our response."},
            {"summary": "Practice responding to criticism with patience", "narration": "Next we examine the fear of judgement."},
        ],
    }
    (directory / "plan.json").write_text(
        json.dumps(data, ensure_ascii=False), encoding="utf-8")


class TestEpisodeStoryline(unittest.TestCase):
    def test_next_episode_inherits_root_and_last_beat(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            seed(base, 1, "Khắc kỷ: Làm chủ phản ứng")
            seed(base, 2, "Đào sâu phản ứng với lời phê bình")
            ctx = build_episode_context(base, 3, "stoic")
            self.assertIn("episode 3", ctx)
            self.assertIn("Khắc kỷ: Làm chủ phản ứng", ctx)
            self.assertIn("fear of judgement", ctx)
            self.assertIn("not a standalone random topic", ctx)
            self.assertIn("STOIC SERIES RULES", ctx)

    def test_no_previous_story_does_not_invent_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual("", build_episode_context(tmp, 2, "stoic"))
            self.assertEqual("", build_episode_context(tmp, 1, "stoic"))

    def test_clone_cannot_contaminate_original_idea_series(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            seed(base, 1, "Other video", mode="link")
            self.assertEqual("", build_episode_context(base, 2, "stoic"))

    def test_genre_mismatch_does_not_crosslink(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            seed(base, 1, "Stoic", genre="animation")
            self.assertEqual("", build_episode_context(base, 2, "stoic"))


if __name__ == "__main__":
    unittest.main()
