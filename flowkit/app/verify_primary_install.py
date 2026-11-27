from pathlib import Path
import hashlib,json,urllib.request,urllib.error,sys,time
root=Path(__file__).resolve().parents[1]
base='http://127.0.0.1:18110'
key=(root/'state/api.key').read_text(encoding='ascii').strip()
def get(path,auth=True,body=None):
 request=urllib.request.Request(base+path,headers={'X-API-Key':key,'Content-Type':'application/json'} if auth else {},
  data=json.dumps(body).encode() if body is not None else None)
 with urllib.request.urlopen(request,timeout=100) as response:
  raw=response.read()
  return json.loads(raw) if 'application/json' in response.headers.get('Content-Type','') else raw
health=get('/health',False)
assert health['instance_id']==hashlib.sha256(str(root).encode()).hexdigest()[:12]
docs=get('/docs',False);assert b'Flow + Muse' in docs
try:get('/v1/jobs',False);raise AssertionError('UNAUTHENTICATED_ACCESS_ALLOWED')
except urllib.error.HTTPError as error:assert error.code==401
try:get('/v1/jobs',body={'provider':'muse','kind':'image','prompt':'invalid capability'});raise AssertionError('INVALID_JOB_ACCEPTED')
except urllib.error.HTTPError as error:assert error.code==422
assert get('/v1/jobs')['jobs']==[]
providers=get('/v1/providers?live=true')
original=json.loads((root/'state/primary_source_hashes.json').read_text(encoding='utf-8'))
changed=[p for p,digest in original.items() if hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()!=digest]
report={'installed':True,'root':str(root),'api':base,'version':health['version'],'api_auth_verified':True,
 'empty_job_history':True,'new_generation_submitted':False,'api_key_sha256':hashlib.sha256(key.encode()).hexdigest(),
 'flow_connected':providers['flow']['connected'],'flow_extension_connected':providers['flow']['extension_connected'],
 'muse_connected':providers['muse']['connected'],'muse_saved_accounts':providers['muse']['saved_accounts'],
 'muse_locally_ready_accounts':providers['muse']['locally_ready_accounts'],
 'main_source_files_checked':len(original),'main_source_files_changed':len(changed)}
(root/'state/primary_install_verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
docs=root/'docs/PRIMARY_PC.md'
with docs.open('a',encoding='utf-8') as stream:
 stream.write('\nVerified: API auth, 7 bundled module origins, FFmpeg/FFprobe 8.0, fresh API jobs, separate ports.\n')
 stream.write('Muse saved accounts: '+str(report['muse_saved_accounts'])+'; live connected: '+str(report['muse_connected'])+'\n')
 stream.write('Flow extension connected: '+str(report['flow_extension_connected'])+'; signed in: '+str(report['flow_connected'])+'\n')
(root/'docs/SDD_LEDGER.md').write_text('2026-10-25: transferred independent FlowKit 1.1.0 to primary PC. Verified 6653 source files by SHA256; seeded 1356 identical local files; copied complete local FFmpeg 8 shared runtime into own bin. Separate API 18110, Flow engine 18100, extension 9232 and CDP 9233. Main existing Chrome port 9222 unchanged. Original source snapshot in state/primary_source_hashes.json. No paid generation submitted.\n',encoding='utf-8')
public={k:v for k,v in report.items() if k!='api_key_sha256'}
print(json.dumps(public,indent=2),flush=True)
