import sys, json, base64
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
                const parsed = JSON.parse(im.innerText);
                return parsed.imports["@app"] || parsed.imports["app"];
            })()''',
            'returnByValue': True
        }
    }))
    data = json.loads(ws.recv())
    data_url = data.get('result', {}).get('result', {}).get('value')
    if data_url and ',' in data_url:
        b64 = data_url.split(',', 1)[1]
        decoded = base64.b64decode(b64).decode('utf-8', errors='ignore')
        print('Decoded length:', len(decoded))
        idx = decoded.find('isDefiniteQuotaError')
        if idx != -1:
            print('isDefiniteQuotaError found:')
            print(decoded[max(0, idx-50):min(len(decoded), idx+500)])
        else:
            print('isDefiniteQuotaError not found')
