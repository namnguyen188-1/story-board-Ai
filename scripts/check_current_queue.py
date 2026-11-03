import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'D:/FLOWKIT/app')
from flow_webtool_direct import WebToolAdapter, _evaluate
from websockets.sync.client import connect

adapter = WebToolAdapter('hidden')
frame = adapter._frame()
with connect(frame['webSocketDebuggerUrl'], open_timeout=5, max_size=10*1024*1024) as ws:
    res = _evaluate(ws, 1, """(() => {
        const b = window.__STORYBOARD_MCP__;
        return {
            isProcessing: b.isProcessing,
            queue: b.queue.map(x => ({
                id: x.id,
                status: x.status,
                hasBase64: !!x.rawBase64,
                base64Len: x.rawBase64 ? x.rawBase64.length : 0,
                error: x.errorMessage,
                progress: x.progressMessage
            }))
        };
    })()""")
    print('Current queue:', res)
