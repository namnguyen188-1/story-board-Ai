"""Isolated gallery E2E; never modifies actual productions."""
import json
import tempfile
import threading
import urllib.error
import urllib.request
from pathlib import Path
from http.server import ThreadingHTTPServer
from studio_library import ProductionGallery, GalleryError, is_test_project
import web_server

with tempfile.TemporaryDirectory(prefix="storyboard_gallery_qa_") as temp:
    root = Path(temp)
    prod = root / "productions"
    trash = root / "recycle"
    a = prod / "My-Feature-Film" / "episode_001"
    a.mkdir(parents=True)
    (a / "episode_final.mp4").write_bytes(b"test video bytes")
    (a / "manifest.json").write_text(json.dumps({"status":"COMPLETED","total_scenes":2,"completed":[1,2]}))
    b = prod / "Hand-Color-QA" / "episode_002"
    b.mkdir(parents=True)
    (b / "sample.png").write_bytes(b"image")
    gallery = ProductionGallery(prod, trash)
    inv = gallery.inventory()
    assert len(inv["productions"]) == 2 and inv["stats"]["episodes"] == 2, inv
    assert sum(p["category"]=="main" for p in inv["productions"]) == 1
    assert is_test_project("MCP-E2E-QA")
    print("GALLERY_INVENTORY_PASS", inv["stats"], flush=True)

    web_server.production_gallery = gallery
    web_server.job_status["running"] = False
    web_server.job_process = None
    server = ThreadingHTTPServer(("127.0.0.1", 0), web_server.StudioRequestHandler)
    port = server.server_address[1]
    worker = threading.Thread(target=server.serve_forever,daemon=True)
    worker.start()

    def call(action, headers=None):
        data = json.dumps(action).encode("utf-8")
        h = {"Content-Type":"application/json","Origin":f"http://127.0.0.1:{port}"}
        if headers: h.update(headers)
        req = urllib.request.Request(f"http://127.0.0.1:{port}/api/productions/manage", data=data,headers=h)
        try:
            with urllib.request.urlopen(req,timeout=5) as resp:
                return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    try:
        code, data = call({"action":"trash","series":"My-Feature-Film","episode":"episode_001"},
                          {"Origin":"https://evil.invalid"})
        assert code == 403,(code,data)
        code, data = call({"action":"trash","series":"../My-Feature-Film"})
        assert code == 400,(code,data)
        code, data = call({"action":"trash","series":"My-Feature-Film","episode":"episode_001"},
                          {"Content-Type":"text/plain"})
        assert code == 415,(code,data)

        web_server.job_status["running"] = True
        code, data = call({"action":"trash","series":"My-Feature-Film","episode":"episode_001"})
        assert code == 409 and a.exists(),(code,data)
        web_server.job_status["running"] = False

        code, data = call({"action":"trash","series":"My-Feature-Film","episode":"episode_001"})
        assert code==200 and not a.exists() and len(gallery.list_trash())==1,(code,data)
        key = data["id"]
        print("GALLERY_TRASH_PASS", flush=True)

        a.mkdir()
        code, _ = call({"action":"restore","id":key})
        assert code == 409,(code,_)
        a.rmdir()
        code, data = call({"action":"restore","id":key})
        assert code==200 and a.exists() and (a/"episode_final.mp4").exists(),(code,data)
        print("GALLERY_RESTORE_PASS", flush=True)

        code, data = call({"action":"trash","series":"Hand-Color-QA"})
        assert code==200 and not (prod/"Hand-Color-QA").exists(),(code,data)
        key = data["id"]
        code, data = call({"action":"purge","id":key})
        assert code==200 and not (trash/key).exists(),(code,data)
        assert a.is_dir()
        print("GALLERY_PROJECT_PURGE_PASS", flush=True)
        print("GALLERY_BACKEND_ISOLATED_E2E_PASS", flush=True)
    finally:
        server.shutdown()
        server.server_close()
