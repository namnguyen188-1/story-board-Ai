"""Muse saved-session, multi-account UI and rendering integration contracts."""
import os,sys,unittest
from pathlib import Path
from html.parser import HTMLParser
ROOT=Path(os.environ.get("STORYBOARD_TEST_ROOT",str(Path(__file__).resolve().parents[1])))
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/"tests"))

class Controls(HTMLParser):
 def __init__(self):super().__init__();self.ids={};self.sources=[]
 def handle_starttag(self,tag,attrs):
  attrs=dict(attrs)
  if "id" in attrs:self.ids[attrs["id"]]=(tag,attrs)
  if tag=="option":self.sources.append(attrs.get("value"))

class MuseManagerUI(unittest.TestCase):
 def test_current_multi_account_controls_are_bound(self):
  html=(ROOT/"web/index.html").read_text(encoding="utf-8")
  js=(ROOT/"web/app.js").read_text(encoding="utf-8")
  controls=Controls();controls.feed(html)
  required={"modalMuseManager":"div","btnHeaderMuse":"button","btnModalAddAccount":"button","museModalAccountCardsContainer":"div","btnFinishMuseLoginModal":"button","radioModalRR":"input","radioModalActive":"input","settingsMuseCountBadge":"span"}
  for key,tag in required.items():
   self.assertIn(key,controls.ids,"Missing Muse manager control: "+key)
   self.assertEqual(controls.ids[key][0],tag)
  self.assertIn("openMuseModal()",controls.ids["btnHeaderMuse"][1].get("onclick",""))
  self.assertIn("addMuseAccountPrompt()",controls.ids["btnModalAddAccount"][1].get("onclick",""))
  self.assertIn("finishMuseLogin(true)",controls.ids["btnFinishMuseLoginModal"][1].get("onclick",""))
  for key,mode in (("radioModalRR","round_robin"),("radioModalActive","active_only")):
   self.assertEqual(controls.ids[key][1].get("type"),"radio")
   self.assertEqual(controls.ids[key][1].get("value"),mode)
   self.assertIn("setMuseDispatchMode",controls.ids[key][1].get("onchange",""))
  self.assertIn("muse_video",controls.sources)
  self.assertNotIn("inMuseKey",controls.ids)
  for handler in ("openMuseModal","addMuseAccountPrompt","finishMuseLogin","setMuseDispatchMode","loadMuseStatus","loginMuseAccount","selectMuseAccount"):
   self.assertRegex(js,r"(?:function\s+"+handler+r"\s*\(|window\."+handler+r"\s*=)","Missing handler: "+handler)

def test_muse_video_suite():
 import importlib.util,subprocess
 if any(importlib.util.find_spec(name) is None for name in ("av","muse_cli")):
  from muse_video_provider import get_muse_config
  cfg=get_muse_config()
  if not cfg["configured"] or Path(sys.executable).resolve()==Path(cfg["python_executable"]).resolve():
   raise AssertionError("Configured Muse runtime lacks required dependencies")
  print("Running full integration suite in configured Muse runtime",flush=True)
  result=subprocess.run([cfg["python_executable"],str(Path(__file__).resolve())],env=os.environ.copy())
  if result.returncode:raise AssertionError("Configured Muse integration suite failed")
  return
 from test_muse_cli_provider import ProviderTests
 from test_muse_skill_input import SkillInputTests
 from test_muse_gateway_worker import GatewayWorkerTests
 from test_muse_login import MuseLoginTests
 from test_native_muse_audio_merge import NativeMerge
 suite=unittest.TestSuite()
 for cls in (ProviderTests,SkillInputTests,GatewayWorkerTests,MuseLoginTests,NativeMerge,MuseManagerUI):
  suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(cls))
 result=unittest.TextTestRunner(verbosity=2).run(suite)
 if not result.wasSuccessful():raise AssertionError("Muse integration regression")
 print("MUSE_SAVED_SESSION_MULTI_ACCOUNT_INTEGRATION_PASS",result.testsRun)
if __name__=="__main__":test_muse_video_suite()