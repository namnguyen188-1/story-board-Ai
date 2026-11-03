"""Tool tự động nạp và phân bổ danh sách Proxy vào các tài khoản Muse AI.
Đọc từ studio/proxies.txt và tự động gán chính xác từng proxy cho từng tài khoản.
"""
from __future__ import annotations
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

STUDIO_DIR = Path(__file__).resolve().parent
if str(STUDIO_DIR) not in sys.path:
    sys.path.insert(0, str(STUDIO_DIR))

import muse_accounts

def main():
    proxy_file = STUDIO_DIR / "proxies.txt"
    print("=======================================================")
    print("🌐 CÔNG CỤ TỰ ĐỘNG GÁN PROXY VÀO TÀI KHOẢN MUSE AI")
    print(f"   Tệp cấu hình: {proxy_file}")
    print("=======================================================\n")

    if not proxy_file.is_file():
        print(f"❌ Không tìm thấy tệp {proxy_file.name}. Vui lòng tạo tệp và dán danh sách proxy.")
        sys.exit(1)

    lines = [line.strip() for line in proxy_file.read_text(encoding="utf-8", errors="replace").splitlines()]
    valid_proxies = [l for l in lines if l and not l.startswith("#")]

    if not valid_proxies:
        print("⚠️ Tệp proxies.txt hiện chưa có dòng proxy hợp lệ nào (chỉ có dòng ghi chú #).")
        print("👉 Hãy mở tệp studio/proxies.txt, dán danh sách proxy vào và chạy lại script này.")
        sys.exit(0)

    try:
        res = muse_accounts.import_proxies_from_file(proxy_file)
        print(f"✅ {res['message']}\n")
        print("--- DANH SÁCH PHÂN BỔ THỰC TẾ ---")
        for m in res.get("mapping", []):
            clean_ip = m['proxy'].split('@')[-1]
            print(f"  👤 {m['account_name']:28s} (ID: {m['account_id']}) ➔ Proxy: {clean_ip}")
        print("\n🎉 Tất cả tài khoản đã được gán Proxy riêng biệt thành công!")
        print("   Khi mở đăng nhập hoặc render video, từng tài khoản sẽ chạy độc lập qua IP này.")
    except Exception as exc:
        print(f"❌ Có lỗi khi gán proxy: {exc}")
        sys.exit(1)

if __name__ == "__main__":
    main()
