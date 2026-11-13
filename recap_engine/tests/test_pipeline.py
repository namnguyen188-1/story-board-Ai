import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline import MovieRecapPipeline

print("=== STARTING FULL END-TO-END MOVIE RECAP PIPELINE TEST ===", flush=True)

pipeline = MovieRecapPipeline()

test_video = Path(__file__).resolve().parent.parent / "demo_assets" / "test_sample.mp4"
if not test_video.is_file():
    test_video = Path(r"D:\STORYBOARD_AI\recap_engine\test_sample.mp4")

result = pipeline.run(
    source_video=str(test_video),
    movie_title="Đặc Nhiệm Bất Tử",
    genre="Hành động Kịch tính",
    target_minutes=0.25,  # 15-second fast test
    aspect_ratio="16:9",
    voice_name="Fenrir",
    voice_speed=1.15,
    user_aliases={"Điệp viên 007": "anh Áo Đen", "Kẻ Phản Diện": "gã Đầu Trọc"},
    watermark_text="@ReviewPhimTop1"
)

print("\n=== PIPELINE COMPLETED SUCCESSFULLY ===")
print("Exported Video:", result.get("video_path"))
print("Duration:", result.get("duration"), "seconds")
print("Total Render Time:", result.get("total_render_time"), "seconds")
print("Cuts Count:", result.get("cuts_count"))
