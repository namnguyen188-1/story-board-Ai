"""Offline test: never launches providers or creates paid jobs."""
import sys,json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,r"D:\STORYBOARD_AI\studio")
from cinematic_engine.drama_asset_first import AssetGateError
from pipeline_router import route_production
from drama_asset_review_api import snapshot,photo
args=SimpleNamespace(production_mode="cinematic_drama",image_provider="muse_video")
cases=[("DRAMA_PREPRODUCTION_NEEDS_VISUAL_REVIEW: 17 assets pending",20),
       ("DRAMA_SCENE_IMAGES_NEED_VISUAL_REVIEW: 1,2,3",20)]
for message,wanted in cases:
    with patch("cinematic_engine.drama_orchestrator.run_cinematic_drama",side_effect=AssetGateError(message)):
        result=route_production(args)
        assert result==wanted,(message,result)
        print("PAUSE_GATE_CORRECT_EXIT",result,message,flush=True)
with patch("cinematic_engine.drama_orchestrator.run_cinematic_drama",
           side_effect=AssetGateError("DRAMA_MUSE_IMAGE_GENERATION_FAILED: connection down")):
    try:route_production(args)
    except AssetGateError:print("GENUINE_FAILURE_STILL_FAILS",flush=True)
    else:raise AssertionError("REAL_FAILURE_WAS_WRONGLY_SUPPRESSED")
base=Path(r"D:\STORYBOARD_AI\studio\productions")
for series,part,num in [
    ("THIÊN SƯ: HUYỀN PHÙ TRẤN QUỶ","THI-N-S-HUY-N-PH-TR-N-QU",1),
    ("DRAMA","DRAMA",3)]:
    ep=base/part/f"episode_{num:03d}"
    s=snapshot(ep,series,num)
    visible=[x for x in s["assets"] if x.get("image_url")]
    assert len(s["assets"])==len(visible), "unrendered scenes should not be review cards"
    count=s["qc"]["asset_counts"]
    expected=sum(count.values())
    assert len(s["assets"])>=expected
    for kind in ("characters","locations","props"):
        x=next(v for v in s["assets"] if v["kind"]==kind and v["image_url"])
        assert photo(ep,x["kind"],x["id"]).is_file()
    print("REVIEW_ENDPOINT",series,"TOTAL_CARDS",len(s["assets"]),
          "MASTER_COUNTS",count,"REVIEW_PENDING",len(s["qc"]["blocked"]),flush=True)
