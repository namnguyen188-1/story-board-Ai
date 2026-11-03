# -*- coding: utf-8 -*-
"""Offline E2E through menu values -> style prompt -> Muse facade (no API calls)."""
from pathlib import Path
import tempfile, sys, json, re, py_compile
ROOT=Path(r"D:\STORYBOARD_AI\studio")
sys.path.insert(0,str(ROOT))
from studio_modes import STYLES
from cinematic_engine.drama_skill9 import export_episode,writing_rules
from muse_video_provider import format_real_acting_prompt
SOURCE=(ROOT/"web"/"index.html").read_text(encoding="utf-8")
JS=(ROOT/"web"/"app.js").read_text(encoding="utf-8")
DRAMA=(ROOT/"cinematic_engine"/"drama_video_engine.py").read_text(encoding="utf-8")
ROUTER=(ROOT/"pipeline_router.py").read_text(encoding="utf-8")
PLANNER=(ROOT/"cinematic_engine"/"drama_planner.py").read_text(encoding="utf-8")
assert "visual_style: visualStyle" in JS, "UI submit missing visual_style"
assert "visual_style=visual_style" in (ROOT/"cinematic_engine"/"drama_orchestrator.py").read_text(encoding="utf-8")
assert '"raw_9_fields": scene.get("raw_9_fields"' in DRAMA
assert 'from series_studio import run as run_legacy' in ROUTER
assert PLANNER.count("writing_rules(genre, visual_style)") == 3
assert "start_state=str(sc_data.get" in PLANNER
MODES=[
 ("flow_video","3D CGI"),
 ("color_cinematic","live-action"),
 ("color_animation","3D CGI"),
 ("colored_marker","FELT-TIP MARKER"),
 ("hand_color","hand-colored 2D"),
 ("whiteboard","monochrome whiteboard"),
]
scenes=[
 {"scene_number":1,"summary":"A sets a lamp on a wooden table, B listens","setting":"bright workshop",
  "visual_setup":"Two characters in a small workshop, lamp in A's hands", "camera_motion":"slow push",
  "start_state":"A holding lamp, B at right of table, closed door",
  "end_state":"Lamp on tabletop, A left, B right, closed door",
  "characters_present":["A","B"],"dialogue_beats":[{"speaker":"A","voice_id":"Orus","text":"Đặt đèn ở đây nhé.","action":"puts lamp down"}]},
 {"scene_number":2,"summary":"B turns lamp on while A watches","setting":"same bright workshop",
  "visual_setup":"Two characters near the same wooden table","camera_motion":"over the shoulder",
  "start_state":"Lamp on tabletop, A left, B right, closed door",
  "end_state":"Lit lamp on tabletop, A left, B right, closed door",
  "characters_present":["A","B"],"dialogue_beats":[{"speaker":"B","voice_id":"Puck","text":"Đèn sáng rồi!","action":"turns on lamp"}]}
]
cast={"A":{"appearance_lock":"blue shirt, short black hair"},"B":{"appearance_lock":"yellow cap, brown vest"}}
results=[]
for mode,expected in MODES:
 assert f'value="{mode}"' in SOURCE and mode in STYLES, (mode,"menu not wired")
 p={"scenes":json.loads(json.dumps(scenes,ensure_ascii=False)),"cast":cast}
 with tempfile.TemporaryDirectory(prefix="MULTI_ROLE_STYLE_") as td:
  r=export_episode(p,Path(td),genre="animation",visual_style=mode,language="Vietnamese",aspect="16:9",seconds=10)
  assert r["pass"] and r["scene_count"]==2 and r["total_seconds"]==20
  t=(Path(td)/"scene_prompts_9_fields.txt").read_text(encoding="utf-8")
  assert t.count("FORMAT & STYLE:")==2 and expected.lower() in t.lower(),(mode,"wrong visual style")
  assert "A speaks" in t and "B speaks" in t and "voice Orus" in t and "voice Puck" in t
  assert t.count("SETTING & START STATE:")==2
  assert "closed door" in t and "lamp on tabletop" in t.lower()
  assert expected.lower() in writing_rules("animation",mode).lower()
  muse_prompt=format_real_acting_prompt({"raw_9_fields":p["scenes"][0]["raw_9_fields"]},{"production_genre":"animation"})
  assert muse_prompt == p["scenes"][0]["raw_9_fields"],mode
  results.append({"style":mode,"preflight":"PASS","muse_payload":"PASS","scenes":r["scene_count"]})
for name in ["cinematic_engine/drama_schema.py","cinematic_engine/drama_skill9.py","cinematic_engine/drama_planner.py","cinematic_engine/drama_orchestrator.py"]:
 py_compile.compile(str(ROOT/name),doraise=True)
print(json.dumps({"overall":"PASS_OFFLINE_NO_MUSE_CALLS","genre":"animation","modes":results,"legacy_narration":"untouched","compile":"PASS"},ensure_ascii=False,indent=2))
