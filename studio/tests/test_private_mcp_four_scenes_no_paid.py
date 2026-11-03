"""Four-scene private Studio pipeline smoke with fake receipts, no external MCP."""
from pathlib import Path
from unittest.mock import patch
from tempfile import TemporaryDirectory
import sys
from PIL import Image
studio=Path(r"D:\STORYBOARD_AI\studio")
sys.path.insert(0,str(studio))
import mcp_v2_batch as pipeline
sample=studio/"mcp_image_test_result"/"city_lost_time_mcp_scene_001.jpg"
assert sample.is_file()
class Fake:
    calls=0
    def __init__(self,root,**kw):
        self.root=Path(root)
        self.kw=kw
        assert str(self.root).startswith(str(studio/"runtime"/"private_mcp_outputs"))
    def preflight(self):
        return {"native":True,"sdk_image":True}
    def render_one_queue(self,specs):
        Fake.calls+=1
        assert len(specs)==4 and self.kw["max_new_images"]==4
        return {s["scene_id"]:{"path":str(sample)} for s in specs}
scenes=[{"description":f"Original fictional nature scene {i} with mountains and river",
         "visual_setup":"Wide bright landscape with well balanced composition"} for i in range(1,5)]
bible={"characters":[],"visual_style":"natural color photography"}
models=("🍌 Nano Banana Pro","🍌 Nano Banana 2 Lite","🍌 Nano Banana 2.1")
with TemporaryDirectory(prefix="studio_private_mcp_scenes_") as temp:
    with patch.object(pipeline,"preflight",return_value=(Fake,models)):
        n=pipeline.generate_episode_images(scenes,bible,series="Independent Test",episode=1,
                         episode_dir=Path(temp),max_new_images=4,
                         model_index=1,backend_factory=Fake)
        assert n==4 and Fake.calls==1
        for i in range(1,5):
            media=Path(temp)/"scenes"/f"scene_{i:04d}"/"image.png"
            assert media.is_file()
            with Image.open(media) as img:
                img.verify()
print("PRIVATE_MCP_FOUR_SCENE_MOCK_RENDER_PASS",flush=True)
