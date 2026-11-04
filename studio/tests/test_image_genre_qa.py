import importlib.util, sys, pathlib
root=pathlib.Path(r'D:\STORYBOARD_SKILL_AUDIT_20261105')
sys.path.insert(0,str(root/'studio'))
import mcp_v2_batch as candidate
from story_skill_bridge import resolve_skill_name, installed_skill, skill_prompt
from story_arc_quality import beat_guidance
spec=importlib.util.spec_from_file_location('original_image',r'D:\STORYBOARD_AI\studio\mcp_v2_batch.py')
old=importlib.util.module_from_spec(spec); spec.loader.exec_module(old)
scene={'description':'A mother and daughter speak near a statue in the living room','visual_setup':'two women talk together'}
chars=[{'name':'Mother','appearance':'middle aged woman'},{'name':'Daughter','appearance':'young woman'}]
for genre in ('family_drama','drama','romance_melodrama','history','documentary','mafia_thriller','psychological_horror'):
 p=candidate.image_prompt(scene,{'genre':genre,'characters':chars})
 assert 'single solitary subject' not in p.lower(),genre
 assert 'marcus aurelius' not in p.lower(),genre
for genre in ('stoic','philosophy'):
 for characters in ([],chars):
  for s in (scene,{'description':'a thoughtful philosopher','visual_setup':'ancient roman temple'}, {'image_prompt':'a classical marble figure in an ancient temple'}):
   b={'genre':genre,'characters':characters}
   assert candidate.image_prompt(s,b)==old.image_prompt(s,b),(genre,s)
for genre in ('animation','whiteboard','colored_marker'):
 p=candidate.image_prompt({'image_prompt':'A cat walks along a bright village street'}, {'genre':genre})
 assert 'photorealistic 8k' not in p.lower(),genre
mapping={'family_drama':'write-video-scene-prompts','romance_melodrama':'write-video-scene-prompts','psychological_horror':'write-video-scene-prompts','mafia_thriller':'write-video-scene-prompts','documentary':'write-narrative-scene-prompts','history':'write-narrative-scene-prompts','stoic':'write-video-scene-prompts'}
for genre,expected in mapping.items():
 assert resolve_skill_name(genre)==expected
 assert installed_skill(expected)['name']==expected
 assert expected in skill_prompt(genre)
assert resolve_skill_name('family_drama',aspect_ratio='9:16')=='write-viral-shorts-prompts'
for genre in ('romance_melodrama','psychological_horror','mafia_thriller'):
 assert 'Educational/philosophical film' not in beat_guidance(1,3,6,genre)
print('PASS: genre prompts, original Stoic comparison, installed skill routing, story guidance')
