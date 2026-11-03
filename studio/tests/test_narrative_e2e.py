import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

root = Path(r"D:\STORYBOARD_AI\studio")
sys.path.insert(0, str(root))
import series_studio as studio
from story_skill_bridge import installed_skill

seen_requests = []
class FakeResponse:
    def __init__(self, value):
        self.text = json.dumps(value, ensure_ascii=False)

class FakeModels:
    def generate_content(self, **kw):
        prompt = str(kw.get("contents") or "")
        seen_requests.append(prompt)
        if "Design an ORIGINAL" in prompt:
            return FakeResponse({
                "world": "15th-century Ming Dynasty Maritime Empire",
                "visual_style": "Epic historical documentary with rich photorealistic maritime visuals",
                "characters": [{"name": "Admiral Zheng He", "stable_appearance": "Imposing mature Chinese admiral in Ming Dynasty naval robes",
                                "attire": "Embroidered silk robes, official hat", "immutable_rules": "same historical look"}],
                "continuity_rules": "Maintain historical authenticity of the ships and navigation instruments",
                "narrator_style": "authoritative, inspiring",
                "core_moral_theme": "Human exploration and oceanic mastery",
                "series_hook_framework": "Each episode unveils a forgotten nautical breakthrough"
            })
        assert "INSTALLED SKILL: write-narrative-scene-prompts" in prompt, "narrative skill not sent"
        assert "HYPER-MUSCULAR CHISELED ROMAN PHILOSOPHER EMPEROR" not in prompt, "Stoic hero prompt leaked into history genre"
        scenes = [
            {
                "scene_number": 1,
                "summary": "The fleet departs Nanjing harbour",
                "narration": "Vào thế kỷ 15, một hạm đội bảo thuyền vĩ đại chưa từng có trong lịch sử đã giương buồm ra khơi.",
                "description": "Massive 15th-century Chinese timber treasure ships with red ribbed sails departing ancient port of Nanjing at dawn, volumetric golden sunlight, photorealistic 8k.",
                "visual_setup": "Nanjing ancient harbor docks crowded with majestic wooden vessels.",
                "text_overlay": "HẠM ĐỘI BẢO THUYỀN"
            },
            {
                "scene_number": 2,
                "summary": "Navigating unknown storm seas",
                "narration": "Vượt qua những cơn bão kinh hoàng trên biển Nam Hải bằng những hải đồ thiên văn bí truyền.",
                "description": "Tremendous wooden treasure ship cutting through towering ocean waves under dramatic stormy twilight sky, bioluminescent sea spray, epic cinematic lighting, 8k.",
                "visual_setup": "Open stormy sea with massive waves crashing against timber hull.",
                "text_overlay": "BÃO BIỂN NAM HẢI"
            }
        ]
        return FakeResponse({"scenes": scenes})

class FakeClient:
    def __init__(self, *a, **kw):
        self.models = FakeModels()

def args(episode):
    return SimpleNamespace(
        series="MingFleetHistory", episode=episode,
        minutes=24/60, scene_seconds=12, language="Vietnamese",
        model="mock-offline", mode="live", input_mode="idea",
        genre="history", visual_style="color_cinematic", region="VN",
        reference_url="", link_clone_mode="exact_clone", speech_pacing="normal",
        image_provider="mcp_v2", size="1280x720", resume=False
    )

with tempfile.TemporaryDirectory(prefix="narrative_e2e_", dir=str(root / "scratch")) as sandbox:
    home = Path(sandbox)
    series = home / "MingFleetHistory"
    series.mkdir()
    with patch.object(studio, "own_api_key", return_value="E2E_FAKE_KEY"), \
         patch.object(studio, "get_api_keys", return_value=["E2E_FAKE_KEY"]), \
         patch.object(studio, "ResilientClient", FakeClient):
        directory = series / "episode_001"
        directory.mkdir()
        prompt = "Hạm đội bảo thuyền thời nhà Minh của Trịnh Hòa và hành trình thám hiểm vĩ đại"
        plan = studio.produce_plan(args(1), series, directory, prompt)
        scene_file = directory / "skill_scenes.txt"
        qc_path = directory / "skill_qc.json"
        assert scene_file.exists() and qc_path.exists()
        qc = json.loads(qc_path.read_text(encoding="utf-8"))
        assert qc["pass"] and qc["scene_count"] == 2 and qc["total_seconds"] == 24
        assert qc["skill_name"] == "write-narrative-scene-prompts"
        assert plan["skill_pipeline"]["name"] == "write-narrative-scene-prompts"
        assert "### SCENE 001" in scene_file.read_text(encoding="utf-8")
        assert "IMAGE PROMPT" in scene_file.read_text(encoding="utf-8")
        assert "THUYẾT MINH / VOICEOVER" in scene_file.read_text(encoding="utf-8")
        assert "FORMAT & STYLE:" not in scene_file.read_text(encoding="utf-8"), "9-field bloat leaked into narrative"
        print("EPISODE_1_NARRATIVE_SKILL_QC_PASS", qc["scene_count"], "scenes")
    print("NARRATIVE_HISTORY_PROMPT_ISOLATION_PASS")
    print("NARRATIVE_SCENE_CONTRACT_PASS")
    print("E2E_NARRATIVE_PLANNER_PASS")
