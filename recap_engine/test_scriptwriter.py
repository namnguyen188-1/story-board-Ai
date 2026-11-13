import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from core.scriptwriter import RecapScriptwriter

writer = RecapScriptwriter()
result = writer.generate_recap_script(
    movie_title='Kẻ Hủy Diệt 2',
    genre='Hành động Viễn tưởng',
    target_minutes=1,
    user_aliases={'Kẻ Hủy Diệt T-800': 'anh Cơ Bắp', 'John Connor': 'bé Cưng', 'T-1000': 'sát thủ Kim Loại Lỏng'}
)
print('✅ Generated Script Title:', result.get('title'))
print('Hook:', result.get('hook'))
print('Aliases:', result.get('character_aliases'))
print('Total segments:', len(result.get('segments', [])))
for s in result.get('segments', [])[:3]:
    print(f"  [{s.get('act')}] {s.get('text')} ({s.get('est_duration')}s)")
