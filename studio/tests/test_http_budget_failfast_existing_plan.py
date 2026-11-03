"""Read-only real server preflight against cached 62-scene episode; never submits image spend."""
from pathlib import Path
import json,hashlib,urllib.request,urllib.error
studio=Path(r"D:\STORYBOARD_AI\studio")
plan=studio/"productions"/"RELA-JATE-Y-MANIFESTARA-S-TODO-LO-QUE-DESEES-ESTOICISMO"/"episode_001"/"plan.json"
payload=json.loads(plan.read_text(encoding="utf-8"))["config"]
hash_before=hashlib.sha256(plan.read_bytes()).digest()
req={"series":payload["series"],"episode":payload["episode"],"prompt":payload["reference_url"],
    "reference_url":payload["reference_url"],"minutes":payload["minutes"],
    "scene_seconds":payload["scene_seconds"],"language":payload["language"],
    "input_mode":"link","mode":"live","image_provider":"mcp_v2",
    "visual_style":payload["visual_style"],"genre":payload["genre"],"region":payload["region"],
    "mcp_max_images":20,"mcp_visual_policy":"unique"}
request=urllib.request.Request("http://127.0.0.1:8765/api/produce",
    data=json.dumps(req).encode("utf-8"),
    headers={"Content-Type":"application/json"},method="POST")
try:
    urllib.request.urlopen(request,timeout=8)
    raise AssertionError("unsafe production accepted: 62 scenes for 20 paid images")
except urllib.error.HTTPError as exc:
    info=json.loads(exc.read())
    assert exc.code==409 and info["code"]=="IMAGE_BUDGET_TOO_SMALL",info
    assert info["scene_count"]==62 and info["required_images"]==62
    assert info["approved_images"]==20 and info["saved_plan"] is True
assert hashlib.sha256(plan.read_bytes()).digest()==hash_before
with urllib.request.urlopen("http://127.0.0.1:8765/api/status",timeout=5) as resp:
    s=json.load(resp)
assert s["running"] is False
print("HTTP_REJECTS_62_FOR_20_BEFORE_GEMINI_NO_NEW_JOB_PASS",flush=True)

req["mcp_visual_policy"]="random_invalid_policy"
request=urllib.request.Request("http://127.0.0.1:8765/api/produce",
    data=json.dumps(req).encode("utf-8"),
    headers={"Content-Type":"application/json"},method="POST")
try:
    urllib.request.urlopen(request,timeout=8)
    raise AssertionError("invalid visual policy accepted")
except urllib.error.HTTPError as exc:
    assert exc.code==400,(exc.code,exc.read())
print("HTTP_INVALID_VISUAL_POLICY_REJECTED_PASS",flush=True)
