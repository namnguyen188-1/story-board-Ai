"""Reliable one-shot production via Web Tool's own import-and-render UI.







This is a compatibility adapter for the *working* Web Tool.



The hidden Web Tool MUST expose a native v1 submit method to be headless;



do not mistake a readable queue for production capabilities.



"""



import hashlib



import json



import os



from pathlib import Path



import threading



import time







from websockets.sync.client import connect



from common import STATE, settings
from flow_models import image_model_key, image_model_display, video_model_display



from flow_webtool_direct import WebToolAdapter, WebToolError, _evaluate, _LOCK







_LEDGER = STATE / "webtool_jobs_ledger.json"











def _load():



    if not _LEDGER.is_file():



        return {}



    return json.loads(_LEDGER.read_text(encoding="utf-8"))











def _commit(items):



    tmp = _LEDGER.with_suffix(".tmp")



    tmp.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")



    os.replace(tmp, _LEDGER)











def receipt_for(request_id):



    return _load().get(request_id)











class WebToolProduction:



    def __init__(self, mode="active"):



        self.adapter = WebToolAdapter(mode)



        self.mode = mode







    def submit(self, request_id, prompt, aspect_ratio="9:16", kind="video",
               image_model="NANO_BANANA_PRO", video_model="OMNI_1_2_FLASH", resolution="720p"):
        if kind not in ("video", "image"):
            raise WebToolError("WEBTOOL_UNSUPPORTED_MEDIA_KIND", 422)
        if aspect_ratio not in ("9:16", "16:9"):
            raise WebToolError("WEBTOOL_INVALID_ASPECT_RATIO", 422)
        if resolution not in ("360p", "720p"):
            raise WebToolError("WEBTOOL_INVALID_RESOLUTION", 422)
        if not isinstance(prompt, str) or not 10 <= len(prompt) <= 16000:
            raise WebToolError("WEBTOOL_INVALID_PROMPT", 422)
        base = {"prompt": prompt, "aspect_ratio": aspect_ratio, "kind": kind, "mode": self.mode}
        def digest(value):
            return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
        legacy_fingerprints = {digest(base)}
        try:
            if kind == "image":
                image_model = image_model_key(image_model)
                legacy_fingerprints.add(digest({**base, "image_model": image_model}))
                model = image_model_display(image_model)
            else:
                model = video_model_display(video_model)
        except ValueError as error:
            raise WebToolError("WEBTOOL_UNSUPPORTED_IMAGE_MODEL" if kind == "image" else
                               "WEBTOOL_UNSUPPORTED_VIDEO_MODEL", 422) from error
        fingerprint = digest({**base, "model_display": model, "resolution": resolution})
        with _LOCK:
            ledger = _load()
            old = ledger.get(request_id)
            if old:
                legacy_match = "model_display" not in old and old.get("fingerprint") in legacy_fingerprints
                if old.get("fingerprint") != fingerprint and not legacy_match:
                    raise WebToolError("WEBTOOL_IDEMPOTENCY_CONFLICT", 409)
                if old.get("shot_id"):
                    return {"shot_id": old["shot_id"], "reused": True, "state": old["state"]}
                raise WebToolError("WEBTOOL_SUBMISSION_OUTCOME_UNKNOWN_NO_RESUBMIT", 409)
            current = self.adapter.status()
            if current.get("processing"):
                raise WebToolError("WEBTOOL_IS_PROCESSING", 409)
            if current.get("native_submit"):
                return self._submit_native(request_id, prompt, aspect_ratio, fingerprint, ledger,
                                           kind=kind, model_display=model, resolution=resolution)
            if kind == "image" and current.get("capability_enqueue"):
                return self._submit_image_capability(request_id, prompt, aspect_ratio, fingerprint, ledger,
                                                     image_model=image_model)
            if current.get("capability_enqueue"):
                return self._submit_capability(request_id, prompt, aspect_ratio, fingerprint, ledger)
            raise WebToolError("WEBTOOL_UPGRADE_REQUIRED", 503)







    def _submit_native(self, request_id, prompt, aspect_ratio, fingerprint, ledger,
                       kind="video", model_display="Omni 1.2 Flash", resolution="720p"):
        ledger[request_id] = {"mode": self.mode, "fingerprint": fingerprint,
                              "kind": kind, "model_display": model_display,
                              "resolution": resolution, "aspect_ratio": aspect_ratio,
                              "state": "native_outcome_unknown", "shot_id": None,
                              "started_at": time.time()}
        _commit(ledger)
        frame = self.adapter._frame()
        params = {"requestId": request_id, "approved": True, "prompt": prompt, "kind": kind,
                  "aspectRatio": aspect_ratio, "durationSeconds": 8,
                  "modelDisplayName": model_display, "resolution": resolution}
        js = r"""(async()=>{const b=window.__STORYBOARD_MCP__?.v1;
          if(!b||typeof b.submit!=='function')return {error:'NATIVE_BRIDGE_MISSING'};
          return await b.submit(PARAMS)})()""".replace("PARAMS", json.dumps(params, ensure_ascii=False))
        with connect(frame["webSocketDebuggerUrl"], open_timeout=5) as ws:
            response = _evaluate(ws, 100, js)
        if not isinstance(response, dict) or not response.get("accepted") or not response.get("jobId"):
            code = response.get("error") if isinstance(response, dict) else None
            raise WebToolError("WEBTOOL_NATIVE_SUBMIT_REJECTED:" + str(code or "OUTCOME_UNKNOWN"), 409)
        shot_id = str(response["jobId"])
        ledger[request_id].update(shot_id=shot_id, state="start_clicked")
        _commit(ledger)
        return {"shot_id": shot_id, "reused": bool(response.get("reused")), "state": "start_clicked"}







    def _submit_capability(self, request_id, prompt, aspect_ratio, fingerprint, ledger):



        """Use the copied Web Tool's existing headless React capabilities.



        Never click hidden UI and never render its sample/pending queue items.



        """



        ledger[request_id] = {"mode": self.mode, "fingerprint": fingerprint,



                              "aspect_ratio": aspect_ratio,



                              "shot_id": None, "state": "enqueue_outcome_unknown",



                              "started_at": time.time()}



        _commit(ledger)



        frame = self.adapter._frame()











        with connect(frame["webSocketDebuggerUrl"], open_timeout=5, max_size=2*1024*1024) as ws:



            payload = [{"title": "FlowKit " + request_id[:24],



                        "text": prompt, "assetKind": "video"}]



            js = r"""(()=>{const b=window.__STORYBOARD_MCP__;



              if(!b||b.isProcessing||typeof b.capabilities?.addToQueue!=='function'



               ||typeof b.capabilities?.retryItem!=='function'



               ||b.queue.some(x=>x.status==='generating'))return {error:'WEBTOOL_NOT_READY'};



              const arr=b.capabilities.addToQueue(PAYLOAD);



              return arr.length===1?{id:arr[0].id}: {error:'ENQUEUE_NOT_SINGLE'};})()""".replace(



                    "PAYLOAD", json.dumps(payload, ensure_ascii=False))



            added = _evaluate(ws, 11, js)



            if not isinstance(added, dict) or not added.get("id"):



                raise WebToolError("WEBTOOL_ENQUEUE_OUTCOME_UNKNOWN", 409)



            shot_id = str(added["id"])



            ledger[request_id].update(shot_id=shot_id, state="enqueued")



            _commit(ledger)



            time.sleep(.7)



            # Safeguard aspect/duration independent of the script parser.



            patch = r"""(()=>{const b=window.__STORYBOARD_MCP__;



              const shot=b?.queue?.find(x=>x.id===__SHOT_ID__);



              if(!shot||shot.status!=='pending'||b.isProcessing)return 'SHOT_MISSING';



              if(typeof b.capabilities?.updateItem!=='function')return 'UPDATE_MISSING';



              b.capabilities.updateItem(__SHOT_ID__,{parsed:{...shot.parsed,



                 aspectRatio:ASPECT,durationSeconds:8}});



              return 'PATCH_OK'})()""".replace("__SHOT_ID__",json.dumps(shot_id)).replace(



                    "ASPECT",json.dumps(aspect_ratio))



            result = _evaluate(ws, 12, patch)



            if result != "PATCH_OK":



                raise WebToolError("WEBTOOL_SHOT_SETTINGS_NOT_APPLIED", 409)



            time.sleep(.7)



            confirmed = _evaluate(ws, 13,



                r"""(()=>{const b=window.__STORYBOARD_MCP__;



                const matches=b.queue.filter(x=>x.id===__SHOT_ID__);



                return {busy:b.isProcessing,match:matches.length,



                   status:matches[0]?.status,aspect:matches[0]?.parsed?.aspectRatio,



                   duration:matches[0]?.parsed?.durationSeconds}})()""".replace(



                    "__SHOT_ID__",json.dumps(shot_id)))



            if not confirmed or confirmed.get("busy") or confirmed.get("match")!=1 or (



                confirmed.get("status")!="pending" or confirmed.get("aspect")!=aspect_ratio



                or confirmed.get("duration")!=8):



                raise WebToolError("WEBTOOL_SHOT_SETTINGS_NOT_CONFIRMED", 409)



            # A prepared shot is confirmed with the requested aspect/duration.



            # An 'enqueued' shot is NOT safe for automatic dispatch.



            ledger[request_id]["state"]="prepared"



            _commit(ledger)



            # Once this journal state exists, NEVER resend on unknown result.



            ledger[request_id]["state"]="start_outcome_unknown"



            _commit(ledger)



            start_js=r"""(()=>{const b=window.__STORYBOARD_MCP__;



              const id=__SHOT_ID__;



              if(!b||b.isProcessing||b.queue.filter(x=>x.id===id&&x.status==='pending').length!==1



                 ||typeof b.capabilities?.retryItem!=='function')return 'BLOCKED';



              const promise=b.capabilities.retryItem(id);



              return promise&&typeof promise.then==='function'?'STARTED':'NO_PROMISE'})()""".replace(



                    "__SHOT_ID__",json.dumps(shot_id))



            started=_evaluate(ws, 14, start_js)



            if started!="STARTED":



                raise WebToolError("WEBTOOL_SINGLE_SHOT_START_UNKNOWN",409)



        ledger[request_id]["state"]="start_clicked"



        _commit(ledger)



        return {"shot_id": shot_id, "reused": False, "state": "start_clicked"}







    def start_enqueued(self, request_id, shot_id):



        """Recover a *prepared* and verified shot without recreating it.







        Only valid while the persistent ledger still says 'prepared'.



        Once dispatch is attempted we never automatically retry.



        """



        with _LOCK:



            ledger = _load()



            prior = ledger.get(request_id)



            if (not prior or prior.get("mode") != self.mode or



                prior.get("shot_id") != shot_id or prior.get("state") != "prepared" or



                prior.get("aspect_ratio") not in ("9:16","16:9")):



                raise WebToolError("WEBTOOL_ENQUEUED_RECOVERY_NOT_SAFE", 409)



            current = self.adapter.status()



            shots = [q for q in current["queue"] if q["id"] == shot_id]



            if current["processing"] or len(shots) != 1 or shots[0]["status"] != "pending":



                raise WebToolError("WEBTOOL_ENQUEUED_SHOT_NOT_PENDING", 409)



            ledger[request_id]["state"] = "start_outcome_unknown"



            _commit(ledger)



            frame = self.adapter._frame()



            js = r"""(()=>{const b=window.__STORYBOARD_MCP__;



               const id=__SHOT_ID__;



               if(!b||b.isProcessing||b.queue.filter(q=>q.id===id&&q.status==='pending').length!==1



                 ||typeof b.capabilities?.retryItem!=='function')return 'BLOCKED';



               const shot=b.queue.find(q=>q.id===id);



               if(shot?.parsed?.aspectRatio!==__ASPECT__||



                  (!__IMAGE__ && shot?.parsed?.durationSeconds!==8))



                 return 'SETTINGS_CHANGED';



               if(__IMAGE__ && b.queue.filter(q=>q.assetKind==='image'&&



                   ['pending','error','generating','queued'].includes(q.status)).length!==1)



                 return 'OTHER_PENDING_IMAGES';



               const result=b.capabilities.retryItem(id);



               return result&&typeof result.then==='function'?'STARTED':'UNCONFIRMED';})()""".replace(



                  "__SHOT_ID__",json.dumps(shot_id)).replace(



                  "__ASPECT__",json.dumps(prior["aspect_ratio"])).replace(



                  "__IMAGE__",json.dumps(prior.get("kind")=="image"))



            with connect(frame["webSocketDebuggerUrl"], open_timeout=5, max_size=2*1024*1024) as ws:



                result = _evaluate(ws, 101, js)



            if result != "STARTED":



                raise WebToolError("WEBTOOL_DISPATCH_OUTCOME_UNKNOWN", 409)



            ledger[request_id]["state"] = "start_clicked"



            _commit(ledger)



            return {"shot_id": shot_id, "state": "start_clicked"}







    def _submit_image_capability(self, request_id, prompt, aspect_ratio, fingerprint, ledger, image_model="NANO_BANANA_PRO"):



        """Enqueue one image and start exactly its image production queue.







        Each managed shot carries its requested model. Only managed pending
        images are consumed; unrelated pending/error images remain untouched.



        """



        # Preserve unrelated pending shots and failure evidence.
        max_concurrency = int(settings().get("flow_webtool_concurrency", 3))



        deadline = time.time() + 90



        while time.time() < deadline:



            before = self.adapter.status()



            in_flight = [



                x for x in before["queue"]



                if (x.get("kind") == "image" or x.get("assetKind") == "image")



                and x["status"] in ("pending", "queued", "generating")



            ]



            if len(in_flight) < max_concurrency:



                break



            time.sleep(0.5)



        else:



            raise WebToolError("WEBTOOL_QUEUE_CAPACITY_EXCEEDED", 429)



        shot_id = f"shot_{int(time.time()*1000)}_0"



        ledger[request_id] = {



            "mode": self.mode, "kind": "image",



            "fingerprint": fingerprint, "aspect_ratio": aspect_ratio, "image_model": image_model,



            "shot_id": shot_id, "state": "start_clicked",



            "started_at": time.time()



        }



        _commit(ledger)



        frame = self.adapter._frame()







        target_model_display = image_model_display(image_model)



        with connect(frame["webSocketDebuggerUrl"], open_timeout=5, max_size=2*1024*1024) as ws:



            start = r"""(()=>{const b=window.__STORYBOARD_MCP__;



              if(!b||typeof b.capabilities?.addToQueue!=='function') return 'NO_CAPABILITIES';



              



              if (!b.capabilities.__robust_wrapped_v4_model_selection) {



                const origUpdateItem = b.capabilities.updateItem;



                if (b.config) {



                  b.config.concurrency = 3;



                }



                let isWorkerPoolRunning = false;



                



                const processPendingQueue = async () => {



                  if (isWorkerPoolRunning) return;



                  isWorkerPoolRunning = true;



                  b.isProcessing = true;



                  



                  try {



                    const { Flow } = await import('flow-sdk');



                    const concurrency = Math.max(1, Math.min(3, b.config?.concurrency || 3));



                    







                    



                    const renderItem = async (item) => {



                      if (!item) return;
                      const uniqueModels = [item.flowkitRequestedImageModel];



                      item.status = 'generating';



                      if (typeof origUpdateItem === 'function') {



                        origUpdateItem(item.id, { status: 'generating' });



                      }



                      



                      let succeeded = false;



                      let lastErr = null;



                      let usedModel = null;



                      



                      for (const m of uniqueModels) {



                        try {



                          const timeoutP = new Promise((_, reject) => setTimeout(() => reject(new Error('FLOW_MODEL_TIMEOUT_90S')), 90000));
                          const res = await Promise.race([
                            Flow.generate.image({
                              prompt: item.promptText,
                              modelDisplayName: m,
                              aspectRatio: item.parsed?.aspectRatio || '9:16'
                            }),
                            timeoutP
                          ]);



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



                    };



                    



                    const worker = async () => {



                      while (true) {



                        const item = (b.queue || []).find(x => x.assetKind === 'image' && x.flowkitRequestedImageModel && x.status === 'pending');



                        if (!item) break;



                        item.status = 'generating';



                        await renderItem(item);



                      }



                    };



                    



                    await Promise.all(Array.from({ length: concurrency }, () => worker()));



                  } finally {



                    isWorkerPoolRunning = false;



                    const hasMore = (b.queue || []).some(x => x.assetKind === 'image' && x.flowkitRequestedImageModel && x.status === 'pending');



                    if (hasMore) {



                      setTimeout(processPendingQueue, 50);



                    } else {



                      b.isProcessing = false;



                    }



                  }



                };



                



                b.capabilities.startImageProduction = async (options) => {



                  processPendingQueue();



                  return { success: true };



                };



                b.capabilities.__robust_wrapped_v4_model_selection = true;



              }



              



              const arr = b.capabilities.addToQueue([{



                title: 'FlowKit image ' + ID.slice(0, 20),



                text: PROMPT,



                assetKind: 'image'



              }]);



              if (!arr || !arr.length) return 'ADD_FAILED';



              const created = arr[0];
              created.flowkitRequestedImageModel = __FLOWKIT_IMAGE_MODEL__;



              created.id = ID;



              created.parsed = created.parsed || {};
              created.parsed.aspectRatio = ASPECT;



              b.queue = b.queue || [];
              const origId = created.id;
              created.id = ID;
              const existing = b.queue.find(x => x.id === origId || x.id === ID);
              if (existing) {
                existing.id = ID;
                existing.flowkitRequestedImageModel = __FLOWKIT_IMAGE_MODEL__;
                if (created.parsed) existing.parsed = created.parsed;
              } else {
                b.queue.push(created);
              }



              setTimeout(() => {



                try {



                  b.capabilities.startImageProduction({ approved: true, maxImages: 10 });



                } catch(e) {



                  console.error('startImageProduction error:', e);



                }



              }, 50);



              return 'STARTED';})()""".replace(



                  "ID", json.dumps(shot_id)).replace("PROMPT", json.dumps(prompt)).replace("ASPECT", json.dumps(aspect_ratio)).replace("__FLOWKIT_IMAGE_MODEL__", json.dumps(target_model_display))



            response = _evaluate(ws, 114, start)



            if response != "STARTED":



                raise WebToolError("WEBTOOL_IMAGE_START_OUTCOME_UNKNOWN: " + str(response), 409)



        return {"shot_id": shot_id, "reused": False, "state": "start_clicked"}



