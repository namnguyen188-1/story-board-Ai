from pathlib import Path
p=Path(r'D:\STORYBOARD_AI\studio\web_server.py')
s=p.read_text(encoding='utf-8',errors='replace').splitlines()
for a,b in [(276950,277450),(286550,286960),(334720,335420)]:
 print('\n====',a,b,'====')
 for j in range(a-1,min(b,len(s))):
  if s[j].strip():print(f'{j+1}: {s[j][:220]}')
