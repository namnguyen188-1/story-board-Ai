import urllib.request
import json

print("====================================================")
print(" KIỂM TRA PHÂN TÁCH TÀI KHOẢN TRONG FLOWKIT")
print("====================================================")

# 1. Google Flow Web (Port 9461)
print("\n[1] GOOGLE FLOW WEB (Cổng CDP: 9461):")
try:
    with urllib.request.urlopen("http://127.0.0.1:9461/json/version", timeout=1.5) as r:
        print("    - Trạng thái: ĐANG KẾT NỐI (ONLINE)")
    with urllib.request.urlopen("http://127.0.0.1:9461/json", timeout=1.5) as r:
        tabs = json.loads(r.read().decode("utf-8"))
        pages = [t for t in tabs if t.get("type") == "page"]
        print(f"    - Số tab mở: {len(pages)}")
        for t in pages:
            title = t.get("title", "")[:35]
            url = t.get("url", "")[:55]
            print(f"      * [{title}]: {url}")
except Exception:
    print("    - Trạng thái: CHƯA BẬT (Chạy SETUP_FLOW.cmd để mở)")

# 2. ChatGPT Web (Port 9468)
print("\n[2] CHATGPT WEB (Cổng CDP: 9468 - TÁCH BIỆT HOÀN TOÀN):")
try:
    with urllib.request.urlopen("http://127.0.0.1:9468/json/version", timeout=1.5) as r:
        print("    - Trạng thái: ĐANG KẾT NỐI (ONLINE)")
    with urllib.request.urlopen("http://127.0.0.1:9468/json", timeout=1.5) as r:
        tabs = json.loads(r.read().decode("utf-8"))
        pages = [t for t in tabs if t.get("type") == "page"]
        print(f"    - Số tab mở: {len(pages)}")
        for t in pages:
            title = t.get("title", "")[:35]
            url = t.get("url", "")[:55]
            print(f"      * [{title}]: {url}")
except Exception:
    print("    - Trạng thái: CHƯA BẬT (Chạy SETUP_CHATGPT.cmd để mở)")

print("\n====================================================")
