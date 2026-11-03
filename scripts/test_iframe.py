import sys
sys.path.insert(0, 'D:/FLOWKIT/app')
from flow_webtool_direct import WebToolAdapter, _evaluate
from websockets.sync.client import connect

adapter = WebToolAdapter('hidden')
frame = adapter._frame()
with connect(frame['webSocketDebuggerUrl']) as ws:
    res = _evaluate(ws, 1, """(async () => {
        try {
            const b = window.__STORYBOARD_MCP__;
            return {
                has_b: !!b,
                keys: b ? Object.keys(b) : [],
                queue: b && b.queue ? b.queue.map(x => ({id: x.id, status: x.status, error: x.errorMessage})) : []
            };
        } catch (e) {
            return {error: String(e)};
        }
    })()""")
    print('MCP state in iframe:', res)
