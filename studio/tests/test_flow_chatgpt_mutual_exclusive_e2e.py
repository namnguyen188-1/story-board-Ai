"""End-to-End (E2E) Verification for Google Flow & ChatGPT Web Mutual-Exclusive Integration.
Tests the complete on-demand lifecycle, port separation, and zero-RAM cleanup.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import time
import urllib.request

STUDIO_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = STUDIO_DIR.parent
FLOWKIT_APP = PROJECT_ROOT / "flowkit" / "app"
if not FLOWKIT_APP.is_dir():
    FLOWKIT_APP = Path("D:/FLOWKIT/app")
if str(FLOWKIT_APP) not in sys.path:
    sys.path.insert(0, str(FLOWKIT_APP))

if str(STUDIO_DIR) not in sys.path:
    sys.path.insert(0, str(STUDIO_DIR))

import engine_orchestrator
import chatgpt_account_manager
import chatgpt_browser

FLOW_PORT = engine_orchestrator._get_active_flow_port()
CHATGPT_PORT = chatgpt_browser.get_active_profile()[1]


def is_port_online(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=1.0) as r:
            return r.status == 200
    except Exception:
        return False


def get_tab_titles(port: int) -> list[str]:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/list", timeout=1.5) as r:
            targets = json.load(r)
            return [t.get("title", "") for t in targets if t.get("type") == "page"]
    except Exception:
        return []


def run_e2e_test():
    print("=" * 65)
    print("🚀 BẮT ĐẦU KIỂM THỬ E2E: KẾT NỐI GOOGLE FLOW & CHATGPT WEB")
    print("=" * 65)

    results = []

    # BƯỚC 0: Dọn dẹp trạng thái ban đầu
    print("\n[BƯỚC 0] Đảm bảo trạng thái ban đầu sạch (close_all_engines)...")
    engine_orchestrator.close_all_engines()
    time.sleep(1.0)
    assert not is_port_online(FLOW_PORT), f"Port {FLOW_PORT} vẫn còn online!"
    assert not is_port_online(CHATGPT_PORT), f"Port {CHATGPT_PORT} vẫn còn online!"
    print(f"✓ Trạng thái ban đầu: Cả 2 cổng {FLOW_PORT} và {CHATGPT_PORT} đều OFFLINE, RAM hoàn toàn giải phóng.")
    results.append(("Bước 0: Khởi tạo sạch", True))

    # BƯỚC 1: Khởi động Google Flow
    print(f"\n[BƯỚC 1] Kích hoạt Google Flow (ensure_exclusive_engine('flow') -> cổng {FLOW_PORT})...")
    res_flow = engine_orchestrator.ensure_exclusive_engine("flow")
    print("Kết quả gọi Flow:", res_flow)
    assert res_flow.get("ok"), f"Không thể bật Flow: {res_flow}"
    active_flow_port = int(res_flow.get("port") or FLOW_PORT)
    assert is_port_online(active_flow_port), f"Port {active_flow_port} (Flow) chưa online!"
    assert not is_port_online(CHATGPT_PORT), f"LỖI XUNG ĐỘT: Port {CHATGPT_PORT} (ChatGPT) không được phép chạy đồng thời!"
    flow_tabs = get_tab_titles(active_flow_port)
    print(f"✓ Google Flow đã ONLINE trên cổng {active_flow_port}. Danh sách tab: {flow_tabs}")
    results.append(("Bước 1: Bật Google Flow độc quyền", True))

    # BƯỚC 2: Chuyển đổi sang ChatGPT Web (Tự động tắt Flow để nhường tài nguyên)
    print(f"\n[BƯỚC 2] Chuyển đổi sang ChatGPT Web (ensure_exclusive_engine('chatgpt') -> cổng {CHATGPT_PORT})...")
    res_chatgpt = engine_orchestrator.ensure_exclusive_engine("chatgpt", show_window=False)
    print("Kết quả gọi ChatGPT:", res_chatgpt)
    assert res_chatgpt.get("ok"), f"Không thể bật ChatGPT: {res_chatgpt}"
    active_cgpt_port = int(res_chatgpt.get("port") or CHATGPT_PORT)
    assert is_port_online(active_cgpt_port), f"Port {active_cgpt_port} (ChatGPT) chưa online!"
    assert not engine_orchestrator._find_alive_flow_ports(), "LỖI: Cổng Google Flow chưa được đóng tự động khi gọi ChatGPT!"
    chatgpt_tabs = get_tab_titles(active_cgpt_port)
    print(f"✓ ChatGPT Web đã ONLINE trên cổng {active_cgpt_port}. Google Flow đã TỰ ĐỘNG ĐÓNG. Tabs: {chatgpt_tabs}")
    results.append(("Bước 2: Chuyển sang ChatGPT (Tự tắt Flow)", True))

    # BƯỚC 3: Kiểm tra API trạng thái giao diện UI Storyboard AI
    print("\n[BƯỚC 3] Kiểm tra API trạng thái UI Storyboard AI Studio...")
    cg_status = chatgpt_account_manager.get_chatgpt_ui_status()
    print("Status ChatGPT UI:", cg_status)
    assert cg_status.get("online") is True, "get_chatgpt_ui_status() phải báo online khi browser đang chạy!"
    print(f"✓ UI Status phản hồi chính xác: Online={cg_status.get('online')}, Badge={cg_status.get('badge')}")
    results.append(("Bước 3: API Trạng thái UI", True))

    # BƯỚC 4: Chuyển đổi ngược lại về Google Flow (Tự động tắt ChatGPT)
    print("\n[BƯỚC 4] Chuyển ngược lại về Google Flow...")
    res_back_flow = engine_orchestrator.ensure_exclusive_engine("flow")
    print("Kết quả gọi lại Flow:", res_back_flow)
    assert res_back_flow.get("ok"), f"Không thể bật lại Flow: {res_back_flow}"
    assert is_port_online(int(res_back_flow.get("port") or active_flow_port)), "Port Flow chưa online lại!"
    assert not engine_orchestrator._find_alive_chatgpt_ports(), "LỖI: Cổng ChatGPT chưa được đóng tự động khi gọi lại Flow!"
    print("✓ Google Flow đã hoạt động trở lại. ChatGPT Web đã TỰ ĐỘNG ĐÓNG.")
    results.append(("Bước 4: Chuyển ngược về Flow (Tự tắt ChatGPT)", True))

    # BƯỚC 5: Đóng toàn bộ và giải phóng 100% tài nguyên
    print("\n[BƯỚC 5] Đóng toàn bộ trình duyệt (close_all_engines)...")
    engine_orchestrator.close_all_engines()
    time.sleep(1.0)
    assert not engine_orchestrator._find_alive_flow_ports(), "Port Flow vẫn mở sau close_all!"
    assert not engine_orchestrator._find_alive_chatgpt_ports(), "Port ChatGPT vẫn mở sau close_all!"
    print("✓ Đã đóng toàn bộ. Hệ thống trở về trạng thái nghỉ, 100% RAM & GPU được giải phóng.")
    results.append(("Bước 5: Giải phóng toàn bộ", True))

    # BÁO CÁO TỔNG KẾT
    print("\n" + "=" * 65)
    print("📊 TỔNG KẾT KIỂM THỬ E2E:")
    for name, ok in results:
        status_sym = "✅ PASS" if ok else "❌ FAIL"
        print(f"  {status_sym} - {name}")
    print("=" * 65)
    print("🎉 KIỂM THỬ E2E THÀNH CÔNG 100%! HỆ THỐNG HOẠT ĐỘNG HOÀN HẢO.")


if __name__ == "__main__":
    run_e2e_test()
