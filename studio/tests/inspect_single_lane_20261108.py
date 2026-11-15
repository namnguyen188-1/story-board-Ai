import pathlib,re
root=pathlib.Path(r'D:\STORYBOARD_AI\studio')
rules={
'web_server.py': ['workers = int(body.get','workers = min(max','"--workers"','if path == "/api/queue/add"','mcp_max_images'],
'web/app.js':['const savedWorkers','window.setWorkerThreads','setWorkerThreads(4)','workers: parseInt','const workers = parseInt'],
'web/index.html':['id="inWorkers"','worker-chip'],
'series_studio.py':['args.workers = max','if args.workers==1','ThreadPoolExecutor','max_workers=args.workers'],
'queue_manager.py':['workers','max_concurrent'],
'studio_mcp/auto_flow_manager.py':['def ensure_ready','def open','def start'],
'flow_account_manager.py':['def launch','def open','def account','ready']
}
for name,terms in rules.items():
 p=root/name
 if not p.is_file():continue
 s=p.read_text(encoding='utf8',errors='replace').splitlines()
 print('\n##########',name,'lines',len(s))
 matches=[i for i,l in enumerate(s) if any(t in l for t in terms)]
 for n,i in enumerate(matches[:25]):
  print('===',i+1,'===\n'+'\n'.join(f'{j+1}:{s[j]}' for j in range(max(0,i-7),min(len(s),i+11)) if s[j].strip())[:2200])
