"""Safe, read-only reconciliation of interrupted Web Tool jobs.

Only when the FlowKit Chrome is ALREADY running. Never launches the browser,
never submits a new shot and never retries an ambiguous generation.
"""
from __future__ import annotations
from common import STATE
from store import Store
from flow_webtool_jobs import receipt_for
from flow_webtool_direct import WebToolAdapter, WebToolError
from browser_lifecycle import _chrome_active


def reconcile_once():
    if not _chrome_active():
        return {"requeued":0,"examined":0,"reason":"BROWSER_SLEEPING"}
    store = Store(STATE/"jobs.sqlite")
    jobs = [j for j in store.list(10000)
            if j["provider"]=="webtool" and j["state"]=="recovery_needed"]
    count=0
    requeued=0
    statuses={}
    for job in jobs:
        count+=1
        remote = job.get("remote") or {}
        receipt=receipt_for(job["id"]) or {}
        shot_id = remote.get("shot_id") or receipt.get("shot_id")
        if not shot_id or receipt.get("state") not in ("prepared","start_clicked","start_outcome_unknown"):
            continue
        mode=job["request"].get("webtool_mode","hidden")
        if mode not in statuses:
            try:
                statuses[mode]=WebToolAdapter(mode).status()
            except WebToolError:
                statuses[mode]=None
        status = statuses[mode]
        if not status:
            continue
        matches=[x for x in status.get("queue",[]) if x["id"]==shot_id]
        if len(matches)!=1:
            continue
        shot=matches[0]
        # Do not dispatch uncertain pending jobs. Only a verified 'prepared'
        # state permits the single-shot worker to start that exact shot.
        may_resume=(
            shot["status"] in ("generating","completed") and
            (shot["status"]!="completed" or shot.get("has_image" if job["request"].get("kind")=="image" else "has_video"))
        ) or (
            shot["status"]=="pending" and receipt["state"]=="prepared" and
            not status.get("processing")
        )
        if not may_resume:
            continue
        latest=store.get(job["id"])
        if not latest or latest["state"]!="recovery_needed":
            continue
        latest.setdefault("remote",{}).update(shot_id=shot_id,mode=mode)
        latest.update(state="queued",error=None,phase="webtool_resuming_known_shot")
        store.save(latest)
        requeued+=1
    return {"requeued":requeued,"examined":count,"reason":"READ_ONLY_RECONCILIATION"}
