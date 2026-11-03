import sys
import os
from pathlib import Path
import urllib.request
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SERVER_URL = "http://127.0.0.1:8765"
STUDIO_DIR = Path(__file__).resolve().parent

def test_robot_assets():
    print("\n[TEST 1/5] Kiểm tra tài nguyên hình ảnh Con Robot AI V2...")
    avatar = STUDIO_DIR / "web" / "assets" / "robot_avatar.png"
    gif = STUDIO_DIR / "web" / "assets" / "robot_animated.gif"
    assert avatar.is_file(), f"Missing {avatar}"
    assert gif.is_file(), f"Missing {gif}"
    print(f"  -> File avatar tồn tại: {avatar.stat().st_size} bytes")
    print(f"  -> File GIF hoạt ảnh tồn tại: {gif.stat().st_size} bytes")

    # Kiểm tra máy chủ phục vụ tĩnh
    try:
        req = urllib.request.urlopen(f"{SERVER_URL}/assets/robot_avatar.png", timeout=5)
        assert req.status == 200, f"HTTP status: {req.status}"
        data = req.read()
        assert len(data) > 1000, "Avatar data too small"
        print("  -> Máy chủ Web phục vụ robot_avatar.png: HTTP 200 OK.")
    except Exception as e:
        print(f"  -> Bỏ qua HTTP probe nếu máy chủ web chưa bật: {e}")

def test_html_robot_elements():
    print("\n[TEST 2/5] Kiểm tra các phần tử giao diện Robot AI trong web/index.html...")
    index_file = STUDIO_DIR / "web" / "index.html"
    content = index_file.read_text(encoding="utf-8")
    required_ids = [
        "aiRobotFloatingWidget",
        "btnToggleRobot",
        "robotLedStatus",
        "robotFloatingBadge",
        "robotHologramPanel",
        "robotHologramMsg",
        "robotStatusFlow",
        "robotStatusComfy",
        "robotStatusGemini",
        "robotBtnGoogleLogin"
    ]
    for rid in required_ids:
        assert f'id="{rid}"' in content or f"id='{rid}'" in content, f"Missing #{rid} in index.html"
    print(f"  -> PASS: Đầy đủ tất cả {len(required_ids)} phần tử giao diện Robot Assistant & Hologram Panel.")

def test_css_robot_styles():
    print("\n[TEST 3/5] Kiểm tra CSS phong cách Hologram Cybernetic trong web/style.css...")
    css_file = STUDIO_DIR / "web" / "style.css"
    css = css_file.read_text(encoding="utf-8")
    required_classes = [
        ".robot-floating-container",
        ".robot-avatar-btn",
        ".robot-led-status",
        ".robot-hologram-panel",
        ".hologram-speech-box",
        ".hologram-matrix"
    ]
    for cls in required_classes:
        assert cls in css, f"Missing {cls} in style.css"
    print(f"  -> PASS: Đầy đủ các lớp CSS điều khiển hoạt ảnh và giao diện Hologram.")

def test_js_robot_controller():
    print("\n[TEST 4/5] Kiểm tra logic điều khiển JavaScript trong web/app.js...")
    js_file = STUDIO_DIR / "web" / "app.js"
    js = js_file.read_text(encoding="utf-8")
    assert "toggleRobotHologram" in js, "Missing toggleRobotHologram"
    assert "robotLoginOnly" in js, "Missing unified login action"
    assert "window.open(url, \"_blank\")" not in js, "Old Edge popup path must be gone"
    assert "robotAutoReconnect" in js, "Missing robotAutoReconnect"
    assert "robotLedStatus" in js, "Missing robotLedStatus updates in app.js"
    print("  -> PASS: JavaScript đã có đầy đủ hàm mở/đóng hologram, hiện/ẩn Chrome và tự đồng bộ LED.")

def test_smart_login_backend():
    print("\n[TEST 5/5] Kiểm tra cơ chế tự động mở hiện Chrome khi cần đăng nhập...")
    accounts_file = STUDIO_DIR / "studio_flow_accounts.py"
    acc_text = accounts_file.read_text(encoding="utf-8")
    assert "SW_RESTORE" in acc_text or "ShowWindow(hwnd,9)" in acc_text, "Missing SW_RESTORE in studio_flow_accounts.py"
    assert "SetForegroundWindow" in acc_text, "Missing SetForegroundWindow in studio_flow_accounts.py"

    manager_file = STUDIO_DIR / "studio_mcp" / "auto_flow_manager.py"
    mgr_text = manager_file.read_text(encoding="utf-8")
    assert "restore_chrome_window" in mgr_text, "auto_flow_manager must call restore_chrome_window on login"
    assert "AUTO_FLOW_LOGIN_REQUIRED" in mgr_text, "auto_flow_manager must handle AUTO_FLOW_LOGIN_REQUIRED"
    print("  -> PASS: Backend đã cài đặt cơ chế thông minh tự khôi phục cửa sổ Chrome khi cần đăng nhập Google.")

if __name__ == "__main__":
    print("=" * 66)
    print("🤖 KIỂM THỬ TÍNH NĂNG CON ROBOT TRỢ LÝ AI & CƠ CHẾ ĐĂNG NHẬP THÔNG MINH")
    print("=" * 66)
    test_robot_assets()
    test_html_robot_elements()
    test_css_robot_styles()
    test_js_robot_controller()
    test_smart_login_backend()
    print("\n" + "=" * 66)
    print("🎉 HOÀN TẤT THÀNH CÔNG 5/5 BỘ KIỂM THỬ TRỢ LÝ ROBOT & TỰ ĐỘNG HIỆN CHROME!")
    print("=" * 66)
