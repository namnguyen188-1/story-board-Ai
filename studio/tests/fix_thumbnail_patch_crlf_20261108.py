from pathlib import Path
p=Path(r'D:\STORYBOARD_AI\studio\tests\apply_thumbnail_reliability_fix_20261108.py')
s=p.read_text(encoding="utf8")
a='text=original.decode("utf-8-sig")'
b='text=original.decode("utf-8-sig").replace("\\r\\n", "\\n")'
c='temp.write_bytes(text.encode("utf8"))'
f='temp.write_bytes(text.replace("\\n", "\\r\\n").encode("utf8"))'
assert s.count(a)==1 and s.count(c)==1
s=s.replace(a,b).replace(c,f)
p.write_text(s,encoding="utf8")
print("PATCH_SCRIPT_CRLF_SAFE")
