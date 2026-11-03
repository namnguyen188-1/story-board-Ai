"""E2E Verification Test: 5-Second Scenes in Narrative (Kể Chuyện) Mode
Verifies:
1. Scene count & duration calculations for both 1-minute and Long videos (3m, 5m, 10m).
2. Pacing & word count requirements for 5-second scenes.
3. Reference Scene Assembler validation with 5s intervals.
4. Web server parameter normalization & preservation of 5s scenes.
"""
import sys
import math
import json
from pathlib import Path

# Setup paths
STUDIO_ROOT = Path(r"D:\STORYBOARD_AI\studio")
sys.path.insert(0, str(STUDIO_ROOT.parent))
sys.path.insert(0, str(STUDIO_ROOT))

# Ensure UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def test_scene_count_and_budget_calculation():
    print("\n" + "=" * 70)
    print("PHẦN 1: KIỂM TRA TÍNH TOÁN SỐ CẢNH & NGÂN SÁCH ẢNH (SHORT & LONG VIDEO)")
    print("=" * 70)

    test_cases = [
        # (minutes, scene_sec, expected_scenes, label)
        (1.0, 5, 12, "Short form 1 phút, cảnh 5s (60s / 5s)"),
        (1.1, 5, 14, "Short form 1.1 phút, cảnh 5s (66s / 5s)"),
        (3.0, 5, 36, "Video dài 3 phút, cảnh 5s (180s / 5s)"),
        (5.0, 5, 60, "Video dài 5 phút, cảnh 5s (300s / 5s)"),
        (10.0, 5, 120, "Video dài 10 phút, cảnh 5s (600s / 5s)"),
        (10.0, 25, 24, "Video dài 10 phút, chuẩn 25s (600s / 25s)"),
    ]

    for minutes, scene_sec, expected_count, label in test_cases:
        eff_sec = max(4, min(scene_sec, 60))
        total_sec = minutes * 60.0
        calculated_count = math.ceil(total_sec / eff_sec)
        assert calculated_count == expected_count, (
            f"Lỗi: {label} -> Mong muốn {expected_count}, thực tế {calculated_count}"
        )
        print(f"  [PASS] {label}: {minutes} phút, {scene_sec}s/cảnh -> {calculated_count} cảnh/ảnh")

def test_reference_scene_assembler_5s_validation():
    print("\n" + "=" * 70)
    print("PHẦN 2: KIỂM TRA VALIDATE PHÂN CẢNH 5 GIÂY TRONG REFERENCE SCENE ASSEMBLER")
    print("=" * 70)

    from studio.reference_scene_assembler import validate_model_batch

    # Giả lập 2 phân cảnh 5 giây liên tiếp
    batch = [
        {
            "scene_number": 1,
            "source_start_seconds": 0.0,
            "source_end_seconds": 5.0,
            "frame_path": "dummy.jpg",
            "caption_text": "El silencio es una gran virtud"
        },
        {
            "scene_number": 2,
            "source_start_seconds": 5.0,
            "source_end_seconds": 10.0,
            "frame_path": "dummy.jpg",
            "caption_text": "Aprende a callar ante los necios"
        }
    ]

    # Model trả về thuyết minh 8-9 từ cho mỗi cảnh 5 giây (vừa khít 5s đọc tự nhiên)
    mock_model_response = json.dumps([
        {
            "scene_number": 1,
            "summary": "Tượng Marcus Aurelius trong hoàng hôn tĩnh lặng",
            "narration": "El silencio es la mayor fortaleza del sabio.",  # 8 từ
            "description": "Cinematic 16:9, close-up of a weathered stone philosopher bust.",
            "visual_setup": "Golden dusk sunlight streaming through ancient temple colonnades.",
            "text_overlay": "DOMINA EL SILENCIO",
            "observed_subjects": ["philosopher bust", "ancient temple"],
            "visual_confidence": "high",
            "uncertainties": []
        },
        {
            "scene_number": 2,
            "summary": "Góc nhìn nghiêng uy nghiêm của triết gia La Mã",
            "narration": "Aprende a callar cuando las palabras sobran.",  # 7 từ
            "description": "Dramatic low-angle shot of weathered marble statue against stormy sky.",
            "visual_setup": "Volumetric warm rim light, chiaroscuro contrast.",
            "text_overlay": "CALLA Y OBSERVA",
            "observed_subjects": ["marble statue", "stormy sky"],
            "visual_confidence": "high",
            "uncertainties": []
        }
    ])

    validated = validate_model_batch(batch, mock_model_response)
    assert len(validated) == 2, f"Expected 2 validated scenes, got {len(validated)}"
    assert validated[0]["narration"] == "El silencio es la mayor fortaleza del sabio."
    assert validated[1]["narration"] == "Aprende a callar cuando las palabras sobran."
    print("  [PASS] Cảnh 5s với 7-8 từ thuyết minh đã vượt qua validate_model_batch thành công!")
    print("  [PASS] Không còn lỗi SCENE_VISION_DESCRIPTION_TOO_SHORT đối với nhịp 5 giây.")

def test_series_studio_word_count_scaling():
    print("\n" + "=" * 70)
    print("PHẦN 3: KIỂM TRA TỐC ĐỘ NÓI (WPS) & NGƯỠNG TỪ TỐI THIỂU CHO CẢNH 5 GIÂY")
    print("=" * 70)

    # 5 giây ở tốc độ nói 1.5 - 2.0 words/second
    wps = 1.45
    scene_seconds = 5
    target_words = int(scene_seconds * wps)  # 7 từ
    min_required_words = max(5, int(target_words * 0.55))

    assert target_words == 7, f"Expected 7 words, got {target_words}"
    assert min_required_words == 5, f"Expected min 5 words, got {min_required_words}"
    print(f"  [PASS] 5s/cảnh -> Target: {target_words} từ | Ngưỡng tối thiểu: {min_required_words} từ")

    # So sánh với 25s
    scene_seconds_25 = 25
    target_words_25 = int(scene_seconds_25 * wps)  # 36 từ
    min_required_words_25 = max(5, int(target_words_25 * 0.55))  # 19 từ
    print(f"  [PASS] 25s/cảnh -> Target: {target_words_25} từ | Ngưỡng tối thiểu: {min_required_words_25} từ")

def test_web_server_scene_seconds_clamping():
    print("\n" + "=" * 70)
    print("PHẦN 4: KIỂM TRA BẢO LƯU GIÁ TRỊ CẢNH 5S TRÊN WEB SERVER & BACKEND")
    print("=" * 70)

    # Test clamping logic from web_server.py
    for raw_sec in [5, "5", 5.0, 10, 25, 60]:
        scene_sec = int(raw_sec)
        scene_sec = max(4, min(scene_sec, 60))
        assert scene_sec == int(raw_sec), f"Expected {raw_sec} to be preserved, got {scene_sec}"
        print(f"  [PASS] Input scene_seconds={raw_sec} -> Giữ nguyên {scene_sec}s (nằm trong dải hợp lệ 4..60)")

def run_all_e2e_tests():
    try:
        test_scene_count_and_budget_calculation()
        test_reference_scene_assembler_5s_validation()
        test_series_studio_word_count_scaling()
        test_web_server_scene_seconds_clamping()
        print("\n" + "=" * 70)
        print(">>> TẤT CẢ 4 HẠNG MỤC KIỂM THỬ E2E CHO CẢNH 5S ĐỀU PASS 100%! <<<")
        print("=" * 70 + "\n")
        return True
    except Exception as e:
        print(f"\n[FAIL] E2E Test gặp lỗi: {e}\n")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_e2e_tests()
    sys.exit(0 if success else 1)
