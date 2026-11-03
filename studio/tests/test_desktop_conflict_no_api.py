"""No-API localhost safety regression for existing-episode errors."""
import sys,json,threading,urllib.request,urllib.error
from pathlib import Path
STUDIO=Path(r"D:\STORYBOARD_AI\studio")
sys.path.insert(0,str(STUDIO))
from http.server import HTTPServer
from web_server import StudioRequestHandler
server=HTTPServer(("127.0.0.1",0),StudioRequestHandler)
thread=threading.Thread(target=server.serve_forever,daemon=True)
thread.start()
url="http://127.0.0.1:"+str(server.server_address[1])+"/api/produce"
def conflict(provider,prompt):
    data={"series":"Whiteboard Chronicles","episode":1,
          "prompt":prompt,"minutes":2,"scene_seconds":30,"language":"English",
          "size":"1280x720","workers":1,"mode":"live","model":"gemini-3.8-flash",
          "image_provider":provider,"mcp_model_index":1,"mcp_max_images":4}
    payload=json.dumps(data).encode()
    request=urllib.request.Request(url,data=payload,headers={"Content-Type":"application/json"},method="POST")
    try:
        urllib.request.urlopen(request,timeout=5)
    except urllib.error.HTTPError as e:
        body=json.loads(e.read().decode())
        assert e.code==409 and body["code"]=="EPISODE_CONFLICT",(e.code,body)
        assert body["next_episode"]>=2 and "Dữ liệu cũ" in body["error"]
        print("EARLY_EPISODE_CONFLICT_PASS",provider,"next",body["next_episode"],flush=True)
    else:
        raise AssertionError("Mismatched provider or plan must reject WITHOUT creating job")
conflict("mcp_v2","Original fictional story about a city frozen in time")
conflict("v2_tuanstor","A completely unrelated test premise")
server.shutdown()
print("NO_API_TESTS_PASS",flush=True)
