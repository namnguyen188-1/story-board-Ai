"""Check the live API and download hashes; never submits generation requests."""
import hashlib
import json
import urllib.request
import urllib.error
from common import ROOT, STATE, INSTANCE_ID, api_key, atomic, settings

base = "http://127.0.0.1:" + str(settings()["api_port"])
headers = {"X-API-Key": api_key()}
def get(path, auth=True):
    with urllib.request.urlopen(urllib.request.Request(base + path, headers=headers if auth else {}), timeout=100) as response:
        return response.read()
health = json.loads(get("/health", False))
assert health["instance_id"] == INSTANCE_ID
try:
    get("/v1/jobs", False)
    raise AssertionError("AUTH_NOT_ENFORCED")
except urllib.error.HTTPError as error:
    assert error.code == 401
providers = json.loads(get("/v1/providers?live=true"))
assert providers["flow"]["connected"] and providers["muse"]["connected"]
verified = []
for job in json.loads(get("/v1/jobs?limit=200"))["jobs"]:
    if job["state"] != "succeeded":
        continue
    for item in job["artifacts"]:
        data = get(item["download_url"])
        assert len(data) == item["bytes"]
        assert hashlib.sha256(data).hexdigest() == item["sha256"]
        verified.append({"provider": job["provider"], "job_id": job["id"], "file": item["name"], "bytes": len(data)})
schema = json.loads(get("/openapi.json", False))
atomic(ROOT / "docs" / "openapi.json", schema)
report = {"ok": True, "authentication_required": True, "flow_live": True, "muse_live": True, "verified_downloads": verified}
atomic(STATE / "api_check.json", report)
print(json.dumps(report))
