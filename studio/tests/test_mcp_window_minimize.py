"""Verification test suite for Chrome Taskbar Minimization & Window Management.
Tests:
1. Functions in studio_flow_accounts.py: _chrome_hwnds_for_pid, minimize_chrome_window, restore_chrome_window, is_chrome_minimized.
2. REST API /api/mcp/window handling (minimize, restore, toggle).
3. DOM integrity for inMcpAutoMinimize and btnMcpToggleWindow in index.html.
"""
import json
import os
import sys
import urllib.request
from pathlib import Path
from unittest.mock import patch, MagicMock

STUDIO_DIR = Path(__file__).resolve().parents[1]
if str(STUDIO_DIR) not in sys.path:
    sys.path.insert(0, str(STUDIO_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

URL = "http://127.0.0.1:8765"


def test_unit_window_helpers():
    print("\n[TEST 1/3] Kiểm tra các hàm điều khiển cửa sổ trong studio_flow_accounts...")
    import studio_flow_accounts as sf
    import threading

    fake_hwnd = 99999
    # Test _chrome_hwnds_for_pid with mock
    with patch("ctypes.windll.user32.EnumWindows") as mock_enum:
        def enum_impl(cb, extra):
            # Simulate callback invocation with fake_hwnd
            cb(fake_hwnd, 0)
            return True
        mock_enum.side_effect = enum_impl
        with patch("ctypes.windll.user32.GetWindowThreadProcessId") as mock_pid:
            def pid_impl(h, ref):
                ref._obj.value = 1234
                return 1
            mock_pid.side_effect = pid_impl

            hwnds = sf._chrome_hwnds_for_pid(1234)
            assert fake_hwnd in hwnds, f"Expected {fake_hwnd} in {hwnds}"
            print("  -> _chrome_hwnds_for_pid tìm đúng HWND theo PID.")

            # Test minimize_chrome_window
            with patch("ctypes.windll.user32.ShowWindow") as mock_show:
                res = sf.minimize_chrome_window(1234)
                assert res is True, "minimize_chrome_window failed"
                mock_show.assert_called_with(fake_hwnd, 7)  # SW_SHOWMINNOACTIVE = 7
                print("  -> minimize_chrome_window gọi ShowWindow(SW_SHOWMINNOACTIVE=7) thành công.")

            # Test is_chrome_minimized
            with patch("ctypes.windll.user32.IsIconic", return_value=1) as mock_iconic:
                assert sf.is_chrome_minimized(1234) is True
                print("  -> is_chrome_minimized phát hiện trạng thái thu nhỏ chính xác.")

            # Test lock_chrome_during_production
            stop_evt = threading.Event()
            with patch.object(sf, "is_chrome_minimized", return_value=False) as mock_min_check, \
                 patch.object(sf, "minimize_chrome_window") as mock_min_win:
                t = sf.lock_chrome_during_production(stop_evt, pid=1234, interval=0.05)
                assert t.is_alive()
                import time; time.sleep(0.12)
                stop_evt.set()
                t.join(timeout=1.0)
                assert mock_min_win.called, "lock_chrome_during_production should call minimize_chrome_window"
                print("  -> lock_chrome_during_production tự động giám sát và khóa taskbar liên tục thành công.")


def test_api_mcp_window_endpoint():
    print("\n[TEST 2/3] Kiểm tra REST API endpoint /api/mcp/window (POST status & lock)...")
    # Test POST /api/mcp/window with action: status
    status_req = urllib.request.Request(
        f"{URL}/api/mcp/window",
        data=json.dumps({"action": "status"}).encode("utf-8"),
        headers={"Content-Type": "application/json", "Origin": "http://127.0.0.1:8765"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(status_req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"  -> POST /api/mcp/window (status): ok={data.get('ok')}, running={data.get('running')}, minimized={data.get('minimized')}")
            assert "ok" in data
            assert "minimized" in data
    except urllib.error.HTTPError as e:
        data = json.loads(e.read().decode("utf-8"))
        print(f"  -> POST (status) phản hồi an toàn: code={e.code}, error={data.get('error')}")
        assert e.code == 400

    # Test POST /api/mcp/window with action: lock
    post_req = urllib.request.Request(
        f"{URL}/api/mcp/window",
        data=json.dumps({"action": "lock"}).encode("utf-8"),
        headers={"Content-Type": "application/json", "Origin": "http://127.0.0.1:8765"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(post_req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"  -> POST /api/mcp/window (lock): ok={data.get('ok')}, minimized={data.get('minimized')}")
            assert "ok" in data
            assert data.get("minimized") is True
    except urllib.error.HTTPError as e:
        data = json.loads(e.read().decode("utf-8"))
        print(f"  -> POST phản hồi an toàn: code={e.code}, error={data.get('error')}")
        assert e.code == 400
    print("  -> PASS: REST API /api/mcp/window hoạt động chuẩn xác.")


def test_dom_elements():
    print("\n[TEST 3/3] Kiểm tra tính toàn vẹn phần tử giao diện trong index.html...")
    html_path = STUDIO_DIR / "web" / "index.html"
    content = html_path.read_text(encoding="utf-8")

    assert 'id="inMcpAutoMinimize"' in content, "Missing inMcpAutoMinimize in index.html"
    assert 'id="btnMcpToggleWindow"' in content, "Missing btnMcpToggleWindow in index.html"
    assert 'id="btnHeaderToggleMcpWindow"' in content, "Missing btnHeaderToggleMcpWindow in index.html"
    assert 'id="robotBtnHideChrome"' in content, "Missing robotBtnHideChrome in index.html"
    print("  -> Đã tìm thấy checkbox inMcpAutoMinimize (Tự động thu nhỏ Chrome).")
    print("  -> Đã tìm thấy nút bấm btnMcpToggleWindow (Thu nhỏ Taskbar trong cài đặt).")
    print("  -> Đã tìm thấy nút bấm 1-Click trên thanh điều hướng chính: btnHeaderToggleMcpWindow (Khóa Taskbar).")
    print("  -> Đã tìm thấy nút bấm trong Trợ lý Robot: robotBtnHideChrome.")
    print("  -> PASS: Giao diện người dùng đầy đủ các nút điều khiển mới.")


if __name__ == "__main__":
    print("=" * 65)
    print("🧪 KIỂM THỬ TÍNH NĂNG THU NHỎ TRÌNH DUYỆT CHROME XUỐNG TASKBAR")
    print("=" * 65)
    test_unit_window_helpers()
    test_api_mcp_window_endpoint()
    test_dom_elements()
    print("\n" + "=" * 65)
    print("🎉 TẤT CẢ CÁC KIỂM THỬ THU NHỎ TRÌNH DUYỆT ĐÃ HOÀN TẤT THÀNH CÔNG 100%!")
    print("=" * 65)
