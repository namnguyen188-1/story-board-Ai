"""Read-only verification of code origin, saved artifacts and protected sources."""
import importlib
import json
from pathlib import Path
import sys
from common import ROOT, STATE, OUTPUTS, MUSE, atomic, file_hash, rebase_muse_profiles
from store import Store


def verify():
    rebase_muse_profiles()
    modules = {}
    for name in ("muse_cli", "muse_accounts", "muse_gateway_worker", "agent.main", "fastapi", "av", "PIL"):
        module = importlib.import_module(name)
        own = Path(module.__file__).resolve().is_relative_to(ROOT)
        modules[name] = own
        if not own:
            raise RuntimeError("EXTERNAL_MODULE_" + name)
    import muse_accounts
    for account in muse_accounts.get_ready_accounts():
        for field in ("profile_home", "cookies_file", "config_file"):
            if not Path(account[field]).resolve().is_relative_to(MUSE):
                raise RuntimeError("EXTERNAL_ACCOUNT_PATH")
    protected = {}
    manifest = ROOT / "COPY_MANIFEST.json"
    if manifest.is_file():
        for path, expected in json.loads(manifest.read_text(encoding="utf-8-sig"))["protected_source_files"].items():
            file = Path(path)
            protected[path] = file_hash(file) == expected if file.is_file() else None
    verified = []
    for job in Store(STATE / "jobs.sqlite").list(10000):
        if job["state"] != "succeeded":
            continue
        for item in job["artifacts"]:
            path = OUTPUTS / job["id"] / item["name"]
            if file_hash(path) != item["sha256"] or path.stat().st_size != item["bytes"]:
                raise RuntimeError("ARTIFACT_CHECKSUM_MISMATCH")
            if item["kind"] == "image":
                from PIL import Image
                with Image.open(path) as media:
                    media.load()
                    info = {"width": media.width, "height": media.height}
            elif item["kind"] == "video":
                import av
                with av.open(str(path)) as media:
                    frame = next(media.decode(video=0))
                    info = {"width": frame.width, "height": frame.height,
                            "seconds": round(media.duration / av.time_base, 3)}
            else:
                info = {"characters": len(path.read_text(encoding="utf-8"))}
            verified.append({"job_id": job["id"], "provider": job["provider"], "file": item["name"], **info})
    report = {"ok": all(value is not False for value in protected.values()),
              "modules_inside_bundle": modules, "protected_sources_unchanged": protected,
              "verified_artifacts": verified}
    atomic(STATE / "verification.json", report)
    print(json.dumps({"ok": report["ok"], "bundled_modules": len(modules),
          "protected_sources": len(protected), "changed_sources": sum(v is False for v in protected.values()),
          "verified_artifacts": verified}, ensure_ascii=False))
    if not report["ok"]:
        raise RuntimeError("PROTECTED_SOURCE_CHANGED")
    return report


if __name__ == "__main__":
    verify()
