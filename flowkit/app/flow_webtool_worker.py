"""Web Tool job worker. Uses the Web Tool app, not Flow's internal network API."""
import asyncio
from pathlib import Path
import shutil
import time

from common import OUTPUTS, artifact, settings
from flow_webtool_direct import WebToolAdapter, WebToolError
from flow_webtool_jobs import WebToolProduction, receipt_for


async def run_webtool(job, checkpoint):
    request = job["request"]
    if request["kind"] not in ("image", "video"):
        raise WebToolError("WEBTOOL_UNSUPPORTED_KIND", 422)
    if request["duration_seconds"] != 8:
        raise WebToolError("WEBTOOL_DURATION_UNSUPPORTED", 422)
    mode = request.get("webtool_mode") or "active"
    job["phase"] = "webtool_checking"
    checkpoint(job)
    remote = job["remote"]
    if not remote.get("shot_id"):
        # Do NOT resubmit if a prior invocation had an unknown outcome.
        ledger = receipt_for(job["id"])
        if ledger is not None:
            if not ledger.get("shot_id"):
                raise WebToolError("WEBTOOL_SUBMISSION_OUTCOME_UNKNOWN_NO_RESUBMIT",409)
            remote.update(shot_id=ledger["shot_id"], mode=mode)
            checkpoint(job)
        else:
            job["phase"] = "webtool_submitting"
            checkpoint(job)
            submitted = await asyncio.to_thread(
                WebToolProduction(mode).submit, job["id"], request["prompt"],
                request["aspect_ratio"], request["kind"], request.get("image_model") or "NANO_BANANA_PRO",
                video_model=request.get("video_model") or "OMNI_1_2_FLASH",
                resolution=request.get("resolution") or "720p")
            remote.update(shot_id=submitted["shot_id"], mode=mode)
            job["phase"] = "webtool_generating"
            checkpoint(job)
    shot_id = remote["shot_id"]
    # Resume only a verified prepared shot; never submit a duplicate scene.
    recorded = receipt_for(job["id"])
    if mode == "hidden" and recorded and recorded.get("state") == "prepared":
        job["phase"] = "webtool_starting_known_shot"
        checkpoint(job)
        await asyncio.to_thread(WebToolProduction(mode).start_enqueued, job["id"], shot_id)
        job["phase"] = "webtool_generating"
        checkpoint(job)
    deadline = time.monotonic() + settings()["job_timeout_seconds"]
    match_wait_until = time.monotonic() + 15.0
    while time.monotonic() < deadline:
        state = await asyncio.to_thread(WebToolAdapter(mode).status)
        matches = [x for x in state["queue"] if x["id"] == shot_id]
        if not matches:
            if time.monotonic() < match_wait_until:
                await asyncio.sleep(0.5)
                continue
            raise WebToolError("WEBTOOL_SHOT_NOT_FOUND_AFTER_START",409)
        shot = matches[-1]
        status = shot["status"]
        if status == "completed":
            if not shot.get("has_image" if request["kind"]=="image" else "has_video"):
                raise WebToolError("WEBTOOL_COMPLETED_WITHOUT_MEDIA",409)
            break
        if status in ("failed","error","cancelled"):
            job["diagnostic"] = {"webtool_error": shot.get("error"),
                                 "webtool_status": status}
            checkpoint(job)
            raise WebToolError("WEBTOOL_REMOTE_FAILED",502)
        job["phase"] = "webtool_generating"
        checkpoint(job)
        await asyncio.sleep(5)
    else:
        raise WebToolError("WEBTOOL_REMOTE_JOB_PENDING",409)
    job["phase"] = "webtool_exporting"
    checkpoint(job)
    image_job = request["kind"] == "image"
    adapter = WebToolAdapter(mode)
    info = await asyncio.to_thread(adapter.export_image if image_job else adapter.export_video, shot_id)
    source = (OUTPUTS / "webtool_exports" / (info["sha256"]+".mp4")) if not image_job else Path(info["source_path"])
    directory = OUTPUTS / job["id"]
    directory.mkdir(parents=True, exist_ok=True)
    output = directory / ("scene.png" if image_job else "video.mp4")
    if not output.exists() or output.stat().st_size != info["bytes"]:
        temp = directory / ("image.part" if image_job else "video.part")
        shutil.copyfile(source,temp)
        temp.replace(output)
    job["artifacts"] = [artifact(job["id"],output,request["kind"])]
    remote.update(sha256=info["sha256"], model=state.get("model"),shot_id=shot_id)
    checkpoint(job)
