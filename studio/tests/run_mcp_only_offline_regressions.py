import contextlib,io,json,runpy,sys,time
from pathlib import Path
from unittest.mock import patch
root=Path(r"D:\STORYBOARD_AI\studio");sys.path.insert(0,str(root))
import mcp_v2_batch
results=[]
for name in ["test_private_mcp_four_scenes_no_paid.py","test_private_mcp_node_guards.py","test_mcp_batch_four_mock.py","test_scene_budget_62_no_credit.py"]:
    output=io.StringIO()
    try:
        with contextlib.redirect_stdout(output),patch.object(mcp_v2_batch,"_clear_completed_flow_queue"):
            runpy.run_path(str(root/"tests"/name),run_name="__main__")
        results.append({"test":name,"status":"PASS"})
    except Exception as exc:
        results.append({"test":name,"status":"FAIL","error":type(exc).__name__+": "+str(exc)})
    (root/"runtime/mcp_v2_only_20261108_102327"/(name+".log")).write_text(output.getvalue(),encoding="utf-8")
print(json.dumps(results))
(root/"runtime/mcp_v2_only_20261108_102327/regression_result.json").write_text(json.dumps(results,indent=2),encoding="utf-8")
