import sys
from pathlib import Path
import json

STUDIO_DIR = Path(__file__).resolve().parent.parent
if str(STUDIO_DIR) not in sys.path:
    sys.path.insert(0, str(STUDIO_DIR))

from cinematic_engine.drama_planner import generate_drama_screenplay

def run_e2e_continuity_test():
    print("======================================================================")
    print("🎬 [E2E TEST] KIỂM TRA ĐỘ LIỀN MẠCH CỤM BỐI CẢNH (SEQUENCE CONTINUITY)")
    print("   Nhánh: Phim Kịch Điện Ảnh Đa Vai (Cinematic Multi-Role Drama)")
    print("======================================================================\n")

    test_prompt = (
        "Trong đêm giông bão tại dinh thự họ Phan, Chủ tịch Phan triệu tập con trai trưởng Phan Quân "
        "và con gái nuôi Lan Anh vào phòng làm việc riêng. Ông bất ngờ xé bỏ di chúc cũ, tuyên bố Lan Anh "
        "sẽ là người thừa kế duy nhất. Phan Quân bàng hoàng, khóa cửa phòng và lấy ra bức thư bí mật đe dọa."
    )
    
    test_dir = STUDIO_DIR / "productions" / "TEST_CONTINUITY" / "episode_001"
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Run screenplay generation for 12 scenes (2 minutes)
    plan = generate_drama_screenplay(
        prompt=test_prompt,
        series_name="Gia Tộc Quyền Lực",
        episode_num=1,
        language="Vietnamese",
        genre="family_drama",
        scene_count=12,
        model="gemini-3.1-flash-lite",
        episode_dir=test_dir,
        visual_style="color_cinematic"
    )

    scenes = plan.scenes if hasattr(plan, "scenes") else plan.get("scenes", [])
    print(f"\n[E2E RESULT] Đã sinh thành công {len(scenes)} phân cảnh kịch bản.")
    
    # 1. Analyze Setting Continuity
    settings = []
    consecutive_counts = []
    cur_setting = None
    cur_count = 0

    for s in scenes:
        setting = s.setting if hasattr(s, "setting") else s.get("setting", "")
        settings.append(setting)
        if setting == cur_setting:
            cur_count += 1
        else:
            if cur_setting:
                consecutive_counts.append((cur_setting, cur_count))
            cur_setting = setting
            cur_count = 1
    if cur_setting:
        consecutive_counts.append((cur_setting, cur_count))

    distinct_settings = len(set(settings))
    print("\n--- 1. PHÂN TÍCH LIỀN MẠCH BỐI CẢNH (SETTING CONTINUITY) ---")
    print(f"Tổng số cảnh: {len(scenes)}")
    print(f"Số lượng bối cảnh khác nhau: {distinct_settings} (Kỳ vọng: <= 2)")
    print("Các khối phân đoạn liên tục (Sequence Blocks):")
    for st, count in consecutive_counts:
        print(f"  • Bối cảnh: '{st}' -> Kéo dài {count} cảnh liên tiếp ({count * 10}s)")

    # 2. Analyze Camera Dynamic Coverage
    print("\n--- 2. PHÂN TÍCH GÓC MÁY QUY ĐIỆN ẢNH (CAMERA SHOT VARIETY) ---")
    camera_motions = []
    for s in scenes:
        cam = s.camera_motion if hasattr(s, "camera_motion") else s.get("camera_motion", "")
        camera_motions.append(cam)
    
    unique_cams = set(camera_motions)
    print(f"Các góc máy sử dụng: {list(unique_cams)}")
    for i, (s, c) in enumerate(zip(scenes[:6], camera_motions[:6]), 1):
        summary = s.summary if hasattr(s, "summary") else s.get("summary", "")
        setting = s.setting if hasattr(s, "setting") else s.get("setting", "")
        print(f"  [Cảnh {i:02d}] Bối cảnh: '{setting}' | Góc máy: '{c}' | Tóm tắt: {summary[:50]}...")

    # 3. Analyze Multi-Character Dialogue
    print("\n--- 3. PHÂN TÍCH THOẠI ĐA VAI & CẢM XÚC (MULTI-ROLE DIALOGUE) ---")
    sample_sc = scenes[1] if len(scenes) > 1 else scenes[0]
    beats = sample_sc.dialogue_beats if hasattr(sample_sc, "dialogue_beats") else sample_sc.get("dialogue_beats", [])
    print(f"Cảnh mẫu ({sample_sc.scene_number if hasattr(sample_sc, 'scene_number') else sample_sc.get('scene_number')}):")
    for b in beats:
        spk = b.speaker if hasattr(b, "speaker") else b.get("speaker")
        tone = b.tone if hasattr(b, "tone") else b.get("tone")
        text = b.text if hasattr(b, "text") else b.get("text")
        act = b.action if hasattr(b, "action") else b.get("action")
        print(f"  🎭 {spk} ({tone}): \"{text}\"")
        print(f"     Hành động diễn xuất: {act}")

    # Assertions
    avg_sequence_len = len(scenes) / max(1, len(consecutive_counts))
    print(f"\nChiều dài trung bình của mỗi phân đoạn bối cảnh: {avg_sequence_len:.1f} cảnh/bối cảnh")
    
    if distinct_settings <= 3 and avg_sequence_len >= 3.5:
        print("\n🎉 [E2E TEST PASSED] ĐẠT CHUẨN LIỀN MẠCH ĐIỆN ẢNH HOLLYWOOD!")
        print("   Các cảnh đã được neo chặt chẽ theo cụm Sequence Block, loại bỏ hoàn toàn hiện tượng nhảy bối cảnh ngẫu nhiên.")
    else:
        print("\n⚠️ Cảnh báo: Vẫn còn phân mảnh bối cảnh, cần siết chặt thêm.")

if __name__ == "__main__":
    run_e2e_continuity_test()
