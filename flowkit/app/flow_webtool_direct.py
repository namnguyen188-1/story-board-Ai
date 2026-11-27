"""Independent CDP adapter for a Google Flow Web Tool iframe (no MCP V2).

This module NEVER calls Google Flow's internal RPCs and never modifies Web Tool
source. It exposes safe diagnostics, a guarded existing-queue start for Web Tools
with a visible start control, and completed MP4 extraction.
"""
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import threading
import time
import urllib.request

from websockets.sync.client import connect
from common import OUTPUTS, ROOT, STATE, settings

_LOCK = threading.RLock()
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class WebToolError(RuntimeError):
    def __init__(self, code, status=409):
        super().__init__(code)
        self.code = code
        self.status = status


def _read_json(url):
    with urllib.request.urlopen(url, timeout=4) as response:
        return json.load(response)


def _cdp(ws, call_id, method, params=None):
    ws.send(json.dumps({"id": call_id, "method": method, "params": params or {}}))
    deadline = time.monotonic() + 12
    while time.monotonic() < deadline:
        response = json.loads(ws.recv(timeout=12))
        if response.get("id") == call_id:
            if response.get("error"):
                raise WebToolError("CHROME_CDP_ERROR", 503)
            return response.get("result", {})
    raise WebToolError("CHROME_CDP_TIMEOUT", 503)


def _evaluate(ws, call_id, expression):
    data = _cdp(ws, call_id, "Runtime.evaluate", {
        "expression": expression, "returnByValue": True, "awaitPromise": True
    })
    if data.get("exceptionDetails"):
        raise WebToolError("WEBTOOL_BRIDGE_EVALUATION_FAILED", 503)
    return data.get("result", {}).get("value")


def _target_url(mode):
    cfg = settings()
    if mode not in ("active", "hidden"):
        raise WebToolError("UNKNOWN_WEBTOOL_MODE", 400)
    url = cfg.get("flow_webtool_url" if mode == "active" else "flow_hidden_webtool_url")
    if not url or not re.fullmatch(
        r"https://flow\.google\.com/project/[0-9a-f-]{36}/tool/[0-9a-f-]{36}", url
    ):
        raise WebToolError("WEBTOOL_URL_NOT_CONFIGURED", 503)
    return url, int(json.loads((STATE / "machine.json").read_text(encoding="utf-8"))["debug_port"])


class WebToolAdapter:
    def __init__(self, mode="active"):
        self.mode = mode
        self.url, port = _target_url(mode)
        self.debug_url = f"http://127.0.0.1:{port}"

    def _frame(self):
        try:
            tabs = _read_json(self.debug_url + "/json")
            browser = _read_json(self.debug_url + "/json/version")
        except Exception as e:
            raise WebToolError("FLOWKIT_CHROME_UNAVAILABLE", 503) from e
        # Only this configured tool owns the job; never bind a different tool iframe.
        pages = [x for x in tabs if x.get("type") == "page"
                 and x.get("url", "").split("?", 1)[0].rstrip("/") == self.url.rstrip("/")]
        exact_pages = [x for x in pages if x.get("url") == self.url]
        if len(exact_pages) == 1:
            pages = exact_pages
        if len(pages) != 1:
            raise WebToolError("WEBTOOL_TAB_NOT_UNIQUE_OR_NOT_OPEN_MATCHES_" + str(len(pages))
                               + "_EXACT_" + str(len(exact_pages)), 503)
        try:
            with connect(browser["webSocketDebuggerUrl"], open_timeout=5) as ws:
                infos = _cdp(ws, 1, "Target.getTargets")["targetInfos"]
        except Exception as e:
            raise WebToolError("WEBTOOL_CDP_TARGETS_UNAVAILABLE", 503) from e
        child_ids = {x["targetId"] for x in infos
                     if x.get("type") == "iframe" and x.get("parentFrameId") == pages[0]["id"]}
        frames = [x for x in tabs if x.get("id") in child_ids
                  and x.get("type") == "iframe" and "usercontent.goog" in x.get("url", "")]
        if not frames:
            raise WebToolError("WEBTOOL_IFRAME_NOT_READY", 503)
        for f in frames:
            try:
                with connect(f["webSocketDebuggerUrl"], open_timeout=4, max_size=1024*1024) as ws:
                    result = _evaluate(ws, 2,
                        "(()=>({bridge:!!window.__STORYBOARD_MCP__,app:document.title==='Flow app'}))()")
                if result and result.get("app") and result.get("bridge"):
                    return f
            except Exception:
                continue
        raise WebToolError("WEBTOOL_BRIDGE_NOT_READY", 503)

    def status(self):
        f = self._frame()
        code = r"""(()=>{const b=window.__STORYBOARD_MCP__;
          const queued=Array.isArray(b?.queue)?b.queue:[];
          const btns=[...document.querySelectorAll('button')].filter(x=>!x.disabled
            &&x.innerText.includes('START PRODUCTION'));
          return {bridge_version:1,processing:!!b?.isProcessing,
            native_start:typeof b?.startProduction==='function'||typeof b?.v1?.start==='function',
            native_submit:typeof b?.v1?.submit==='function',
            native_status:typeof b?.v1?.status==='function',
            native_result:typeof b?.v1?.result==='function',
            capability_enqueue:typeof b?.capabilities?.addToQueue==='function',
            capability_single_start:typeof b?.capabilities?.retryItem==='function'||typeof b?.capabilities?.startImageProduction==='function'||typeof b?.capabilities?.startProduction==='function',
            ui_start_ready:btns.length===1 && btns[0].innerText.includes('START PRODUCTION (1 VIDEO)'),
            model:b?.config?.model||null,
            native_bridge_version:b?.v1?.version||null,
            queue:queued.map(x=>({id:String(x.id),status:x.status||'unknown',
              title:String(x.title||'').slice(0,200),kind:x.assetKind||null,
              error:String(x.errorMessage||x.error||'').slice(0,450)||null,
              has_video:x.status==='completed' && typeof x.rawBase64==='string'
                && x.mimeType==='video/mp4',
              has_image:x.status==='completed' && typeof x.rawBase64==='string'
                && ['image/jpeg','image/png','image/webp'].includes(x.mimeType)}))}})()"""
        with connect(f["webSocketDebuggerUrl"], open_timeout=5) as ws:
            state = _evaluate(ws, 3, code)
        if not state:
            raise WebToolError("WEBTOOL_BRIDGE_UNREADABLE", 503)
        return {"connected": True, "mode": self.mode, "webtool_url": self.url,
                "engine": "webtool_bridge", **state}

    def start_existing(self, expected_shot_id, request_id):
        """Only start a known, *pending*, one-shot queue through existing UI.

        Save an attempted request before pressing start; never auto-resubmit
        after a timeout, Chrome restart, or unknown remote outcome.
        """
        if not re.fullmatch(r"[A-Za-z0-9_-]{4,100}", request_id or ""):
            raise WebToolError("INVALID_REQUEST_ID", 400)
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", expected_shot_id or ""):
            raise WebToolError("INVALID_SHOT_ID", 400)
        with _LOCK:
            ledger = STATE / "webtool_dispatch_ledger.json"
            existing = json.loads(ledger.read_text(encoding="utf-8")) if ledger.exists() else {}
            if request_id in existing:
                previous = existing[request_id]
                if previous["mode"] != self.mode or previous["shot_id"] != expected_shot_id:
                    raise WebToolError("IDEMPOTENCY_CONFLICT", 409)
                return {"reused": True, **previous}
            current = self.status()
            q = current["queue"]
            if current["processing"] or len(q) != 1 or q[0]["id"] != expected_shot_id or q[0]["status"] != "pending":
                raise WebToolError("WEBTOOL_QUEUE_NOT_SAFE_FOR_START", 409)
            if not current["ui_start_ready"]:
                raise WebToolError("WEBTOOL_START_API_NOT_EXPOSED", 503)
            entry = {"mode": self.mode, "shot_id": expected_shot_id,
                     "state": "dispatch_outcome_unknown", "at": time.time()}
            existing[request_id] = entry
            tmp = ledger.with_suffix(".tmp")
            tmp.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(tmp, ledger)
            frame = self._frame()
            js = r"""(()=>{const b=window.__STORYBOARD_MCP__;
             if(b?.isProcessing||b?.queue?.length!==1||b.queue[0]?.status!=='pending')return 'BLOCKED';
             const a=[...document.querySelectorAll('button')].filter(x=>!x.disabled
                &&x.innerText.includes('START PRODUCTION (1 VIDEO)'));
             if(a.length!==1)return 'NOT_AVAILABLE';a[0].click();return 'CLICKED'})()"""
            with connect(frame["webSocketDebuggerUrl"], open_timeout=5) as ws:
                response = _evaluate(ws, 4, js)
            entry["state"] = "start_clicked" if response == "CLICKED" else "dispatch_outcome_unknown"
            existing[request_id] = entry
            tmp.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(tmp, ledger)
            if response != "CLICKED":
                raise WebToolError("WEBTOOL_START_NOT_CONFIRMED", 409)
            return {"reused": False, **entry}

    def export_video(self, shot_id):
        current = self.status()
        candidate = [q for q in current["queue"] if q["id"] == shot_id]
        if len(candidate) != 1 or candidate[0]["status"] != "completed" or not candidate[0]["has_video"]:
            raise WebToolError("WEBTOOL_VIDEO_NOT_COMPLETED", 409)
        with _LOCK:
            frame = self._frame()
            with connect(frame["webSocketDebuggerUrl"], open_timeout=5, max_size=3*1024*1024) as ws:
                header = _evaluate(ws, 10, r"""(()=>{const x=window.__STORYBOARD_MCP__?.queue?.find(x=>x.id==SHOT_ID);
                    return x?.status==='completed'&&x.mimeType==='video/mp4'?
                      {length:x.rawBase64?.length||0}:null})()""".replace("SHOT_ID", json.dumps(shot_id)))
                if not header or not (1000 < header["length"] <= 130_000_000):
                    raise WebToolError("WEBTOOL_MP4_UNAVAILABLE_OR_TOO_LARGE", 409)
                parts = []
                for i, start in enumerate(range(0, header["length"], 220_000)):
                    end = min(start + 220_000, header["length"])
                    js = f"window.__STORYBOARD_MCP__.queue.find(x=>x.id=={json.dumps(shot_id)}).rawBase64.slice({start},{end})"
                    part = _evaluate(ws, i+20, js)
                    if not isinstance(part, str) or len(part) != end-start:
                        raise WebToolError("WEBTOOL_MP4_TRANSFER_INCOMPLETE", 503)
                    parts.append(part)
            data = base64.b64decode("".join(parts), validate=True)
            if len(data) < 1024 or data[4:8] != b"ftyp":
                raise WebToolError("WEBTOOL_MP4_INVALID", 502)
            sha = hashlib.sha256(data).hexdigest()
            folder = OUTPUTS / "webtool_exports"
            folder.mkdir(parents=True, exist_ok=True)
            output = folder / (sha + ".mp4")
            if not output.is_file() or output.stat().st_size != len(data):
                temp = folder / (sha + ".part")
                temp.write_bytes(data)
                os.replace(temp, output)
            probe = subprocess.run(
                [str(ROOT/"bin"/"ffprobe.exe"), "-v", "error",
                 "-show_entries", "format=duration,size:stream=codec_type,width,height",
                 "-of", "json", str(output)], capture_output=True, text=True, timeout=25)
            if probe.returncode:
                raise WebToolError("WEBTOOL_MP4_VERIFICATION_FAILED", 502)
            info = json.loads(probe.stdout)
            streams = info.get("streams", [])
            video = next((x for x in streams if x.get("codec_type") == "video"), None)
            if not video or float(info.get("format", {}).get("duration", 0)) < 1:
                raise WebToolError("WEBTOOL_MP4_VERIFICATION_FAILED", 502)
            return {"shot_id": shot_id, "sha256": sha, "bytes": len(data),
                    "duration_seconds": float(info["format"]["duration"]),
                    "width": video.get("width"), "height": video.get("height"),
                    "download_url": f"/v1/webtool/files/{sha}.mp4"}


    def export_image(self, shot_id):
        """Read completed image from the authorized Web Tool Bridge; normalize PNG."""
        import io
        from PIL import Image, UnidentifiedImageError
        state=self.status()
        items=[q for q in state["queue"] if q["id"]==shot_id]
        if not items or items[-1]["status"]!="completed" or not items[-1].get("has_image"):
            raise WebToolError("WEBTOOL_IMAGE_NOT_COMPLETED",409)
        with _LOCK:
            frame=self._frame()
            with connect(frame["webSocketDebuggerUrl"],open_timeout=5,max_size=3*1024*1024) as ws:
                expr=r"""(()=>{const x=window.__STORYBOARD_MCP__?.queue?.find(q=>q.id===SHOT);
                     if(!x||x.status!=='completed'||!['image/png','image/jpeg','image/webp'].includes(x.mimeType))
                       return null;
                     return {mime:x.mimeType,length:x.rawBase64?.length||0};})()""".replace(
                        "SHOT",json.dumps(shot_id))
                header=_evaluate(ws,120,expr)
                if not header or not (1000<header["length"]<=70_000_000):
                    raise WebToolError("WEBTOOL_IMAGE_PAYLOAD_INVALID",502)
                chunks=[]
                for index,offset in enumerate(range(0,header["length"],220_000)):
                    end=min(offset+220_000,header["length"])
                    js=(f"window.__STORYBOARD_MCP__.queue.find(q=>q.id==={json.dumps(shot_id)})"
                        f".rawBase64.slice({offset},{end})")
                    value=_evaluate(ws,121+index,js)
                    if not isinstance(value,str) or len(value)!=end-offset:
                        raise WebToolError("WEBTOOL_IMAGE_TRANSFER_INCOMPLETE",503)
                    chunks.append(value)
            raw=base64.b64decode("".join(chunks),validate=True)
            try:
                with Image.open(io.BytesIO(raw)) as image:
                    image.load()
                    if image.width<64 or image.height<64:
                        raise WebToolError("WEBTOOL_IMAGE_TOO_SMALL",502)
                    result=image.convert("RGBA" if "A" in image.getbands() else "RGB")
                    width,height=result.size
                    output_dir=OUTPUTS/"webtool_exports"
                    output_dir.mkdir(parents=True,exist_ok=True)
                    digest=hashlib.sha256(raw).hexdigest()
                    dest=output_dir/(digest+".png")
                    if not dest.is_file():
                        temp=output_dir/(digest+".part.png")
                        result.save(temp,format="PNG")
                        os.replace(temp,dest)
            except (UnidentifiedImageError,OSError) as error:
                raise WebToolError("WEBTOOL_IMAGE_FORMAT_INVALID",502) from error
            return {"shot_id":shot_id,"sha256":hashlib.sha256(dest.read_bytes()).hexdigest(),
                    "source_mime":header["mime"],"width":width,"height":height,
                    "bytes":dest.stat().st_size,"source_path":str(dest)}

def verified_export(digest):
    if not _SHA256.fullmatch(digest):
        raise WebToolError("INVALID_ARTIFACT_DIGEST", 400)
    filename = OUTPUTS / "webtool_exports" / (digest + ".mp4")
    if not filename.is_file():
        raise WebToolError("WEBTOOL_ARTIFACT_NOT_FOUND", 404)
    return filename
