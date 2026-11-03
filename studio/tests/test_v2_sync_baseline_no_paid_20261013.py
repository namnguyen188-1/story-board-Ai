"""No-paid baseline regression: detect drift without modifying any installed files."""
from tempfile import TemporaryDirectory
from pathlib import Path
from copy import deepcopy
import json,sys
root=Path(r"D:\STORYBOARD_AI\studio")
sys.path.insert(0,str(root))
from studio_mcp.v2_baseline import verify_v2_baseline,BaselineDriftError
def expect(label,changed,expected):
 with TemporaryDirectory(prefix="v2_pin_test_") as t:
  p=Path(t)/"manifest.json"
  p.write_text(json.dumps(changed,indent=2),encoding="utf-8")
  try:
   verify_v2_baseline(manifest_path=p)
  except BaselineDriftError as exc:
   assert str(exc).startswith(expected),(label,exc)
   print("BASELINE_DRIFT_REJECTED",label,str(exc),flush=True)
  else:raise AssertionError(label+" wrongly allowed")
original=json.loads((root/"studio_mcp"/"MCP_V2_PINNED_BASELINE.json").read_text(encoding="utf-8"))
healthy=verify_v2_baseline()
assert healthy["verified"] and healthy["v2_identical"]==38 and healthy["reviewed_studio_adapters"]==4
print("BASELINE_GOOD_STUDIO_PASS",json.dumps(healthy),flush=True)
core=deepcopy(original)
key=next(iter(core["core_files"]))
core["core_files"][key]="0"*64
expect("unapproved_V2_core_change",core,"STORYBOARD_MCP_V2_CORE_DRIFT")
adapter=deepcopy(original)
key=next(iter(adapter["intentional_studio_adapters"]))
adapter["intentional_studio_adapters"][key]["studio_sha256"]="0"*64
expect("unreviewed_adapter_change",adapter,"STORYBOARD_MCP_V2_ADAPTER_DRIFT")
lock=deepcopy(original)
lock["package_lock_sha256"]="0"*64
expect("dependency_lock_change",lock,"STORYBOARD_MCP_V2_DEPENDENCY_LOCK_DRIFT")
files=deepcopy(original)
files["core_files"].pop(next(iter(files["core_files"])))
expect("missing_core_hash",files,"STORYBOARD_MCP_V2_BASELINE_FILESET_DRIFT")
print("V2_SYNC_BASELINE_NEGATIVE_REGRESSION_4_4_PASS",flush=True)
