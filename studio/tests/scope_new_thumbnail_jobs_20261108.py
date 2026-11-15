from pathlib import Path
p=Path(r'D:\STORYBOARD_AI\studio\tests\run_live_thumbnail_stability_20261108.py')
s=p.read_text(encoding="utf8")
a='base=root/"runtime/thumbnail_reliability_qa_20261108"/variant'
b='base=root/"runtime/thumbnail_reliability_qa_20261108"/(variant+"_r2")'
c='"QA_STOIC_THUMB_20261108_"+variant.upper()'
f='"QA_STOIC_THUMB_20261108_"+variant.upper()+"_R2"'
assert s.count(a)==1 and s.count(c)==2
s=s.replace(a,b).replace(c,f)
p.write_text(s,encoding="utf8")
print("QA_SCOPES_CHANGED",s.count("_R2"))
