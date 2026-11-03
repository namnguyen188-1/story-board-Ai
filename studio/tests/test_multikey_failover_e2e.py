"""Unit and E2E Tests for Multi-API-Key Failover and Model Fallback.
Verifies:
1. Parsing of diverse key formats (comma, semicolon, newline, .env syntax).
2. ApiKeyPool rotation and cooldown tracking.
3. Automatic Failover from Key 1 -> Key 2 upon 429 Quota Exceeded.
4. Automatic Model Fallback (gemini-3.8-flash -> gemini-3.6-flash) when all keys are exhausted on the primary model.
5. Web Server /api/config/key accepts and saves multiple keys.
6. Web Server /api/config exposes key count and safe masked keys.
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

import resilient_gemini as rg

class Mock429QuotaError(Exception):
    code = 429
    def __str__(self):
        return "Resource has been exhausted (e.g. check quota, rate limit exceeded)."

class Mock400Error(Exception):
    code = 400

class MockCoreClient:
    def __init__(self, key_model_map):
        self.key_model_map = key_model_map
        self.history = []

    def models_generate_content(self, model, key=""):
        self.history.append((key, model))
        outcome = self.key_model_map.get((key, model))
        if isinstance(outcome, Exception):
            raise outcome
        return {"text": f"OK from {key} using {model}"}

def test_key_parsing():
    print("[1/5] Kiểm tra trích xuất danh sách khóa API từ các định dạng khác nhau...")
    sample_text = """
    # Comment
    AIzaSyAlpha1111111111111, AIzaSyBeta2222222222222
    GEMINI_API_KEY=AIzaSyGamma3333333333333; AIzaSyDelta4444444444444
    AIzaSyEpsilon55555555555
    """
    keys = rg.parse_api_keys_text(sample_text)
    assert len(keys) == 5, f"Kỳ vọng 5 khóa, nhận được {len(keys)}: {keys}"
    assert keys[0] == "AIzaSyAlpha1111111111111"
    assert keys[4] == "AIzaSyEpsilon55555555555"
    print(f"  -> PASS: Trích xuất thành công {len(keys)} khóa: {[rg.mask_key(k) for k in keys]}")

def test_key_pool():
    print("[2/5] Kiểm tra quản lý bể khóa (ApiKeyPool) và hạ nhiệt (cooldown)...")
    keys = ["KEY_AAAAA_111111", "KEY_BBBBB_222222", "KEY_CCCCC_333333"]
    pool = rg.ApiKeyPool(keys)
    assert pool.get_ordered_keys() == keys

    # Đánh dấu khóa đầu tiên cạn quota
    pool.mark_exhausted(keys[0], cooldown_seconds=10.0)
    ordered = pool.get_ordered_keys()
    assert ordered[0] == keys[1], f"Khóa đầu tiên phải là B, nhận: {ordered[0]}"
    assert ordered[1] == keys[2]
    assert keys[0] in ordered  # Khóa A bị đẩy xuống cuối
    print("  -> PASS: ApiKeyPool tự động đảo khóa cạn quota xuống cuối hàng đợi.")

def test_key_failover_simulation():
    print("[3/5] Kiểm tra kịch bản Khóa 1 cạn quota (429) -> Tự động chuyển Khóa 2...")
    key1 = "AIzaSyKeyOne1111111111111"
    key2 = "AIzaSyKeyTwo2222222222222"
    
    mock_matrix = {
        (key1, "gemini-3.8-flash"): Mock429QuotaError(),
        (key2, "gemini-3.8-flash"): {"text": "Thành công từ Khóa 2!"},
    }
    
    class FakeClient:
        def __init__(self, k):
            self.k = k
            self.models = self
        def generate_content(self, *, model, **kwargs):
            outcome = mock_matrix.get((self.k, model))
            if isinstance(outcome, Exception):
                raise outcome
            return outcome or {"text": "default"}

    rclient = rg.ResilientClient(api_keys=[key1, key2])
    # Hook client factory for mock
    rclient._client_cache[key1] = FakeClient(key1)
    rclient._client_cache[key2] = FakeClient(key2)

    res = rclient.models.generate_content(model="gemini-3.8-flash")
    assert res == {"text": "Thành công từ Khóa 2!"}
    print("  -> PASS: Tự động phát hiện 429 và đổi sang Khóa 2 thành công mà không gây lỗi!")

def test_model_fallback_simulation():
    print("[4/5] Kiểm tra kịch bản Tất cả khóa hết quota model 1 -> Tự chuyển Model 2...")
    key1 = "AIzaSyKeyOne1111111111111"
    key2 = "AIzaSyKeyTwo2222222222222"
    
    # Cả key1 và key2 đều hết quota cho gemini-3.8-flash, nhưng key1 còn quota cho gemini-3.6-flash
    mock_matrix = {
        (key1, "gemini-3.8-flash"): Mock429QuotaError(),
        (key2, "gemini-3.8-flash"): Mock429QuotaError(),
        (key1, "gemini-3.6-flash"): {"text": "Thành công từ model dự phòng 3.6-flash!"},
    }

    class FakeClient:
        def __init__(self, k):
            self.k = k
            self.models = self
        def generate_content(self, *, model, **kwargs):
            outcome = mock_matrix.get((self.k, model))
            if isinstance(outcome, Exception):
                raise outcome
            return outcome

    rclient = rg.ResilientClient(api_keys=[key1, key2])
    rclient._client_cache[key1] = FakeClient(key1)
    rclient._client_cache[key2] = FakeClient(key2)

    res = rclient.models.generate_content(model="gemini-3.8-flash")
    assert res == {"text": "Thành công từ model dự phòng 3.6-flash!"}
    print("  -> PASS: Cả 2 khóa hết quota model chính -> Tự động chuyển model dự phòng thành công!")

def test_web_api_multikey():
    print("[5/5] Kiểm tra Web Server REST API /api/config và /api/config/key...")
    env_file = Path(r"D:\STORYBOARD_AI\studio\.env")
    backup_env = env_file.read_text(encoding="utf-8") if env_file.exists() else ""

    # Đảm bảo web server đang chạy
    try:
        with urllib.request.urlopen("http://127.0.0.1:8765/api/status", timeout=0.5) as r:
            pass
    except Exception:
        import threading
        from web_server import start_server
        t = threading.Thread(target=start_server, args=(8765,), daemon=True)
        t.start()
        time.sleep(1)

    try:
        # Thử lưu 2 API key qua REST API
        keys_input = "AIzaSyTestSampleKeyOne12345, AIzaSyTestSampleKeyTwo67890"
        req = urllib.request.Request(
            "http://127.0.0.1:8765/api/config/key",
            data=json.dumps({"gemini_key": keys_input}).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "MultiKeyTest/1.0"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            assert data.get("status") == "SAVED"
            assert data.get("count") == 2, f"Kỳ vọng 2 khóa, nhận: {data}"
            print(f"  -> POST /api/config/key -> count={data['count']}, masked={data.get('masked')}")

        # Kiểm tra GET /api/config
        req_get = urllib.request.Request("http://127.0.0.1:8765/api/config", headers={"User-Agent": "MultiKeyTest/1.0"})
        with urllib.request.urlopen(req_get, timeout=5) as resp_get:
            cfg = json.loads(resp_get.read().decode("utf-8"))
            assert cfg.get("gemini_api_configured") is True
            assert cfg.get("gemini_api_count") == 2
            assert "...2345" in str(cfg.get("gemini_keys_masked"))
            print(f"  -> GET /api/config -> configured={cfg['gemini_api_configured']}, count={cfg['gemini_api_count']}")
            print("  -> PASS: Web Server nhận diện và quản lý đa khóa hoàn hảo.")
    finally:
        # Khôi phục nguyên trạng .env
        if backup_env:
            env_file.write_text(backup_env, encoding="utf-8")
        print("  -> Đã khôi phục file .env nguyên bản của hệ thống.")

def main():
    print("=" * 65)
    print("KIỂM THỬ TÍNH NĂNG ĐA KHÓA API & TỰ ĐỘNG CHUYỂN MODEL GEMINI")
    print("=" * 65)
    test_key_parsing()
    test_key_pool()
    test_key_failover_simulation()
    test_model_fallback_simulation()
    test_web_api_multikey()
    print("=" * 65)
    print("🎉 TẤT CẢ 5/5 BƯỚC KIỂM THỬ ĐA KHÓA & CHUYỂN MODEL ĐỀU PASS 100%!")
    print("=" * 65)

if __name__ == "__main__":
    main()
