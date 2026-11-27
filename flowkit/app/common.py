try:
    import silent_subprocess
except ImportError:
    pass

import hashlib
import json
import os
from pathlib import Path
import secrets

ROOT = Path(os.environ.get("FLOWMUSE_ROOT", Path(__file__).resolve().parent.parent)).resolve()
STATE = ROOT / "state"
OUTPUTS = ROOT / "outputs"
MUSE = ROOT / "engines" / "muse"
PYTHON = MUSE / "runtime" / "muse" / "python" / "python.exe"
INSTANCE_ID = hashlib.sha256(str(ROOT).encode()).hexdigest()[:12]
DEFAULTS = {"api_host": "127.0.0.1", "api_port": 8110, "flow_url": "http://127.0.0.1:8100",
            "flow_project_id": "93e7fa3f-e8a4-451d-a03e-f4f3228ee5df", "job_timeout_seconds": 1500}


def atomic(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    for _ in range(5):
        try:
            os.replace(temp, path)
            return
        except PermissionError:
            time.sleep(0.05)
    try:
        os.replace(temp, path)
    except Exception:
        pass


def settings():
    path = ROOT / "settings.json"
    if not path.exists():
        atomic(path, DEFAULTS)
    return {**DEFAULTS, **json.loads(path.read_text(encoding="utf-8-sig"))}


def api_key():
    path = STATE / "api.key"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(secrets.token_urlsafe(32), encoding="ascii")
    return path.read_text(encoding="ascii").strip()


def file_hash(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def rebase_muse_profiles():
    """Rebase only files in this kit. Never fall back to the user's global session."""
    profiles = MUSE / "runtime" / "muse_profiles"
    if not profiles.is_dir():
        return
    for path in profiles.rglob("config.json"):
        try:
            config = json.loads(path.read_text(encoding="utf-8-sig"))
            config["cookies_file"] = str(path.with_name("cookies.txt"))
            atomic(path, config)
        except Exception:
            pass


def artifact(job_id, path, kind):
    path = Path(path).resolve()
    parent = (OUTPUTS / job_id).resolve()
    if not path.is_relative_to(parent) or not path.is_file() or path.stat().st_size == 0:
        raise RuntimeError("OUTPUT_NOT_VERIFIED")
    if kind == "image":
        from PIL import Image
        with Image.open(path) as media:
            metadata = {"width": media.width, "height": media.height}
    elif kind == "video":
        import av
        with av.open(str(path)) as media:
            frame = next(media.decode(video=0))
            metadata = {"width": frame.width, "height": frame.height,
                        "duration_seconds": round(media.duration / av.time_base, 3)}
    else:
        metadata = {"encoding": "utf-8", "characters": len(path.read_text(encoding="utf-8"))}
    return {**metadata, "name": path.name, "kind": kind, "bytes": path.stat().st_size,
            "sha256": file_hash(path), "download_url": f"/v1/jobs/{job_id}/files/{path.name}"}
