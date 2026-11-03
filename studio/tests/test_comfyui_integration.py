"""Integration test for ComfyUI Local Image Engine in Storyboard Studio.
Verifies:
1. ComfyUI REST API connectivity (http://127.0.0.1:8188)
2. Active SDXL Lightning checkpoint detection
3. High-speed local image generation (1280x720, 16:9, RGB)
4. Web Server /api/comfyui/status endpoint
5. Prompt styling logic for whiteboard and color film styles
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from pathlib import Path
from PIL import Image

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import comfyui_image_provider as provider

def test_comfyui_status():
    print("[1/4] Kiểm tra trạng thái ComfyUI API...")
    assert provider.is_ready(), "ComfyUI không phản hồi tại http://127.0.0.1:8188"
    ckpt = provider.get_active_checkpoint()
    assert ckpt in provider.PREFERRED_CHECKPOINTS, f"Checkpoint không mong muốn: {ckpt}"
    print(f"  -> PASS: ComfyUI sẵn sàng, Checkpoint hoạt động: {ckpt}")

def test_prompt_styling():
    print("[2/4] Kiểm tra tiền xử lý prompt theo thể loại và phong cách...")
    pos_wb, neg_wb = provider.build_prompts("một chú mèo chơi piano", visual_style="whiteboard")
    assert "whiteboard" in pos_wb and "clean pure white background" in pos_wb
    assert "color" in neg_wb and "shading" in neg_wb

    pos_col, neg_col = provider.build_prompts("thành phố cyberpunk về đêm", visual_style="color_cinematic", genre="sci_fi")
    assert "cinematic film shot" in pos_col and "sci_fi" in pos_col
    print("  -> PASS: Tiền xử lý prompt hoạt động chính xác cho cả bảng trắng lẫn phim màu.")

def test_image_generation():
    print("[3/4] Kiểm tra tạo ảnh thực tế qua ComfyUI (1280x720 HD)...")
    out_dir = Path(r"D:\STORYBOARD_AI\studio\scratch")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "test_comfy_e2e_image.png"
    if out_file.exists():
        out_file.unlink()

    t0 = time.time()
    result = provider.make_image(
        prompt="A cute cartoon robot explorer on a futuristic space station, friendly character",
        output=out_file,
        visual_style="whiteboard",
        width=1280,
        height=720,
    )
    elapsed = round(time.time() - t0, 2)
    assert Path(result).is_file(), f"Tệp ảnh không tồn tại: {result}"
    
    with Image.open(result) as img:
        assert img.size == (1280, 720), f"Sai kích thước ảnh: {img.size}"
        assert img.mode == "RGB", f"Sai chế độ màu: {img.mode}"
    
    file_size_kb = round(Path(result).stat().st_size / 1024, 1)
    print(f"  -> PASS: Tạo ảnh thành công trong {elapsed}s! Kích thước: 1280x720 RGB, dung lượng: {file_size_kb} KB")

def test_web_endpoint():
    print("[4/4] Kiểm tra Web Server REST API /api/comfyui/status...")
    url = "http://127.0.0.1:8765/api/comfyui/status"
    req = urllib.request.Request(url, headers={"User-Agent": "StudioTest/1.0"})
    with urllib.request.urlopen(req, timeout=5) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data.get("ready") is True
        assert data.get("checkpoint")
        print(f"  -> PASS: Web API phản hồi 200 OK -> ready={data['ready']}, model={data['checkpoint']}")

def main():
    print("=" * 60)
    print("KIỂM THỬ TÍCH HỢP COMFYUI LOCAL CHO STORYBOARD STUDIO")
    print("=" * 60)
    test_comfyui_status()
    test_prompt_styling()
    test_image_generation()
    test_web_endpoint()
    print("=" * 60)
    print("🎉 TẤT CẢ 4/4 BƯỚC KIỂM THỬ COMFYUI ĐỀU VƯỢT QUA 100%!")
    print("=" * 60)

if __name__ == "__main__":
    main()
