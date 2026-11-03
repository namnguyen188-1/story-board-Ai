import sys
with open(r'd:/STORYBOARD_AI/studio/web/app.js', encoding='utf-8') as f:
    lines = f.readlines()

for j in range(22485, 22530):
    l = lines[j].strip()
    if l:
        sys.stdout.buffer.write(f'{j+1}: {l}\n'.encode('utf-8'))
