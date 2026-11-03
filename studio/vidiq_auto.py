"""Automatic official title ratings. No invented aggregate SEO or CTR score."""
import base64,ctypes,hashlib,json,os,tempfile,threading
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import Request,urlopen

ROOT=Path(__file__).resolve().parent
LOCK=threading.RLock()
ENDPOINT='https://mcp.vidiq.com/mcp'

def _protect(data,decrypt=False):
    if os.name!='nt':raise ValueError('Windows credential protection required')
    from ctypes import wintypes
    class Blob(ctypes.Structure):
        _fields_=[('cbData',wintypes.DWORD),('pbData',ctypes.POINTER(ctypes.c_ubyte))]
    buf=ctypes.create_string_buffer(data);src=Blob(len(data),ctypes.cast(buf,ctypes.POINTER(ctypes.c_ubyte)));out=Blob()
    api=ctypes.windll.crypt32
    if decrypt:ok=api.CryptUnprotectData(ctypes.byref(src),None,None,None,None,1,ctypes.byref(out))
    else:ok=api.CryptProtectData(ctypes.byref(src),None,None,None,None,1,ctypes.byref(out))
    if not ok:raise ValueError('Credential protection failed')
    try:return ctypes.string_at(out.pbData,out.cbData)
    finally:ctypes.windll.kernel32.LocalFree(out.pbData)

def save_key(key):
    key=str(key).strip()
    if len(key)<15 or any(c.isspace() for c in key):raise ValueError('Khóa vidIQ không hợp lệ')
    _atomic(ROOT/'vidiq_credential.dpapi',base64.b64encode(_protect(key.encode())).decode())

def api_key():
    key=os.environ.get('VIDIQ_API_KEY','').strip()
    if key:return key
    try:return _protect(base64.b64decode((ROOT/'vidiq_credential.dpapi').read_bytes()),True).decode()
    except Exception:return ''

def _atomic(path,text):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=path.parent,delete=False) as f:f.write(text);tmp=f.name
    try:os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

class Client:
    def __init__(self,key):
        self.key=key;self.session=None;self.seq=0
        self.rpc('initialize',{'protocolVersion':'2025-03-26','capabilities':{},'clientInfo':{'name':'StoryboardSEO','version':'1.0'}})
        self.rpc('notifications/initialized',{},notification=True)
        listing=self.rpc('tools/list',{})
        self.tool=next(t for t in listing.get('tools',[]) if t['name'] in ('vidiq_score_title','score_title'))
    def rpc(self,method,params,notification=False):
        self.seq+=1
        body={'jsonrpc':'2.0','method':method,'params':params}
        if not notification:body['id']=self.seq
        headers={'Authorization':'Bearer '+self.key,'Content-Type':'application/json','Accept':'application/json, text/event-stream'}
        if self.session:headers['Mcp-Session-Id']=self.session;headers['MCP-Protocol-Version']='2025-03-26'
        with urlopen(Request(ENDPOINT,json.dumps(body).encode(),headers),timeout=20) as r:
            self.session=r.headers.get('Mcp-Session-Id',self.session)
            raw=r.read().decode()
        if notification:return {}
        if raw.lstrip().startswith('data:') or '\ndata:' in raw:
            messages=[json.loads(line[5:].strip()) for line in raw.splitlines() if line.startswith('data:')]
            response=next(x for x in messages if x.get('id')==self.seq)
        else:response=json.loads(raw)
        if 'error' in response:raise ValueError('MCP request failed')
        return response.get('result',{})
    def score_title(self,title,kind):
        result=self.rpc('tools/call',{'name':self.tool['name'],'arguments':{'title':title,'type':kind}})
        if result.get('isError'):raise ValueError('vidIQ scoring failed')
        data=result.get('structuredContent')
        if not isinstance(data,dict):
            data=next((json.loads(c['text']) for c in result.get('content',[]) if c.get('type')=='text' and c.get('text','').lstrip().startswith('{')),None)
        if not isinstance(data,dict):raise ValueError('Missing structured rating')
        score=data.get('score')
        if isinstance(score,bool) or not isinstance(score,(int,float)) or not 0<=score<=100:raise ValueError('Invalid rating')
        return data

def ensure_scores(root,package):
    with LOCK:
        key=api_key();titles=[str(t.get('title','')).strip() for t in (package.get('titles') or [])[:3]]
        state={'status':'not_connected','source':'vidiq_mcp' if key else None,'total_score':None,'title_scores':[],
               'thumbnail':{'status':'requires_video_id','score':None,'message':'API thumbnail yêu cầu video ID; chưa chấm ảnh trước đăng.'},
               'message':'Nhập khóa vidIQ một lần để tự chấm sau khi tạo gói SEO.'}
        package['official_vidiq']=state
        if not key:return package
        cache_path=Path(root)/'.vidiq_title_scores.json'
        try:cache=json.loads(cache_path.read_text(encoding='utf-8'))
        except Exception:cache={}
        client=None;kind='short' if package.get('video_format')=='short' else 'long'
        for title in titles:
            if not title:continue
            digest=hashlib.sha256((key+'\0'+kind+'\0'+title).encode()).hexdigest()
            entry=cache.get(digest)
            if not isinstance(entry,dict):
                entry={'title':title,'score':None,'status':'pending','measured_at':None,'credits_used':None}
                try:
                    if client is None:client=Client(key)
                except Exception:
                    entry.update(status='connection_failed',message='Chưa kết nối được vidIQ; sẽ thử kết nối khi mở lại.')
                    state['title_scores'].append(entry)
                    continue
                # Persist before sending: a lost response must never cause an automatic paid retry.
                cache[digest]=entry;_atomic(cache_path,json.dumps(cache,ensure_ascii=False))
                try:
                    result=client.score_title(title,kind)
                    score=result.get('score')
                    if isinstance(score,bool) or not isinstance(score,(int,float)) or not 0<=score<=100:raise ValueError('Invalid rating')
                    entry.update(score=score,status='scored',measured_at=datetime.now(timezone.utc).isoformat(),credits_used=(result.get('_credits') or {}).get('used'))
                except Exception:
                    entry.update(status='unavailable',message='Chưa lấy được điểm; không tự gọi lại để tránh trừ credit lặp.')
                _atomic(cache_path,json.dumps(cache,ensure_ascii=False))
            state['title_scores'].append(dict(entry))
        good=[x for x in state['title_scores'] if x.get('status')=='scored']
        state['status']='scored' if good and len(good)==len(state['title_scores']) else 'partial' if good else 'unavailable'
        state['message']='vidIQ: điểm dự đoán sức hút tiêu đề; không phải tổng điểm SEO hoặc CTR đo được.'
        return package
