"""Deterministic E2E: production planner with fake LLM -> real skill -> 9-field QC -> continuity.
Runs only inside scratch, never calls Gemini, Muse, Flow, TTS or YouTube.
"""
import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

root = Path(r"D:\STORYBOARD_SKILL_AUDIT_20261105\studio")
sys.path.insert(0,str(root))
import series_studio as studio
from story_skill_bridge import installed_skill

seen_requests = []
class FakeResponse:
    def __init__(self,value): self.text=json.dumps(value,ensure_ascii=False)
class FakeModels:
    def generate_content(self,**kw):
        prompt=str(kw.get("contents") or "")
        seen_requests.append(prompt)
        if "Design an ORIGINAL" in prompt:
            return FakeResponse({
                "world":"A consistent quiet Roman study",
                "visual_style":"Warm natural daylight, cinematic authenticity",
                "characters":[{"name":"Teacher","stable_appearance":"Middle-aged person with dark hair",
                               "attire":"Plain brown linen tunic", "immutable_rules":"same look every scene"}],
                "continuity_rules":"Keep same character and visual mood",
                "narrator_style":"calm",
                "core_moral_theme":"Mastering one's response to criticism",
                "series_hook_framework":"Each chapter adds one practice"})
        assert "INSTALLED SKILL: write-video-scene-prompts" in prompt, "skill was not sent to LLM"
        assert "REAL ACTING" in prompt, "acting rules absent"
        if "episode 2 of ONE ongoing series" in prompt:
            title="Continue the practice of remaining calm when criticized"
        else:
            title="Understand the first reaction to a harsh comment"
        scenes=[]
        for i in (1,2):
            scenes.append({
                "scene_number":i,
                "summary":f"{title}: chapter beat {i}",
                "narration":"You can choose how to respond. Do not surrender your judgment to strangers. Breathe once, consider what is truly yours to control, and act with patience.",
                "description":"In a quiet Roman study, the teacher moves from the table toward a window, then pauses to consider their response.",
                "visual_setup":"Roman study with a wooden table, a book, sunlight through the window.",
                "text_overlay":"INNER STRENGTH"
            })
        return FakeResponse({"scenes":scenes})
class FakeClient:
    def __init__(self,*a,**kw): self.models=FakeModels()

def args(episode):
    return SimpleNamespace(series="StoicSkillE2E",episode=episode,
         minutes=16/60,scene_seconds=8,language="English",
         model="mock-offline",mode="live",input_mode="idea",
         genre="stoic",visual_style="color_cinematic",region="US",
         reference_url="",link_clone_mode="exact_clone",speech_pacing="slow",
         image_provider="mcp_v2",size="640x360",resume=False)

with tempfile.TemporaryDirectory(prefix="story_skill_e2e_",dir=str(root/"scratch")) as sandbox:
    home=Path(sandbox);series=home/"StoicSkillE2E";series.mkdir()
    with patch.object(studio,"own_api_key",return_value="E2E_FAKE_KEY"), \
         patch.object(studio,"get_api_keys",return_value=["E2E_FAKE_KEY"]), \
         patch.object(studio,"ResilientClient",FakeClient):
        plans=[]
        for ep in (1,2):
            directory=series/f"episode_{ep:03d}"
            directory.mkdir()
            prompt=("How should people respond to criticism?" if ep==1
                    else "Continue the Stoic lesson from episode 1, expanding on one's reaction")
            plan=studio.produce_plan(args(ep),series,directory,prompt)
            plans.append(plan)
            scene_file=directory/"skill_scenes.txt"
            qc_path=directory/"skill_qc.json"
            assert scene_file.exists() and qc_path.exists()
            qc=json.loads(qc_path.read_text(encoding="utf-8"))
            assert qc["pass"] and qc["scene_count"]==2 and qc["total_seconds"]==16
            assert plan["skill_pipeline"]["sha256"]==installed_skill()["sha256"]
            assert "FORMAT & STYLE:" in scene_file.read_text(encoding="utf-8")
            assert "AUDIO:" in scene_file.read_text(encoding="utf-8")
            saved=studio.read_json(directory/"plan.json")
            assert len(saved["scenes"])==2
            print(f"EPISODE_{ep}_SKILL_QC_PASS",qc["scene_count"],"scenes",flush=True)
    assert any("LOCKED ORIGINAL SERIES PREMISE" in q and "episode 2 of ONE ongoing series" in q for q in seen_requests)
    assert all("life-or-death climax" not in q for q in seen_requests if "Write EXACTLY" in q)
    print("SERIES_CONTINUITY_PROMPT_PASS")
    print("STOIC_SAFETY_WRITER_PASS")
    print("SKILL_LOADED_FROM_DISK_PASS")
    print("E2E_SCRIPT_PLANNER_2_EPISODES_PASS")
