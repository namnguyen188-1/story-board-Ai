"""Standalone Node RPC guard regression. Zero Flow browser connections or credits."""
import json,os,subprocess
from pathlib import Path
root=Path(r"D:\STORYBOARD_AI\studio\studio_mcp\node")
rpc=root/"studio-flow-rpc.mjs"
url="https://flow.google.com/project/11111111-1111-4111-8111-111111111111/tool/22222222-2222-4222-8222-222222222222?mode=APP"
root_output=Path(r"D:\STORYBOARD_AI\studio\runtime\private_mcp_outputs")
def invoke(action,env_extra):
    env=os.environ.copy()
    for key in ("STORYBOARD_STUDIO_TOOL_URL","STORYBOARD_MCP_APPROVED","STORYBOARD_MCP_MAX_NEW_IMAGES"):
        env.pop(key,None)
    env.update({
      "FLOW_MCP_USER_DATA_DIR":str(Path.home()/".storyboard-studio-private-chrome-default"),
      "FLOW_MCP_STATE_DIR":str(Path.home()/".storyboard-studio-private-state-default"),
      "FLOW_MCP_CDP_PORT":"9550",
      "STORYBOARD_MCP_OUTPUT_ROOT":str(root_output),
      **env_extra
    })
    request={"name":"flow_storyboard_native_image","arguments":{
      "action":action,"tool_url":url,
      "jobs":[{"job_id":"v2_test_private_12345678","scene_id":"offline_scene","prompt":"A clean fictional landscape cinematic wide photo",
       "model":"🍌 Nano Banana 2 Lite","fallback":False,
       "aspect_ratio":"16:9","output_dir":str(root_output/"test")}]}}
    result=subprocess.run(["node",str(rpc)],input=json.dumps(request),text=True,capture_output=True,encoding="utf-8",
                          timeout=20,cwd=str(root),env=env)
    assert result.stdout.strip(), ("No structured output",result.stderr[:200])
    reply=json.loads(result.stdout.strip().splitlines()[-1])
    return result.returncode,reply

status,res=invoke("render_batch",{"STORYBOARD_STUDIO_TOOL_URL":url})
assert status!=0 and "SPEND_NOT_APPROVED" in res.get("code",""),res
print("PRIVATE_SPEND_GATE_PASS",flush=True)
status,res=invoke("health",{})
assert status!=0 and "TOOL_URL_REQUIRED" in res.get("code",""),res
print("PRIVATE_MISSING_TOOL_CONFIG_PASS",flush=True)
status,res=invoke("render_batch",{"STORYBOARD_STUDIO_TOOL_URL":url,
                                  "STORYBOARD_MCP_APPROVED":"1","STORYBOARD_MCP_MAX_NEW_IMAGES":"0"})
assert status!=0 and "SPEND_NOT_APPROVED" in res.get("code",""),res
print("PRIVATE_BUDGET_GATE_PASS",flush=True)
print("PRIVATE_NODE_RPC_NO_PAID_CALLS_PASS",flush=True)
