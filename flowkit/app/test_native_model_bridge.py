import ast
import contextlib
import io
import hashlib
import json
from pathlib import Path
import re
import tempfile
import threading
import types
import unittest
from unittest.mock import patch
from typing import Literal
import uuid
from pydantic import BaseModel, Field, field_validator, model_validator

APP=Path(__file__).parent/'local_after'
if not APP.is_dir(): APP=Path(__file__).parent/'local_before'
if not APP.is_dir(): APP=Path(__file__).parent

class WebToolError(RuntimeError):
    def __init__(self,code,status=409):super().__init__(code);self.code,self.status=code,status

def module_for(folder):
    common=types.ModuleType('common');common.STATE=Path(folder);common.settings=lambda:{}
    direct=types.ModuleType('flow_webtool_direct');direct.WebToolError=WebToolError;direct._LOCK=threading.RLock()
    class Adapter:
        def __init__(self,mode):pass
        def status(self):return {'native_submit':True,'processing':False,'queue':[]}
        def _frame(self):return {'webSocketDebuggerUrl':'ws://test'}
    direct.WebToolAdapter=Adapter;direct._evaluate=lambda *a:None
    models=types.ModuleType('flow_models');exec((APP/'flow_models.py').read_text(encoding='utf-8'),models.__dict__)
    ns={}
    with patch.dict('sys.modules',{'common':common,'flow_webtool_direct':direct,'flow_models':models}):
        exec(compile((APP/'flow_webtool_jobs.py').read_text(encoding='utf-8'),'flow_webtool_jobs.py','exec'),ns)
    ns['connect']=lambda *a,**k:contextlib.nullcontext(object())
    payloads=[]
    def evaluate(ws,call,script):
        match=re.search(r'b\.submit\((\{.*\})\)',script)
        if not match:raise AssertionError('Native dispatch not used')
        payloads.append(json.JSONDecoder().raw_decode(match[1])[0]);return {'accepted':True,'jobId':'job-native-one'}
    ns['_evaluate']=evaluate
    return ns,payloads

class NativeModelTests(unittest.TestCase):
    def test_model_upgrade_opens_new_tool_without_navigating_existing_work(self):
        tree=ast.parse((APP/'flow_browser.py').read_text(encoding='utf-8'))
        fn=next((n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_open_target_page'),None)
        self.assertIsNotNone(fn,'Missing non-destructive tool switch')
        old={'id':'unsaved-old-tool','type':'page','url':'https://flow.google.com/project/p/tool/old'}
        target='https://flow.google.com/project/p/tool/new';commands=[];created=False
        def cdp(ws,call,method,params=None):
            nonlocal created
            commands.append((method,params));created=True;return {'targetId':'new-tool'}
        def urlopen(url,timeout=None):
            data={'webSocketDebuggerUrl':'ws://browser'} if url.endswith('/version') else [old]+([{'id':'new-tool','type':'page','url':target}] if created else [])
            return io.BytesIO(json.dumps(data).encode())
        direct=types.ModuleType('flow_webtool_direct');direct._cdp=cdp
        ws=types.ModuleType('websockets.sync.client');ws.connect=lambda *a,**kw:contextlib.nullcontext(object())
        ns={'json':json,'urllib':types.SimpleNamespace(request=types.SimpleNamespace(urlopen=urlopen)),'time':types.SimpleNamespace(sleep=lambda n:None)}
        with patch.dict('sys.modules',{'flow_webtool_direct':direct,'websockets.sync.client':ws}):
            exec(compile(ast.Module(body=[fn],type_ignores=[]),'flow_browser.py','exec'),ns)
            pages=ns['_open_target_page']('http://local',target)
        self.assertEqual(pages[0]['id'],'new-tool')
        self.assertEqual(commands,[('Target.createTarget',{'url':target,'background':True})])
        self.assertEqual(old['url'],'https://flow.google.com/project/p/tool/old')

    def test_adapter_selects_only_the_configured_tool_iframe(self):
        common=types.ModuleType('common')
        common.OUTPUTS=common.ROOT=common.STATE=Path('unused');common.settings=lambda:{}
        ns={}
        with patch.dict('sys.modules',{'common':common}):
            exec(compile((APP/'flow_webtool_direct.py').read_text(encoding='utf-8'),'flow_webtool_direct.py','exec'),ns)
        target='https://flow.google.com/project/p/tool/owned'
        tabs=[{'id':'wrong','type':'page','url':'https://flow.google.com/project/p/tool/shared'},
              {'id':'right','type':'page','url':target},
              {'id':'same-tool-query','type':'page','url':target+'?mode=APP&fromViewSource=tools'},
              {'id':'fwrong','type':'iframe','url':'https://a.usercontent.goog/x','webSocketDebuggerUrl':'ws://wrong'},
              {'id':'fright','type':'iframe','url':'https://b.usercontent.goog/x','webSocketDebuggerUrl':'ws://right'}]
        ns['_read_json']=lambda url:{'webSocketDebuggerUrl':'ws://test'} if url.endswith('/version') else tabs
        ns['connect']=lambda *a,**k:contextlib.nullcontext(object())
        ns['_cdp']=lambda *a,**k:{'targetInfos':[{'targetId':'fwrong','type':'iframe','parentFrameId':'wrong'}, {'targetId':'fright','type':'iframe','parentFrameId':'right'}]}
        ns['_evaluate']=lambda *a,**k:{'app':True,'bridge':True}
        adapter=object.__new__(ns['WebToolAdapter']);adapter.url=target;adapter.debug_url='http://local'
        self.assertEqual(adapter._frame()['id'],'fright')

    def test_loading_iframe_is_not_faked_into_a_ready_bridge(self):
        common=types.ModuleType('common');common.OUTPUTS=common.ROOT=common.STATE=Path('unused');common.settings=lambda:{}
        ns={}
        with patch.dict('sys.modules',{'common':common}):
            exec(compile((APP/'flow_webtool_direct.py').read_text(encoding='utf-8'),'flow_webtool_direct.py','exec'),ns)
        target='https://flow.google.com/project/p/tool/owned'
        tabs=[{'id':'right','type':'page','url':target},{'id':'fright','type':'iframe','url':'https://b.usercontent.goog/x','webSocketDebuggerUrl':'ws://right'}]
        ns['_read_json']=lambda url:{'webSocketDebuggerUrl':'ws://test'} if url.endswith('/version') else tabs
        ns['connect']=lambda *a,**kw:contextlib.nullcontext(object())
        ns['_cdp']=lambda *a,**kw:{'targetInfos':[{'targetId':'fright','type':'iframe','parentFrameId':'right'}]}
        calls=[]
        def evaluate(ws,call,code):calls.append(code);return {'app':True,'bridge':False}
        ns['_evaluate']=evaluate
        adapter=object.__new__(ns['WebToolAdapter']);adapter.url=target;adapter.debug_url='http://local'
        with self.assertRaisesRegex(ns['WebToolError'],'BRIDGE_NOT_READY'):adapter._frame()
        self.assertEqual(len(calls),1)

    def test_image_uses_native_model_and_never_legacy_worker(self):
        with tempfile.TemporaryDirectory() as folder:
            ns,seen=module_for(folder)
            try:r=ns['WebToolProduction']('hidden').submit('req-one','a red sailboat','16:9','image','NANO_BANANA_2.1')
            except Exception as e:self.fail('Native image dispatch failed: '+str(e))
            self.assertEqual(r['shot_id'],'job-native-one')
            self.assertEqual(seen[0]['kind'],'image');self.assertEqual(seen[0]['modelDisplayName'],'\U0001f34c Nano Banana 2.1')
            self.assertEqual(seen[0]['approved'],True)

    def test_video_passes_explicit_new_model_and_resolution(self):
        with tempfile.TemporaryDirectory() as folder:
            ns,seen=module_for(folder)
            try:ns['WebToolProduction']('hidden').submit('req-one','a red sailboat','16:9','video',video_model='VEO_3_1_LITE',resolution='720p')
            except Exception as e:self.fail('Explicit video model rejected: '+str(e))
            self.assertEqual(seen[0]['modelDisplayName'],'Veo 3.1 - Lite');self.assertEqual(seen[0]['resolution'],'720p')
            self.assertEqual(seen[0]['durationSeconds'],8)

    def test_old_video_receipt_reused_without_new_sdk_call(self):
        with tempfile.TemporaryDirectory() as folder:
            fp=hashlib.sha256(json.dumps(dict(prompt='a red sailboat',aspect_ratio='16:9',kind='video',mode='hidden'),sort_keys=True,ensure_ascii=False).encode()).hexdigest()
            (Path(folder)/'webtool_jobs_ledger.json').write_text(json.dumps({'req-one':{'fingerprint':fp,'shot_id':'old-shot','state':'start_clicked'}}))
            ns,seen=module_for(folder)
            r=ns['WebToolProduction']('hidden').submit('req-one','a red sailboat','16:9','video')
            self.assertTrue(r['reused']);self.assertEqual(seen,[])

    def test_unknown_video_model_rejected_before_dispatch(self):
        with tempfile.TemporaryDirectory() as folder:
            ns,seen=module_for(folder)
            with self.assertRaisesRegex(WebToolError,'UNSUPPORTED_VIDEO_MODEL'):
                ns['WebToolProduction']('hidden').submit('req-one','a red sailboat','16:9','video',video_model='INVENTED')
            self.assertEqual(seen,[]);self.assertFalse((Path(folder)/'webtool_jobs_ledger.json').exists())

    def test_model_change_with_same_id_conflicts(self):
        with tempfile.TemporaryDirectory() as folder:
            ns,seen=module_for(folder);p=ns['WebToolProduction']('hidden')
            p.submit('req-one','a red sailboat','16:9','video')
            with self.assertRaisesRegex(WebToolError,'IDEMPOTENCY_CONFLICT'):
                p.submit('req-one','a red sailboat','16:9','video',video_model='VEO_3_1_LITE')
            self.assertEqual(len(seen),1)

    def test_old_webtool_without_native_bridge_cannot_silently_use_old_model(self):
        with tempfile.TemporaryDirectory() as folder:
            ns,seen=module_for(folder);p=ns['WebToolProduction']('hidden');p.adapter.status=lambda:{'native_submit':False,'capability_enqueue':True,'capability_single_start':True}
            with self.assertRaisesRegex(WebToolError,'UPGRADE_REQUIRED'):
                p.submit('req-one','a red sailboat','16:9','video')
            self.assertEqual(seen,[])

    def test_gateway_keeps_explicit_model_fields_in_payload(self):
        ns=dict(BaseModel=BaseModel,Field=Field,field_validator=field_validator,model_validator=model_validator,Literal=Literal,uuid=uuid)
        exec((APP/'flow_models.py').read_text(encoding='utf-8'),ns)
        cls=next(n for n in ast.parse((APP/'gateway.py').read_text(encoding='utf-8')).body if isinstance(n,ast.ClassDef) and n.name=='JobRequest')
        exec(compile(ast.Module(body=[cls],type_ignores=[]),'gateway.py','exec'),ns)
        payload=ns['JobRequest'](provider='webtool',kind='video',prompt='a red sailboat',video_model='VEO_3_1_LITE',resolution='720p').model_dump()
        self.assertEqual(payload.get('video_model'),'VEO_3_1_LITE');self.assertEqual(payload.get('resolution'),'720p')

if __name__=='__main__':unittest.main(verbosity=2)
