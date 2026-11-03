import unittest,json,copy,sys
from pathlib import Path
sys.path.insert(0,"D:/STORYBOARD_AI/studio")
from cinematic_engine.drama_asset_first import validate_story_continuity,bind_scene,AssetGateError
EP=Path("D:/STORYBOARD_AI/studio/scratch/multi_role_asset_first_e2e/episode_006")
class SixSceneContinuity(unittest.TestCase):
 def manifest(self):
  return json.loads((EP/"00_ASSET_PACK"/"asset_bible.json").read_text(encoding="utf-8"))
 def test_registry_six_scene_real_plan(self):
  m=self.manifest()
  self.assertEqual((len(m["characters"]),len(m["locations"]),len(m["props"]),len(m["scenes"])),(2,2,3,6))
  self.assertEqual(m["scenes"]["scene_0002"]["location_id"],m["scenes"]["scene_0003"]["location_id"])
  self.assertNotEqual(m["scenes"]["scene_0003"]["location_id"],m["scenes"]["scene_0004"]["location_id"])
 def test_state_good(self):
  self.assertEqual(validate_story_continuity(self.manifest())["status"],"PASS_STRUCTURED")
 def test_prop_teleport_fails(self):
  m=copy.deepcopy(self.manifest())
  m["scenes"]["scene_0002"]["prop_state"]["dien_thoai"]["start"]["holder"]="Minh"
  self.assertIn("PROP_TELEPORT_OR_MUTATION",[e["reason"] for e in validate_story_continuity(m)["issues"]])
 def test_unauthorized_costume_fails(self):
  m=copy.deepcopy(self.manifest())
  m["scenes"]["scene_0002"]["wardrobe_state"]["lan"]="different_red_dress"
  self.assertIn("UNSCRIPTED_OUTFIT_CHANGE",[e["reason"] for e in validate_story_continuity(m)["issues"]])
 def test_no_fake_scene_image_pass(self):
  p=json.loads((EP/"drama_plan.json").read_text(encoding="utf-8"))
  from unittest.mock import patch
  # A changed image must lose approval even when scene_master.png exists.
  with patch("cinematic_engine.drama_asset_first.sha",return_value="unapproved_changed_digest"):
   with self.assertRaises(AssetGateError):
    bind_scene(EP,p["scenes"][5],verify_scene_image=True)
