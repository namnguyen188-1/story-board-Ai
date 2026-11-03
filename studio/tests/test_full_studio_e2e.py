"""Comprehensive End-to-End (E2E) Test for Storyboard Studio Pro.
Tests:
1. Static Web UI serving (HTTP 200, DOM, styles, scripts)
2. REST API endpoints (/api/config, /api/voices, /api/analyze-link, /api/mcp/accounts)
3. Link Analysis for Spanish and English videos (duration, language, region, voice matching)
4. Production Lifecycle E2E via POST /api/produce (offline mode)
5. Progress streaming and job completion via /api/status
6. Media serving and video scrubbing (HTTP 206 Partial Content)
"""
from __future__ import annotations
import sys, json, time, urllib.request, urllib.parse, urllib.error
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BASE_URL = "http://127.0.0.1:8765"
ROOT_DIR = Path(r"D:\STORYBOARD_AI\studio")

def ensure_server():
    try:
        with urllib.request.urlopen(f"{BASE_URL}/api/status", timeout=0.5) as r:
            return
    except Exception:
        import threading
        from web_server import start_server
        t = threading.Thread(target=start_server, args=(8765,), daemon=True)
        t.start()
        time.sleep(1)

def http_get(path, timeout=35):
    ensure_server()
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, headers={"User-Agent": "StudioE2E/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, resp.read().decode("utf-8")

def http_post_json(path, data, timeout=35):
    url = f"{BASE_URL}{path}"
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={
        "Content-Type": "application/json",
        "User-Agent": "StudioE2E/1.0"
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))

def test_static_ui():
    print("[E2E 1/6] Kiểm tra giao diện Web tĩnh (GET /)...", flush=True)
    status, html = http_get("/")
    assert status == 200, f"Expected 200, got {status}"
    assert "Storyboard Studio Pro" in html or "Storyboard" in html
    assert 'id="inPrompt"' in html
    assert 'id="inLanguage"' in html
    assert 'id="inRegion"' in html
    assert 'id="inVoice"' in html
    assert 'id="inGenre"' in html
    assert 'id="btnLive"' in html
    assert 'id="btnOffline"' in html
    print("  -> PASS: Giao diện Web HTML và các ID điều khiển sẵn sàng.", flush=True)

def test_api_config_and_voices():
    print("[E2E 2/6] Kiểm tra API cấu hình và danh mục giọng nói (/api/config, /api/voices)...", flush=True)
    status, raw = http_get("/api/config")
    assert status == 200
    cfg = json.loads(raw)
    assert "productions_dir" in cfg
    print(f"  -> Config status: gemini={cfg.get('gemini_api_configured')}, v2={cfg.get('v2_gateway_ready')}")

    # Check Spanish voices
    status, raw = http_get("/api/voices?region=ES")
    assert status == 200
    v_es = json.loads(raw)
    es_ids = [v[0] for v in v_es.get("curated", {}).get("male", [])] + [v[0] for v in v_es.get("curated", {}).get("female", [])]
    assert "Charon" in es_ids or "Orus" in es_ids, f"Spanish voices missing: {es_ids}"
    print(f"  -> PASS: Danh mục giọng Tây Ban Nha (ES) có {len(es_ids)} giọng chuẩn ({', '.join(es_ids)}).", flush=True)

    # Check Vietnamese voices
    status, raw = http_get("/api/voices?region=VN")
    assert status == 200
    v_vn = json.loads(raw)
    vn_ids = [v[0] for v in v_vn.get("curated", {}).get("male", [])] + [v[0] for v in v_vn.get("curated", {}).get("female", [])]
    assert "Orus" in vn_ids and "Aoede" in vn_ids and "Fenrir" in vn_ids
    print(f"  -> PASS: Danh mục giọng Việt Nam (VN) có {len(vn_ids)} giọng chuẩn ({', '.join(vn_ids)}).", flush=True)

def test_link_detection():
    print("[E2E 3/6] Kiểm tra tự động nhận diện video link (/api/analyze-link) & Clone nhân vật...", flush=True)
    
    # 1. Spanish video (Despacito)
    t0 = time.time()
    status, raw = http_get("/api/analyze-link?url=https://www.youtube.com/watch?v=kJQP7kiw5Fk", timeout=60)
    elapsed = round(time.time() - t0, 2)
    assert status == 200
    data_es = json.loads(raw)
    assert data_es["ok"] is True
    assert data_es["language"] == "Spanish", f"Expected Spanish, got {data_es['language']}"
    assert data_es["region"] in ("ES", "MX"), f"Expected ES/MX, got {data_es['region']}"
    assert 2.0 <= data_es["duration_minutes"] <= 5.5, f"Expected 2.0 - 5.5 min, got {data_es['duration_minutes']}"
    assert data_es["suggested_voice"] in ("Orus", "Charon", "Algenib", "Despina")
    assert "character" in data_es, "Character DNA should be extracted"
    print(f"  -> PASS: Video tiếng Tây Ban Nha -> {data_es['duration_minutes']} phút, {data_es['language']} ({data_es['region']}), Giọng: {data_es['suggested_voice']} (xử lý trong {elapsed}s).", flush=True)

    # 2. Stoic Clone Video (Shorts)
    t0 = time.time()
    status, raw = http_get("/api/analyze-link?url=https://youtube.com/shorts/QhZt_Lu1-jw", timeout=60)
    elapsed = round(time.time() - t0, 2)
    assert status == 200
    data_stoic = json.loads(raw)
    assert data_stoic["ok"] is True
    assert data_stoic.get("character", {}).get("character_name"), "Stoic philosopher character should be cloned"
    print(f"  -> PASS: Video Shorts Stoic -> Clone thành công: {data_stoic['character']['character_name']} ({elapsed}s).", flush=True)

def test_production_e2e():
    print("[E2E 4/6] Khởi chạy sản xuất phim tự động E2E qua POST /api/produce (offline mode)...", flush=True)
    payload = {
        "mode": "offline",
        "series": "Studio E2E Full Auto Test",
        "episode": 1,
        "prompt": "Hành trình thám hiểm vũ trụ và khám phá hành tinh mới trong tương lai.",
        "input_mode": "idea",
        "language": "Vietnamese",
        "region": "VN",
        "voice_name": "Orus",
        "genre": "documentary",
        "visual_style": "color_cinematic",
        "subtitle_style": "karaoke_viral",
        "subtitle_size": 52,
    }

    status, resp = http_post_json("/api/produce", payload)
    assert status == 200, f"Produce failed: {status} -> {resp}"
    assert resp["status"] == "STARTED", resp
    print("  -> Khởi tạo tiến trình sản xuất thành công. Đang giám sát tiến độ...", flush=True)

    # Poll status until done
    start_poll = time.time()
    max_wait = 180  # 180 seconds max for offline scenes + SEO pack generation
    last_stage = ""
    while time.time() - start_poll < max_wait:
        time.sleep(2)
        s_code, s_raw = http_get("/api/status")
        assert s_code == 200
        st = json.loads(s_raw)
        stage = st.get("stage", "")
        pct = st.get("percent", 0)
        if stage != last_stage:
            print(f"    [Tiến độ {pct}%] Giai đoạn: {stage} - {st.get('message', '')}", flush=True)
            last_stage = stage
        if not st.get("running"):
            assert st.get("exit_code") == 0, f"Job failed with exit code: {st.get('exit_code')}"
            print(f"  -> PASS: Sản xuất hoàn thành 100%! Thời gian chạy: {st.get('elapsed_seconds')}s.", flush=True)
            return st
    raise TimeoutError("Production job did not complete within timeout")

def test_episode_query_and_media(job_status):
    print("[E2E 5/6] Kiểm tra truy vấn tập phim và tệp phương tiện (/api/episode, /media/...)...", flush=True)
    series_query = urllib.parse.quote("Studio E2E Full Auto Test - Offline Test")
    status, raw = http_get(f"/api/episode?series={series_query}&episode=1")
    assert status == 200
    ep_data = json.loads(raw)
    assert ep_data.get("series")
    assert len(ep_data.get("scenes", [])) == 2, f"Expected 2 scenes, got {len(ep_data.get('scenes', []))}"
    
    final_video = ep_data.get("final_video_url")
    assert final_video, "Final video URL is missing"
    print(f"  -> Video xuất bản: {final_video}", flush=True)

    # Test HTTP 206 Partial Content (Streaming & Scrubbing support)
    video_url = f"{BASE_URL}{final_video}"
    req = urllib.request.Request(video_url, headers={"Range": "bytes=0-1023"})
    with urllib.request.urlopen(req, timeout=5) as v_resp:
        assert v_resp.status == 206, f"Expected HTTP 206 for Range request, got {v_resp.status}"
        chunk = v_resp.read()
        assert len(chunk) == 1024
        print("  -> PASS: Video hỗ trợ HTTP 206 Partial Content (tua video tức thì).", flush=True)

def test_seo_publishing_pack_e2e():
    print("[E2E 6/7] Kiểm tra Gói Xuất bản YouTube & Bộ Thẻ Tags SEO (/api/episode/seo)...", flush=True)
    status, raw = http_get("/api/episode/seo?series=DRAMA&episode=1")
    assert status == 200, f"Expected 200, got {status}"
    data = json.loads(raw)
    assert data.get("best_title"), "Best title missing"
    assert len(data.get("titles", [])) >= 5, "Should have at least 5 CTR title options"
    tags = data.get("tags", [])
    assert len(tags) >= 20, f"Expected >= 20 tags for top SEO rank, got {len(tags)}"
    tag_chars = data.get("tags_character_count", 0)
    assert 380 <= tag_chars <= 495, f"Expected tag characters in golden range [380, 495], got {tag_chars}"
    assert data.get("thumbnail_file"), "Thumbnail file missing"
    vidiq = data.get("vidiq_score", {})
    assert vidiq.get("total_score", 0) >= 95, f"Expected vidIQ score >= 95, got {vidiq.get('total_score')}"
    tags_comp = data.get("component_scores", {}).get("tags", {})
    assert tags_comp.get("score") == 10, f"Expected tags score 10/10, got {tags_comp.get('score')}"
    print(f"  -> PASS: Bộ Thẻ Tags SEO đạt {tags_comp.get('score')}/10 ({len(tags)} tags, {tag_chars}/500 ký tự). Điểm vidIQ: {vidiq.get('total_score')}/100.", flush=True)

def test_stop_job_e2e():
    print("[E2E 7/7] Kiểm tra tính năng dừng khẩn cấp (/api/stop)...", flush=True)
    payload = {
        "mode": "offline",
        "series": "Studio E2E Full Auto Test",
        "episode": 2,
        "prompt": "Tập 2 dự kiến bị dừng khẩn cấp.",
        "input_mode": "idea",
    }
    status, resp = http_post_json("/api/produce", payload)
    assert status == 200 and resp["status"] == "STARTED"
    time.sleep(1)
    
    stop_status, stop_resp = http_post_json("/api/stop", {})
    assert stop_status == 200 and stop_resp["status"] in ("STOPPING", "NOT_RUNNING")
    time.sleep(1)
    
    s_code, s_raw = http_get("/api/status")
    st = json.loads(s_raw)
    assert not st.get("running")
    print("  -> PASS: Lệnh dừng tiến trình phản hồi chính xác, hệ thống an toàn.", flush=True)

def main():
    print("=" * 60)
    print("BẮT ĐẦU CHẠY KIỂM THỬ TOÀN DIỆN E2E CHO STORYBOARD STUDIO")
    print("=" * 60)
    try:
        test_static_ui()
        test_api_config_and_voices()
        test_link_detection()
        job_st = test_production_e2e()
        test_episode_query_and_media(job_st)
        test_seo_publishing_pack_e2e()
        test_stop_job_e2e()
        print("=" * 60)
        print("🎉 TẤT CẢ 7/7 BƯỚC KIỂM THỬ E2E HOÀN TẤT VÀ VƯỢT QUA 100%!")
        print("=" * 60)
    except Exception as exc:
        print(f"\n❌ E2E KIỂM THỬ THẤT BẠI: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
