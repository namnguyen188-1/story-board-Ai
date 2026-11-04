import sys,tempfile,copy
from pathlib import Path
sys.path.insert(0,r'D:\STORYBOARD_SKILL_AUDIT_20261105\studio')
from cinematic_engine.drama_skill9 import export_episode,build_scene
from cinematic_engine.drama_auto_repair import sanitize_forbidden_words
def make(words):
 return {'scene_number':1,'summary':'A person speaks in a room.','setting':'A room',
  'visual_setup':'A simple room','dialogue_beats':[{'speaker':'Linh','text':words}]}
scene=make('I saw a gun.')
before=build_scene(scene,{},None,genre='drama',visual_style='color_cinematic',language='English',aspect='16:9')
assert '"I saw a gun."' in before and '"I saw a badge holder."' in sanitize_forbidden_words(before)
plan={'scenes':[scene],'cast':{}}
with tempfile.TemporaryDirectory() as t:
 try:
  export_episode(plan,Path(t),genre='drama',visual_style='color_cinematic',language='English',aspect='16:9',preserve_dialogue=True)
 except RuntimeError as e:
  assert 'DRAMA_LOCKED_DIALOGUE_CHANGED' in str(e),e
 else: raise AssertionError('changed locked dialogue should be blocked')
 assert plan['scenes'][0]['dialogue_beats'][0]['text']=='I saw a gun.'
 assert not (Path(t)/'scene_prompts_9_fields.txt').exists()
print('PASS: script dialogue replacement detected and blocked before export; source retained')

plain={'scenes':[make('We must leave now.')],'cast':{}}
with tempfile.TemporaryDirectory() as t:
 report=export_episode(plain,Path(t),genre='drama',visual_style='color_cinematic',language='English',aspect='16:9',preserve_dialogue=True)
 assert report['pass']
 content=(Path(t)/'scene_prompts_9_fields.txt').read_text(encoding='utf-8')
 assert '"We must leave now."' in content
print('PASS: ordinary locked dialogue passes real nine-field validator unchanged')
