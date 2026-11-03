"""Test MCP 4-image batch plumbing without sending API/web jobs."""
from pathlib import Path
import sys
studio=Path(r"D:\STORYBOARD_AI\studio")
sys.path.insert(0,str(studio))
from mcp_v2_batch import generate_episode_images
from PIL import Image
source=studio/"mcp_image_test_result"/"city_lost_time_mcp_scene_001.jpg"
assert source.is_file()
class Fake:
    calls=0
    def __init__(self,root,**kwargs):
        self.kwargs=kwargs
    def preflight(self):
        return {"native":True,"sdk_image":True}
    def render_one_queue(self,specs):
        Fake.calls+=1
        assert len(specs)==4 and self.kwargs["max_new_images"]==4
        return {x["scene_id"]:{"path":str(source)} for x in specs}
scenes=[{"description":f"Scene number {i} of an original city mystery with visible clocktower",
         "visual_setup":"Wide whiteboard silhouette and cyan clock hands"} for i in range(4)]
bible={"characters":[{"name":"Ethan","appearance":"black ink contours"}],
       "visual_style":"minimal ink whiteboard"}
folder=studio/"productions"/"MCP-Batch-4-Mock-QA"/"episode_099"
count=generate_episode_images(scenes,bible,series="MCP Batch 4 Mock QA",
                             episode=99,episode_dir=folder,
                             max_new_images=4,backend_factory=Fake)
assert count==4 and Fake.calls==1
for i in range(1,5):
    path=folder/"scenes"/f"scene_{i:04d}"/"image.png"
    with Image.open(path) as im:
        im.verify()
print("MOCK_SINGLE_QUEUE_FOUR_IMAGES_PASS",flush=True)
try:
    generate_episode_images(scenes,bible,series="MCP Batch 4 Mock QA",episode=99,
                            episode_dir=folder,max_new_images=3,backend_factory=Fake)
except Exception as e:
    assert "budget" in str(e).lower()
    print("MOCK_IMAGE_BUDGET_GUARD_PASS",flush=True)
else:
    raise AssertionError("budget must fail before any paid job")
