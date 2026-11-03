"""New direct one-image MCP render entry must fail before paid journal on stale queue."""
import sys,json
from pathlib import Path
from tempfile import TemporaryDirectory
sys.path.insert(0,r"D:\STORYBOARD_AI\studio")
from studio_mcp.image_backend import StoryboardImageBackend,StoryboardImageError,IMAGE_MODELS
def fake_tool(actions,items):
    def call(action,**kwargs):
        actions.append(action)
        if action!="health":raise AssertionError("Forbidden paid render_batch")
        return {"native":True,"sdk_image":True,"image_capability":True,
          "capabilities":["addToQueue","startImageProduction"],
          "queue_items":items,"running":False}
    return call
for case,items in [
    ("already_completed",[{"id":"shot_123","status":"completed","asset_kind":"image","has_prompt":True}]),
    ("user_pending",[{"id":"shot_1","status":"pending","asset_kind":"video","has_prompt":True}])
]:
    with TemporaryDirectory(prefix="studio_mcp_singleguard_") as tmp:
        actions=[]
        root=Path(tmp)/"project"
        backend=StoryboardImageBackend(root,transport=fake_tool(actions,items),
          enabled=True,spending_approved=True,max_new_images=1,
          model=IMAGE_MODELS[1],fallback=False)
        try:
            backend.render_one_queue([{"scene_id":"qa_scene_0001",
                "prompt":"A whimsical original river village drawing in bright blue and green.",
                "aspect_ratio":"16:9"}])
        except StoryboardImageError as exc:
            assert "STORYBOARD_IMAGE_TOOL_QUEUE_STALE_NO_SUBMIT" in str(exc),str(exc)
        else:raise AssertionError("Image render was wrongly allowed")
        assert actions==["health"],actions
        assert not root.exists(),"No reservation or uncertain journal should be created"
        print("DIRECT_RENDER_NO_PAID_FAILFAST_PASS",case,flush=True)
print("NO_FALSE_SUBMIT_UNCERTAIN_AFTER_READ_ONLY_QUEUE_REJECTION_PASS",flush=True)
