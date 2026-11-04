import sys,json,tempfile
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
root=Path(r'D:\STORYBOARD_SKILL_AUDIT_20261105\studio')
sys.path.insert(0,str(root))
import series_studio as s
from story_skill_bridge import resolve_skill_name, skill_prompt, installed_skill
from studio_modes import GENRES
genres=[g for g in GENRES if g!='auto']
for genre in genres:
 for aspect in ('16:9','9:16'):
  expected=resolve_skill_name(genre,'narrative',aspect)
  content=skill_prompt(genre,'narrative',aspect)
  assert 'INSTALLED SKILL: '+expected in content,(genre,aspect,expected)
  assert installed_skill(expected)['name']==expected
try: installed_skill('skill-definitely-missing')
except RuntimeError as e: assert 'SKILL_MISSING' in str(e)
else: raise AssertionError('missing skill must not substitute another')
print('PASS skill selection and real skill loading across %s genres, 2 aspect ratios; missing skill rejected' % len(genres))
long_line='CẢNH 1\nĐêm trong căn phòng.\n"Chúng ta cần nói chuyện."'
with tempfile.TemporaryDirectory() as td:
 args=s.parser().parse_args(['run','--mode','live','--input-mode','script','--series','QA','--episode','1','--minutes','1','--scene-seconds','8','--size','1280x720','--genre','family_drama','--visual-style','color_cinematic','--region','VN','--language','Vietnamese','--voice-name','Kore','--prompt',long_line])
 with patch.object(s,'own_api_key',side_effect=AssertionError('script must not call LLM')):
  p=Path(td); plan=s.produce_plan(args,p,p/'episode_001',long_line)
 assert plan['config']['prompt']==long_line
 assert plan['scenes'][0]['narration']=='Chúng ta cần nói chuyện.'
 print('PASS locked script does not call LLM; source and quoted narration retained')
