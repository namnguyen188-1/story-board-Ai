"""No-paid regression: stale remote queue must fail before Python journals/reserves credit."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json,sys
ROOT=Path(r"D:\STORYBOARD_AI\studio")
sys.path.insert(0,str(ROOT))
from studio_mcp.image_backend import StoryboardImageBackend,StoryboardImageError,IMAGE_MODELS
caps=["addToQueue","startImageProduction"]
def health(items,running=False):
    return {"native":True,"sdk_image":True,"image_capability":True,
            "capabilities":caps,"queue_items":items,"queue_count":len(items),"running":running}
cases=[
    ("empty",health([]),True),
    ("placeholder",health([{"id":"shot_1","status":"pending","asset_kind":"video","has_prompt":False}]),True),
    ("user_populated_pending",health([{"id":"shot_1","status":"pending","asset_kind":"video","has_prompt":True}]),False),
    ("completed",health([{"id":"shot_1700000_0","status":"completed","asset_kind":"image"}]),False),
    ("busy",health([],True),False),
    ("pending-other",health([{"id":"shot_99","status":"pending","asset_kind":"image"}]),False),
]
with TemporaryDirectory(prefix="studio_guard_test_") as folder:
    for name,state,allowed in cases:
        called=[]
        def fake(action,**kwargs):
            called.append(action)
            if action!="health":raise AssertionError("Unexpected remote paid operation")
            return state
        backend=StoryboardImageBackend(Path(folder)/name,transport=fake,
              enabled=True,spending_approved=False,max_new_images=0,model=IMAGE_MODELS[1],fallback=False)
        failed=False
        try:backend.preflight()
        except StoryboardImageError as exc:
            assert "QUEUE_STALE_NO_SUBMIT" in str(exc),str(exc)
            failed=True
        assert failed is (not allowed),(name,failed,allowed)
        assert called==["health"],called
        assert not (Path(folder)/name).exists(),"No paid reservation may exist"
        print("READ_ONLY_QUEUE_PREFLIGHT_PASS",name,"allowed",allowed,flush=True)
print("NO_CREDIT_AND_NO_JOURNAL_GUARD_PASS",flush=True)
