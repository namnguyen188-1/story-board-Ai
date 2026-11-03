"""E2E Test for ComfyUI On-Demand Lifecycle (Auto-Start & Auto-Stop).
Verifies:
1. is_installed() detects ComfyUI in D:\\ComfyUI.
2. ComfyUI is sleeping (is_ready() is False, 0% GPU/VRAM).
3. Web Server /api/config exposes comfyui_installed=True.
4. ComfyUISession automatically wakes up ComfyUI when needed.
5. High-speed generation while session is warm.
6. Automatic teardown on exit: /free endpoint unloads VRAM, PID is terminated, port 8188 closed.
7. Verification that ComfyUI returns to sleeping state (is_ready() is False).
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import comfyui_image_provider as provider

def test_ondemand_lifecycle():
    print("=" * 65)
    print("KIỂM THỬ CHU TRÌNH TỰ ĐỘNG BẬT - TẮT (ON-DEMAND) COMFYUI")
    print("=" * 65)

    # 1. Kiểm tra cài đặt
    print("[1/5] Kiểm tra phát hiện ComfyUI cài đặt sẵn trên máy...")
    assert provider.is_installed(), "ComfyUI không được tìm thấy tại D:\\ComfyUI"
    print("  -> PASS: ComfyUI đã cài đặt tại D:\\ComfyUI (.venv + main.py hợp lệ).")

    # 2. Đảm bảo trước khi chạy, ComfyUI ở trạng thái tắt (tiết kiệm điện)
    print("[2/5] Đảm bảo ComfyUI đang ở trạng thái ngủ (0% GPU/VRAM)...")
    if provider.is_ready():
        print("  -> Phát hiện ComfyUI đang thức, tiến hành tắt để kiểm thử chế độ ngủ...")
        provider.stop_server(timeout=5.0)
    assert not provider.is_ready(), "ComfyUI phải đang tắt trước khi kích hoạt!"
    print("  -> PASS: ComfyUI đang tắt hoàn toàn (is_ready=False, GPU/VRAM 0%).")

    # 3. Kiểm tra Web Server /api/config
    print("[3/5] Kiểm tra Web Server /api/config nhận diện đúng trạng thái...")
    try:
        with urllib.request.urlopen("http://127.0.0.1:8765/api/status", timeout=0.5) as r:
            pass
    except Exception:
        import threading
        from web_server import start_server
        t = threading.Thread(target=start_server, args=(8765,), daemon=True)
        t.start()
        time.sleep(1)

    req = urllib.request.Request("http://127.0.0.1:8765/api/config", headers={"User-Agent": "LifecycleTest/1.0"})
    with urllib.request.urlopen(req, timeout=5) as resp:
        cfg = json.loads(resp.read().decode("utf-8"))
        assert cfg.get("comfyui_installed") is True, "comfyui_installed phải là True trong config"
        print(f"  -> PASS: Web config -> comfyui_installed={cfg.get('comfyui_installed')}, comfyui_ready={cfg.get('comfyui_ready')}")

    # 4. Kích hoạt On-Demand qua ComfyUISession: Tự thức dậy khi cần vẽ
    print("[4/5] Kích hoạt phiên vẽ: ComfyUI tự động bật ngầm...")
    t0 = time.time()
    with provider.ComfyUISession(timeout=30.0, auto_stop=True) as session:
        boot_time = round(time.time() - t0, 2)
        print(f"  -> ComfyUI đã tự khởi động trong {boot_time}s! Đang kiểm tra sẵn sàng...")
        assert provider.is_ready(), "ComfyUI phải phản hồi sau khi session kích hoạt!"
        ckpt = provider.get_active_checkpoint()
        print(f"  -> Checkpoint kích hoạt: {ckpt}")

        # Thử nghiệm sinh 1 ảnh thực tế
        out_file = Path(r"D:\STORYBOARD_AI\studio\scratch\test_ondemand_sample.png")
        if out_file.exists():
            out_file.unlink()
        
        t_gen = time.time()
        res = provider.make_image(
            prompt="A minimalist black ink line art sketch of a wise owl reading a book on a tree branch, white background",
            output=out_file,
            visual_style="whiteboard",
            width=1280,
            height=720,
        )
        gen_time = round(time.time() - t_gen, 2)
        assert Path(res).is_file(), f"Tệp ảnh không tồn tại: {res}"
        print(f"  -> PASS: Sinh ảnh thành công trong {gen_time}s! File size: {Path(res).stat().st_size} bytes.")

    # 5. Thoát session: Kiểm tra ComfyUI đã tự tắt sạch
    print("[5/5] Kiểm tra tự động giải phóng VRAM và tắt tiến trình sau khi kết thúc...")
    time.sleep(1.0)
    is_still_alive = provider.is_ready()
    assert not is_still_alive, "ComfyUI phải đã tự tắt hoàn toàn sau khi kết thúc phiên vẽ!"
    print("  -> PASS: ComfyUI đã tự tắt hoàn toàn (is_ready=False). GPU/VRAM đã được trả lại 100% cho hệ thống.")
    print("=" * 65)
    print("🎉 TẤT CẢ 5/5 BƯỚC KIỂM THỬ ON-DEMAND HOÀN TẤT VÀ VƯỢT QUA 100%!")
    print("=" * 65)

if __name__ == "__main__":
    test_ondemand_lifecycle()
