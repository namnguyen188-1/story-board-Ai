import unittest
import numpy as np
from PIL import Image, ImageDraw
from pathlib import Path
import re

from studio.seo_packager import (
    ensure_episode_in_title,
    is_clean_lang_text,
    _parse_hook_lines,
    generate_thumbnail_image,
)
from studio.seo_genre_profiles import enrich_and_maximize_tags


class TestSeoInternationalStandards(unittest.TestCase):
    def test_ensure_episode_in_title(self):
        # English: Should convert Vietnamese or Spanish episode indicators to (Episode X)
        t1 = ensure_episode_in_title("Marcus Cole (Tập 3) - Standing Up", 3, "English")
        self.assertIn("(Episode 3)", t1)
        self.assertNotIn("Tập 3", t1)

        t2 = ensure_episode_in_title("Marcus Cole (Episodio 3) - Standing Up", 3, "English")
        self.assertIn("(Episode 3)", t2)
        self.assertNotIn("Episodio", t2)

        # English: Keep clean title if already in English
        t3 = ensure_episode_in_title("Marcus Cole | Episode 3 - Standing Up", 3, "English")
        self.assertIn("Episode 3", t3)

        # Vietnamese: Convert English to Tập X
        t4 = ensure_episode_in_title("Marcus Cole (Episode 3) - Đứng Lên", 3, "Vietnamese")
        self.assertIn("(Tập 3)", t4)
        self.assertNotIn("Episode", t4)

        # Spanish: Convert English to Episodio X
        t5 = ensure_episode_in_title("Marcus Cole (Episode 3) - La Verdad", 3, "Spanish")
        self.assertIn("(Episodio 3)", t5)
        self.assertNotIn("Episode 3", t5)

    def test_is_clean_lang_text(self):
        self.assertFalse(is_clean_lang_text("Tập 3", is_vietnamese=False))
        self.assertFalse(is_clean_lang_text("tap 3", is_vietnamese=False))
        self.assertFalse(is_clean_lang_text("phim ngắn hay", is_vietnamese=False))
        self.assertFalse(is_clean_lang_text("Dale LIKE và COMPARTE", is_vietnamese=False))
        self.assertTrue(is_clean_lang_text("The Ultimate Neighborhood Showdown", is_vietnamese=False))
        self.assertTrue(is_clean_lang_text("Tập 3: Cái kết bất ngờ", is_vietnamese=True))

    def test_enrich_and_maximize_tags_isolation(self):
        # Contaminated tag list containing foreign and Vietnamese tags
        dirty_tags = [
            "drama", "drama episode 3", "family drama",
            "tập 3", "tap 3", "phim", "cau chuyen",
            "episodio 3", "folge 3", "серия 3",
            "retribution", "justice", "hoa drama"
        ]
        clean_en = enrich_and_maximize_tags(
            base_tags=dirty_tags,
            primary_kw="drama",
            genre="family_drama",
            language="English",
            series_name="drama",
            episode_num=3,
        )
        for t in clean_en:
            self.assertFalse(bool(re.search(r"[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]", t)), f"Vietnamese accent in tag: {t}")
            self.assertFalse(bool(re.search(r"\b(tập|tap|phim|câu chuyện|cau chuyen)\b", t, re.IGNORECASE)), f"Vietnamese word in tag: {t}")
            self.assertFalse(bool(re.search(r"\b(episodio|folge|серия)\b", t, re.IGNORECASE)), f"Foreign word in English tag: {t}")

        self.assertIn("drama", clean_en)
        self.assertIn("drama episode 3", clean_en)
        self.assertIn("retribution", clean_en)

    def test_parse_hook_lines(self):
        # 2-part setup/punchline split
        p1 = _parse_hook_lines("UNFAIR HOA RULES! / Instant Retribution")
        self.assertEqual(len(p1), 2)
        self.assertEqual(p1[0], "UNFAIR HOA RULES!")
        self.assertEqual(p1[1], "Instant Retribution")

        p2 = _parse_hook_lines("CAUGHT ON CAMERA\nHuge Mistake")
        self.assertEqual(len(p2), 2)
        self.assertEqual(p2[0], "CAUGHT ON CAMERA")
        self.assertEqual(p2[1], "Huge Mistake")

    def test_thumbnail_face_avoidance(self):
        # Create a test frame where a character face is positioned on the left side
        test_frame = Image.new("RGB", (1280, 720), (30, 30, 40))
        draw = ImageDraw.Draw(test_frame)
        # Draw face on left (X=200..450, Y=100..350) in skin tone (RGB: 220, 160, 140)
        draw.ellipse((200, 100, 450, 350), fill=(220, 160, 140))

        out_path = Path("studio/tests/test_out_thumb.jpg")
        base_path = Path("studio/tests/test_in_thumb.png")
        test_frame.save(base_path)

        try:
            generate_thumbnail_image(
                base_image_path=base_path,
                output_path=out_path,
                hook_text="SHOCKING TRUTH / NEVER AGAIN",
                preferred_side="auto",
            )
            thumb = Image.open(out_path)
            arr = np.array(thumb)
            # Find yellow text coordinates
            yellow_mask = (arr[:, :, 0] > 200) & (arr[:, :, 1] > 180) & (arr[:, :, 2] < 50)
            y_indices, x_indices = np.where(yellow_mask)

            # Text MUST be positioned on the RIGHT half (X >= 650) to leave the face on left untouched
            self.assertTrue(len(x_indices) > 0, "Yellow text should be rendered")
            self.assertGreaterEqual(x_indices.min(), 650, f"Text x_min is {x_indices.min()}, which encroaches on left-side face!")
        finally:
            if base_path.exists():
                base_path.unlink()
            if out_path.exists():
                out_path.unlink()


if __name__ == "__main__":
    unittest.main()
