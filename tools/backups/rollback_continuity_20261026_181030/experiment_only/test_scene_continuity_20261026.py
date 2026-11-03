# -*- coding: utf-8 -*-
"""Unpaid regression guards for cross-scene continuity; no video account calls."""
import unittest, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cinematic_engine.scene_continuity import continuity_instruction
from muse_video_provider import format_real_acting_prompt
class ContinuityGuards(unittest.TestCase):
 def setUp(self):
  self.old={"summary":"Robot Ti installs a golden gear", "setting":"repair workshop",
    "characters_present":["Robot Ti"],"dialogue_beats":[{"speaker":"Robot Ti","text":"Xong rồi","action":"puts the gear in the copper lantern"}]}
  self.new={"summary":"Robot Ti winds the crank","setting":"repair workshop",
    "characters_present":["Robot Ti"],"description":"Robot winds the crank",
    "visual_setup":"The copper lantern stays on the bench.","dialogue":"Chiếc đèn sáng rồi!"}
  self.bible={"production_genre":"animation","visual_style":"3D animation","characters":[{"name":"Robot Ti","appearance":"blue robot with a yellow scarf"}]}
 def test_same_scene_start_state_kept(self):
  msg=continuity_instruction(self.old,self.new)
  self.assertIn("SAME LOCATION",msg)
  self.assertIn("puts the gear",msg)
  self.assertIn("Xong rồi",msg)
 def test_new_location_needs_transition(self):
  other=dict(self.new, setting="garden")
  self.assertIn("LOCATION CHANGE",continuity_instruction(self.old,other))
 def test_muse_prompt_has_previous_scene(self):
  scene=dict(self.new,continuity_context=continuity_instruction(self.old,self.new))
  prompt=format_real_acting_prompt(scene,self.bible)
  self.assertIn("SCENE-TO-SCENE CONTINUITY",prompt)
  self.assertIn("PREVIOUS SCENE EVENT",prompt)
  self.assertIn("3D CGI",prompt)
 def test_9_fields_shape_retained(self):
  keys=["FORMAT & STYLE","CHARACTERS","SETTING & START STATE","LIGHTING & COLOR",
        "CAMERA","TIMED ACTION","END STATE","AUDIO","CONSTRAINTS"]
  raw="\n".join(k+": placeholder" for k in keys)
  scene=dict(self.new,raw_9_fields=raw,continuity_context=continuity_instruction(self.old,self.new))
  actual=format_real_acting_prompt(scene,self.bible)
  self.assertEqual([x for x in keys if x+":" in actual],keys)
  self.assertIn("PREVIOUS SCENE EVENT:",actual)
  self.assertEqual(actual.count("SETTING & START STATE:"),1)
 def test_muse_missing_scene_bridge_blocked(self):
  p=Path(__file__).resolve().parents[1]/"cinematic_engine"/"drama_orchestrator.py"
  code=p.read_text(encoding="utf-8")
  self.assertIn('if missing_nums and image_provider == "muse_video":',code)
  self.assertIn('configured_workers = 1',code)
if __name__=="__main__":unittest.main()
