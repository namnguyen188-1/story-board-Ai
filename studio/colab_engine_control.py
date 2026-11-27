"""Colab Engine Controller for Storyboard AI Studio Pro.
Allows seamless switching between local NVIDIA RTX 3060 Ti and Google Colab Cloud GPU (Tesla T4).
Features self-healing SSH tunnel auto-reconnect.
"""
import sys
import os
import time
import json
import subprocess
import urllib.request
from pathlib import Path

STUDIO_DIR = Path(__file__).resolve().parent
CONFIG_PATH = STUDIO_DIR / "engine_config.json"

def get_stats(host):
    try:
        url = f"http://{host}/system_stats"
        req = urllib.request.Request(url, headers={"User-Agent": "StoryboardStudio/1.0"})
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            data = json.loads(resp.read().decode())
            devices = data.get("devices", [])
            dev_name = devices[0].get("name", "Unknown GPU") if devices else "CPU"
            vram = devices[0].get("vram_total", 0) / 1e9 if devices else 0
            return True, dev_name, vram
    except Exception:
        return False, None, 0

def load_config():
    if CONFIG_PATH.is_file():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"mode": "local", "use_colab_gpu": False, "colab_host": "127.0.0.1:8189", "local_host": "127.0.0.1:8188"}

def save_config(cfg):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

def ensure_tunnel(session_name="stoi-engine"):
    """Ensures the SSH tunnel to Colab is connected. Auto-starts if disconnected."""
    ok, _, _ = get_stats("127.0.0.1:8189")
    if ok:
        return True

    print("-> Đang tự động kết nối lại hầm bảo mật SSH tới Google Colab...", flush=True)
    colab_cli = Path.home() / ".local" / "bin" / "colab.exe"
    cli_str = str(colab_cli).replace("\\", "/")
    
    cmd = [
        "ssh", "-N", "-L", "8189:127.0.0.1:8188",
        "-o", f"ProxyCommand={cli_str} ssh --proxy-mode -s {session_name}",
        "-o", "StrictHostKeyChecking=no",
        "-o", "ServerAliveInterval=20",
        "-o", "ServerAliveCountMax=5",
        "root@colab"
    ]
    
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    subprocess.Popen(cmd, creationflags=flags)
    
    # Cho 3-4 giay de kiem tra ket noi
    for _ in range(8):
        time.sleep(1)
        ok, _, _ = get_stats("127.0.0.1:8189")
        if ok:
            print("-> Kết nối hầm Colab thành công!", flush=True)
            return True
            
    return False

def show_status():
    cfg = load_config()
    print("=" * 60)
    print("  STORYBOARD AI STUDIO PRO - DUAL ENGINE STATUS")
    print("=" * 60)
    
    local_ok, local_dev, local_vram = get_stats(cfg.get("local_host", "127.0.0.1:8188"))
    
    # Thu kiem tra va ket noi neu dang bat mode colab
    if cfg.get("use_colab_gpu", False) or cfg.get("mode") == "colab":
        colab_ok, colab_dev, colab_vram = get_stats(cfg.get("colab_host", "127.0.0.1:8189"))
        if not colab_ok:
            ensure_tunnel()
    
    colab_ok, colab_dev, colab_vram = get_stats(cfg.get("colab_host", "127.0.0.1:8189"))
    
    mode = cfg.get("mode", "local")
    use_colab = cfg.get("use_colab_gpu", False)
    
    print(f"\n[1] LOCAL GPU (Cục bộ):")
    if local_ok:
        print(f"    - Trạng thái: ONLINE")
        print(f"    - Thiết bị:   {local_dev} ({local_vram:.2f} GB)")
        print(f"    - Cổng kết nối: {cfg.get('local_host')}")
    else:
        print(f"    - Trạng thái: OFFLINE (Chưa bật ComfyUI nội bộ)")

    print(f"\n[2] CLOUD GPU (Google Colab):")
    if colab_ok:
        print(f"    - Trạng thái: ONLINE (Đang kết nối)")
        print(f"    - Thiết bị:   {colab_dev} ({colab_vram:.2f} GB VRAM)")
        print(f"    - Cổng kết nối: {cfg.get('colab_host')}")
    else:
        print(f"    - Trạng thái: OFFLINE / DISCONNECTED")

    print("\n" + "-" * 60)
    active_engine = "GOOGLE COLAB GPU (Cloud)" if (mode == "colab" and colab_ok) else "LOCAL NVIDIA GPU (Máy tính)"
    print(f"★ ĐỘNG CƠ ĐANG KÍCH HOẠT: {active_engine}")
    print("=" * 60)

def enable_colab():
    cfg = load_config()
    cfg["mode"] = "colab"
    cfg["use_colab_gpu"] = True
    save_config(cfg)
    ensure_tunnel()
    print("-> Đã KÍCH HOẠT động cơ Google Colab GPU cho Storyboard AI!")
    show_status()

def disable_colab():
    cfg = load_config()
    cfg["mode"] = "local"
    cfg["use_colab_gpu"] = False
    save_config(cfg)
    print("-> Đã CHUYỂN VỀ động cơ NVIDIA cục bộ trên máy tính!")
    show_status()

if __name__ == "__main__":
    arg = sys.argv[1].lower() if len(sys.argv) > 1 else "status"
    if arg in ("status", "info"):
        show_status()
    elif arg in ("enable", "colab", "on"):
        enable_colab()
    elif arg in ("disable", "local", "off"):
        disable_colab()
    elif arg in ("tunnel", "connect"):
        ensure_tunnel()
    else:
        print(f"Lệnh không rõ: {arg}. Dùng: status, enable, disable, tunnel")
