from pathlib import Path
root=Path(r"D:\STORYBOARD_AI\studio")
router=root/"pipeline_router.py"
r=router.read_text(encoding="utf-8")
old='''        from cinematic_engine.drama_orchestrator import run_cinematic_drama

        return run_cinematic_drama(args_obj)'''
new='''        from cinematic_engine.drama_orchestrator import run_cinematic_drama
        from cinematic_engine.drama_asset_first import AssetGateError

        try:
            return run_cinematic_drama(args_obj)
        except AssetGateError as exc:
            # A visual approval gate is intentional, not a crashed production.
            # Exit code 20 is reserved for WAITING_FOR_ASSET_REVIEW.
            # Other missing-file/provider/consistency errors still fail.
            detail = str(exc)
            if detail.startswith((
                "DRAMA_PREPRODUCTION_NEEDS_VISUAL_REVIEW:",
                "DRAMA_SCENE_IMAGES_NEED_VISUAL_REVIEW:",
            )):
                print("DRAMA_ASSET_REVIEW_REQUIRED: " + detail, flush=True)
                return 20
            raise'''
assert r.count(old)==1,(r.count(old),"ROUTER_BLOCK_NOT_FOUND")
r=r.replace(old,new)
router.write_text(r,encoding="utf-8")
server=root/"web_server.py"
s=server.read_text(encoding="utf-8")
start=s.index("def worker_thread(")
stop=s.index("\n    except Exception as e:",start)
block=s[start:stop]
mark='''        if code == 0:'''
assert block.count(mark)==1
pivot=block.index(mark)
elsemark='''        else:'''
nextelse=block.index(elsemark,pivot)
block=block[:nextelse]+'''        elif code == 20 and not was_stopped:

            # Production is intentionally paused for human approval of
            # actual cast/location/prop reference pictures or scene stills.
            job_status["stage"] = "AWAITING_ASSET_REVIEW"
            job_status["percent"] = max(20, int(job_status.get("percent") or 0))
            job_status["message"] = (
                "Đã tạo ảnh. Cần duyệt ảnh nhân vật, bối cảnh, đạo cụ "
                "hoặc ảnh cảnh trong nút 'Duyệt ảnh', sau đó chọn 'Chạy tiếp'."
            )
            job_status["awaiting_asset_review"] = True

'''+block[nextelse:]
old_hook='''            queue_manager.on_job_completed(series_slug_name, episode_num, code, was_stopped)'''
assert block.count(old_hook)==1
block=block.replace(old_hook,'''            if code != 20:
                queue_manager.on_job_completed(series_slug_name, episode_num, code, was_stopped)
            else:
                print("[DRAMA_ASSET_REVIEW_PAUSE] Queue retained; no job marked failed.", flush=True)''')
s=s[:start]+block+s[stop:]
server.write_text(s,encoding="utf-8")
ui=root/"web"/"app.js"
v=ui.read_text(encoding="utf-8")
key='''    } else if (hasCurrentCompletedVideo || (data.stage === "COMPLETED" && isJobForCurrentEpisode)) {'''
assert v.count(key)==1,(v.count(key),"APP_STATUS_INSERTION_WRONG")
v=v.replace(key,'''    } else if (data.stage === "AWAITING_ASSET_REVIEW" && isJobForCurrentEpisode) {

      el.headerStatusText.textContent = "Cần duyệt ảnh tham chiếu";

'''+key)
ui.write_text(v,encoding="utf-8")
print("PATCHED_GRACEFUL_PAUSE_PIPELINE_AND_UI",flush=True)
