"""One-batch Storyboard Studio MCP image pipeline.



Studio's private Flow MCP image backend is used. It manages one queue,

has durable verified receipts and never re-submits an uncertain job.

"""

from __future__ import annotations

import os,sys,uuid,re,shutil,json,hashlib

from pathlib import Path

from PIL import Image,ImageOps

from studio_image_budget import inspect_budget, select_keyframes, ImageBudgetError

from mcp_v2_images import preflight,PRODUCTION_ROOT,clean_id,StudioMcpImageError



def sanitize_statue_terms(text: str) -> str:

    if not text:

        return ""

    import re

    t = text

    # Clean video post-production editing artifacts
    t = re.sub(r'(?i)\\b(peripheral|subtle|vertical|edge)?\\s*(mirroring|mirrored|mirror seam|mirror effect|mirrored border effects?|kaleidoscope(\\s+edge\\s+blur)?|diptych|split[- ]screen|two statues|two men|twin statues|dual|double)\\b', '', t)
    t = re.sub(r'(?i)\\b(cinematic\\s+)?(16:9|9:16)\\s*(shot|composition|framing)?\\b', '', t)

    # Check if this is explicitly a close-up / portrait / medium shot

    is_closeup = bool(re.search(r'(?i)\b(close[- ]?up|portrait|face|medium[- ]?close[- ]?up|profile)\b', t))

    if is_closeup:

        t = re.sub(r'(?i)\b(half[- ]?body\s+)?busts?\b', 'heroic sculpted marble statue', t)

        t = re.sub(r'(?i)\btượng\s+bán\s+thân\b', 'tượng cẩm thạch uy nghi', t)

        t = re.sub(r'(?i)\b(on|upon)\s+(a\s+)?([a-z\s]+)?pedestal\b', 'with dramatic stormy atmosphere', t)

        t = re.sub(r'(?i)\b([a-z\s]+)?pedestals?\b', 'dramatic atmospheric backdrop', t)

        t = re.sub(r'\s{2,}', ' ', t).strip()

        return t



    # 1. Clean Vietnamese bust phrases

    t = re.sub(r'(?i)\btượng\s+bán\s+thân\b', 'tượng uy nghi sừng sững', t)

    t = re.sub(r'(?i)\btượng\s+nửa\s+người\b', 'tượng đứng uy nghi', t)



    # 2. Clean bust phrases

    t = re.sub(r'(?i)\b(sculpted\s+|carved\s+|weathered\s+|classical\s+)?(male\s+)?(statue\s+)?(half[- ]?body\s+)?bust(\s+and\s+torso)?(\s+of)?\b', 'heroic monumental classical statue of', t)

    t = re.sub(r'(?i)\b(stone|marble|bronze|sculpted|classical)\s+(half[- ]?body\s+)?bust\b', r'\1 colossal statue', t)

    t = re.sub(r'(?i)\b(half[- ]?body\s+)?busts?\b', 'heroic statue', t)

    t = re.sub(r'(?i)\bhalf[- ]?body(\s+statue|\s+sculpture)?\b', 'heroic monumental statue', t)

    t = re.sub(r'(?i)\btorso[- ]only(\s+statue|\s+sculpture)?\b', 'complete anatomical statue', t)

    t = re.sub(r'(?i)\bwaist[- ]up(\s+statue|\s+sculpture)?\b', 'heroic statue', t)



    # 3. Clean pedestal phrases

    t = re.sub(r'(?i)\b(on|upon)\s+(a\s+)?([a-z\s]+)?pedestal\b', 'against a dramatic stormy sky', t)

    t = re.sub(r'(?i)\b([a-z\s]+)?pedestals?\b', 'grand classical architectural base', t)



    # 4. Clean prepositions and duplicates

    t = re.sub(r'(?i)\bstatue\s+towering\s+monumental\s+classical\s+statue\b', 'towering monumental classical statue', t)

    t = re.sub(r'(?i)\bof\s+(with|in|at|against|beneath|under|facing|on|upon)\b', r'\1', t)

    t = re.sub(r'(?i)\bof\s*$', '', t)

    t = re.sub(r'(?i)\bof\s+of\b', 'of', t)

    t = re.sub(r'\s{2,}', ' ', t).strip()

    return t



def image_prompt(scene,bible):
    characters=[]
    has_clone = bool(bible.get("characters") and isinstance(bible["characters"][0], dict) and (bible["characters"][0].get("clone_prompt") or bible["characters"][0].get("appearance")))

    is_vert = bool(bible.get("is_vertical") or bible.get("aspect_ratio") == "9:16" or str(scene.get("aspect_ratio","")).strip() == "9:16")
    aspect_desc = "vertical 9:16 mobile portrait." if is_vert else "wide 16:9 landscape."
    ratio_tag = "9:16" if is_vert else "16:9"

    # Explicit prompt override if supplied
    explicit_prompt = str(scene.get("image_prompt", "")).strip()
    if explicit_prompt and len(explicit_prompt) >= 15:
        p = explicit_prompt
        if "16:9" not in p and "9:16" not in p:
            p = f"Cinematic {ratio_tag}, {p}"
        if "no text" not in p.lower() and "no watermark" not in p.lower():
            p = p.rstrip(". ") + ". No text overlays, no watermarks, photorealistic 8k."
        return p[:1000]

    # ACCURATE VIDEO CLONING MODE: 100% faithful replication of competitor reference video
    if has_clone:
        c = bible["characters"][0]
        clone_base = c.get("clone_prompt") or c.get("appearance", "")
        clean_clone = re.sub(r'(?i)\b(cinematic\s+)?(16:9|9:16)\s*(shot|composition|framing)?,?\s*', '', clone_base).strip(', ')
        rules = str(c.get("immutable_rules", "")).strip()
        scene_desc = str(scene.get("description", "")).strip()
        setup = str(scene.get("visual_setup", "")).strip()
        
        # Sanitize against any mirrored/split/kaleidoscope/dual/pedestal defects
        bad_words_pattern = r'(?i)\b(mirrored|symmetrical|mirror|kaleidoscope|dual|twin|two statues|two men|double|split|collage|diptych|pedestal|severed bust)\b'
        scene_desc = re.sub(bad_words_pattern, '', scene_desc).strip(', ')
        setup = re.sub(bad_words_pattern, '', setup).strip(', ')
        
        prompt_parts = [
            f"Cinematic {ratio_tag} photograph, {aspect_desc}",
            "Single solitary subject centered in frame, only one figure in entire image, never two figures, never twin statues, never mirrored, never a pedestal",
            clean_clone
        ]
        if scene_desc and scene_desc.lower() not in clean_clone.lower():
            prompt_parts.append(f"Scene: {scene_desc}")
        if setup and setup.lower() not in clean_clone.lower():
            prompt_parts.append(f"Framing: {setup}")
        if rules and rules.lower() not in clean_clone.lower():
            prompt_parts.append(f"Visual rules: {rules}")
            
        prompt_parts.append("Masterpiece, cinematic lighting, photorealistic 8k, ultra-detailed. Single continuous image filling entire canvas from top to bottom and edge to edge, single shot only, absolutely no split screen, no collage, no diptych, no dual panels, no white lines, no borders, no filmstrip, no perforated margins, no text overlays, no watermarks, no distorted faces, no pedestals.")
        full_prompt = ". ".join(p.rstrip(". ") for p in prompt_parts if p)
        return re.sub(r'\s{2,}', ' ', full_prompt).strip()[:1000]

    for row in bible.get("characters",[]):
        if isinstance(row,dict):
            parts = [str(row.get(k,"")).strip() for k in ("name","appearance","attire","personality") if row.get(k)]
            if row.get("clone_prompt"):
                parts.append(f"CLONE PROMPT: {row['clone_prompt']}")
            if row.get("immutable_rules"):
                parts.append(f"RULES: {row['immutable_rules']}")
            characters.append(" | ".join(parts))

    from studio_modes import image_instruction
    genre = str(bible.get("production_genre") or bible.get("genre") or "").strip().lower()
    style = bible.get("visual_style_mode","whiteboard")
    series_name = str(bible.get("series") or scene.get("series") or "").strip().lower()

    scene_desc_low = (str(scene.get("description", "")) + " " + str(scene.get("visual_setup", ""))).lower()

    is_stoic = (
        genre in ("stoic", "philosophy", "history")
        or "stoi" in series_name
        or any(kw in scene_desc_low for kw in ("statue", "sculpture", "monument", "tượng", "carrara", "marcus", "stoic", "philosopher", "demigod", "rome", "roman"))
    )

    def _stoic_enhance(txt: str) -> str:
        if not txt:
            return txt
        # 1. Strip any close-up, side profile, or severed head framing commands
        txt = re.sub(r'(?i)\b(a\s+)?close[- ]up,?\s*(side[- ])?profile\s*view\s*of\s*(a\s+)?', 'heroic medium shot torso composition of ', txt)
        txt = re.sub(r'(?i)\bdramatic\s+close[- ]up,?\s*(side[- ])?profile\s*(angle)?', 'heroic cinematic medium shot, athletic muscular torso framing', txt)
        txt = re.sub(r'(?i)\bclose[- ]up\s+of\s+(the\s+)?(marble\s+)?statue[^\,\.]*', 'cinematic medium shot of hyper-muscular classical Carrara marble statue with colossal broad shoulders, sculpted chest pecs, and 6-pack abs', txt)
        txt = re.sub(r'(?i)\bfocusing\s+on\s+the\s+statue\'?s\s+face\b', 'framing the imposing muscular chest, broad shoulders, and dignified bearded face', txt)
        txt = re.sub(r'(?i)\bclose[- ]up\s+of\s+the\s+statue\'?s\s+eyes\b', 'heroic medium shot showing dignified warrior face, massive broad shoulders, and sculpted pectoral chest', txt)
        txt = re.sub(r'(?i)\b(classical\s+)?(marble\s+)?busts?\b', 'hyper-muscular marble statue with sculpted pectoral chest, striated deltoids, and 6-pack abs', txt)
        txt = re.sub(r'(?i)\b(tượng\s+)?bán\s+thân\b', 'tượng cơ bắp vạm vỡ ngực nở vai rộng', txt)
        txt = re.sub(r'(?i)\bfull[- ]length\s+standing\s+(classical\s+)?(marble\s+)?statue\b', 'heroic medium torso shot of hyper-muscular Roman philosopher emperor statue with massive broad shoulders and sculpted pecs', txt)
        txt = re.sub(r'(?i)\bstanding\s+resolute\s+on\s+its\s+weathered\s+stone\s+pedestal\b', 'heroic athletic demigod physique in ancient Roman forum', txt)
        txt = re.sub(r'(?i)\bpedestals?\b', 'ancient marble colonnade', txt)
        txt = re.sub(r'(?i)\bchest[- ]up\s+(medium\s+)?(shot|view)\s+of\s+(a\s+)?(classical\s+)?(marble\s+)?statue\b', 'heroic medium shot of an unbroken classical statue with complete intact muscular arms', txt)
        txt = re.sub(r'(?i)\b(broken|ruined|headless|armless|damaged|fragmented|amputated)\s+(statue|sculpture|marble|torso|limbs?)\b', 'magnificent intact unbroken \\2', txt)
        txt = re.sub(r'(?i)\b(severed|broken|missing)\s+(arms?|hands?|limbs?)\b', 'fully sculpted unbroken arms', txt)

        # 2. Inject explicit hyper-muscular demigod physique attributes
        muscular_traits = (
            "hyper-muscular chiseled demigod physique, colossal broad shoulders, thick muscular neck, "
            "powerfully sculpted pectoral chest muscles, striated deltoids, vascular arms, 6-pack abs, "
            "both arms fully intact and unbroken, complete sculpted arms attached, "
            "royal crimson red toga draped over one shoulder leaving the bare muscular chest and muscular arm proudly displayed"
        )
        if "muscular" not in txt.lower() and "pectoral" not in txt.lower():
            txt = f"{muscular_traits}, {txt}"
        return txt

    if is_stoic:
        raw_desc = _stoic_enhance(str(scene.get("description", "")))
        raw_setup = _stoic_enhance(str(scene.get("visual_setup", "")))
        cleaned_chars = [_stoic_enhance(c) for c in characters]
    else:
        raw_desc = str(scene.get("description", ""))
        raw_setup = str(scene.get("visual_setup", ""))
        cleaned_chars = characters

    is_vert = bool(bible.get("is_vertical") or bible.get("aspect_ratio") == "9:16")
    aspect_desc = "vertical 9:16 mobile portrait." if is_vert else "wide 16:9 landscape."
    ratio_tag = "9:16" if is_vert else "16:9"

    # Explicit prompt override if supplied
    explicit_prompt = str(scene.get("image_prompt", "")).strip()
    if explicit_prompt and len(explicit_prompt) >= 15:
        p = explicit_prompt
        if is_stoic:
            p = _stoic_enhance(p)
        if "16:9" not in p and "9:16" not in p:
            p = f"Cinematic {ratio_tag}, {p}"
        if "no text" not in p.lower() and "no watermark" not in p.lower():
            p = p.rstrip(". ") + ". No text overlays, no watermarks, photorealistic 8k."
        return p[:1000]

    char_essence = ""
    if cleaned_chars:
        first_c = cleaned_chars[0].split("|")[0].strip()
        if first_c and first_c.lower() not in raw_desc.lower():
            char_essence = f" Featuring {first_c[:120]}."

    scene_core = raw_desc.strip()[:450]
    comp_core = (" " + raw_setup.strip()[:200]) if raw_setup and raw_setup.lower() not in scene_core.lower() else ""

    if is_stoic:
        anti_cutoff = (
            "Full head, face, muscular neck, massive broad shoulders, sculpted chest pecs, "
            "both arms fully intact and unbroken, complete muscular arms sculpted and attached, "
            "and athletic torso completely in frame, perfectly centered cinematic composition, "
            "not cropped, no severed head, no decapitation, no extreme close-up, "
            "never broken arms, no amputated limbs, no severed arms, no stump arms, no missing arms, "
            "completely unbroken intact sculpture, anatomically complete."
        )
        short_prompt = (
            f"Cinematic {ratio_tag} photograph, {aspect_desc} "
            f"{scene_core}. {anti_cutoff} "
            f"Art style: classical Carrara marble sculpture in grand ancient Roman ruins at golden twilight, dramatic chiaroscuro lighting. "
            "High quality, rich atmosphere, natural lighting, photorealistic 8k. "
            "Single continuous image filling entire canvas from edge to edge, single shot only, absolutely no split screen, no collage, no diptych, no dual panels, no borders, no filmstrip, no perforated margins, no text overlays, no watermarks, no distorted faces, no broken arms, no severed arms, no amputee, no missing limbs, no broken ruins."
        )
    else:
        style_snippet = str(bible.get("visual_style", "Cinematic")).strip()[:180]
        short_prompt = (
            f"Cinematic {ratio_tag} photograph, {aspect_desc} "
            f"{scene_core}{comp_core}.{char_essence} "
            f"Art style: {style_snippet}. "
            "High quality, rich atmosphere, natural lighting, photorealistic 8k. "
            "Single continuous image filling entire canvas from edge to edge, single shot only, absolutely no split screen, no collage, no diptych, no dual panels, no borders, no filmstrip, no perforated margins, no text overlays, no watermarks, no distorted faces, no broken arms, no severed arms, no amputee, no missing limbs, no broken ruins."
        )
    return re.sub(r'\s{2,}', ' ', short_prompt).strip()[:1000]



def import_receipt_image(receipt,target,idx=None,total=None):

    original=Path(str(receipt["path"]))

    if not original.is_file():

        raise StudioMcpImageError("Missing verified image in MCP receipt")

    with Image.open(original) as im:

        im.load()

        if im.width<256 or im.height<256:

            raise StudioMcpImageError("MCP image too small")

        rgb=im.convert("RGB")

        is_vert = im.height > im.width

        target_size = (864, 1536) if is_vert else (1536, 864)

        target_ratio = 9/16 if is_vert else 16/9

        if abs(rgb.width/rgb.height - target_ratio) > 0.01:

            rgb = ImageOps.pad(rgb, target_size, color="white", method=Image.Resampling.LANCZOS)

        dest=Path(target)

        dest.parent.mkdir(parents=True,exist_ok=True)

        temp=dest.with_name(dest.stem+"."+uuid.uuid4().hex+".png")

        rgb.save(temp,format="PNG")

        os.replace(temp,dest)

    try:

        from clean_watermark import remove_gemini_watermark

        remove_gemini_watermark(dest)

    except Exception as cw_err:

        print(f"[WATERMARK_CLEANER] Note: {cw_err}", flush=True)

    prefix = f"scene {idx}/{total} " if idx and total else ""

    print("MCP_IMAGE_IMPORTED",prefix+dest.name,"bytes",dest.stat().st_size,flush=True)



def _clear_completed_flow_queue(cdp_port=9550):

    node_dir = Path(__file__).resolve().parent / "studio_mcp" / "node"

    node_exe = node_dir / ("node.exe" if os.name == "nt" else "node")

    executable = str(node_exe) if node_exe.is_file() else (shutil.which("node") or "node")

    script = (

        "import('playwright-core').then(async ({chromium}) => {\n"

        "  try {\n"

        f"    const browser = await chromium.connectOverCDP('http://127.0.0.1:{cdp_port}');\n"

        "    for (const page of browser.contexts().flatMap(c => c.pages())) {\n"

        "      for (const frame of page.frames()) {\n"

        "        const cleared = await frame.evaluate(() => {\n"

        "          const b = window.__STORYBOARD_MCP__;\n"

        "          if (!b || b.isProcessing) return false;\n"

        "          const q = b.queue || [];\n"

        "          if (q.length > 0) {\n"

        "            if (b.capabilities && b.capabilities.clearQueue) {\n"

        "              b.capabilities.clearQueue();\n"

        "              return true;\n"

        "            }\n"

        "          }\n"

        "          return false;\n"

        "        }).catch(() => false);\n"

        "        if (cleared) { await page.waitForTimeout(400); break; }\n"

        "      }\n"

        "    }\n"

        "    await browser.close();\n"

        "  } catch (e) {}\n"

        "});\n"

    )

    try:

        from silent_subprocess import _get_silent_si_and_flags

        si, flags = _get_silent_si_and_flags()

        subprocess.run([executable, "-e", script], cwd=str(node_dir), startupinfo=si, creationflags=flags, timeout=8)

    except Exception:

        pass



def generate_episode_images(scenes,bible,*,series,episode,episode_dir,max_new_images,

                            model_index=1,backend_factory=None,visual_policy="unique"):

    if not scenes or len(scenes)>1000:

        raise StudioMcpImageError("Invalid scene batch length")

    try:

        budget=inspect_budget(len(scenes),max_new_images,visual_policy)

        anchor_indices,mapping=select_keyframes(len(scenes),budget["image_jobs"])

    except ImageBudgetError as exc:

        raise StudioMcpImageError(str(exc)) from exc

    from studio_flow_accounts import apply_worker_env

    account = apply_worker_env()

    klass,models=preflight()

    print("MCP_ACCOUNT_SELECTED",account["name"],flush=True)

    if model_index not in (0,1,2):

        raise StudioMcpImageError("Invalid image model")

    os.environ["STORYBOARD_MCP_APPROVED"]="1"

    os.environ["STORYBOARD_MCP_MAX_NEW_IMAGES"]=str(int(max_new_images))

    folder="storyboard_studio_mcp_"+clean_id(series)+"_ep"+str(int(episode)).zfill(3)

    kw={"enabled":True,"spending_approved":True,"max_new_images":int(max_new_images),

        "model":models[model_index],"fallback":False}

    specs=[]

    for idx in anchor_indices:

        scene=scenes[idx-1]

        specs.append({

            "scene_id":clean_id(series)[:55]+"_ep"+str(int(episode))+

                      "_scene_"+str(idx).zfill(4),

            "prompt":image_prompt(scene,bible),

            "aspect_ratio":"9:16" if bible.get("is_vertical") or bible.get("aspect_ratio") == "9:16" else "16:9"

        })

    # The exact image batch owns a durable budget. Resuming unchanged input

    # reuses the same receipts; a revised script cannot inherit old spent slots.

    revision=hashlib.sha256(json.dumps({"specs":specs,"model":models[model_index],

        "fallback":False},sort_keys=True,ensure_ascii=False).encode()).hexdigest()[:20]

    scope=PRODUCTION_ROOT/(folder+"_run_"+revision)

    backend=(backend_factory or klass)(scope,**kw)

    print("MCP_BATCH_PREPARED",len(specs),"scenes",len(scenes),"budget",max_new_images,

          "visual_policy",visual_policy,"model_index",model_index,flush=True)

    print("MCP_RENDERING_BATCH",len(specs),"account",account.get("name","MCP"),flush=True)

    # FlowKit Priority: Use FlowKit WebTool if alive, fallback to legacy MCP
    use_flowkit = False
    try:
        from studio import flowkit_client
        if flowkit_client.is_flowkit_alive() or flowkit_client.ensure_flowkit_running(max_wait_seconds=2):
            use_flowkit = True
    except Exception:
        pass

    if use_flowkit:
        print(f"[FLOWKIT_BATCH] Rendering {len(specs)} scenes using FlowKit WebTool...", flush=True)
        for idx, spec in zip(anchor_indices, specs):
            target = Path(episode_dir) / "scenes" / f"scene_{idx:04d}" / "image.png"
            flowkit_client.generate_image(
                prompt=spec["prompt"],
                output_path=target,
                aspect_ratio=spec.get("aspect_ratio", "16:9"),
                scene_num=idx
            )
            print(f"[FLOWKIT_SCENE_DONE] scene {idx}/{len(scenes)} saved", flush=True)
    else:
        _clear_completed_flow_queue(account.get("cdp_port", 9550))
        backend.preflight()
        receipts = backend.render_one_queue(specs)
        if len(receipts) != len(specs):
            raise StudioMcpImageError("MCP batch incomplete: no local render started")
        for idx, spec in zip(anchor_indices, specs):
            if spec["scene_id"] not in receipts:
                raise StudioMcpImageError("Missing MCP image receipt for scene " + str(idx))
            target = Path(episode_dir) / "scenes" / f"scene_{idx:04d}" / "image.png"
            import_receipt_image(receipts[spec["scene_id"]], target, idx, len(scenes))

    # Reuse images ONLY when the operator selected that cheaper mode before

    # pressing Produce. No unapproved remote image generations are added.

    if visual_policy=="reuse" and len(anchor_indices)<len(scenes):

        for scene_no in range(1,len(scenes)+1):

            anchor=int(mapping[str(scene_no)])

            if scene_no==anchor:

                continue

            source=Path(episode_dir)/"scenes"/f"scene_{anchor:04d}"/"image.png"

            target=Path(episode_dir)/"scenes"/f"scene_{scene_no:04d}"/"image.png"

            if not source.is_file() or source.stat().st_size<1024:

                raise StudioMcpImageError("Missing key visual for scene "+str(scene_no))

            target.parent.mkdir(parents=True,exist_ok=True)

            tmp=target.with_name("image."+uuid.uuid4().hex+".png")

            try:

                shutil.copy2(source,tmp)

                os.replace(tmp,target)

            finally:

                tmp.unlink(missing_ok=True)

        print("MCP_VISUALS_REUSED",len(scenes)-len(specs),"scene images",flush=True)

    for scene_no in range(1,len(scenes)+1):

        asset=Path(episode_dir)/"scenes"/f"scene_{scene_no:04d}"/"image.png"

        if not asset.is_file() or asset.stat().st_size<1024:

            raise StudioMcpImageError("Image mapping incomplete at scene "+str(scene_no))

    mapping_file=Path(episode_dir)/"visual_mapping.json"

    temp=mapping_file.with_name("visual_mapping."+uuid.uuid4().hex+".json")

    temp.write_text(json.dumps({"policy":visual_policy,"scene_count":len(scenes),

        "approved_max_new_images":int(max_new_images),"remote_jobs":len(specs),

        "anchor_scenes":anchor_indices,"scene_to_anchor":mapping},ensure_ascii=False,indent=2),encoding="utf-8")

    os.replace(temp,mapping_file)

    print("MCP_BATCH_ALL_IMAGES_PASS",len(scenes),"remote_jobs",len(specs),flush=True)

    return len(scenes)

