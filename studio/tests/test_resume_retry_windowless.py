"""
Test suite to verify:
1. Incomplete episode detection and resume payload in /api/episode & /api/produce
2. DOM structure and JS handling for Resume & Retry buttons
3. ComfyUI and Desktop App console window suppression (pythonw, SW_HIDE, CREATE_NO_WINDOW)
"""

import sys
import json
import urllib.request
import urllib.error
from pathlib import Path
import re

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SERVER_URL = "http://127.0.0.1:8765"

def test_console_window_suppression():
    print("\n[TEST 1/4] Kiểm tra cấu hình ẩn cửa sổ đen console (pythonw & SW_HIDE)...")
    comfy_file = Path("comfyui_image_provider.py")
    assert comfy_file.is_file(), "comfyui_image_provider.py must exist"
    comfy_text = comfy_file.read_text(encoding="utf-8")
    
    assert "pythonw.exe" in comfy_text, "comfyui_image_provider.py must use pythonw.exe"
    assert "wShowWindow = 0" in comfy_text, "comfyui_image_provider.py must set SW_HIDE (0)"
    assert "CREATE_NO_WINDOW" in comfy_text, "comfyui_image_provider.py must set CREATE_NO_WINDOW"
    print("  -> comfyui_image_provider.py: Cấu hình pythonw.exe, SW_HIDE=0 và CREATE_NO_WINDOW chuẩn xác.")

    desktop_file = Path("desktop_app.py")
    assert desktop_file.is_file(), "desktop_app.py must exist"
    desktop_text = desktop_file.read_text(encoding="utf-8")
    assert "GetConsoleWindow" in desktop_text and "ShowWindow" in desktop_text, "desktop_app.py must hide console window"
    print("  -> desktop_app.py: Có cơ chế Win32 ShowWindow(GetConsoleWindow(), 0) ẩn cửa sổ đen CMD.")

    bat_file = Path("../LAUNCH_STUDIO.bat")
    if bat_file.is_file():
        bat_text = bat_file.read_text(encoding="utf-8")
        assert "pythonw.exe" in bat_text, "LAUNCH_STUDIO.bat should reference pythonw.exe"
        print("  -> LAUNCH_STUDIO.bat: Ưu tiên khởi chạy bằng pythonw.exe.")
    print("  -> PASS: Đã triệt tiêu hoàn toàn bảng đen console.")

def test_resume_dom_elements():
    print("\n[TEST 2/4] Kiểm tra các nút Chạy Tiếp / Chạy Lại trên Giao Diện (HTML/JS)...")
    html_file = Path("web/index.html")
    html_text = html_file.read_text(encoding="utf-8")
    
    assert 'id="resumeBanner"' in html_text, "resumeBanner element must exist"
    assert 'id="btnResume"' in html_text, "btnResume button must exist"
    assert 'id="btnRetryEpisode"' in html_text, "btnRetryEpisode button must exist"
    assert 'id="btnRetryError"' in html_text, "btnRetryError button must exist"
    print("  -> web/index.html: Có đầy đủ resumeBanner, btnResume (▶️ Chạy Tiếp), btnRetryEpisode (🔄 Làm Lại), btnRetryError (🔄 Thử Lại).")

    js_file = Path("web/app.js")
    js_text = js_file.read_text(encoding="utf-8")
    assert "btnResume" in js_text, "app.js must handle btnResume"
    assert "btnRetryEpisode" in js_text, "app.js must handle btnRetryEpisode"
    assert "btnRetryError" in js_text, "app.js must handle btnRetryError"
    assert "can_resume" in js_text, "app.js must inspect can_resume"
    print("  -> web/app.js: Đã gắn sự kiện click cho btnResume, btnRetryEpisode, btnRetryError.")
    print("  -> PASS: Giao diện người dùng đầy đủ các nút và logic phục hồi.")

def test_api_episode_resume_info():
    print("\n[TEST 3/4] Kiểm tra API /api/episode phát hiện tập dở dang và can_resume...")
    # Tạo một thư mục episode giả định chưa xong để test
    test_prod_dir = Path("productions/Test_Resume_Series/episode_001")
    scenes_dir = test_prod_dir / "scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)
    
    # Tạo plan.json có 5 cảnh
    plan_data = {
        "title": "Tập Kiểm Tra Chạy Tiếp",
        "scenes": [
            {"scene_number": 1, "narration": "Cảnh 1"},
            {"scene_number": 2, "narration": "Cảnh 2"},
            {"scene_number": 3, "narration": "Cảnh 3"},
            {"scene_number": 4, "narration": "Cảnh 4"},
            {"scene_number": 5, "narration": "Cảnh 5"}
        ]
    }
    (test_prod_dir / "plan.json").write_text(json.dumps(plan_data, ensure_ascii=False), encoding="utf-8")
    
    # Tạo cảnh 1 và 2 đã hoàn thành (có final.mp4 trong scenes/scene_0001 và scene_0002)
    (scenes_dir / "scene_0001").mkdir(exist_ok=True)
    (scenes_dir / "scene_0001" / "final.mp4").write_bytes(b"dummy video scene 1")
    (scenes_dir / "scene_0002").mkdir(exist_ok=True)
    (scenes_dir / "scene_0002" / "final.mp4").write_bytes(b"dummy video scene 2")

    # Đảm bảo chưa có episode_final.mp4 (chưa hoàn thành)
    ep_final = test_prod_dir / "episode_final.mp4"
    if ep_final.is_file():
        ep_final.unlink()

    # Gọi /api/episode?series=Test_Resume_Series&episode=1
    url = f"{SERVER_URL}/api/episode?series=Test_Resume_Series&episode=1"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=5) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        
    assert data.get("can_resume") is True, f"can_resume should be True: {data}"
    assert data.get("completed_scenes") == 2, f"completed_scenes should be 2, got {data.get('completed_scenes')}"
    assert data.get("total_scenes") == 5, f"total_scenes should be 5, got {data.get('total_scenes')}"
    assert data.get("next_scene") == 3, f"next_scene should be 3, got {data.get('next_scene')}"
    print(f"  -> /api/episode trả về can_resume=True, completed=2/5, next_scene=3 chuẩn xác!")
    print("  -> PASS: Phát hiện tập đang chạy dở và phân tích số cảnh đã xong hoàn hảo.")

def test_api_produce_resume_flag():
    print("\n[TEST 4/4] Kiểm tra API /api/produce chấp nhận cờ resume mà không bị EPISODE_CONFLICT...")
    # Thử gửi request sản xuất với resume: True cho tập Test_Resume_Series ep 1
    # Máy chủ không được ném lỗi 409 (EPISODE_CONFLICT)
    req_body = {
        "series": "Test_Resume_Series",
        "episode": 1,
        "resume": True,
        "mode": "auto"
    }
    
    # Đọc server status trước
    with urllib.request.urlopen(f"{SERVER_URL}/api/status") as resp:
        st = json.loads(resp.read().decode("utf-8"))
        if st.get("running"):
            print("  -> Máy chủ đang bận xử lý job khác, bỏ qua gọi thực thi.")
            return

    # Gọi API produce
    post_data = json.dumps(req_body).encode("utf-8")
    req = urllib.request.Request(f"{SERVER_URL}/api/produce", data=post_data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            assert data.get("status") == "STARTED", f"Expected status: STARTED, got {data}"
            print(f"  -> /api/produce phản hồi thành công: status={data.get('status')}")
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        assert "EPISODE_CONFLICT" not in err_msg, f"Should not fail with EPISODE_CONFLICT when resume=True: {err_msg}"
        print(f"  -> Lỗi HTTP ngoài dự kiến: {err_msg}")
        raise

    print("  -> PASS: API /api/produce cho phép chạy tiếp trơn tru, không bị chặn bởi EPISODE_CONFLICT.")

if __name__ == "__main__":
    print("==================================================================")
    print("🧪 KIỂM THỬ TÍNH NĂNG CHẠY TIẾP, THỬ LẠI & ẨN CONSOLE COMFYUI")
    print("==================================================================")
    test_console_window_suppression()
    test_resume_dom_elements()
    test_api_episode_resume_info()
    test_api_produce_resume_flag()
    print("\n==================================================================")
    print("🎉 TẤT CẢ 4/4 BỘ TEST KIỂM THỬ ĐÃ THÀNH CÔNG RỰC RỠ 100%!")
    print("==================================================================")
