"""HTTP preflight switches by the requested genre and never starts a costly job on mismatch."""
import json,sys,threading,urllib.request,urllib.error
from http.server import HTTPServer
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0,r"D:\STORYBOARD_AI\studio")
import web_server
from studio_mcp import accounts, projects
request_body={
"series":"MCP Routing Guard QA","episode":1,
"prompt":"Original fictional stoic story about patience and fortitude for family-friendly audience.",
"input_mode":"idea","minutes":0.2,"scene_seconds":30,"language":"English",
"voice_name":"auto","genre":"stoic","visual_style":"auto","region":"auto",
"mode":"live","model":"gemini-3.8-flash","image_provider":"mcp_v2",
"mcp_max_images":1,"mcp_visual_policy":"unique"
}
app=HTTPServer(("127.0.0.1",0),web_server.StudioRequestHandler)
thread=threading.Thread(target=app.serve_forever,daemon=True)
thread.start()
url="http://127.0.0.1:"+str(app.server_address[1])+"/api/produce"
def post():
 req=urllib.request.Request(url,data=json.dumps(request_body).encode("utf-8"),
    method="POST",headers={"Content-Type":"application/json"})
 try:urllib.request.urlopen(req,timeout=6);raise AssertionError("Unexpected job start")
 except urllib.error.HTTPError as exc:return exc.code,json.loads(exc.read())
try:
 target="https://flow.google.com/project/a48a51c1-a8a7-4b54-81a2-8789f7bc4c1f/tool/8fbef6e9-a6e4-4b21-a8b0-0be7a559273d"
 called=[]
 def genre_url(row,genre):
    called.append(genre)
    raise projects.ProjectError("FLOW_GENRE_HAS_NO_PROJECT_MAPPING")
 with patch.object(accounts,"account_tool_url",return_value=target),patch.object(projects,"url_for",side_effect=genre_url):
    code,data=post()
 assert code==409 and data["code"]=="FLOW_GENRE_HAS_NO_PROJECT_MAPPING",(code,data)
 assert called==["stoic"],called
 print("HTTP_UNMAPPED_GENRE_FAILS_BEFORE_GEMINI_PASS",flush=True)
 called.clear()
 def browser_guard(row,tool_url=None,*,allow_duplicate_for_isolated_job=False):
    assert allow_duplicate_for_isolated_job is True
    called.append(tool_url)
    raise accounts.AccountError("STORYBOARD_PRIVATE_WEB_TOOL_NOT_OPEN")
 with patch.object(accounts,"account_tool_url",return_value=target),patch.object(projects,"url_for",return_value=target),patch.object(accounts,"require_production_browser",side_effect=browser_guard):
    code,data=post()
 assert code==409 and data["code"]=="STORYBOARD_PRIVATE_WEB_TOOL_NOT_OPEN",(code,data)
 assert called==[target],called
 assert web_server.job_status["running"] is False
 print("HTTP_SELECTED_EXACT_PROJECT_TOOL_FAILFAST_PASS",flush=True)
finally:
 app.shutdown()
 app.server_close()
print("NO_REMOTE_IMAGE_OR_GEMINI_JOB_SUBMITTED_PASS",flush=True)
