import sys, json
sys.path.insert(0, 'D:/FLOWKIT/app')
from flow_webtool_direct import WebToolAdapter, _evaluate
from websockets.sync.client import connect

adapter = WebToolAdapter('hidden')
f = adapter._frame()

wrapper_js = r"""(() => {
  const b = window.__STORYBOARD_MCP__;
  if (!b || !b.capabilities) return 'NO_MCP';
  
  const origUpdateItem = b.capabilities.updateItem;
  
  b.capabilities.startImageProduction = async (options) => {
    const { Flow } = await import('flow-sdk');
    const queue = b.queue || [];
    const pendingImages = queue.filter(x => x.assetKind === 'image' && x.status === 'pending');
    if (!pendingImages.length) return { success: true, processed: 0 };
    
    b.isProcessing = true;
    const models = [
      b.config?.imageModel || '🍌 Nano Banana 2.1',
      '🍌 Nano Banana 2.1',
      '🍌 Nano Banana 2 Lite',
      '🍌 Nano Banana Pro'
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
          console.log(`[FLOWKIT_ROBUST] Generating image ${item.id} with ${m}...`);
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
            console.log(`[FLOWKIT_ROBUST] Successfully generated with ${m}!`);
            break;
          }
        } catch (err) {
          lastErr = err;
          console.warn(`[FLOWKIT_ROBUST] Model ${m} error:`, err?.message || err);
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
  return 'WRAPPED_SUCCESS';
})()"""

with connect(f['webSocketDebuggerUrl'], open_timeout=5) as ws:
    res = _evaluate(ws, 125, wrapper_js)
    print('Wrapper injection result:', res)
