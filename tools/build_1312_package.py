"""Build and verify Storyboard_AI_Studio_Pro_v1.3.12.zip from 1.3.11 baseline with all 7 skills and 5s pacing."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import zipfile

ROOT = Path(r"D:\STORYBOARD_AI")
DIST = ROOT / "dist"
BASE = DIST / "Storyboard_AI_Studio_Pro_v1.3.11.zip"
OUT = DIST / "Storyboard_AI_Studio_Pro_v1.3.12.zip"
STAGE = DIST / "_stage_v1312_final"
SEVEN = Path(r"C:\Program Files\7-Zip\7z.exe")

assert BASE.is_file(), f"Baseline not found: {BASE}"
assert SEVEN.is_file(), f"7-Zip not found: {SEVEN}"

if STAGE.exists():
    shutil.rmtree(STAGE, ignore_errors=True)
STAGE.mkdir(parents=True, exist_ok=True)

# 1. Collect all target files to stage
files_to_overlay = []

# All 7 skills
for skill_file in (ROOT / ".agents" / "skills").rglob("*"):
    if skill_file.is_file() and "__pycache__" not in skill_file.parts:
        rel = skill_file.relative_to(ROOT)
        files_to_overlay.append(str(rel).replace("\\", "/"))

# Core studio files updated
studio_updates = [
    "studio/reference_scene_assembler.py",
    "studio/version.json",
    "studio/series_studio.py",
    "studio/web_server.py",
    "studio/web/app.js",
    "studio/web/index.html",
    "studio/tests/test_narrative_5s_pacing_e2e.py",
]

# Include cinematic drama updates from 1.3.12 RC2
cinematic_updates = [
    "studio/cinematic_engine/drama_asset_first.py",
    "studio/cinematic_engine/drama_aspect_repair.py",
    "studio/cinematic_engine/drama_asset_manager.py",
    "studio/cinematic_engine/drama_orchestrator.py",
    "studio/cinematic_engine/drama_video_engine.py",
    "studio/cinematic_engine/drama_skill9.py",
    "studio/cinematic_engine/drama_schema.py",
    "studio/cinematic_engine/drama_planner.py",
    "studio/cinematic_engine/drama_voice_director.py",
    "studio/muse_asset_images.py",
    "studio/muse_scene_image.py",
    "studio/drama_preproduction_worker.py",
    "studio/muse_video_provider.py",
    "studio/muse_gateway_worker.py",
    "studio/comfyui_image_provider.py",
    "studio/comfyui_identity_refs.py",
    "studio/drama_asset_review_api.py",
    "studio/web/drama_asset_review.js",
]

for p in studio_updates + cinematic_updates:
    if (ROOT / p).is_file():
        files_to_overlay.append(p)

files_to_overlay = sorted(list(set(files_to_overlay)))

print(f"Staging {len(files_to_overlay)} files into {STAGE}...")
for rel_path in files_to_overlay:
    src = ROOT / rel_path
    dst = STAGE / rel_path
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

# Ensure version.json is strictly 1.3.12
ver_json = STAGE / "studio" / "version.json"
ver_data = {
    "version": "1.3.12",
    "app_name": "Storyboard AI Studio Pro",
    "release_date": "2026-11-04"
}
ver_json.write_text(json.dumps(ver_data, indent=2, ensure_ascii=False), encoding="utf-8")

# 2. Build OUT zip from BASE
if OUT.exists():
    OUT.unlink()
print(f"Copying baseline {BASE} to {OUT}...")
shutil.copyfile(BASE, OUT)

print("Applying overlay with 7-Zip...")
cmd = [str(SEVEN), "u", "-tzip", str(OUT), *files_to_overlay, "-y"]
res = subprocess.run(cmd, cwd=STAGE, capture_output=True, text=True, timeout=300)
if res.returncode != 0:
    raise RuntimeError(f"7-Zip update failed:\n{res.stderr}\n{res.stdout}")

# 3. Verify ZIP integrity
print("Verifying updated ZIP integrity...")
with zipfile.ZipFile(OUT) as zf:
    test_result = zf.testzip()
    assert test_result is None, f"Corrupted zip entry: {test_result}"
    
    # Check version.json
    ver = json.loads(zf.read("studio/version.json").decode("utf-8"))
    assert ver["version"] == "1.3.12", f"Expected version 1.3.12, got {ver}"
    
    # Check 5s pacing patch in reference_scene_assembler.py
    assembler_code = zf.read("studio/reference_scene_assembler.py").decode("utf-8", errors="ignore")
    assert "min_words=max(6," in assembler_code, "5s patch missing in ZIP!"
    
    # Check all 7 skills are present
    namelist = zf.namelist()
    expected_skills = [
        "create-youtube-thumbnail",
        "publish-youtube-drama",
        "publish-youtube-narrative",
        "publish-youtube-shorts",
        "write-narrative-scene-prompts",
        "write-video-scene-prompts",
        "write-viral-shorts-prompts"
    ]
    for s in expected_skills:
        found = any(f".agents/skills/{s}/" in name for name in namelist)
        assert found, f"Skill {s} missing in ZIP!"

out_bytes = OUT.stat().st_size
hasher = hashlib.sha256()
with OUT.open("rb") as f:
    while chunk := f.read(1024 * 1024):
        hasher.update(chunk)
out_sha = hasher.hexdigest().upper()

print("\n" + "=" * 60)
print("BUILD SUCCESSFUL!")
print(f"File:   {OUT}")
print(f"Bytes:  {out_bytes}")
print(f"SHA256: {out_sha}")
print("=" * 60)

# Write manifest and release notes
notes_content = """## 🚀 Storyboard AI Studio Pro - Bản Cập Nhật v1.3.12

### ⏱️ 1. Hỗ Trợ Nhịp Cảnh 5 Giây (5s Pacing) Chế Độ Kể Chuyện (Narrative)
- **Tùy chỉnh tự do 5s–60s/cảnh**: Mở khóa hoàn toàn ô độ dài cảnh, không bị giới hạn cứng.
- **Tự động đồng bộ ngân sách ảnh**: Video 1 phút chia đều 12 cảnh (12 ảnh), video dài 5 phút chia 60 cảnh (60 ảnh), video 10 phút chia 120 cảnh.
- **Khớp chuẩn dung lượng giọng đọc (TTS)**: Tối ưu ngưỡng từ xuống 6–7 từ cho cảnh 5 giây, triệt tiêu lỗi thiếu từ `SCENE_VISION_DESCRIPTION_TOO_SHORT`.

### 🧠 2. Tách Biệt Độc Lập Trọn Bộ 7 Kỹ Năng AI Chuyên Sâu (.agents/skills)
- **Kể Chuyện / Thuyết Minh (16:9 Dài)**: Cặp skill `write-narrative-scene-prompts` (prompt ảnh ngắn 40–80 từ) + `publish-youtube-narrative` (SEO chuyên sâu, timestamps thực tế, thumbnail 50/50).
- **Shorts Triệu View (9:16 Dọc <60s)**: Cặp skill `write-viral-shorts-prompts` (nhịp cắt 2–3s, siêu Hook 3s đầu, vòng lặp vô tận Loop) + `publish-youtube-shorts` (tiêu đề <50 ký tự, né vùng an toàn UI Shorts).
- **Phim Kịch Đa Vai (Cinematic Drama)**: Cặp skill `write-video-scene-prompts` (video prompt 9 trường cố định 10s Muse) + `publish-youtube-drama` (mâu thuẫn kịch tính, đối đầu, character consistency).
- **Thiết Kế Thumbnail Độc Lập**: Skill `create-youtube-thumbnail` vẽ chữ 3D Vàng kim hoàng gia / Cam hổ phách rực rỡ, Google Flow tự vẽ 3D hòa quyện ánh sáng, tự động xóa sạch logo watermark.

### 🌐 3. Chuẩn Hóa Cấu Hình Đăng Bài YouTube
- Khớp chuẩn 100% ngôn ngữ phụ đề & âm thanh (Tây Ban Nha, Tiếng Việt, Tiếng Anh).
- Chứng nhận phụ đề FCC chuẩn quốc tế (Nội dung chưa từng phát sóng truyền hình tại Hoa Kỳ).
"""

notes_path = DIST / "RELEASE_NOTES_v1.3.12.md"
notes_path.write_text(notes_content.strip(), encoding="utf-8")

manifest_data = {
    "version": "1.3.12",
    "release_name": "Storyboard_AI_Studio_Pro_v1.3.12",
    "installer": "https://github.com/anma8802-create/AI-tool/releases/latest/download/Storyboard_AI_Studio_Pro_v1.3.12.zip",
    "bytes": out_bytes,
    "sha256": out_sha,
    "release_notes": [
        "Hỗ trợ phân cảnh 5 giây (5s Pacing) cho chế độ Kể Chuyện (Narrative) cả video ngắn 1 phút và video dài.",
        "Tự động tính toán đúng số cảnh và ngân sách ảnh theo thời lượng (1 phút = 12 ảnh, 5 phút = 60 ảnh, 10 phút = 120 ảnh).",
        "Đồng bộ trọn bộ 7 kỹ năng AI chuyên biệt độc lập (.agents/skills) cho Kể Chuyện, Phim Kịch, Shorts 9:16 và Thumbnail 3D.",
        "Thiết kế Thumbnail 3D màu vàng kim hoàng gia / cam hổ phách rực rỡ bắt mắt, Google Flow tự vẽ 3D và tự khử watermark.",
        "Chuẩn hóa cấu hình đăng bài YouTube: đúng ngôn ngữ và chứng nhận phụ đề FCC.",
        "Tích hợp bộ kiểm thử E2E tự động xác thực toàn diện tiến trình sản xuất."
    ]
}

manifest_path = DIST / "latest_v1.3.12.json"
manifest_path.write_text(json.dumps(manifest_data, indent=2, ensure_ascii=False), encoding="utf-8")

# Also update dist/latest.json
(DIST / "latest.json").write_text(json.dumps(manifest_data, indent=2, ensure_ascii=False), encoding="utf-8")
# And root latest.json
(ROOT / "latest.json").write_text(json.dumps(manifest_data, indent=2, ensure_ascii=False), encoding="utf-8")

print("Generated RELEASE_NOTES_v1.3.12.md and latest_v1.3.12.json successfully!")
