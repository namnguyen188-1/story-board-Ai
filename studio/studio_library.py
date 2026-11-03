"""Safe, reversible production gallery management. No production media is removed implicitly."""
from __future__ import annotations

import json
import os
import re
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

_EPISODE = re.compile(r"episode_[0-9]{3,8}\Z")
_TEST_NAMES = ("qa", "regression", "e2e", "offline-test", "smoke", "stress", "flicker", "test", "mock", "integration")


class GalleryError(Exception):
    def __init__(self, message: str, status: int = 400):
        self.status = status
        super().__init__(message)


def is_test_project(name: str) -> bool:
    lowered = name.lower()
    return any(marker in lowered for marker in _TEST_NAMES)


def folder_size(folder: Path) -> int:
    total = 0
    for base, folders, files in os.walk(folder, followlinks=False):
        folders[:] = [d for d in folders if not (Path(base) / d).is_symlink()]
        for filename in files:
            entry = Path(base) / filename
            if not entry.is_symlink():
                try:
                    total += entry.stat().st_size
                except OSError:
                    pass
    return total


def _safe_name(name: object) -> str:
    if not isinstance(name, str) or not name or name in (".", ".."):
        raise GalleryError("Tên thư mục không hợp lệ.")
    if (len(name) > 200 or "/" in name or "\\" in name or ":" in name
        or "\0" in name or name.startswith(".") or name.endswith((" ", "."))):
        raise GalleryError("Tên thư mục không hợp lệ.")
    return name


class ProductionGallery:
    def __init__(self, productions_dir: Path, recycle_dir: Path):
        self.productions = Path(productions_dir).resolve()
        self.recycle = Path(recycle_dir).resolve()

    def _project(self, series: object) -> Path:
        path = self.productions / _safe_name(series)
        if path.is_symlink():
            raise GalleryError("Không thao tác với thư mục liên kết.", 403)
        return path

    def _episode(self, name: object) -> str:
        name = _safe_name(name)
        if not _EPISODE.fullmatch(name):
            raise GalleryError("Mã tập phim không hợp lệ.")
        return name

    def _trash_entry(self, id_value: object) -> Path:
        if not isinstance(id_value, str) or not re.fullmatch(r"[a-f0-9]{32}", id_value):
            raise GalleryError("Mã thùng rác không hợp lệ.")
        return self.recycle / id_value

    def inventory(self) -> dict:
        self.productions.mkdir(parents=True, exist_ok=True)
        result = []
        bytes_total = 0
        for project in self.productions.iterdir():
            if not project.is_dir() or project.is_symlink() or project.name.startswith("."):
                continue
            episodes = []
            for ep in project.iterdir():
                if ep.is_symlink() or not ep.is_dir() or not _EPISODE.fullmatch(ep.name):
                    continue
                manifest_file = ep / "manifest.json"
                manifest = {}
                if manifest_file.is_file() and not manifest_file.is_symlink():
                    try:
                        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
                        if not isinstance(manifest, dict):
                            manifest = {}
                    except (OSError, ValueError, TypeError):
                        pass
                final = ep / "episode_final.mp4"
                size = folder_size(ep)
                updated = ep.stat().st_mtime
                completed = manifest.get("completed", [])
                if not isinstance(completed, (list, dict)):
                    completed = []
                episodes.append({
                    "folder": ep.name,
                    "has_final": final.is_file() and not final.is_symlink(),
                    "has_plan": (ep / "plan.json").is_file() and not (ep / "plan.json").is_symlink(),
                    "status": str(manifest.get("status") or "UNKNOWN"),
                    "total_scenes": int(manifest.get("total_scenes") or 0),
                    "completed_scenes": len(completed),
                    "updated": str(manifest.get("updated") or ""),
                    "updated_epoch": updated,
                    "size_bytes": size,
                    "final_url": f"/media/{final.relative_to(self.productions.parent).as_posix()}" if final.exists() else None,
                })
            # Include shared bibles, anchors, and project metadata in project storage.
            size = folder_size(project)
            bytes_total += size
            episodes.sort(key=lambda item: item["updated_epoch"], reverse=True)
            result.append({
                "series": project.name,
                "category": "test" if is_test_project(project.name) else "main",
                "episodes": episodes,
                "size_bytes": size,
                "updated_epoch": max([e["updated_epoch"] for e in episodes], default=project.stat().st_mtime)
            })
        result.sort(key=lambda item: (item["category"] != "main", -item["updated_epoch"]))
        trashed = self.list_trash()
        return {
            "productions": result, "trash": trashed,
            "stats": {
                "projects": len(result),
                "episodes": sum(len(p["episodes"]) for p in result),
                "test_projects": sum(p["category"] == "test" for p in result),
                "bytes": bytes_total,
                "trash_items": len(trashed),
                "trash_bytes": sum(item["size_bytes"] for item in trashed)
            }
        }

    def list_trash(self) -> list[dict]:
        if not self.recycle.exists():
            return []
        entries = []
        for entry in self.recycle.iterdir():
            if entry.is_symlink() or not entry.is_dir() or not re.fullmatch(r"[a-f0-9]{32}", entry.name):
                continue
            manifest = entry / "record.json"
            if not manifest.is_file() or manifest.is_symlink():
                continue
            try:
                record = json.loads(manifest.read_text(encoding="utf-8"))
                name = _safe_name(record.get("series"))
                episode = record.get("episode")
                if episode is not None:
                    self._episode(episode)
                payload = entry / "payload"
                if not payload.is_dir() or payload.is_symlink():
                    continue
                entries.append({
                    "id": entry.name, "series": name, "episode": episode,
                    "removed_at": record.get("removed_at", ""),
                    "size_bytes": folder_size(payload),
                    "category": "test" if is_test_project(name) else "main",
                })
            except (OSError, ValueError, TypeError, GalleryError):
                continue
        entries.sort(key=lambda x: x["removed_at"], reverse=True)
        return entries

    def trash(self, series: object, episode: object = None) -> dict:
        project = self._project(series)
        if episode is not None:
            source = project / self._episode(episode)
        else:
            source = project
        if source.is_symlink():
            raise GalleryError("Không thao tác với thư mục liên kết.", 403)
        if not source.exists() or not source.is_dir():
            raise GalleryError("Không tìm thấy phim hoặc dự án.", 404)

        self.recycle.mkdir(parents=True, exist_ok=True)
        key = uuid.uuid4().hex
        record_dir = self.recycle / key
        record_dir.mkdir()
        try:
            record = {
                "series": project.name, "episode": episode,
                "removed_at": datetime.now(timezone.utc).isoformat(),
            }
            (record_dir / "record.json").write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
            source.rename(record_dir / "payload")
        except Exception:
            # Never remove user data after a failed move.
            if not (record_dir / "payload").exists():
                shutil.rmtree(record_dir, ignore_errors=True)
            raise
        return {"id": key, **record, "status": "TRASHED"}

    def restore(self, id_value: object) -> dict:
        entry = self._trash_entry(id_value)
        manifest = entry / "record.json"
        payload = entry / "payload"
        if entry.is_symlink() or payload.is_symlink() or not manifest.is_file() or not payload.is_dir():
            raise GalleryError("Không tìm thấy bản lưu trong thùng rác.", 404)
        record = json.loads(manifest.read_text(encoding="utf-8"))
        project = self._project(record.get("series"))
        ep = record.get("episode")
        target = project / self._episode(ep) if ep is not None else project
        if target.exists() or target.is_symlink():
            raise GalleryError("Thư mục gốc đã tồn tại. Không ghi đè dữ liệu hiện có.", 409)
        if ep is not None:
            project.mkdir(parents=True, exist_ok=True)
        payload.rename(target)
        shutil.rmtree(entry)
        return {"status": "RESTORED", "series": project.name, "episode": ep}

    def purge(self, id_value: object) -> dict:
        entry = self._trash_entry(id_value)
        payload = entry / "payload"
        if entry.is_symlink() or payload.is_symlink() or not payload.is_dir() or not (entry / "record.json").is_file():
            raise GalleryError("Không tìm thấy dữ liệu cần xóa.", 404)
        shutil.rmtree(entry)
        return {"status": "DELETED"}
