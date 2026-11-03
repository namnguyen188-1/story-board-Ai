# -*- coding: utf-8 -*-
"""Regression: 3-second placeholders must not get PASS; no internet/API calls."""
import sys,tempfile,json,py_compile
from pathlib import Path
ROOT=Path(r"D:\STORYBOARD_AI\studio")
sys.path.insert(0,str(ROOT))
from cinematic_engine.drama_orchestrator import export_legacy_compatibility_bridge
import youtube_manager
with tempfile.TemporaryDirectory(prefix="audit_failclosed_") as tmp:
 ep=Path(tmp)/"episode_001";sc=ep/"scenes"/"scene_0001";sc.mkdir(parents=True)
 (sc/"scene_final.mp4").write_bytes(b"FAKE" * 3000)
 raw={"series_name":"QA_FailClosed","episode_num":1,"language":"Vietnamese","genre":"animation",
      "scenes":[{"scene_number":1,"summary":"A cinematic scene","dialogue_beats":[],"setting":"workshop","visual_setup":"test"}],"cast":{}}
 export_legacy_compatibility_bridge(ep,raw,[],None,image_provider="muse_video")
 result=json.loads((sc/"result.json").read_text(encoding="utf-8"))
 assert result["status"]=="FAILED",result
 print("FAKE_3S_CLIP_REJECTED_PASS",result["status"])
real=ROOT/"productions"/"ho-t-h-nh-3d"/"episode_001"
qc=json.loads((real/"episode_qc.json").read_text(encoding="utf-8"))
assert qc["status"]=="FAILED_INCOMPLETE" and qc["missing_scenes"]==[63,67] and not qc["publish_allowed"]
assert not (real/"episode_final.mp4").exists()
assert not (real/"episode_001_final.mp4").exists()
print("BAD_MASTER_QUARANTINED_AND_PUBLISH_BLOCKED_PASS")
for f in ["cinematic_engine/drama_orchestrator.py","muse_video_provider.py",
          "muse_gateway_worker.py","web_server.py","seo_quality.py","seo_packager.py"]:
 py_compile.compile(str(ROOT/f),doraise=True)
print("CHANGED_MODULES_COMPILE_PASS")
