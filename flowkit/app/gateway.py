import asyncio
from contextlib import asynccontextmanager
import hmac
import json
from pathlib import Path
import re
import time
from typing import Literal
import uuid

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.security import APIKeyHeader
import httpx
from pydantic import BaseModel, Field, model_validator, field_validator

from common import ROOT, STATE, OUTPUTS, MUSE, INSTANCE_ID, api_key, rebase_muse_profiles, settings
from store import Store, Conflict
from flow_models import image_model_key, video_model_key
from providers import flow_health, muse_health, muse_accounts, _muse_verified_account_ids, Pending, run_flow, run_muse
from flow_webtool_direct import WebToolAdapter, WebToolError, verified_export
from flow_webtool_worker import run_webtool
from flow_webtool_jobs import receipt_for
from browser_lifecycle import begin_use, end_use, ensure_browser, close_if_safe, status as browser_status
from webtool_recovery import reconcile_once

store = Store(STATE / "jobs.sqlite")
key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
tasks = []


def authorize(value=Depends(key_header)):
    if not value or not hmac.compare_digest(value, api_key()):
        raise HTTPException(401, "X-API-Key is required")


class JobRequest(BaseModel):
    provider: Literal["flow", "muse", "webtool"]
    kind: Literal["image", "video", "scene", "text"]
    prompt: str = Field(min_length=1, max_length=120000)
    aspect_ratio: Literal["9:16", "16:9"] = "9:16"
    duration_seconds: Literal[8] = 8
    image_model: Literal["NANO_BANANA_PRO", "NANO_BANANA_2", "NANO_BANANA_2_LITE", "NANO_BANANA_2.1", "NANO_BANANA_2_1"] = "NANO_BANANA_PRO"
    video_model: Literal["OMNI_1_2_FLASH", "VEO_3_1_LITE", "OMNI_1_1_FLASH"] = "OMNI_1_2_FLASH"
    resolution: Literal["360p", "720p"] = "720p"
    webtool_mode: Literal["active", "hidden"] = "hidden"
    account_id: str | None = Field(default=None, pattern=r"^[A-Za-z0-9_-]{1,80}$")
    project_id: uuid.UUID | None = None
    request_id: str | None = Field(default=None, min_length=4, max_length=100)

    @field_validator("image_model", mode="before")
    @classmethod
    def normalize_image_model(cls, value):
        # Keep legacy request storage stable while accepting current names.
        return image_model_key(value)

    @field_validator("video_model", mode="before")
    @classmethod
    def normalize_video_model(cls, value):
        return video_model_key(value)

    @model_validator(mode="after")
    def validate_capability(self):
        if self.provider == "muse" and self.kind not in {"scene", "text"}:
            raise ValueError("Muse supports kind=text or kind=scene (image plus video)")
        if self.provider == "flow" and self.kind == "text":
            raise ValueError("Flow text generation is not supported")
        if self.provider == "webtool" and self.kind not in {"image", "video"}:
            raise ValueError("Web Tool supports image and 8-second video jobs only")
        if self.provider == "webtool" and self.kind == "image" and self.webtool_mode != "hidden":
            raise ValueError("Web Tool image jobs require the hidden Remix adapter")
        if self.kind != "text" and len(self.prompt) > 16000:
            raise ValueError("Media prompts are limited to 16000 characters")
        return self


class BatchRequest(BaseModel):
    requests: list[JobRequest] = Field(min_length=1, max_length=50)


def public(job):
    return {key: value for key, value in job.items() if key not in {"remote"}}


async def provider_worker(provider):
    while True:
        job = store.claim(provider)
        if not job:
            await asyncio.sleep(0.4)
            continue
        needs_browser = provider in {"flow", "webtool"}
        if needs_browser:
            begin_use()
        try:
            if needs_browser:
                await asyncio.to_thread(ensure_browser, provider)
            if provider == "flow":
                await run_flow(job, store.save)
            elif provider == "webtool":
                await run_webtool(job, store.save)
            else:
                await run_muse(job, store.save)
            job.update(state="succeeded", phase="complete", error=None, finished_at=time.time())
        except asyncio.CancelledError:
            job.update(state="recovery_needed", error={"code": "SERVICE_STOPPED", "message": "No automatic resubmit; inspect and resume the same job"})
            store.save(job)
            raise
        except Exception as error:
            receipt = OUTPUTS / job["id"] / "muse_job.json"
            remote_known = bool(job["remote"]) if provider in {"flow", "webtool"} else receipt.is_file()
            uncertain = isinstance(error, Pending) or "submitting" in job["phase"] or remote_known
            terminal = str(error).startswith(("MUSE_REMOTE_FAILED", "FLOW_REMOTE_FAILED", "MUSE_ASPECT_MISMATCH", "WEBTOOL_REMOTE_FAILED"))
            if provider == "webtool":
                # A rejected preflight has not reached Google Flow. A persisted
                # dispatch attempt may already have done so; never replay it.
                uncertain = bool(job["remote"]) or receipt_for(job["id"]) is not None
            if terminal:
                uncertain = False
            if isinstance(error, httpx.HTTPStatusError):
                code = "FLOW_HTTP_" + str(error.response.status_code)
                # Persist classifications only, never signed URLs or browser credentials.
                detail = error.response.text
                clues = re.findall(r"(?:NO_AT_TOKEN|NO_FLOW_TAB|RpcError|FlowBatchError|TimeoutError|ValueError|RPC[^\n]{0,24}\[[0-9, ]+\]|Extension not connected|No Flow tab[^\n]{0,40}|not signed in|recaptcha[^\n]{0,35})", detail, re.I)
                job["diagnostic"] = {"http_status": error.response.status_code, "clues": clues[:4]}
                # A concrete rejected submit was not accepted. A poll failure can still be pending.
                if error.response.status_code in {400, 401, 403, 404, 422, 429} and "submitting" in job["phase"]:
                    uncertain = False
            elif isinstance(error, (httpx.TimeoutException, httpx.NetworkError)):
                code = "FLOW_CONNECTION_INTERRUPTED"
            else:
                text = str(error).split(":", 1)[0]
                code = text if re.fullmatch(r"[A-Z][A-Z0-9_]{2,100}", text) else "PROVIDER_ERROR"
            job.update(state="recovery_needed" if uncertain else "failed", error={"code": code,
                "message": "Keep this job ID; a remote request may already exist" if uncertain else "Provider did not return a verified result"})
        finally:
            if needs_browser:
                end_use()
        store.save(job)


async def browser_idle_watcher():
    iteration = 0
    while True:
        await asyncio.sleep(5)
        iteration += 1
        try:
            # Reconnect ONLY an existing accepted remote shot. Never spawn a
            # sleeping browser, rerun an unknown submit, or create a duplicate.
            if iteration % 4 == 0:
                await asyncio.to_thread(reconcile_once)
            await asyncio.to_thread(close_if_safe)
        except Exception as error:
            from browser_lifecycle import record_error
            await asyncio.to_thread(record_error, type(error).__name__)
            # A lifecycle fault must never stop jobs or change an unknown status.


@asynccontextmanager
async def lifespan(app):
    rebase_muse_profiles()
    api_key()
    store.recover()
    tasks.extend(asyncio.create_task(provider_worker(provider)) for provider in ("flow", "muse"))
    for _ in range(3):
        tasks.append(asyncio.create_task(provider_worker("webtool")))
    tasks.append(asyncio.create_task(browser_idle_watcher()))
    yield
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    tasks.clear()


app = FastAPI(title="Flow + Muse Orchestrator", version="1.1.0", lifespan=lifespan,
              description="Independent local dispatcher. Flow supports image/video/scene; Muse supports text jobs and an image+video scene. Providers never silently substitute for each other.")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "flow-muse-orchestrator", "version": "1.1.0", "instance_id": INSTANCE_ID}


@app.get("/", response_class=HTMLResponse)
async def home():
    return """<!doctype html><html lang=vi><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>FlowKit - On-Demand</title><style>body{font:15px system-ui;max-width:760px;margin:36px auto;padding:20px;background:#10151e;color:#e5ecf7;line-height:1.65}h1{font-size:24px;margin:0}h2{font-size:17px;margin-top:28px}a{color:#8bc6ff}code{overflow-wrap:anywhere}li{margin:8px 0}.small{font-size:13px;color:#a8b5c9}</style><h1>FlowKit - On-Demand</h1><p>API nh&#7853;n l&#7879;nh lu&#244;n s&#7861;n s&#224;ng. Chrome v&#224; Web Tool ch&#7881; m&#7903; khi c&#243; t&#225;c v&#7909; s&#7843;n xu&#7845;t.</p><h2>V&#242;ng &#273;&#7901;i s&#7843;n xu&#7845;t</h2><ol><li>Vi&#7871;t k&#7883;ch b&#7843;n: kh&#244;ng m&#7903; Chrome/Web Tool.</li><li>B&#7845;m S&#7843;n xu&#7845;t: FlowKit t&#7921; m&#7903; Chrome &#7849;n v&#224; Web Tool &#273;&#250;ng d&#7921; &#225;n.</li><li>&#272;ang render: gi&#7919; nguy&#234;n phi&#234;n, kh&#244;ng t&#7855;t/b&#7853;t.</li><li>Ho&#224;n t&#7845;t: l&#432;u, ki&#7875;m tra MP4; ch&#7881; &#273;&#243;ng sau th&#7901;i gian r&#7843;nh v&#224; kh&#244;ng c&#242;n job ch&#7901;/c&#7847;n kh&#244;i ph&#7909;c.</li></ol><p><strong>Ch&#7871; &#273;&#7897;:</strong> <code>browser_mode: on_demand</code>; <strong>th&#7901;i gian r&#7843;nh:</strong> 90 gi&#226;y. C&#7845;u h&#236;nh: <code>D:\\FLOWKIT\\settings.json</code>.</p><p><a href=/docs>Xem API v&#224; c&#225;c l&#7879;nh tr&#7841;ng th&#225;i</a></p><p class=small>D&#249;ng kh&#243;a <code>X-API-Key</code> t&#7841;i <code>state/api.key</code> trong trang API docs. <code>GET /v1/runtime/browser</code> ch&#7881; &#273;&#7885;c tr&#7841;ng th&#225;i; kh&#244;ng kh&#7903;i &#273;&#7897;ng Chrome. <code>POST /v1/runtime/browser/stop</code> ch&#7881; &#273;&#243;ng khi an to&#224;n.</p></html>"""


@app.get("/v1/providers", dependencies=[Depends(authorize)])
async def providers(live: bool = False):
    flow, muse = await asyncio.gather(flow_health(), muse_health(live))
    runtime = await asyncio.to_thread(browser_status)
    # The local API stays awake but the authorized Chrome profile is deliberately
    # stopped. Report this as sleeping, not a connection failure.
    sleeping = runtime["mode"] == "on_demand" and not runtime["browser_running"]
    flow["sleeping"] = sleeping
    flow["available_on_request"] = bool(sleeping and flow["configured"])
    if sleeping:
        flow.pop("error", None)
    try:
        webtool = await asyncio.to_thread(WebToolAdapter("hidden").status)
    except WebToolError as error:
        runtime = await asyncio.to_thread(browser_status)
        sleeping = runtime["mode"] == "on_demand" and not runtime["browser_running"]
        webtool = {"connected": False, "sleeping": sleeping,
                   "available_on_request": sleeping,
                   "error": None if sleeping else error.code}
    return {"flow": flow, "muse": muse, "webtool": webtool,
            "limits": {"flow": 1, "muse": 1, "webtool": 1}, "silent_fallback": False}


@app.get("/v1/accounts/muse", dependencies=[Depends(authorize)])
async def accounts():
    verified = await asyncio.to_thread(_muse_verified_account_ids)
    return [{**{key: item.get(key) for key in ("id", "name", "active", "ready", "status")},
             "authenticated_recently": (item["id"] in verified) if verified is not None else None}
            for item in muse_accounts()]


def submit(body, idempotency_key=None):
    data = body.model_dump(mode="json", exclude={"request_id"})
    identity = idempotency_key or body.request_id or str(uuid.uuid4())
    if len(identity) > 120:
        raise HTTPException(400, "Idempotency-Key is too long")
    try:
        job, reused = store.create(data, identity)
    except Conflict as error:
        raise HTTPException(409, str(error)) from None
    return {"job_id": job["id"], "state": job["state"], "reused": reused, "status_url": "/v1/jobs/" + job["id"]}


@app.post("/v1/jobs", status_code=202, dependencies=[Depends(authorize)])
async def create_job(body: JobRequest, idempotency_key: str | None = Header(default=None)):
    return submit(body, idempotency_key)


@app.post("/v1/jobs/batch", status_code=202, dependencies=[Depends(authorize)])
async def batch(body: BatchRequest):
    return {"jobs": [submit(item) for item in body.requests]}


@app.get("/v1/jobs", dependencies=[Depends(authorize)])
async def list_jobs(limit: int = Query(default=50, ge=1, le=200)):
    return {"jobs": [public(job) for job in store.list(limit)]}


@app.get("/v1/jobs/{job_id}", dependencies=[Depends(authorize)])
async def get_job(job_id: uuid.UUID):
    job = store.get(str(job_id))
    if not job:
        raise HTTPException(404, "Job not found")
    return public(job)


@app.post("/v1/jobs/{job_id}/resume", status_code=202, dependencies=[Depends(authorize)])
async def resume(job_id: uuid.UUID):
    job = store.get(str(job_id))
    if not job:
        raise HTTPException(404, "Job not found")
    if job["state"] != "recovery_needed":
        raise HTTPException(409, "Only recovery_needed jobs can resume")
    if job.get("browser_hold") is False:
        raise HTTPException(409, "Reviewed unknown remote outcome; do not resubmit")
    if job["provider"] == "flow":
        if "submitting" in job["phase"] or not job["remote"]:
            raise HTTPException(409, "The submit outcome is unknown; do not create a duplicate request")
    elif job["provider"] == "webtool":
        recorded = receipt_for(job["id"])
        shot = job["remote"].get("shot_id") or (recorded or {}).get("shot_id")
        if not shot:
            raise HTTPException(409, "No confirmed Web Tool shot; inspect before retry, never resubmit")
        job["remote"].update(shot_id=shot, mode=job["request"].get("webtool_mode", "active"))
    else:
        receipt = OUTPUTS / job["id"] / "muse_job.json"
        if not receipt.is_file() or not json.loads(receipt.read_text(encoding="utf-8")).get("session_id"):
            raise HTTPException(409, "No accepted Muse session is recorded; inspect before retry")
    job.update(state="queued", error=None)
    store.save(job)
    return {"job_id": job["id"], "state": "queued", "same_remote_job": True}


class ParkUnknownRequest(BaseModel):
    confirm: Literal[True]


@app.post("/v1/jobs/{job_id}/park", dependencies=[Depends(authorize)])
async def park_unknown_flow_job(job_id: uuid.UUID, body: ParkUnknownRequest):
    """Preserve an old, unresumable 502 for audit without pinning Chrome forever.

    Does NOT mark the job successful/failed, retry, clear remote state or modify
    credentials. Only a rejected image submission with no remote ID is eligible.
    """
    job = store.get(str(job_id))
    if not job:
        raise HTTPException(404, "Job not found")
    if job["provider"] != "flow" or job["state"] != "recovery_needed" or (
        job.get("phase") != "image_submitting"
    ) or job.get("remote") or job.get("artifacts") or (
        (job.get("error") or {}).get("code") != "FLOW_HTTP_502"
    ):
        raise HTTPException(409, "Only an unresolved Flow 502 with no remote ID can be parked")
    if job.get("browser_hold") is False:
        return {"job_id":job["id"], "state":"recovery_needed",
                "parked":True, "reused":True}
    if time.time() - job.get("updated_at",time.time()) < 1800:
        raise HTTPException(409, "Wait until the unknown remote outcome has aged 30 minutes")
    if any(j["state"] in {"running", "queued"} and j["provider"] in {"flow","webtool"}
           for j in store.list(10000)):
        raise HTTPException(409, "Media jobs still active; do not park during production")
    # It is a local browser-lifetime decision, NOT proof that Google did not
    # accept the request. No job is retried or declared failed.
    job["browser_hold"] = False
    job["recovery_review"] = {
        "status":"parked_unverified_502",
        "reason":"No confirmed Flow media ID was returned by the 502 response",
        "remote_outcome":"unknown",
        "retry_permitted":False,
        "reviewed_at":time.time()
    }
    store.save(job)
    return {"job_id":job["id"], "state":"recovery_needed",
            "parked":True, "remote_outcome":"unknown", "automatic_retry":False}


@app.post("/v1/jobs/{job_id}/cancel", dependencies=[Depends(authorize)])
async def cancel(job_id: uuid.UUID):
    job = store.get(str(job_id))
    if not job:
        raise HTTPException(404, "Job not found")
    if job["state"] != "queued":
        raise HTTPException(409, "Only a queued local job can be cancelled; an accepted remote job may keep running")
    job["state"] = "cancelled"
    store.save(job)
    return {"job_id": job["id"], "state": "cancelled"}


@app.get("/v1/jobs/{job_id}/files/{filename}", dependencies=[Depends(authorize)])
async def download(job_id: uuid.UUID, filename: str):
    job = store.get(str(job_id))
    if not job or not any(a["name"] == filename for a in job["artifacts"]):
        raise HTTPException(404, "Artifact not found")
    path = (OUTPUTS / str(job_id) / filename).resolve()
    if not path.is_relative_to((OUTPUTS / str(job_id)).resolve()) or not path.is_file():
        raise HTTPException(404, "Artifact not found")
    return FileResponse(path, filename=filename)


# Optional direct connection to an existing Web Tool's iframe.
# This never replaces Flow Direct/Muse and never modifies the remote Web Tool.
class WebToolStartRequest(BaseModel):
    mode: Literal["active", "hidden"] = "active"
    expected_shot_id: str = Field(min_length=1, max_length=100)
    request_id: str = Field(min_length=4, max_length=100)
    confirm: Literal[True]


class WebToolExportRequest(BaseModel):
    mode: Literal["active", "hidden"] = "active"
    shot_id: str = Field(min_length=1, max_length=100)


@app.get("/v1/webtool/status", dependencies=[Depends(authorize)])
async def webtool_status(mode: Literal["active", "hidden"] = "hidden"):
    try:
        return await asyncio.to_thread(WebToolAdapter(mode).status)
    except WebToolError as error:
        runtime = await asyncio.to_thread(browser_status)
        sleeping = runtime["mode"] == "on_demand" and not runtime["browser_running"]
        return {"mode": mode, "connected": False, "sleeping": sleeping,
                "available_on_request": sleeping,
                "error": None if sleeping else error.code}


@app.post("/v1/webtool/start-existing", status_code=202, dependencies=[Depends(authorize)])
async def webtool_start_existing(body: WebToolStartRequest):
    """Start only the pending single-shot queue already in the Web Tool.
    No arbitrary prompt injection; hidden mode requires an exposed command.
    """
    try:
        return await asyncio.to_thread(WebToolAdapter(body.mode).start_existing,
                                       body.expected_shot_id, body.request_id)
    except WebToolError as error:
        raise HTTPException(error.status, error.code) from None


@app.post("/v1/webtool/export", dependencies=[Depends(authorize)])
async def webtool_export(body: WebToolExportRequest):
    """Export an already completed MP4; this does NOT start generation."""
    try:
        return await asyncio.to_thread(WebToolAdapter(body.mode).export_video, body.shot_id)
    except WebToolError as error:
        raise HTTPException(error.status, error.code) from None


@app.get("/v1/webtool/files/{digest}.mp4", dependencies=[Depends(authorize)])
async def webtool_export_file(digest: str):
    try:
        path = verified_export(digest)
    except WebToolError as error:
        raise HTTPException(error.status, error.code) from None
    return FileResponse(path, media_type="video/mp4", filename=path.name)


@app.get("/v1/runtime/browser", dependencies=[Depends(authorize)])
async def get_browser_runtime():
    """Inspect the on-demand FlowKit browser. No browser is launched."""
    return await asyncio.to_thread(browser_status)


@app.post("/v1/runtime/browser/stop", dependencies=[Depends(authorize)])
async def stop_browser_when_safe():
    """Optional manual idle-close, denied during production or recovery."""
    outcome = await asyncio.to_thread(close_if_safe, True)
    if not outcome["closed"]:
        raise HTTPException(409, outcome)
    return outcome


# Disabled in R&D: the read-only Flow Direct diagnostic was not live-verified.
# Do not expose or invoke a partially tested endpoint.
async def flow_direct_readonly_diagnostics():
    """Open ONLY FlowKit's existing authorized profile to inspect Flow Direct.

    No render request, new Flow project, account data, cookies, or retry occurs.
    Hold the browser lease across the check so the idle watcher cannot close
    it while a read-only credit/status request is in progress.
    """
    begin_use()
    try:
        try:
            await asyncio.to_thread(ensure_browser, "flow")
        except Exception as exc:
            return {"connected":False,"status":"BROWSER_PRECHECK_FAILED",
                    "reason":type(exc).__name__,"media_submissions":0}
        healthy = None
        for attempt in range(8):
            healthy = await flow_health()
            if healthy.get("connected"):
                break
            await asyncio.sleep(2)
        if not healthy or not healthy.get("connected"):
            return {"connected":False,"status":"FLOW_SESSION_NOT_READY",
                    "extension_connected":bool((healthy or {}).get("extension_connected")),
                    "media_submissions":0}
        try:
            async with httpx.AsyncClient(timeout=40) as client:
                response=await client.get(settings()["flow_url"]+"/api/flow/credits")
            # Return only transport/result classification; never expose raw
            # account information, errors, signed URLs, or account identifiers.
            result = {
                "connected":True,"status":"READ_ONLY_CHECK_COMPLETE",
                "credits_endpoint_http":response.status_code,
                "credits_lookup_ok":response.status_code==200,
                "media_submissions":0,
                "warning":"Credit endpoint health does not prove generate-image RPC works"
            }
            return result
        except Exception as exc:
            return {"connected":True,"status":"CREDIT_READ_FAILED",
                    "reason":type(exc).__name__,"media_submissions":0}
    finally:
        end_use()
