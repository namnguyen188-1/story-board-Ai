from pathlib import Path
p=Path(r"D:\STORYBOARD_AI\studio\cinematic_engine\drama_orchestrator.py")
s=p.read_text(encoding="utf-8")
begin=s.index("    # Scene stills must be composed from the approved 3 asset categories BEFORE")
end=s.index("    scenes_data = raw_plan.get(",begin)
new='''    # Render every missing scene STILL first, then pause for one visual review
    # instead of forcing the user to click Sản xuất once per scene.
    pending_scene_reviews = []
    for scene_data in raw_plan.get("scenes", []):
        scene_num = int(scene_data.get("scene_number", 0))
        scene_dir = episode_dir / "scenes" / f"scene_{scene_num:04d}"
        try:
            bind_scene(episode_dir, scene_data, verify_scene_image=True)
            continue  # Scene image already approved and proven current.
        except AssetGateError:
            # A present but unapproved/stale scene image MUST be reviewed
            # or explicitly repaired; never silently resubmit a paid Muse job.
            pic = scene_dir / "scene_master.png"
            proof = scene_dir / "scene_master.json"
            if pic.is_file() or proof.is_file():
                pending_scene_reviews.append(scene_num)
                continue
            if image_provider != "muse_video":
                raise
            cmd = [str(muse_python), "-u", str(asset_worker), "scene",
                   "--episode-dir", str(episode_dir), "--scene-number", str(scene_num)]
            job = subprocess.run(cmd, timeout=420, check=False, capture_output=True,
                                 text=True, encoding="utf-8", errors="replace",
                                 creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            if job.stdout:
                print(job.stdout[-6500:], flush=True)
            if job.returncode != 0:
                raise AssetGateError("DRAMA_SCENE_IMAGE_GENERATION_FAILED: " +
                                     (job.stderr or job.stdout)[-1200:])
            pending_scene_reviews.append(scene_num)
    if pending_scene_reviews:
        raise AssetGateError(
            "DRAMA_SCENE_IMAGES_NEED_VISUAL_REVIEW: " +
            ",".join(map(str,pending_scene_reviews)) +
            ". All available scene stills have been generated. " +
            "Open 'Duyệt ảnh nhân vật · bối cảnh · đạo cụ' in Phim Kịch Đa Vai, "
            "review each scene image, then press Sản xuất / Tiếp tục again. "
            "No video has been submitted before review.")

'''
s=s[:begin]+new+s[end:]
p.write_text(s,encoding="utf-8")
print("SIX_SCENES_BATCH_PREPRODUCTION_REVIEW_GATE_PATCHED",flush=True)
