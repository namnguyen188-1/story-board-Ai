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
            'expression': '''(() => {
                const im = document.querySelector("script[type=importmap]");
                return im ? im.innerText : "NO_IMPORTMAP";
            })()''',
            'returnByValue': True
        }
    }))
    data = json.loads(ws.recv())
    print('Importmap:', data.get('result', {}).get('result', {}).get('value'))
