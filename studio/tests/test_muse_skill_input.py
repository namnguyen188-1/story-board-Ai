import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from studio_input_modes import parse_locked_screenplay
BODY='FORMAT & STYLE:\nAn 8-second continuous shot.\nCHARACTERS:\nNo people.\nSETTING & START STATE:\nA white paper boat on still water.\nLIGHTING & COLOR:\nNeutral morning light.\nCAMERA:\nSlow push.\nTIMED ACTION:\n0-8 seconds: ripples move the boat.\nEND STATE:\nBoat rests near a leaf.\nAUDIO:\nNo generated dialogue or narration. EDITOR VO: "A small journey begins."\nCONSTRAINTS:\nNo added text.'
class SkillInputTests(unittest.TestCase):
 def test_skill_scene_identifier_and_timeline_are_accepted(self):
  scenes=parse_locked_screenplay("SCENE_001 — 00:00–00:08, clip dự kiến 8 giây.\n"+BODY)
  self.assertEqual(len(scenes),1);self.assertEqual(scenes[0]["script_seconds"],8)
  self.assertIn("TIMED ACTION:",scenes[0]["description"])
  self.assertEqual(scenes[0]["narration"],"A small journey begins.")
 def test_legacy_header_remains_supported(self):
  scenes=parse_locked_screenplay("SHOT 1\n"+BODY+"\nSHOT 2\n"+BODY)
  self.assertEqual([s["scene_number"] for s in scenes],[1,2])
 def test_missing_scene_is_rejected(self):
  with self.assertRaises(ValueError):parse_locked_screenplay("SCENE_002 — 00:08–00:16\n"+BODY)
if __name__=="__main__":unittest.main()
