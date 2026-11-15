from pathlib import Path
s=Path(r"D:\STORYBOARD_AI\studio\web_server.py").read_text(encoding="utf8").splitlines()
for a,b in [(274500,278550),(286400,287300),(315800,319000)]:
 print("\n=== RANGE",a,b,"===")
 count=0
 for i in range(a-1,b):
  if s[i].strip():
   print(f"{i+1}: {s[i][:200]}")
   count+=1
   if count>=85:break
