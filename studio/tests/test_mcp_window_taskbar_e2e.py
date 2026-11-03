"""End-to-End (E2E) Test Suite: Chrome Taskbar Minimization in Storyboard Studio.

Verifies:
1. Web UI static contract (DOM elements in index.html & app.js).
2. Live HTTP API /api/mcp/window controls (status, minimize, restore, toggle).
3. Production launch window minimization and async locking.
4. Physical Windows OS window state (IsIconic) for the active Chrome process.
"""
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

STUDIO_DIR = Path(__file__).resolve().parent
if str(STUDIO_DIR) not in sys.path:
    sys.path.insert(0, str(STUDIO_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BASE_URL = "http://127.0.0.1:8765"


def test_e2e_web_ui_contracts():
    print("\n[E2E 1/4] Kiểm tra giao diện Web & Logic Javascript...")
    # 1. Check index.html served over HTTP
    req = urllib.request.Request(f"{BASE_URL}/", headers={"User-Agent": "StudioE2E/1.0"})
    with urllib.request.urlopen(req, timeout=5) as resp:
        assert resp.status == 200
        html = resp.read().decode("utf-8")
        assert 'id="inMcpAutoMinimize"' in html, "Thiếu checkbox inMcpAutoMinimize trong HTML"
        assert 'id="btnMcpToggleWindow"' in html, "Thiếu nút btnMcpToggleWindow trong HTML"
        assert 'checked' in html[html.find('id="inMcpAutoMinimize"')-20:html.find('id="inMcpAutoMinimize"')+50], "Checkbox inMcpAutoMinimize phải có thuộc tính checked mặc định"
        print("  -> index.html: Có checkbox inMcpAutoMinimize (mặc định checked) và nút btnMcpToggleWindow.")

    # 2. Check app.js served over HTTP
    req_js = urllib.request.Request(f"{BASE_URL}/app.js", headers={"User-Agent": "StudioE2E/1.0"})
    with urllib.request.urlopen(req_js, timeout=5) as resp:
        assert resp.status == 200
        js = resp.read().decode("utf-8")
        assert 'savedAutoMin !== "false"' in js, "app.js phải khôi phục giá trị mặc định là true"
        assert 'auto_minimize_browser: el.inMcpAutoMinimize ? Boolean(el.inMcpAutoMinimize.checked) : true' in js, "app.js payload phải fallback về true"
        print("  -> app.js: Logic lưu cấu hình và payload sản xuất luôn mặc định true.")
    print("  -> PASS [1/4]: Giao diện Web đã đồng bộ 100%.")


def test_e2e_http_window_api():
    print("\n[E2E 2/4] Kiểm tra REST API điều khiển cửa sổ (/api/mcp/window)...")
    
    def call_window_api(action):
        data = json.dumps({"action": action}).encode("utf-8")
        req = urllib.request.Request(
            f"{BASE_URL}/api/mcp/window",
            data=data,
            headers={"Content-Type": "application/json", "Origin": BASE_URL},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))

    # 1. Status
    res_status = call_window_api("status")
    assert res_status.get("ok") is True, f"API status failed: {res_status}"
    print(f"  -> Trạng thái ban đầu: minimized={res_status.get('minimized')}, pid={res_status.get('pid')}")

    # 2. Restore (mở to để kiểm tra tính năng mở lại)
    res_restore = call_window_api("restore")
    assert res_restore.get("ok") is True, f"API restore failed: {res_restore}"
    assert res_restore.get("minimized") is False, "Cửa sổ phải ở trạng thái mở"
    print("  -> Lệnh 'restore': Cửa sổ Chrome mở to thành công trên màn hình.")
    time.sleep(0.5)

    # 3. Minimize (thu nhỏ xuống Taskbar)
    res_min = call_window_api("minimize")
    assert res_min.get("ok") is True, f"API minimize failed: {res_min}"
    assert res_min.get("minimized") is True, "Cửa sổ phải ở trạng thái thu nhỏ Taskbar"
    print("  -> Lệnh 'minimize': Cửa sổ Chrome đã thu nhỏ xuống Taskbar thành công.")
    time.sleep(0.5)

    # 4. Toggle
    res_toggle1 = call_window_api("toggle")
    assert res_toggle1.get("ok") is True
    print(f"  -> Lệnh 'toggle' lần 1: minimized={res_toggle1.get('minimized')}")
    time.sleep(0.5)

    res_toggle2 = call_window_api("toggle")
    assert res_toggle2.get("ok") is True
    assert res_toggle2.get("minimized") is True, "Sau 2 lần toggle từ minimize thì phải quay về minimized"
    print("  -> Lệnh 'toggle' lần 2: Đã đưa cửa sổ trở lại Taskbar an toàn.")
    print("  -> PASS [2/4]: REST API /api/mcp/window hoạt động hoàn hảo 100%.")


def test_e2e_production_launch_and_locking():
    print("\n[E2E 3/4] Kiểm tra hàm thu nhỏ tự động và khóa ngầm (Lock Minimized Async)...")
    import studio_flow_accounts as sf
    import ctypes

    row = sf.active()
    pid = sf.base._pid_browser_for_account(row)
    assert pid, "Không tìm thấy tiến trình Chrome đang hoạt động"

    # Test minimize_active_account_browser
    success = sf.minimize_active_account_browser()
    assert success is True, "minimize_active_account_browser thất bại"
    print(f"  -> Đã kích hoạt minimize_active_account_browser() cho PID {pid}.")

    # Kiểm tra trạng thái ngay lập tức
    assert sf.is_chrome_minimized(pid) is True, "Chrome phải đang ở trạng thái thu nhỏ"

    # Chờ 1.5 giây để kiểm tra lock_chrome_minimized_async vẫn tiếp tục bảo vệ
    time.sleep(1.5)
    assert sf.is_chrome_minimized(pid) is True, "Chrome vẫn duy trì trạng thái thu nhỏ sau khi khóa ngầm chạy"
    print("  -> Luồng lock_chrome_minimized_async bảo vệ thành công, Chrome vẫn khóa chặt ở Taskbar.")
    print("  -> PASS [3/4]: Cơ chế tự động khóa cửa sổ khi sản xuất hoạt động ổn định.")


def test_e2e_live_os_window_verification():
    print("\n[E2E 4/4] Xác minh trạng thái thực tế của cửa sổ trên Windows OS (ctypes user32)...")
    import ctypes
    import studio_flow_accounts as sf

    user32 = ctypes.windll.user32
    row = sf.active()
    pid = sf.base._pid_browser_for_account(row)
    hwnds = sf._chrome_hwnds_for_pid(pid)
    assert len(hwnds) > 0, "Không tìm thấy HWND của Chrome"

    main_hwnd = hwnds[0]
    is_iconic = user32.IsIconic(main_hwnd)
    is_visible = user32.IsWindowVisible(main_hwnd)

    print(f"  -> Chrome PID: {pid}")
    print(f"  -> Chrome HWND: {main_hwnd}")
    print(f"  -> IsIconic (1 = Thu nhỏ thanh Taskbar): {is_iconic}")
    print(f"  -> IsWindowVisible: {is_visible}")

    assert is_iconic == 1, f"LỖI: Cửa sổ Chrome HWND {main_hwnd} không ở trạng thái thu nhỏ Taskbar (IsIconic={is_iconic})!"
    print("  -> XÁC NHẬN: Cửa sổ Chrome trên màn hình Windows hiện ĐANG THU NHỎ HOÀN TOÀN DƯỚI TASKBAR.")
    print("  -> PASS [4/4]: Xác minh hệ điều hành thành công 100%.")


if __name__ == "__main__":
    print("=" * 70)
    print("🚀 BẮT ĐẦU KIỂM THỬ TOÀN DIỆN E2E: TỰ ĐỘNG THU NHỎ CHROME XUỐNG TASKBAR")
    print("=" * 70)
    test_e2e_web_ui_contracts()
    test_e2e_http_window_api()
    test_e2e_production_launch_and_locking()
    test_e2e_live_os_window_verification()
    print("\n" + "=" * 70)
    print("🎉 TOÀN BỘ 4/4 BÀI KIỂM THỬ E2E ĐÃ HOÀN TẤT VÀ VƯỢT QUA 100% THÀNH CÔNG!")
    print("=" * 70)
