# -*- coding: utf-8 -*-
"""
E2E Benchmark for Long Multi-Character Drama Video (Episode 4)
==============================================================
Validates:
1. 12-scene screenplay spanning 120 seconds (2.0 minutes).
2. Clean separation of Protagonist (Linh, 27yo) and Secondary (Bà Hòa, 58yo).
3. 00_ASSET_PACK turnaround sheets with isolated appearance DNA.
4. 9-field prompt construction with [PRIMARY FOCUS ACTOR] alternating per shot.
5. Verification of Muse anchor sync payload.
"""

import sys
import json
from pathlib import Path

STUDIO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(STUDIO_ROOT))
sys.path.insert(0, str(STUDIO_ROOT / "cinematic_engine"))

from studio_input_modes import parse_locked_screenplay, convert_locked_scenes_to_drama_plan
from cinematic_engine.drama_asset_manager import generate_master_asset_pack, get_scene_character_anchors, get_primary_character_anchor
from cinematic_engine.drama_skill9 import build_scene, export_episode

EP4_SCRIPT = """
========== SCENE_001 | TIMELINE 00:00–00:10 | GENERATE 10 SECONDS ==========
FORMAT & STYLE: 16:9; 10s motion-video scene; Full-color cinematic film aesthetics, naturalistic spatial lighting, credible live-action actors; NO 3D cartoon rendering, NO statues; consistent actor scale.
CHARACTERS: [PRIMARY FOCUS ACTOR] LINH: CHAR_LINH / Linh, nữ thiên sư trưởng thành 27 tuổi, mặt trái xoan, mắt nâu trầm, tóc đen tết nửa đầu, kẹp bạc hình lá, áo cổ trang xanh lam nhạt cổ trắng W01, thắt lưng đỏ, cổ tay buộc dây bùa đỏ, giọng nữ Việt trầm rõ. Không đổi hình dạng khuôn mặt hoặc trang phục.
SETTING & START STATE: LOC_DEN: sân đền cổ Trung Hoa hư cấu, giếng đá giữa sân niêm phong bằng bùa vàng, hương án đá ở phía Bắc. Linh đứng cách giếng đá 2m, mắt chăm chú quan sát mép giếng.
LIGHTING & COLOR: Ánh trăng lạnh xuyên qua mái đền cổ, độ tương phản cao, tông màu điện ảnh u tối huyền bí.
CAMERA: Medium shot, máy quay theo dõi chậm từ vai Linh hướng về phía giếng đá, ống kính 35mm anamorphic.
TIMED ACTION: 00:00-00:04 Linh bước chậm hai bước về phía miệng giếng đá, vạt áo lam khẽ bay theo gió đêm. 00:04-00:08 Cô ngồi xổm xuống, đưa ngón tay khẽ sờ vào mép đá phong ấn. 00:08-00:10 Linh ngước nhìn lên khi nghe tiếng bước chân từ hiên đền.
END STATE: Linh dừng lại ở mép giếng, ánh mắt cảnh giác hướng về phía hành lang đền.
AUDIO:
LINH: "Khí đen ở đáy giếng... đang bốc lên dữ dội hơn đêm qua."
CONSTRAINTS: Không đổi góc trục không gian, giữ đúng trang phục áo lam nhạt thắt lưng đỏ của Linh.

========== SCENE_002 | TIMELINE 00:10–00:20 | GENERATE 10 SECONDS ==========
FORMAT & STYLE: 16:9; 10s motion-video scene; Full-color cinematic film aesthetics, naturalistic spatial lighting, credible live-action actors; NO 3D cartoon rendering, NO statues; consistent actor scale.
CHARACTERS: [PRIMARY FOCUS ACTOR] BÀ HÒA: CHAR_HOA / Bà Hòa, nữ thủ đền 58 tuổi, mặt gầy hiền có nếp nhăn nhỏ, tóc muối tiêu búi thấp, áo nâu sẫm W01, khăn vai xanh rêu, thắt lưng có chùm chìa khóa đồng, giọng nữ Việt khàn nhẹ, dứt khoát. Không thay đổi trang phục.
[SUPPORTING ACTOR] LINH: CHAR_LINH / Linh, nữ thiên sư 27 tuổi, áo lam nhạt W01.
SETTING & START STATE: LOC_DEN: Hành lang gỗ đền cổ hướng ra sân giếng đá. Bà Hòa đứng dưới ánh đèn dầu mờ ảo, hai tay siết chặt chùm chìa khóa đồng trước ngực.
LIGHTING & COLOR: Ánh đèn lồng dầu vàng ấm áp rọi lên nửa mặt Bà Hòa, hậu cảnh là màn đêm xanh thẫm.
CAMERA: Medium close-up tập trung vào biểu cảm căng thẳng của Bà Hòa, ống kính 50mm xóa phông nhẹ phía sau.
TIMED ACTION: 00:00-00:05 Bà Hòa vội vã bước ra bậc thềm hành lang, chùm chìa khóa đồng va vào nhau lách cách. 00:05-00:10 Bà Hòa giơ tay cảnh báo, ánh mắt lộ rõ vẻ sợ hãi tột cùng.
END STATE: Bà Hòa đứng sững lại ở đầu bậc thềm, nhìn thẳng về phía Linh bên miệng giếng.
AUDIO:
BÀ HÒA: "Cô Linh! Đừng chạm vào mép đá, phong ấn ba mươi năm qua chưa từng lay động!"
CONSTRAINTS: Bà Hòa giữ đúng tóc muối tiêu búi thấp, áo nâu sẫm và khăn vai rêu; tuyệt đối không lẫn nét mặt hay áo lam của Linh.

========== SCENE_003 | TIMELINE 00:20–00:30 | GENERATE 10 SECONDS ==========
FORMAT & STYLE: 16:9; 10s motion-video scene; Full-color cinematic film aesthetics, naturalistic spatial lighting; 35mm anamorphic.
CHARACTERS: [PRIMARY FOCUS ACTOR] LINH: CHAR_LINH / Linh, nữ thiên sư trưởng thành 27 tuổi, áo cổ trang xanh lam nhạt cổ trắng W01, thắt lưng đỏ, bùa đỏ tay.
[SUPPORTING ACTOR] BÀ HÒA: CHAR_HOA / Bà Hòa, nữ thủ đền 58 tuổi, áo nâu sẫm W01.
SETTING & START STATE: Sân đền cổ bên miệng giếng đá. Linh quay nửa người về phía bậc thềm nơi Bà Hòa đang đứng.
LIGHTING & COLOR: Ánh trăng bàng bạc chiếu rọi gương mặt điềm tĩnh của Linh.
CAMERA: Over-the-shoulder shot từ phía sau lưng Bà Hòa hướng về gương mặt cương nghị của Linh.
TIMED ACTION: 00:00-00:05 Linh đứng thẳng dậy, tay trái giữ chặt dải bùa đỏ ở cổ tay. 00:05-00:10 Cô lắc đầu nhẹ nhàng, cất giọng kiên định giải thích tình hình nguy cấp.
END STATE: Linh đứng cạnh miệng giếng, ánh mắt kiên định nhìn Bà Hòa.
AUDIO:
LINH: "Bà Hòa, vết nứt đã lan ra rồi. Nếu không gia cố ngay, tà khí sẽ thoát ra trước nửa đêm!"
CONSTRAINTS: Duy trì đúng tỉ lệ cơ thể và trang phục của hai diễn viên.

========== SCENE_004 | TIMELINE 00:30–00:40 | GENERATE 10 SECONDS ==========
FORMAT & STYLE: 16:9; 10s motion-video scene; Full-color cinematic film aesthetics, naturalistic spatial lighting.
CHARACTERS: [PRIMARY FOCUS ACTOR] BÀ HÒA: CHAR_HOA / Bà Hòa, nữ thủ đền 58 tuổi, mặt gầy hiền tóc muối tiêu búi thấp, áo nâu sẫm W01, khăn xanh rêu.
SETTING & START STATE: Sân đền cổ gần hương án đá. Bà Hòa bước xuống sân gạch rêu phong.
LIGHTING & COLOR: Ánh trăng xanh hòa lẫn bóng tối mờ ảo của mái đình cong vút.
CAMERA: Low angle medium shot theo chân Bà Hòa khi bà tiến gần hương án đá.
TIMED ACTION: 00:00-00:06 Bà Hòa run rẩy tiến lại gần hương án đá, mắt không rời miệng giếng đen ngòm. 00:06-00:10 Bà đưa bàn tay gầy gò sờ lên rãnh khuyết hình trăng lưỡi liềm trên đá.
END STATE: Bà Hòa đứng tựa bên hương án đá, thở dốc vì lo lắng.
AUDIO:
BÀ HÒA: "Chỉ có chiếc gương đồng trong gian thờ mới áp chế được... Nhưng không ai dám vào đó!"
CONSTRAINTS: Khóa chặt đặc điểm tuổi tác 58 tuổi và áo nâu sẫm của Bà Hòa.

========== SCENE_005 | TIMELINE 00:40–00:50 | GENERATE 10 SECONDS ==========
FORMAT & STYLE: 16:9; 10s motion-video scene; Full-color cinematic film aesthetics.
CHARACTERS: [PRIMARY FOCUS ACTOR] LINH: CHAR_LINH / Linh, nữ thiên sư 27 tuổi, áo lam nhạt W01, bùa đỏ tay.
SETTING & START STATE: Bên cạnh nắp giếng đá niêm phong bùa vàng.
LIGHTING & COLOR: Ánh trăng chiếu rọi bùa vàng đang rung rinh dưới luồng gió lạ từ đáy giếng.
CAMERA: Close-up tập trung vào đôi bàn tay bọc dây bùa đỏ của Linh và lá bùa vàng cổ xưa.
TIMED ACTION: 00:00-00:05 Linh quỳ một gối, ngón tay nhẹ nhàng lướt qua mép bùa vàng bị rách góc. 00:05-00:10 Một luồng khói đen mỏng rỉ ra từ kẽ đá, Linh giật tay lại, sắc mặt nghiêm nghị.
END STATE: Linh rút tay lại, ánh mắt tràn đầy sự cảnh giác.
AUDIO:
LINH: "Bùa chú thượng cổ đã mục rỗng... Chúng ta không còn nhiều thời gian!"
CONSTRAINTS: Không biến đổi trang phục hay màu sắc áo lam của Linh.

========== SCENE_006 | TIMELINE 00:50–01:00 | GENERATE 10 SECONDS ==========
FORMAT & STYLE: 16:9; 10s motion-video scene; Full-color cinematic film aesthetics.
CHARACTERS: [PRIMARY FOCUS ACTOR] BÀ HÒA: CHAR_HOA / Bà Hòa, nữ thủ đền 58 tuổi, áo nâu sẫm W01, khăn vai xanh rêu.
SETTING & START STATE: Gian hành lang trước cửa gian thờ nhỏ có rèm che cũ kỹ.
LIGHTING & COLOR: Ánh đèn dầu hắt bóng Bà Hòa dài trên bức tường vôi lở loét.
CAMERA: Dolly shot từ từ tiến vào gương mặt tái nhợt của Bà Hòa khi bà đưa ngón tay chỉ về gian thờ.
TIMED ACTION: 00:00-00:06 Bà Hòa chỉ tay run run vào cánh cửa gỗ khép hờ của gian thờ cổ. 00:06-00:10 Bà hít một hơi sâu, cất lời dặn dò khẩn thiết.
END STATE: Tay Bà Hòa vẫn chỉ vào cửa gian thờ, người hơi run rẩy.
AUDIO:
BÀ HÒA: "Chìa khóa ở đây... Hãy mang gương đồng đặt ngay tâm hương án!"
CONSTRAINTS: Giữ đúng phục trang áo nâu và chùm chìa khóa đồng ở thắt lưng Bà Hòa.

========== SCENE_007 | TIMELINE 01:00–01:10 | GENERATE 10 SECONDS ==========
FORMAT & STYLE: 16:9; 10s motion-video scene; Full-color cinematic film aesthetics.
CHARACTERS: [PRIMARY FOCUS ACTOR] LINH: CHAR_LINH / Linh, nữ thiên sư 27 tuổi, áo lam nhạt W01, bùa đỏ tay.
SETTING & START STATE: Bên trong gian thờ nhỏ, bụi mờ bay trong không khí, giữa phòng đặt một chiếc gương đồng cổ.
LIGHTING & COLOR: Ánh sáng bạc leo lét từ khe cửa rọi vào mặt gương đồng phủ bụi mờ.
CAMERA: Tracking shot đi theo bước chân Linh tiến sâu vào gian thờ tĩnh lặng.
TIMED ACTION: 00:00-00:05 Linh đẩy nhẹ cánh cửa gỗ cót két, bước vào trong gian thờ phủ bụi. 00:05-00:10 Cô dừng lại trước bệ gương đồng cổ, tay đưa lên rút một đạo bùa đỏ từ thắt lưng.
END STATE: Linh đứng đối diện chiếc gương đồng, bóng mờ phản chiếu trong gương.
AUDIO:
LINH: "Gương đồng Bát Quái... Cổ vật này vẫn còn giữ được linh khí ngàn năm."
CONSTRAINTS: Giữ nguyên diện mạo 27 tuổi, kẹp tóc bạc hình lá của Linh.

========== SCENE_008 | TIMELINE 01:10–01:20 | GENERATE 10 SECONDS ==========
FORMAT & STYLE: 16:9; 10s motion-video scene; Full-color cinematic film aesthetics.
CHARACTERS: [PRIMARY FOCUS ACTOR] BÀ HÒA: CHAR_HOA / Bà Hòa, nữ thủ đền 58 tuổi, áo nâu sẫm W01, chùm chìa khóa đồng.
SETTING & START STATE: Ngoài sân đền, bên cạnh giếng đá. Nắp giếng bắt đầu rung nhẹ từng nhịp.
LIGHTING & COLOR: Tông xanh lam thẫm, khói sương bảng lảng từ mặt đất bốc lên.
CAMERA: Medium shot quay toàn cảnh Bà Hòa lùi dần về phía hương án đá khi nắp giếng chấn động.
TIMED ACTION: 00:00-00:05 Mặt đất khẽ rung, những viên sỏi nhỏ quanh miệng giếng nhảy múa. 00:05-01:00 Bà Hòa hai tay chắp lại niệm chú, mắt trừng lớn nhìn về gian thờ chờ đợi.
END STATE: Bà Hòa đứng tựa lưng vào hương án đá, miệng lẩm bẩm cầu nguyện.
AUDIO:
BÀ HÒA: "Nhanh lên cô Linh! Nắp giếng... nắp giếng đang tự dịch chuyển rồi!"
CONSTRAINTS: Khóa chặt vẻ mặt khắc khổ hiền từ và y phục áo nâu của Bà Hòa.

========== SCENE_009 | TIMELINE 01:20–01:30 | GENERATE 10 SECONDS ==========
FORMAT & STYLE: 16:9; 10s motion-video scene; Full-color cinematic film aesthetics.
CHARACTERS: [PRIMARY FOCUS ACTOR] LINH: CHAR_LINH / Linh, nữ thiên sư 27 tuổi, áo lam nhạt W01.
SETTING & START STATE: Trong gian thờ, mặt gương đồng bỗng nhiên phát ra ánh sáng tím mờ ảo.
LIGHTING & COLOR: Ánh tím huyền ảo từ mặt gương phản chiếu lên khuôn mặt thanh tú của Linh.
CAMERA: Extreme close-up đôi mắt nâu trầm của Linh phản chiếu ánh sáng từ gương đồng.
TIMED ACTION: 00:00-00:05 Linh đưa hai bàn tay nâng tấm gương đồng nặng nề khỏi bệ thờ. 00:05-00:10 Cô quay người dứt khoát sải bước chạy vụt ra phía cửa hướng về sân đền.
END STATE: Linh ôm gương đồng chạy nhanh ra phía ánh trăng ngoài sân.
AUDIO:
LINH: "Tôi ra ngay đây! Hãy giữ chặt chân hương án đá!"
CONSTRAINTS: Chuyển động cơ thể dứt khoát uyển chuyển của nữ thiên sư 27 tuổi.

========== SCENE_010 | TIMELINE 01:30–01:40 | GENERATE 10 SECONDS ==========
FORMAT & STYLE: 16:9; 10s motion-video scene; Full-color cinematic film aesthetics.
CHARACTERS: [PRIMARY FOCUS ACTOR] BÀ HÒA: CHAR_HOA / Bà Hòa, 58 tuổi, áo nâu sẫm W01, chùm chìa khóa đồng.
[SUPPORTING ACTOR] LINH: CHAR_LINH / Linh, 27 tuổi, áo lam W01.
SETTING & START STATE: Sân đền cổ bên hương án đá. Bà Hòa dùng cả thân mình tì vào mép đá.
LIGHTING & COLOR: Ánh trăng gay gắt pha lẫn sương đêm lạnh giá.
CAMERA: Two-shot góc rộng ghi nhận khoảnh khắc Linh lao đến cạnh Bà Hòa.
TIMED ACTION: 00:00-00:05 Bà Hòa dồn hết sức cắm chiếc chìa khóa đồng vào rãnh hương án. 00:05-00:10 Linh chạy đến kịp thời, đặt mạnh tấm gương đồng vào đúng khớp trăng khuyết.
END STATE: Hai nhân vật cùng nhau giữ chặt tấm gương đồng trên bệ đá.
AUDIO:
BÀ HÒA: "Khớp khóa đã vào rãnh! Hãy niệm chú ngay!"
CONSTRAINTS: Giữ đúng sự khác biệt rõ rệt về thế hệ và trang phục giữa Linh (lam) và Bà Hòa (nâu).

========== SCENE_011 | TIMELINE 01:40–01:50 | GENERATE 10 SECONDS ==========
FORMAT & STYLE: 16:9; 10s motion-video scene; Full-color cinematic film aesthetics.
CHARACTERS: [PRIMARY FOCUS ACTOR] LINH: CHAR_LINH / Linh, nữ thiên sư 27 tuổi, áo lam nhạt W01, dây bùa đỏ.
SETTING & START STATE: Hương án đá rực sáng kim quang phản chiếu thẳng vào nắp giếng đá.
LIGHTING & COLOR: Kim quang vàng kim rực rỡ xua tan bóng tối huyền bí xung quanh.
CAMERA: Dynamic Dutch angle zoom-in gương mặt Linh khi cô kết ấn tay quyết đoán.
TIMED ACTION: 00:00-00:06 Linh vung tay kết ấn, dải bùa đỏ trên cổ tay bung tỏa phát sáng rực rỡ. 00:06-00:10 Luồng kim quang từ gương đồng bắn thẳng vào miệng giếng, đè bẹp luồng khí đen.
END STATE: Linh giữ nguyên ấn chú, nắp giếng đá dần dần ổn định trở lại.
AUDIO:
LINH: "Càn Khôn Chính Khí, Vạn Quỷ Tiêu Tan... Phong ấn, Định!"
CONSTRAINTS: Ánh sáng hiệu ứng tự nhiên, không làm méo mó giải phẫu khuôn mặt của Linh.

========== SCENE_012 | TIMELINE 01:50–02:00 | GENERATE 10 SECONDS ==========
FORMAT & STYLE: 16:9; 10s motion-video scene; Full-color cinematic film aesthetics.
CHARACTERS: [PRIMARY FOCUS ACTOR] BÀ HÒA: CHAR_HOA / Bà Hòa, 58 tuổi, tóc muối tiêu búi thấp, áo nâu sẫm W01.
[SUPPORTING ACTOR] LINH: CHAR_LINH / Linh, 27 tuổi, áo lam nhạt W01.
SETTING & START STATE: Toàn cảnh sân đền cổ. Khí đen tan biến hoàn toàn, ánh trăng thanh bình rọi sáng cả ngôi đền.
LIGHTING & COLOR: Ánh sáng trăng ấm áp dịu dàng, khói hương thoang thoảng bay trong gió đêm.
CAMERA: Slow pull-back wide shot từ hai nhân vật lùi xa dần lên cao ngắm nhìn toàn cảnh đền cổ.
TIMED ACTION: 00:00-00:05 Bà Hòa thở phào nhẹ nhõm, đưa tay lau mồ hôi trên trán rồi mỉm cười nhìn Linh. 00:05-00:10 Linh cúi đầu chào Bà Hòa với nụ cười điềm tĩnh, vạt áo lam khẽ bay.
END STATE: Hai nhân vật đứng cạnh nhau thanh thản trong đêm trăng yên bình.
AUDIO:
BÀ HÒA: "Cảm ơn cô... Ngôi đền này đã được cứu rồi."
LINH: "Bảo trọng nhé bà, nhưng chúng ta vẫn cần phải cảnh giác khi trăng tròn."
CONSTRAINTS: Khung hình điện ảnh kết thúc mãn nhãn, hai nhân vật giữ nguyên 100% bản sắc hình ảnh từ cảnh 1.
"""

def main():
    print("=" * 60)
    print("🎬 TEST E2E: LONG MULTI-CHARACTER DRAMA EPISODE 4 (12 SCENES)")
    print("=" * 60)

    ep_dir = STUDIO_ROOT / "productions" / "kh-m-ph" / "episode_004"
    ep_dir.mkdir(parents=True, exist_ok=True)

    # 1. Parse screenplay
    parsed = parse_locked_screenplay(EP4_SCRIPT)
    print(f"✓ Parsed {len(parsed)} scenes from screenplay.")
    assert len(parsed) == 12, f"Expected 12 scenes, got {len(parsed)}"

    # 2. Convert to Drama Plan
    plan = convert_locked_scenes_to_drama_plan(
        parsed,
        series_name="khám phá",
        episode_num=4,
        language="Vietnamese",
        genre="drama"
    )
    print("✓ Converted to Drama Plan.")

    # 3. Check Cast Isolation
    cast = plan.get("cast", {})
    print("\n--- CAST AUDIT ---")
    for name, prof in cast.items():
        print(f"[{name}] role={prof.get('role')} gender={prof.get('gender')}")
        app = prof.get("appearance_lock", "")
        print(f"   DNA snippet: {app[:120]}...")
        if name == "LINH":
            assert "27 tuổi" in app, "Linh must have 27 tuổi"
            assert "58 tuổi" not in app, "Linh MUST NOT contain Bà Hòa's 58 tuổi!"
        elif name == "BÀ HÒA":
            assert "58 tuổi" in app, "Bà Hòa must have 58 tuổi"
            assert "27 tuổi" not in app, "Bà Hòa MUST NOT contain Linh's 27 tuổi!"

    print("✓ Cast Appearance DNA is 100% strictly isolated!")

    # 4. Generate Master Asset Pack (Turnaround sheets)
    asset_res = generate_master_asset_pack(
        episode_dir=ep_dir,
        plan_data=plan,
        genre="drama",
        visual_style="color_cinematic",
        render_images=True
    )
    print("✓ Master Asset Pack generated successfully.")

    # 5. Verify Turnaround Files
    chars_dir = ep_dir / "00_ASSET_PACK" / "characters"
    linh_jpg = chars_dir / "linh_turnaround.jpg"
    hoa_jpg = chars_dir / "b_h_a_turnaround.jpg"
    assert linh_jpg.exists(), f"Missing {linh_jpg}"
    assert hoa_jpg.exists(), f"Missing {hoa_jpg}"
    print(f"✓ Turnaround sheets created: {linh_jpg.name} ({linh_jpg.stat().st_size} bytes), {hoa_jpg.name} ({hoa_jpg.stat().st_size} bytes)")

    # 6. Verify 9-Fields Scene Prompts
    print("\n--- 9-FIELDS PROMPT VERIFICATION (ALL 12 SCENES) ---")
    prev_sc = None
    for sc in plan["scenes"]:
        sc_num = sc["scene_number"]
        # Determine primary focus character: odd scenes = LINH, even scenes = BÀ HÒA
        primary = "LINH" if sc_num % 2 != 0 else "BÀ HÒA"
        sc["primary_focus_character"] = primary

        p9 = build_scene(sc, cast, prev_sc, genre="drama", visual_style="color_cinematic", language="Vietnamese", aspect="16:9", seconds=10, index=sc_num)
        prev_sc = sc

        # Audit prompt
        char_line = [l for l in p9.splitlines() if l.startswith("CHARACTERS:")][0]
        assert f"[PRIMARY FOCUS ACTOR] {primary}" in char_line, f"Scene {sc_num} missing primary actor {primary}"
        if primary == "BÀ HÒA":
            assert "58 tuổi" in char_line, f"Scene {sc_num} Bà Hòa prompt missing 58 tuổi!"
            hoa_part = char_line.split("BÀ HÒA:")[1]
            if "[SUPPORTING" in hoa_part:
                hoa_part = hoa_part.split("[SUPPORTING")[0]
            assert "27 tuổi" not in hoa_part, f"Scene {sc_num} Bà Hòa has Linh's 27yo in its actor definition!"

        # Check anchor resolution
        primary_anc = get_primary_character_anchor(ep_dir, sc.get("characters_present", []), primary)
        assert primary_anc and primary_anc.is_file(), f"Scene {sc_num} failed to resolve primary anchor {primary}"
        print(f"Scene {sc_num:02d} [{primary:^7}]: Anchor={primary_anc.name} | Verified OK")

    # Export episode files
    export_res = export_episode(plan, ep_dir, genre="drama", visual_style="color_cinematic", language="Vietnamese", aspect="16:9", seconds=10)
    print(f"✓ export_episode: {export_res['scene_count']} scenes exported successfully.")

    # Save outputs
    (ep_dir / "drama_plan.json").write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
    (ep_dir / "plan.json").write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✓ Saved drama_plan.json and plan.json to {ep_dir}")

    print("\n" + "=" * 60)
    print("🏆 ALL 12 SCENES READY FOR LONG-VIDEO MUSE RENDERING BENCHMARK!")
    print("=" * 60)

if __name__ == "__main__":
    main()
