from pathlib import Path
p=Path(r"D:\STORYBOARD_AI\studio\web_server.py")
s=p.read_text(encoding="utf-8")
start=s.index('        elif path in ("/api/status/reset", "/api/reset_status"):')
end=s.index('        elif path == "/api/config/vidiq":',start)
block=s[start:end]
old='''                if not job_status["running"]:

'''
new='''                if (job_status.get("awaiting_asset_review") or
                        job_status.get("stage") == "AWAITING_ASSET_REVIEW"):
                    # Navigating to a new episode must not silently discard a
                    # durable review gate for another episode. The user can
                    # resume or explicitly review the current saved assets.
                    return self.end_json({"status": "REVIEW_PENDING", "job": job_status})

                if not job_status["running"]:

'''
assert block.count(old)==1,block[:380]
s=s[:start]+block.replace(old,new)+s[end:]
p.write_text(s,encoding="utf-8")
print("STATUS_RESET_NOW_PRESERVES_AWAITING_ASSET_REVIEW",flush=True)
