"""Isolated per-account multiple Flow projects and genres; no browser or paid requests."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import sys,json
sys.path.insert(0,r"D:\STORYBOARD_AI\studio")
from studio_mcp import projects as p
from studio_mcp import accounts as a
P1="a48a51c1-a8a7-4b54-81a2-8789f7bc4c1f"
P2="79dfa39d-8ec4-4ab7-aaa2-2be03bd1bdd0"
T1="8fbef6e9-a6e4-4b21-a8b0-0be7a559273d"
T2="69da86fb-6c79-43d2-a387-ef47b0fda4db"
refs=[{"id":P1+":"+T1,"project_id":P1,"tool_id":T1},
      {"id":P2+":"+T2,"project_id":P2,"tool_id":T2}]
with TemporaryDirectory(prefix="flow_project_registry_a_") as first,TemporaryDirectory(prefix="flow_project_registry_b_") as second:
    a1={**a.active_account(),"state_dir":first}
    a2={**a.active_account(),"state_dir":second}
    assert p.load(a1)["projects"]==[]
    with patch.object(p,"tabs",return_value=refs),patch.object(a,"_require_idle",return_value=None):
        s1=p.register(a1,refs[0]["id"],"Khắc kỷ ES","stoic")
        s2=p.register(a1,refs[1]["id"],"Drama HOA","family_drama")
        assert len(p.load(a1)["projects"])==2
        assert p.url_for(a1,"stoic")==p.project_url(P1,T1)
        assert p.url_for(a1,"family_drama")==p.project_url(P2,T2)
        assert p.selected(a1,"stoic")["label"]=="Khắc kỷ ES"
        p.choose(a1,refs[0]["id"],"auto")
        assert p.url_for(a1,"auto")==p.project_url(P1,T1)
        assert p.url_for(a1,"family_drama")==p.project_url(P2,T2)
        assert p.selected(a1,"auto")["label"]=="Khắc kỷ ES"
        assert p.is_registered(a1,p.project_url(P1,T1))
        assert not p.is_registered(a1,p.project_url(P1,T2))
        assert p.load(a2)["projects"]==[], "Other account must remain isolated"
        for ref,genre in [("bad","western"),(P1+":"+T2,"western")]:
            try:p.register(a1,ref,"Different","western");raise AssertionError("Unseen Flow project allowed")
            except p.ProjectError as exc:assert "FLOW_PROJECT_MUST_BE_OPEN" in str(exc)
        try:p.url_for(a1,"western");raise AssertionError("Missing genre mapping fell back silently")
        except p.ProjectError as exc:assert "FLOW_GENRE_HAS_NO_PROJECT_MAPPING" in str(exc)
        try:p.choose(a1,P1+":"+T2,"stoic");raise AssertionError("Unknown project selected")
        except p.ProjectError as exc:assert "NOT_REGISTERED" in str(exc)
        stored=json.loads(Path(first,"studio_flow_projects.json").read_text(encoding="utf-8"))
        assert "cookie" not in json.dumps(stored).lower()
        assert "token" not in json.dumps(stored).lower()
        assert "password" not in json.dumps(stored).lower()
        assert len(stored["genres"])==2
    print("MULTI_ACCOUNT_ISOLATION_PASS",flush=True)
    print("STOIC_DRAMA_DISTINCT_PROJECTS_AUTO_ROUTE_PASS",flush=True)
    print("PROJECT_SWITCH_EXACT_ID_NO_FALLBACK_PASS",flush=True)
    print("NO_BROWSER_OR_PAID_REQUESTS_PASS",flush=True)
