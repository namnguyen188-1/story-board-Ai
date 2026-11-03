"""Budget regression: 62 scenes at 20-image cap, explicit reuse, never call Flow."""
from pathlib import Path
import json,sys, tempfile
from types import SimpleNamespace
from unittest.mock import patch
from PIL import Image
studio=Path(r"D:\STORYBOARD_AI\studio")
sys.path.insert(0,str(studio))
from studio_image_budget import inspect_budget,required_images,select_keyframes,ImageBudgetError,cached_plan_scene_count
import mcp_v2_batch as pipeline
import series_studio
assert required_images(25.8,25)==62
for policy,count,budget in [("unique",62,20),("reuse",62,20)]:
    try:
        result=inspect_budget(count,budget,policy)
        if policy=="unique": raise AssertionError("Must block unapproved 62 jobs")
        assert result["image_jobs"]==20
    except ImageBudgetError:
        if policy!="unique": raise
anchors,mapping=select_keyframes(62,20)
assert len(anchors)==20 and anchors[0]==1 and anchors[-1]==62
assert len(mapping)==62 and set(mapping.values())==set(anchors)
assert inspect_budget(62,62,"unique")["image_jobs"]==62
print("BUDGET_62_20_BLOCK_OR_REUSE_PASS",flush=True)

plan=studio/"productions"/"RELA-JATE-Y-MANIFESTARA-S-TODO-LO-QUE-DESEES-ESTOICISMO"/"episode_001"/"plan.json"
saved=json.loads(plan.read_text(encoding="utf-8"))
cfg=saved["config"]
mtime=plan.stat().st_mtime_ns
assert cached_plan_scene_count(plan,minutes=25.8,scene_seconds=25,input_mode="link")==62
assert cached_plan_scene_count(plan,minutes=10,scene_seconds=25,input_mode="link") is None
args=SimpleNamespace(**cfg)
assert series_studio.produce_plan(args,plan.parent.parent,plan.parent,cfg["prompt"]) is not None
assert plan.stat().st_mtime_ns==mtime
assert len(json.loads(plan.read_text(encoding="utf-8"))["scenes"])==62
print("ACTUAL_CACHED_62_SCENES_REUSED_WITHOUT_GEMINI_PASS",flush=True)

model=("🍌 Nano Banana Pro","🍌 Nano Banana 2 Lite","🍌 Nano Banana 2.1")
class Backend:
    calls=0
    batch_sizes=[]
    def __init__(self,scope,**kw):
        assert 0<kw["max_new_images"]<=20
        self.limit=kw["max_new_images"]
    def preflight(self):return {"native":True}
    def render_one_queue(self,specs):
        Backend.calls+=1
        Backend.batch_sizes.append(len(specs))
        assert len(specs)==20
        # tiny local synthetic receipt; no external network.
        return {spec["scene_id"]:{"path":str(png)} for spec in specs}
scenes=[{"description":f"Original scene {i} with evocative landscape and walking figures",
         "visual_setup":"Cinematic storyboard shot with warm lighting"} for i in range(62)]
bible={"characters":[],"visual_style":"cinematic color","production_genre":"stoic","visual_style_mode":"hand_color"}
with tempfile.TemporaryDirectory(prefix="studio_budget62_") as temp:
    png=Path(temp)/"sample.png"
    Image.new("RGB",(400,300),(30,70,120)).save(png)
    with patch.object(pipeline,"preflight",return_value=(Backend,model)),\
         patch.object(pipeline,"import_receipt_image",wraps=pipeline.import_receipt_image) as importer:
        total=pipeline.generate_episode_images(scenes,bible,
             series="Budget Regression",episode=1,episode_dir=Path(temp),
             max_new_images=20,model_index=1,backend_factory=Backend,
             visual_policy="reuse")
    assert total==62 and Backend.calls==1 and Backend.batch_sizes==[20],Backend.batch_sizes
    assert importer.call_count==20
    mapping_data=json.loads((Path(temp)/"visual_mapping.json").read_text(encoding="utf-8"))
    assert mapping_data["remote_jobs"]==20 and mapping_data["policy"]=="reuse"
    for i in range(1,63):
        media=Path(temp)/"scenes"/f"scene_{i:04d}"/"image.png"
        with Image.open(media) as img:img.verify()
    print("MCP_20_REMOTE_JOBS_62_SCENE_IMAGES_MOCK_PASS",flush=True)
print("FULL_SCENE_BUDGET_NO_SPEND_REGRESSION_PASS",flush=True)
