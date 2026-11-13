"""Storyboard AI Series Studio: resumable, independent multi-episode production.







Uses a separate .env and never reads secrets from YouTube SEO Pro V2.







"""







from __future__ import annotations







import argparse, concurrent.futures, hashlib, json, math, os, re, shutil







import subprocess, sys, threading, time, uuid, wave















if hasattr(sys.stdout, "reconfigure"):







    try:







        sys.stdout.reconfigure(encoding="utf-8", errors="replace")







    except Exception:







        pass







if hasattr(sys.stderr, "reconfigure"):







    try:







        sys.stderr.reconfigure(encoding="utf-8", errors="replace")







    except Exception:







        pass















from datetime import datetime







from pathlib import Path















HOME = Path(__file__).resolve().parent







if str(HOME) not in sys.path:







    sys.path.insert(0, str(HOME))















try:







    import silent_subprocess







except Exception:







    pass















from resilient_gemini import ResilientClient, TransientGeminiFailure







from studio_modes import GENRES,STYLES,REGIONS,resolve_genre,resolve_style,detect_genre,voice_for,image_instruction,tts_style







from studio_input_modes import parse_locked_screenplay,analyze_reference,youtube_url







from story_arc_quality import beat_guidance,audit_plan,BAD_OPENING







ENGINE = HOME / "engine"







PRODUCTIONS = HOME / "productions"







ENGINE_BIN = ENGINE / "bin"







if ENGINE_BIN.is_dir() and str(ENGINE_BIN) not in os.environ.get("PATH", ""):







    os.environ["PATH"] = str(ENGINE_BIN) + os.pathsep + os.environ.get("PATH", "")















def stamp():







    return datetime.now().isoformat(timespec="seconds")















def slug(s):







    return re.sub(r"[^a-zA-Z0-9_-]+", "-", s.strip()).strip("-")[:70] or "series"















def write_json(path, data):







    path = Path(path)







    path.parent.mkdir(parents=True, exist_ok=True)







    temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")







    temp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")







    for attempt in range(15):







        try:







            os.replace(temp, path)







            return







        except (PermissionError, OSError):







            time.sleep(0.04 * (attempt + 1))







    try:







        shutil.copy2(temp, path)







        try:







            temp.unlink(missing_ok=True)







        except Exception:







            pass







    except Exception:







        os.replace(temp, path)















def read_json(path):







    return json.loads(Path(path).read_text(encoding="utf-8"))















def hash_of(value):







    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()















def get_api_keys() -> list[str]:







    from resilient_gemini import get_all_api_keys







    return get_all_api_keys()















def own_api_key() -> str:







    keys = get_api_keys()







    return keys[0] if keys else ""















def ffprobe(path):







    path = Path(path)







    if not path.is_file() or path.stat().st_size < 800:







        raise RuntimeError("Missing, tiny or invalid media: " + str(path))







    proc = subprocess.run(["ffprobe","-v","error","-show_entries",







        "stream=codec_type,codec_name,width,height,duration:format=duration,size",







        "-of","json",str(path)], capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=45, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))







    if proc.returncode:







        raise RuntimeError("ffprobe failed on " + path.name + ": " + proc.stderr[-350:])







    meta = json.loads(proc.stdout)







    return meta, float(meta.get("format",{}).get("duration",0) or 0)















def qc_clip(path, need_audio=True, expected_wh=None):







    meta, duration = ffprobe(path)







    streams = meta.get("streams",[])







    video = [s for s in streams if s.get("codec_type") == "video"]







    audio = [s for s in streams if s.get("codec_type") == "audio"]







    if not video or (need_audio and not audio) or duration < 0.6:







        raise RuntimeError("QC failed: video/audio/duration for " + str(path))







    if expected_wh and (video[0].get("width"),video[0].get("height")) != tuple(expected_wh):







        raise RuntimeError("QC failed: dimensions in " + str(path))







    return {"duration_seconds":round(duration,3),"bytes":Path(path).stat().st_size,







            "video_codec":video[0].get("codec_name"),"audio_codec":audio[0].get("codec_name") if audio else None}















def doctor(args):







    print("STORYBOARD_STUDIO_DOCTOR")







    print("Folder:",HOME)







    print("Source:",ENGINE)







    print("Independent Gemini key configured:",bool(own_api_key()))







    from v2_tuanstor_image import is_ready as v2_image_ready







    print("V2 Tuan Stor image gateway available (read-only config):",v2_image_ready())







    try:







        from comfyui_image_provider import is_ready as comfy_is_ready







        print("ComfyUI Local image provider available:",comfy_is_ready())







    except Exception:







        print("ComfyUI Local image provider available:",False)







    try:







        from mcp_v2_images import preflight







        preflight()







        print("MCP V2 image bridge installed:", True)







    except Exception:







        print("MCP V2 image bridge installed:", False)







    for executable in ("ffmpeg","ffprobe"):







        print(executable, "available:",bool(shutil.which(executable)))







    for module in ("cv2","numpy","PIL","google.genai"):







        try:







            __import__(module)







            ok = "YES"







        except ImportError:







            ok = "NO"







        print(module,ok)







    print("V2 Tuansu API config is read-only; V2 source and settings remain unchanged.")















VIETNAMESE_EXCLUSIVE_CHARS = set(







    "ăằắẳẵặĂẰẮẲẴẶ"







    "âầấẩẫậÂẦẤẨẪẬ"







    "êềếểễệÊỀẾỂỄỆ"







    "ôồốổỗộÔỒỐỔỖỘ"







    "ơờớởỡợƠỜỚỞỠỢ"







    "ưừứửữựƯỪỨỬỮỰ"







    "đĐ"







    "ảãạẢÃẠ"







    "ẻẽẹẺẼẸ"







    "ỉĩịỈĨỊ"







    "ỏõọỎÕỌ"







    "ủũụỦŨỤ"







    "ỷỹỵỶỸỴ"







)







CYRILLIC_PATTERN = re.compile(r"[\u0400-\u04FF]")















def validate_scene_language(text: str, target_lang: str) -> bool:







    """Verifies that the generated narration or text adheres strictly to target_lang."""







    if not text or not isinstance(text, str):







        return False







    t_clean = text.strip()







    if not t_clean:







        return False







    t_lower = str(target_lang or "").lower().strip()







    is_vi = "viet" in t_lower or "tiếng việt" in t_lower or t_lower == "vn"















    # 1. If target IS Vietnamese, text MUST be authentic Vietnamese and NOT pure English







    if is_vi:







        has_vi_chars = any(c in VIETNAMESE_EXCLUSIVE_CHARS for c in t_clean) or any(c in "àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ" for c in t_clean.lower())







        has_common_en = bool(re.search(r"\b(the|and|this|that|with|from|which|they|have|were|been|about|would|there|when|what|their)\b", t_clean, re.I))







        if not has_vi_chars and has_common_en:







            return False















    # 2. If target is NOT Vietnamese, reject text containing Vietnamese exclusive characters or words







    if not is_vi:







        if any(c in VIETNAMESE_EXCLUSIVE_CHARS for c in t_clean):







            return False







        if re.search(r"\b(và|của|những|người|chúng ta|trong khi|nhưng mà|tại sao|không phải|với|được|cho|một|các)\b", t_clean, re.I):







            return False















    # 2. If target is Russian, text MUST be written primarily in Cyrillic







    if "russ" in t_lower or "tiếng nga" in t_lower or t_lower == "ru":







        cyrillic_chars = CYRILLIC_PATTERN.findall(t_clean)







        letters = [c for c in t_clean if c.isalpha()]







        if not letters:







            return False







        cyrillic_ratio = len(cyrillic_chars) / max(1, len(letters))







        if cyrillic_ratio < 0.6:







            return False















    # 3. If target is Asian script (Chinese, Japanese, Korean, Thai, Arabic)







    if "chin" in t_lower or "tiếng trung" in t_lower or t_lower == "zh":







        if not re.search(r"[\u4E00-\u9FFF]", t_clean): return False







    elif "jap" in t_lower or "tiếng nhật" in t_lower or t_lower == "ja":







        if not re.search(r"[\u3040-\u30FF\u4E00-\u9FFF]", t_clean): return False







    elif "kor" in t_lower or "tiếng hàn" in t_lower or t_lower == "ko":







        if not re.search(r"[\uAC00-\uD7AF]", t_clean): return False







    elif "thai" in t_lower or "tiếng thái" in t_lower or t_lower == "th":







        if not re.search(r"[\u0E00-\u0E7F]", t_clean): return False







    elif "arab" in t_lower or "ả rập" in t_lower or t_lower == "ar":







        if not re.search(r"[\u0600-\u06FF]", t_clean): return False















    return True















def force_translate_chunk_to_language(client, model: str, chunk: dict, target_lang: str) -> dict:







    """Translates any scenes that were returned in the wrong language into native target_lang."""







    scenes = chunk.get("scenes", [])







    if not scenes:







        return chunk







    print(f"[LANG_TRANSLATOR] Phát hiện phân cảnh sai ngôn ngữ mục tiêu ({target_lang})! Đang tự động dịch sang {target_lang}...", flush=True)







    payload_to_trans = []







    for sc in scenes:







        payload_to_trans.append({







            "scene_number": sc.get("scene_number"),







            "summary": sc.get("summary", ""),







            "narration": sc.get("narration", ""),







            "text_overlay": sc.get("text_overlay", "")







        })







    prompt = (







        f"You are a master cinema screenwriter and literary translator.\n"







        f"Translate the following screenplay scene elements into native, deeply evocative, natural {target_lang}.\n"







        f"CRITICAL RULES:\n"







        f"1. Translate 'narration', 'summary', and 'text_overlay' 100% into {target_lang}.\n"







        f"2. For Russian, write strictly in native Russian using the Cyrillic alphabet.\n"







        f"3. Maintain the exact same dramatic tone, pacing, pauses, and rhetorical impact.\n"







        f"4. Do NOT output any Vietnamese characters or words unless target language is Vietnamese.\n"







        f"5. Return JSON only with key 'translated_scenes' containing an array of objects with keys: scene_number, summary, narration, text_overlay.\n"







        f"Example format:\n{{\"translated_scenes\": [{{\"scene_number\": 1, \"summary\": \"...\", \"narration\": \"...\", \"text_overlay\": \"...\"}}]}}\n\n"







        f"Input scenes:\n{json.dumps(payload_to_trans, ensure_ascii=False)}"







    )







    candidate_models = []







    for m in (model, "gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.8-flash", "gemini-3.6-flash"):







        if m and m not in candidate_models:







            candidate_models.append(m)















    for t_model in candidate_models:







        try:







            res = client.models.generate_content(







                model=t_model,







                contents=prompt,







                config={"response_mime_type": "application/json", "temperature": 0.1}







            )







            res_text = res.text.strip()







            if res_text.startswith("```"):







                res_text = re.sub(r"^```(?:json)?\s*", "", res_text)







                res_text = re.sub(r"\s*```$", "", res_text)







            # Resilient fixes for malformed LLM JSON: '":,' -> '": ' and trailing commas







            res_text = re.sub(r'":\s*,\s*', '": ', res_text)







            res_text = re.sub(r',\s*([}\]])', r'\1', res_text)







            data = json.loads(res_text)







            if isinstance(data, list):







                trans_list = data







            elif isinstance(data, dict):







                trans_list = data.get("translated_scenes") or data.get("scenes") or []







            else:







                trans_list = []







            if trans_list and len(trans_list) == len(scenes):







                for orig_sc, trans_sc in zip(scenes, trans_list):







                    orig_sc["narration"] = trans_sc.get("narration", orig_sc["narration"])







                    orig_sc["summary"] = trans_sc.get("summary", orig_sc["summary"])







                    orig_sc["text_overlay"] = trans_sc.get("text_overlay", orig_sc["text_overlay"])







                print(f"[LANG_TRANSLATOR] Đã dịch thành công {len(scenes)} cảnh sang {target_lang} chuẩn xác!", flush=True)







                return chunk







        except Exception as e:







            print(f"[LANG_TRANSLATOR] Model {t_model} translation failed: {e}", flush=True)







    return chunk















def make_bible(client, model, prompt, series,genre="documentary",style="color_cinematic"):
    from studio_modes import ART
    genre_spec = ART.get(genre, "")
    genre_prompt_chunk = f"\nAUTHORITATIVE GENRE SPECIFICATION (Strictly adhere to this aesthetic, world setting, and character archetype):\n{genre_spec}\n" if genre_spec else ""
    request = (f"Design an ORIGINAL, production-ready, viral episodic series story bible for '{series}', with STYLE '{style}' and GENRE '{genre}'.\n"
         f"{genre_prompt_chunk}\n"
         "JSON only, with keys: "
         "- world: detailed setting, geography, historical/cultural context, atmospheric palette, lighting rules matching the genre specification. "
         "- visual_style: exact art direction, cinematic camera aesthetics, color temperature matching the genre. "
         "- characters: array of 1-3 recurring protagonists with: name, stable_appearance (exact age, facial structure, skin tone, eye color, hairstyle matching the genre), attire (signature iconic clothing, textures, colors), signature_props (iconic accessories/items), personality, immutable_rules (rules to prevent appearance drift across scenes and episodes). "
         "- continuity_rules: strict rules to preserve exact character visual DNA and world atmosphere across all episodes. "
         "- narrator_style: voiceover tone, cadence, rhythm tailored to the genre. "
         "- core_moral_theme: profound human life lesson, emotional awakening, or moral truth. "
         "- series_hook_framework: central overarching mystery, quest, or dramatic stakes linking episodes together. "
         f"Preserve character appearance across episodes. Series: {series}. Premise: {prompt[:5500]}")







    result = client.models.generate_content(model=model,contents=request,







              config={"response_mime_type":"application/json"})







    data = json.loads(result.text)







    if not isinstance(data,dict) or not data.get("characters"):







        raise ValueError("Empty or invalid story bible")







    return data















def produce_plan(args, series_dir, episode_dir, prompt):







    plan_file = episode_dir/"plan.json"







    config_data = {"series":args.series,"episode":args.episode,"prompt":prompt,







          "minutes":args.minutes,"scene_seconds":args.scene_seconds,"language":args.language,







          "model":args.model,"mode":args.mode,"input_mode":args.input_mode,







          "genre":args.genre,"visual_style":args.visual_style,"region":args.region,







          "reference_url":args.reference_url if args.input_mode=="link" else "",







          "link_clone_mode":getattr(args, "link_clone_mode", "exact_clone") if args.input_mode=="link" else "",







          "speech_pacing":getattr(args, "speech_pacing", "slow"),







          "image_provider":getattr(args, "image_provider", "comfyui")}







    fingerprint = hash_of(config_data)







    if plan_file.exists():







        saved = read_json(plan_file)







        if (args.mode=="live" and args.input_mode=="link" and







              getattr(args,"link_clone_mode","exact_clone")=="exact_clone"):







            from clone_integrity import require_fresh_exact_clone_plan







            source_ref = episode_dir/"reference_analysis.json"







            reference = read_json(source_ref) if source_ref.is_file() else {}

            try:

                require_fresh_exact_clone_plan(saved, reference)

            except Exception as clone_check_err:

                print(f"[CLONE_INTEGRITY] Kịch bản cũ cần làm mới: {clone_check_err}. Đang tạo mới từ link...", flush=True)

                saved = None



        if saved and (getattr(args, "resume", False) or not (episode_dir / "episode_final.mp4").is_file()):







            print(f"[RESUME] Phát hiện kịch bản tập {args.episode}. Tự động khôi phục để chạy tiếp...", flush=True)







            return saved







        if saved.get("fingerprint") != fingerprint:







            raise RuntimeError("Episode already exists with different settings. Choose a different episode number.")







        return saved







    # Lock the narrative across episodes without touching user-authored or clone scripts.

    continuity_context = ""

    if args.input_mode == "idea" and args.episode > 1:

        from episode_storyline import build_episode_context

        continuity_context = build_episode_context(series_dir, args.episode, args.genre)

        if continuity_context:

            print(f"[SERIES_CONTINUITY] Episode {args.episode} follows prior original story plan.", flush=True)

        elif args.genre == "stoic":

            raise RuntimeError("SERIES_CONTINUITY_MISSING: Cannot write an unrelated Stoic episode. "

                               "Create a new series starting with episode 1, or use Resume for an existing episode. "

                               "Prior episode must contain an original idea-mode plan in the same genre.")



    supplied_scenes = parse_locked_screenplay(prompt, scene_seconds=getattr(args, "scene_seconds", 7)) if args.input_mode=="script" else None



    # Shorts & vertical 9:16 must use fast-paced 6-8s scenes (never dragging 25s)

    is_short_pacing = (float(getattr(args, "minutes", 2.0) or 2.0) <= 1.05) or (getattr(args, "aspect_ratio", "") == "9:16") or (getattr(args, "is_short", False))

    if getattr(args, "scene_seconds", 0) <= 0:

        g_clean = str(getattr(args, "genre", "")).lower()
        if is_short_pacing:
            args.scene_seconds = 4
        elif any(g in g_clean for g in ("whiteboard", "colored_marker")):
            args.scene_seconds = 6
        elif any(g in g_clean for g in ("drama", "family_drama", "hoa_drama", "action", "narrative")):
            args.scene_seconds = 8
        elif any(g in g_clean for g in ("stoic", "philosophy")):
            args.scene_seconds = 9
        else:
            args.scene_seconds = 8



    scene_total = len(supplied_scenes) if supplied_scenes is not None else max(1,math.ceil(args.minutes*60/max(4, args.scene_seconds)))







    print(f"PLAN_START series {args.series} ep {args.episode} scenes {scene_total}", flush=True)







    # Scope bibles by premise and visual identity: unrelated productions must never







    # inherit an old character or world even when the series display name is reused.







    series_master_bible = series_dir / "series_master_bible.json"







    bible_file = series_dir/"bibles"/(args.genre+"_"+args.visual_style+"_"+hash_of(prompt[:2200])[:13]+".json")







    if series_master_bible.is_file() and not bible_file.exists() and args.episode > 1:







        try:







            shutil.copy2(series_master_bible, bible_file)







            print(f"[CONTINUITY] Đã tự động kế thừa Master Bible nhân vật & bối cảnh cho tập {args.episode} từ series '{args.series}'!", flush=True)







        except Exception:







            pass







    if args.input_mode=="script":







        # Locked user screenplay: no calls to the LLM scriptwriter.







        bible={"world":"Original screenplay supplied by user; do not alter its characters or dialogue.",







               "visual_style":image_instruction(args.genre,args.visual_style),







               "characters":[{"name":"Script characters","appearance":"Keep all characters as specified in each scene"}],







               "continuity_rules":"Exact screenplay and dialogue; never replace story with previous series bible.",







               "narrator_style":tts_style(args.language,args.genre,args.region)}







        scenes=supplied_scenes







    elif args.mode == "offline":







        if not bible_file.exists():







            write_json(bible_file,{"world":"Offline test scenes","visual_style":"Monochrome whiteboard",







                           "characters":[{"name":"Drawing","appearance":"simple black outlines"}]})







        bible = read_json(bible_file)







        scenes = [{"scene_number":i+1,"summary":f"Test beat {i+1}",







                   "narration":f"Offline test: storyboard scene {i+1}. Synthetic demonstration audio.",







                   "description":f"A clear drawing of a sun and a scene number {i+1}.",







                   "visual_setup":"Whiteboard 16:9 with thick black ink","text_overlay":""}







                  for i in range(scene_total)]







    else:







        key = own_api_key()







        if not key:







            try:







                from tuansuapi_provider import get_gateway_config







                gw = get_gateway_config()







                if gw.get("enabled") == "1" and gw.get("api_key"):







                    key = "TUANSU_GATEWAY_ACTIVE"







            except Exception:







                pass







        if not key:







            raise RuntimeError("Separate Gemini key missing. Add GEMINI_API_KEY to D:\\STORYBOARD_AI\\studio\\.env hoặc cấu hình API Bên Thứ Ba (Tuấn Stor)")







        client=ResilientClient(api_keys=get_api_keys() if key != "TUANSU_GATEWAY_ACTIVE" else [])















        # A verified source timeline prevents thumbnail-only repetition.







        reference_timeline = []







        cloned_dna = None







        ref_analysis_p = episode_dir / "reference_analysis.json"







        if ref_analysis_p.is_file():







            try:







                ref_data = read_json(ref_analysis_p)







                from clone_integrity import valid_reference







                if valid_reference(ref_data):







                    reference_timeline = ref_data.get("timeline", [])







                if ref_data.get("character"):







                    cloned_dna = ref_data["character"]







                    cloned_dna["anchor_image"] = ref_data.get("anchor_image", "")







            except Exception:







                pass







        ref_detected_lang = ref_data.get("language", "") if "ref_data" in locals() and isinstance(ref_data, dict) else ""







        if not cloned_dna and (args.input_mode == "link" or getattr(args, "reference_url", "")):







            try:







                from competitor_cloner import analyze_competitor_character







                ref_data = analyze_competitor_character(getattr(args, "reference_url", "") or prompt)







                ref_detected_lang = ref_data.get("language", "")







                from clone_integrity import valid_reference







                if valid_reference(ref_data):







                    reference_timeline = ref_data.get("timeline", [])







                if ref_data.get("character"):







                    cloned_dna = ref_data["character"]







                    cloned_dna["anchor_image"] = ref_data.get("anchor_image", "")







            except Exception:







                pass















        if (args.input_mode=="link" and







                getattr(args,"link_clone_mode","exact_clone")=="exact_clone" and







                not reference_timeline):







            raise RuntimeError("CLONE_REFERENCE_TIMELINE_UNVERIFIED: "







                "Khong co timeline duoc xac minh tu dau den cuoi video. "







                "Khong tao canh hay tieu credit Google Flow.")















        if not bible_file.exists():







            if cloned_dna:







                print("PLAN_BIBLE_START Đang khóa DNA nhân vật clone từ video tham chiếu...", flush=True)







                char_name = cloned_dna.get("character_name", "Protagonist")







                char_app = cloned_dna.get("appearance_lock", "")







                char_att = cloned_dna.get("wardrobe_lock", "")







                if args.visual_style == "hand_color":







                    art_style = "Vibrant hand-drawn colored sketch and marker watercolor illustration on clean paper with expressive colorful artistic rendering."







                elif args.visual_style == "colored_marker":







                    art_style = "Vibrant colored whiteboard marker illustration in the signature style of After Skool, hand-drawn with multicolored chisel-tip marker pens on clean white whiteboard."







                elif args.visual_style == "whiteboard":







                    art_style = "Crisp black marker line art drawing on clean white whiteboard."







                elif args.visual_style == "color_animation":







                    art_style = "Vibrant stylized 3D/2D animation movie aesthetic with rich colors."







                elif args.visual_style == "color_cinematic":







                    art_style = cloned_dna.get("art_style") or "Photorealistic cinematic 16:9 widescreen film."







                else:







                    art_style = cloned_dna.get("art_style", "Cinematic visual storytelling")







                rules = cloned_dna.get("immutable_rules", "Preserve identical facial features and clothing across all scenes")







                premise = cloned_dna.get("story_premise", prompt)







                effective_genre = args.genre if (args.genre and args.genre != "auto") else cloned_dna.get("suggested_genre", "documentary")







                bible = {







                    "world": f"Story world based on cloned reference '{char_name}': {premise[:500]}",







                    "visual_style": art_style,







                    "production_genre": effective_genre,







                    "visual_style_mode": args.visual_style,







                    "characters": [







                        {







                            "name": char_name,







                            "appearance": char_app,







                            "attire": char_att,







                            "personality": f"Cloned protagonist: {char_name}",







                            "immutable_rules": rules,







                            "clone_prompt": cloned_dna.get("clone_prompt", "")







                        }







                    ],







                    "continuity_rules": f"CHARACTER CONTINUITY: Primary subject is '{char_name}'. Appearance: '{char_app}'. Attire: '{char_att}'. Rules: {rules}. Allow natural cinematic diversity: wide panoramic views, environment and landscape establishing shots, objects, and close-ups. Do not force an identical bust portrait into every scene.",







                    "narrator_style": tts_style(args.language, effective_genre, args.region),







                    "anchor_image": cloned_dna.get("anchor_image", "")







                }







                write_json(bible_file, bible)







                print("PLAN_BIBLE_DONE Thế giới và nhân vật đã sẵn sàng (Đã khóa nhân vật).", flush=True)







            else:







                print("PLAN_BIBLE_START Đang xây dựng thế giới & nhân vật...", flush=True)







                new_bible = make_bible(client, args.model, prompt, args.series, args.genre, args.visual_style)







                write_json(bible_file, new_bible)







                if not series_master_bible.exists() or args.episode == 1:







                    write_json(series_master_bible, new_bible)







                print("PLAN_BIBLE_DONE Thế giới và nhân vật đã sẵn sàng.", flush=True)







        bible=read_json(bible_file)







        if cloned_dna and (not bible.get("characters") or not bible["characters"][0].get("clone_prompt")):







            bible["characters"] = [







                {







                    "name": cloned_dna.get("character_name", "Protagonist"),







                    "appearance": cloned_dna.get("appearance_lock", ""),







                    "attire": cloned_dna.get("wardrobe_lock", ""),







                    "personality": f"Cloned protagonist: {cloned_dna.get('character_name', '')}",







                    "immutable_rules": cloned_dna.get("immutable_rules", ""),







                    "clone_prompt": cloned_dna.get("clone_prompt", "")







                }







            ]







            bible["anchor_image"] = cloned_dna.get("anchor_image", "")







            write_json(bible_file, bible)















        # Exact 100% transcript cloning from competitor video







        exact_cloned_scenes = None







        if args.input_mode == "link" and getattr(args, "link_clone_mode", "exact_clone") == "exact_clone":







            try:







                from transcript_cloner import get_cloned_screenplay







                ref_url = getattr(args, "reference_url", "") or prompt







                print(f"[TRANSCRIPT_CLONER] Đang bóc băng & chuyển ngữ 100% kịch bản từ video gốc ({ref_url[:80]})...", flush=True)







                active_genre = bible.get("production_genre") or (args.genre if args.genre != "auto" else "documentary")







                cloned_pack = get_cloned_screenplay(







                    ref_url,







                    target_language=args.language,







                    target_minutes=args.minutes,







                    scene_seconds=args.scene_seconds,







                    character_info=cloned_dna or (bible.get("characters", [{}])[0] if bible.get("characters") else None),







                    genre=active_genre,







                    preferred_lang=ref_detected_lang or getattr(args, "language", ""),







                )







                if cloned_pack.get("ok") and cloned_pack.get("scenes"):







                    exact_cloned_scenes = cloned_pack["scenes"]







                    from clone_integrity import validate_timed_scenes







                    cap_info=cloned_pack.get("source_caption_lines") or []







                    source_duration=float(cloned_pack.get("source_duration_seconds") or 0)







                    validate_timed_scenes(exact_cloned_scenes,cap_info,source_duration)







                    if any(not sc.get("source_visual_evidence") or







                           not sc.get("visual_semantic_verified")







                           for sc in exact_cloned_scenes):







                        raise RuntimeError("CLONE_VISUAL_SEMANTICS_NOT_VERIFIED")







                    print(f"[TRANSCRIPT_CLONER] Đã căn thời gian {len(exact_cloned_scenes)} cảnh với chứng cứ nguồn.", flush=True)







            except Exception as tr_err:







                code=str(tr_err).split(":",1)[0].strip()







                if not code.startswith(("CLONE_","SCENE_","SOURCE_")):







                    code=type(tr_err).__name__







                code=code[:110]







                print(f"[CLONE_FAILOVER] Bóc phụ đề 100% ({code}). Tự động kích hoạt chế độ chuyển thể sáng tạo theo dàn ý video để hoàn thành sản xuất...", flush=True)







                exact_cloned_scenes = None







        if exact_cloned_scenes:







            scenes = exact_cloned_scenes







            scene_total = len(scenes)







            print(f"TOTAL_SCENES {scene_total}", flush=True)







            print(f"PLAN_START series {args.series} ep {args.episode} scenes {scene_total}", flush=True)







        else:







            scenes=[]







            part_dir=episode_dir/"plan_parts"







            part_dir.mkdir(parents=True,exist_ok=True)







            per_batch=8







            for pos in range(0,scene_total,per_batch):







                n=min(per_batch,scene_total-pos)







                batch_num = pos//per_batch+1







                total_batches = (scene_total+per_batch-1)//per_batch







                print(f"PLAN_BATCH_START {batch_num}/{total_batches} scenes {pos+1}-{pos+n}", flush=True)







                file=part_dir/f"part_{pos//per_batch+1:03d}.json"







                if file.exists():
                    chunk=read_json(file)
                    if isinstance(chunk, dict) and "scenes" in chunk and len(chunk["scenes"]) > n:
                        chunk["scenes"] = chunk["scenes"][:n]







                else:







                    prior = " | ".join(s["summary"] for s in scenes[-4:])







                    char_focus = ""







                    if bible.get("characters") and isinstance(bible["characters"], list) and bible["characters"]:







                        c0 = bible["characters"][0]







                        if isinstance(c0, dict) and c0.get("name"):







                            def _safe_str(v, limit):







                                if isinstance(v, dict):







                                    s = ", ".join(f"{k}: {sub_v}" for k, sub_v in v.items())







                                elif isinstance(v, list):







                                    s = ", ".join(str(item) for item in v)







                                else:







                                    s = str(v or "")







                                return s[:limit]







                            char_focus = (f" CHARACTER CONTINUITY REFERENCE (only when this character is actually visible): '{c0['name']}'. "







                                          f"Appearance: {_safe_str(c0.get('appearance'), 250)}. "







                                          f"Attire: {_safe_str(c0.get('attire'), 150)}. "







                                          "Keep the character consistent only WHEN they appear. "







                                          "Do not force a half-body portrait into every shot. "







                                          "Allow observed wide/full-body views, landscape, objects and camera movement.")







                    timeline_focus = ""







                    if reference_timeline:







                        times = [float(b.get("timestamp_seconds",0)) for b in reference_timeline]







                        target = (pos+n/2)/max(1,scene_total)*max(1,times[-1])







                        near = min(range(len(times)),key=lambda j:abs(times[j]-target))







                        beats = reference_timeline[max(0,near-1):min(len(times),near+2)]







                        timeline_focus = (" Observed source shot rhythm, use for ORIGINAL cinematography: "







                                          +json.dumps(beats,ensure_ascii=False)[:1700]







                                          +" Do not reproduce source frames or dialogue.")







                    speech_pace = getattr(args, "speech_pacing", "slow")







                    wps = 1.9 if speech_pace == "slow" or args.genre in ("stoic", "documentary", "history") else (2.4 if speech_pace == "fast" else 2.1)

                    if args.input_mode == "idea" and (speech_pace == "slow" or args.genre in ("stoic", "documentary", "history")):

                        wps = 1.45







                    target_words = int(args.scene_seconds * wps)







                    max_words = int(target_words * 1.15)







                    target_lang_name = str(args.language or "Vietnamese").strip()







                    target_lang_upper = target_lang_name.upper()







                    







                    if "russ" in target_lang_name.lower() or "nga" in target_lang_name.lower():







                        hook_examples = "'ТАЙНА 70 ЛЕТ', 'НЕОЖИДАННЫЙ ПОВОРОТ', 'НИКОГДА НЕ ЗАБЫВАЙ'"







                    elif "span" in target_lang_name.lower() or "tây ban nha" in target_lang_name.lower():







                        hook_examples = "'SECRETO DE 70 AÑOS', 'VERDAD INESPERADA', 'NUNCA OLVIDES'"







                    elif "viet" in target_lang_name.lower() or "việt" in target_lang_name.lower():







                        hook_examples = "'BÍ MẬT 70 NĂM', 'SỰ THẬT BẤT NGỜ', 'ĐỪNG BAO GIỜ QUÊN'"







                    else:







                        hook_examples = "'70-YEAR SECRET', 'THE SHOCKING TRUTH', 'NEVER FORGET'"















                    lang_mandate = (







                        f"\n======================================================================\n"







                        f"CRITICAL TARGET LANGUAGE MANDATE:\n"







                        f"ALL SPOKEN NARRATION ('narration'), SCENE SUMMARIES ('summary'),\n"







                        f"AND HOOK OVERLAYS ('text_overlay') MUST BE WRITTEN 100% IN {target_lang_upper}!\n"







                        f"- Target Language: {target_lang_name} (Dialect/Region: {args.region})\n"







                        f"- Even if the Episode premise, Series Bible, or prompt instructions below are written in Vietnamese or English,\n"







                        f"  you MUST translate and write all spoken narration and dialogue strictly in {target_lang_name}.\n"







                        f"- ABSOLUTE PROHIBITION: DO NOT output Vietnamese words or characters (no à, á, ả, ã, ạ, ă, â, đ, ê, ô, ơ, ư...) unless target language is specifically Vietnamese!\n"







                        f"- If target language is Russian, write strictly in native Cyrillic Russian.\n"







                        f"- 'description' and 'visual_setup' MUST be written in English for the AI image generator.\n"







                        f"======================================================================\n"







                    )















                    stoic_hero_desc = (
                        "- When portraying Stoic philosophical scenes or classical heroes (Marcus Aurelius archetype): The protagonist is a DIGNIFIED LIVING HISTORICAL ROMAN PHILOSOPHER EMPEROR, a mature living human (around 50 years old) with weathered Mediterranean bronze skin, expressive dark eyes full of calm wisdom, curly salt-and-pepper beard, wearing a royal crimson and cream-white draped linen toga. NEVER depict stone statues, marble busts, pedestals, or cold sculptures; NEVER produce severed limbs, headless bodies, or amputated hands. The protagonist has 100% complete living human anatomy with fully intact arms and natural hands with five fingers. Alternate between dramatic contemplative medium portraits of the emperor in imperial courtyards, sunlit colonnades, candlelit libraries with parchment scrolls, and panoramic Roman vistas.\n"
                        if (args.genre == "stoic" or str(getattr(args, "series", "")).lower().startswith("stoi"))
                        else ""
                    )

                    request=(f"You are a master viral cinema and documentary screenwriter. Write EXACTLY {n} consecutive "







                         f"{args.genre} {args.visual_style} film scenes, numbered {pos+1} through {pos+n}. Spoken narration MUST be in "







                         f"{args.language}. Each scene targets {args.scene_seconds} seconds of speech.\n"







                         f"{lang_mandate}\n"







                         f"MANDATORY PACING & WORD COUNT: Each scene's spoken narration MUST contain approximately {target_words} words (maximum {max_words} words). "







                         "Write deep, calm, evocative narration with an unhurried, contemplative rhythm (~115-120 words/minute) and natural pauses (using commas, dashes —, and periods) between thoughts. Do NOT rush or cram too many words! JSON only, with key 'scenes', "







                         f"array of objects with scene_number, summary (in {args.language}), narration (in {args.language}), description (in English for AI image generator), visual_setup (in English), text_overlay (short 3-5 word hook in {args.language}).\n\n"







                         "MANDATORY VIRAL RETENTION & CONTINUITY STORYTELLING RULES:\n"







                         f"1. SCENE 1 (SENSATIONAL MILLION-VIEW COLD OPEN HOOK - 100% IN MEDIAS RES & DIRECT CHARACTER DIALOGUE): If this batch starts at Scene 1, Scene 1 MUST be the most heart-pounding, visually shocking, and emotionally intense scene of the entire episode! "



                         "STRICTLY FORBIDDEN: Passive/calm actions (kneeling quietly, wiping snow, strolling, gazing at scenery, reading books, philosophical pondering) and expository backstory narration. "



                         "MANDATORY CLIMAX FLASHFORWARD & PEAK CONFLICT: Plunge the viewer straight into a life-or-death climax (armed pursuit, weapon drawn, fresh blood dripping, trapped at a cliff edge, torchlights closing in, confrontation against corrupt authority, an imminent execution or explosive revelation). "



                         "MANDATORY DIRECT CHARACTER DIALOGUE: Spoken line ('narration') MUST be 100% DIRECT IN-SCENE SPOKEN DIALOGUE by the protagonist, shouted, gasping, or whispered in sheer terror/fury. NEVER use greetings ('Xin chào', 'Hello', 'Hola') or calm narrative exposition! "



                         f"The 'text_overlay' for Scene 1 must be a shocking 3-4 word curiosity trigger in ALL CAPS (e.g. {hook_examples}).\n"







                         "2. MIDDLE SCENES (HIGH-STAKES ESCALATION, SENSORY DETAILS & RELENTLESS PACING):\n"
                         "   - THE TICKING CLOCK: Establish an urgent countdown or narrowing window of survival/remedy (before nightfall, before the blizzard strikes, before the deadline). Characters feel time running out in every scene.\n"
                         "   - SHOW, DON'T TELL (SENSORY GROUNDING): Forbid abstract emotional labels ('he was scared', 'she felt sad'). Ground all emotion in physical actions, somatic reactions, and sensory reality (trembling fingers struggling with coat buttons, smelling cold air, protective body posture, a blackened injury, labored breathing). Show the physical and emotional cost of every action.\n"
                         "   - IMPOSSIBLE MORAL DILEMMAS: Force characters into agonizing choices with severe consequences (sacrifice self vs save children; preserve pride vs beg for life; choose between duty and survival).\n"
                         "   - PUNCHY STACCATO DIALOGUE: Spoken lines must be concise, authentic, and fraught with subtext ('Not without you', 'Take the boys and go'). Avoid long, polite, artificial monologues.\n"
                         "   - ESCALATING OBSTACLES: Every 45 seconds, reveal a new complication that makes the situation worse (wagon axle splits, horses sold, temperature plunges). Never let tension plateau.\n"







                         "3. FINAL SCENE (VIRAL CLIFFHANGER & ZEIGARNIK OPEN LOOP): If this batch includes the final scene, do NOT wrap up the entire narrative with a predictable, closed conclusion! Deliver an emotional/dramatic climax, but right in the final moments, abruptly unveil a SUDDEN UNRESOLVED MYSTERY, a shocking discovery, or an unanswered twist (Zeigarnik Effect). End on a suspenseful cliffhanger hook or provocative question that makes it physically impossible for the viewer to leave and FORCES them to watch the next episode!\n"







                         "4. CHARACTER & WORLD CONTINUITY: Strictly adhere to the character DNA, signature attire, distinctive facial features, accessories, and atmospheric world defined in the Series Bible. Characters and visual settings must remain 100% consistent across every scene.\n"







                         "5. CINEMATIC REAL ACTING & NATURAL DYNAMICS (REAL ACTING PRINCIPLES):\n"







                         "- Characters must possess motivated physical presence: describe eyelines, posture, breathing, hand contact with props/surfaces, and natural micro-expressions. Strictly avoid frozen mannequin stares or stiff idle bodies.\n"







                         "- Natural physical causality: Trigger -> attention (eyes move) -> head turns -> body adjusts posture -> motivated action or response.\n"







                         f"{stoic_hero_desc}" 







                         "- Continuous blocking: The visual setup and character placement at the end of each scene must transition plausibly into the next scene without jarring position snaps.\n\n"







                         f"STORY ARC BY POSITION: {beat_guidance(pos+1,n,scene_total,args.genre,prompt[:1200])}\n"







                         f"Set visuals as detailed {image_instruction(args.genre,args.visual_style)}. Physical and character continuity is crucial. No placeholders, no repetitions. "







                         f"{char_focus} {timeline_focus} "







                         f"Series bible: {json.dumps(bible,ensure_ascii=False)[:9000]}. "







                         f"Episode premise: {prompt[:5000]}. "

                         f"{continuity_context} "







                         f"Previous beats: {prior[:2000]}. "







                         f"This batch is part of a {args.minutes}-minute episode.")

                    # Keep the writing skill aligned with the actual output dimensions,
                    # including direct CLI calls that specify size without aspect-ratio.
                    size_parts = str(getattr(args, "size", "") or "").lower().split("x")
                    portrait_size = (len(size_parts) == 2 and all(part.isdigit() for part in size_parts)
                                     and int(size_parts[1]) > int(size_parts[0]))
                    is_short_mode = (getattr(args, "aspect_ratio", "") == "9:16") or portrait_size or str(args.genre).endswith("_shorts") or bool(getattr(args, "is_short", False))
                    is_drama_mode = (getattr(args, "production_mode", "") == "cinematic_drama") or (args.genre in ("drama", "family_drama", "theatrical_drama", "mafia_thriller", "romance_melodrama", "psychological_horror", "western", "action"))

                    if is_short_mode:
                        # Shorts branch: write-viral-shorts-prompts blueprint (9:16 vertical retention hook)
                        request = re.sub(
                            r"1\. SCENE 1 .*?(?=2\. MIDDLE SCENES)",
                            "1. ACT 1: VIRAL SHORTS SUPER HOOK (0.0s – 3.5s): Arrest viewer attention in first 1.5 seconds. "
                            "Visual Hook: an extraordinary expression or in medias res moment. Audio Hook: a shocking curiosity-gap statement. "
                            "Text overlay: punchy 2-3 word curiosity trigger in ALL CAPS.\n",
                            request, flags=re.S)
                        request = re.sub(
                            r"3\. FINAL SCENE .*?(?=4\. CHARACTER & WORLD CONTINUITY)",
                            "3. ACT 3: VIRAL CLIMAX & INFINITE SEAMLESS LOOP (45.0s – 58.0s): Deliver a punchy climax resolution, and craft the final spoken sentence "
                            "to grammatically and conceptually flow seamlessly back into the very first sentence of Scene 1 for infinite autoplay loop.\n",
                            request, flags=re.S)
                        request += ("\nSHORTS OVERRIDE: Pacing is 2.0s - 3.5s per scene. Keep spoken narration concise (~2.5 words/sec), "
                                    "visual prompts focused on central 9:16 safe-zone framing. Total duration must remain under 58 seconds.")
                    elif args.genre == "stoic":
                        # Stoic benchmark branch: Keep 100% UNTOUCHED for proven stability
                        request = re.sub(
                            r"1\. SCENE 1 .*?(?=2\. MIDDLE SCENES)",
                            "1. STOIC COLD OPEN: Begin with an urgent, relatable inner dilemma "
                            "or a counterintuitive philosophical question. Use reflective, "
                            "credible narration, never violent spectacle or invented danger.\n",
                            request, flags=re.S)
                        request = re.sub(
                            r"3\. FINAL SCENE .*?(?=4\. CHARACTER & WORLD CONTINUITY)",
                            "3. STOIC FINAL SCENE: Deliver a useful insight or concrete "
                            "practice and invite the next chapter with a genuine unanswered "
                            "question rooted in the existing series premise; no fabricated mystery.\n",
                            request, flags=re.S)
                        request += ("\nSTOIC OVERRIDE: Prioritize philosophical clarity, source "
                                    "accuracy, calm pacing, and the saved series storyline over "
                                    "generic viral shock instructions or artificial cliffhangers.")
                    elif args.genre == "family_drama":
                        # Family drama: authentic domestic conflict, never weapons or blood
                        request = re.sub(
                            r"1\. SCENE 1 .*?(?=2\. MIDDLE SCENES)",
                            "1. FAMILY DRAMA COLD OPEN (INTENSE DOMESTIC CROSSROADS & RAW EMOTION): "
                            "Plunge straight into a realistic, high-stakes family crossroads (e.g. an unexpected confrontation over a hidden will, "
                            "a painful secret discovered, a broken family dinner, or confronting a heartbreaking betrayal between loved ones). "
                            "STRICTLY FORBIDDEN: Armed combat, weapons, blood, gore, crime syndicates, or action stunts. "
                            "Spoken line ('narration') MUST be 100% realistic spoken dialogue between family members with authentic emotional depth.\n",
                            request, flags=re.S)
                        request = re.sub(
                            r"3\. FINAL SCENE .*?(?=4\. CHARACTER & WORLD CONTINUITY)",
                            "3. FAMILY DRAMA FINAL SCENE (EMOTIONAL ZEIGARNIK CLIFFHANGER): "
                            "Deliver an emotional turning point or shocking domestic revelation (e.g. an unopened letter from the past, "
                            "a sudden knock on the door with unexpected news, an ultimatum given). "
                            "Leave viewers deeply invested in the family's fate for the next episode.\n",
                            request, flags=re.S)
                        request += ("\nFAMILY DRAMA OVERRIDE: Authentic human/family dynamics matching the story world. "
                                    "Real human relationships, generational conflict, tears, emotional warmth and high-stakes drama. Zero gratuitous armed violence.")
                    elif args.genre == "mafia_thriller":
                        # Mafia / Detective / Noir thriller: gritty investigation, intellectual duel, high-stakes standoff
                        request = re.sub(
                            r"1\. SCENE 1 .*?(?=2\. MIDDLE SCENES)",
                            "1. MAFIA THRILLER COLD OPEN (HIGH-STAKES INTELLECTUAL CONFRONTATION OR CRIME ENIGMA): "
                            "Open in medias res with a tense standoff, an illicit late-night negotiation, discovering a critical piece of incriminating evidence, "
                            "or a narrow escape from shadowy pursuers in rain-slicked neon alleys. "
                            "Spoken line ('narration') MUST be sharp, razor-tense character dialogue or gritty internal detective monologue.\n",
                            request, flags=re.S)
                        request = re.sub(
                            r"3\. FINAL SCENE .*?(?=4\. CHARACTER & WORLD CONTINUITY)",
                            "3. MAFIA THRILLER FINAL SCENE (DEVASTATING BETRAYAL & CLIFFHANGER TWIST): "
                            "Deliver an explosive realization: an undercover identity blown, a trusted ally turning out to be the informant, or walking into a masterfully orchestrated trap. "
                            "Leave viewers desperate for the retribution in the next episode.\n",
                            request, flags=re.S)
                        request += ("\nMAFIA THRILLER OVERRIDE: Neo-noir gritty cinematic atmosphere. High-contrast chiaroscuro shadows, "
                                    "rain-slicked urban textures, tailored suits, smoky rooms, tense psychological chess. Authentic adult crime drama.")
                    elif args.genre == "action":
                        # Action / Adventure: dynamic kinetic energy, narrow escapes, adrenaline pacing
                        request = re.sub(
                            r"1\. SCENE 1 .*?(?=2\. MIDDLE SCENES)",
                            "1. ACTION COLD OPEN (HEART-POUNDING KINETIC ESCAPE & HIGH STAKES): "
                            "Plunge straight into a high-octane pursuit, a desperate tactical breach, or a breathless physical confrontation against overwhelming odds. "
                            "Spoken line ('narration') MUST be urgent, visceral, in-the-moment spoken command or gasping realization.\n",
                            request, flags=re.S)
                        request = re.sub(
                            r"3\. FINAL SCENE .*?(?=4\. CHARACTER & WORLD CONTINUITY)",
                            "3. ACTION FINAL SCENE (MOMENTUM CLIFFHANGER): "
                            "End at the brink of an even greater catastrophe or impossible showdown (e.g. cornered against a collapsing bridge, timer ticking down, enemy reinforcements arriving). "
                            "Leave viewers gasping for the next chapter.\n",
                            request, flags=re.S)
                        request += ("\nACTION OVERRIDE: Fast kinetic momentum, dynamic camera movements, physical environment interactions, relentless pacing.")
                    elif args.genre == "western":
                        # Western / Frontier: sun-scorched tension, moral dilemma, frontier standoff
                        request = re.sub(
                            r"1\. SCENE 1 .*?(?=2\. MIDDLE SCENES)",
                            "1. WESTERN COLD OPEN (DUST-CHOKED STANDOFF & MORAL CROSSROADS): "
                            "Open with a high-noon frontier showdown, entering a hostile saloon, or a wounded lone rider discovering an abandoned outpost under a blazing sun. "
                            "Spoken line ('narration') MUST be laconic, steely frontier dialogue or weathered traveler monologue.\n",
                            request, flags=re.S)
                        request = re.sub(
                            r"3\. FINAL SCENE .*?(?=4\. CHARACTER & WORLD CONTINUITY)",
                            "3. WESTERN FINAL SCENE (FRONTIER RECKONING): "
                            "End on an ominous distant dust cloud signaling approaching outlaws, a drawn gun at twilight, or a hard-bitten choice between gold and honor.\n",
                            request, flags=re.S)
                        request += ("\nWESTERN OVERRIDE: Gritty 1880s American frontier. Wide vistas, leather, spurs, dust devils, golden hour sun, weathered wooden structures.")
                    elif args.genre == "romance_melodrama":
                        # Romance: emotional heartache and longing, zero armed violence
                        request = re.sub(
                            r"1\. SCENE 1 .*?(?=2\. MIDDLE SCENES)",
                            "1. ROMANCE COLD OPEN (HEARTBREAKING CROSSROADS & EMOTIONAL RUPTURE): "
                            "Open with an intensely romantic or devastating in medias res moment (e.g. an unexpected reunion after years apart, "
                            "a tearful confrontation in the rain, a painful broken promise, or discovering a hidden sacrifice). "
                            "STRICTLY FORBIDDEN: Armed violence, weapons, gore, crime, or action violence. "
                            "Spoken line ('narration') MUST be deeply emotional character dialogue filled with longing, hurt, or passionate love.\n",
                            request, flags=re.S)
                        request = re.sub(
                            r"3\. FINAL SCENE .*?(?=4\. CHARACTER & WORLD CONTINUITY)",
                            "3. ROMANCE FINAL SCENE (ROMANTIC CLIFFHANGER): "
                            "End on a poignant unresolved choice or breathtaking romantic revelation (e.g. a confession interrupted at the last second, "
                            "a departure train pulling away, an unexpected sacrifice revealed). Leave viewers desperate for reconciliation.\n",
                            request, flags=re.S)
                        request += ("\nROMANCE OVERRIDE: Modern aesthetic romance. Golden hour warmth, expressive character glances, "
                                    "intimate emotional tension, beautiful cinematography. Zero physical combat.")
                    elif args.genre in ("whiteboard", "colored_marker"):
                        # Whiteboard: After Skool intellectual hook and visual metaphors
                        request = re.sub(
                            r"1\. SCENE 1 .*?(?=2\. MIDDLE SCENES)",
                            "1. WHITEBOARD INTELLECTUAL HOOK (AFTER SKOOL PARADOX & CURIOSITY GAP): "
                            "Open with a startling psychological paradox, counterintuitive life rule, or shocking human behavior truth. "
                            "Single engaging, witty Voiceover Narrator (NO character acting, NO life-or-death screams). "
                            "Visuals describe ingenious hand-drawn marker illustrations with visual metaphors sketching onto a clean white whiteboard.\n",
                            request, flags=re.S)
                        request = re.sub(
                            r"3\. FINAL SCENE .*?(?=4\. CHARACTER & WORLD CONTINUITY)",
                            "3. WHITEBOARD FINAL SCENE (MIND-EXPANDING PAYOFF): "
                            "Deliver a profound mental model shift or actionable life lesson, completing the whiteboard conceptual drawing. "
                            "End with an intriguing open question that changes how the viewer sees reality.\n",
                            request, flags=re.S)
                        request += ("\nWHITEBOARD OVERRIDE: After Skool style whiteboard marker art. Images MUST be colorful marker drawings on pure white background. "
                                    "No live-action actors, no real human skin, no photorealism, no violence.")
                    elif args.genre == "animation":
                        # Animation: Charming adventure or heartfelt cartoon
                        request = re.sub(
                            r"1\. SCENE 1 .*?(?=2\. MIDDLE SCENES)",
                            "1. ANIMATION COLD OPEN (VIBRANT INCITING INCIDENT & CHARMING HOOK): "
                            "Plunge into a vibrant, whimsical, or thrilling animated inciting incident. "
                            "Expressive 3D stylized cartoon characters, family-friendly humor or charming adventure stakes. "
                            "STRICTLY FORBIDDEN: Gory blood, severed limbs, dark adult violence, or realistic photographic skin.\n",
                            request, flags=re.S)
                        request = re.sub(
                            r"3\. FINAL SCENE .*?(?=4\. CHARACTER & WORLD CONTINUITY)",
                            "3. ANIMATION FINAL SCENE (AWE-INSPIRING ADVENTURE CLIFFHANGER): "
                            "Deliver a heartwarming resolution to this chapter while unveiling an exciting new magical horizon or mysterious creature for the next episode.\n",
                            request, flags=re.S)
                        request += ("\nANIMATION OVERRIDE: 3D Pixar/Disney style animated aesthetic. Vibrant colors, expressive cartoon acting, "
                                    "family-friendly themes. Zero dark gore or adult horror.")
                    elif args.genre == "psychological_horror":
                        # Psychological horror: creeping dread and paranoia, avoid generic gunfights
                        request = re.sub(
                            r"1\. SCENE 1 .*?(?=2\. MIDDLE SCENES)",
                            "1. PSYCHOLOGICAL HORROR COLD OPEN (ATMOSPHERIC DREAD & UNSETTLING ANOMALY): "
                            "Open with an eerie, skin-crawling anomaly (e.g. an unsettling shadow that moves on its own, a phone ringing from an empty house, "
                            "a whisper in the dark, or a creeping sense of paranoia). Focus on atmospheric dread and chilling suspense, not generic gunfights.\n",
                            request, flags=re.S)
                        request = re.sub(
                            r"3\. FINAL SCENE .*?(?=4\. CHARACTER & WORLD CONTINUITY)",
                            "3. HORROR FINAL SCENE (CHILLING ZEIGARNIK OPEN LOOP): "
                            "End on a hair-raising revelation or unsettling twist that leaves the viewer questioning what was real, desperate to see what lurks next.\n",
                            request, flags=re.S)
                    elif args.genre == "history":
                        # History: authentic period accuracy, monumental turning point
                        request = re.sub(
                            r"1\. SCENE 1 .*?(?=2\. MIDDLE SCENES)",
                            "1. HISTORICAL EPIC COLD OPEN (CRITICAL HISTORICAL PIVOT & MAJESTIC SCALE): "
                            "Open at the fateful eve of a monumental historical turning point (e.g. an empire on the brink of collapse, signing a secret decree, an army gathering on the misty plains). "
                            "Spoken line ('narration') MUST be authoritative, deeply immersive period narration or authentic historical speech.\n",
                            request, flags=re.S)
                        request = re.sub(
                            r"3\. FINAL SCENE .*?(?=4\. CHARACTER & WORLD CONTINUITY)",
                            "3. HISTORICAL FINAL SCENE (EPOCHAL LEGACY & UNANSWERED MYSTERY): "
                            "Conclude with the profound impact of this event echoing across centuries, leaving an unsolved riddle or inspiring question for the next chapter.\n",
                            request, flags=re.S)
                        request += ("\nHISTORY OVERRIDE: Strict period accuracy, authentic architecture, ceremonial attire, dignified pacing, majestic cinematic visuals. Single authoritative Voiceover Narrator.")
                    elif not is_drama_mode:
                        # Narrative Storytelling / Documentary / History branch: write-narrative-scene-prompts blueprint
                        request = re.sub(
                            r"1\. SCENE 1 .*?(?=2\. MIDDLE SCENES)",
                            "1. NARRATIVE COLD OPEN (COMPELLING HOOK & EXPEDITION/HISTORICAL PREMISE): Open with an intriguing question, "
                            "a forgotten historical fact, or a breathtaking panoramic visual setup. Spoken line is 1 single authoritative, "
                            "immersive Voiceover Narrator (no theatrical shouting or life-or-death character panic).\n",
                            request, flags=re.S)
                        request = re.sub(
                            r"3\. FINAL SCENE .*?(?=4\. CHARACTER & WORLD CONTINUITY)",
                            "3. NARRATIVE FINAL SCENE: Deliver an inspiring, thought-provoking reflection or historical conclusion "
                            "that leaves a lasting impression on the viewer.\n",
                            request, flags=re.S)
                        request += ("\nNARRATIVE OVERRIDE: Single voiceover narrator. Image prompts must describe pure visuals only (40-80 English words) "
                                    "with dynamic cinematic camera (wide establishing shots, medium details, aerial views). Absolutely NO 9-field acting bloat, "
                                    "no character dialogues inside image prompts, no forced classical Roman statues/emperor references unless the topic is specifically classical Rome.")

                    if args.input_mode == "idea":
                        # Load the actual installed skill based on genre & format. Preserve JSON schema
                        # for image, narration, subtitles and legacy project compatibility.
                        from story_skill_bridge import skill_prompt
                        if speech_pace == "slow":
                            request = request.replace("~115-120 words/minute", "~85-95 words/minute")
                        request += skill_prompt(
                            genre=args.genre,
                            production_mode=getattr(args, "production_mode", "auto"),
                            aspect_ratio=getattr(args, "aspect_ratio", "") or ("9:16" if is_short_mode else "16:9"),
                            is_short=is_short_mode
                        )



                    err=None







                    print(f"PLAN_BATCH_PROMPT Đang kết nối AI viết kịch bản đợt {batch_num}/{total_batches} (Cảnh {pos+1}-{pos+n})...", flush=True)







                    for attempt in range(3):







                        try:







                            res=client.models.generate_content(model=args.model,contents=request,







                                  config={"response_mime_type":"application/json"})







                            chunk=json.loads(res.text)







                            if not isinstance(chunk,dict) or len(chunk.get("scenes",[])) != n:







                                raise ValueError("Scene count mismatch")







                            for sc in chunk["scenes"]:
                                # Normalize description from alternative AI keys
                                if not sc.get('description'):
                                    sc['description'] = sc.get('visual_description') or sc.get('visual_setup') or sc.get('image_prompt') or sc.get('prompt') or sc.get('summary') or ''
                                if not sc.get('visual_setup'):
                                    sc['visual_setup'] = sc.get('description') or 'Cinematic eye-level shot, 16:9 widescreen composition'

                                # Normalize narration from dialogue or speech fields
                                if not sc.get('narration'):
                                    alt_speech = sc.get('dialogue') or sc.get('speech_text') or sc.get('text') or sc.get('monologue') or sc.get('summary') or ''
                                    if alt_speech:
                                        sc['narration'] = str(alt_speech)

                                min_required_words = max(5, int(target_words * 0.55)) if ('target_words' in locals() and target_words > 0) else (6 if (getattr(args, 'scene_seconds', 25) <= 10 or getattr(args, 'minutes', 2.0) <= 1.05) else 18)
                                word_count = len(sc.get('narration', '').split())

                                if attempt < 2 and (word_count < min_required_words or not sc.get('description')):
                                    raise ValueError(f"Scene {sc.get('scene_number')} narration too short ({word_count}/{min_required_words} words) or missing description")
                                elif not sc.get('description') or word_count < 3:
                                    # Fallback healing on final attempt: ensure valid description and narration
                                    if not sc.get('description'):
                                        sc['description'] = f"Cinematic scene {sc.get('scene_number')} from {args.genre} drama, dramatic lighting, high production quality."
                                    if word_count < 3:
                                        sc['narration'] = sc.get('summary') or sc.get('narration') or f"The dramatic story continues in scene {sc.get('scene_number')}."







                                # Verify target language compliance







                                if not validate_scene_language(sc.get("narration", ""), args.language):







                                    print(f"[LANGUAGE_MISMATCH] Phân cảnh {sc.get('scene_number')} không đúng ngôn ngữ {args.language}! Kích hoạt dịch cưỡng bức...", flush=True)







                                    chunk = force_translate_chunk_to_language(client, args.model, chunk, args.language)







                                    if not validate_scene_language(sc.get("narration", ""), args.language):







                                        raise ValueError(f"Language mismatch: narration not in {args.language}")







                                    break







                            if pos == 0 and BAD_OPENING.search(str(chunk["scenes"][0].get("narration",""))):







                                raise ValueError("Generic greeting instead of a strong opening hook")







                            write_json(file,chunk)







                            err=None







                            print(f"PLAN_BATCH_DONE {batch_num}/{total_batches} scenes {pos+1}-{pos+n} saved (accumulated {len(scenes) + len(chunk['scenes'])} scenes)", flush=True)







                            break







                        except TransientGeminiFailure as exc:







                            err=exc







                            if attempt < 2:







                                print(f"[AI_COOLDOWN] Đang chờ khôi phục hạn mức tốc độ Google API (429)... Thử lại lần {attempt+2}/3 sau {10*(attempt+1)}s...", flush=True)







                                time.sleep(10 * (attempt + 1))







                                continue







                            break







                        except Exception as exc:







                            err=exc







                            if attempt < 2:







                                print(f"[AI_RETRY] Đợt {batch_num} gặp sự cố ({type(exc).__name__}). Đang thử lại...", flush=True)







                                time.sleep(3 * (attempt + 1))







                    if err:







                        raise RuntimeError(f"Planning batch {pos//per_batch+1} failed; saved earlier batches") from err







                for sc in chunk["scenes"]:







                    if not sc.get("narration") or not sc.get("description"):







                        raise RuntimeError("Invalid cached scene content")







                scenes.extend(chunk["scenes"])







        if len(scenes) > scene_total:
            scenes = scenes[:scene_total]
        elif len(scenes) < scene_total:
            raise RuntimeError(f"Plan scene count incomplete: got {len(scenes)}/{scene_total}")







    bible=dict(bible)







    bible["production_genre"]=args.genre







    bible["visual_style_mode"]=args.visual_style







    if getattr(args, "aspect_ratio", "") == "9:16" and getattr(args, "size", "") in ("1280x720", "", None):
        w_plan, h_plan = 720, 1280
    else:
        w_plan, h_plan = map(int, str(getattr(args, "size", "1280x720")).lower().split("x"))







    bible["resolution"] = f"{w_plan}x{h_plan}"







    bible["is_vertical"] = bool(h_plan > w_plan)







    bible["aspect_ratio"] = "9:16" if h_plan > w_plan else "16:9"







    arc_report=audit_plan(scenes,args.genre,locked=(args.input_mode=="script"))







    data={"fingerprint":fingerprint,"config":config_data,"created":stamp(),







          "bible":bible,"scenes":scenes,"scene_count":scene_total,







          "story_arc_qc":arc_report}







    if args.input_mode == "idea":

        # Publish a strict 9-field artifact validated by the installed skill.

        # The existing JSON scene plan remains the production source of truth.

        try:


            from story_skill_bridge import export_idea_scenes


            skill_text, skill_report = export_idea_scenes(
                scenes, bible, args.scene_seconds, w_plan, h_plan,
                genre=args.genre,
                production_mode=getattr(args, "production_mode", "auto"),
                title=getattr(args, "series", "My Series"))


            (episode_dir / "skill_scenes.txt").write_text(skill_text, encoding="utf-8")


            write_json(episode_dir / "skill_qc.json", skill_report)


            data["skill_pipeline"] = {"name": skill_report.get("skill_name", "write-video-scene-prompts"),


                                      "sha256": skill_report.get("skill_sha256", ""),


                                      "scenes_validated": skill_report.get("scene_count", len(scenes)),


                                      "text_qc_pass": skill_report.get("pass", True)}


        except Exception as sk_err:


            print(f"[SKILL_EXPORT_WARNING] {sk_err}. Đang tiếp tục kế hoạch sản xuất chính...", flush=True)



    write_json(plan_file,data)







    print(f"PLAN_READY scenes {scene_total}", flush=True)







    print(f"TOTAL_SCENES {scene_total}", flush=True)







    return data















def offline_fixtures(scene, scene_dir, width, height):







    import cv2,numpy as np, math







    i=int(scene["scene_number"])







    img=np.full((height,width,3),255,dtype=np.uint8)







    cv2.rectangle(img,(int(width*.07),int(height*.12)),(int(width*.93),int(height*.88)),(35,35,38),3)







    cv2.circle(img,(int(width*.27),int(height*.48)),int(height*.12),(45,65,225),-1) # Crimson red marker fill







    cv2.circle(img,(int(width*.27),int(height*.48)),int(height*.12),(35,35,38),3)  # Ink contour







    cv2.putText(img,"SERIES EPISODE",(int(width*.38),int(height*.45)),







        cv2.FONT_HERSHEY_SIMPLEX,max(.45,width/1200),(185,85,25),2) # Royal blue marker text







    cv2.putText(img,f"SCENE {i}",(int(width*.45),int(height*.62)),







        cv2.FONT_HERSHEY_SIMPLEX,max(.4,width/1350),(35,145,45),2) # Emerald green marker text







    png=scene_dir/"image.png"







    cv2.imwrite(str(png),img)







    wav_path=scene_dir/"audio.wav"







    sr,secs=24000,3







    sample=np.arange(sr*secs)







    tone=(np.sin(sample*2*np.pi*(220+i*30)/sr)*8500).astype(np.int16)







    with wave.open(str(wav_path),"wb") as wf:







        wf.setnchannels(1);wf.setsampwidth(2);wf.setframerate(sr)







        wf.writeframes(tone.tobytes())







    return png,wav_path















def subtitle_json(scene, duration, path):

    narration = str(scene.get("narration") or "").strip()

    if not narration:

        return False



    # 1. Smart Sentence & Clause Segmentation

    parts = re.split(r'([.!?]+(?:\s+|$))', narration)

    raw_sentences = []

    current = ""

    for p in parts:

        current += p

        if re.search(r'[.!?]+(?:\s+|$)', p):

            s = current.strip()

            if s:

                raw_sentences.append(s)

            current = ""

    if current.strip():

        raw_sentences.append(current.strip())



    chunks = []

    buffer = ""

    for s in raw_sentences:

        w_count = len(s.split())

        buf_count = len(buffer.split())

        if not buffer:

            buffer = s

        elif buf_count + w_count <= 12 and (buf_count < 4 or w_count < 4):

            buffer = f"{buffer} {s}"

        else:

            chunks.append(buffer)

            buffer = s

    if buffer:

        chunks.append(buffer)



    if not chunks:

        words = narration.split()

        if not words:

            return False

        chunks = [" ".join(words[i:i+10]) for i in range(0, len(words), 10)]



    total_chars = max(1, sum(len(c) for c in chunks))

    margin_start = 0.3

    margin_end = 0.3

    usable_duration = max(1.0, float(duration) - margin_start - margin_end)

    gap = 0.12 if len(chunks) > 1 else 0.0

    speech_pool = max(0.5, usable_duration - gap * (len(chunks) - 1))



    subs = []

    cursor = margin_start

    for c_text in chunks:

        fraction = len(c_text) / total_chars

        c_dur = max(0.8, fraction * speech_pool)

        start_t = round(cursor, 3)

        end_t = round(min(float(duration) - 0.1, cursor + c_dur), 3)

        subs.append({"start": start_t, "end": end_t, "text": c_text})

        cursor = end_t + gap



    write_json(path, {"subtitles": subs})

    return True















def render_one(job_path):







    job=read_json(job_path)







    scene=job["scene"]







    bible=job.get("bible",{})







    scene_dir=Path(job["scene_dir"])







    scene_dir.mkdir(parents=True,exist_ok=True)







    scratch = scene_dir / "scratch"; scratch.mkdir(exist_ok=True); os.chdir(scratch) # temp and output must differ







    sys.path.insert(0,str(ENGINE))







    os.environ["GEMINI_API_KEY"]=os.environ.get("GEMINI_API_KEY","")







    width,height=job["width"],job["height"]







    if job["mode"]=="offline":







        import types







        p=types.ModuleType("tools");p.__path__=[str(ENGINE/"tools")]







        u=types.ModuleType("tools.utils")







        u.GLOBAL_OUTPUT_DIR=str(scene_dir)







        sys.modules["tools"]=p;sys.modules["tools.utils"]=u;p.utils=u







        from tools.draw_animation import draw_animation_tool_fn







        from tools.merge_audio_video import merge_audio_video_tool_fn







        from tools.video_subtitle import burn_subtitles_to_video_tool_fn







        image,audio=offline_fixtures(scene,scene_dir,width,height)







    else:







        from tools import image_gen_tool_fn, prompt_tool_fn, generate_tts_audio_tool_fn







        from tools import draw_animation_tool_fn, merge_audio_video_tool_fn







        from tools import burn_subtitles_to_video_tool_fn







        from tools import utils







        utils.set_output_dir(str(scene_dir))







        image=scene_dir/"image.png"







        if job.get("image_provider") == "muse_video":







            from muse_video_provider import make_scene_media







            # Always consult the durable Muse receipt, even if a preview image







            # exists. An image alone must never bypass the required motion clip.







            try:



                make_scene_media(scene, bible, image, width=width, height=height,



                                 duration=int(scene.get("script_seconds", job.get("scene_seconds", 8))))



            except Exception as muse_err:



                if image.exists() and image.stat().st_size > 1000:

                    print(f"[MUSE_FALLBACK] Không thể tạo video Muse ({muse_err}). Đã có sẵn ảnh tĩnh ({image.name}, {image.stat().st_size} bytes), tự động kích hoạt Flow Video tạo video chuyển động cho Hook...", flush=True)

                    job["image_provider"] = job.get("fallback_image_provider", "mcp_v2")

                    job["is_hook_motion_video"] = True

                elif job.get("is_auto_muse_hook"):

                    print(f"[AUTO_HOOK_WARN] Không thể tạo video Muse cho Hook Cảnh 1 ({muse_err}). Tự động bọc lót dùng ảnh tĩnh & Flow Video...", flush=True)

                    job["image_provider"] = job.get("fallback_image_provider", "gemini")

                    job["is_hook_motion_video"] = True



                else:



                    raise







        if job.get("image_provider") != "muse_video" and (not image.exists() or image.stat().st_size<1000):







            if job.get("image_provider") == "flowkit":
                raise RuntimeError("FLOWKIT_REMOVED_SELECT_MCP_V2")
            elif job.get("image_provider") == "mcp_v2":







                raise RuntimeError("MCP_BATCH_IMAGE_NOT_AVAILABLE: no scene-level resubmission")







            else:







                has_clone = bool(job.get("bible",{}).get("characters") and job["bible"]["characters"][0].get("clone_prompt"))







                if job.get("visual_style","whiteboard")!="whiteboard" or has_clone:







                    from mcp_v2_batch import image_prompt







                    imgprompt=image_prompt(scene,job["bible"])







                else:







                    imgprompt=prompt_tool_fn(scene["description"],visual_setup=scene.get("visual_setup",""),







                                            text_overlay=scene.get("text_overlay",""),







                                            global_plan=job["bible"])







                if not isinstance(imgprompt,str) or "error" in imgprompt.lower():
                    # Robust fallback: use pre-generated scene prompt or description instead of failing
                    imgprompt = scene.get("prompt") or scene.get("description") or scene.get("visual_setup") or "Cinematic scene, 8k resolution, detailed lighting"
                    print(f"[PROMPT_FALLBACK] Prompt generator gap loi, su dung truc tiep mo ta canh ({scene.get('scene_number', '?')})", flush=True)







                ref=job.get("anchor_image","")
                genre_str = str(job.get("genre", "")).lower()

                # HOLLYWOOD MULTI-SHOT DIVERSITY FILTER:
                # Do NOT force protagonist face IP-Adapter on objects, landscapes, or other characters!
                scene_text = (str(job.get("scene", {}).get("description", "")) + " " + str(job.get("scene", {}).get("visual_setup", "")) + " " + str(job.get("scene", {}).get("summary", ""))).lower()
                is_object_or_broll = any(kw in scene_text for kw in ("boots", "envelope", "letter", "counter", "desk", "paper", "pen", "road", "landscape", "cabin exterior", "doorway", "fireplace", "window", "scale", "post office", "mailbag", "snowy prairie", "empty"))
                is_other_person = any(kw in scene_text for kw in ("woman", "widow", "female", "girl", "elderly woman", "postman", "mailman", "child", "children", "boy", "wife", "mother"))

                bible_chars = job.get("bible", {}).get("characters", [])
                anchor_char_name = str(bible_chars[0].get("name", "")).lower() if bible_chars else ""

                if is_object_or_broll or is_other_person:
                    ref = "" # Absolutely clear IP-Adapter reference! Allow true object/female generation!
                elif anchor_char_name and (anchor_char_name not in scene_text and not any(kw in scene_text for kw in ("protagonist", "his face", "he stands", "he sits", "he looks"))):
                    ref = "" # Clear IP-Adapter if protagonist isn't explicitly active in this shot!

                if any(g in genre_str for g in ("stoic", "philosophy", "statue")):
                    ref = ""

                prov = job.get("image_provider")







                if prov=="v2_tuanstor":







                    from v2_tuanstor_image import make_image







                    generated=make_image(imgprompt,scene_dir/"image.png",







                            reference_path=ref if (ref and Path(ref).is_file()) else None)







                elif prov=="comfyui":







                    from comfyui_image_provider import make_image







                    generated=make_image(imgprompt,scene_dir/"image.png",







                            reference_path=ref if (ref and Path(ref).is_file()) else None,







                            visual_style=job.get("visual_style","whiteboard"),







                            genre=job.get("genre","documentary"),







                            width=width,height=height)







                else:







                    generated=image_gen_tool_fn(imgprompt,







                            reference_image_path=ref if Path(ref).is_file() else None)







            if not Path(generated).is_file():







                raise RuntimeError("Image generation failed: "+str(generated)[:200])







            if Path(generated).resolve()!=image.resolve():







                shutil.copy2(generated,image)







        if job.get("image_provider") not in ("comfyui", "muse_video", "mock", "placeholder") and job.get("clean_watermark", True) and image.is_file():







            try:







                from clean_watermark import remove_gemini_watermark







                remove_gemini_watermark(image)







            except Exception as cw_err:







                print(f"[WATERMARK_CLEANER] Note: {cw_err}", flush=True)







        audio=scene_dir/"audio.wav"



        muse_clip_file = scene_dir / "muse_clip.mp4"







        # 100% GIỮ NGUYÊN BẢN ÂM THANH & GIỌNG NÓI GỐC CỦA MUSE AI CHO HOOK CẢNH 1 - KHÔNG LỒNG TIẾNG NGOÀI!



        if job.get("image_provider") == "muse_video" and muse_clip_file.is_file() and muse_clip_file.stat().st_size > 1024:



            print(f"[MUSE_NATIVE_AUDIO] 🎙️ Cảnh {scene.get('scene_number', 1)}: Sử dụng 100% âm thanh & giọng nói gốc nguyên bản của Muse AI (KHÔNG lồng tiếng ngoài)!", flush=True)



            import subprocess



            cmd_extract = [



                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",



                "-i", str(muse_clip_file.resolve()),



                "-vn", "-c:a", "pcm_s16le", "-ar", "24000", "-ac", "1",



                str(audio.resolve())



            ]



            subprocess.run(cmd_extract, check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))



            generated = str(audio)



        elif not audio.exists() or audio.stat().st_size<2000:







            if not scene["narration"].strip():







                from studio_color_render import create_silence







                create_silence(audio,scene.get("script_seconds",job.get("scene_seconds",8)))







                generated=str(audio)







            else:







                scene_num = int(scene.get("scene_number", 1))







                total_sc = int(job.get("total_scenes") or 10)







                if scene_num == 1:







                    scene_intent = "VIRAL COLD OPEN HOOK: immediate dramatic curiosity, punchy delivery, intense curiosity gap to hook the listener in the first 3 seconds"







                elif scene_num == total_sc:







                    scene_intent = "SUSPENSEFUL CLIFFHANGER: lingering unresolved tension, contemplative pauses, leaving an open loop"







                elif scene_num >= int(total_sc * 0.7):







                    scene_intent = "DRAMATIC CLIMAX: mounting emotional weight, sharp revelation, heightened intensity"







                else:







                    scene_intent = "DYNAMIC STORYTELLING: natural prosody, expressive breathing pauses, engaging conversational flow"















                base_style = tts_style(job["language"], job.get("genre", "documentary"), job.get("region", "auto"), pacing=job.get("speech_pacing", "slow"))







                combined_style = f"{base_style} Scene {scene_num}/{total_sc} Emotional Intent: {scene_intent}."















                generated=generate_tts_audio_tool_fn(







                    scene["narration"],language=job["language"],







                    voice_name=job.get("voice_name","Kore"),







                    voice_style=combined_style)







            if not Path(generated).is_file():







                raise RuntimeError("TTS generation failed: "+str(generated)[:200])







            if Path(generated).resolve()!=audio.resolve():







                shutil.copy2(generated,audio)



                gen_words = Path(str(generated) + ".words.json")



                if gen_words.exists():



                    try:



                        shutil.copy2(gen_words, Path(str(audio) + ".words.json"))



                    except Exception:



                        pass







        if str(scene.get("narration") or "").strip():
            from audio_signal_guard import require_audible_if_spoken
            require_audible_if_spoken(audio, scene["narration"])

        if scene.get("locked_script"):







            with wave.open(str(audio),"rb") as recorded:







                spoken_seconds=recorded.getnframes()/max(1,recorded.getframerate())







            allowed_seconds=float(scene.get("script_seconds",job.get("scene_seconds",8)))







            if spoken_seconds>allowed_seconds*1.25+0.4:







                raise RuntimeError(







                    "LOCKED_SCRIPT_DIALOGUE_TOO_LONG: speech %.2fs exceeds "







                    "scene %.2fs. Original words have NOT been changed. "







                    "Shorten the dialogue or extend the scene duration."







                    %(spoken_seconds,allowed_seconds))







    render_style=job.get("visual_style","whiteboard")







    motion_mode=job.get("motion_mode","ken_burns")







    style_receipt=scene_dir/"render_style.json"







    previous_receipt=(read_json(style_receipt) if style_receipt.exists() else {})







    previous_style=previous_receipt.get("visual_style")







    previous_motion=previous_receipt.get("motion_mode","ken_burns")







    hand_color_engine="contour_fill_v2_20261013"







    is_flow_video = (render_style == "flow_video" or motion_mode == "flow_video" or bool(job.get("is_hook_motion_video")))







    was_flow_video = (previous_style == "flow_video" or previous_motion == "flow_video")







    if (render_style in ("hand_color", "flow_video", "colored_marker", "whiteboard") or previous_style in ("hand_color", "flow_video", "colored_marker", "whiteboard")







            or is_flow_video or was_flow_video):







        if (previous_style!=render_style or previous_motion!=motion_mode or







            (render_style=="hand_color" and







             previous_receipt.get("hand_color_engine")!=hand_color_engine)):







            # Never delete image/audio: these may be the user's paid MCP image







            # or saved original narration. Only derived media are regenerated.







            for name in ("silent.mp4","merged.mp4","final.mp4","result.json"):







                cached=scene_dir/name







                if cached.exists():cached.unlink()







    merged=scene_dir/"merged.mp4"







    silent=scene_dir/"silent.mp4"







    if not silent.exists() or not qc_silent(silent):







        muse_clip = scene_dir / "muse_clip.mp4"







        if job.get("image_provider") == "muse_video" and not muse_clip.is_file():







            raise RuntimeError("MUSE_OUTPUT_MISSING: Chưa có video chuyển động đã xác minh.")







        if job.get("image_provider") == "muse_video" and muse_clip.is_file() and muse_clip.stat().st_size > 1024:



            # 100% Video & Âm thanh gốc nguyên bản từ Muse AI (scale canvas chuẩn, giữ nguyên âm thanh gốc)



            import subprocess



            cmd_scale_merged = [



                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",



                "-i", str(muse_clip.resolve()),



                "-vf", f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},setsar=1",



                *([ "-c:v", "h264_nvenc", "-preset", "p4", "-cq", "20", "-pix_fmt", "yuv420p" ] if getattr(__import__("studio_color_render", fromlist=["_hardware_encoder_usable"]), "_hardware_encoder_usable", lambda: False)() else [ "-c:v", "libx264", "-pix_fmt", "yuv420p" ]),



                "-c:a", "aac", "-b:a", "192k",



                str(merged.resolve())



            ]



            subprocess.run(cmd_scale_merged, check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))



            raw = str(merged)







        elif job.get("visual_style")=="hand_color":







            from studio_hand_color import hand_color_video







            raw=hand_color_video(image,audio,silent,width,height)







        elif job.get("visual_style") in ("colored_marker", "whiteboard"):







            from studio_colored_marker import colored_marker_video







            raw=colored_marker_video(image,audio,silent,width,height)







        elif job.get("image_provider") == "comfyui" and (is_flow_video or job.get("is_hook_motion_video")):
            try:
                from studio_comfyui_motion import render_comfyui_motion_for_scene
                raw = render_comfyui_motion_for_scene(scene, bible, image, audio, silent, width=width, height=height)
            except Exception as ad_err:
                print(f"[ANIMATEDIFF_FALLBACK] AnimateDiff error: {ad_err}. Falling back to 2.5D camera...", flush=True)
                from studio_color_render import color_video
                scene_text = " ".join(filter(None, [scene.get("prompt"), scene.get("description"), scene.get("narration"), scene.get("visual_setup")]))
                raw = color_video(image, audio, silent, width, height, camera_motion=job.get("camera_motion", "auto"), overlay_preset=job.get("atmospheric_overlay", "auto"), scene_text=scene_text)
        elif is_flow_video:
            try:
                from studio_flow_video import render_flow_video_for_scene
                raw=render_flow_video_for_scene(
                    scene, bible, image, silent,
                    model=job.get("flow_video_model", "Omni 1.1 Flash"),
                    duration=job.get("flow_video_duration", 8),
                    aspect_ratio="16:9" if width >= height else "9:16",
                    width=width, height=height
                )
            except Exception as fv_err:
                print(f"[FLOW_VIDEO_FALLBACK] Flow video error: {fv_err}. Falling back to 2.5D camera...", flush=True)
                from studio_color_render import color_video
                scene_text = " ".join(filter(None, [scene.get("prompt"), scene.get("description"), scene.get("narration"), scene.get("visual_setup")]))
                raw = color_video(image, audio, silent, width, height, camera_motion=job.get("camera_motion", "auto"), overlay_preset=job.get("atmospheric_overlay", "auto"), scene_text=scene_text)







        elif job.get("visual_style","whiteboard")!="whiteboard" and job["mode"]=="live":







            from studio_color_render import color_video







            scene_text = " ".join(filter(None, [







                scene.get("prompt"),







                scene.get("description"),







                scene.get("text"),







                scene.get("dialogue"),







                scene.get("speech_text")







            ]))







            raw=color_video(image,audio,silent,width,height,







                            scene_index=scene.get("scene_number",1),







                            motion_type=job.get("camera_motion","auto"),







                            overlay_effect=job.get("atmospheric_overlay","auto"),







                            genre=job.get("genre","documentary"),







                            scene_text=scene_text)







        else:







            target_audio_dur = None

            if audio and Path(audio).is_file():

                try:

                    import wave

                    with wave.open(str(audio), "rb") as _w:

                        target_audio_dur = _w.getnframes() / max(1, _w.getframerate())

                except Exception:

                    pass



            raw=draw_animation_tool_fn(str(image),resize_wd=width,resize_ht=height,







                    frame_rate=25 if job["mode"]=="live" else 15,







                    split_len=16 if job["mode"]=="live" else 18,







                    object_skip_rate=7 if job["mode"]=="live" else 10,







                    end_duration_sec=1,

                    target_duration=target_audio_dur)







        if not Path(raw).is_file():







            raise RuntimeError("Drawing render failed: "+str(raw)[:200])







        if Path(raw).resolve()!=silent.resolve():







            shutil.copy2(raw,silent)

        is_cloud_watermark_video = (
            ((job.get("motion_mode") == "flow_video" or job.get("is_hook_motion_video")) and job.get("image_provider") != "comfyui")
            or (job.get("image_provider") in ("flow_video", "veo", "flowkit") and job.get("image_provider") != "comfyui")
        )
        if is_cloud_watermark_video and job.get("clean_watermark", True) and silent.is_file():
            try:
                from clean_watermark import remove_video_watermark
                remove_video_watermark(silent, silent, width=width, height=height)
            except Exception:
                pass







    write_json(style_receipt,{"visual_style":render_style,







        "motion_mode":motion_mode,







        **({"hand_color_engine":hand_color_engine} if render_style=="hand_color" else {})})



















    if not merged.exists() or not qc_complete(merged,width,height):







        effective_audio = audio

        if is_flow_video and audio and Path(audio).is_file():

            try:

                from studio_flow_video import mix_foley_into_scene_audio

                foley_audio = scene_dir / "audio_with_foley.wav"

                if mix_foley_into_scene_audio(Path(audio), scene, foley_audio):

                    effective_audio = foley_audio

            except Exception:

                pass

        ret=merge_audio_video_tool_fn(str(silent),str(effective_audio),str(merged))







        if not Path(ret).is_file():







            raise RuntimeError("FFmpeg audio merge failed: "+str(ret)[-300:])







    final=scene_dir/"final.mp4"







    if job.get("subtitles") and scene["narration"].strip() and job.get("subtitle_style") != "none":







        _,sec=ffprobe(merged)







        js=scene_dir/"subtitles.json"







        subtitle_json(scene,sec,js)







        tmp_final = scene_dir / "final_burn.mp4"







        if tmp_final.exists():







            try:







                tmp_final.unlink()







            except Exception:







                pass







        ret=burn_subtitles_to_video_tool_fn(







            str(merged), str(js), str(tmp_final),







            subtitle_style=job.get("subtitle_style", "karaoke_viral"),







            video_height=height,







            video_width=width,







            custom_font_size=job.get("subtitle_size", 0)







        )







        if not Path(ret).is_file():







            raise RuntimeError("FFmpeg subtitle burn failed: "+str(ret)[-300:])







        if Path(ret).resolve() != final.resolve():







            shutil.move(str(ret), str(final))







    else:







        shutil.copy2(merged,final)







    qc=qc_clip(final,True,(width,height))
    if str(scene.get("narration") or "").strip():
        from audio_signal_guard import require_audible_if_spoken
        require_audible_if_spoken(final, scene["narration"])







    report={"status":"PASS","scene":scene["scene_number"],"qc":qc,







            "input_hash":job["input_hash"],"image_path":str(image),"final_path":str(final),







            "created":stamp()}







    write_json(scene_dir/"result.json",report)







    print("SCENE_PASS",scene["scene_number"],json.dumps(qc))







    return 0















def qc_silent(path):







    try:







        return qc_clip(path,False)["duration_seconds"]>0.5







    except Exception:







        return False















def qc_complete(path,w,h):







    try:







        qc_clip(path,True,(w,h))







        return True







    except Exception:







        return False















def compute_cta_times(dur: float, is_vertical: bool = False) -> list:

    """Computes periodic CTA appearance timestamps based on video duration.

    - Minute 1 (Early Engagement Hook): Appears at ~45s - 50s.

    - Periodic interval: Every 2.5 - 3 minutes (160s - 180s).

    - Finale: Last 8.5s of the video.

    - Vertical Shorts (<= 90s): Appears early at 10s - 16s + finale.

    """

    if dur < 8.0:

        return []



    # Case 1: Shorts 9:16 or short clips (<= 90s)

    if is_vertical or dur <= 90.0:

        t_first = round(max(10.0, min(16.0, dur * 0.28)), 1)

        times = [t_first]

        if dur >= 38.0 and (dur - 6.5) > (t_first + 12.0):

            times.append(round(dur - 6.5, 1))

        return times



    # Case 2: Standard Long/Mid-form Video (16:9)

    # First CTA at minute 1 (45s - 50s) to capture maximum viewer retention

    first_cta = round(min(50.0, max(25.0, dur * 0.15)), 1)

    times = [first_cta]



    # Periodic interval: every ~160s (2.6 minutes) for optimal engagement

    interval = 160.0 if dur <= 600.0 else 180.0

    curr = first_cta + interval

    while curr <= (dur - 25.0):

        times.append(round(curr, 1))

        curr += interval



    # Finale CTA in the last 8.5 seconds before end

    finale_t = round(dur - 8.5, 1)

    if finale_t > (times[-1] + 35.0):

        times.append(finale_t)



    return times





def apply_cinematic_cta_and_audio(source_video, output_video, width, height):







    """Overlays Subscribe/Like/Bell CTA periodically (every 10m for long videos, 5m for short videos),







    with whoosh SFX and ambient BGM."""







    source_p = Path(source_video)







    output_p = Path(output_video)















    cta_path = ENGINE / "assets" / "social_cta" / "cta_like_subscribe_bell_v9.mp4"







    bgm_path = ENGINE / "assets" / "music" / "ambient_mystery" / "fallback_ambient_mystery.wav"







    sfx_path = ENGINE / "assets" / "sfx" / "whoosh.wav"















    try:







        meta = qc_clip(source_p)







        dur = float(meta.get("duration_seconds") or 0.0)







    except Exception:







        dur = 0.0















    is_vertical = height > width

    times = compute_cta_times(dur, is_vertical=is_vertical)

    # Hollywood Master Sound Design (Multi-act BGM, Dynamic Ducking, Timed SFX)
    try:
        from studio_sound_design import apply_hollywood_audio_master
        if apply_hollywood_audio_master(source_p, output_p, cta_path if cta_path.is_file() else None, times, width, height, ENGINE):
            print(f"[CINEMATIC_CTA] Master am thanh dien anh Hollywood & Dynamic Ducking thanh cong 100%!", flush=True)
            return
    except Exception as exc:
        print(f"[CINEMATIC_CTA_WARN] Nang cap am thanh Hollywood gap loi ({exc}), chuyen sang che do du phong an toan.", flush=True)



    if not cta_path.is_file() or not times:







        if source_p.resolve() != output_p.resolve():







            shutil.copy2(source_p, output_p)







        return















    # Dimensions







    cta_w = int(width * (0.75 if is_vertical else 0.38))







    margin_b = 160 if is_vertical else 35















    # 1. Video Filter







    v_filters = []







    if len(times) == 1:







        t0 = times[0]







        v_filters.append(







            f"[1:v]chromakey=0x00FF00:0.25:0.08,scale={cta_w}:-1,setpts=PTS-STARTPTS+{t0}/TB,format=rgba[cta];"







            f"[0:v][cta]overlay=(W-w)/2:H-h-{margin_b}:eof_action=pass[vout]"







        )







        final_v = "[vout]"







    else:







        v_filters.append(







            f"[1:v]chromakey=0x00FF00:0.25:0.08,scale={cta_w}:-1,format=rgba,split={len(times)}"







            + "".join(f"[c{i}]" for i in range(len(times)))







        )







        curr_v = "0:v"







        for i, t in enumerate(times):







            v_filters.append(f"[c{i}]setpts=PTS-STARTPTS+{t}/TB[cta{i}]")







            next_v = f"v{i+1}"







            v_filters.append(f"[{curr_v}][cta{i}]overlay=(W-w)/2:H-h-{margin_b}:eof_action=pass[{next_v}]")







            curr_v = next_v







        final_v = f"[{curr_v}]"















    inputs = ["-i", str(source_p), "-i", str(cta_path)]







    next_input_idx = 2







    audio_chains = ["[0:a]"]















    # 2. Audio Filters







    extra_a_filters = []















    # Ambient BGM







    if bgm_path.is_file():







        inputs.extend(["-i", str(bgm_path)])







        extra_a_filters.append(f"[{next_input_idx}:a]aloop=loop=-1:size=2e+09,volume=0.10[bgm]")







        audio_chains.append("[bgm]")







        next_input_idx += 1















    # SFX Whoosh







    if sfx_path.is_file():







        inputs.extend(["-i", str(sfx_path)])







        sfx_idx = next_input_idx







        next_input_idx += 1















        if len(times) == 1:







            ms = int(times[0] * 1000)







            extra_a_filters.append(f"[{sfx_idx}:a]adelay={ms}|{ms},volume=0.35[sfx]")







            audio_chains.append("[sfx]")







        else:







            extra_a_filters.append(f"[{sfx_idx}:a]asplit={len(times)}" + "".join(f"[sa{i}]" for i in range(len(times))))







            for i, t in enumerate(times):







                ms = int(t * 1000)







                extra_a_filters.append(f"[sa{i}]adelay={ms}|{ms}[sfx{i}]")







            all_sfx_tags = "".join(f"[sfx{i}]" for i in range(len(times)))







            extra_a_filters.append(f"{all_sfx_tags}amix=inputs={len(times)}:dropout_transition=0,volume=0.35[sfx]")







            audio_chains.append("[sfx]")















    if len(audio_chains) > 1:







        extra_a_filters.append(f"{''.join(audio_chains)}amix=inputs={len(audio_chains)}:duration=first:dropout_transition=2,loudnorm=I=-14:LRA=7:TP=-1,aformat=channel_layouts=stereo[aout]")







        audio_map = "[aout]"







    else:







        extra_a_filters.append("[0:a]loudnorm=I=-14:LRA=7:TP=-1,aformat=channel_layouts=stereo[aout]")







        audio_map = "[aout]"















    filt_complex = ";".join(v_filters)







    if extra_a_filters:







        filt_complex += ";" + ";".join(extra_a_filters)















    tmp_out = output_p.parent / f"cta_pending_{output_p.name}"







    cmd = [







        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",







        *inputs,







        "-filter_complex", filt_complex,







        "-map", final_v, "-map", audio_map,







        *([ "-c:v", "h264_nvenc", "-preset", "p4", "-cq", "20" ] if getattr(__import__("studio_color_render", fromlist=["_hardware_encoder_usable"]), "_hardware_encoder_usable", lambda: False)() else [ "-c:v", "libx264", "-preset", "fast", "-crf", "20" ]),







        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",







        "-movflags", "+faststart",







        str(tmp_out)







    ]







    time_strs = [f"{int(t//60)}m{int(t%60):02d}s" if t >= 60 else f"{t:.1f}s" for t in times]







    print(f"[CINEMATIC_CTA] Đang chèn nút Like/Sub/Chuông ({', '.join(time_strs)} - tổng {len(times)} lần) & hòa âm BGM...", flush=True)







    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=3600,







                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))







    if p.returncode == 0 and tmp_out.is_file() and tmp_out.stat().st_size > 10000:







        try:







            os.replace(tmp_out, output_p)







        except Exception:







            time.sleep(1.0)







            shutil.copy2(tmp_out, output_p)







            tmp_out.unlink(missing_ok=True)







        print(f"[CINEMATIC_CTA] Hoàn tất lồng ghép {len(times)} lần nút tương tác và âm thanh điện ảnh 100%!", flush=True)







    else:







        print(f"[CINEMATIC_CTA] Cảnh báo lồng hiệu ứng ({p.stderr[-200:]}), giữ nguyên bản video gốc.", flush=True)







        if source_p.resolve() != output_p.resolve():







            shutil.copy2(source_p, output_p)







        if tmp_out.is_file():







            tmp_out.unlink(missing_ok=True)















def concat_episode(scene_clips, output):







    listing=output.parent/"concat_list.txt"







    listing.write_text("".join("file '"+str(Path(p).resolve()).replace("\\","/").replace("'","'\\''")+"'\n"







                               for p in scene_clips),encoding="utf-8")







    tmp=output.parent/"final_pending.mp4"







    cmd=["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0",







         "-i",str(listing),"-c","copy","-movflags","+faststart",str(tmp)]







    p=subprocess.run(cmd,capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=3600, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))







    if p.returncode:







        raise RuntimeError("Concatenation failed: "+p.stderr[-1200:])







    qc_clip(tmp)







    os.replace(tmp,output)







    return qc_clip(output)















def run(args):







    if not args.prompt and not args.prompt_file and not (args.input_mode=="link" and args.reference_url):







        if getattr(args, "resume", False):







            series_dir = PRODUCTIONS / slug(args.series)







            episode_dir = series_dir / f"episode_{args.episode:03d}"







            plan_file = episode_dir / "plan.json"







            if plan_file.is_file():







                try:







                    p_data = read_json(plan_file)







                    cfg = p_data.get("config") or {}
                    if cfg.get("language") and (getattr(args, "language", "Auto") == "Auto" or "--language" not in sys.argv):
                        args.language = cfg["language"]
                    if cfg.get("region") and (str(getattr(args, "region", "auto")).lower() == "auto" or "--region" not in sys.argv):
                        args.region = cfg["region"]
                    if cfg.get("genre") and (getattr(args, "genre", "auto") == "auto" or "--genre" not in sys.argv):
                        args.genre = cfg["genre"]
                    if cfg.get("voice_name") and (getattr(args, "voice_name", "auto") == "auto" or "--voice-name" not in sys.argv):
                        args.voice_name = cfg["voice_name"]
                    if cfg.get("input_mode") and "--input-mode" not in sys.argv:
                        args.input_mode = cfg["input_mode"]
                    if cfg.get("reference_url") and not getattr(args, "reference_url", ""):
                        args.reference_url = cfg["reference_url"]
                    args.prompt = cfg.get("prompt") or p_data.get("title") or p_data.get("synopsis") or "Stoic Marcus Aurelius"







                except Exception:







                    pass







        if not args.prompt and not args.prompt_file and not (args.input_mode=="link" and args.reference_url):







            raise RuntimeError("Provide an idea, screenplay, or YouTube reference URL")







    prompt=Path(args.prompt_file).read_text(encoding="utf-8") if args.prompt_file else (args.prompt or "")







    if args.input_mode not in ("idea","link","script"):







        raise ValueError("Input mode invalid")







    original_genre=args.genre







    original_visual_style=args.visual_style







    original_voice=args.voice_name







    original_language=args.language

    # Auto settings in the next chapter inherit the established series profile.

    if args.input_mode == "idea" and args.episode > 1:

        prev_file = PRODUCTIONS / slug(args.series) / f"episode_{args.episode-1:03d}" / "plan.json"

        prev_plan = read_json(prev_file) if prev_file.is_file() else {}

        prev_cfg = prev_plan.get("config") or {}

        if isinstance(prev_cfg, dict) and prev_cfg.get("input_mode") == "idea":

            for field in ("language", "genre", "visual_style", "region"):

                selected = getattr(args, field, None)

                previous = prev_cfg.get(field)

                if str(selected).lower() == "auto" and previous and str(previous).lower() != "auto":

                    setattr(args, field, previous)







    if args.language=="Auto":







        from studio_modes import detect_language







        args.language=("English" if args.input_mode=="link" else detect_language(prompt))







    args.genre=resolve_genre(args.genre,detect_genre(prompt) if args.input_mode!="link" else None)







    args.visual_style=resolve_style(args.visual_style,args.genre)







    args.region = "auto" if str(args.region).lower()=="auto" else str(args.region).upper()







    if args.region not in REGIONS:







        raise ValueError("Unknown region")







    args.voice_name=voice_for(args.language,args.genre,args.region,args.voice_name)







    if args.input_mode!="link" and not prompt.strip():







        raise RuntimeError("Input text is empty")







    if args.input_mode=="script":







        parse_locked_screenplay(prompt, scene_seconds=getattr(args, "scene_seconds", 7)) # validate or auto-segment







    try:







        args.minutes = float(args.minutes)







        if not math.isfinite(args.minutes) or args.minutes <= 0:







            args.minutes = 1.0







    except (ValueError, TypeError):







        args.minutes = 1.0







    args.minutes = max(0.1, min(args.minutes, 180.0))















    try:







        args.scene_seconds = int(args.scene_seconds)







        if args.scene_seconds <= 0:

            # Shorts & vertical 9:16 must use fast-paced 6-8s scenes, never dragging 25s

            if getattr(args, "minutes", 2.0) <= 1.05 or getattr(args, "aspect_ratio", "") == "9:16" or getattr(args, "is_short", False):

                args.scene_seconds = 7

            else:

                args.scene_seconds = 25

    except (ValueError, TypeError):

        if getattr(args, "minutes", 2.0) <= 1.05 or getattr(args, "aspect_ratio", "") == "9:16" or getattr(args, "is_short", False):

            args.scene_seconds = 7

        else:

            args.scene_seconds = 25







    args.scene_seconds = max(4, min(args.scene_seconds, 60))







    args.workers = max(1, min(int(args.workers or 1), 16))







    width,height=map(int,args.size.lower().split("x"))







    if (width,height) not in [(640,360),(1280,720),(1920,1080),(720,1280),(1080,1920)]:







        raise RuntimeError("Supported formats: 640x360, 1280x720, 1920x1080, 720x1280 (Shorts), 1080x1920 (Shorts FHD)")







    if args.mode=="live" and not own_api_key():







        try:







            from tuansuapi_provider import get_gateway_config







            gw = get_gateway_config()







            if not (gw.get("enabled") == "1" and gw.get("api_key")):







                raise RuntimeError("Gemini text/TTS key missing from Studio/.env và chưa cấu hình API Bên Thứ Ba (Tuấn Stor)")







        except Exception as exc:







            raise RuntimeError("Gemini text/TTS key missing from Studio/.env và chưa cấu hình API Bên Thứ Ba: " + str(exc))







    if args.mode=="live" and args.image_provider=="v2_tuanstor":







        from v2_tuanstor_image import config as v2_image_config







        v2_image_config()  # Read-only access; never write to V2







    if args.mode=="live" and args.image_provider=="comfyui":







        from comfyui_image_provider import is_installed as comfy_is_installed







        if not comfy_is_installed():







            raise RuntimeError("ComfyUI chưa được cài đặt tại D:\\ComfyUI. Vui lòng cài đặt ComfyUI để sử dụng chế độ GPU.")







    if args.mode=="live" and args.image_provider=="muse_video":







        from muse_video_provider import test_muse_connection







        muse_status = test_muse_connection()







        if not muse_status.get("ok"):







            raise RuntimeError(muse_status.get("message", "MUSE_NOT_READY"))







        args.workers = 1







    if (args.mode=="live" and args.input_mode=="link" and







          getattr(args,"link_clone_mode","exact_clone")=="exact_clone"):







        existing_ep=(PRODUCTIONS/slug(args.series)/f"episode_{args.episode:03d}")







        existing_plan=existing_ep/"plan.json"







        if existing_plan.is_file():







            from clone_integrity import require_fresh_exact_clone_plan







            ref_file=existing_ep/"reference_analysis.json"







            reference=read_json(ref_file) if ref_file.is_file() else {}







            require_fresh_exact_clone_plan(read_json(existing_plan),reference)















    if args.mode=="live" and args.image_provider=="mcp_v2":







        from studio_mcp.projects import is_registered, url_for







        from studio_mcp.accounts import active_account







        chosen=getattr(args,"mcp_project_url","") or url_for(active_account(),args.genre)







        if not chosen or not is_registered(active_account(),chosen):







            raise RuntimeError("STORYBOARD_GENRE_PROJECT_UNMAPPED")







        os.environ["STORYBOARD_FROZEN_PROJECT_URL"]=chosen







        # Note: MCP V2 image batching runs sequentially upfront via mcp_v2_batch.py.







        # Scene video rendering (TTS + Ken Burns + subtitles) runs independently and supports multi-workers.







        if args.workers > 16:







            args.workers = 16







        if not 1<=args.mcp_max_images<=1000:







            raise RuntimeError("Approve MCP image budget of 1..1000 for this episode")







        from mcp_v2_images import preflight







        from studio_mcp.accounts import require_production_browser







        preflight()







        # Never spend Gemini planning/API calls for a closed private Flow browser.







        require_production_browser(tool_url=chosen,







            allow_duplicate_for_isolated_job=bool(re.fullmatch(







                r"[a-fA-F0-9]{32}",os.getenv("STORYBOARD_CANARY_TARGET_ID",""))))















    if args.input_mode=="link":







        url=youtube_url(args.reference_url or prompt)







        if args.mode=="live":







            target_series=PRODUCTIONS/slug(args.series)







            target_ep=target_series/f"episode_{args.episode:03d}"







            data_path=target_ep/"reference_analysis.json"







            if data_path.is_file():







                details=read_json(data_path)







                if details.get("canonical_url")!=url and details.get("source_url")!=url:



                    print(f"[CLONE] Phát hiện link tham khảo mới cho tập {args.episode}, đang cập nhật phân tích...", flush=True)



                    from competitor_cloner import analyze_competitor_character



                    details = analyze_competitor_character(url)



                    write_json(data_path, details)







                if not details.get("character") or not details.get("whole_video_verified"):







                    from competitor_cloner import analyze_competitor_character







                    details=analyze_competitor_character(url)







                    write_json(data_path,details)







            else:







                from competitor_cloner import analyze_competitor_character







                details=analyze_competitor_character(url)







                write_json(data_path,details)















            # Auto-save competitor thumbnail and metadata into episode folder for SEO package learning







            try:







                from competitor_cloner import extract_youtube_video_id, download_reference_thumbnail







                from studio_input_modes import extract_youtube_metadata







                comp_vid = details.get("video_id") or extract_youtube_video_id(url)







                comp_thumb = target_ep / "thumbnail_competitor_trend.jpg"







                if not comp_thumb.exists() or comp_thumb.stat().st_size < 3000:







                    download_reference_thumbnail(comp_vid, comp_thumb)







                    print(f"[SEO_CLONER] Đã tải ảnh thumbnail đối thủ về: {comp_thumb.name} để học gói SEO!", flush=True)







                if not details.get("keywords") or not details.get("title"):







                    yt_meta = extract_youtube_metadata(url)







                    details.update({k: v for k, v in yt_meta.items() if v})







                    write_json(data_path, details)







            except Exception as thumb_err:







                print(f"[SEO_CLONER] Lưu ý tải thumbnail đối thủ: {thumb_err}", flush=True)















            if getattr(args,"link_clone_mode","exact_clone")=="exact_clone":

                from clone_integrity import require_valid_reference

                try:

                    require_valid_reference(details,duration_minutes=details.get("duration_minutes",0))

                    if not (isinstance(details.get("character"),dict) and

                            details["character"].get("vision_verified") and

                            details["character"].get("in_video_verified")):

                        print("[CLONE] Character vision evidence not fully verified; adapting gracefully.", flush=True)

                        args.link_clone_mode = "creative_adaptation"

                except Exception as req_err:

                    print(f"[CLONE] Exact reference verification softened: {req_err}. Transitioning to creative adaptation.", flush=True)

                    args.link_clone_mode = "creative_adaptation"







            if original_language=="Auto":







                guess=str(details.get("language") or details.get("primary_language","English")).strip().lower()







                known={"vietnamese":"Vietnamese","spanish":"Spanish","english":"English",







                       "french":"French","german":"German","portuguese":"Portuguese",







                       "japanese":"Japanese","hindi":"Hindi","korean":"Korean",







                       "chinese":"Chinese","italian":"Italian","russian":"Russian",







                       "thai":"Thai","indonesian":"Indonesian","arabic":"Arabic"}







                args.language=next((name for key,name in known.items() if guess.startswith(key)),"English")







            if getattr(args,"region","auto")=="auto":







                if args.language == "Vietnamese":







                    args.region = "VN"







                elif details.get("region"):







                    cand_reg=str(details["region"]).upper().strip()







                    if cand_reg in REGIONS:







                        args.region=cand_reg







            user_explicit_minutes = getattr(args, "_minutes_explicit", False) or ("--minutes" in sys.argv)
            if details.get("duration_minutes") and not user_explicit_minutes:







                try:







                    dur=float(details["duration_minutes"])







                    if 0.5<=dur<=60.0:







                        args.minutes=round(dur,1)







                except Exception:pass







            if original_genre=="auto" and str(details.get("genre")) in GENRES:







                args.genre=resolve_genre("auto",details.get("genre"))







                args.visual_style=resolve_style(original_visual_style,args.genre)







            if original_voice=="auto":







                from studio_voices import VOICES







                sug=str(details.get("suggested_voice","")).strip()







                if sug in VOICES:







                    args.voice_name=sug







                else:







                    args.voice_name=voice_for(args.language,args.genre,args.region,original_voice)







            elif original_language=="Auto":







                args.voice_name=voice_for(args.language,args.genre,args.region,original_voice)















            char_info = details.get("character") or {}







            char_name = char_info.get("character_name", "Nhân vật chính")







            char_app = char_info.get("appearance_lock", "")







            char_att = char_info.get("wardrobe_lock", "")







            if args.visual_style == "hand_color":







                art_style = "Vibrant hand-drawn colored sketch and marker watercolor illustration on clean paper with expressive colorful artistic rendering."







            elif args.visual_style == "colored_marker":







                art_style = "Vibrant colored whiteboard marker illustration in the signature style of After Skool, hand-drawn with multicolored chisel-tip marker pens on clean white whiteboard."







            elif args.visual_style == "whiteboard":







                art_style = "Crisp black marker line art drawing on clean white whiteboard."







            elif args.visual_style == "color_animation":







                art_style = "Vibrant stylized 3D/2D animation movie aesthetic with rich colors."







            elif args.visual_style == "color_cinematic":







                art_style = char_info.get("art_style") or details.get("visual_style") or "Photorealistic cinematic 16:9 widescreen film."







            else:







                art_style = char_info.get("art_style", details.get("visual_style", args.visual_style))







            char_clone_prompt = char_info.get("clone_prompt", "")







            premise = char_info.get("story_premise", details.get("title", prompt))















            prompt = (







                f"[CLONE CHÍNH XÁC NHÂN VẬT TỪ VIDEO GỐC]\n"







                f"• Nhân vật chính (Khóa 100%): {char_name}\n"







                f"• Ngoại hình: {char_app}\n"







                f"• Trang phục: {char_att}\n"







                f"• Bút pháp: {art_style}\n"







                f"• Quy tắc bất biến: {char_info.get('immutable_rules', 'Giữ nguyên diện mạo trong toàn bộ phân cảnh')}\n"







                f"• Clone prompt: {char_clone_prompt}\n"







                f"• Cốt truyện tham chiếu: {premise}\n"







                f"• Ghi chú người dùng: {prompt}"







            )







        else:







            prompt="Original offline sample inspired by "+url+". "+prompt







    series_dir=PRODUCTIONS/slug(args.series)







    episode_dir=series_dir/f"episode_{args.episode:03d}"







    if args.mode=="live" and args.image_provider=="mcp_v2":







        from studio_image_budget import required_images, inspect_budget, cached_plan_scene_count







        scripted = parse_locked_screenplay(prompt, scene_seconds=getattr(args, "scene_seconds", 7)) if args.input_mode=="script" else None







        count=cached_plan_scene_count(episode_dir/"plan.json",minutes=args.minutes,







            scene_seconds=args.scene_seconds,input_mode=args.input_mode)







        if count is None:







            try:







                count=required_images(args.minutes,args.scene_seconds,scripted)







            except Exception as exc:







                print(f"[IMAGE_BUDGET] Fallback count due to: {exc}", flush=True)







                count = max(1, math.ceil(args.minutes * 60 / max(4, args.scene_seconds)))







        budget=inspect_budget(count,args.mcp_max_images,args.mcp_visual_policy)







        print("IMAGE_BUDGET_PREFLIGHT",budget,"saved_plan",







              (episode_dir/"plan.json").is_file(),flush=True)







    episode_dir.mkdir(parents=True,exist_ok=True)







    # Prevent silent reuse of an existing V2-TuanStor/Gemini image when switching providers.







    first_job=episode_dir/"scenes"/"scene_0001"/"job.json"







    if args.mode=="live" and first_job.is_file():







        prior=read_json(first_job)







        if getattr(args, "resume", False):







            # Resuming an existing episode: adopt prior voice, provider, and language to maintain continuity







            if prior.get("voice_name"):







                args.voice_name = prior["voice_name"]







            if prior.get("image_provider") and (not getattr(args, "image_provider", None) or getattr(args, "image_provider") in ("", "gemini")):
                args.image_provider = prior["image_provider"]







            if prior.get("language"):







                args.language = prior["language"]







            if prior.get("region"):







                args.region = prior["region"]







            if prior.get("genre"):







                args.genre = prior["genre"]







            if prior.get("visual_style"):







                args.visual_style = prior["visual_style"]







        else:







            old_provider=prior.get("image_provider","gemini")







            if old_provider!=args.image_provider:







                previous_assets=episode_dir/"scenes"/"scene_0001"







                if any((previous_assets/x).is_file() for x in ("image.png","final.mp4","result.json")):







                    raise RuntimeError("This episode contains assets from provider '"+old_provider+







                          "'. Choose a new episode number to switch image provider.")







            previous_voice=prior.get("voice_name","Kore")







            if previous_voice!=args.voice_name and (







                episode_dir/"scenes"/"scene_0001"/"audio.wav").is_file():







                raise RuntimeError(







                    "This episode contains audio from narrator voice '"+previous_voice+







                    "'. Choose a new episode number to switch voice without reusing existing speech.")







    plan=produce_plan(args,series_dir,episode_dir,prompt)







    scenes=plan["scenes"]







    if args.mode=="live" and args.image_provider=="mcp_v2":







        from studio_image_budget import inspect_budget







        # Exact persisted plan count always wins; never silently raise paid limit.







        decision=inspect_budget(len(scenes),args.mcp_max_images,args.mcp_visual_policy)







        print("IMAGE_BUDGET_VALIDATED",decision,flush=True)







    manifest_file=episode_dir/"manifest.json"







    report={"series":args.series,"episode":args.episode,"status":"RUNNING",







            "mode":args.mode,"total_scenes":len(scenes),"updated":stamp(),







            "completed":[],"failed":[],"target_minutes":args.minutes}







    write_json(manifest_file,report)







    if args.mode=="live" and args.image_provider=="flowkit":
        raise RuntimeError("FLOWKIT_REMOVED_SELECT_MCP_V2")
    elif args.mode=="live" and args.image_provider=="mcp_v2":
        from mcp_v2_batch import generate_episode_images







        try:







            generate_episode_images(scenes,plan["bible"],







                series=args.series,episode=args.episode,episode_dir=episode_dir,







                max_new_images=args.mcp_max_images,







                model_index=args.mcp_model_index,







                visual_policy=args.mcp_visual_policy)







        except Exception as e:







            report.update({"status":"BLOCKED_MCP_IMAGE","updated":stamp(),







                           "blocker_type":type(e).__name__})







            write_json(manifest_file,report)







            raise







    first_image=None







    style_image=None







    key=own_api_key() if args.mode=="live" else ""

    # CINEMATIC MONTAGE & SHOT BANK ENGINE
    # For single-character/statue genres (Stoic, Philosophy, etc.) with long scene lists:
    # Use curated Master Shot Bank & intelligent film montage mapping instead of 400+ random redundant generations
    # STRICT GENRE ISOLATION GUARD:
    # Shot Bank of Stoic marble statues is 100% EXCLUSIVE to Stoic / Philosophy genres.
    # It MUST NEVER touch Drama, Western, Whiteboard, Animation, or other genres!
    genre_norm = str(getattr(args, "genre", "") or "").lower().strip()
    series_norm = str(getattr(args, "series", "") or "").lower().strip()
    is_non_stoic = any(
        k in genre_norm
        for k in ("drama", "family_drama", "western", "ranch", "whiteboard", "colored_marker", "hand_color", "animation", "action", "horror", "documentary")
    )
    is_stoic = not is_non_stoic and (
        genre_norm in ("stoic", "stoicism", "stoi", "philosophy", "khắc kỷ", "khac_ky", "khac ky")
        or series_norm in ("stoic", "stoicism", "khắc kỷ", "khac_ky", "khac ky")
    )
    is_shot_bank_applicable = is_stoic and getattr(args, "image_provider", "") == "comfyui"
    if is_shot_bank_applicable and len(scenes) >= 15:
        try:
            from cinematic_shot_bank import ensure_shot_bank_and_montage
            print(f"[CINEMATIC_MONTAGE] Activating Dedicated Stoic Shot Bank & Montage Engine for {len(scenes)} scenes...", flush=True)
            ensure_shot_bank_and_montage(
                episode_dir=episode_dir,
                scenes=scenes,
                genre=genre_norm,
                image_provider=args.image_provider,
            )
        except Exception as sb_err:
            print(f"[CINEMATIC_MONTAGE_WARN] Shot bank setup warning: {sb_err}", flush=True)















    def task(i,reference):







        scene=scenes[i]







        num=i+1







        print(f"--- Processing Scene {num}/{len(scenes)} ---", flush=True)







        print(f"SCENE_START {num}/{len(scenes)}", flush=True)







        directory=episode_dir/"scenes"/f"scene_{num:04d}"







        directory.mkdir(parents=True,exist_ok=True)







        # TỰ ĐỘNG CHUYỂN ĐỔI HYBRID HOOK: Cảnh 1 (Hook mở đầu 25-30s) ở chế độ kể chuyện tự động dùng Video chuyển động

        scene_img_provider = args.image_provider

        is_auto_muse_hook = False

        is_hook_motion_video = False



        is_narrative_cinematic = any(g in (getattr(args, "genre", "") or "").lower() for g in ("drama", "western", "family_drama", "action", "mafia_thriller", "psychological_horror", "romance_melodrama", "history"))
        if (num == 1 and getattr(args, "mode", "live") == "live"):
            if scene_img_provider == "comfyui" and is_narrative_cinematic:
                is_hook_motion_video = True
                print(f"\n⚡ [AUTO_HOOK_VIDEO] 🎬 Cảnh 1 là Cold Open Hook (30s): Tự động dùng ComfyUI AnimateDiff SDXL tạo video chuyển động thật trên GPU nội bộ!", flush=True)
            elif (scene_img_provider != "muse_video"
                and getattr(args, "image_provider", "") != "flowkit"
                and scene_img_provider != "flowkit" and getattr(args, "motion_mode", "ken_burns") == "flow_video"):
                try:
                    import muse_accounts
                    ready_accs = muse_accounts.get_ready_accounts()
                    if ready_accs:
                        scene_img_provider = "muse_video"
                        is_auto_muse_hook = True
                        print(f"\n⚡ [AUTO_HOOK_VIDEO] 🎬 Cảnh 1 là Cold Open Hook (30s): Tự động dùng Muse AI tạo video chuyển động thật ({len(ready_accs)} tài khoản sẵn sàng)!", flush=True)
                    else:
                        is_hook_motion_video = True
                        print(f"\n⚡ [AUTO_HOOK_VIDEO] 🎬 Cảnh 1 là Cold Open Hook (30s): Không có tài khoản Muse, tự động kích hoạt Flow Video AI Motion (Omni Flash / Veo)!", flush=True)
                except Exception as e_hook:
                    is_hook_motion_video = True
                    print(f"[AUTO_HOOK_VIDEO_NOTE] Chuyển đổi Hook Cảnh 1 sang Flow Video AI Motion ({e_hook})", flush=True)







        fingerprint=hash_of({"scene":scene,"resolution":args.size,"language":args.language,







                "mode":args.mode,"voice_name":args.voice_name,"region":args.region,







                "genre":args.genre,"visual_style":args.visual_style,







                "camera_motion":getattr(args, "camera_motion", "auto"),







              "motion_mode":getattr(args, "motion_mode", "ken_burns"),







              "flow_video_model":getattr(args, "flow_video_model", "Omni 1.1 Flash"),







              "flow_video_duration":getattr(args, "flow_video_duration", 8),







                "atmospheric_overlay":getattr(args, "atmospheric_overlay", "auto"),







                "subtitle":not args.no_subtitles,"reference":reference,







                "subtitle_style":getattr(args, "subtitle_style", "karaoke_viral") if not args.no_subtitles else None,







                "subtitle_size":getattr(args, "subtitle_size", 0) if not args.no_subtitles else None,







                "image_provider":scene_img_provider,

             "is_auto_muse_hook": is_auto_muse_hook,

             "is_hook_motion_video": is_hook_motion_video,

             "fallback_image_provider": args.image_provider,







                "mcp_model_index":args.mcp_model_index if scene_img_provider=="mcp_v2" else None})







        resultfile=directory/"result.json"







        if resultfile.exists():







            try:







                result=read_json(resultfile)







                if result.get("input_hash")==fingerprint and (directory/"final.mp4").is_file() and qc_complete(directory/"final.mp4",width,height):







                    img_p = directory/"image.png"







                    print(f"SCENE_RESUMED {num}/{len(scenes)} (Dùng lại cảnh đã hoàn thành và khớp cấu hình)", flush=True)







                    return {"scene":num,"status":"RESUMED","qc":result.get("qc"),"image_path":str(img_p if img_p.is_file() else "")}







            except Exception:







                pass







        # If parameters changed (e.g. subtitle size or style), remove stale final.mp4 to ensure re-burn







        stale_final = directory / "final.mp4"







        if stale_final.is_file():







            try:







                stale_final.unlink()







            except Exception:







                pass







        actual_ratio = "9:16" if height > width else "16:9"
        job={"scene":scene,"scene_dir":str(directory),"mode":args.mode,
             "width":width,"height":height,"aspect_ratio":actual_ratio,"language":args.language,







             "voice_name":args.voice_name,"genre":args.genre,







             "speech_pacing":getattr(args, "speech_pacing", "slow"),







             "visual_style":args.visual_style,"region":args.region,







             "camera_motion":getattr(args, "camera_motion", "auto"),







             "motion_mode":getattr(args, "motion_mode", "ken_burns"),







             "flow_video_model":getattr(args, "flow_video_model", "Omni 1.1 Flash"),







             "flow_video_duration":getattr(args, "flow_video_duration", 8),







             "atmospheric_overlay":getattr(args, "atmospheric_overlay", "auto"),







             "scene_seconds":args.scene_seconds,"api_key":key,







             "subtitles":not args.no_subtitles,"bible":plan.get("bible", {}),







             "anchor_image":reference,"input_hash":fingerprint,







             "image_provider":scene_img_provider,

             "is_auto_muse_hook": is_auto_muse_hook,

             "is_hook_motion_video": is_hook_motion_video,

             "fallback_image_provider": args.image_provider,







             "mcp_model_index":args.mcp_model_index,







             "mcp_max_images":args.mcp_max_images,







             "subtitle_style":getattr(args, "subtitle_style", "karaoke_viral"),







             "subtitle_size":getattr(args, "subtitle_size", 0),







             "total_scenes": len(plan.get("scenes", [])),







             "series":args.series,"episode":args.episode}







        jobfile=directory/"job.json"







        # Never write secrets into any manifest or on-disk job.







        job["api_key"]=""







        write_json(jobfile,job)







        env=os.environ.copy()







        env["GEMINI_API_KEY"]=key







        env["PYTHONIOENCODING"]="utf-8"







        env["PYTHONUTF8"]="1"







        command=[sys.executable,str(HOME/"series_studio.py"),"scene","--job",str(jobfile)]







        last_error=""







        for attempt in range(1,4):







            try:







                p=subprocess.run(command,capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=args.scene_timeout,







                                 cwd=str(directory),env=env, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))







                (directory/"run.log").write_text(







                    ("ATTEMPT "+str(attempt)+"\n"+p.stdout+"\n"+p.stderr)[-30000:],







                    encoding="utf-8")







                if p.returncode==0 and qc_complete(directory/"final.mp4",width,height):







                    result=read_json(resultfile)







                    return {"scene":num,"status":"PASS","qc":result["qc"],







                            "image_path":str(directory/"image.png")}







                last_error=(p.stderr or p.stdout or "Scene video failed QC")[-500:]







            except Exception as e:







                last_error=str(e)[-500:]







            if any(x in last_error.lower() for x in (







                    "401","403","invalid api key","permission_denied",







                    "gemini request failed after bounded retries",







                    "gemini temporarily unavailable after bounded retries",







                    "429 quota_or_rate_limit",







                    "muse_",







                    "storyboard_image_remote_uncertain_no_resubmit",







                    "flow_mcp_call_failed",







                    "storyboard_image_partial_uncertain_no_resubmit",







                    "storyboard_image_budget_exhausted",







                    "existing queue work must not be altered",







                    "locked_script_dialogue_too_long")):







                break







            if attempt<3:







                time.sleep(3*attempt)







        return {"scene":num,"status":"FAILED","error":last_error}















    completed=[]







    failed=[]







    record_lock = threading.Lock()







    def record(outcome):







        with record_lock:







            if outcome["status"]=="FAILED":







                failed.append(outcome)







                print("FAIL",outcome["scene"],outcome.get("error",""),flush=True)







            else:







                completed.append(outcome)







                print("SCENE_PASS", outcome["scene"], json.dumps(outcome["qc"]), flush=True)







                print(outcome["status"],outcome["scene"],outcome["qc"]["duration_seconds"],flush=True)







            report.update({"completed":[x["scene"] for x in completed],"failed":failed,







                           "updated":stamp(),"status":"RUNNING"})







            write_json(manifest_file,report)















    # Style anchors MUST be isolated by story and genre, otherwise a new







    # cinematographic film can inherit a whiteboard frame from another film.







    style_anchor=(series_dir/"style_anchors"/







                 (args.genre+"_"+args.visual_style+"_"+







                  hash_of(prompt[:2400])[:16]+".png"))







    style_anchor.parent.mkdir(parents=True,exist_ok=True)







    # Freeze the visual anchor per episode for reliable restarts.







    episode_anchor=episode_dir/"anchor_used.json"







    if episode_anchor.exists():







        anchor_value=read_json(episode_anchor).get("path","")







    else:







        cand_anchor = plan.get("bible", {}).get("anchor_image", "")







        if cand_anchor and Path(cand_anchor).is_file():







            anchor_value = str(cand_anchor)







            if not style_anchor.exists():







                try:







                    shutil.copy2(cand_anchor, style_anchor)







                except Exception:







                    pass







        else:







            anchor_value=str(style_anchor) if style_anchor.exists() else ""







        write_json(episode_anchor,{"path":anchor_value,"created":stamp()})







    comfy_was_running = False







    if args.mode=="live" and args.image_provider=="comfyui":







        from comfyui_image_provider import is_ready as comfy_is_ready, ensure_server







        comfy_was_running = comfy_is_ready()







        if not comfy_was_running:







            try:







                from gpu_capabilities import detect_gpu







                gpu_name = detect_gpu().get("primary", {}).get("name", "GPU")







            except Exception:







                gpu_name = "GPU"







            print(f"[ComfyUI] Tự động bật ComfyUI trên {gpu_name} để tạo ảnh (khởi động AI có thể mất 15-30s)...", flush=True)







            if not ensure_server(timeout=180.0):







                raise RuntimeError("ComfyUI không thể khởi động trên cổng 8188. Vui lòng kiểm tra ComfyUI tại D:\\ComfyUI hoặc kiểm tra GPU VRAM.")







            else:







                print("[ComfyUI] ComfyUI đã sẵn sàng!", flush=True)















    try:







        first=task(0,anchor_value)







        record(first)







        if first["status"]!="FAILED":







            first_image=first["image_path"]







            if not style_anchor.exists() and Path(first_image).is_file():







                shutil.copy2(first_image,style_anchor)







            if args.workers==1:







                previous=first_image







                for i in range(1,len(scenes)):







                    outcome = task(i, anchor_value)







                    record(outcome)







                    if outcome["status"]=="FAILED":







                        break







                    # previous = outcome["image_path"]







            else:







                # All remaining scenes share the first stable style anchor.







                with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:







                    futures={pool.submit(task,i,first_image):i+1 for i in range(1,len(scenes))}







                    for future in concurrent.futures.as_completed(futures):







                        record(future.result())







        if failed or len(completed)!=len(scenes):







            report["status"]="INCOMPLETE"







            write_json(manifest_file,report)







            raise RuntimeError(f"Episode incomplete: {len(completed)}/{len(scenes)} scenes; resume with same command.")







        ordered=[episode_dir/"scenes"/f"scene_{i:04d}"/"final.mp4" for i in range(1,len(scenes)+1)]







        print(f"PHASE_CONCAT {len(scenes)}", flush=True)







        print("EPISODE_CONCAT_START", flush=True)







        final=episode_dir/"episode_final.mp4"







        raw_concat=episode_dir/"episode_raw_concat.mp4"







        qc_raw=concat_episode(ordered,raw_concat)







        apply_cinematic_cta_and_audio(raw_concat,final,width,height)







        qc=qc_clip(final) if final.is_file() else qc_raw







        ratio=qc["duration_seconds"]/(args.minutes*60)







        report.update({"status":"PASS" if 0.80<=ratio<=1.20 else "DURATION_REVIEW",







                       "qc":qc,"duration_ratio":round(ratio,3),"output":str(final),"updated":stamp()})







        write_json(manifest_file,report)







        print("EPISODE_RESULT",json.dumps({"status":report["status"],"path":str(final),







                    "scenes":len(scenes),"duration_seconds":qc["duration_seconds"],"target_minutes":args.minutes}))







        if report["status"]=="DURATION_REVIEW":







            print("WARNING: Actual episode duration differs from requested target; inspect narration and timing.")















        # Automatically extract YouTube Shorts (9:16) only if explicitly enabled







        if getattr(args, "with_shorts", False):







            try:







                from shorts_extractor import generate_episode_short







                print("[SHORTS] Dang tu dong trich xuat doan cao trao hay nhat de tao video YouTube Shorts (9:16)...", flush=True)







                short_res = generate_episode_short(episode_dir)







                if short_res.get("ok"):







                    print(f"[SHORTS] Da tao thanh cong video Shorts 9:16 ({short_res.get('duration_seconds')}s): {short_res.get('filename')}", flush=True)







            except Exception as shorts_err:







                print(f"[SHORTS] Canh bao tao video Shorts tu dong: {shorts_err}", flush=True)







        else:







            print("[SHORTS] Da tat hoan toan tao video Shorts de toi uu 100% toc do cho Video Dai.", flush=True)







            for old_s in (episode_dir / "episode_short.mp4", episode_dir / "youtube_shorts_pack.json", episode_dir / "youtube_shorts_pack.txt"):







                if old_s.is_file():







                    try:







                        old_s.unlink()







                    except Exception:







                        pass















        # Automatically generate complete vidIQ SEO publishing package and 50/50 Rule of Thirds thumbnail







        try:







            from seo_packager import generate_seo_package







            print("[SEO] Dang tao goi dang bai bam kich ban va mot thumbnail chinh...", flush=True)







            seo_data = generate_seo_package(







                episode_dir=episode_dir,







                series_name=args.series,







                episode_num=args.episode,







                language=args.language,







                genre=args.genre,







                include_shorts=getattr(args, "with_shorts", False),







                force_regenerate=True,







            )







            print(f"[SEO] Da tao goi dang bai YouTube cho '{args.series} - Tap {args.episode}'! Kiem tra noi bo: {seo_data.get('metadata_checks', {}).get('total_score', 'chua do')}/100", flush=True)







        except Exception as seo_err:







            print(f"[SEO] Canh bao tao bo SEO tu dong: {seo_err}", flush=True)















        # Automatically organize project into clean, ready-to-upload folders







        try:







            from project_organizer import organize_episode







            print("[PUBLISH] Đang tự động sắp xếp thư mục đăng bài chuẩn SEO (Video, Thumbnail, Nội dung)...", flush=True)







            org_res = organize_episode(episode_dir)







            if org_res.get("ok"):







                print(f"[PUBLISH] Đã sẵn sàng gói đăng bài tại: {org_res.get('details', {}).get('episode_publish_dir')}", flush=True)







        except Exception as org_err:







            print(f"[PUBLISH] Cảnh báo sắp xếp gói đăng bài: {org_err}", flush=True)















        # Automatically upload to YouTube in Unlisted mode

        if getattr(args, "auto_upload", False):

            try:

                from youtube_manager import auto_upload_episode

                print("[YOUTUBE] Đang kiểm tra và tự động đăng bài lên YouTube (chế độ Không công khai)...", flush=True)

                yt_res = auto_upload_episode(

                    episode_dir=episode_dir,

                    series_name=args.series,

                    language=args.language,

                    privacy_status="unlisted"

                )

                if yt_res.get("ok"):

                    print(f"[YOUTUBE] ĐÃ TỰ ĐỘNG ĐĂNG THÀNH CÔNG LÊN YOUTUBE!", flush=True)

                    print(f"   Link xem: {yt_res.get('video_url')}", flush=True)

                    print(f"   Trạng thái: Không công khai (Unlisted) - YouTube đang xử lý bản HD/4K!", flush=True)

                elif yt_res.get("skipped"):

                    print(f"[YOUTUBE] {yt_res.get('reason')}", flush=True)

                else:

                    print(f"[YOUTUBE] Cảnh báo tự động đăng: {yt_res.get('error')}", flush=True)

            except Exception as yt_err:

                print(f"[YOUTUBE] Cảnh báo lỗi tự động đăng: {yt_err}", flush=True)















        return 0







    finally:







        if args.mode=="live" and args.image_provider=="comfyui" and not comfy_was_running:







            from comfyui_image_provider import stop_server







            print("[ComfyUI] Hoàn tất quá trình tạo ảnh. Đang tự động tắt ComfyUI và giải phóng GPU...", flush=True)







            stop_server()







            print("[ComfyUI] Đã tắt ComfyUI thành công. GPU trở về trạng thái nghỉ (tiết kiệm điện).", flush=True)















def parser():







    p=argparse.ArgumentParser(description="Independent Storyboard AI Series Studio")







    sub=p.add_subparsers(dest="action",required=True)







    sub.add_parser("doctor")







    w=sub.add_parser("scene")







    w.add_argument("--job",required=True)







    r=sub.add_parser("run")







    r.add_argument("--series",default="My Storyboard Series")







    r.add_argument("--episode",type=int,default=1)







    r.add_argument("--prompt")







    r.add_argument("--prompt-file")







    r.add_argument("--minutes",type=float,default=30)







    r.add_argument("--scene-seconds",type=int,default=30)







    r.add_argument("--language",default="Vietnamese")







    r.add_argument("--input-mode",choices=["idea","link","script"],default="idea")







    r.add_argument("--reference-url",default="")







    r.add_argument("--link-clone-mode",choices=["exact_clone","creative_adaptation"],default="exact_clone")







    r.add_argument("--genre",choices=list(GENRES),default="auto")







    r.add_argument("--visual-style",choices=list(STYLES),default="auto")







    r.add_argument("--region",choices=list(REGIONS),default="auto")







    from studio_voices import VOICES,DEFAULT_VOICE







    r.add_argument("--voice-name",choices=list(VOICES)+["auto"],default=DEFAULT_VOICE)







    r.add_argument("--speech-pacing",choices=["slow","normal","fast"],default="slow")







    r.add_argument("--size",default="1280x720")
    r.add_argument("--aspect-ratio",choices=["16:9","9:16"],default="")







    r.add_argument("--workers",type=int,default=1)







    r.add_argument("--mode",choices=["offline","live"],default="live")







    r.add_argument("--model",default="gemini-3.8-flash")







    r.add_argument("--image-provider",choices=["gemini","v2_tuanstor","mcp_v2","comfyui","muse_video"],







                   default="mcp_v2")







    r.add_argument("--mcp-model-index",type=int,choices=[0,1,2],default=1)







    r.add_argument("--mcp-max-images",type=int,default=0,







                   help="Approved maximum NEW MCP images for this episode")







    r.add_argument("--mcp-project-url",default="",







                   help="Exact Flow project/tool selected and frozen before Gemini planning")







    r.add_argument("--mcp-visual-policy",choices=["unique","reuse"],default="unique",







                   help="unique = one original image per scene; reuse = share max approved key visuals")







    r.add_argument("--no-subtitles",action="store_true")







    r.add_argument("--subtitle-style",default="karaoke_viral",







                   choices=["karaoke_viral","yellow_black","yellow_box","white_box","white_stroke","cyan_black","green_black","none"],







                   help="Color and visual style preset for subtitles")







    r.add_argument("--subtitle-size",type=int,default=0,







                   help="Custom subtitle font size in pixels (0 for auto)")







    r.add_argument("--camera-motion",default="auto",







                   choices=["auto","zoom_in","zoom_out","pan_right","pan_left","tilt_up","orbit_drift","none"],







                   help="Cinematic camera motion preset for scene rendering")







    r.add_argument("--motion-mode",default="ken_burns",choices=["ken_burns","flow_video"],







                   help="Video motion engine: ken_burns (2.5D Camera) or flow_video (Google Flow AI Motion)")







    r.add_argument("--flow-video-model",default="Omni 1.1 Flash",







                   choices=["Omni 1.1 Flash","Veo 3.1 - Fast","Veo 3.1 - Quality","Veo 3.1 - Lite"],







                   help="Google Flow AI video model")







    r.add_argument("--flow-video-duration",type=int,default=8,choices=[4,6,8,10],







                   help="Flow video clip duration in seconds")







    r.add_argument("--atmospheric-overlay",default="auto",







                   choices=["auto","dust_particles","cinematic_smoke","falling_snow",







                            "cinematic_rain","fire_embers","vintage_film","sun_rays","none"],







                   help="Cinematic atmospheric particle overlay preset")







    r.add_argument("--scene-timeout",type=int,default=1800)







    r.add_argument("--resume",action="store_true",







                   help="Resume production from existing plan and completed scenes")







    r.add_argument("--with-shorts",action="store_true",default=False,







                   help="Enable automatic extraction of YouTube Shorts and Shorts SEO pack (default: False)")







    r.add_argument("--no-shorts",dest="with_shorts",action="store_false",







                   help="Disable automatic extraction of YouTube Shorts and Shorts SEO pack")







    r.add_argument("--clean-watermark",action="store_true",default=True,







                   help="Automatically inpaint and remove Gemini/Google Flow watermarks")







    r.add_argument("--no-clean-watermark",dest="clean_watermark",action="store_false",







                   help="Disable watermark removal")







    r.add_argument("--auto-upload",action="store_true",default=False,







                   help="Automatically upload completed episode to YouTube in Unlisted mode")







    r.add_argument("--no-auto-upload",dest="auto_upload",action="store_false",







                   help="Disable automatic YouTube upload")







    return p















if __name__=="__main__":







    args=parser().parse_args()







    try:







        if args.action=="doctor":







            doctor(args)







        elif args.action=="scene":







            sys.exit(render_one(args.job))







        else:







            sys.exit(run(args))







    except Exception as ex:







        print("STUDIO_ERROR:",str(ex),file=sys.stderr)







        sys.exit(1)



