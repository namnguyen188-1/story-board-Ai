"""Install the bundled Flow extension through Chrome's Extensions CDP domain."""
import hashlib
import json
from pathlib import Path
import time
import urllib.request
from websockets.sync.client import connect


class ExtensionBootstrapError(RuntimeError):
    pass


class BrowserCDP:
    def __init__(self, port):
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=3) as response:
            info = json.load(response)
        self.ws = connect(info["webSocketDebuggerUrl"], open_timeout=4, max_size=4 * 1024 * 1024)
        self.sequence = 0

    def call(self, method, params=None, session=None):
        self.sequence += 1
        identity = self.sequence
        message = {"id": identity, "method": method, "params": params or {}}
        if session:
            message["sessionId"] = session
        self.ws.send(json.dumps(message))
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            reply = json.loads(self.ws.recv(timeout=max(0.1, deadline - time.monotonic())))
            if reply.get("id") != identity:
                continue
            if "error" in reply:
                # Never return page state or raw browser messages to clients.
                raise ExtensionBootstrapError("CHROME_EXTENSION_API_UNAVAILABLE")
            return reply.get("result", {})
        raise ExtensionBootstrapError("CHROME_EXTENSION_API_TIMEOUT")

    def close(self):
        self.ws.close()


def fingerprint(folder):
    """Compare only packaged extension files; never inspect account data."""
    folder = Path(folder)
    paths = sorted(p for p in folder.rglob("*") if p.is_file() and "_metadata" not in p.parts)
    if not paths:
        return None
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.relative_to(folder).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def choose_existing(records, directory, expected, digest):
    for record in records:
        if not record.get("enabled") or record.get("name") != expected["name"] or record.get("version") != expected["version"]:
            continue
        path = Path(record.get("path", ""))
        if path.is_dir() and fingerprint(path) == digest:
            return {"id": record["id"], "version": record["version"], "enabled": True,
                    "mode": "reused", "fingerprint": digest}
    return None


def ensure_extension(port, directory, can_install=None):
    directory = Path(directory).resolve()
    manifest = directory / "manifest.json"
    if not manifest.is_file():
        raise ExtensionBootstrapError("BUNDLED_FLOW_EXTENSION_MISSING")
    expected = json.loads(manifest.read_text(encoding="utf-8-sig"))
    digest = fingerprint(directory)
    cdp = BrowserCDP(port)
    try:
        try:
            records = cdp.call("Extensions.getExtensions").get("extensions", [])
        except ExtensionBootstrapError:
            records = []
        existing = choose_existing(records, directory, expected, digest)
        if existing:
            return existing
        if can_install is not None and not can_install():
            raise ExtensionBootstrapError("FLOW_JOBS_ACTIVE_EXTENSION_CHANGE_BLOCKED")
        loaded = cdp.call("Extensions.loadUnpacked", {"path": str(directory)})
        extension_id = loaded.get("id")
        if not extension_id:
            raise ExtensionBootstrapError("FLOW_EXTENSION_INSTALL_NOT_CONFIRMED")
        # Verify enabled state on browsers supporting the inventory API.
        try:
            records = cdp.call("Extensions.getExtensions").get("extensions", [])
        except ExtensionBootstrapError:
            records = None
        if records is not None:
            installed = next((r for r in records if r.get("id") == extension_id), None)
            if not installed or not installed.get("enabled"):
                raise ExtensionBootstrapError("FLOW_EXTENSION_NOT_ENABLED")
        # Existing Flow tabs must reload once for document_start content scripts.
        targets = cdp.call("Target.getTargets").get("targetInfos", [])
        for target in targets:
            if target.get("type") == "page" and target.get("url", "").startswith("https://flow.google.com/"):
                session = cdp.call("Target.attachToTarget", {"targetId": target["targetId"], "flatten": True})["sessionId"]
                cdp.call("Page.reload", session=session)
                cdp.call("Target.detachFromTarget", {"sessionId": session})
        return {"id": extension_id, "version": expected["version"], "enabled": True,
                "mode": "installed", "fingerprint": digest}
    finally:
        cdp.close()
