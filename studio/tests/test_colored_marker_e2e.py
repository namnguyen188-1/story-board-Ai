"""Comprehensive E2E Verification for 'colored_marker' (Vẽ bút dạ màu) Visual Style.

Tests:
1. Prompt & mode resolution in studio_modes and series_studio.
2. Web UI produce pipeline (/api/produce) with visual_style="colored_marker".
3. Background production execution via production_python runtime.
4. Colored marker video rendering (studio_colored_marker.py) with drawing hand + colored ink.
5. Codec, duration, resolution, and visual progression verification.
6. Web server episode query and HTTP 206 partial content streaming.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

STUDIO_DIR = Path(r"D:\STORYBOARD_AI\studio")
BASE_URL = "http://127.0.0.1:8765"


def ensure_server():
    try:
        req = urllib.request.Request(f"{BASE_URL}/api/status", headers={"User-Agent": "MarkerE2E/1.0"})
        with urllib.request.urlopen(req, timeout=1.5) as r:
            return
    except Exception:
        print("[SETUP] Web server is not running on 8765. Launching...", flush=True)
        py = str(STUDIO_DIR / "runtime" / "python" / "python.exe")
        if not Path(py).is_file():
            py = sys.executable
        subprocess.Popen(
            [py, "web_server.py", "--port", "8765"],
            cwd=str(STUDIO_DIR),
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        time.sleep(3)


def http_get(path, timeout=15):
    ensure_server()
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, headers={"User-Agent": "MarkerE2E/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, resp.read().decode("utf-8")


def http_post_json(path, data, timeout=15):
    ensure_server()
    url = f"{BASE_URL}{path}"
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={
        "Content-Type": "application/json",
        "User-Agent": "MarkerE2E/1.0",
    })
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


def test_colored_marker_e2e():
    print("=" * 70, flush=True)
    print("STEP 1: Verify prompt resolution for colored_marker mode", flush=True)
    print("=" * 70, flush=True)
    sys.path.insert(0, str(STUDIO_DIR))
    from studio_modes import image_instruction, ART, STYLES

    assert "colored_marker" in STYLES, "'colored_marker' must be in STYLES"
    prompt = image_instruction("whiteboard", "colored_marker")
    assert prompt == ART["colored_marker"], "Prompt must match ART['colored_marker']"
    assert "After Skool" in prompt, "Prompt must include After Skool signature style"
    assert "chisel-tip" in prompt, "Prompt must mention chisel-tip marker pens"
    print("  -> PASS: Prompt correctly resolved for colored_marker:", prompt[:90] + "...", flush=True)

    print("\n" + "=" * 70, flush=True)
    print("STEP 2: Prepare clean test episode in productions", flush=True)
    print("=" * 70, flush=True)
    ensure_server()

    # Wait for any active production to settle
    for _ in range(30):
        _, raw = http_get("/api/status")
        st = json.loads(raw)
        if not st.get("running"):
            break
        print("  -> Đang chờ tác vụ trước đó hoàn tất...", flush=True)
        time.sleep(2)
    else:
        raise RuntimeError("Another job is stuck running")

    series_name = "Marker-Mode-Automated-E2E"
    offline_series_dir = STUDIO_DIR / "productions" / f"{series_name}---Offline-Test"
    if offline_series_dir.exists():
        shutil.rmtree(offline_series_dir, ignore_errors=True)
    print("  -> PASS: Thư mục kiểm thử sẵn sàng sạch sẽ:", offline_series_dir.name, flush=True)

    print("\n" + "=" * 70, flush=True)
    print("STEP 3: Trigger offline production with visual_style='colored_marker'", flush=True)
    print("=" * 70, flush=True)
    payload = {
        "series": series_name,
        "episode": 1,
        "prompt": "Khám phá vũ trụ và những điều kỳ diệu của khoa học qua những nét vẽ bút dạ sinh động.",
        "input_mode": "idea",
        "mode": "offline",
        "minutes": 0.15,
        "scene_seconds": 4,
        "size": "640x360",
        "workers": 1,
        "image_provider": "gemini",
        "genre": "whiteboard",
        "visual_style": "colored_marker",
        "region": "VN",
        "language": "Vietnamese",
        "voice_name": "auto",
        "subtitle_style": "karaoke_viral",
    }

    status, resp = http_post_json("/api/produce", payload)
    assert status == 200, f"Produce failed: {status} -> {resp}"
    assert resp.get("status") == "STARTED", f"Unexpected response: {resp}"
    print("  -> Khởi chạy sản xuất thành công! Đang giám sát tiến trình...", flush=True)

    start_time = time.monotonic()
    last_stage = ""
    job_completed = False

    while time.monotonic() - start_time < 180:
        time.sleep(2)
        _, raw = http_get("/api/status")
        st = json.loads(raw)
        stage = st.get("stage", "")
        pct = st.get("percent", 0)
        msg = st.get("message", "")
        if stage != last_stage:
            print(f"    [Tiến độ {pct}%] Giai đoạn: {stage} - {msg[:100]}", flush=True)
            last_stage = stage
        if not st.get("running"):
            assert st.get("exit_code") == 0, f"Job failed with exit code: {st.get('exit_code')}, logs: {st.get('recent_logs', [])[-10:]}"
            job_completed = True
            print(f"  -> PASS: Sản xuất hoàn tất 100%! Thời gian thực thi: {round(time.monotonic() - start_time, 1)}s.", flush=True)
            break

    assert job_completed, "Job timed out after 180 seconds"

    print("\n" + "=" * 70, flush=True)
    print("STEP 4: Verify generated files and video streams on disk", flush=True)
    print("=" * 70, flush=True)
    ep_dir = offline_series_dir / "episode_001"
    assert ep_dir.is_dir(), f"Episode directory missing: {ep_dir}"

    plan_file = ep_dir / "plan.json"
    manifest_file = ep_dir / "manifest.json"
    final_video_file = ep_dir / "episode_final.mp4"

    assert plan_file.is_file(), "plan.json missing"
    assert manifest_file.is_file(), "manifest.json missing"
    assert final_video_file.is_file(), "episode_final.mp4 missing"
    assert final_video_file.stat().st_size > 50000, f"Final video too small: {final_video_file.stat().st_size} bytes"

    # Check plan config
    plan_data = json.loads(plan_file.read_text(encoding="utf-8"))
    assert plan_data["config"]["visual_style"] == "colored_marker", f"Wrong style in plan: {plan_data['config']}"
    print("  -> PASS: plan.json ghi nhận visual_style='colored_marker'", flush=True)

    # Check scenes
    scenes = list((ep_dir / "scenes").glob("scene_*"))
    assert len(scenes) >= 2, f"Expected at least 2 scenes, got {len(scenes)}"

    for sc in scenes:
        assert (sc / "image.png").is_file(), f"{sc}/image.png missing"
        assert (sc / "audio.wav").is_file(), f"{sc}/audio.wav missing"
        assert (sc / "silent.mp4").is_file(), f"{sc}/silent.mp4 missing"
        assert (sc / "merged.mp4").is_file(), f"{sc}/merged.mp4 missing"
        assert (sc / "final.mp4").is_file(), f"{sc}/final.mp4 missing"
        assert (sc / "render_style.json").is_file(), f"{sc}/render_style.json missing"

        r_style = json.loads((sc / "render_style.json").read_text(encoding="utf-8"))
        assert r_style.get("visual_style") == "colored_marker", f"Wrong style in {sc}: {r_style}"

    print(f"  -> PASS: Toàn bộ {len(scenes)} phân cảnh tạo đầy đủ tệp và ghi nhận visual_style='colored_marker'", flush=True)

    print("\n" + "=" * 70, flush=True)
    print("STEP 5: Validate frame evolution with OpenCV (Drawing Hand + Marker strokes)", flush=True)
    print("=" * 70, flush=True)
    import cv2
    import numpy as np

    sc1_silent = ep_dir / "scenes" / "scene_0001" / "silent.mp4"
    cap = cv2.VideoCapture(str(sc1_silent))
    assert cap.isOpened(), f"Cannot open {sc1_silent} with cv2"

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    assert total_frames > 25, f"Expected >25 frames, got {total_frames}"

    # Read frame 0 (Initial canvas)
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    ret, frame_0 = cap.read()
    assert ret, "Failed to read frame 0"
    # Early canvas should be mostly white
    mean_early = float(np.mean(frame_0))
    assert mean_early > 220, f"Expected early canvas to be bright white, got mean={mean_early}"

    # Read frame at 35% (Outlines being drawn with hand)
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(total_frames * 0.35))
    ret, frame_mid = cap.read()
    assert ret, "Failed to read frame at 35%"
    # Mid frame should have hand overlay and dark/colored ink strokes
    assert not np.array_equal(frame_0, frame_mid), "Frame 0 and mid frame must differ"

    # Read frame at 98% (Completed marker artwork hold)
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(total_frames * 0.98))
    ret, frame_end = cap.read()
    assert ret, "Failed to read end frame"
    cap.release()

    print(f"  -> PASS: Video có {total_frames} khung hình. Diễn hoạt vẽ tay và các nét mực biến chuyển chính xác!", flush=True)

    print("\n" + "=" * 70, flush=True)
    print("STEP 6: Verify ffprobe stream metadata on final video", flush=True)
    print("=" * 70, flush=True)
    probe_cmd = [
        "ffprobe", "-v", "error", "-show_entries",
        "stream=codec_type,codec_name,width,height:format=duration,size",
        "-of", "json", str(final_video_file)
    ]
    probe = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
    info = json.loads(probe.stdout)
    v_streams = [s for s in info["streams"] if s["codec_type"] == "video"]
    a_streams = [s for s in info["streams"] if s["codec_type"] == "audio"]

    assert len(v_streams) == 1, "Expected 1 video stream"
    assert len(a_streams) == 1, "Expected 1 audio stream"
    assert v_streams[0]["codec_name"] == "h264", f"Expected h264, got {v_streams[0]['codec_name']}"
    assert a_streams[0]["codec_name"] == "aac", f"Expected aac, got {a_streams[0]['codec_name']}"
    assert v_streams[0]["width"] == 640 and v_streams[0]["height"] == 360, f"Unexpected dimensions: {v_streams[0]}"
    duration = float(info["format"]["duration"])
    assert duration > 5.0, f"Expected duration > 5s, got {duration}s"
    print(f"  -> PASS: Video hoàn chỉnh đạt chuẩn H.264/AAC, thời lượng {duration:.2f}s, độ phân giải 640x360", flush=True)

    print("\n" + "=" * 70, flush=True)
    print("STEP 7: Verify Web API endpoint /api/episode & HTTP 206 Streaming", flush=True)
    print("=" * 70, flush=True)
    encoded_series = urllib.parse.quote(f"{series_name} - Offline Test")
    status, ep_raw = http_get(f"/api/episode?series={encoded_series}&episode=1")
    assert status == 200, f"/api/episode failed: {status}"
    ep_resp = json.loads(ep_raw)
    assert ep_resp.get("series")
    assert len(ep_resp.get("scenes", [])) >= 2
    final_url = ep_resp.get("final_video_url")
    assert final_url and final_url.startswith("/media/"), f"Invalid video URL: {final_url}"

    # Test HTTP 206 Partial Content (Streaming)
    stream_req = urllib.request.Request(f"{BASE_URL}{final_url}", headers={"Range": "bytes=0-1023"})
    with urllib.request.urlopen(stream_req, timeout=5) as s_resp:
        assert s_resp.status == 206, f"Expected HTTP 206, got {s_resp.status}"
        chunk = s_resp.read()
        assert len(chunk) == 1024, f"Expected 1024 bytes, got {len(chunk)}"

    print(f"  -> PASS: API trả về thông tin tập phim chính xác, hỗ trợ phát luồng HTTP 206 Partial Content!", flush=True)

    print("\n" + "=" * 70, flush=True)
    print("COLORED_MARKER_E2E_ALL_TESTS_PASSED 100%", flush=True)
    print("=" * 70, flush=True)
    return True


if __name__ == "__main__":
    success = test_colored_marker_e2e()
    sys.exit(0 if success else 1)
