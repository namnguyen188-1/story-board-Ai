import re
from pathlib import Path

p = Path("D:/FLOWKIT/app/flow_webtool_jobs.py")
txt = p.read_text(encoding="utf-8")

old_block = '''        with connect(frame["webSocketDebuggerUrl"], open_timeout=5, max_size=2*1024*1024) as ws:
            start = r"""(()=>{const b=window.__STORYBOARD_MCP__;
              if(!b) return 'NO_MCP';
              b.queue = b.queue || [];
              const shot = {
                id: ID,
                title: 'FlowKit image ' + ID.slice(0, 20),
                assetKind: 'image',
                aspectRatio: ASPECT,
                status: 'generating'
              };
              b.queue.push(shot);
              (async()=>{
                try{
                  const {Flow}=await import('flow-sdk');
                  const candidates = [
                    TARGET_MODEL,
                    '\\ud83c\\udf4c Nano Banana 2 Lite',
                    '\\ud83c\\udf4c Nano Banana 2.1',
                    '\\ud83c\\udf4c Nano Banana Pro'
                  ];
                  const models = [...new Set(candidates)];
                  let res = null;
                  let lastErr = null;
                  let usedModel = null;
                  for (const m of models) {
                    try {
                      res = await Flow.generate.image({
                        prompt: PROMPT,
                        aspectRatio: ASPECT,
                        modelDisplayName: m
                      });
                      if (res && res.base64) {
                        usedModel = m;
                        break;
                      }
                    } catch (err) {
                      lastErr = err;
                      const msg = String(err?.message || err);
                      console.warn('FlowKit model ' + m + ' failed: ' + msg);
                      continue;
                    }
                  }
                  if(res&&res.base64){
                    shot.status='completed';
                    shot.rawBase64=res.base64;
                    shot.mimeType=res.mimeType||'image/jpeg';
                    shot.mediaId=res.mediaId;
                    shot.modelUsed=usedModel;
                    shot.completedAt=Date.now();
                  }else{
                    shot.status='error';
                    shot.errorMessage=String(lastErr?.message||'NO_IMAGE_DATA_RETURNED');
                  }
                }catch(err){
                  shot.status='error';
                  shot.errorMessage=String(err?.message||err);
                }
              })();
              return 'STARTED';})()""".replace(
                  "ID", json.dumps(shot_id)).replace("PROMPT", json.dumps(prompt)).replace("ASPECT", json.dumps(aspect_ratio)).replace("TARGET_MODEL", json.dumps(target_model_display))
            response = _evaluate(ws, 114, start)
            if response != "STARTED":
                raise WebToolError("WEBTOOL_IMAGE_START_OUTCOME_UNKNOWN", 409)
        return {"shot_id": shot_id, "reused": False, "state": "start_clicked"}'''

new_block = '''        with connect(frame["webSocketDebuggerUrl"], open_timeout=5, max_size=2*1024*1024) as ws:
            start = r"""(()=>{const b=window.__STORYBOARD_MCP__;
              if(!b||typeof b.capabilities?.addToQueue!=='function'||typeof b.capabilities?.startImageProduction!=='function') return 'NO_CAPABILITIES';
              const arr = b.capabilities.addToQueue([{
                title: 'FlowKit image ' + ID.slice(0, 20),
                text: PROMPT,
                assetKind: 'image'
              }]);
              if (!arr || !arr.length) return 'ADD_FAILED';
              const created = arr[0];
              created.id = ID;
              if (created.parsed) {
                created.parsed.aspectRatio = ASPECT;
              }
              setTimeout(() => {
                try {
                  b.capabilities.startImageProduction({ approved: true, maxImages: 10 });
                } catch(e) {
                  console.error('startImageProduction error:', e);
                }
              }, 50);
              return 'STARTED';})()""".replace(
                  "ID", json.dumps(shot_id)).replace("PROMPT", json.dumps(prompt)).replace("ASPECT", json.dumps(aspect_ratio))
            response = _evaluate(ws, 114, start)
            if response != "STARTED":
                raise WebToolError("WEBTOOL_IMAGE_START_OUTCOME_UNKNOWN: " + str(response), 409)
        return {"shot_id": shot_id, "reused": False, "state": "start_clicked"}'''

assert old_block in txt, "Pattern old_block not found in flow_webtool_jobs.py"
txt = txt.replace(old_block, new_block)
p.write_text(txt, encoding="utf-8")
print("Successfully patched _submit_image_capability in flow_webtool_jobs.py")
