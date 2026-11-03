"""HTTP no-credit regression: auto detected genre falls back to selected known project.
Never creates image or production files.
"""
import sys,threading,urllib.request,urllib.error,json
from http.server import HTTPServer
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0,r"D:\STORYBOARD_AI\studio")
import web_server
from studio_mcp import accounts,projects,production_tab
target="https://flow.google.com/project/7a7f7f89-c38d-4237-b4aa-ba499acd7507/tool/642784b8-d39f-4e7b-b168-fe6218bbc45b"
body={
"series":"Auto Genre Fallback No Paid QA 20261013",
"episode":1,"prompt":"A fictional peaceful riverside village at sunrise, a bridge and trees.",
"input_mode":"idea","minutes":0.1,"scene_seconds":8,
"language":"English","voice_name":"auto","genre":"auto",
"visual_style":"hand_color","region":"US","mode":"live",
"model":"gemini-3.8-flash","image_provider":"mcp_v2",
"mcp_model_index":1,"mcp_max_images":1,"mcp_visual_policy":"unique"
}
app=HTTPServer(("127.0.0.1",0),web_server.StudioRequestHandler)
thread=threading.Thread(target=app.serve_forever,daemon=True)
thread.start()
url="http://127.0.0.1:"+str(app.server_address[1])+"/api/produce"
calls=[]
def route(row,genre):
 calls.append(("url",genre))
 if genre=="documentary":raise projects.ProjectError("FLOW_GENRE_HAS_NO_PROJECT_MAPPING")
 assert genre=="auto",genre
 return target
def guard(row,tool_url=None,**kwargs):
 calls.append(("guard",tool_url))
 assert kwargs.get("allow_duplicate_for_isolated_job") is True
def prepare(row,tool_url):
 calls.append(("prepare",tool_url))
 raise production_tab.ProductionTabError("EXPECTED_NO_PAID_CANARY_BLOCK")
try:
 with patch.object(accounts,"account_tool_url",return_value=target),\
      patch.object(projects,"url_for",side_effect=route),\
      patch.object(accounts,"require_production_browser",side_effect=guard),\
      patch.object(production_tab,"prepare",side_effect=prepare):
  req=urllib.request.Request(url,data=json.dumps(body).encode(),
    headers={"Content-Type":"application/json"},method="POST")
  try:urllib.request.urlopen(req,timeout=12);raise AssertionError("unexpected paid production")
  except urllib.error.HTTPError as err:code=err.code;result=json.loads(err.read())
 assert code==409 and result["code"]=="MCP_PRODUCTION_SESSION_NOT_READY",(code,result)
 assert calls==[("url","documentary"),("url","auto"),
   ("guard",target),("prepare",target)],calls
 assert not web_server.job_status["running"]
 print("AUTO_GENRE_FALLBACK_TO_SELECTED_V2_PROJECT_BEFORE_SPEND_PASS",flush=True)
finally:
 app.shutdown();app.server_close()
