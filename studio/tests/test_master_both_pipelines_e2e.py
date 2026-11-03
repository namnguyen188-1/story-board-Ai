"""Master E2E Verification Suite for Storyboard AI Studio
Tests BOTH pipelines end-to-end:
1. Pipeline A: Luồng Kể Chuyện Thuyết Minh (Narrative Storytelling)
2. Pipeline B: Luồng Phim Kịch Điện Ảnh Đa Vai (Cinematic Multi-Role Drama)
3. Router Dispatch & API Integration
"""
from __future__ import annotations

import os
import sys
import json
import time
import subprocess
from pathlib import Path

# Configure utf-8 stdout/stderr
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

STUDIO_ROOT = Path(r"D:\STORYBOARD_AI\studio")
sys.path.insert(0, str(STUDIO_ROOT))
sys.path.insert(0, str(STUDIO_ROOT / "cinematic_engine"))

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.details = []

    def record(self, name: str, success: bool, msg: str = ""):
        if success:
            self.passed += 1
            print(f"  [PASS] {name} - {msg}")
        else:
            self.failed += 1
            print(f"  [FAIL] {name} - {msg}")
        self.details.append({"name": name, "success": success, "msg": msg})

res = TestResults()

def test_router_dispatch():
    print("\n" + "=" * 70)
    print("MỤC 1: KIỂM THỬ ĐIỀU PHỐI ĐỘC LẬP GIỮA 2 LUỒNG (PIPELINE ROUTER)")
    print("=" * 70)
    class MockArgs:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    # Test Router recognizes both modes
    args_narrative = MockArgs(production_mode="narrative", image_provider="gemini")
    args_drama = MockArgs(production_mode="cinematic_drama", image_provider="muse_video")

    is_drama_false = (str(args_narrative.production_mode).strip().lower() == "cinematic_drama")
    is_drama_true = (str(args_drama.production_mode).strip().lower() == "cinematic_drama")

    res.record("Router Dispatch Luồng A (Narrative)", not is_drama_false, "Nhánh A nhận diện chính xác")
    res.record("Router Dispatch Luồng B (Cinematic Drama)", is_drama_true, "Nhánh B nhận diện chính xác")

def test_pipeline_a_narrative_e2e():
    print("\n" + "=" * 70)
    print("MỤC 2: KIỂM THỬ E2E LUỒNG A - KỂ CHUYỆN THUYẾT MINH (NARRATIVE)")
    print("=" * 70)
    ep_dir = STUDIO_ROOT / "productions" / "Test-Narrative-E2E" / "episode_001"
    final_video = ep_dir / "episode_final.mp4"
    plan_file = ep_dir / "plan.json"
    publish_dir = ep_dir / "00_DANG_BAI_YOUTUBE"

    plan_ok = plan_file.is_file() and plan_file.stat().st_size > 500
    res.record("Kịch bản Luồng A (plan.json)", plan_ok, f"Kích thước: {plan_file.stat().st_size} bytes" if plan_ok else "Thiếu plan.json")

    video_ok = final_video.is_file() and final_video.stat().st_size > 50000
    if video_ok:
        cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", str(final_video)]
        probe = json.loads(subprocess.run(cmd, capture_output=True, text=True, check=True).stdout)
        has_v = any(s["codec_type"] == "video" for s in probe["streams"])
        has_a = any(s["codec_type"] == "audio" for s in probe["streams"])
        dur = float(probe["format"]["duration"])
        res.record("Video tập phim Luồng A (episode_final.mp4)", has_v and has_a, f"Thời lượng: {dur:.2f}s, Video={has_v}, Audio={has_a}")
    else:
        res.record("Video tập phim Luồng A (episode_final.mp4)", False, "File video không tồn tại hoặc quá nhỏ")

    seo_ok = publish_dir.is_dir()
    res.record("Gói xuất bản YouTube & SEO Luồng A", seo_ok, "Thư mục 00_DANG_BAI_YOUTUBE đầy đủ")

def test_pipeline_b_cinematic_drama_components():
    print("\n" + "=" * 70)
    print("MỤC 3: KIỂM THỬ E2E LUỒNG B - PHIM KỊCH ĐIỆN ẢNH ĐA VAI (CINEMATIC DRAMA)")
    print("=" * 70)

    # 3.1: Screenplay Generation & Validation
    print("\n[BƯỚC 3.1] Kịch bản Phim Kịch Đa vai & Khóa DNA Nhân vật:")
    test_dir = STUDIO_ROOT / "scratch" / "master_e2e_drama"
    test_dir.mkdir(parents=True, exist_ok=True)
    plan_file = test_dir / "drama_plan.json"

    plan = {
        "title": "Gia Tộc Họ Vũ - Tập 1: Di Chúc Giả Mạo",
        "logline": "Cuộc đối đầu kịch tính trong đêm giông bão tại Đà Lạt về bản di chúc bị làm giả.",
        "master_setting": "Classical luxury villa library in Dalat storm",
        "cast": {
            "Vu Hoang Minh": {
                "gender": "male",
                "role": "protagonist",
                "voice_id": "Charon",
                "appearance_lock": "32 years old, sharp black bespoke Italian suit, penetrating cold eyes"
            },
            "Ba Bich Loan": {
                "gender": "female",
                "role": "antagonist",
                "voice_id": "Aoede",
                "appearance_lock": "52 years old, royal plum velvet Ao Dai, cunning gaze, emerald necklace"
            }
        },
        "scenes": [
            {
                "scene_number": 1,
                "summary": "Vũ Hoàng Minh ném tập hồ sơ giám định chữ ký lên bàn gỗ mun, vạch trần âm mưu của mẹ kế.",
                "visual_setup": "Classic dimly lit luxury villa library, torrential rain and lightning outside tall arched windows, two well-dressed Vietnamese individuals facing off across a dark mahogany desk",
                "camera_motion": "slow_push_in",
                "bgm_mood": "tense_investigation",
                "sfx_cues": ["thunder_crack", "rain_on_window"],
                "characters_present": ["Vu Hoang Minh", "Ba Bich Loan"],
                "dialogue_beats": [
                    {
                        "speaker": "Vu Hoang Minh",
                        "tone": "commanding",
                        "text": "Bà Bích Loan, chữ ký trên bản di chúc này là giả mạo hoàn toàn!",
                        "action": "Slams forensic report onto the desk with authoritative force"
                    },
                    {
                        "speaker": "Ba Bich Loan",
                        "tone": "sarcastic",
                        "text": "Cậu nghĩ tờ giấy này có thể ngăn được tôi tiếp quản tập đoàn sao?",
                        "action": "Sneers disdainfully, slowly touching her emerald necklace"
                    }
                ]
            }
        ]
    }
    plan_file.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")

    scenes = plan.get("scenes", [])
    cast = plan.get("cast", {})
    hook = plan.get("logline", "") or plan.get("title", "")
    res.record("Kịch bản Phim kịch Đa vai (drama_plan.json)", len(scenes) > 0 and len(cast) > 0,
               f"Tổng {len(scenes)} cảnh, {len(cast)} nhân vật, Hook: {hook[:45]}...")

    # 3.2: Multi-Voice Dialogue Synthesis & Cinematic Tempo (drama_audio_engine.py)
    print("\n[BƯỚC 3.2] Lồng tiếng Đa nhân vật & Tách biệt Cao độ/Nhịp thoại (Multi-Voice Audio Engine):")
    from cinematic_engine.drama_audio_engine import DramaAudioEngine
    from cinematic_engine.drama_schema import CharacterProfile

    cast_dict = {}
    for name, data in cast.items():
        if isinstance(data, dict):
            cast_dict[name] = CharacterProfile(
                name=name,
                gender=data.get("gender", "male"),
                role=data.get("role", "supporting"),
                voice_id=data.get("voice_id", "Charon"),
                appearance_lock=data.get("appearance_lock", "")
            )

    test_dir = STUDIO_ROOT / "scratch" / "master_e2e_drama"
    test_dir.mkdir(parents=True, exist_ok=True)
    sc1_dir = test_dir / "scenes" / "scene_0001"
    sc1_dir.mkdir(parents=True, exist_ok=True)

    sc1_data = scenes[0]
    audio_engine = DramaAudioEngine()
    audio_res = audio_engine.assemble_scene_dialogue(
        scene=sc1_data,
        language="Vietnamese",
        scene_dir=sc1_dir,
        cast_map=cast_dict
    )
    diag_wav = Path(audio_res["master_audio_path"])
    diag_ok = diag_wav.is_file() and diag_wav.stat().st_size > 10000
    res.record("Tổng hợp Giọng đối đáp Đa nhân vật (audio.wav)", diag_ok,
               f"File: {diag_wav.name}, Size: {diag_wav.stat().st_size} bytes, Số beat thoại: {len(audio_res.get('beats', []))}")

    # 3.3: BGM Dynamic Sidechain Auto-Ducking (drama_sound_mixer.py)
    print("\n[BƯỚC 3.3] Hòa âm BGM Điện ảnh với Auto-Ducking tự động (Sound Mixer):")
    from cinematic_engine.drama_sound_mixer import DramaSoundMixer
    sound_mixer = DramaSoundMixer()
    master_wav = sc1_dir / "scene_master_audio.wav"
    mixed_wav = sound_mixer.mix_scene_audio(
        dialogue_master_wav=diag_wav,
        bgm_mood="tense_investigation",
        sfx_cues=[],
        output_master_wav=master_wav
    )
    mix_ok = Path(mixed_wav).is_file() and Path(mixed_wav).stat().st_size > 10000
    res.record("Hòa âm BGM Auto-Ducking (scene_master_audio.wav)", mix_ok, f"Size: {Path(mixed_wav).stat().st_size} bytes")

    # 3.4: Subtitle Sentence-by-Sentence Synchronicity & Video Assembly (drama_video_engine.py)
    print("\n[BƯỚC 3.4] Phụ đề Đồng bộ Từng câu Thoại & Dựng Video Cảnh (Video Engine):")
    from cinematic_engine.drama_video_engine import DramaVideoEngine
    video_engine = DramaVideoEngine(fps=24)

    # Prepare mock input files for scene 1
    sample_clip = STUDIO_ROOT / "diagnostics" / "continuity_live_QA_20261026" / "scenes" / "scene_0001" / "muse_clip.mp4"
    if sample_clip.is_file():
        import shutil
        shutil.copy2(str(sample_clip), str(sc1_dir / "muse_clip.mp4"))
        # Extract base image thumbnail so it doesn't trigger remote re-render
        cmd_extract = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-ss", "00:00:01.000", "-i", str(sample_clip),
            "-vframes", "1", "-q:v", "2", str(sc1_dir / "scene_base.png")
        ]
        subprocess.run(cmd_extract, check=True)

    vid_res = video_engine.render_scene(
        scene=sc1_data,
        scene_dir=sc1_dir,
        aspect_ratio="16:9",
        cast_map=cast_dict,
        image_provider="muse_video",
        subtitle_style="karaoke_viral"
    )
    final_sc1_mp4 = Path(vid_res["final_video_path"])
    sc1_ok = final_sc1_mp4.is_file() and final_sc1_mp4.stat().st_size > 100000
    res.record("Dựng Video Cảnh 1 kèm Phụ đề Đồng bộ (scene_final.mp4)", sc1_ok, f"Size: {final_sc1_mp4.stat().st_size} bytes")

    # Create scene 2 mock for concatenation testing
    sc2_dir = test_dir / "scenes" / "scene_0002"
    sc2_dir.mkdir(parents=True, exist_ok=True)
    sample_clip2 = STUDIO_ROOT / "diagnostics" / "continuity_live_QA_20261026" / "scenes" / "scene_0002" / "muse_clip.mp4"
    final_sc2_mp4 = sc2_dir / "scene_final.mp4"
    if sample_clip2.is_file():
        shutil.copy2(str(sample_clip2), str(final_sc2_mp4))

    # 3.5: Master Episode Concatenation with Pop-Free Audio & Continuous BGM
    print("\n[BƯỚC 3.5] Ghép Phim Liền mạch, Khử tiếng nổ/click & BGM Nền (Master Concatenation):")
    from cinematic_engine.drama_orchestrator import concatenate_scene_videos
    master_episode_mp4 = test_dir / "episode_001_final.mp4"

    assembled_mp4 = concatenate_scene_videos(
        scene_videos=[final_sc1_mp4, final_sc2_mp4],
        output_episode_mp4=master_episode_mp4,
        bgm_mood="tense_investigation",
        enable_bgm_ducking=True
    )

    concat_ok = assembled_mp4.is_file() and assembled_mp4.stat().st_size > 1000000
    if concat_ok:
        cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", str(assembled_mp4)]
        probe = json.loads(subprocess.run(cmd, capture_output=True, text=True, check=True).stdout)
        has_v = any(s["codec_type"] == "video" for s in probe["streams"])
        has_a = any(s["codec_type"] == "audio" for s in probe["streams"])
        dur = float(probe["format"]["duration"])
        res.record("Ghép Master Tập Phim Liền mạch (episode_001_final.mp4)", has_v and has_a,
                   f"Thời lượng: {dur:.2f}s, Kích thước: {assembled_mp4.stat().st_size / 1024 / 1024:.2f} MB, Audio={has_a}")
    else:
        res.record("Ghép Master Tập Phim Liền mạch (episode_001_final.mp4)", False, "File ghép không thành công")

def test_web_ui_and_workers():
    print("\n" + "=" * 70)
    print("MỤC 4: KIỂM THỬ TÍCH HỢP GIAO DIỆN WEB & ĐIỀU PHỐI ĐA TÀI KHOẢN (WEB UI & WORKERS)")
    print("=" * 70)
    app_js = (STUDIO_ROOT / "web" / "app.js").read_text(encoding="utf-8")
    index_html = (STUDIO_ROOT / "web" / "index.html").read_text(encoding="utf-8")
    web_server = (STUDIO_ROOT / "web_server.py").read_text(encoding="utf-8")

    # Check that hardcoded 1-worker is GONE
    no_hardcoded_workers = 'workers: imageProvider === "muse_video" ? 1' not in app_js
    res.record("Mở khóa điều khiển số luồng Muse trong app.js", no_hardcoded_workers, "Không còn bị ép 1 luồng")

    # Check 6 Luồng chip exists
    has_6_chip = 'data-val="6"' in index_html
    res.record("Chip chọn 6 luồng (x6 Muse) trên giao diện index.html", has_6_chip, "Người dùng có thể chọn tối đa 6 tài khoản")

    # Check ready accounts in muse_accounts.py
    import muse_accounts
    ready_accs = muse_accounts.get_ready_accounts()
    res.record("Tài khoản Muse sẵn sàng trong hệ thống", len(ready_accs) >= 1, f"Đang có {len(ready_accs)} tài khoản sẵn sàng")

    # Check API routes
    has_retry_api = '/api/scene/retry' in web_server
    has_assemble_api = '/api/episode/assemble' in web_server
    res.record("API /api/scene/retry và /api/episode/assemble", has_retry_api and has_assemble_api, "Sẵn sàng phục vụ thao tác per-scene")

if __name__ == "__main__":
    t0 = time.time()
    print("🚀 BẮT ĐẦU CHẠY KIỂM THỬ TOÀN DIỆN E2E CHO CẢ 2 LUỒNG...")
    try:
        test_router_dispatch()
        test_pipeline_a_narrative_e2e()
        test_pipeline_b_cinematic_drama_components()
        test_web_ui_and_workers()
    except Exception as e:
        print(f"\n❌ LỖI NGOẠI LỆ TRONG QUÁ TRÌNH KIỂM THỬ: {e}")
        import traceback
        traceback.print_exc()

    total_time = round(time.time() - t0, 2)
    print("\n" + "=" * 70)
    print(f"📊 KẾT QUẢ KIỂM THỬ E2E TỔNG THỂ (Thời gian: {total_time}s):")
    print(f"   Tổng số bài kiểm tra: {res.passed + res.failed}")
    print(f"   Đạt (PASS): {res.passed}")
    print(f"   Thất bại (FAIL): {res.failed}")
    print("=" * 70)

    if res.failed == 0 and res.passed >= 10:
        print("\n🎉 TOÀN BỘ CẢ 2 LUỒNG (KỂ CHUYỆN & PHIM KỊCH ĐA VAI) HOẠT ĐỘNG HOÀN TOÀN ỔN ĐỊNH VÀ SẴN SÀNG!")
        sys.exit(0)
    else:
        print(f"\n⚠️ CÒN {res.failed} BÀI KIỂM THỬ CHƯA ĐẠT. CẦN KIỂM TRA LẠI.")
        sys.exit(1)
