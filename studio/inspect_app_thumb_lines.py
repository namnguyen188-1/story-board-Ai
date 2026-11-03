with open(r'd:/STORYBOARD_AI/studio/web/app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for j in range(22480, 22530):
    print(f"{j+1}: {repr(lines[j])}")
