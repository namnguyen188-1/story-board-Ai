"""Local Storyboard video jobs through the private Google Flow MCP runtime.

Generates AI motion video directly via Google Flow (Veo 3.1 & Omni 1.1 Flash).
Supports Image-to-Video (using keyframe image as reference) and Text-to-Video.
Durable receipts, ffprobe stream verification, zero baseline drift.
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

from .transport import _atomic_write, _sha_file, NODE, OUTPUT
from .accounts import active_account, connection_check

VIDEO_MODELS = (
    "Omni 1.1 Flash",
    "Veo 3.1 - Fast",
    "Veo 3.1 - Quality",
    "Veo 3.1 - Lite",
)
DEFAULT_VIDEO_MODEL = "Omni 1.1 Flash"
DEFAULT_DURATION = 8

class StoryboardVideoError(RuntimeError):
    pass

class StoryboardVideoTransport:
    def __init__(self, timeout=1800, account=None):
        self.timeout = timeout
        self.account = account

    def __call__(self, action, **kwargs):
        if action not in {"health", "render_batch", "receipts"}:
            raise StoryboardVideoError(f"STORYBOARD_VIDEO_ACTION_DENIED: {action}")
        account = self.account or active_account()
        check = connection_check(account["id"])
        if not check.get("connected"):
            raise StoryboardVideoError(f"STORYBOARD_VIDEO_BROWSER_NOT_CONNECTED: {account.get('name', account.get('id'))}")

        bundled_node = NODE / ("node.exe" if os.name == "nt" else "node")
        executable = str(bundled_node) if bundled_node.is_file() else shutil.which("node")
        script = NODE / "studio-flow-video-rpc.mjs"
        if not executable or not script.is_file():
            raise StoryboardVideoError("STORYBOARD_VIDEO_RUNTIME_NOT_INSTALLED")

        env = {k: v for k, v in os.environ.items()}
        env["FLOW_MCP_CDP_PORT"] = str(account.get("cdp_port", 9550))
        env["STORYBOARD_MCP_OUTPUT_ROOT"] = str(OUTPUT.resolve())

        payload = {"action": action, **kwargs}
        try:
            res = subprocess.run(
                [executable, str(script)],
                input=json.dumps(payload, ensure_ascii=False),
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                cwd=str(NODE),
                env=env,
                timeout=self.timeout,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
            )
            raw = res.stdout.strip().splitlines()[-1] if res.stdout.strip() else "{}"
            data = json.loads(raw)
        except (OSError, subprocess.TimeoutExpired, ValueError, IndexError) as exc:
            raise StoryboardVideoError("STORYBOARD_VIDEO_REMOTE_TIMEOUT_OR_UNAVAILABLE") from exc

        if res.returncode != 0 or data.get("ok") is not True:
            err_msg = str(data.get("error") or data.get("code") or res.stderr or "UNKNOWN")[:150]
            raise StoryboardVideoError(f"STORYBOARD_VIDEO_RPC_FAILED: {err_msg}")

        return data

class StoryboardVideoBackend:
    def __init__(self, root, *, transport=None, account=None, enabled=True, model=DEFAULT_VIDEO_MODEL,
                 duration=DEFAULT_DURATION, aspect_ratio="16:9", resolution="720p"):
        self.root = Path(root).resolve()
        self.account = account
        self.transport = transport or StoryboardVideoTransport(account=account)
        self.enabled = enabled is True
        if model not in VIDEO_MODELS:
            model = DEFAULT_VIDEO_MODEL
        self.model = model
        self.duration = int(duration) if duration in (4, 6, 8, 10) else DEFAULT_DURATION
        self.aspect_ratio = aspect_ratio if aspect_ratio in ("16:9", "9:16") else "16:9"
        self.resolution = resolution if resolution in ("720p", "1080p") else "720p"

    def preflight(self):
        if not self.enabled:
            raise StoryboardVideoError("STORYBOARD_VIDEO_DISABLED")
        health = self.transport("health")
        if not health.get("healthy"):
            raise StoryboardVideoError("STORYBOARD_VIDEO_HEALTH_CHECK_FAILED")
        return health

    def _journal(self, scene_id):
        j_dir = self.root / ".storyboard_video_jobs"
        j_dir.mkdir(parents=True, exist_ok=True)
        return j_dir / (hashlib.sha256(scene_id.encode()).hexdigest()[:24] + ".json")

    def _verify(self, receipt, job):
        if (not isinstance(receipt, dict) or receipt.get("job_id") != job["job_id"]
                or receipt.get("scene_id") != job["scene_id"]
                or receipt.get("mime_type") != "video/mp4"):
            raise StoryboardVideoError("STORYBOARD_VIDEO_RECEIPT_MISMATCH")
        p = Path(str(receipt.get("path") or "")).resolve()
        if not p.is_file() or p.stat().st_size != receipt.get("bytes"):
            raise StoryboardVideoError("STORYBOARD_VIDEO_FILE_MISSING_OR_CORRUPT")
        if _sha_file(p) != receipt.get("sha256"):
            raise StoryboardVideoError("STORYBOARD_VIDEO_SHA_MISMATCH")
        return receipt

    def render_video_batch(self, scenes):
        """Render a list of scenes into video files.
        
        scenes: list of dicts with:
          - scene_id: str (e.g. 'scene_0001')
          - prompt: str
          - reference_image: str (optional path to keyframe image for Image-to-Video)
          - aspect_ratio: '16:9' or '9:16' (optional)
          - duration: 4, 6, 8, 10 (optional)
        """
        if not self.enabled:
            raise StoryboardVideoError("STORYBOARD_VIDEO_DISABLED")
        if not isinstance(scenes, list) or not scenes:
            raise StoryboardVideoError("STORYBOARD_VIDEO_EMPTY_BATCH")

        entries = []
        results = {}
        for sc in scenes:
            sid = str(sc.get("scene_id") or "")
            prompt = str(sc.get("prompt") or "").strip()
            ratio = sc.get("aspect_ratio") or self.aspect_ratio
            duration = int(sc.get("duration") or self.duration)
            ref_img = str(sc.get("reference_image") or "") if sc.get("reference_image") else None

            spec = {
                "scene_id": sid,
                "prompt": prompt,
                "aspect_ratio": ratio,
                "duration": duration,
                "model": self.model,
            }
            fp = hashlib.sha256(json.dumps(spec, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            job = {
                **spec,
                "job_id": f"flow_vid_{sid[:35]}_{fp[:16]}",
                "output_dir": str(self.root),
                "resolution": self.resolution,
                "reference_image": ref_img,
            }

            old = None
            j_file = self._journal(sid)
            if j_file.is_file():
                try:
                    old = json.loads(j_file.read_text(encoding="utf-8"))
                    if old.get("fingerprint") == fp and old.get("state") == "completed":
                        results[sid] = self._verify(old.get("receipt"), job)
                    else:
                        old = None
                except Exception:
                    old = None

            entries.append((sid, fp, job, old))

        # Check in-flight receipts
        uncertain = [e for e in entries if e[3] and e[0] not in results]
        if uncertain:
            res = self.transport("receipts", jobs=[e[2] for e in uncertain])
            by_id = {r.get("job_id"): r for r in res.get("receipts", []) if isinstance(r, dict)}
            for e in uncertain:
                r = by_id.get(e[2]["job_id"])
                if r:
                    checked = self._verify(r, e[2])
                    _atomic_write(self._journal(e[0]), {
                        "fingerprint": e[1],
                        "job_id": e[2]["job_id"],
                        "scene_id": e[0],
                        "state": "completed",
                        "receipt": checked,
                    })
                    results[e[0]] = checked

        # Submit new jobs
        new_jobs = [e for e in entries if e[0] not in results]
        if new_jobs:
            self.preflight()
            print(f"[FLOW_VIDEO] Đang gửi {len(new_jobs)} phân cảnh đến Google Flow ({self.model})...", flush=True)
            res = self.transport("render_batch", jobs=[e[2] for e in new_jobs])
            receipts = {r.get("job_id"): r for r in res.get("receipts", []) if isinstance(r, dict)}
            for e in new_jobs:
                jid = e[2]["job_id"]
                if jid not in receipts:
                    raise StoryboardVideoError(f"STORYBOARD_VIDEO_RECEIPT_MISSING: {e[0]}")
                checked = self._verify(receipts[jid], e[2])
                results[e[0]] = checked

        return results
