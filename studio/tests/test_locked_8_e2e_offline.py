import sys,json
from pathlib import Path
root=Path(r"D:\STORYBOARD_AI\studio")
sys.path.insert(0,str(root))
from series_studio import parser,run
prior=root/"productions"/"Whiteboard-Chronicles"/"episode_003"/"plan.json"
script=json.loads(prior.read_text(encoding="utf-8"))["config"]["prompt"]
args=parser().parse_args([
 "run","--mode","offline","--input-mode","script",
 "--series","Locked Screenplay Eight Scenes E2E QA","--episode","1",
 "--minutes","0.4","--scene-seconds","5","--size","640x360",
 "--workers","2","--genre","family_drama","--visual-style","color_cinematic",
 "--region","VN","--language","Vietnamese","--voice-name","auto",
 "--image-provider","mcp_v2","--mcp-max-images","8",
 "--prompt","placeholder"
])
args.prompt=script
run(args)
folder=root/"productions"/"Locked-Screenplay-Eight-Scenes-E2E-QA"/"episode_001"
plan=json.loads((folder/"plan.json").read_text(encoding="utf-8"))
manifest=json.loads((folder/"manifest.json").read_text(encoding="utf-8"))
assert plan["scene_count"]==8,len(plan["scenes"])
assert len(manifest["completed"])==8,manifest
assert manifest["status"] in ("PASS","DURATION_REVIEW"),manifest["status"]
assert (folder/"episode_final.mp4").is_file()
assert "vi phạm" in plan["scenes"][0]["narration"]
assert not plan["scenes"][5]["narration"]
print("FULL_EIGHT_SCENE_LOCKED_SCREENPLAY_OFFLINE_E2E_PASS",manifest["status"])
