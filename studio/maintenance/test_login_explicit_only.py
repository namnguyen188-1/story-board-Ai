"""No Chrome launch when creating/selecting accounts; only explicit login."""
import ast,sys
from pathlib import Path
root=Path(sys.argv[1])
src=(root/"web_server.py").read_text(encoding="utf-8")
tree=ast.parse(src)
def eq_action(node,action):
    return isinstance(node,ast.If) and isinstance(node.test,ast.Compare) and \
        any(isinstance(x,ast.Constant) and x.value==action for x in node.test.comparators)
def calls(node,name):
    return [x for x in ast.walk(ast.Module(body=node.body,type_ignores=[]))
            if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id==name]
create=[x for x in ast.walk(tree) if eq_action(x,"create") and
        any(isinstance(c,ast.Call) and isinstance(c.func,ast.Name) and c.func.id=="create"
            for c in ast.walk(ast.Module(body=x.body,type_ignores=[])))]
login=[x for x in ast.walk(tree) if eq_action(x,"login") and calls(x,"open_login")]
assert len(create)==1 and not calls(create[0],"open_login"),"Create still opens Chrome"
assert login,"No explicit login action"
js=(root/"web"/"app.js").read_text(encoding="utf-8")
html=(root/"web"/"index.html").read_text(encoding="utf-8")
assert "Chỉ khi bạn bấm Đăng nhập / Hiện Google Flow" in js
assert "btnMcpAddAccount" in html and "Thêm tài khoản" in html
print("EXPLICIT_LOGIN_ONLY_PASS; CREATE_SELECT_NO_POPUP")
