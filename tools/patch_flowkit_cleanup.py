import re
from pathlib import Path

p = Path("studio/flowkit_client.py")
text = p.read_text(encoding="utf-8")
old = """def ensure_flowkit_running(max_wait_seconds: int = 15) -> bool:
    \"\"\"Ensure FlowKit API is running; if down, attempt background launch.\"\"\"
    if is_flowkit_alive():
        return True"""

new = """def cleanup_stale_flowkit_jobs():
    \"\"\"Unblock FlowKit if previous jobs were left in recovery_needed state.\"\"\"
    db_file = FLOWKIT_ROOT / "state" / "jobs.sqlite"
    if not db_file.is_file():
        return
    try:
        import sqlite3
        with sqlite3.connect(str(db_file), timeout=5) as conn:
            conn.execute("UPDATE jobs SET state = 'failed' WHERE state = 'recovery_needed'")
            conn.commit()
    except Exception:
        pass


def ensure_flowkit_running(max_wait_seconds: int = 15) -> bool:
    \"\"\"Ensure FlowKit API is running; if down, attempt background launch.\"\"\"
    cleanup_stale_flowkit_jobs()
    if is_flowkit_alive():
        return True"""

# Normalize CRLF / LF for matching
old_crlf = old.replace("\n", "\r\n")
new_crlf = new.replace("\n", "\r\n")

if old_crlf in text:
    text = text.replace(old_crlf, new_crlf, 1)
    p.write_text(text, encoding="utf-8")
    print("Patched flowkit_client.py (CRLF)!")
elif old in text:
    text = text.replace(old, new, 1)
    p.write_text(text, encoding="utf-8")
    print("Patched flowkit_client.py (LF)!")
else:
    print("Target not found in flowkit_client.py")
