import sys,http.server
from pathlib import Path
sys.path.insert(0,"D:/STORYBOARD_AI/studio")
import web_server
web_server.PRODUCTIONS_DIR=Path("D:/STORYBOARD_AI/studio/scratch")
server=http.server.ThreadingHTTPServer(("127.0.0.1",8766),web_server.StudioRequestHandler)
print("DRAMA_REVIEW_STAGING_HTTP_READY_8766",flush=True)
server.serve_forever()
