from pathlib import Path
import ast
p=Path(r'D:\STORYBOARD_AI\studio\project_organizer.py')
s=p.read_text(encoding='utf-8-sig')
t=ast.parse(s)
for node in ast.walk(t):
 if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name=='organize_episode':
  print('FUNCTION',ast.unparse(node.args),'LINE',node.lineno)
  x=ast.get_source_segment(s,node)
  print('\n'.join(z for z in x.splitlines() if z.strip())[:12500])
