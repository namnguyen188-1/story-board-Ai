import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

root = Path(r"D:\STORYBOARD_AI\studio")
sys.path.insert(0, str(root))

import series_studio as studio
from story_skill_bridge import resolve_skill_name, installed_skill, skill_prompt, export_idea_scenes

def test_skill_resolution():
    # 1. Stoic
    assert resolve_skill_name("stoic") == "write-video-scene-prompts"
    # 2. Shorts
    assert resolve_skill_name("documentary", is_short=True) == "write-viral-shorts-prompts"
    assert resolve_skill_name("facts_shorts") == "write-viral-shorts-prompts"
    assert resolve_skill_name("history", aspect_ratio="9:16") == "write-viral-shorts-prompts"
    # 3. Drama
    assert resolve_skill_name("family_drama") == "write-video-scene-prompts"
    assert resolve_skill_name("drama") == "write-video-scene-prompts"
    assert resolve_skill_name("mystery", production_mode="cinematic_drama") == "write-video-scene-prompts"
    # 4. Narrative / Documentary / History
    assert resolve_skill_name("documentary") == "write-narrative-scene-prompts"
    assert resolve_skill_name("history") == "write-narrative-scene-prompts"
    assert resolve_skill_name("kechuyen") == "write-narrative-scene-prompts"
    print("SKILL_RESOLUTION_TEST_PASS")

def test_skill_prompts():
    doc_prompt = skill_prompt("documentary", production_mode="narrative", aspect_ratio="16:9")
    assert "INSTALLED SKILL: write-narrative-scene-prompts" in doc_prompt
    assert "1-VOICE STORYTELLING & PURE IMAGE PROMPTS" in doc_prompt
    assert "PURE VISUAL PROMPT in English (40-80 words)" in doc_prompt

    shorts_prompt = skill_prompt("facts_shorts", aspect_ratio="9:16", is_short=True)
    assert "INSTALLED SKILL: write-viral-shorts-prompts" in shorts_prompt
    assert "AUTHORITATIVE SHORTS WRITING RULES" in shorts_prompt
    assert "Act 1 Super Hook" in shorts_prompt

    drama_prompt = skill_prompt("family_drama", production_mode="cinematic_drama")
    assert "INSTALLED SKILL: write-video-scene-prompts" in drama_prompt
    assert "REAL ACTING" in drama_prompt

    stoic_prompt = skill_prompt("stoic")
    assert "INSTALLED SKILL: write-video-scene-prompts" in stoic_prompt
    print("SKILL_PROMPTS_TEST_PASS")

def test_export_idea_scenes():
    scenes = [
        {
            "scene_number": 1,
            "summary": "Ming treasure fleet sets sail",
            "narration": "Hạm đội bảo thuyền của Trịnh Hòa xuất kích vượt đại dương.",
            "description": "Massive ancient Chinese timber treasure ships with red silk sails sailing across vast azure ocean, golden dawn sunlight, photorealistic 8k.",
            "visual_setup": "Chinese port harbour with hundreds of magnificent wooden ships.",
            "text_overlay": "HẠM ĐỘI BẢO THUYỀN",
            "camera": "Wide establishing drone shot"
        },
        {
            "scene_number": 2,
            "summary": "Admiral Zheng He consults magnetic compass",
            "narration": "Chiếc la bàn từ tính đầu tiên dẫn đường cho hàng vạn thủy thủ.",
            "description": "Close-up of weathered hands of Admiral Zheng He holding an ornate bronze magnetic compass, warm candle glow inside wooden cabin, detailed 8k.",
            "visual_setup": "Ship cabin navigation table with parchment sea charts.",
            "text_overlay": "BÍ MẬT HÀNG HẢI",
            "camera": "Intimate slow pan"
        }
    ]
    bible = {"world": "Ming Dynasty Maritime Era", "visual_style": "Historical epic documentary"}

    # Test Narrative Export
    text_narrative, report_narrative = export_idea_scenes(
        scenes, bible, 25, 1280, 720, genre="history", production_mode="narrative", title="Hạm Đội Bảo Thuyền"
    )
    assert report_narrative["pass"]
    assert report_narrative["skill_name"] == "write-narrative-scene-prompts"
    assert "### SCENE 001" in text_narrative
    assert "IMAGE PROMPT" in text_narrative
    assert "THUYẾT MINH / VOICEOVER" in text_narrative
    assert "CAMERA MOTION" in text_narrative

    # Test Shorts Export
    text_shorts, report_shorts = export_idea_scenes(
        scenes, bible, 8, 720, 1280, genre="history", title="Hạm Đội Bí Ẩn"
    )
    assert report_shorts["pass"]
    assert report_shorts["skill_name"] == "write-viral-shorts-prompts"
    assert "### SCENE 001" in text_shorts
    assert "[ACT 1: SIÊU HOOK]" in text_shorts
    assert "[ACT 3: CAO TRÀO & INFINITE LOOP]" in text_shorts

    print("EXPORT_IDEA_SCENES_TEST_PASS")

if __name__ == "__main__":
    test_skill_resolution()
    test_skill_prompts()
    test_export_idea_scenes()
    print("ALL_GENRE_SKILL_ROUTING_TESTS_PASS!")
