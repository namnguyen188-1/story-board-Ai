from pathlib import Path

p = Path("D:/FLOWKIT/app/flow_webtool_jobs.py")
txt = p.read_text(encoding="utf-8")

old_start_marker = 'start = r"""(()=>{const b=window.__STORYBOARD_MCP__;\n              if(!b||typeof b.capabilities?.addToQueue!=='
assert old_start_marker in txt, "Marker not found in flow_webtool_jobs.py"

# Find start definition block
start_idx = txt.find('start = r"""(()=>{const b=window.__STORYBOARD_MCP__;')
end_idx = txt.find('.replace(\n                  "ID", json.dumps(shot_id))', start_idx)
assert start_idx != -1 and end_idx != -1

new_start_code = r'''start = r"""(()=>{const b=window.__STORYBOARD_MCP__;
              if(!b||typeof b.capabilities?.addToQueue!=='function') return 'NO_CAPABILITIES';
              
              if (!b.capabilities.__robust_wrapped) {
                const origUpdateItem = b.capabilities.updateItem;
                b.capabilities.startImageProduction = async (options) => {
                  const { Flow } = await import('flow-sdk');
                  const queue = b.queue || [];
                  const pendingImages = queue.filter(x => x.assetKind === 'image' && x.status === 'pending');
                  if (!pendingImages.length) return { success: true, processed: 0 };
                  
                  b.isProcessing = true;
                  const models = [
                    b.config?.imageModel || '\ud83c\udf4c Nano Banana 2.1',
                    '\ud83c\udf4c Nano Banana 2.1',
                    '\ud83c\udf4c Nano Banana 2 Lite',
                    '\ud83c\udf4c Nano Banana Pro'
                  ];
                  const uniqueModels = [...new Set(models)];
                  
                  for (const item of pendingImages) {
                    item.status = 'generating';
                    if (typeof origUpdateItem === 'function') {
                      origUpdateItem(item.id, { status: 'generating' });
                    }
                    
                    let succeeded = false;
                    let lastErr = null;
                    let usedModel = null;
                    
                    for (const m of uniqueModels) {
                      try {
                        const res = await Flow.generate.image({
                          prompt: item.promptText,
                          modelDisplayName: m,
                          aspectRatio: item.parsed?.aspectRatio || '16:9'
                        });
                        if (res && res.base64 && res.mediaId) {
                          item.status = 'completed';
                          item.rawBase64 = res.base64;
                          item.mimeType = res.mimeType || 'image/jpeg';
                          item.mediaId = res.mediaId;
                          item.modelUsed = m;
                          item.completedAt = Date.now();
                          
                          const bytes = Uint8Array.from(atob(res.base64), c => c.charCodeAt(0));
                          const blob = new Blob([bytes], { type: res.mimeType || 'image/jpeg' });
                          item.imageUrl = URL.createObjectURL(blob);
                          
                          if (typeof origUpdateItem === 'function') {
                            origUpdateItem(item.id, {
                              status: 'completed',
                              imageUrl: item.imageUrl,
                              rawBase64: res.base64,
                              mimeType: res.mimeType || 'image/jpeg',
                              mediaId: res.mediaId,
                              modelUsed: m,
                              completedAt: item.completedAt
                            });
                          }
                          succeeded = true;
                          usedModel = m;
                          break;
                        }
                      } catch (err) {
                        lastErr = err;
                        continue;
                      }
                    }
                    
                    if (!succeeded) {
                      item.status = 'error';
                      item.errorMessage = String(lastErr?.message || 'ALL_MODELS_FAILED');
                      if (typeof origUpdateItem === 'function') {
                        origUpdateItem(item.id, {
                          status: 'error',
                          errorMessage: item.errorMessage
                        });
                      }
                    }
                  }
                  b.isProcessing = false;
                  return { success: true };
                };
                b.capabilities.__robust_wrapped = true;
              }
              
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
              b.queue = b.queue || [];
              if (!b.queue.some(x => x.id === ID)) {
                b.queue.push(created);
              }
              setTimeout(() => {
                try {
                  b.capabilities.startImageProduction({ approved: true, maxImages: 10 });
                } catch(e) {
                  console.error('startImageProduction error:', e);
                }
              }, 50);
              return 'STARTED';})()"""'''

txt = txt[:start_idx] + new_start_code + txt[end_idx:]
p.write_text(txt, encoding="utf-8")
print("Successfully permanently patched flow_webtool_jobs.py with multi-model auto-fallback!")
