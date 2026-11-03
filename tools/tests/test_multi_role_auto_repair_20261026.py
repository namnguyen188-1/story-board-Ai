"""Offline repair regression from REAL saved scenes 63 and 67; no Muse API calls."""
from pathlib import Path
import sys, json, tempfile, copy, ast, hashlib, py_compile
ROOT=Path(r"D:\STORYBOARD_AI\studio")
sys.path.insert(0,str(ROOT))
from cinematic_engine.drama_skill9 import build_scene
from cinematic_engine.drama_auto_repair import (
    parse_9_fields, arm_one_repair, load_armed_repair,
    simplified_prompt, META_NAME, ALT_NAME, OLD_RECEIPT_NAME
)
EP=ROOT/"productions"/"ho-t-h-nh-3d"/"episode_001"
plan=json.loads((EP/"drama_plan.json").read_text(encoding="utf-8"))
assert len(plan["scenes"])==90
tested=0
for n in [63,67]:
    scene=copy.deepcopy(plan["scenes"][n-1])
    previous=plan["scenes"][n-2]
    scene["raw_9_fields"]=build_scene(scene,plan["cast"],previous,genre="animation",
        visual_style="color_animation",language="Vietnamese",aspect="9:16",
        seconds=10,index=n)
    original=scene["raw_9_fields"]
    oh,orig_fields=parse_9_fields(original)
    with tempfile.TemporaryDirectory(prefix=f"muse_auto_repair_{n}_") as td:
        d=Path(td)
        rec=d/"muse_job.json"
        accepted={"state":"accepted","cli_ack":True,"session_id":"QA-PENDING"}
        rec.write_text(json.dumps(accepted),encoding="utf-8")
        assert not arm_one_repair(d,scene,"MUSE_SCENE_REVIEW_REQUIRED"),"Pending must not be retried"
        assert rec.exists() and not (d/META_NAME).exists()
        failure={"state":"failed","cli_ack":True,"session_id":"QA-FAILED"}
        rec.write_text(json.dumps(failure),encoding="utf-8")
        assert not arm_one_repair(d,scene,"MUSE_SCENE_REVIEW_REQUIRED: moderation refusal")
        assert rec.exists()
        for protected_reason in ("integrity_check_failed","no_video_review_required","moderation_refusal"):
            rec.write_text(json.dumps({**failure,"terminal_reason":protected_reason}),encoding="utf-8")
            assert not arm_one_repair(d,scene,"MUSE_SCENE_REVIEW_REQUIRED: completed without video")
            assert rec.exists() and not (d/META_NAME).exists()
        rec.write_text(json.dumps(failure),encoding="utf-8")
        assert arm_one_repair(d,scene,"MUSE_SCENE_REVIEW_REQUIRED: completed without valid video")
        assert not rec.exists() and (d/OLD_RECEIPT_NAME).exists()
        assert not arm_one_repair(d,scene,"MUSE_SCENE_REVIEW_REQUIRED")
        rh,revised_fields=parse_9_fields(scene["raw_9_fields"])
        assert rh==oh
        assert len(revised_fields)==9
        for key in ("FORMAT & STYLE","CHARACTERS","END STATE","AUDIO"):
            assert revised_fields[key]==orig_fields[key],(n,key)
        assert "3D CGI" in revised_fields["FORMAT & STYLE"],n
        assert "9:16" in revised_fields["FORMAT & STYLE"],n
        assert revised_fields["TIMED ACTION"] != orig_fields["TIMED ACTION"],n
        assert len(scene["raw_9_fields"]) < len(original),n
        reloaded=copy.deepcopy(plan["scenes"][n-1]);reloaded["raw_9_fields"]=original
        assert load_armed_repair(d,reloaded)
        assert reloaded["raw_9_fields"]==scene["raw_9_fields"]
        # No mutation of cast/dialogue/source scene structure or existing files
        assert scene["dialogue_beats"]==plan["scenes"][n-1]["dialogue_beats"]
        assert (d/OLD_RECEIPT_NAME).read_text().find("QA-FAILED")>0
        tested+=1
        print(f"SCENE_{n}_ONE_REPAIR_ARMED_PASS original={len(original)} repaired={len(scene['raw_9_fields'])}",flush=True)
# Test import is only in distinct multi-role cinema rendering branch.
orchestrator=(ROOT/"cinematic_engine"/"drama_orchestrator.py").read_text(encoding="utf-8")
assert 'from .drama_auto_repair import arm_one_repair' in orchestrator
assert 'from .drama_auto_repair import load_armed_repair' in orchestrator
assert 'if image_provider == "muse_video":' in orchestrator
assert 'from series_studio import run as run_legacy' in (ROOT/"pipeline_router.py").read_text(encoding="utf-8")
for path in [ROOT/"cinematic_engine"/"drama_auto_repair.py",ROOT/"cinematic_engine"/"drama_orchestrator.py"]:
    py_compile.compile(str(path),doraise=True)
print("MULTI_ROLE_ONLY_ROUTE_PASS")
print("NO_DUPLICATE_PENDING_NO_POLICY_BYPASS_PASS")
print("OFFLINE_REPAIR_TESTS",tested,"/",2,"PASS")
