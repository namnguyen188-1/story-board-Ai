import importlib.util,sys,pathlib
root=pathlib.Path(r'D:\STORYBOARD_SKILL_AUDIT_20261105\studio');sys.path.insert(0,str(root))
import mcp_v2_batch as new
spec=importlib.util.spec_from_file_location('original',r'D:\STORYBOARD_AI\studio\mcp_v2_batch.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
scene={'description':'A woman walks down a busy street','visual_setup':'A street at dusk'}
for character in [
 {'name':'Linh','clone_prompt':'adult woman wearing a red coat','appearance':'adult woman'},
 {'name':'Linh','clone_prompt':'','appearance':'adult woman wearing a red coat','personality':'Cloned protagonist: Linh'},
]:
 bible={'genre':'family_drama','characters':[character]}
 assert new.image_prompt(scene,bible)==old.image_prompt(scene,bible),character
 assert 'single solitary subject' in new.image_prompt(scene,bible).lower()
print('PASS: explicit clone and cloned appearance-only preserve original output')
