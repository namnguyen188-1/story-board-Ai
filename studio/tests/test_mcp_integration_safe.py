"""Mock transport tests: NO MCP generation requests and NO API costs."""
from pathlib import Path
import sys,hashlib,shutil
from PIL import Image
root=Path(__file__).parent
sys.path.insert(0,str(root))
from mcp_v2_images import make_image,preflight
from series_studio import parser
class FakeTransport:
    requests=0
    def __call__(self, action, **kwargs):
        if action=="render_batch":
            self.requests+=1
            assert len(kwargs["jobs"])==1
            job=kwargs["jobs"][0]
            src=root/"mcp_image_test_result"/"city_lost_time_mcp_scene_001.jpg"
            assert src.is_file(), "MCP verified fixture missing"
            target=Path(job["output_dir"])/(job["job_id"]+".jpg")
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(src,target)
            return {"receipts":[{
                "job_id":job["job_id"],"scene_id":job["scene_id"],
                "path":str(target),"bytes":target.stat().st_size,
                "sha256":hashlib.sha256(target.read_bytes()).hexdigest(),
                "mime_type":"image/jpeg","media_id":"verified-fixture",
                "model_used":job["model"],"attempted_models":[job["model"]]
            }]}
        if action=="health":
            return {"native":True,"sdk_image":True,"image_capability":True,
                    "capabilities":["addToQueue","startImageProduction"]}
        if action=="receipts":
            return {"receipts":[]}
        raise AssertionError("unexpected transport action "+str(action))
transport=FakeTransport()
preflight()
p=root/"diagnostics"/"mcp_integration_mock_scene.png"
prompt="Original whiteboard city skyline with frozen raindrops, a clock tower, and one clockmaker holding a pocket watch."
src=make_image(prompt,p,series="MCP Adapter Unit QA",episode=988,scene=1,
               max_new_images=1,model_index=1,transport=transport)
assert src==str(p) and p.stat().st_size>10000
with Image.open(p) as img:
    assert img.width>0 and abs(img.width/img.height-16/9)<0.02, img.size
print("MOCK_MCP_IMAGE_COPY_PASS")
src2=make_image(prompt,p,series="MCP Adapter Unit QA",episode=988,scene=1,
               max_new_images=1,model_index=1,transport=transport)
assert transport.requests==1,(transport.requests,src2)
print("RECEIPT_RESUME_NO_DUPLICATE_PASS")
try:
    make_image(prompt,root/"diagnostics"/"forbidden_second.png",
               series="MCP Adapter Unit QA",episode=988,scene=2,
               max_new_images=1,model_index=1,transport=transport)
except Exception as e:
    assert "BUDGET" in str(e).upper() or "EXHAUSTED" in str(e).upper(),type(e).__name__+str(e)
    print("MCP_IMAGE_BUDGET_GUARD_PASS")
else:
    raise AssertionError("one-image budget should block the second image")
args=parser().parse_args(["run","--prompt","An animation test with original story content",
     "--mode","live","--image-provider","mcp_v2","--mcp-model-index","1",
     "--mcp-max-images","4"])
assert args.image_provider=="mcp_v2" and args.mcp_max_images==4
print("MCP_CLI_SELECTORS_PASS")
print("ALL_MCP_ADAPTER_MOCK_TESTS_PASS")
