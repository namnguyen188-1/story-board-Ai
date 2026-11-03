from pathlib import Path
import re

server_py = Path(r"D:\STORYBOARD_AI\studio\web_server.py")
text = server_py.read_text(encoding="utf-8")

pattern = r'(\s+return self\.end_json\(\{"status": "STOPPING"\}\)\s+)(return self\.end_json\(\{"status": "NOT_RUNNING"\}\))'

replacement = r'''\1try:
                    active_file = WEB_DIR / "active_run_status.json"
                    if active_file.exists():
                        active_file.unlink()
                except Exception:
                    pass
                job_status["running"] = False
                job_status["stage"] = "IDLE"
                job_status["message"] = "Đã dừng tiến trình theo yêu cầu."
                \2'''

if re.search(pattern, text):
    new_text = re.sub(pattern, replacement, text, count=1)
    server_py.write_text(new_text, encoding="utf-8")
    print("PATCH_REGEX_SUCCESS")
else:
    print("REGEX_NOT_FOUND")
