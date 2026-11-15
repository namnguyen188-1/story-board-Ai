import ast,hashlib,json,pathlib,urllib.request
from html.parser import HTMLParser
root=pathlib.Path(r"D:\STORYBOARD_AI\studio");cp=root/"runtime/mcp_v2_only_20261108_102327"
class SelectParser(HTMLParser):
 def __init__(self):super().__init__();self.inside=False;self.options=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=="select":self.inside=a.get("id")=="inImageSource"
  if tag=="option" and self.inside:self.options.append(a)
 def handle_endtag(self,tag):
  if tag=="select":self.inside=False
def get(url):
 with urllib.request.urlopen("http://127.0.0.1:8765"+url,timeout=8) as r:return r.read()
h=get("/").decode("utf-8");parser=SelectParser();parser.feed(h)
assert any(x.get("value")=="mcp_v2" and "selected" in x for x in parser.options)
assert not any(x.get("value")=="flowkit" for x in parser.options)
status=json.loads(get("/api/flow/status"))
assert status["provider"]=="mcp_v2" and status["flowkit_required"] is False
js=get("/app.js").decode("utf-8")
assert '"flowkit"' not in js
report={"provider":status["provider"],"connected":status["connected"],"logged_in":status["logged_in"],
"flowkit_required":status["flowkit_required"],"served_default":"mcp_v2","flowkit_option_present":False,
"hashes":{n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in json.loads((cp/"migration_result.json").read_text())["files"]},
"visual_check":"browser extension unavailable; HTTP and Node VM verified",
"live_generation":"not attempted; previous Google unusual-activity denial unresolved"}
(cp/"final_verification.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps({k:v for k,v in report.items() if k!="hashes"}))
