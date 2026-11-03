"""Regression: Muse durable receipts may not be deleted by account failover."""
import sys,tempfile,json
from pathlib import Path
from unittest.mock import patch
ROOT=Path(r"D:\STORYBOARD_AI\studio")
sys.path.insert(0,str(ROOT))
import muse_video_provider as v
import muse_accounts
cases=[
 ("MUSE_SCENE_INPUT_CHANGED: previous fingerprint", "MUSE_SCENE_INPUT_CHANGED"),
 ("MUSE_JOB_PENDING: outstanding remote work", "MUSE_JOB_PENDING"),
 ("MUSE_REMOTE_FAILED: Job kết thúc nhưng chưa có video gắn đúng mã cảnh.", "MUSE_SCENE_REVIEW_REQUIRED"),
 ("MUSE_CONNECTION_INTERRUPTED: intermittent", "MUSE_RECEIPT_PROTECTED"),
]
for reason,expected in cases:
    with tempfile.TemporaryDirectory(prefix="muse_guard_") as td:
        scene_dir=Path(td)
        target=scene_dir/"scene_base.png"
        calls=[]
        def fake_worker(action,req,timeout):
            calls.append(action)
            (scene_dir/"muse_job.json").write_text(json.dumps({"state":"accepted","session_id":"DO_NOT_DELETE","tag":"TEST"}),encoding="utf-8")
            raise RuntimeError(reason)
        mock_acc={"id":"qa","name":"qa","profile_home":None}
        with patch.object(muse_accounts,"get_account_for_scene",return_value=mock_acc) as acc_mock:
            with patch.object(v,"_worker",side_effect=fake_worker):
                try:
                    v.make_scene_media({"scene_number":63,"raw_9_fields":"TEST"},
                                      {},target,width=720,height=1280,duration=10)
                except RuntimeError as exc:
                    assert expected in str(exc),(expected,str(exc))
                else:
                    raise AssertionError("Expected error, got fake successful video")
        assert calls==["render"],calls
        assert acc_mock.call_count==1,acc_mock.call_count
        assert json.loads((scene_dir/"muse_job.json").read_text())["session_id"]=="DO_NOT_DELETE"
        print("PASS",expected,flush=True)
print("NO_DUPLICATE_MUSE_ACCOUNT_FALLBACK_4/4_PASS")
