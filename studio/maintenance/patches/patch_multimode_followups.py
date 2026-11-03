from pathlib import Path
import py_compile
root=Path(r"D:\STORYBOARD_AI\studio")
file=root/"series_studio.py"
s=file.read_text(encoding="utf-8")
def repl(a,b,n):
    global s
    assert a in s,("MISSING",n)
    s=s.replace(a,b,1)
repl('''    args.genre=resolve_genre(args.genre)
    args.visual_style=resolve_style(args.visual_style,args.genre)
    if args.region not in REGIONS:
        raise ValueError("Unknown region")
    args.voice_name=voice_for(args.language,args.genre,args.region,args.voice_name)''',
'''    original_genre=args.genre
    original_visual_style=args.visual_style
    original_voice=args.voice_name
    args.genre=resolve_genre(args.genre)
    args.visual_style=resolve_style(args.visual_style,args.genre)
    if args.region not in REGIONS:
        raise ValueError("Unknown region")
    args.voice_name=voice_for(args.language,args.genre,args.region,args.voice_name)''',"requested_presets")
repl('''            if args.genre=="documentary" and str(details.get("genre")) in GENRES:
                args.genre=resolve_genre("auto",details.get("genre"))
                args.visual_style=resolve_style(args.visual_style,args.genre)''',
'''            if original_genre=="auto" and str(details.get("genre")) in GENRES:
                args.genre=resolve_genre("auto",details.get("genre"))
                args.visual_style=resolve_style(original_visual_style,args.genre)
                args.voice_name=voice_for(args.language,args.genre,args.region,original_voice)''',"auto_video_genre_voice")
repl('''                imgprompt=prompt_tool_fn(scene["description"],visual_setup=scene.get("visual_setup",""),
                                        text_overlay=scene.get("text_overlay",""),
                                        global_plan=job["bible"])''',
'''                if job.get("visual_style","whiteboard")!="whiteboard":
                    from mcp_v2_batch import image_prompt
                    imgprompt=image_prompt(scene,job["bible"])
                else:
                    imgprompt=prompt_tool_fn(scene["description"],visual_setup=scene.get("visual_setup",""),
                                            text_overlay=scene.get("text_overlay",""),
                                            global_plan=job["bible"])''',"avoid_whiteboard_prompt")
repl('''        shutil.copy2(raw,silent)
    merged=scene_dir/"merged.mp4"''',
'''        if Path(raw).resolve()!=silent.resolve():
            shutil.copy2(raw,silent)
    merged=scene_dir/"merged.mp4"''',"samefile_color")
file.write_text(s,encoding="utf-8")
f=root/"studio_input_modes.py"
s=f.read_text(encoding="utf-8")
needle='''        scenes.append({
          "scene_number":scene_num,"summary":summary,''';
assert needle in s
s=s.replace(needle,'''        seconds_match=re.search(r"(?i)\\b([5-9]|[1-5][0-9])-second continuous shot\\b",body)
        locked_seconds=int(seconds_match.group(1)) if seconds_match else 8
        scenes.append({
          "script_seconds":locked_seconds,
          "scene_number":scene_num,"summary":summary,''',1)
f.write_text(s,encoding="utf-8")
for x in [file,f,root/"studio_color_render.py"]:
    py_compile.compile(str(x),doraise=True)
print("COLOR_PROVIDER_DIRECT_AND_LOCKED_SCENE_TIME_PASS")
