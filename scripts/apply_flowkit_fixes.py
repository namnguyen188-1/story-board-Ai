import sqlite3, json
from pathlib import Path

# 1. Clean jobs.sqlite
conn = sqlite3.connect('D:/FLOWKIT/state/jobs.sqlite')
c = conn.cursor()
c.execute("SELECT id, body FROM jobs WHERE state = 'recovery_needed' OR body LIKE '%recovery_needed%'")
rows = c.fetchall()
print('Found recovery_needed jobs to fix:', len(rows))
for jid, body_str in rows:
    try:
        b = json.loads(body_str)
        b['state'] = 'failed'
        c.execute('UPDATE jobs SET state = ?, body = ? WHERE id = ?', ('failed', json.dumps(b), jid))
    except Exception as e:
        print('Error fixing job:', jid, e)
conn.commit()
conn.close()
print('Cleaned jobs.sqlite!')

# 2. Patch flow_browser.py
fb_path = Path('D:/FLOWKIT/app/flow_browser.py')
fb_txt = fb_path.read_text(encoding='utf-8')
old_can_install = '''    def can_install():
        for job in Store(STATE / "jobs.sqlite").list(10000):
            if job["provider"] not in {"flow", "webtool"}:
                continue
            if job["state"] == "recovery_needed" and job.get("browser_hold") is not False:
                # An old job with no confirmed remote task must never block extension installation
                if not job.get("remote"):
                    continue
                return False
            if job["state"] == "running" and (
                job.get("remote") or job.get("phase") not in {"new", "webtool_checking"}
            ):
                return False
        return True'''

new_can_install = '''    def can_install():
        now = time.time()
        for job in Store(STATE / "jobs.sqlite").list(100):
            if job.get("provider") not in {"flow", "webtool"}:
                continue
            if job.get("state") == "running" and (now - job.get("updated_at", 0) < 60):
                if job.get("remote") or job.get("phase") not in {"new", "webtool_checking"}:
                    return False
        return True'''

if old_can_install in fb_txt:
    fb_txt = fb_txt.replace(old_can_install, new_can_install)
    fb_path.write_text(fb_txt, encoding='utf-8')
    print('Patched flow_browser.py successfully!')
else:
    print('Notice: old_can_install not matched exactly, checking...')

# 3. Patch flow_webtool_worker.py
fww_path = Path('D:/FLOWKIT/app/flow_webtool_worker.py')
fww_txt = fww_path.read_text(encoding='utf-8')

old_loop = '''    deadline = time.monotonic() + settings()["job_timeout_seconds"]
    while time.monotonic() < deadline:
        state = await asyncio.to_thread(WebToolAdapter(mode).status)
        matches = [x for x in state["queue"] if x["id"] == shot_id]
        if not matches:
            raise WebToolError("WEBTOOL_SHOT_NOT_FOUND_AFTER_START",409)'''

new_loop = '''    deadline = time.monotonic() + settings()["job_timeout_seconds"]
    match_wait_until = time.monotonic() + 15.0
    while time.monotonic() < deadline:
        state = await asyncio.to_thread(WebToolAdapter(mode).status)
        matches = [x for x in state["queue"] if x["id"] == shot_id]
        if not matches:
            if time.monotonic() < match_wait_until:
                await asyncio.sleep(0.5)
                continue
            raise WebToolError("WEBTOOL_SHOT_NOT_FOUND_AFTER_START",409)'''

if old_loop in fww_txt:
    fww_txt = fww_txt.replace(old_loop, new_loop)
    fww_path.write_text(fww_txt, encoding='utf-8')
    print('Patched flow_webtool_worker.py successfully!')
else:
    print('Notice: old_loop not matched exactly in flow_webtool_worker.py')

# 4. Patch flow_webtool_jobs.py to add b.queue immediate push
fwj_path = Path('D:/FLOWKIT/app/flow_webtool_jobs.py')
fwj_txt = fwj_path.read_text(encoding='utf-8')
target_sub = '''              const created = arr[0];
              created.id = ID;
              if (created.parsed) {
                created.parsed.aspectRatio = ASPECT;
              }
              setTimeout(() => {'''

repl_sub = '''              const created = arr[0];
              created.id = ID;
              if (created.parsed) {
                created.parsed.aspectRatio = ASPECT;
              }
              b.queue = b.queue || [];
              if (!b.queue.some(x => x.id === ID)) {
                b.queue.push(created);
              }
              setTimeout(() => {'''

if target_sub in fwj_txt:
    fwj_txt = fwj_txt.replace(target_sub, repl_sub)
    fwj_path.write_text(fwj_txt, encoding='utf-8')
    print('Patched flow_webtool_jobs.py successfully!')
else:
    print('Notice: target_sub not matched in flow_webtool_jobs.py')
