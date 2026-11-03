from pathlib import Path

p = Path(r"D:\STORYBOARD_AI\studio\web_server.py")
s = p.read_text(encoding="utf-8")

sub = '''                if (job_status.get("awaiting_asset_review") or
                        job_status.get("stage") == "AWAITING_ASSET_REVIEW"):
                    # Navigating to a new episode must not silently discard a
                    # durable review gate for another episode. The user can
                    # resume or explicitly review the current saved assets.
                    return self.end_json({"status": "REVIEW_PENDING", "job": job_status})'''

if sub in s:
    s = s.replace(sub, '''                job_status["awaiting_asset_review"] = False''')
    p.write_text(s, encoding="utf-8")
    print("PATCH_SERVER_RESET_APPLIED")
else:
    print("SUBSTRING_NOT_FOUND")
