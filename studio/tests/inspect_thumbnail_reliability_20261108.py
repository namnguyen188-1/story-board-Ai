from pathlib import Path
root=Path(r'D:\STORYBOARD_AI\studio')
targets={'seo_packager.py':['def generate_thumbnail_with_flow','def','mcp_v2_images','thumbnail_seo','thumbnail_shorts','generate_thumbnail','reuse'], 'thumbnail_studio.py':['def generate','mcp_v2','thumbnail','def '], 'web_server.py':['generate_thumbnail_with_flow','/api/episode/seo','/api/thumbnail','thumbnail_shorts'], 'tests':['test_thumbnail','test_mcp','test_single_lane']}
for f,terms in targets.items():
 p=root/f
 if not p.exists():continue
 if p.is_dir():
  print('TESTS',[(x.name) for x in p.glob('test_*') if any(t in x.name for t in terms)][:65]);continue
 lines=p.read_text(encoding='utf8',errors='replace').splitlines()
 print('\nFILE',f,len(lines))
 for i,l in enumerate(lines):
  if any(t in l for t in terms) and (f!='seo_packager.py' or not l.startswith('def ') or any(k in l for k in ('thumbnail','flow'))):
   if f=='web_server.py' and len(l)>400:continue
   print(i+1,l.strip()[:195])
   if f=='seo_packager.py' and i>10000:break
