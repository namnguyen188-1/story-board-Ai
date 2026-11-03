import sys
sys.path.insert(0, 'D:/FLOWKIT/app')
from flow_webtool_direct import WebToolAdapter, _evaluate
from websockets.sync.client import connect

adapter = WebToolAdapter('hidden')
frame = adapter._frame()
with connect(frame['webSocketDebuggerUrl']) as ws:
    res = _evaluate(ws, 1, """(() => {
        const b = window.__STORYBOARD_MCP__;
        return {
            addToQueueStr: String(b.capabilities.addToQueue),
            startImageProductionStr: String(b.capabilities.startImageProduction)
        };
    })()""")
    print('addToQueue implementation:', res.get('addToQueueStr')[:300])
    print('startImageProduction implementation:', res.get('startImageProductionStr')[:300])
