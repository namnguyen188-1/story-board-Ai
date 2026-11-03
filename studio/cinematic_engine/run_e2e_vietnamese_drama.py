"""E2E Production Test: Vietnamese High-Tension Family Drama.
Generates a complete multi-scene episode:
- Hook cực mạnh & đối thoại kịch tính (Family succession conflict, forged will & medical conspiracy)
- Đồng nhất nhân vật (Character DNA locks for Vu Hoang Minh & Ba Bich Loan)
- Đồng nhất bối cảnh (Classical luxury villa library in Dalat storm)
- Full audio multi-voice synthesis + BGM auto-ducking + SFX + Subtitles + Final video
"""
import sys
import os
import json
import time
from pathlib import Path

# Fix Windows stdout encoding
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

STUDIO_ROOT = Path(__file__).resolve().parent.parent
if str(STUDIO_ROOT) not in sys.path:
    sys.path.insert(0, str(STUDIO_ROOT))

from pipeline_router import route_production


class ProductionArgs:
    def __init__(self, **kwargs):
        self.production_mode = "cinematic_drama"
        self.series = "Gia Tộc Họ Vũ"
        self.episode = 1
        self.language = "Vietnamese"
        self.genre = "family_drama"
        self.minutes = 1.0  # 3 tight high-tension dramatic scenes
        self.scene_seconds = 20.0
        self.size = "1280x720"
        self.aspect_ratio = "16:9"
        self.image_provider = "muse_video"
        self.resume = True
        self.prompt = (
            "Đêm giông bão sấm sét tại biệt thự họ Vũ ở Đà Lạt. Cậu cả Vũ Hoàng Minh "
            "(32 tuổi, vest đen may đo sang trọng, ánh mắt sắc lạnh cương nghị) bất ngờ trở về "
            "sau cái chết đáng ngờ của người cha Chủ tịch tập đoàn. Anh đối đầu trực diện với mẹ kế "
            "là bà Bích Loan (52 tuổi, áo dài nhung đỏ mận quý phái, ánh mắt xảo quyệt, đeo chuỗi ngọc lục bảo). "
            "Hoàng Minh ném bản kết quả giám định chữ ký và hồ sơ bệnh án bị đánh tráo lên bàn gỗ mun, "
            "vạch trần âm mưu chiếm đoạt toàn bộ cổ phần tập đoàn 2000 tỷ. Hai bên đấu khẩu kịch tính, "
            "tung những câu thoại sắc lẹm, bóc trần bộ mặt thật của nhau trước khi luật sư gia đình "
            "bước vào với chiếc USB chứa video trăn trối cuối cùng."
        )
        for k, v in kwargs.items():
            setattr(self, k, v)


def main():
    print("=" * 70)
    print("🎬 KIỂM THỬ E2E: SẢN XUẤT 1 TẬP PHIM DRAMA VIỆT NAM HOÀN CHỈNH")
    print("   Chủ đề: Gia Tộc Họ Vũ - Tập 1: Bản Di Chúc Giả Mạo")
    print("   Tiêu chí: Hook mạnh, đối thoại sắc lẹm, đồng nhất nhân vật & bối cảnh")
    print("=" * 70)

    args = ProductionArgs()
    start_time = time.time()

    exit_code = route_production(args)
    elapsed = time.time() - start_time

    if exit_code != 0:
        print(f"\n[FAIL] Quá trình sản xuất thất bại với mã lỗi: {exit_code}")
        return False

    # Inspect produced assets
    from series_studio import slug
    series_slug = slug(args.series)
    ep_dir = STUDIO_ROOT / "productions" / series_slug / f"episode_{args.episode:03d}"
    plan_file = ep_dir / "drama_plan.json"
    final_video = ep_dir / f"episode_{args.episode:03d}_final.mp4"

    assert plan_file.exists(), f"Không tìm thấy drama_plan.json tại {plan_file}"
    assert final_video.exists(), f"Không tìm thấy video cuối cùng tại {final_video}"

    with open(plan_file, "r", encoding="utf-8") as f:
        plan = json.load(f)

    print("\n" + "=" * 70)
    print("📊 BÁO CÁO NGHIỆM THU ĐỒNG NHẤT NHÂN VẬT & BỐI CẢNH:")
    print("=" * 70)
    print(f"🎬 TỰA ĐỀ TẬP PHIM: {plan.get('title')}")
    print(f"📌 LOGLINE / HOOK: {plan.get('logline')}")
    print(f"🏰 BỐI CẢNH CHÍNH (MASTER SETTING): {plan.get('master_setting')}")

    print("\n🎭 DANH SÁCH NHÂN VẬT & DNA KHÓA NGOẠI HÌNH (CHARACTER DNA LOCKS):")
    for name, char in plan.get("cast", {}).items():
        if name != "Narrator":
            print(f"  • {name} ({char.get('gender')}, vai: {char.get('role')}):")
            print(f"    - Giọng đọc: {char.get('voice_id')} ({char.get('voice_label')})")
            print(f"    - Khóa ngoại hình (Appearance Lock): {char.get('appearance_lock')}")

    print("\n📜 TRÍCH ĐOẠN ĐỐI THOẠI & NHỊP KỊCH TÍNH (SCREENPLAY BEATS):")
    for sc in plan.get("scenes", []):
        print(f"\n--- [CẢNH {sc['scene_number']:02d}: {sc.get('setting')}] ---")
        print(f"    Tóm tắt: {sc.get('summary')}")
        print(f"    BGM & SFX: {sc.get('bgm_mood')} | {sc.get('sfx_cues')}")
        print(f"    Khung hình: {sc.get('visual_setup', '')[:80]}...")
        for b in sc.get("dialogue_beats", []):
            spk = b.get("speaker")
            tone = b.get("tone")
            txt = b.get("text")
            act = b.get("action")
            print(f"    [{spk}] ({tone}): \"{txt}\"")
            if act:
                print(f"        -> Hành động: {act}")

    print("\n" + "=" * 70)
    print(f"🎞️ TẬP PHIM ĐÃ XUẤT RA THÀNH CÔNG:")
    print(f"   File video: {final_video}")
    print(f"   Dung lượng: {final_video.stat().st_size / 1024 / 1024:.2f} MB")
    print(f"   Thời gian thực hiện toàn bộ quy trình: {elapsed:.1f} giây")
    print("=" * 70)
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
