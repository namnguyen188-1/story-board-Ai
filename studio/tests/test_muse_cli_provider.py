"""Contract tests for the Muse provider; no network or account mutation."""
import json, os, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import muse_video_provider as provider

class ProviderTests(unittest.TestCase):
    def test_saved_session_transport_does_not_require_api_key(self):
        with tempfile.TemporaryDirectory() as td:
            with patch.object(provider,"CONFIG_FILE",Path(td)/"config.json",create=True):
                cfg=provider.get_muse_config()
        self.assertEqual(cfg.get("transport"),"muse-cli")
        self.assertNotIn("api_key",cfg)

    def test_prompt_keeps_scene_prompt_and_character_description(self):
        scene={"description":"She sets the cup down.","prompt":"[9] A slow camera push follows her gaze.","narration":"Hello."}
        bible={"world":"a kitchen","characters":[{"name":"Linh","description":"a red coat and short black hair"}]}
        prompt=provider.format_real_acting_prompt(scene,bible)
        self.assertIn("red coat",prompt)
        self.assertIn(scene["prompt"],prompt)
        self.assertIn("PERFORMANCE",prompt)

    def test_settings_never_rewrite_studio_env(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"muse.json"
            with patch.object(provider,"CONFIG_FILE",p,create=True):
                with patch.object(provider,"STUDIO_ENV",Path(td)/".env",create=True):
                    provider.save_muse_config(enabled=True,python_executable=sys.executable)
                    data=json.loads(p.read_text())
                    self.assertEqual(data["python_executable"],sys.executable)
                    self.assertNotIn("api_key",data)
                    self.assertFalse((Path(td)/".env").exists())
if __name__=="__main__":unittest.main()
