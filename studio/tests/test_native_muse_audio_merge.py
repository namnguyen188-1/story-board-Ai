import ast,contextlib,io,json,os,pathlib,shutil,sys,tempfile,types,unittest
from unittest.mock import patch
ROOT=pathlib.Path(__file__).parent
SOURCE=(ROOT if (ROOT/'series_studio.py').is_file() else ROOT.parent)/'series_studio.py'
class NativeMerge(unittest.TestCase):
 def render(self,muse,cached=False):
  with tempfile.TemporaryDirectory() as tmp:
   root=pathlib.Path(tmp);scene=root/'scene';scene.mkdir()
   (scene/'image.png').write_bytes(b'IMAGE'*400)
   (scene/'audio.wav').write_bytes(b'AUDIO'*600)
   original=b'NATIVE_AUDIO_VIDEO'*300
   (scene/'muse_clip.mp4').write_bytes(original)
   if cached:(scene/'silent.mp4').write_bytes(b'SILENT'*400)
   job={'scene':{'scene_number':1,'narration':'Words','script_seconds':10},'scene_dir':str(scene),'bible':{},'width':1280,'height':720,'mode':'live','image_provider':'muse_video' if muse else 'gemini','clean_watermark':False,'visual_style':'cinematic','subtitles':False,'input_hash':'test'}
   merges=[];commands=[]
   def merge(s,a,target):
    merges.append(target);pathlib.Path(target).write_bytes(b'MERGED'*400);return target
   def run(cmd,**kw):commands.append(cmd);pathlib.Path(cmd[-1]).write_bytes(b'FFMPEG'*400)
   def color(image,audio,target,*args,**kw):pathlib.Path(target).write_bytes(b'COLOR'*400);return str(target)
   tools=types.ModuleType('tools');tools.utils=types.SimpleNamespace(set_output_dir=lambda x:None)
   for name in ('image_gen_tool_fn','prompt_tool_fn','generate_tts_audio_tool_fn','draw_animation_tool_fn','burn_subtitles_to_video_tool_fn'):setattr(tools,name,lambda *a,**k:(_ for _ in ()).throw(AssertionError('Unexpected external rendering or TTS')))
   tools.merge_audio_video_tool_fn=merge
   provider=types.ModuleType('muse_video_provider');provider.make_scene_media=lambda *a,**kw:None
   color_module=types.ModuleType('studio_color_render');color_module.color_video=color
   tree=ast.parse(SOURCE.read_text(encoding='utf-8'));fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='render_one')
   env={'Path':pathlib.Path,'os':os,'sys':sys,'shutil':shutil,'json':json,'ENGINE':root,'read_json':lambda p:job if str(p)=='JOB' else {},'write_json':lambda p,x:pathlib.Path(p).write_text(json.dumps(x)),'qc_silent':lambda p:p.exists(),'qc_complete':lambda p,w,h:p.exists(),'qc_clip':lambda *a,**kw:{'duration_seconds':10},'stamp':lambda:'TEST'}
   exec(compile(ast.Module(body=[fn],type_ignores=[]),str(SOURCE),'exec'),env)
   cwd=os.getcwd();paths=list(sys.path)
   try:
    with patch.dict(sys.modules,{'tools':tools,'muse_video_provider':provider,'studio_color_render':color_module}),patch('subprocess.run',side_effect=run),contextlib.redirect_stdout(io.StringIO()):
     self.assertEqual(env['render_one']('JOB'),0)
    self.assertTrue((scene/'final.mp4').is_file())
    self.assertEqual(json.loads((scene/'result.json').read_text())['status'],'PASS')
    self.assertEqual((scene/'muse_clip.mp4').read_bytes(),original)
    if muse and not cached:
     self.assertEqual(len(commands),2)
     self.assertEqual(merges,[],'Native Muse audio must bypass external audio merge')
     self.assertEqual(commands[-1][-1],str((scene/'merged.mp4').resolve()))
     self.assertEqual((scene/'final.mp4').read_bytes(),(scene/'merged.mp4').read_bytes())
    else:self.assertEqual(len(merges),1)
   finally:os.chdir(cwd);sys.path[:]=paths
 def test_new_native_muse_clip_preserves_its_audio(self):self.render(True)
 def test_cached_silent_can_resume_audio_merge(self):self.render(True,True)
 def test_non_muse_image_render_still_merges_tts(self):self.render(False)
if __name__=='__main__':unittest.main(verbosity=2)
