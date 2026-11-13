import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pipeline import MovieRecapPipeline

print("==================================================================", flush=True)
print("🎬 STARTING REAL MOVIE END-TO-END RECAP TEST", flush=True)
print("==================================================================", flush=True)

pipeline = MovieRecapPipeline()

result = pipeline.run(
    source_video=r"D:\STORYBOARD_AI\recap_engine\demo_real_movie.mp4",
    movie_title="Âm Mưu Ngày Cưới Của Thợ Trang Điểm",
    genre="Tâm lý, Kịch tính, Xã hội",
    target_minutes=1.5,  # 1.5 minutes review (approx 20 segments)
    aspect_ratio="16:9",
    voice_name="Fenrir",
    voice_speed=1.15,
    subtitle_file=r"D:\STORYBOARD_AI\recap_engine\demo_movie.srt",
    user_aliases={
        "Pamela": "cô Dâu Sang Chảnh",
        "Make Up Artist": "chị Thợ Trang Điểm",
        "Groom": "chú Rể Giàu Có"
    },
    watermark_text="@ReviewPhimHay"
)

print("\n==================================================================", flush=True)
print("🎉 REAL E2E MOVIE RECAP PIPELINE FINISHED SUCCESSFULLY!", flush=True)
print("==================================================================", flush=True)
print("Exported Video Path :", result.get("video_path"))
print("Review Duration     :", result.get("duration"), "seconds")
print("Total Render Time   :", result.get("total_render_time"), "seconds")
print("Total Video Cuts    :", result.get("cuts_count"))
print("Session Folder      :", result.get("session_dir"))
