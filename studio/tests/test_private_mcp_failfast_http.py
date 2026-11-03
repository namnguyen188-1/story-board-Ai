"""HTTP regression: mock absent URL in a separate in-process server; NEVER launch a live job."""
import json,sys,threading,urllib.error,urllib.request
from pathlib import Path
from http.server import HTTPServer
from unittest.mock import patch
studio=Path(r"D:\STORYBOARD_AI\studio")
sys.path.insert(0,str(studio))
from studio_mcp import accounts
import web_server
from web_server import StudioRequestHandler
server=HTTPServer(("127.0.0.1",0),StudioRequestHandler)
worker=threading.Thread(target=server.serve_forever,daemon=True)
body={"series":"Private MCP Safety Test","episode":1,"input_mode":"idea",
      "prompt":"A fictional mountain journey with calm narrator.",
      "language":"Vietnamese","voice_name":"auto","mode":"live",
      "visual_style":"auto","genre":"auto","region":"auto",
      "image_provider":"mcp_v2","mcp_max_images":1,"scene_seconds":10,"minutes":0.2}
try:
    with patch.object(accounts,"account_tool_url",return_value=""),patch.object(web_server.subprocess,"Popen",side_effect=AssertionError("Live job launch forbidden by mock")):
        worker.start()
        request=urllib.request.Request(
            "http://127.0.0.1:"+str(server.server_address[1])+"/api/produce",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type":"application/json"},method="POST")
        try:
            urllib.request.urlopen(request,timeout=5)
            raise AssertionError("Must fail closed without Studio tool URL")
        except urllib.error.HTTPError as e:
            payload=json.loads(e.read())
            assert e.code==409 and payload.get("code")=="PRIVATE_MCP_TOOL_URL_REQUIRED",(e.code,payload)
    print("PRIVATE_MCP_NO_SPEND_NO_JOB_E2E_PASS",flush=True)
finally:
    server.shutdown()
    server.server_close()
