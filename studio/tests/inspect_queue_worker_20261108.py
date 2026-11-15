import pathlib
p=pathlib.Path(r'D:\STORYBOARD_AI\studio\queue_manager.py')
s=p.read_text(encoding='utf8',errors='replace').splitlines()
for i,l in enumerate(s):
 if any(k in l for k in ('def add_job','def bulk_add_jobs','def start_queue','/api/produce','get("workers"','"workers"','workers=','workers =','subprocess','requests.post')):
  print('\n===',i+1,'===\n'+'\n'.join(f'{j+1}:{s[j]}' for j in range(max(0,i-5),min(len(s),i+15)) if s[j].strip())[:2500])
