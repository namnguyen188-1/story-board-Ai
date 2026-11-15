import ast
from pathlib import Path
p=Path(r"D:\STORYBOARD_AI\studio\seo_packager.py")
s=p.read_text(encoding="utf-8-sig")
tree=ast.parse(s)
for nm in ("generate_thumbnail_image","generate_shorts_thumbnail_cover","generate_thumbnail_with_flow"):
 nd=next(n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==nm)
 print("\nFUNCTION",nm,"line",nd.lineno,"args",ast.unparse(nd.args),"returns",ast.unparse(nd.returns) if nd.returns else None)
 code=ast.get_source_segment(s,nd)
 lines=[line for line in code.splitlines() if line.strip()]
 print("\n".join(lines[:80]))
