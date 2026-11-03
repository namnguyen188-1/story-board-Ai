import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'D:/FLOWKIT/app')
from flow_webtool_direct import WebToolAdapter, _evaluate
from websockets.sync.client import connect

adapter = WebToolAdapter('hidden')
frame = adapter._frame()
with connect(frame['webSocketDebuggerUrl'], open_timeout=5, max_size=10*1024*1024) as ws:
    res = _evaluate(ws, 1, """(async () => {
        const b = window.__STORYBOARD_MCP__;
        try {
            const out = await b.capabilities.startImageProduction({approved: true, maxImages: 1});
            return {out: out};
        } catch (e) {
            return {err: String(e)};
        }
    })()""")
    print('startImageProduction result:', res)
