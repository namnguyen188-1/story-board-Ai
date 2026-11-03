"""Offline regressions for image anchoring and native-audio timecode gates."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
ROOT = Path(r"D:\STORYBOARD_AI\studio")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "engine"))
from cinematic_engine.drama_video_engine import DramaVideoEngine
from cinematic_engine.native_audio_subtitles import validate_words
from muse_gateway_worker import run_render

class ReferenceVoiceGuards(unittest.TestCase):
    def test_muse_rejects_missing_reference_before_network(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(RuntimeError, "MUSE_REFERENCE_MISSING"):
                run_render({"output_image_path":str(Path(d)/"image.png"),"prompt":"unit",
                            "width":1280,"height":720,"duration":10,
                            "reference_image":str(Path(d)/"lost.jpg")})
    def test_packed_scene_does_not_render_without_character_anchor(self):
        with tempfile.TemporaryDirectory() as d:
            scene_dir = Path(d)/"episode"/"scenes"/"scene_0001"
            scene_dir.mkdir(parents=True)
            (Path(d)/"episode"/"00_ASSET_PACK"/"characters").mkdir(parents=True)
            with self.assertRaisesRegex(RuntimeError,"SCENE_CHARACTER_REFERENCE_MISSING"):
                DramaVideoEngine().render_scene({"scene_number":1,"characters_present":["Lan"]},
                    scene_dir, image_provider="muse_video")
    def test_zero_length_word_is_only_repaired_in_bounded_speech_span(self):
        words=[{"word":"này","start":3.9,"end":4.7},
               {"word":"là","start":4.7,"end":4.7},
               {"word":"của","start":4.7,"end":4.92}]
        fixed=validate_words(words,5)
        self.assertEqual(len(fixed),3)
        self.assertLessEqual(fixed[1]["end"]-fixed[1]["start"],.061)
        self.assertLessEqual(fixed[0]["end"],fixed[1]["start"])
        with self.assertRaisesRegex(RuntimeError,"INVALID_WORD_TIMING"):
            validate_words([{"word":"x","start":2,"end":2}],5)
    def test_cinematic_reference_replaces_unverified_cache(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            r1=d/"lan.jpg"; r2=d/"lan_other.jpg"
            Image.new("RGB",(32,32), "green").save(r1)
            Image.new("RGB",(32,32), "blue").save(r2)
            generated=d/"result.png"
            Image.effect_noise((256,256), 80).convert("RGB").save(generated)
            scene=d/"scene"; scene.mkdir()
            base=scene/"scene_base.png"
            Image.effect_noise((256,256), 50).convert("RGB").save(base)
            calls=[]
            def fake_image_gen_tool_fn(**kwargs):
                calls.append(kwargs)
                return str(generated)
            import types
            fake_module = types.ModuleType("comfyui_image_provider")
            fake_module.make_image = fake_image_gen_tool_fn
            with patch.dict(sys.modules, {"comfyui_image_provider": fake_module}):
                engine=DramaVideoEngine()
                engine.ensure_scene_base_visual({"visual_setup":"woman in coat"},scene,
                                                reference_image_path=r1)
                self.assertEqual(len(calls),1)
                self.assertEqual(calls[0]["reference_path"],str(r1))
                self.assertTrue((scene/"scene_base_before_reference_repair.png").exists())
                meta=json.loads((scene/"scene_base_reference.json").read_text())
                self.assertEqual(meta["generation_source"],"comfyui_ipadapter")
                engine.ensure_scene_base_visual({"visual_setup":"woman in coat"},scene,
                                                reference_image_path=r1)
                self.assertEqual(len(calls),1)
                engine.ensure_scene_base_visual({"visual_setup":"woman in coat"},scene,
                                                reference_image_path=r2)
                self.assertEqual(len(calls),2)
if __name__=="__main__":
    unittest.main(verbosity=2)
