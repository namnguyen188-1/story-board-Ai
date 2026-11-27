import ast
import contextlib
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import types
import unittest
from typing import Literal
import uuid
from unittest.mock import patch

from pydantic import BaseModel, Field, model_validator, field_validator

APP = Path(__file__).parent / 'local_after'
if not APP.is_dir():
    APP = Path(__file__).parent

def job_request_class():
    tree = ast.parse((APP / 'gateway.py').read_text(encoding='utf-8'))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'JobRequest')
    ns = dict(BaseModel=BaseModel, Field=Field, model_validator=model_validator,
              field_validator=field_validator, Literal=Literal, uuid=uuid)
    if (APP / 'flow_models.py').exists():
        exec((APP / 'flow_models.py').read_text(encoding='utf-8'), ns)
    exec(compile(ast.Module(body=[cls], type_ignores=[]), 'gateway.py', 'exec'), ns)
    return ns['JobRequest']

def adapter_module(folder):
    common = types.ModuleType('common')
    common.STATE = Path(folder)
    common.settings = lambda: {'flow_webtool_concurrency': 3}
    direct = types.ModuleType('flow_webtool_direct')
    class WebToolError(RuntimeError):
        def __init__(self, code, status=409):
            super().__init__(code)
            self.code, self.status = code, status
    class Adapter:
        def __init__(self, mode): pass
        def status(self):
            return dict(processing=False, queue=[], capability_enqueue=True,
                        capability_single_start=True, native_submit=False)
        def _frame(self): return {'webSocketDebuggerUrl': 'ws://test'}
    direct.WebToolAdapter, direct.WebToolError = Adapter, WebToolError
    import threading
    direct._LOCK = threading.RLock()
    direct._evaluate = lambda *a: None
    ns = {'__name__': 'test_webtool_adapter'}
    modules = {'common': common, 'flow_webtool_direct': direct}
    if (APP / 'flow_models.py').exists():
        models = types.ModuleType('flow_models')
        exec((APP / 'flow_models.py').read_text(encoding='utf-8'), models.__dict__)
        modules['flow_models'] = models
    with patch.dict('sys.modules', modules):
        exec(compile((APP / 'flow_webtool_jobs.py').read_text(encoding='utf-8'), 'flow_webtool_jobs.py', 'exec'), ns)
    ns['connect'] = lambda *a, **kw: contextlib.nullcontext(object())
    ns['time'] = types.SimpleNamespace(time=lambda: 1000, sleep=lambda n: None)
    return types.SimpleNamespace(**ns), ns

class ModelUpgradeTests(unittest.TestCase):
    def test_api_accepts_new_image_name_and_preserves_legacy_payload(self):
        cls = job_request_class()
        for alias in ('NANO_BANANA_2.1', 'NANO_BANANA_2_1', 'NANO_BANANA_2'):
            with self.subTest(alias=alias):
                try:
                    job = cls(provider='webtool', kind='image', prompt='a red sailboat', image_model=alias)
                except ValueError as e:
                    self.fail('New Flow model name rejected: ' + str(e))
                self.assertEqual(job.image_model, 'NANO_BANANA_2')

    def test_video_dispatch_does_not_reference_image_model(self):
        with tempfile.TemporaryDirectory() as folder:
            mod, ns = adapter_module(folder)
            replies = {11: {'id': 'video-one'}, 12: 'PATCH_OK',
                       13: dict(busy=False, match=1, status='pending', aspect='16:9', duration=8),
                       14: 'STARTED'}
            ns['_evaluate'] = lambda ws, call, js: replies[call]
            try:
                out = mod.WebToolProduction('hidden')._submit_capability('video-job', 'a sailboat at dawn', '16:9', 'legacy-test', {})
            except NameError as e:
                self.fail('Video dispatch crashes before enqueue: ' + str(e))
            self.assertEqual(out['shot_id'], 'video-one')

    def image_scripts(self, folder, model='NANO_BANANA_2'):
        mod, ns = adapter_module(folder)
        scripts = []
        def evaluate(ws, call, js):
            scripts.append(js)
            return 0 if call == 109 else 'STARTED'
        ns['_evaluate'] = evaluate
        out = mod.WebToolProduction('hidden')._submit_image_capability('image-job', 'a red sailboat', '16:9', 'legacy-test', {}, model)
        return scripts, out, mod

    def run_image_scripts(self, scripts, reject=False):
        harness = r'''
const vm = require('node:vm');
const scripts = SCRIPTS;
const calls = [];
const b = {config:{imageModel:'Nano Banana Pro'}, isProcessing:false,
 queue:[{id:'unrelated',assetKind:'image',status:'pending',promptText:'KEEP ME'},
        {id:'old-error',assetKind:'image',status:'error',promptText:'PRESERVE EVIDENCE'}]};
b.capabilities = {
 addToQueue(items){const rows=items.map(x=>({...x,id:'generated-original',status:'pending',promptText:x.text,parsed:{}}));b.queue.push(...rows);return rows;},
 updateItem(id, fields){Object.assign(b.queue.find(x=>x.id===id)||{},fields);},
 removeItem(id){b.queue=b.queue.filter(x=>x.id!==id);}
};
const context={window:{__STORYBOARD_MCP__:b},console,Blob,URL,Uint8Array,atob,
 setTimeout:(fn,ms)=>{if(ms<1000)setImmediate(fn);return 1;},
 FLOW_MOCK:{generate:{image:async req=>{calls.push(req);if(REJECT)throw new Error('MODEL_UNAVAILABLE');return {base64:'eA==',mediaId:'media-one',mimeType:'image/png'};}}}};
vm.createContext(context);
for (const code of scripts) vm.runInContext(code.replace("import('flow-sdk')",'Promise.resolve({Flow:FLOW_MOCK})'),context);
setTimeout(()=>{console.log(JSON.stringify({calls,queue:b.queue.map(x=>({id:x.id,status:x.status}))}));},100);
'''
        harness = harness.replace('SCRIPTS', json.dumps(scripts)).replace('REJECT', json.dumps(reject))
        result = subprocess.run(['node', '-e', harness], capture_output=True, text=True, encoding='utf-8', timeout=5)
        if result.returncode:
            self.fail('Generated dispatch script failed: ' + result.stderr[-2000:])
        return json.loads(result.stdout.strip().splitlines()[-1])

    def test_image_dispatch_honors_requested_model_without_processing_other_shots(self):
        with tempfile.TemporaryDirectory() as folder:
            scripts, _, _ = self.image_scripts(folder)
            observed = self.run_image_scripts(scripts)
            self.assertEqual([(x['prompt'], x['modelDisplayName']) for x in observed['calls']],
                             [('a red sailboat', '\U0001f34c Nano Banana 2.1')])
            states = {x['id']:x['status'] for x in observed['queue']}
            self.assertEqual(states['unrelated'], 'pending')
            self.assertEqual(states['old-error'], 'error')

    def test_model_error_never_submits_to_other_models(self):
        with tempfile.TemporaryDirectory() as folder:
            scripts, _, _ = self.image_scripts(folder, 'NANO_BANANA_2_LITE')
            observed = self.run_image_scripts(scripts, reject=True)
            self.assertEqual([(x['prompt'],x['modelDisplayName']) for x in observed['calls']],
                             [('a red sailboat','\U0001f34c Nano Banana 2 Lite')])

    def test_same_request_with_different_model_conflicts_without_resubmitting(self):
        with tempfile.TemporaryDirectory() as folder:
            _, _, mod = self.image_scripts(folder)
            with self.assertRaisesRegex(RuntimeError, 'IDEMPOTENCY_CONFLICT'):
                mod.WebToolProduction('hidden').submit('image-job','a red sailboat','16:9','image','NANO_BANANA_PRO')

    def test_unknown_model_rejected_before_queue_or_ledger_mutation(self):
        with tempfile.TemporaryDirectory() as folder:
            mod, ns = adapter_module(folder)
            with self.assertRaisesRegex(RuntimeError, 'UNSUPPORTED_IMAGE_MODEL'):
                mod.WebToolProduction('hidden').submit('bad-model-job','a red sailboat','16:9','image','MADE_UP_MODEL')
            self.assertFalse((Path(folder)/'webtool_jobs_ledger.json').exists())

    def test_legacy_receipt_is_reused_without_dispatch(self):
        with tempfile.TemporaryDirectory() as folder:
            prompt='a red sailboat'
            oldfp=hashlib.sha256(json.dumps(dict(prompt=prompt,aspect_ratio='16:9',kind='image',mode='hidden'),sort_keys=True,ensure_ascii=False).encode()).hexdigest()
            (Path(folder)/'webtool_jobs_ledger.json').write_text(json.dumps({'old-job':dict(fingerprint=oldfp,shot_id='old-shot',state='start_clicked')}))
            mod, ns = adapter_module(folder)
            result=mod.WebToolProduction('hidden').submit('old-job',prompt,'16:9','image','NANO_BANANA_2')
            self.assertTrue(result['reused'])
            self.assertEqual(result['shot_id'],'old-shot')

if __name__ == '__main__':
    unittest.main(verbosity=2)
