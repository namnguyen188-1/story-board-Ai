from pathlib import Path
path=Path(r"D:\STORYBOARD_AI\studio\cinematic_engine\drama_orchestrator.py")
s=path.read_text(encoding="utf-8")
start=s.index("    # 0. Pre-Production Master Asset Pack")
end=s.index("    # Multi-role cinema only: validate the installed 9-field skill",start)
replace='''    # 0. REAL Asset-First Production Bible (Cast + Locations + Hero Props).
    # Do NOT call the legacy Pillow "4 angle" blueprint: it mirrors one
    # portrait and silently presents fake views as verified model sheets.
    from .drama_asset_first import build_manifest, validate_assets, bind_scene, AssetGateError
    asset_manifest = build_manifest(episode_dir, raw_plan, style=visual_style)
    print(f"[DRAMA_ASSET_PLAN] {len(asset_manifest['characters'])} characters, "
          f"{len(asset_manifest['locations'])} locations, {len(asset_manifest['props'])} props. "
          "No generated image can be replaced by a mirrored portrait.", flush=True)

'''
s=s[:start]+replace+s[end:]
needle='    print(f"[MULTI_ROLE_SKILL9] VALIDATED {skill_report[\'scene_count\']} scenes / {skill_report[\'total_seconds\']}s", flush=True)'
if s.count(needle)!=1:raise AssertionError("SKILL9_LOG_LOCATION_NOT_UNIQUE")
block='''

    # P0 gate: the script and the complete 3-category Asset Bible MUST exist
    # before image/video generation. For Muse, generate *real master images*
    # on-demand with durable receipts. Missing visual approval stops here.
    preprod_qc = validate_assets(episode_dir, asset_manifest)
    if preprod_qc["status"] != "READY" and image_provider == "muse_video":
        import subprocess
        muse_python = Path(__file__).resolve().parents[1] / "runtime" / "muse" / "python" / "python.exe"
        asset_worker = Path(__file__).resolve().parents[1] / "drama_preproduction_worker.py"
        if not muse_python.is_file() or not asset_worker.is_file():
            raise AssetGateError("DRAMA_MUSE_IMAGE_WORKER_MISSING")
        print("[DRAMA_ASSET_RENDER] Creating real Muse master reference images before video...", flush=True)
        job = subprocess.run(
            [str(muse_python), "-u", str(asset_worker), "assets",
             "--episode-dir", str(episode_dir), "--max-assets", "20"],
            timeout=3600, check=False, capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if job.stdout:
            print(job.stdout[-8000:], flush=True)
        if job.returncode != 0:
            raise AssetGateError("DRAMA_MUSE_IMAGE_GENERATION_FAILED: " +
                                 (job.stderr or job.stdout)[-1500:])
        preprod_qc = validate_assets(episode_dir, asset_manifest)
    if preprod_qc["status"] != "READY":
        raise AssetGateError(
            f"DRAMA_PREPRODUCTION_NEEDS_VISUAL_REVIEW: {len(preprod_qc['blocked'])} "
            "asset groups missing or awaiting approval. Review 00_ASSET_PACK/asset_qc.json. "
            "Video is NOT submitted until the three asset groups are verified.")
    # Scene stills must be composed from the approved 3 asset categories BEFORE
    # Muse video. Reuse existing image + proof to avoid duplicate paid requests.
    for scene_data in raw_plan.get("scenes", []):
        scene_num = int(scene_data.get("scene_number", 0))
        try:
            bind_scene(episode_dir, scene_data, verify_scene_image=True)
        except AssetGateError:
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
            # Fail closed until generated image is visually inspected.
            bind_scene(episode_dir, scene_data, verify_scene_image=True)
'''
s=s.replace(needle,needle+block)
# Remove fake Muse->still successful fallback for this branch; retry is handled above.
marker='                    # SMART RESILIENT FALLBACK: Never fail an entire 100+ scene episode for 1 problematic scene!'
if s.count(marker)!=1:raise AssertionError("FALLBACK_MARKER_COUNT")
s=s.replace(marker,'                    # Asset-first Muse I2V must not silently become a still-motion PASS.\n                    raise RuntimeError("DRAMA_MUSE_I2V_FAILED_NO_STILL_FALLBACK: "+str(render_err)) from render_err\n\n'+marker)
old='''        if qc.get("status") in ("SCENES_VERIFIED", "PASS_WITH_FALLBACKS") and episode_final_mp4.is_file():

            qc["status"] = "PASS"

            qc["publish_allowed"] = True'''
if old not in s:raise AssertionError("NO_FAKE_PASS_BLOCK_NOT_FOUND")
new='''        if qc.get("status") == "SCENES_VERIFIED" and episode_final_mp4.is_file():

            # Technical decode alone is not proof of 3-asset visual continuity
            # or true image-conditioned Muse video.
            qc["status"] = "PENDING_VISUAL_CONTINUITY_REVIEW"
            qc["publish_allowed"] = False'''
s=s.replace(old,new,1)
path.write_text(s,encoding="utf-8")
print("DRAMA_ORCHESTRATOR_ASSET_FIRST_PATCH_PASS",len(s),flush=True)
