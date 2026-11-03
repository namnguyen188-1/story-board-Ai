import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'D:/FLOWKIT/app')
from flow_webtool_direct import WebToolAdapter, _evaluate
from websockets.sync.client import connect
import json, time

adapter = WebToolAdapter('hidden')
frame = adapter._frame()
with connect(frame['webSocketDebuggerUrl'], open_timeout=5, max_size=10*1024*1024) as ws:
    # 1. Clean queue
    clean_res = _evaluate(ws, 1, """(() => {
        const b = window.__STORYBOARD_MCP__;
        if (!b || b.isProcessing) return {error: 'busy'};
        b.capabilities.clearQueue();
        return {ok: true, queueLen: b.queue.length};
    })()""")
    print('Clean queue:', clean_res)

    # 2. Add 1 image item
    prompt = "Ancient marble bust of Marcus Aurelius in museum, dramatic lighting, 8k"
    add_res = _evaluate(ws, 2, f"""(() => {{
        const b = window.__STORYBOARD_MCP__;
        const arr = b.capabilities.addToQueue([{{
            title: 'Test Image',
            text: {json.dumps(prompt)},
            assetKind: 'image'
        }}]);
        return {{ok: true, added: arr}};
    }})()""")
    shot_id = add_res['added'][0]['id']
    print('Added shot_id:', shot_id)

    # 3. Trigger startImageProduction
    trigger_res = _evaluate(ws, 3, """(() => {
        const b = window.__STORYBOARD_MCP__;
        b.capabilities.startImageProduction({approved: true, maxImages: 1});
        return {started: true};
    })()""")
    print('Trigger startImageProduction:', trigger_res)

    # 4. Poll for completion (up to 45 seconds)
    print('Polling for result of shot:', shot_id)
    for _ in range(30):
        time.sleep(2)
        st = _evaluate(ws, 4, f"""(() => {{
            const b = window.__STORYBOARD_MCP__;
            const item = b.queue.find(x => x.id === {json.dumps(shot_id)});
            if (!item) return {{missing: true}};
            return {{
                id: item.id,
                status: item.status,
                hasBase64: !!item.rawBase64,
                base64Len: item.rawBase64 ? item.rawBase64.length : 0,
                error: item.errorMessage
            }};
        }})()""")
        print('Status:', st)
        if st.get('status') == 'completed':
            print('SUCCESS! Image generated with length:', st.get('base64Len'))
            break
        if st.get('status') == 'error':
            print('ERROR:', st.get('error'))
            break
