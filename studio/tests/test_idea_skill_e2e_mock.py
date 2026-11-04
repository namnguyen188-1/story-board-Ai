import sys,json,tempfile,contextlib,io
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
root=Path(r'D:\STORYBOARD_SKILL_AUDIT_20261105\studio')
sys.path.insert(0,str(root))
import series_studio as studio
class FakeModels:
 def __init__(self):self.requests=[]
 def generate_content(self,**kw):
  self.requests.append(kw['contents'])
  sc={'scene_number':1,'summary':'A mother and daughter talk at home',
   'narration':'A mother and daughter discuss their concerns in a calm conversation that reveals their family situation and leads them to make an important decision together.',
   'description':'A mother speaks to her daughter inside a warm living room.',
   'visual_setup':'Wide shot inside family home', 'text_overlay':''}
  return SimpleNamespace(text=json.dumps({'scenes':[sc]}))
for genre,aspect,expected in [('family_drama','16:9','write-video-scene-prompts'),
 ('documentary','16:9','write-narrative-scene-prompts'),
 ('animation','16:9','write-narrative-scene-prompts'),
 ('stoic','16:9','write-video-scene-prompts'),
 ('family_drama','9:16','write-viral-shorts-prompts'),
 ('family_drama','size_only','write-viral-shorts-prompts')]:
 with tempfile.TemporaryDirectory(prefix='skill_qa_') as td:
  p=Path(td); ep=p/'episode_001';ep.mkdir()
  args=studio.parser().parse_args(['run','--mode','live','--input-mode','idea','--series','QA','--episode','1',
   '--minutes','0.1','--scene-seconds','8','--size',('720x1280' if aspect in ('9:16','size_only') else '1280x720'),
   '--aspect-ratio',('16:9' if aspect=='size_only' else aspect),'--genre',genre,'--visual-style','auto','--region','US','--language','English',
   '--voice-name','Kore','--prompt','A fictional story'])
  if aspect == 'size_only': args.aspect_ratio = ''
  models=FakeModels();fake=SimpleNamespace(models=models)
  bible={'world':'A fictional world','visual_style':'as selected','characters':[],'continuity_rules':'Stay consistent'}
  with patch.object(studio,'own_api_key',return_value='fake-key'),patch.object(studio,'get_api_keys',return_value=[]),patch.object(studio,'ResilientClient',return_value=fake),patch.object(studio,'make_bible',return_value=bible),contextlib.redirect_stdout(io.StringIO()):
   plan=studio.produce_plan(args,p,ep,args.prompt)
  assert len(models.requests)>=1
  assert any('INSTALLED SKILL: '+expected in x for x in models.requests),(genre,aspect)
  print('PASS',genre,aspect,'request contains',expected,'plan name:',plan.get('skill_pipeline',{}).get('name'))
