import ast,sys,pathlib,tempfile,types,re,json,unittest,importlib.util
from datetime import datetime
from unittest.mock import patch
BASE=pathlib.Path(__file__).parent
if not (BASE/'web_server.py').is_file():BASE=BASE.parent
LIVE=pathlib.Path(r'D:\STORYBOARD_AI\studio');sys.path.insert(0,str(LIVE))
class UploadRoutes(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  spec=importlib.util.spec_from_file_location('yt_upload_test',BASE/'youtube_manager.py');cls.yt=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.yt)
  tree=ast.parse((BASE/'web_server.py').read_text(encoding='utf-8'))
  branch=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and isinstance(n.test,ast.Compare) and any(isinstance(x,ast.Constant) and x.value=='/api/youtube/upload' for x in n.test.comparators))
  function=ast.parse('def upload_route(self,body): pass').body[0];function.body=branch.body
  cls.tree=ast.fix_missing_locations(ast.Module(body=[function],type_ignores=[]))
 def call(self,media_type='long',**body):
  with tempfile.TemporaryDirectory() as tmp:
   root=pathlib.Path(tmp);video=root/'episode_final.mp4';video.write_bytes(b'VIDEO')
   info={'video_path':video,'language':'English','title':'Actual title','description':'Description','tags':['real'],'publish_pack':{'publishing_schedule':{'best_time_today':None,'golden_hours':None}}}
   uploaded=[]
   yt=self.yt
   globals_={'re':re,'datetime':datetime,'resolve_production_episode':lambda *a:('show',1,root)}
   exec(compile(self.tree,'web_server.py','exec'),globals_)
   with patch.dict(sys.modules,{'youtube_manager':yt}),patch.object(yt,'resolve_episode_media',return_value=info) as resolve,patch.object(yt,'get_channel_publish_settings',return_value={'default_language':'en'}),patch.object(yt,'set_series_channel_mapping'),patch.object(yt,'update_channel_publish_settings'),patch.object(yt,'start_background_upload',side_effect=lambda **kw:uploaded.append(kw) or {'ok':True}),patch.object(yt,'start_background_batch_upload',side_effect=AssertionError('Unexpected second upload')):
    result=globals_['upload_route'](types.SimpleNamespace(end_json=lambda value,status=200:(value,status)),{'series':'show','episode':1,'channel_id':'CHANNEL','media_type':media_type,**body})
   return result,uploaded,resolve.call_args.kwargs
 def test_long_reaches_single_upload(self):
  result,uploads,_=self.call();self.assertTrue(result[0]['ok']);self.assertEqual(len(uploads),1)
 def test_legacy_both_normalizes_before_resolving_media(self):
  result,uploads,args=self.call('both');self.assertTrue(result[0]['ok']);self.assertEqual(len(uploads),1);self.assertEqual(args['media_type'],'long')
 def test_disabled_shorts_normalizes_before_resolving_media(self):
  result,uploads,args=self.call('short');self.assertTrue(result[0]['ok']);self.assertEqual(len(uploads),1);self.assertEqual(args['media_type'],'long')
 def test_schedule_without_time_is_rejected_instead_of_invented(self):
  result,uploads,_=self.call(privacy='schedule_seo');self.assertEqual(result[1],400);self.assertFalse(uploads)
 def test_false_disclosure_and_empty_playlist_are_preserved(self):
  result,uploads,_=self.call(contains_synthetic_media=False,new_playlist_title=None,source='advanced_modal')
  self.assertTrue(result[0]['ok']);self.assertIs(uploads[0]['contains_synthetic_media'],False);self.assertIsNone(uploads[0]['new_playlist_title'])
 def test_language_mapping_is_preserved_for_upload_metadata(self):
  for source,expected in [('English','en-US'),('Spanish','es'),('Tiếng Việt','vi')]:
   self.assertEqual(self.yt.to_youtube_bcp47(source),expected)
if __name__=='__main__':unittest.main(verbosity=2)