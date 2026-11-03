from pathlib import Path
import py_compile,shutil
root=Path(r"D:\STORYBOARD_AI\studio")
p=root/"series_studio.py"
backup=root/"checkpoints"/"mcp_batch_e2e_20261012"
backup.mkdir(parents=True,exist_ok=True)
shutil.copy2(p,backup/p.name)
s=p.read_text(encoding="utf-8")
start=s.index('''            if job.get("image_provider")=="mcp_v2":''')
end=s.index('''            else:
                imgprompt=prompt_tool_fn''',start)
s=s[:start]+'''            if job.get("image_provider")=="mcp_v2":
                raise RuntimeError("MCP_BATCH_IMAGE_NOT_AVAILABLE: no scene-level resubmission")
'''+s[end:]
needle='''    write_json(manifest_file,report)
    first_image=None'''
assert needle in s
s=s.replace(needle,'''    write_json(manifest_file,report)
    if args.mode=="live" and args.image_provider=="mcp_v2":
        from mcp_v2_batch import generate_episode_images
        try:
            generate_episode_images(scenes,plan["bible"],
                series=args.series,episode=args.episode,episode_dir=episode_dir,
                max_new_images=args.mcp_max_images,
                model_index=args.mcp_model_index)
        except Exception as e:
            report.update({"status":"BLOCKED_MCP_IMAGE","updated":stamp(),
                           "blocker_type":type(e).__name__})
            write_json(manifest_file,report)
            raise
    first_image=None''',1)
p.write_text(s,encoding="utf-8")
for file in [p,root/"mcp_v2_batch.py",root/"mcp_v2_images.py",root/"studio_gui.py"]:
    py_compile.compile(str(file),doraise=True)
print("MCP_BATCH_PATCH_PASS")
print("NO_SCENE_LEVEL_RESUBMIT_GUARD_PASS")
