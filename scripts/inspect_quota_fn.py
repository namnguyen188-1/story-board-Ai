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
            'expression': 'import("@app").then(m => m.default?.toString() || String(m))',
            'awaitPromise': True,
            'returnByValue': True
        }
    }))
    data = json.loads(ws.recv())
    code = data.get('result', {}).get('result', {}).get('value', '')
    with open('scratch/app_component_code.js', 'w', encoding='utf-8') as out:
        out.write(code)
    print('Saved @app code, length:', len(code))
