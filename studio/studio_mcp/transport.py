"""Private stdio transport: only Studio paths, no shared V2 process or data."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
try:
    import silent_subprocess
except Exception:
    pass

HOME=Path(__file__).resolve().parent.parent
NODE=HOME/"studio_mcp"/"node"
OUTPUT=HOME/"runtime"/"private_mcp_outputs"

class PrivateMcpTransportError(RuntimeError):
    pass

def _sha_file(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda:stream.read(1048576),b""):
            h.update(block)
    return h.hexdigest()

def _atomic_write(path, value):
    p=Path(path)
    p.parent.mkdir(parents=True,exist_ok=True)
    fd,temp=tempfile.mkstemp(prefix=".studio_",dir=str(p.parent))
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as file:
            json.dump(value,file,ensure_ascii=False,sort_keys=True)
            file.flush();os.fsync(file.fileno())
        os.replace(temp,p)
    finally:
        if os.path.exists(temp):os.unlink(temp)

def _isolated(row):
    from .accounts import AccountError
    profile=Path(row["user_data_dir"]).resolve()
    state=Path(row["state_dir"]).resolve()
    home=Path.home().resolve()
    allowed_profile=(
        home/".storyboard-studio-private-chrome-default",
        home/".storyboard-studio-private-chrome-accounts",
        home/".storyboard-studio-flow-accounts",
    )
    allowed_state=(
        home/".storyboard-studio-private-state-default",
        home/".storyboard-studio-private-mcp-accounts",
        home/".storyboard-studio-flow-mcp",
        home/".storyboard-studio-flow-accounts",
    )
    def within(path,parents):
        return any(path==p or p in path.parents for p in parents)
    if not within(profile,allowed_profile) or not within(state,allowed_state):
        raise AccountError("STORYBOARD_PRIVATE_PROFILE_MUST_NOT_USE_V2")
    if not (9460<=int(row["cdp_port"])<=9629):
        raise AccountError("STORYBOARD_PRIVATE_CDP_PORT_REQUIRED")

class LocalFlowMcpTransport:
    def __init__(self,timeout=2100,target_id=None):
        self.timeout=timeout
        self.target_id=target_id
    def __call__(self,name,arguments,*,account=None):
        from .accounts import active_account,account_tool_url,account_env,connection_check
        if name!="flow_storyboard_native_image":
            raise PrivateMcpTransportError("STORYBOARD_PRIVATE_IMAGE_TOOL_ONLY")
        row=account or active_account()
        _isolated(row)
        from .projects import is_registered
        frozen=os.getenv("STORYBOARD_FROZEN_PROJECT_URL","")
        link=(arguments.get("tool_url") if arguments.get("action")=="health" and
              is_registered(row,arguments.get("tool_url","")) else
              (frozen or account_tool_url(row)))
        if not link or not is_registered(row,link) or arguments.get("tool_url")!=link:
            raise PrivateMcpTransportError("STORYBOARD_PRIVATE_TOOL_URL_REQUIRED")
        bundled_node = NODE / ("node.exe" if os.name == "nt" else "node")
        executable = str(bundled_node) if bundled_node.is_file() else shutil.which("node")
        if not executable or not (NODE/"studio-flow-rpc.mjs").is_file() or not (NODE/"dist"/"cli.js").is_file():
            raise PrivateMcpTransportError("STORYBOARD_PRIVATE_RUNTIME_NOT_INSTALLED")
        if arguments.get("action") not in ("health","render_batch","receipts","dry_run"):
            raise PrivateMcpTransportError("STORYBOARD_PRIVATE_ACTION_DENIED")
        # No implicit Chrome startup, paid call or access to a foreign CDP endpoint.
        browser=connection_check(row["id"])
        if browser.get("connected") is not True:
            raise PrivateMcpTransportError("STORYBOARD_PRIVATE_BROWSER_NOT_CONNECTED")
        # Pin the bundled Node core to the V2 0.3.1 verified baseline.
        # Do not access or modify the original V2 at runtime.
        from .v2_baseline import verify_v2_baseline,BaselineDriftError
        try:
            verify_v2_baseline()
        except BaselineDriftError as exc:
            raise PrivateMcpTransportError(str(exc)) from exc
        env={k:v for k,v in os.environ.items() if not k.startswith(("V2_FLOW_","V2_STORYBOARD_"))}
        env.update(account_env(row))
        # The worker inherits a target created by Studio. Ordinary health
        # remains strict, and is never silently redirected to a user tab.
        target=self.target_id or os.getenv("STORYBOARD_CANARY_TARGET_ID", "")
        env.pop("STORYBOARD_CANARY_TARGET_ID",None)
        if target:
            import re
            if not re.fullmatch(r"[A-Fa-f0-9]{32}",str(target)):
                raise PrivateMcpTransportError("FLOW_PRODUCTION_TARGET_INVALID")
            env["STORYBOARD_CANARY_TARGET_ID"]=str(target)
        env["STORYBOARD_STUDIO_TOOL_URL"]=link
        env["STORYBOARD_MCP_OUTPUT_ROOT"]=str(OUTPUT.resolve())
        env["STORYBOARD_MCP_APPROVED"]="1" if arguments["action"]=="render_batch" and os.getenv("STORYBOARD_MCP_APPROVED")=="1" else "0"
        env["STORYBOARD_MCP_MAX_NEW_IMAGES"]=os.getenv("STORYBOARD_MCP_MAX_NEW_IMAGES","0") if env["STORYBOARD_MCP_APPROVED"]=="1" else "0"
        env["FLOW_MCP_CONFIG"]=str(NODE/"studio-flow-config.json")
        OUTPUT.mkdir(parents=True,exist_ok=True)
        try:
            res=subprocess.run([executable,str(NODE/"studio-flow-rpc.mjs")],
                input=json.dumps({"name":name,"arguments":arguments},ensure_ascii=False),
                text=True,encoding="utf-8",errors="replace",capture_output=True,
                cwd=str(NODE),env=env,timeout=self.timeout,
                creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
            payload=json.loads(res.stdout.strip().splitlines()[-1])
        except (OSError, subprocess.TimeoutExpired,ValueError,IndexError) as exc:
            raise PrivateMcpTransportError("STORYBOARD_PRIVATE_REMOTE_UNCERTAIN") from exc
        if res.returncode!=0 or payload.get("ok") is not True:
            raise PrivateMcpTransportError("STORYBOARD_PRIVATE_MCP_FAILED:"+str(payload.get("code","unknown"))[:1000])
        return payload.get("result",{})
