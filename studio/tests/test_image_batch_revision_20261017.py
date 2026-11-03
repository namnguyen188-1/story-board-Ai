import sys,unittest,tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import mcp_v2_batch as batch
class RevisionTests(unittest.TestCase):
    def test_same_batch_resumes_same_budget_changed_content_gets_separate_budget(self):
        roots=[]
        class Backend:
            def __init__(self,root,**kw):roots.append(root)
            def preflight(self):pass
            def render_one_queue(self,specs):return {s["scene_id"]:{} for s in specs}
        def imported(receipt,target,*args):
            target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b"x"*1025)
        with tempfile.TemporaryDirectory() as folder, \
             patch.object(batch,"PRODUCTION_ROOT",Path(folder)/"outputs"), \
             patch.object(batch,"preflight",return_value=(Backend,["m0","m1","m2"])), \
             patch("studio_flow_accounts.apply_worker_env",return_value={"name":"test"}), \
             patch.object(batch,"import_receipt_image",side_effect=imported):
            legacy=Path(folder)/"outputs"/"storyboard_studio_mcp_test_ep001"
            legacy.mkdir(parents=True);(legacy/"old-budget").write_text("preserve")
            for text in ["An original dramatic scene","An original dramatic scene","A changed dramatic scene"]:
                batch.generate_episode_images([{"description":text}],{},series="test",episode=1,
                    episode_dir=Path(folder)/"episode",max_new_images=1,backend_factory=Backend)
            self.assertEqual(roots[0],roots[1],"Resume must keep durable receipts")
            self.assertNotEqual(roots[1],roots[2],"Changed content must not inherit exhausted old slots")
            self.assertNotEqual(roots[0],legacy)
            self.assertEqual((legacy/"old-budget").read_text(),"preserve")
if __name__=="__main__":unittest.main()
