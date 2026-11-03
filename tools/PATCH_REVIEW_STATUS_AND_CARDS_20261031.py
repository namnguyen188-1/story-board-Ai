from pathlib import Path
root=Path(r"D:\STORYBOARD_AI\studio")
server=root/"web_server.py"
s=server.read_text(encoding="utf-8")
needle='''    job_status["user_stopped"] = False'''
assert s.count(needle)>=1
start=s.index("def worker_thread(")
before=s[:start];block=s[start:]
assert needle in block
block=block.replace(needle,'''    job_status["user_stopped"] = False
    job_status["awaiting_asset_review"] = False''',1)
s=before+block
server.write_text(s,encoding="utf-8")
api=root/"drama_asset_review_api.py"
a=api.read_text(encoding="utf-8")
needle2='''        proof=folder/"scene_master.json"
        accepted=False;reason="SCENE_IMAGE_NOT_RENDERED"'''
new='''        proof=folder/"scene_master.json"
        # Show only generated scene stills. Unrendered placeholders for 66
        # scenes overwhelm the actual 17 master assets in the review dialog.
        if not (folder/"scene_master.png").is_file() and not proof.is_file():
            continue
        accepted=False;reason="SCENE_IMAGE_NOT_RENDERED"'''
assert a.count(needle2)==1
api.write_text(a.replace(needle2,new),encoding="utf-8")
print("AWAITING_REVIEW_STATUS_RESET_AND_REVIEW_CARDS_COMPACT_PASS",flush=True)
