from pathlib import Path
p=Path(r"D:\STORYBOARD_AI\studio\tests\inspect_offline_thumbnail_api_20261108.py")
s=p.read_text(encoding="utf8")
assert s.count("utf8-sig")==1
p.write_text(s.replace("utf8-sig","utf-8-sig"),encoding="utf8")
print("ENCODING_FIXED")
