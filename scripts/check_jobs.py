import sqlite3, json
con = sqlite3.connect('D:/FLOWKIT/state/jobs.sqlite')
cur = con.cursor()
rows = cur.execute("SELECT id, provider, state, body FROM jobs WHERE state != 'succeeded' AND state != 'failed'").fetchall()
print(f"Non-terminal jobs: {len(rows)}")
for r in rows:
    b = json.loads(r[3]) if r[3] else {}
    print(r[0], r[1], r[2], b.get('phase'), b.get('browser_hold'))
