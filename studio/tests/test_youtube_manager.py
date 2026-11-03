"""Test suite for Storyboard AI Studio Pro - YouTube Multi-Channel Management & 1-Click Upload."""
import sys
import unittest
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
STUDIO_DIR = ROOT_DIR / "studio"
if str(STUDIO_DIR) not in sys.path:
    sys.path.insert(0, str(STUDIO_DIR))

import youtube_manager


class TestYouTubeManager(unittest.TestCase):

    def setUp(self):
        self.original_config = youtube_manager.load_youtube_config()

    def tearDown(self):
        youtube_manager.save_youtube_config(self.original_config)

    def test_01_credentials_and_auth_url(self):
        res = youtube_manager.set_oauth_credentials(
            client_id="123456789-test.apps.googleusercontent.com",
            client_secret="test_secret_abc"
        )
        self.assertTrue(res["ok"])
        self.assertTrue(res["client_id_configured"])

        auth_url = youtube_manager.build_auth_url(
            redirect_uri="http://127.0.0.1:8765/api/youtube/oauth_callback"
        )
        self.assertIn("accounts.google.com/o/oauth2/v2/auth", auth_url)
        self.assertIn("123456789-test.apps.googleusercontent.com", auth_url)
        self.assertIn("youtube.upload", auth_url)

    def test_02_channel_crud(self):
        cfg = {
            "client_id": "test_client",
            "client_secret": "test_secret",
            "active_channel_id": "UC001",
            "channels": [
                {
                    "id": "UC001",
                    "name": "Channel Alpha",
                    "custom_url": "@alpha",
                    "subscriber_count": "1000",
                    "default_privacy": "private"
                },
                {
                    "id": "UC002",
                    "name": "Channel Beta",
                    "custom_url": "@beta",
                    "subscriber_count": "5000",
                    "default_privacy": "unlisted"
                }
            ]
        }
        youtube_manager.save_youtube_config(cfg)

        summary = youtube_manager.get_channels_summary()
        self.assertEqual(summary["count"], 2)
        self.assertEqual(summary["active_channel_id"], "UC001")

        # Select Beta
        sel = youtube_manager.set_active_channel("UC002")
        self.assertTrue(sel["ok"])
        self.assertEqual(sel["active_channel_id"], "UC002")

        # Update privacy
        priv = youtube_manager.update_channel_privacy("UC002", "public")
        self.assertTrue(priv["ok"])
        self.assertEqual(priv["default_privacy"], "public")

        # Delete Alpha
        d = youtube_manager.delete_channel("UC001")
        self.assertTrue(d["ok"])
        self.assertEqual(d["deleted"], True)
        self.assertEqual(len(youtube_manager.get_channels_summary()["channels"]), 1)

    def test_03_resolve_episode_media(self):
        # Test on existing stoi episode
        ep = STUDIO_DIR / "productions" / "stoi" / "episode_001"
        if ep.is_dir():
            media = youtube_manager.resolve_episode_media(ep)
            self.assertIsNotNone(media["video_path"])
            self.assertIsNotNone(media["thumbnail_path"])
            self.assertTrue(len(media["title"]) > 0)
            self.assertTrue(len(media["tags"]) > 0)

    def test_04_raw_json_credentials(self):
        # Web format
        web_json = json.dumps({
            "web": {
                "client_id": "web_id_123.apps.googleusercontent.com",
                "client_secret": "web_sec_456"
            }
        })
        res = youtube_manager.set_oauth_credentials(raw_json=web_json)
        self.assertTrue(res["ok"])
        cfg = youtube_manager.load_youtube_config()
        self.assertEqual(cfg["client_id"], "web_id_123.apps.googleusercontent.com")
        self.assertEqual(cfg["client_secret"], "web_sec_456")

        # Installed format
        installed_json = json.dumps({
            "installed": {
                "client_id": "inst_id_789.apps.googleusercontent.com",
                "client_secret": "inst_sec_012"
            }
        })
        res2 = youtube_manager.set_oauth_credentials(raw_json=installed_json)
        self.assertTrue(res2["ok"])
        cfg2 = youtube_manager.load_youtube_config()
        self.assertEqual(cfg2["client_id"], "inst_id_789.apps.googleusercontent.com")
        self.assertEqual(cfg2["client_secret"], "inst_sec_012")


if __name__ == "__main__":
    unittest.main()
