import sys, unittest
from pathlib import Path

# Add studio to sys.path
studio_dir = Path(__file__).resolve().parent.parent
if str(studio_dir) not in sys.path:
    sys.path.insert(0, str(studio_dir))

class TestCinematicLinkProtection(unittest.TestCase):
    def test_muse_prompt_live_action_for_drama(self):
        from muse_video_provider import format_real_acting_prompt
        scene = {
            "visual_setup": "Princess Ugomma stands in the misty sacred river under divine judgment.",
            "action": "Ugomma looks around anxiously as mist rises.",
            "dialogue": "I am innocent!",
            "camera": "slow dramatic dolly push-in",
            "genre": "drama",
            "visual_style": "color_cinematic"
        }
        bible = {
            "production_mode": "cinematic_drama",
            "genre": "drama",
            "visual_style": "color_cinematic",
            "master_setting": "Sacred riverbank"
        }
        prompt = format_real_acting_prompt(scene, bible)
        self.assertIn("8k master cinema live-action film", prompt)
        self.assertIn("photorealistic 35mm anamorphic lens", prompt)
        self.assertNotIn("Pixar", prompt)
        self.assertNotIn("3D CGI", prompt)
        self.assertNotIn("animated feature film", prompt)

    def test_drama_skill9_branch2_for_cinematic_drama(self):
        from cinematic_engine.drama_skill9 import writing_rules
        rules = writing_rules("drama", "color_cinematic")
        self.assertIn("BRANCH 2: CINEMATIC LIVE-ACTION DRAMA PIPELINE (Real Actors)", rules)
        self.assertIn("Characters MUST be photorealistic living human actors", rules)
        self.assertNotIn("BRANCH 1: ANIMATION PIPELINE", rules)

    def test_drama_skill9_protects_against_folktale_keyword(self):
        from cinematic_engine.drama_skill9 import writing_rules
        # Even if genre string is 'family_drama' or visual_style is 'color_cinematic'
        rules = writing_rules("family_drama", "color_cinematic")
        self.assertIn("BRANCH 2: CINEMATIC LIVE-ACTION DRAMA PIPELINE", rules)

if __name__ == '__main__':
    unittest.main()
