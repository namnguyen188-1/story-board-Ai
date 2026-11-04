import sys
from pathlib import Path
sys.path.insert(0,str(Path(r'D:\STORYBOARD_SKILL_AUDIT_20261105\studio')))
from story_skill_bridge import export_idea_scenes
bible={}
ok=[{'scene_number':1,'description':'A bright path in the woods','narration':'A story begins.'}]
missing=[{'scene_number':1,'description':'A bright path in the woods','narration':''}]
for scenes,expected in ((ok,True),(missing,False)):
 _,r=export_idea_scenes(scenes,bible,8,1280,720,genre='documentary')
 assert r['pass'] is expected,(expected,r)
 assert r['validation_scope']=='structural_text_checks_only'
_,r=export_idea_scenes(ok*8,bible,8,720,1280,genre='documentary')
assert not r['pass'] and 'shorts_total_duration_exceeds_58_seconds' in r['errors'],r
print('PASS actual QC detects empty narration and long Shorts; labels scope correctly')
