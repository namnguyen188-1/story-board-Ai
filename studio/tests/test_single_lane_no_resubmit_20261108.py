import tempfile,json,hashlib,unittest,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from studio_mcp.image_backend import StoryboardImageBackend,IMAGE_MODELS,StoryboardImageError
class Fake:
 def __init__(self):self.calls=[]
 def __call__(self,action,**kwargs):
  self.calls.append(action)
  if action=="receipts":return {"receipts":[]}
  if action=="render_batch":raise AssertionError("UNAUTHORIZED_RESUBMIT")
  if action=="health":return {"native":True,"sdk_image":True,"image_capability":True,
   "capabilities":["addToQueue","startImageProduction"],"queue_items":[]}
  raise AssertionError("Unexpected action: "+action)
class Guard(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup)
  self.root=Path(self.t.name);self.fake=Fake()
  self.backend=StoryboardImageBackend(self.root,transport=self.fake,enabled=True,
   spending_approved=True,max_new_images=1,model=IMAGE_MODELS[1],fallback=False)
  self.spec={"scene_id":"story_one_scene","prompt":"A calm wooden sailboat with vivid red sail at dawn, blue sea and rocky coast.","aspect_ratio":"16:9"}
  fp=hashlib.sha256(json.dumps({**self.spec,"model":IMAGE_MODELS[1],"fallback":False},sort_keys=True,ensure_ascii=False).encode()).hexdigest()
  path=self.backend._journal(self.spec["scene_id"]);path.parent.mkdir(parents=True,exist_ok=True)
  self.journal=path;self.fp=fp
 def write(self,fp):
  self.journal.write_text(json.dumps({"scene_id":self.spec["scene_id"],"fingerprint":fp,"state":"submit_uncertain"}),encoding="utf8")
 def test_unresolved_job_must_not_be_resubmitted(self):
  self.write(self.fp);old=self.journal.read_bytes()
  with self.assertRaisesRegex(StoryboardImageError,"UNCERTAIN|RESUBMIT"):
   self.backend.render_one_queue([self.spec])
  self.assertEqual(self.journal.read_bytes(),old)
  self.assertEqual(self.fake.calls,["receipts"])
 def test_changed_prompt_must_not_overwrite_uncertain_journal(self):
  self.write("another_fingerprint");old=self.journal.read_bytes()
  with self.assertRaisesRegex(StoryboardImageError,"UNCERTAIN|RESUBMIT"):
   self.backend.render_one_queue([self.spec])
  self.assertEqual(self.journal.read_bytes(),old)
  self.assertNotIn("render_batch",self.fake.calls)
if __name__=="__main__":unittest.main(verbosity=2)
