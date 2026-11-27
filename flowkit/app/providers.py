import asyncio
import json
import os
from pathlib import Path
import sys
import time
from urllib.parse import urlsplit
import uuid

import httpx
from common import ROOT, MUSE, OUTPUTS, PYTHON, artifact, atomic, rebase_muse_profiles, settings


class Pending(Exception):
    pass


def safe_operations(operations):
    result = []
    for item in operations:
        op = item.get("operation", {})
        video = op.get("metadata", {}).get("video", {})
        result.append({"operation": {"name": op.get("name"), "metadata": {"video": {"mediaId": video.get("mediaId")}}}, "status": item.get("status")})
    return result


async def flow_health():
    result = {"configured": True, "extension_connected": False, "connected": False,
              "capabilities": ["image", "video", "scene"]}
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(settings()["flow_url"] + "/health")
            response.raise_for_status()
            result["extension_connected"] = bool(response.json().get("extension_connected"))
            if result["extension_connected"]:
                response = await client.get(settings()["flow_url"] + "/api/ext/debug-tab")
                response.raise_for_status()
                page = response.json().get("result", {}).get("data", {})
                # An authenticated tab for a DIFFERENT Google Flow project is
                # not sufficient. Direct submits must use the one signed-in
                # project already authorized in this independent FlowKit profile.
                cfg = settings()
                expected = urlsplit(cfg.get("flow_hidden_webtool_url") or
                                    cfg.get("flow_webtool_url") or
                                    "https://flow.google.com/project/" + cfg["flow_project_id"])
                actual = urlsplit(str(page.get("url") or ""))
                right_tab = (expected.scheme == "https"
                             and expected.netloc == "flow.google.com"
                             and expected.path.startswith("/project/")
                             and actual.scheme == expected.scheme
                             and actual.netloc == expected.netloc
                             and actual.path == expected.path)
                signed_in = bool(page.get("hasAt"))
                result["connected"] = signed_in and right_tab
                if not result["connected"]:
                    result["error"] = ("FLOW_AUTH_REQUIRED" if not signed_in
                                       else "FLOW_UNEXPECTED_PROJECT_TAB")
    except Exception:
        result["connected"] = False
    return result


def muse_accounts():
    import muse_accounts as accounts
    return accounts.list_accounts()


def _muse_verified_account_ids():
    """Recent read-only gateway checks, never infer auth from cookie-file size."""
    cache = ROOT / "state" / "muse_auth_cache.json"
    try:
        record = json.loads(cache.read_text(encoding="utf-8"))
        age = time.time() - float(record.get("checked_at", 0))
        if age < 0 or age > 1800:
            return None
        return {x["account_id"] for x in record.get("accounts", [])
                if x.get("authenticated") is True}
    except (OSError, ValueError, TypeError, KeyError):
        return None


def muse_account(account_id=None):
    import muse_accounts as accounts
    selected = account_id or accounts.get_active_id()
    ready = accounts.get_ready_accounts()
    account = next((item for item in ready if item["id"] == selected), None)
    if account_id:
        # Never silently change an explicitly requested account.
        if account is None:
            raise RuntimeError("MUSE_AUTH_REQUIRED")
        return account
    verified = _muse_verified_account_ids()
    if verified is not None:
        # A stored cookie is not proof of a live login. Select only a recently
        # authenticated Muse account; do not silently dispatch to expired ones.
        if account is not None and account["id"] in verified:
            return account
        for candidate in ready:
            if candidate["id"] in verified:
                return candidate
        raise RuntimeError("MUSE_AUTH_REQUIRED")
    # No recent read-only status audit. The actual Muse worker still verifies
    # authentication and cannot claim success solely from READY metadata.
    account = account or next(iter(ready), None)
    if account is None:
        raise RuntimeError("MUSE_AUTH_REQUIRED")
    return account


async def muse_worker(action, request, request_path, timeout=75):
    atomic(request_path, request)
    env = os.environ.copy()
    env.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8", MUSE_NO_UPDATE_CHECK="1",
               USERPROFILE=str(request["account_home"]), PATH=str(ROOT / "bin") + os.pathsep + env.get("PATH", ""))
    process = await asyncio.create_subprocess_exec(str(PYTHON), "-B", "-u", *([str(MUSE / "muse_text_worker.py"), str(request_path)] if action == "text" else
                 [str(MUSE / "muse_gateway_worker.py"), action, "--request", str(request_path)]), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
               env=env, creationflags=0x08000000 if os.name == "nt" else 0)
    try:
        stdout, _ = await asyncio.wait_for(process.communicate(), timeout)
    except asyncio.TimeoutError:
        if os.name == "nt":
            killer = await asyncio.create_subprocess_exec("taskkill", "/PID", str(process.pid), "/T", "/F",
                     stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL, creationflags=0x08000000)
            await killer.wait()
        else:
            process.kill()
        await process.communicate()
        raise Pending("MUSE_JOB_PENDING") from None
    for line in reversed(stdout.decode("utf-8", errors="replace").splitlines()):
        try:
            result = json.loads(line)
            if isinstance(result, dict) and "ok" in result:
                if result["ok"]:
                    return result
                error = str(result.get("error", "MUSE_WORKER_FAILED"))
                if error.startswith(("MUSE_JOB_PENDING", "MUSE_CONNECTION_INTERRUPTED", "MUSE_AUTH_REQUIRED")):
                    raise Pending(error.split(":", 1)[0])
                raise RuntimeError(error.split(":", 1)[0])
        except json.JSONDecodeError:
            continue
    raise Pending("MUSE_WORKER_OUTCOME_UNKNOWN")


async def muse_health(live=False):
    rebase_muse_profiles()
    accounts = muse_accounts()
    verified = _muse_verified_account_ids()
    result = {"configured": PYTHON.is_file(), "saved_accounts": len(accounts),
              "locally_ready_accounts": sum(bool(a.get("ready")) for a in accounts),
              "recently_authenticated_accounts": len(verified) if verified is not None else None,
              "authentication_checked": verified is not None,
              "connected": None, "capabilities": ["scene", "text"]}
    if live:
        try:
            account = muse_account()
            probe = await muse_worker("status", {"account_home": str(account["profile_home"]), "account_id": account["id"]},
                        ROOT / "state" / "muse_status_request.json", timeout=75)
            result["connected"] = bool(probe.get("ok"))
        except Exception as error:
            result.update(connected=False, error=str(error).split(":", 1)[0])
    return result


async def normalize_muse_video(source, target, seconds):
    """Keep the provider download intact and produce the requested delivery length."""
    import av
    source, target = Path(source), Path(target)
    with av.open(str(source)) as media:
        duration = media.duration / av.time_base if media.duration else 0
    if duration < seconds - 0.15:
        raise RuntimeError("MUSE_VIDEO_TOO_SHORT")
    ffmpeg = ROOT / "bin" / "ffmpeg.exe"
    if not ffmpeg.is_file():
        raise RuntimeError("BUNDLED_FFMPEG_MISSING")
    temporary = target.with_name(target.stem + ".part.mp4")
    process = await asyncio.create_subprocess_exec(str(ffmpeg), "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(source), "-t", str(seconds), "-map", "0:v:0", "-map", "0:a?", "-c:v", "libx264",
        "-preset", "fast", "-crf", "18", "-c:a", "aac", "-movflags", "+faststart", str(temporary),
        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
        creationflags=0x08000000 if os.name == "nt" else 0)
    try:
        await asyncio.wait_for(process.wait(), 180)
    except BaseException:
        process.kill()
        await process.wait()
        temporary.unlink(missing_ok=True)
        raise
    if process.returncode:
        temporary.unlink(missing_ok=True)
        raise RuntimeError("MUSE_VIDEO_NORMALIZE_FAILED")
    with av.open(str(temporary)) as media:
        if not media.duration or abs(media.duration / av.time_base - seconds) > 0.15:
            raise RuntimeError("MUSE_VIDEO_DURATION_MISMATCH")
        next(media.decode(video=0))
    temporary.replace(target)
    return target


async def run_muse(job, checkpoint):
    req = job["request"]
    if req["kind"] == "text":
        return await run_muse_text(job, checkpoint)
    work = OUTPUTS / job["id"]
    work.mkdir(parents=True, exist_ok=True)
    if not (ROOT / "bin" / "ffmpeg.exe").is_file():
        raise RuntimeError("BUNDLED_FFMPEG_MISSING")
    account = muse_account(job.get("account_id") or req.get("account_id"))
    job["account_id"] = account["id"]
    # A READY cookie on disk may be expired. Check live authentication BEFORE
    # any paid create/send call, never during an uncertain remote submission.
    job["phase"] = "muse_auth_preflight"; checkpoint(job)
    try:
        preflight = await muse_worker("status",
            {"account_home":str(account["profile_home"]),"account_id":account["id"]},
            work / "muse_auth_preflight.json", timeout=60)
    except Pending as error:
        raise RuntimeError(str(error).split(":", 1)[0]) from None
    if not preflight.get("ok"):
        raise RuntimeError("MUSE_AUTH_REQUIRED")
    portrait = req["aspect_ratio"] == "9:16"
    request = {"prompt": req["prompt"], "width": 720 if portrait else 1280, "height": 1280 if portrait else 720,
               "duration": req["duration_seconds"], "output_image_path": str(work / "scene.png"),
               "lock_path": str(MUSE / "runtime" / ("muse_render_" + account["id"] + ".lock")),
               "account_home": str(account["profile_home"]), "account_id": account["id"]}
    if account.get("vm_id"):
        request["vm_id"] = account["vm_id"]
    job["phase"] = "muse_worker"
    checkpoint(job)
    result = await muse_worker("render", request, work / "worker_request.json", timeout=settings()["job_timeout_seconds"])
    final_video = await normalize_muse_video(result["video"]["path"], work / "video.mp4", req["duration_seconds"])
    job["artifacts"] = [artifact(job["id"], result["image"]["path"], "image"), artifact(job["id"], final_video, "video")]
    job["remote"] = {"session_id": result.get("session_id")}


async def download_flow(client, media_id, work, kind):
    response = await client.get("/api/flow/media/" + media_id)
    response.raise_for_status()
    record = response.json().get(kind, {})
    url = record.get("fifeUrl")
    host = (urlsplit(url or "").hostname or "").lower()
    if not url or not url.startswith("https://") or not (host == "flow-content.google" or host.endswith((".googleusercontent.com", ".googleapis.com", ".google"))):
        raise RuntimeError("FLOW_MEDIA_URL_UNAVAILABLE")
    target = work / ("scene.png" if kind == "image" else "video.mp4")
    raw = target.with_suffix(".download")
    async with httpx.AsyncClient(timeout=180, follow_redirects=True) as downloader:
        async with downloader.stream("GET", url) as stream:
            stream.raise_for_status()
            size = 0
            with raw.open("wb") as output:
                async for chunk in stream.aiter_bytes():
                    size += len(chunk)
                    if size > 256 * 1024 * 1024:
                        raise RuntimeError("FLOW_DOWNLOAD_TOO_LARGE")
                    output.write(chunk)
    if kind == "image":
        from PIL import Image
        with Image.open(raw) as image:
            image.load()
            image.convert("RGB").save(target, "PNG")
        raw.unlink()
    else:
        raw.replace(target)
        import av
        with av.open(str(target)) as video:
            if not video.streams.video or not video.duration:
                raise RuntimeError("FLOW_VIDEO_NOT_VERIFIED")
    return artifact(work.name, target, kind)


async def run_flow(job, checkpoint):
    req, remote = job["request"], job["remote"]
    work = OUTPUTS / job["id"]
    work.mkdir(parents=True, exist_ok=True)
    cfg = settings()
    # FlowKit is pinned to one user-approved Flow project during R&D.
    # Do not let job payloads redirect paid media generation elsewhere.
    project = str(cfg["flow_project_id"])
    if req.get("project_id") and str(req["project_id"]) != project:
        raise RuntimeError("FLOW_PROJECT_MISMATCH")
    ratio = "PORTRAIT" if req["aspect_ratio"] == "9:16" else "LANDSCAPE"
    async with httpx.AsyncClient(base_url=cfg["flow_url"], timeout=180) as client:
        if not (await flow_health())["connected"]:
            raise RuntimeError("FLOW_TAB_NOT_READY")
        if req["kind"] in {"image", "scene"} and not remote.get("image_id"):
            job["phase"] = "image_submitting"; checkpoint(job)
            response = await client.post("/api/flow/generate-image", json={"prompt": req["prompt"], "project_id": project,
                "aspect_ratio": "IMAGE_ASPECT_RATIO_" + ratio, "image_model": req["image_model"], "count": 1})
            response.raise_for_status()
            media = response.json().get("media", [])
            if not media or not media[0].get("name"):
                raise Pending("FLOW_SUBMISSION_OUTCOME_UNKNOWN")
            remote["image_id"] = str(uuid.UUID(media[0]["name"]))
            job["phase"] = "image_ready"; checkpoint(job)
        if remote.get("image_id") and not any(a["kind"] == "image" for a in job["artifacts"]):
            job["artifacts"].append(await download_flow(client, remote["image_id"], work, "image")); checkpoint(job)
        if req["kind"] == "image":
            return
        if not remote.get("type"):
            job["phase"] = "video_submitting"; checkpoint(job)
            if req["kind"] == "scene":
                response = await client.post("/api/flow/generate-video", json={"prompt": req["prompt"], "project_id": project,
                    "start_image_media_id": remote["image_id"], "scene_id": job["id"], "model_family": "veo",
                    "user_paygate_tier": "PAYGATE_TIER_TWO", "aspect_ratio": "VIDEO_ASPECT_RATIO_" + ratio, "duration_s": 8})
                response.raise_for_status()
                remote.update(type="veo", operations=safe_operations(response.json()["operations"]))
            else:
                response = await client.post("/api/flow/generate-video-omni-text", json={"prompt": req["prompt"], "project_id": project,
                    "aspect_ratio": "VIDEO_ASPECT_RATIO_" + ratio, "duration_s": req["duration_seconds"]})
                response.raise_for_status()
                poll = response.json().get("flowkitPolling", {})
                remote.update(type="omni", workflows=poll.get("workflows", []))
                if not remote["workflows"]:
                    raise Pending("FLOW_SUBMISSION_OUTCOME_UNKNOWN")
            job["phase"] = "video_accepted"; checkpoint(job)
        deadline = time.monotonic() + cfg["job_timeout_seconds"]
        while time.monotonic() < deadline:
            if remote["type"] == "omni":
                response = await client.post("/api/flow/check-omni-status", json={"project_id": project, "workflows": remote["workflows"]})
                response.raise_for_status()
                state = response.json()
                if state.get("done"):
                    item = state.get("workflows", [{}])[0]
                    if item.get("status") != "MEDIA_GENERATION_STATUS_SUCCESSFUL":
                        raise RuntimeError("FLOW_REMOTE_FAILED")
                    remote["video_id"] = item.get("media", {}).get("media_id") or item.get("primary_media_id")
                    break
            else:
                response = await client.post("/api/flow/check-status", json={"project_id": project, "operations": remote["operations"]})
                response.raise_for_status()
                remote["operations"] = safe_operations(response.json().get("operations", []))
                checkpoint(job)
                item = remote["operations"][0] if remote["operations"] else {}
                if item.get("status") == "MEDIA_GENERATION_STATUS_SUCCESSFUL":
                    remote["video_id"] = item["operation"]["metadata"]["video"].get("mediaId")
                    break
                if item.get("status") in {"MEDIA_GENERATION_STATUS_FAILED", "MEDIA_GENERATION_STATUS_CANCELLED"}:
                    raise RuntimeError("FLOW_REMOTE_FAILED")
            await asyncio.sleep(10)
        else:
            raise Pending("FLOW_JOB_PENDING")
        checkpoint(job)
        job["artifacts"].append(await download_flow(client, str(uuid.UUID(remote["video_id"])), work, "video"))


async def run_muse_text(job, checkpoint):
    req = job["request"]
    work = OUTPUTS / job["id"]
    work.mkdir(parents=True, exist_ok=True)
    account = muse_account(job.get("account_id") or req.get("account_id"))
    job["account_id"] = account["id"]
    job["phase"] = "muse_auth_preflight"; checkpoint(job)
    try:
        preflight = await muse_worker("status",
            {"account_home":str(account["profile_home"]),"account_id":account["id"]},
            work / "muse_auth_preflight.json", timeout=60)
    except Pending as error:
        raise RuntimeError(str(error).split(":", 1)[0]) from None
    if not preflight.get("ok"):
        raise RuntimeError("MUSE_AUTH_REQUIRED")
    request = {"prompt": req["prompt"], "output_text_path": str(work / "text.txt"),
               "lock_path": str(MUSE / "runtime" / ("muse_render_" + account["id"] + ".lock")),
               "account_home": str(account["profile_home"]), "account_id": account["id"]}
    job["phase"] = "muse_text_worker"; checkpoint(job)
    result = await muse_worker("text", request, work / "worker_request.json", timeout=settings()["job_timeout_seconds"])
    job["artifacts"] = [artifact(job["id"], result["path"], "text")]
    job["remote"] = {"session_id": result.get("session_id")}
