"""Per-account, per-genre Google Flow project routing. No credential or V2 access."""
from __future__ import annotations
import json, re
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import urlopen

URL_RE=re.compile(r"^/project/([0-9a-fA-F-]{36})/tool/([0-9a-fA-F-]{36})$")
MAX_PROJECTS=48

class ProjectError(ValueError):pass

def _base():
    from . import accounts
    return accounts

def project_url(project_id, tool_id):
    candidate=f"https://flow.google.com/project/{project_id}/tool/{tool_id}"
    if not URL_RE.fullmatch(urlsplit(candidate).path):
        raise ProjectError("FLOW_PROJECT_URL_INVALID")
    return candidate

def _parts(link):
    try:
        parsed=urlsplit(link)
        if parsed.scheme!="https" or parsed.netloc!="flow.google.com" or parsed.query not in ("","mode=APP","fromViewSource=tools"):
            return None
        found=URL_RE.fullmatch(parsed.path)
        return tuple(x.lower() for x in found.groups()) if found else None
    except (ValueError,TypeError):
        return None

def _path(account):
    return Path(account["state_dir"])/"studio_flow_projects.json"

def _bootstrap(account):
    # Legacy persisted Studio URL is preserved as default project, without copying any cookie.
    old=Path(account["state_dir"])/"studio_private_tool_url.json"
    try:
        item=json.loads(old.read_text(encoding="utf-8"))
        parts=_parts(str(item.get("url") or ""))
    except (OSError,ValueError,TypeError,AttributeError):
        parts=None
    records=[{"id":parts[0]+":"+parts[1],"project_id":parts[0],"tool_id":parts[1],
             "label":"Dự án đã liên kết", "genre":"auto"}] if parts else []
    return {"version":1,"active":records[0]["id"] if records else None,
            "genres":{},"projects":records}

def load(account):
    location=_path(account)
    if not location.is_file():
        return _bootstrap(account)
    try:
        data=json.loads(location.read_text(encoding="utf-8"))
        if data.get("version")!=1:raise ValueError("version")
        projects=data["projects"]
        if not isinstance(projects,list) or len(projects)>MAX_PROJECTS:raise ValueError("projects")
        from studio_modes import GENRES
        seen=set()
        for entry in projects:
            parts=(entry["project_id"],entry["tool_id"])
            if _parts(project_url(*parts))!=parts or entry["id"]!=":".join(parts):
                raise ValueError("identity")
            if entry["genre"] not in GENRES or not isinstance(entry["label"],str) or not 1<=len(entry["label"])<=65:
                raise ValueError("attributes")
            if entry["id"] in seen:raise ValueError("duplicate")
            seen.add(entry["id"])
        if data.get("active") is not None and data["active"] not in seen:raise ValueError("active")
        if not isinstance(data.get("genres"),dict):raise ValueError("genres")
        for genre,pid in data["genres"].items():
            if genre not in GENRES or pid not in seen:raise ValueError("genre mapping")
        return data
    except (OSError,ValueError,KeyError,TypeError,AttributeError) as exc:
        raise ProjectError("STUDIO_FLOW_PROJECT_REGISTRY_CORRUPT") from exc

def save(account,data):
    from .accounts import _atomic_store
    # Reject malformed records BEFORE writing, even for a newly bootstrapped file.
    for entry in data["projects"]:
        if _parts(project_url(entry["project_id"],entry["tool_id"]))!= (entry["project_id"],entry["tool_id"]):
            raise ProjectError("FLOW_PROJECT_ID_INVALID")
    _atomic_store(_path(account),data)

def tabs(account):
    """Only the exact account Chrome CDP. List metadata, never credentials."""
    from .accounts import connection_check,_pid_browser_for_account
    from .transport import _isolated
    _isolated(account)
    if not connection_check(account["id"]).get("connected") or not _pid_browser_for_account(account):
        return []
    try:
        with urlopen(f"http://127.0.0.1:{account['cdp_port']}/json/list",timeout=8.0) as response:
            pages=json.load(response)
    except (OSError,ValueError,TypeError):
        return []
    result={}
    for page in pages:
        if page.get("type")!="page":continue
        parts=_parts(page.get("url",""))
        if parts:
            ref=":".join(parts)
            result[ref]={"id":ref,"project_id":parts[0],"tool_id":parts[1]}
    return list(result.values())


def exact_tool_tab_count(account, link):
    """Count exact Tool tabs, without deduplication; no prompt reads."""
    from .accounts import connection_check,_pid_browser_for_account
    from .transport import _isolated
    _isolated(account)
    expected=_parts(link)
    if not expected or not connection_check(account["id"]).get("connected"):
        return 0
    if not _pid_browser_for_account(account):
        return 0
    try:
        with urlopen(f"http://127.0.0.1:{account['cdp_port']}/json/list",timeout=8.0) as response:
            pages=json.load(response)
    except (OSError,ValueError,TypeError):
        return 0
    if not isinstance(pages,list):
        return 0
    return sum(1 for page in pages if isinstance(page,dict) and
               page.get("type")=="page" and _parts(page.get("url",""))==expected)


def cleanup_duplicate_tool_tabs(account, link=None):
    """Compatibility hook: tab order does not establish ownership.

    A new production tab may be listed BEFORE the original Web Tool. Closing
    matching[1:] can delete the original, and releasing the temporary tab then
    exits Chrome. A blank tab may also belong to the user. Preserve all tabs;
    duplicate preflight reports the conflict, while production_tab releases
    only its exact, verified disposable target.
    """
    from .transport import _isolated
    _isolated(account)
    return 0


def probe_v2_compatible_tool(account, ref, *, timeout=37):
    """Allow registration only for an account-owned, V2-compatible native app.

    Read-only: inspect the exact Flow tab. Never read prompts or spend credit.
    """
    from .accounts import _pid_browser_for_account
    from .transport import _isolated,NODE
    import os,shutil,subprocess
    _isolated(account)
    if not _pid_browser_for_account(account):
        raise ProjectError("FLOW_V2_COMPATIBLE_CHROME_REQUIRED")
    parts=ref.split(":")
    if len(parts)!=2:
        raise ProjectError("FLOW_PROJECT_ID_INVALID")
    target=project_url(parts[0],parts[1])
    if not any(p["id"]==ref for p in tabs(account)):
        raise ProjectError("FLOW_V2_COMPATIBLE_TOOL_TAB_REQUIRED")
    executable=NODE/("node.exe" if os.name=="nt" else "node")
    if not executable.is_file():
        found=shutil.which("node")
        if not found:raise ProjectError("FLOW_V2_PROBE_NODE_MISSING")
        executable=Path(found)
    script=NODE/"verify-v2-compatible-tool.mjs"
    if not script.is_file():raise ProjectError("FLOW_V2_PROBE_NOT_INSTALLED")
    try:
        result=subprocess.run([str(executable),str(script)],
            input=json.dumps({"port":account["cdp_port"],"tool_url":target}),
            cwd=str(NODE),encoding="utf-8",errors="replace",text=True,
            capture_output=True,timeout=timeout,
            creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        payload=json.loads(result.stdout.strip().splitlines()[-1])
    except (OSError,subprocess.TimeoutExpired,ValueError,IndexError) as exc:
        raise ProjectError("FLOW_V2_NATIVE_BRIDGE_PROBE_FAILED") from exc
    if result.returncode!=0 or payload.get("ok") is not True or payload.get("compatible") is not True:
        raise ProjectError("FLOW_V2_NATIVE_IMAGE_BRIDGE_MISSING")
    return True


def register(account, ref, label, genre):
    from studio_modes import GENRES
    from .accounts import _require_idle
    _require_idle()
    if genre not in GENRES:raise ProjectError("FLOW_GENRE_INVALID")
    label=str(label or "").strip()
    if not 1<=len(label)<=65 or any(ord(ch)<32 for ch in label):
        raise ProjectError("FLOW_PROJECT_LABEL_INVALID")
    visible=next((item for item in tabs(account) if item["id"]==ref),None)
    if not visible:raise ProjectError("FLOW_PROJECT_MUST_BE_OPEN_IN_ACCOUNT_CHROME")
    # Reject unrelated Web Tools before saving a new project mapping.
    probe_v2_compatible_tool(account,ref)
    data=load(account)
    existing=next((p for p in data["projects"] if p["id"]==ref),None)
    if not existing:
        if len(data["projects"])>=MAX_PROJECTS:raise ProjectError("FLOW_PROJECT_LIMIT")
        data["projects"].append({**visible,"label":label,"genre":genre})
    else:
        existing.update(label=label,genre=genre)
    data["active"]=ref
    if genre!="auto":data["genres"][genre]=ref
    save(account,data)
    return {"id":ref,"label":label,"genre":genre}

def choose(account, ref, genre=None):
    from studio_modes import GENRES
    from .accounts import _require_idle
    _require_idle()
    data=load(account)
    item=next((item for item in data["projects"] if item["id"]==ref),None)
    if item is None:raise ProjectError("FLOW_PROJECT_NOT_REGISTERED")
    if genre is not None and genre not in GENRES:raise ProjectError("FLOW_GENRE_INVALID")
    data["active"]=ref
    if genre and genre!="auto":data["genres"][genre]=ref
    save(account,data)
    return {"id":ref,"label":item["label"],"genre":genre or item["genre"]}

def selected(account,genre="auto"):
    from studio_modes import GENRES
    if genre not in GENRES:raise ProjectError("FLOW_GENRE_INVALID")
    data=load(account)
    target=data["genres"].get(genre) if genre!="auto" else None
    if target is None:
        target=data["active"]
        # Explicit mappings win; unassigned genre never guesses a different
        # genre's project once multiple projects exist.
        if genre!="auto" and len(data["projects"])>1 and any(g!="auto" for g in data["genres"]):
            raise ProjectError("FLOW_GENRE_HAS_NO_PROJECT_MAPPING")
    item=next((p for p in data["projects"] if p["id"]==target),None)
    return item

def url_for(account,genre="auto"):
    entry=selected(account,genre)
    return project_url(entry["project_id"],entry["tool_id"]) if entry else ""

def is_registered(account,url):
    ref=_parts(url)
    if not ref:return False
    return any((p["project_id"],p["tool_id"])==ref for p in load(account)["projects"])

def summary(account):
    data=load(account)
    return {"active":data["active"],"projects":[{"id":p["id"],"label":p["label"],"genre":p["genre"]} for p in data["projects"]],
            "genres":data["genres"],"open_tabs":tabs(account)}
