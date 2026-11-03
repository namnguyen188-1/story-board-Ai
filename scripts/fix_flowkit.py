import sqlite3, json
from pathlib import Path

# 1. Patch flow_browser.py
fb_path = Path("D:/FLOWKIT/app/flow_browser.py")
fb_txt = fb_path.read_text(encoding="utf-8")

old_code = '''            if job["state"] == "recovery_needed" and job.get("browser_hold") is not False:
                # A reviewed unresumable RPC 502 remains in the ledger, but must
                # not block extension loading on every subsequent cold start.
                return False'''

new_code = '''            if job["state"] == "recovery_needed" and job.get("browser_hold") is not False:
                # An old job with no confirmed remote task must never block extension installation
                if not job.get("remote"):
                    continue
                return False'''

if old_code in fb_txt:
    fb_txt = fb_txt.replace(old_code, new_code)
    fb_path.write_text(fb_txt, encoding="utf-8")
    print("Successfully patched can_install in flow_browser.py")
else:
    print("WARNING: old_code not found in flow_browser.py")

# 2. Mark stuck recovery_needed jobs as failed in jobs.sqlite
con = sqlite3.connect("D:/FLOWKIT/state/jobs.sqlite")
cur = con.cursor()
rows = cur.execute("SELECT id, body FROM jobs WHERE state = 'recovery_needed'").fetchall()
print(f"Found {len(rows)} recovery_needed jobs to resolve")
for r in rows:
    job_id = r[0]
    b = json.loads(r[1]) if r[1] else {}
    b["state"] = "failed"
    b["browser_hold"] = False
    cur.execute("UPDATE jobs SET state = 'failed', body = ? WHERE id = ?", (json.dumps(b), job_id))
    print(f"Resolved job {job_id} -> failed")
con.commit()
con.close()
print("jobs.sqlite successfully cleaned up!")
