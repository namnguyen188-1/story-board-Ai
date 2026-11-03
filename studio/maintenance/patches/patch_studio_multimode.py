"""Connect Studio genre/mode/color/voice pipeline (checkpointed).
No external API calls by this patch.
"""
from pathlib import Path
import shutil,py_compile,datetime
root=Path(r"D:\STORYBOARD_AI\studio")
target=root/"series_studio.py"
batch=root/"mcp_v2_batch.py"
tts=root/"engine"/"tools"/"tts.py"
files=[target,batch,tts]
cp=root/"checkpoints"/("multigenre_modes_"+datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
cp.mkdir(parents=True,exist_ok=True)
for i,x in enumerate(files):shutil.copy2(x,cp/(str(i)+"_"+x.name))
def transform(file, pairs):
    s=file.read_text(encoding="utf-8")
    for label,old,new in pairs:
        if old not in s:
            raise RuntimeError("Patch anchor not found: "+file.name+" / "+label)
        s=s.replace(old,new,1)
    file.write_text(s,encoding="utf-8")

transform(target,[
 ("imports",'from resilient_gemini import ResilientClient, TransientGeminiFailure',
 '''from resilient_gemini import ResilientClient, TransientGeminiFailure
from studio_modes import GENRES,STYLES,REGIONS,resolve_genre,resolve_style,voice_for,image_instruction,tts_style
from studio_input_modes import parse_locked_screenplay,analyze_reference,youtube_url'''),
 ("make_bible",'\"Design an ORIGINAL, production-ready story bible for an ongoing whiteboard animated drama \"',
 '''"Design an ORIGINAL, production-ready story bible for a "+str(series)+" film, with STYLE "+str(style)+" and GENRE "+str(genre)+". "'''),
 ("make_bible_args",'def make_bible(client, model, prompt, series):',
 'def make_bible(client, model, prompt, series,genre="documentary",style="color_cinematic"):'),
 ("fingerprint_config",'''          "model":args.model,"mode":args.mode}''',
 '''          "model":args.model,"mode":args.mode,"input_mode":args.input_mode,
          "genre":args.genre,"visual_style":args.visual_style,"region":args.region,
          "reference_url":args.reference_url if args.input_mode=="link" else ""}'''),
 ("scene_total",'''    scene_total = max(1,math.ceil(args.minutes*60/args.scene_seconds))
    bible_file = series_dir/"series_bible.json"
    if args.mode == "offline":''',
 '''    supplied_scenes = parse_locked_screenplay(prompt) if args.input_mode=="script" else None
    scene_total = len(supplied_scenes) if supplied_scenes is not None else max(1,math.ceil(args.minutes*60/args.scene_seconds))
    # Scope bibles by premise and visual identity: unrelated productions must never
    # inherit an old character or world even when the series display name is reused.
    bible_file = series_dir/"bibles"/(args.genre+"_"+args.visual_style+"_"+hash_of(prompt[:2200])[:13]+".json")
    if args.input_mode=="script":
        # Locked user screenplay: no calls to the LLM scriptwriter.
        bible={"world":"Original screenplay supplied by user; do not alter its characters or dialogue.",
               "visual_style":image_instruction(args.genre,args.visual_style),
               "characters":[{"name":"Script characters","appearance":"Keep all characters as specified in each scene"}],
               "continuity_rules":"Exact screenplay and dialogue; never replace story with previous series bible.",
               "narrator_style":tts_style(args.language,args.genre,args.region)}
        scenes=supplied_scenes
    elif args.mode == "offline":'''),
 ("make_bible_call",'''            write_json(bible_file,make_bible(client,args.model,prompt,args.series))''',
 '''            write_json(bible_file,make_bible(client,args.model,prompt,args.series,args.genre,args.visual_style))'''),
 ("request_scenes",'''                     f"whiteboard-film scenes, numbered {pos+1} through {pos+n}. Spoken narration is in "''',
 '''                     f"{args.genre} {args.visual_style} film scenes, numbered {pos+1} through {pos+n}. Spoken narration is in "'''),
 ("scene_style",'''                     "hand-drawn art: physical continuity is crucial. No placeholders, no repetitions. "''',
 '''                     f"{image_instruction(args.genre,args.visual_style)} Physical and character continuity is crucial. No placeholders, no repetitions. "'''),
 ("bible_meta",'''    if len(scenes) != scene_total:
        raise RuntimeError("Plan scene count incomplete")
    data={''',
 '''    if len(scenes) != scene_total:
        raise RuntimeError("Plan scene count incomplete")
    bible=dict(bible)
    bible["production_genre"]=args.genre
    bible["visual_style_mode"]=args.visual_style
    data={'''),
 ("audio_style",'''            generated=generate_tts_audio_tool_fn(scene["narration"],language=job["language"],voice_name=job.get("voice_name","Kore"))''',
 '''            if not scene["narration"].strip():
                from studio_color_render import create_silence
                create_silence(audio,scene.get("script_seconds",job.get("scene_seconds",8)))
                generated=str(audio)
            else:
                generated=generate_tts_audio_tool_fn(
                    scene["narration"],language=job["language"],
                    voice_name=job.get("voice_name","Kore"),
                    voice_style=tts_style(job["language"],job.get("genre","documentary"),job.get("region","auto")))'''),
 ("color_render",'''        raw=draw_animation_tool_fn(str(image),resize_wd=width,resize_ht=height,
                frame_rate=25 if job["mode"]=="live" else 15,
                split_len=16 if job["mode"]=="live" else 18,
                object_skip_rate=7 if job["mode"]=="live" else 10,
                end_duration_sec=1)''',
 '''        if job.get("visual_style","whiteboard")!="whiteboard" and job["mode"]=="live":
            from studio_color_render import color_video
            raw=color_video(image,audio,silent,width,height)
        else:
            raw=draw_animation_tool_fn(str(image),resize_wd=width,resize_ht=height,
                    frame_rate=25 if job["mode"]=="live" else 15,
                    split_len=16 if job["mode"]=="live" else 18,
                    object_skip_rate=7 if job["mode"]=="live" else 10,
                    end_duration_sec=1)'''),
 ("run_prompt_header",'''    if not args.prompt and not args.prompt_file:
        raise RuntimeError("Provide --prompt or --prompt-file")
    prompt=Path(args.prompt_file).read_text(encoding="utf-8") if args.prompt_file else args.prompt
    if not prompt.strip():
        raise RuntimeError("Episode premise cannot be empty")''',
 '''    if not args.prompt and not args.prompt_file and not (args.input_mode=="link" and args.reference_url):
        raise RuntimeError("Provide an idea, screenplay, or YouTube reference URL")
    prompt=Path(args.prompt_file).read_text(encoding="utf-8") if args.prompt_file else (args.prompt or "")
    if args.input_mode not in ("idea","link","script"):
        raise ValueError("Input mode invalid")
    args.genre=resolve_genre(args.genre)
    args.visual_style=resolve_style(args.visual_style,args.genre)
    if args.region not in REGIONS:
        raise ValueError("Unknown region")
    args.voice_name=voice_for(args.language,args.genre,args.region,args.voice_name)
    if args.input_mode!="link" and not prompt.strip():
        raise RuntimeError("Input text is empty")
    if args.input_mode=="script":
        parse_locked_screenplay(prompt) # fail before ANY AI or new media'''),
 ("reference_insert",'''    series_dir=PRODUCTIONS/slug(args.series)''',
 '''    if args.input_mode=="link":
        url=youtube_url(args.reference_url or prompt)
        if args.mode=="live":
            target_series=PRODUCTIONS/slug(args.series)
            target_ep=target_series/f"episode_{args.episode:03d}"
            data_path=target_ep/"reference_analysis.json"
            if data_path.is_file():
                details=read_json(data_path)
                if details.get("source_url")!=url:
                    raise RuntimeError("Existing reference is different; choose a new episode")
            else:
                from google import genai
                from resilient_gemini import ResilientClient
                details=analyze_reference(ResilientClient(genai.Client(api_key=own_api_key())),args.model,url)
                write_json(data_path,details)
            if args.genre=="documentary" and str(details.get("genre")) in GENRES:
                args.genre=resolve_genre("auto",details.get("genre"))
                args.visual_style=resolve_style(args.visual_style,args.genre)
            prompt=("Create an ORIGINAL story that uses high-level storytelling techniques from the public "
                   "reference; do not copy original dialogue, named characters, exact scenes or specific plot. "
                   "Own new premise: "+str(details.get("new_original_story_seed",""))[:1500]+". "
                   "Reference hook: "+str(details.get("hook_technique",""))[:600]+". "
                   "Narrative structure: "+str(details.get("narrative_structure",""))[:900]+". "
                   "Pacing: "+str(details.get("scene_pacing",""))[:500]+". "
                   "Additional user idea: "+prompt[:2000])
        else:
            prompt="Original offline sample inspired by "+url+". "+prompt
    series_dir=PRODUCTIONS/slug(args.series)'''),
 ("task_hash",'''                "mode":args.mode,"voice_name":args.voice_name,"subtitle":not args.no_subtitles,"reference":reference,''',
 '''                "mode":args.mode,"voice_name":args.voice_name,"region":args.region,
                "genre":args.genre,"visual_style":args.visual_style,
                "subtitle":not args.no_subtitles,"reference":reference,'''),
 ("job_style",'''             "voice_name":args.voice_name,"api_key":key,''',
 '''             "voice_name":args.voice_name,"genre":args.genre,
             "visual_style":args.visual_style,"region":args.region,
             "scene_seconds":args.scene_seconds,"api_key":key,'''),
 ("parser_opts",'''    r.add_argument("--language",default="English")''',
 '''    r.add_argument("--language",default="English")
    r.add_argument("--input-mode",choices=["idea","link","script"],default="idea")
    r.add_argument("--reference-url",default="")
    r.add_argument("--genre",choices=list(GENRES),default="auto")
    r.add_argument("--visual-style",choices=list(STYLES),default="auto")
    r.add_argument("--region",choices=list(REGIONS),default="auto")'''),
 ("voice_auto",'r.add_argument("--voice-name",choices=list(VOICES),default=DEFAULT_VOICE)',
 'r.add_argument("--voice-name",choices=list(VOICES)+["auto"],default=DEFAULT_VOICE)'),
])
transform(batch,[("image_prompt",'''    return ("Original cinematic WHITEBOARD INK ART, wide 16:9 landscape, "
            "white background, crisp black outlines, very restrained color, "
            "coherent storytelling composition. "''',
 '''    from studio_modes import image_instruction
    genre=bible.get("production_genre","whiteboard")
    style=bible.get("visual_style_mode","whiteboard")
    return ("Original professionally composed cinematic storyboard image, wide 16:9 landscape. "
            +image_instruction(genre,style)+" Coherent storytelling composition. "'''),
 ("locked",'''            ". No text overlays, no hands drawing pictures, no marker pens, "
            "no watermarks, no distorted people.")[:19500]''',
 '''            ". No text overlays, no watermarks, no distorted people. "
            "If photorealistic: preserve full colors, realistic faces and clothing; "
            "no drawing hand, no sketch paper.")[:19500]''')])
transform(tts,[("voice_style_arg",'language: str = "english", voice_name: str = "Kore") -> str:',
 'language: str = "english", voice_name: str = "Kore", voice_style: str = "") -> str:'),
 ("voice_style_meta",'''                    "text":text,
                    "speech_metadata":{"style":"Natural, expressive, confident and coherent storytelling in "+language}''',
 '''                    "text":text,
                    "speech_metadata":{"style":voice_style or ("Natural, expressive, confident and coherent storytelling in "+language)}''')])
for f in files+[root/"studio_modes.py",root/"studio_input_modes.py",root/"studio_color_render.py"]:
    py_compile.compile(str(f),doraise=True)
print("STUDIO_THREE_INPUT_MODES_COLOR_PATCH_PASS")
print("CODE_CHECKPOINT",cp)
