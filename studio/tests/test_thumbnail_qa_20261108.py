import unittest,tempfile,sys,json,types
from pathlib import Path
from unittest.mock import patch
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import seo_packager as seo
class Tests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup)
  self.ep=Path(self.t.name)/"episode_001";self.ep.mkdir()
  (self.ep/"plan.json").write_text(json.dumps({"title":"La fuerza del silencio","genre":"stoic","bible":{"characters":[{"name":"Marcus Aurelius"}]}}),encoding="utf8")
  self.calls=[]
  fake=types.ModuleType("mcp_v2_images")
  def gen(prompt,out,**kw):
   self.calls.append({"prompt":prompt,"out":str(out),**kw})
   ratio=kw["aspect_ratio"]
   Image.new("RGB",(1536,864) if ratio=="16:9" else (1080,1920),(37,91,133)).save(out,format="PNG")
  fake.make_image=gen
  clean=types.ModuleType("clean_watermark");clean.remove_gemini_watermark=lambda path:None
  organizer=types.ModuleType("project_organizer");organizer.organize_episode=lambda d:None
  self.patch=patch.dict(sys.modules,{"mcp_v2_images":fake,"clean_watermark":clean,"project_organizer":organizer})
  self.patch.start();self.addCleanup(self.patch.stop)
  import studio_mcp.accounts as accounts
  import studio_mcp.production_tab as tabs
  import studio_mcp.transport as mcp
  import studio_mcp.image_backend as backend
  self.session_events=[]
  class FakeHealth:
   def __call__(self,action,**kwargs):
    assert action=="health"
    return {"native":True,"sdk_image":True,"image_capability":True,
            "capabilities":["addToQueue","startImageProduction"],
            "queue_items":[],"running":False}
  fake_tab="a"*32
  def make_target(*args):
   self.session_events.append("prepare")
   return fake_tab
  def close_target(*args):
   self.session_events.append("close")
   return {"ok":True}
  def abandon_target(*args):
   self.session_events.append("abandon")
   return {"ok":True}
  self.session_patches=[
   patch.object(accounts,"active_account",return_value={"id":"qa_account"}),
   patch.object(accounts,"account_tool_url",return_value="https://flow.google.com/project/example/tool/example"),
   patch.object(tabs,"prepare",side_effect=make_target),
   patch.object(tabs,"close_completed",side_effect=close_target),
   patch.object(tabs,"abandon_fresh",side_effect=abandon_target),
   patch.object(mcp,"LocalFlowMcpTransport",return_value=object()),
   patch.object(backend,"StoryboardImageTransport",return_value=FakeHealth()),
  ]
  for obj in self.session_patches:
   obj.start();self.addCleanup(obj.stop)
 def call(self,ratio="16:9",force=False):
  return seo.generate_thumbnail_with_flow(self.ep,series_name="TEST_STOIC_THUMBNAIL",genre="stoic",
       hook_text="EL PODER DEL SILENCIO",aspect_ratio=ratio,force_regenerate=force)
 def test_landscape_is_actual_jpeg(self):
  with patch.object(seo,"is_vertical_short_episode",return_value=False):
   got=self.call()
  self.assertTrue(got["ok"],got)
  self.assertEqual(got["aspect_ratio"],"16:9")
  with Image.open(got["thumbnail_file"]) as im:
   self.assertEqual(im.format,"JPEG")
   self.assertGreater(im.width,im.height)
  self.assertEqual(len(self.calls),1)
 def test_explicit_landscape_overrides_short_episode(self):
  with patch.object(seo,"is_vertical_short_episode",return_value=True):
   got=self.call(ratio="16:9")
  self.assertEqual(got["aspect_ratio"],"16:9")
  self.assertFalse(got["is_short"])
  self.assertTrue(got["thumbnail_file"].endswith("thumbnail_seo.jpg"))
 def test_short_is_actual_vertical_jpeg(self):
  with patch.object(seo,"is_vertical_short_episode",return_value=False):
   got=self.call(ratio="9:16")
  with Image.open(got["thumbnail_file"]) as im:
   self.assertEqual((im.format,im.size),("JPEG",(1080,1920)))
  self.assertEqual(self.calls[0]["aspect_ratio"],"9:16")
 def test_cache_read_does_not_recharge(self):
  with patch.object(seo,"is_vertical_short_episode",return_value=False):
   one=self.call("16:9"); two=self.call("16:9")
  self.assertEqual(two["backend"],"cached_existing")
  self.assertEqual(len(self.calls),1)
 def test_invalid_png_disguised_as_jpg_regenerated(self):
  bad=self.ep/"thumbnail_seo.jpg"
  Image.new("RGB",(1536,864),"red").save(bad,format="PNG")
  with patch.object(seo,"is_vertical_short_episode",return_value=False):
   got=self.call("16:9")
  self.assertEqual(len(self.calls),1)
  with Image.open(got["thumbnail_file"]) as im:self.assertEqual(im.format,"JPEG")
 def test_one_session_is_prepared_and_released(self):
  with patch.object(seo,"is_vertical_short_episode",return_value=False):
   self.assertTrue(self.call()["ok"])
  self.assertEqual(self.session_events,["prepare","close"])
 def test_prepare_failure_does_not_generate(self):
  import studio_mcp.production_tab as tabs
  with patch.object(tabs,"prepare",side_effect=RuntimeError("PREFLIGHT_REJECTED")):
   got=self.call()
  self.assertFalse(got["ok"])
  self.assertIn("PREFLIGHT_REJECTED",got["error"])
  self.assertEqual(len(self.calls),0)
 def test_denial_no_alternate_or_overwrite(self):
  old=self.ep/"thumbnail_seo.jpg"
  original=b"existing-invalid-preserve"
  old.write_bytes(original)
  import mcp_v2_images
  with patch.object(mcp_v2_images,"make_image",side_effect=RuntimeError("GOOGLE_UNUSUAL_ACTIVITY")):
   with patch.object(seo,"is_vertical_short_episode",return_value=False):
    got=self.call("16:9")
  self.assertFalse(got["ok"])
  self.assertIn("GOOGLE_UNUSUAL_ACTIVITY",got["error"])
  self.assertEqual(old.read_bytes(),original)
if __name__=="__main__":unittest.main(verbosity=2)
