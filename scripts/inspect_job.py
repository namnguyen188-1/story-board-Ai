import sqlite3, json
con = sqlite3.connect('D:/FLOWKIT/state/jobs.sqlite')
cur = con.cursor()
row = cur.execute("SELECT id, provider, state, body FROM jobs WHERE id = '8eb30fa7-7050-4169-8ffe-bd9f8d522558'").fetchone()
if row:
    print(row[0], row[1], row[2])
    print(json.dumps(json.loads(row[3]), indent=2))
