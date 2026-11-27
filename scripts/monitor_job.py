import urllib.request
import json
import time
import sys

URL = "http://127.0.0.1:8765/api/status"

print("[MONITOR] Đang túc trực chờ tiến trình sản xuất bắt đầu...", flush=True)

# Wait up to 2 hours (2400 iterations * 3s = 7200s)
job_started = False
for i in range(2400):
    try:
        with urllib.request.urlopen(URL, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("running"):
                job_started = True
                print(f"[MONITOR] BẮT ĐẦU SẢN XUẤT: {data.get('series')} - Tập {data.get('episode')}", flush=True)
                break
    except Exception:
        pass
    time.sleep(3)

if not job_started:
    print("[MONITOR] Hết thời gian chờ (2 tiếng).", flush=True)
    sys.exit(0)

last_stage = None
last_percent = -1
last_scene = -1

while True:
    time.sleep(3)
    try:
        with urllib.request.urlopen(URL, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[MONITOR_WARN] Không kết nối được server tạm thời: {e}", flush=True)
        continue

    running = data.get("running", False)
    stage = data.get("stage", "UNKNOWN")
    percent = data.get("percent", 0)
    current_scene = data.get("current_scene", 0)
    total_scenes = data.get("total_scenes", 0)
    msg = data.get("message", "")
    exit_code = data.get("exit_code")

    if stage != last_stage or percent != last_percent or current_scene != last_scene:
        print(f"[TIẾN ĐỘ] {percent}% | Giai đoạn: {stage} | Cảnh: {current_scene}/{total_scenes} | Thông báo: {msg}", flush=True)
        last_stage = stage
        last_percent = percent
        last_scene = current_scene

    if not running:
        if exit_code == 0 or (percent >= 100 and data.get("final_video_url")):
            print(f"[MONITOR_SUCCESS] 🎉 Sản xuất hoàn tất 100%! Video: {data.get('final_video_url')}", flush=True)
        else:
            print(f"[MONITOR_FINISHED] Tiến trình kết thúc. Exit code: {exit_code}, Message: {msg}", flush=True)
        break
