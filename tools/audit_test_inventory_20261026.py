# -*- coding: utf-8 -*-
"""Read-only test inventory for live Storyboard AI, no API usage."""
from pathlib import Path
import ast, re, json, sys
ROOT=Path(r"D:\STORYBOARD_AI\studio")
tests=ROOT/"tests"
items=[]
for file in sorted(tests.glob("test*.py")):
    txt=file.read_text(encoding="utf-8-sig",errors="replace")
    try:
        mod=ast.parse(txt)
        tests_f=[x.name for x in mod.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef)) and x.name.startswith("test_")]
        test_classes=[x.name for x in mod.body if isinstance(x,ast.ClassDef) and ("Test" in x.name)]
        mains=any(isinstance(x,ast.If) and isinstance(x.test,ast.Compare) and
            isinstance(x.test.left,ast.Name) and x.test.left.id=="__name__" for x in mod.body)
        top_level_calls=[ast.unparse(x.value)[:80] for x in mod.body if isinstance(x,ast.Expr) and isinstance(x.value,ast.Call)]
        syntax_ok=True
    except SyntaxError as e:
        tests_f=[];test_classes=[];mains=False;top_level_calls=[];syntax_ok=False
    items.append({"file":file.name,"functions":len(tests_f),"classes":test_classes,
        "main":mains,"syntax":syntax_ok,"top_level_calls":top_level_calls[:3],
        "possible_network":bool(re.search(r"(requests\.(get|post)|httpx|urllib\.request|muse_cli|generate_content|live_api|upload_video|publish_video)",txt,re.I)),
        "safe_name":bool(re.search(r"(offline|no_api|no_paid|mock|cached|guard|metadata|schema|script|skill)",file.stem,re.I))})
out={"count":len(items),"tests":items}
Path(r"D:\STORYBOARD_AI\studio\diagnostics\audit_inventory_20261026.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
print("TOTAL",len(items),"MAIN",sum(t["main"] for t in items),"FUNCTION_TESTS",sum(t["functions"] for t in items),"SYNTAX_ERRORS",[t["file"] for t in items if not t["syntax"]])
for t in items:
    if t["main"] and t["safe_name"]:
        print("SAFE_ENTRY",t["file"],"network_signal",t["possible_network"],"top",str(t["top_level_calls"])[:100])
