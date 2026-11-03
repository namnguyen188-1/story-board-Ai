import sys, json
sys.path.insert(0, 'D:/FLOWKIT/app')
from flow_webtool_direct import WebToolAdapter
from websockets.sync.client import connect

adapter = WebToolAdapter('hidden')
f = adapter._frame()
with connect(f['webSocketDebuggerUrl'], open_timeout=5) as ws:
    ws.send(json.dumps({
        'id': 1,
        'method': 'Runtime.evaluate',
        'params': {
            'expression': '''(async () => {
                const { Flow } = await import("flow-sdk");
                const results = {};
                for (const m of ["🍌 Nano Banana 2 Lite", "🍌 Nano Banana 2.1", "🍌 Nano Banana Pro"]) {
                    try {
                        const res = await Flow.generate.image({
                            prompt: "test simple sphere on white background",
                            aspectRatio: "16:9",
                            modelDisplayName: m
                        });
                        results[m] = { success: !!res?.mediaId, mime: res?.mimeType };
                    } catch (e) {
                        results[m] = { success: false, error: String(e?.message || e) };
                    }
                }
                return results;
            })()''',
            'awaitPromise': True,
            'returnByValue': True
        }
    }))
    data = json.loads(ws.recv())
    print('Model test results:', json.dumps(data.get('result', {}).get('result', {}).get('value'), indent=2))
