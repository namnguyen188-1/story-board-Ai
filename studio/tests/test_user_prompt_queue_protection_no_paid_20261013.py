"""Ensure own-user pending shot_1 is protected, isolated canary target allows test only."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import os,sys
sys.path.insert(0,r"D:\STORYBOARD_AI\studio")
from studio_mcp.image_backend import StoryboardImageBackend,StoryboardImageError,IMAGE_MODELS
h={"native":True,"sdk_image":True,"image_capability":True,
   "capabilities":["addToQueue","startImageProduction"],"running":False,
   "queue_items":[{"id":"shot_1","status":"pending","asset_kind":"video","has_prompt":True}]}
with TemporaryDirectory() as tmp:
    calls=[]
    def safe(action,**kwargs):
        calls.append(action)
        assert action=="health"
        return h
    backend=StoryboardImageBackend(tmp,transport=safe,
        enabled=True,spending_approved=False,max_new_images=0,
        model=IMAGE_MODELS[1],fallback=False)
    with patch.dict(os.environ,{"STORYBOARD_CANARY_TARGET_ID":""}):
        try:backend.preflight()
        except StoryboardImageError as exc:assert "QUEUE_STALE_NO_SUBMIT" in str(exc)
        else:raise AssertionError("Original user's queued prompt could be erased")
    with patch.dict(os.environ,{"STORYBOARD_CANARY_TARGET_ID":"0123456789ABCDEF0123456789ABCDEF"}):
        assert backend.preflight()["queue_items"][0]["has_prompt"] is True
    assert not any(Path(tmp).glob(".storyboard_image_jobs/*"))
    assert calls==["health","health"]
print("USER_POPULATED_FLOW_PROMPT_PROTECTED",flush=True)
print("EXPLICIT_ISOLATED_CANARY_ALLOWED_NO_SPEND",flush=True)
