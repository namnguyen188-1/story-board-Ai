"""Local Storyboard-only image jobs through the private Google Flow MCP runtime."""
from __future__ import annotations
import hashlib
import json
import os
import re
from pathlib import Path
from PIL import Image, ImageOps
from .transport import LocalFlowMcpTransport, _atomic_write, _sha_file
from .accounts import account_tool_url, active_account

IMAGE_MODELS = ("🍌 Nano Banana Pro", "🍌 Nano Banana 2 Lite", "🍌 Nano Banana 2.1")
RENDER_VERSION = "storyboard-native-image-v1"

class StoryboardImageError(RuntimeError):
    pass

class StoryboardImageTransport:
    def __init__(self, mcp=None, tool_url=None):
        # Resolve the active Studio account when the worker starts; never reuse
        # a cached URL from a former V2 session or another Studio account.
        from .projects import is_registered
        account=active_account()
        trusted = os.getenv("STORYBOARD_FROZEN_PROJECT_URL") or account_tool_url(account)
        if not trusted or not is_registered(account,trusted) or (tool_url is not None and tool_url != trusted):
            raise StoryboardImageError("STORYBOARD_PRIVATE_TOOL_URL_REQUIRED")
        self.mcp = mcp or LocalFlowMcpTransport()
        self.tool_url = trusted

    def __call__(self, action, **kwargs):
        if action not in {"health", "render_batch", "receipts", "dry_run"}:
            raise StoryboardImageError("STORYBOARD_IMAGE_ACTION_DENIED")
        result = self.mcp("flow_storyboard_native_image", {
            "action": action, "tool_url": self.tool_url, **kwargs
        })
        if not isinstance(result, dict) or not isinstance(result.get("result"), dict):
            raise StoryboardImageError("STORYBOARD_IMAGE_MCP_INVALID")
        return result["result"]

def validate_image_tool_readiness(h, *, require_queue=False, scoped_production_target=None):
    """Pure read-only validation; no credit reservation, journal or queue edits."""
    if not isinstance(h, dict) or (h.get("native") is not True or h.get("sdk_image") is not True
            or h.get("image_capability") is not True
            or not {"addToQueue", "startImageProduction"}.issubset(set(h.get("capabilities") or []))):
        raise StoryboardImageError("STORYBOARD_IMAGE_REAL_TOOL_MISSING")
    items = h.get("queue_items")
    if items is None:
        if require_queue:
            raise StoryboardImageError("STORYBOARD_IMAGE_QUEUE_STATE_UNKNOWN_NO_SUBMIT")
        return h  # legacy synthetic mocks only; current Flow always supplies list.
    if not isinstance(items, list):
        raise StoryboardImageError("STORYBOARD_IMAGE_QUEUE_STATE_UNKNOWN_NO_SUBMIT")
    # A fresh Studio-owned production tab can have the app default shot_1.
    # Only an exact scoped Chrome target from prepare() may replace it.
    isolated_canary = bool(re.fullmatch(r"[a-fA-F0-9]{32}",
        scoped_production_target or os.getenv("STORYBOARD_CANARY_TARGET_ID", "")))
    placeholder = (len(items)==1 and isinstance(items[0],dict)
        and items[0].get("id")=="shot_1"
        and items[0].get("status")=="pending"
        and items[0].get("asset_kind")=="video")
    completed_items = (len(items) > 0 and all(isinstance(x, dict) and x.get("status") == "completed" for x in items))
    if h.get("running") is True or not (len(items)==0 or placeholder or completed_items):
        raise StoryboardImageError("STORYBOARD_IMAGE_TOOL_QUEUE_STALE_NO_SUBMIT")
    return h

class StoryboardImageBackend:
    def __init__(self, root, *, transport=None, enabled=False, spending_approved=False,
                 max_new_images=0, model=IMAGE_MODELS[0], fallback=True):
        self.root = Path(root).resolve()
        self.transport = transport or StoryboardImageTransport()
        self.enabled = enabled is True
        self.spending_approved = spending_approved is True
        self.max_new_images = int(max_new_images)
        if model not in IMAGE_MODELS or type(fallback) is not bool:
            raise StoryboardImageError("STORYBOARD_IMAGE_MODEL_POLICY_INVALID")
        self.model, self.fallback = model, fallback

    def preflight(self):
        if not self.enabled:
            raise StoryboardImageError("STORYBOARD_IMAGE_OPT_IN_DISABLED")
        return validate_image_tool_readiness(self.transport("health"))


    def _journal(self, scene):
        return self.root / ".storyboard_image_jobs" / (hashlib.sha256(scene.encode()).hexdigest()[:24] + ".json")

    def _verify(self, receipt, job):
        if (not isinstance(receipt, dict) or receipt.get("job_id") != job["job_id"]
                or receipt.get("scene_id") != job["scene_id"]
                or receipt.get("mime_type") not in {"image/png", "image/jpeg", "image/webp"}
                or not receipt.get("media_id") or receipt.get("model_used") not in IMAGE_MODELS
                or (not self.fallback and receipt.get("model_used") != self.model)):
            raise StoryboardImageError("STORYBOARD_IMAGE_RECEIPT_ID_MISMATCH")
        p = Path(str(receipt.get("path") or "")).resolve()
        if (p.parent != self.root or not p.is_file()
                or p.stat().st_size != receipt.get("bytes") or _sha_file(p) != receipt.get("sha256")):
            raise StoryboardImageError("STORYBOARD_IMAGE_INTEGRITY_FAILED")
        try:
            with Image.open(p) as image:
                if image.width <= 0 or image.height <= 0:
                    raise ValueError("dimensions")
                expected = {"image/png": "PNG", "image/jpeg": "JPEG", "image/webp": "WEBP"}[receipt["mime_type"]]
                if image.format != expected:
                    raise ValueError("format")
                image.verify()
        except Exception as exc:
            raise StoryboardImageError("STORYBOARD_IMAGE_DECODER_FAILED") from exc
        return receipt

    def render_one_queue(self, scenes):
        if not self.enabled:
            raise StoryboardImageError("STORYBOARD_IMAGE_OPT_IN_DISABLED")
        if not isinstance(scenes, list) or not 1 <= len(scenes) <= 1000:
            raise StoryboardImageError("STORYBOARD_IMAGE_COUNT_INVALID")
        entries, results, seen = [], {}, set()
        for scene in scenes:
            sid, prompt, ratio = scene.get("scene_id"), scene.get("prompt"), scene.get("aspect_ratio", "16:9")
            if (not isinstance(sid, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", sid)
                    or sid in seen or not isinstance(prompt, str) or not 20 <= len(prompt.strip()) <= 20000
                    or ratio not in {"16:9", "9:16"}):
                raise StoryboardImageError("STORYBOARD_IMAGE_SCENE_INVALID")
            seen.add(sid)
            spec = {"scene_id": sid, "prompt": prompt, "aspect_ratio": ratio,
                    "model": self.model, "fallback": self.fallback}
            fp = hashlib.sha256(json.dumps(spec, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            job = {**spec, "job_id": f"v2_image_{sid[:35]}_{fp[:20]}", "output_dir": str(self.root)}
            old = None
            if self._journal(sid).exists():
                try:
                    old = json.loads(self._journal(sid).read_text(encoding="utf-8"))
                except Exception as exc:
                    raise StoryboardImageError("STORYBOARD_IMAGE_JOURNAL_CORRUPT") from exc
                if old.get("fingerprint") != fp:
                    # Input prompt changed; invalidate obsolete journal so the new prompt can be generated cleanly
                    try:
                        self._journal(sid).unlink(missing_ok=True)
                    except Exception:
                        pass
                    old = None
                elif old.get("state") == "completed":
                    results[sid] = self._verify(old.get("receipt"), job)
            entries.append((sid, fp, job, old))

        def accept(entry, receipt):
            sid, fp, job, _ = entry
            checked = self._verify(receipt, job)
            _atomic_write(self._journal(sid), {"fingerprint": fp, "job_id": job["job_id"],
                         "scene_id": sid, "state": "completed", "receipt": checked})
            results[sid] = checked

        uncertain = [e for e in entries if e[3] and e[0] not in results]
        if uncertain:
            response = self.transport("receipts", jobs=[e[2] for e in uncertain])
            by_id = {r.get("job_id"): r for r in response.get("receipts", []) if isinstance(r, dict)}
            unresolved = []
            for e in uncertain:
                receipt = by_id.get(e[2]["job_id"])
                if receipt is None:
                    unresolved.append(e[2]["job_id"])
                else:
                    accept(e, receipt)  # Commit all recovered successes first.
            if unresolved:
                # Recover gracefully from unrendered or dropped scenes (e.g. timeout or browser disconnect):
                # Clean up stale uncertain journals and re-queue unresolved items into 'new' so they are rendered
                # while preserving all existing completed scene images.
                unresolved_set = set(unresolved)
                for e in uncertain:
                    if e[2]["job_id"] in unresolved_set:
                        try:
                            self._journal(e[0]).unlink(missing_ok=True)
                        except Exception:
                            pass
                        try:
                            native_j = self.root / ".storyboard_native_image_jobs" / (
                                hashlib.sha256(e[2]["job_id"].encode("utf-8")).hexdigest()[:24] + ".json"
                            )
                            native_j.unlink(missing_ok=True)
                        except Exception:
                            pass
                entries = [
                    (e[0], e[1], e[2], None if e[2]["job_id"] in unresolved_set else e[3])
                    for e in entries
                ]
        new = [e for e in entries if e[3] is None]
        if new:
            # All callers, including direct one-image jobs, must verify that
            # the Web Tool is safe BEFORE writing any paid slot or journal.
            self.preflight()
            if not self.spending_approved or not 1 <= self.max_new_images <= 1000 or len(new) > self.max_new_images:
                raise StoryboardImageError("STORYBOARD_IMAGE_SPENDING_NOT_APPROVED")
            active_job_ids = {r.get("job_id") for r in results.values() if isinstance(r, dict)}
            for sdir_name in (".storyboard_image_jobs", ".storyboard_native_image_jobs"):
                s_dir = self.root / sdir_name / ".reserved_slots"
                if s_dir.exists():
                    for sf in list(s_dir.glob("*.json")):
                        try:
                            sdata = json.loads(sf.read_text(encoding="utf-8"))
                            if sdata.get("job_id") not in active_job_ids:
                                sf.unlink(missing_ok=True)
                        except Exception:
                            sf.unlink(missing_ok=True)
            slots = self.root / ".storyboard_image_jobs" / ".reserved_slots"
            used = len(list(slots.glob("*.json"))) if slots.exists() else 0
            if used + len(new) > self.max_new_images:
                raise StoryboardImageError("STORYBOARD_IMAGE_BUDGET_EXHAUSTED")
            slots.mkdir(parents=True, exist_ok=True)
            for sid, fp, job, _ in new:
                already_reserved = False
                for sf in list(slots.glob("*.json")):
                    try:
                        sdata = json.loads(sf.read_text(encoding="utf-8"))
                        if sdata.get("job_id") == job["job_id"]:
                            already_reserved = True
                            break
                    except Exception:
                        pass
                if not already_reserved:
                    reserved = False
                    for i in range(1, self.max_new_images + 1):
                        try:
                            with (slots / f"{i:04d}.json").open("x", encoding="utf-8") as f:
                                json.dump({"job_id": job["job_id"]}, f); f.flush(); os.fsync(f.fileno())
                            reserved = True
                            break
                        except FileExistsError:
                            continue
                    if not reserved:
                        raise StoryboardImageError("STORYBOARD_IMAGE_BUDGET_EXHAUSTED")
                try:
                    self._journal(sid).unlink(missing_ok=True)
                except Exception:
                    pass
                try:
                    with self._journal(sid).open("x", encoding="utf-8") as f:
                        json.dump({"scene_id": sid, "job_id": job["job_id"], "fingerprint": fp,
                                   "state": "submit_uncertain"}, f); f.flush(); os.fsync(f.fileno())
                except FileExistsError as exc:
                    raise StoryboardImageError("STORYBOARD_IMAGE_CONCURRENT_JOB") from exc
            try:
                response = self.transport("render_batch", jobs=[e[2] for e in new])
            except Exception as exc:
                raise StoryboardImageError(f"STORYBOARD_IMAGE_REMOTE_UNCERTAIN_NO_RESUBMIT: {exc}") from exc
            records = {r.get("job_id"): r for r in response.get("receipts", []) if isinstance(r, dict)}
            for e in new:
                if e[2]["job_id"] not in records:
                    raise StoryboardImageError("STORYBOARD_IMAGE_RECEIPT_MISSING_NO_RESUBMIT")
                accept(e, records[e[2]["job_id"]])
        return results
