import os
import sys
from pathlib import Path
from unittest.mock import patch

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from studio.seo_packager import (
    format_upload_settings_checklist_txt,
    generate_thumbnail_with_flow
)
from studio.thumbnail_studio import render_viral_3d_text_overlay

def test_checklist_spanish_language():
    pack = {"language": "Spanish", "series": "stoi-1", "episode": 1}
    guide = format_upload_settings_checklist_txt(pack)
    assert "Tiếng Tây Ban Nha (Spanish)" in guide, f"Missing Spanish name: {guide}"
    assert "Mã chuẩn YouTube: es" in guide, f"Missing BCP-47 es: {guide}"
    assert "chưa từng phát sóng trên truyền hình tại Hoa Kỳ" in guide, f"Missing FCC caption text: {guide}"
    print("CHECKLIST_SPANISH_TEST_PASS")

def test_checklist_vietnamese_language():
    pack = {"language": "vi", "series": "triet-hoc", "episode": 1}
    guide = format_upload_settings_checklist_txt(pack)
    assert "Tiếng Việt (Vietnamese)" in guide, f"Missing Vietnamese name: {guide}"
    assert "Mã chuẩn YouTube: vi" in guide, f"Missing BCP-47 vi: {guide}"
    print("CHECKLIST_VIETNAMESE_TEST_PASS")

def test_thumbnail_vibrant_gold_color_prompts(tmp_path):
    test_ep = tmp_path / "ep_test"
    test_ep.mkdir(parents=True, exist_ok=True)
    
    import studio.seo_packager as sp
    called_prompts = []
    
    def mock_generate_image(prompt, aspect_ratio="9:16", **kwargs):
        called_prompts.append(prompt)
        # Create a blank jpg to satisfy existence check
        out_f = test_ep / "thumbnail_flow_base.jpg"
        from PIL import Image
        im = Image.new("RGB", (1080, 1920), (20, 20, 20))
        im.save(out_f)
        return out_f
        
    with patch("studio.flowkit_client.is_flowkit_alive", return_value=True), \
         patch("studio.flowkit_client.ensure_flowkit_running", return_value=True), \
         patch("studio.flowkit_client.generate_image", side_effect=mock_generate_image):
        
        # Test 1-word hook: "ESTOICISMO"
        sp.generate_thumbnail_with_flow(
            episode_dir=test_ep,
            series_name="stoi",
            genre="stoic",
            aspect_ratio="9:16",
            hook_text="ESTOICISMO"
        )
        assert len(called_prompts) > 0, "FlowKit was not called"
        p = called_prompts[0]
        assert "radiant 3D burnished imperial gold" in p, f"Missing radiant gold: {p}"
        assert "pure white cracked marble" not in p, f"Dull silver marble found: {p}"
        print("THUMBNAIL_SINGLE_WORD_GOLD_PROMPT_PASS")

        # Test 2-word hook: "DOMINA TU MENTE"
        called_prompts.clear()
        sp.generate_thumbnail_with_flow(
            episode_dir=test_ep,
            series_name="stoi",
            genre="stoic",
            aspect_ratio="9:16",
            hook_text="DOMINA TU MENTE"
        )
        assert len(called_prompts) > 0
        p2 = called_prompts[0]
        assert "radiant 3D burnished imperial gold" in p2, f"Missing radiant gold: {p2}"
        assert "blazing molten amber-gold" in p2, f"Missing molten amber: {p2}"
        assert "pure white cracked marble" not in p2, f"Dull silver marble found: {p2}"
        print("THUMBNAIL_TWO_LINE_GOLD_AMBER_PROMPT_PASS")

def test_thumbnail_studio_palette():
    overlay = render_viral_3d_text_overlay(
        canvas_size=(1080, 1920),
        lines=["ESTOICISMO"],
        text_box=(50, 1100, 1030, 1450),
        font_path="C:/Windows/Fonts/arialbd.ttf"
    )
    assert overlay is not None
    assert overlay.size == (1080, 1920)
    print("THUMBNAIL_STUDIO_PALETTE_PASS")

if __name__ == "__main__":
    import tempfile
    test_checklist_spanish_language()
    test_checklist_vietnamese_language()
    with tempfile.TemporaryDirectory() as td:
        test_thumbnail_vibrant_gold_color_prompts(Path(td))
    test_thumbnail_studio_palette()
    print("ALL_PUBLISH_LANGUAGE_AND_THUMBNAIL_COLOR_TESTS_PASS!")
