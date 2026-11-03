"""Storyboard facade for the verified saved-session Muse CLI gateway."""

from __future__ import annotations

import sys

if hasattr(sys.stdout, "reconfigure"):

    try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    except Exception: pass

if hasattr(sys.stderr, "reconfigure"):

    try: sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    except Exception: pass

import json

import os

import re

import signal

import subprocess

import tempfile

import time

from pathlib import Path

from typing import Any



HOME = Path(__file__).resolve().parent

CONFIG_FILE = HOME / "runtime" / "muse_provider.json"

WORKER = HOME / "muse_gateway_worker.py"

_LOGIN_MANAGER = None





def _login_manager():

    global _LOGIN_MANAGER

    if _LOGIN_MANAGER is None:

        from muse_login import LoginManager

        _LOGIN_MANAGER = LoginManager(HOME)

    return _LOGIN_MANAGER





def start_muse_login(account_id: str | None = None, account_name: str | None = None):

    if not get_muse_config()["configured"]:

        raise RuntimeError("MUSE_RUNTIME_MISSING: Chưa cài hoặc chưa bật bộ kết nối Muse trên máy này.")

    return _login_manager().start(account_id=account_id, account_name=account_name)





def finish_muse_login(login_id: str, account_id: str | None = None):

    return _login_manager().complete(login_id, _worker, account_id=account_id)





def muse_login_status(account_id: str | None = None):

    return _login_manager().status(account_id=account_id)





def verify_muse_header(header: str) -> dict[str, Any]:

    return _worker("verify-header", {"header": header}, timeout=45)





def get_muse_config() -> dict[str, Any]:

    bundled = HOME / "runtime" / "muse" / "python" / "python.exe"

    legacy = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "muse-cli-audit" / "venv" / "Scripts" / "python.exe"

    default = bundled if bundled.is_file() else legacy

    cfg = {"transport": "muse-cli", "python_executable": str(default), "enabled": True}

    if CONFIG_FILE.is_file():

        saved = json.loads(CONFIG_FILE.read_text(encoding="utf-8-sig"))

        if "enabled" in saved:

            cfg["enabled"] = saved["enabled"]

        saved_python = saved.get("python_executable")

        if saved_python and Path(saved_python).is_file():

            cfg["python_executable"] = saved_python

    cfg["configured"] = bool(cfg["enabled"] and Path(cfg["python_executable"]).is_file())

    return cfg





def save_muse_config(*, python_executable: str = "", enabled: bool = True) -> bool:

    cfg = get_muse_config()

    python = python_executable.strip() or cfg["python_executable"]

    if not Path(python).is_file():

        raise ValueError("MUSE_RUNTIME_MISSING: Chưa tìm thấy bộ kết nối Muse trên máy.")

    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)

    data = {"python_executable": python, "enabled": bool(enabled)}

    temp = CONFIG_FILE.with_suffix(".tmp")

    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    os.replace(temp, CONFIG_FILE)

    return True





def _stop_worker(process):

    """Stop only this worker and its descendants, including Windows venv launchers."""

    if os.name == "nt":

        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],

                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10,

                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))

    else:

        try:

            os.killpg(process.pid, signal.SIGKILL)

        except ProcessLookupError:

            pass

    try:

        process.communicate(timeout=5)

    except subprocess.TimeoutExpired:

        process.kill()

        for stream in (process.stdout, process.stderr):

            if stream:

                stream.close()





def _worker(action: str, request: dict | None = None, timeout: float = 60) -> dict:

    cfg = get_muse_config()

    if not cfg["configured"]:

        raise RuntimeError("MUSE_RUNTIME_MISSING: Chưa cài hoặc chưa bật bộ kết nối Muse trên máy này.")

    env = os.environ.copy()

    env.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8", MUSE_NO_UPDATE_CHECK="1")

    if request and request.get("account_home"):

        env["USERPROFILE"] = str(request["account_home"])

    request_path = None

    p = None

    command = [cfg["python_executable"], "-u", str(WORKER), action]

    try:

        if request is not None:

            with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as f:

                json.dump(request, f, ensure_ascii=False)

                request_path = Path(f.name)

            command += ["--request", str(request_path)]

        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,

                             text=True, encoding="utf-8", errors="replace", env=env,

                             start_new_session=os.name != "nt",

                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))

        stdout, _ = p.communicate(timeout=timeout)

        result = None

        for line in reversed(stdout.splitlines()):

            try:

                value = json.loads(line)

                if isinstance(value, dict) and "ok" in value:

                    result = value

                    break

            except ValueError:

                continue

        if result is None:

            raise RuntimeError("MUSE_WORKER_FAILED: Bộ kết nối chưa trả kết quả; job đã có mã sẽ được theo dõi khi chạy tiếp.")

        if not result.get("ok"):

            raise RuntimeError(str(result.get("error") or "MUSE_WORKER_FAILED"))

        return result

    except subprocess.TimeoutExpired as exc:

        if p is not None:

            _stop_worker(p)

        if action == "auth-export":

            raise RuntimeError("MUSE_LOGIN_CHECK_TIMEOUT: Kiểm tra đăng nhập quá thời gian. Giữ cửa sổ Muse mở rồi thử Kết nối lại.") from exc

        raise RuntimeError("MUSE_JOB_PENDING: Hết thời gian theo dõi. Bấm tiếp tục để kiểm tra job cũ, không tạo lại.") from exc

    finally:

        if request_path:

            request_path.unlink(missing_ok=True)





def test_muse_connection(account_id: str | None = None) -> dict[str, Any]:

    try:

        import muse_accounts

        target_id = account_id or muse_accounts.get_active_id()

        acc = muse_accounts.get_account(target_id) if target_id else None

        req = None

        if acc and acc.get("profile_home"):
            req = {"account_home": str(acc["profile_home"]), "account_id": target_id}



        try:

            return _worker("status", request=req, timeout=60)

        except Exception as first_exc:

            if account_id:

                raise

            # In multi-account setup, failover check to other ready accounts

            ready_accs = [a for a in muse_accounts.list_accounts() if a.get("ready") and a.get("id") != target_id]

            for backup_acc in ready_accs:

                b_info = muse_accounts.get_account(backup_acc["id"])

                if b_info and b_info.get("profile_home"):

                    b_req = {"account_home": str(b_info["profile_home"]), "account_id": b_info["id"]}

                    try:

                        res = _worker("status", request=b_req, timeout=30)

                        if res.get("ok"):

                            print(f"[MUSE_PREFLIGHT] Tài khoản chính '{target_id}' chập chờn mạng, tự động chuyển sang tài khoản sẵn sàng '{b_info['id']}'...", flush=True)

                            muse_accounts.select_account(b_info["id"])

                            return res

                    except Exception:

                        continue

            raise first_exc

    except Exception as exc:

        message = str(exc)

        return {"ok": False, "status": message.split(":", 1)[0], "message": message}





def format_real_acting_prompt(scene: dict[str, Any], bible: dict[str, Any]) -> str:

    try:

        from cinematic_engine.drama_auto_repair import sanitize_forbidden_words

    except Exception:

        def sanitize_forbidden_words(t): return t



    sc_num = scene.get("scene_number", scene.get("number", 0)) if isinstance(scene, dict) else 0



    # 1. If raw_9_fields is not present in scene dict, look up scene_prompts_9_fields.txt directly

    if not (scene.get("raw_9_fields") and str(scene["raw_9_fields"]).strip()):

        candidate_paths = []

        if scene.get("scene_dir"):

            sd = Path(scene["scene_dir"])

            candidate_paths.extend([sd.parent.parent / "scene_prompts_9_fields.txt", sd.parent / "scene_prompts_9_fields.txt"])

        if scene.get("episode_dir"):

            candidate_paths.append(Path(scene["episode_dir"]) / "scene_prompts_9_fields.txt")

        for cand in candidate_paths:

            if cand and cand.is_file():

                try:

                    c_text = cand.read_text(encoding="utf-8")

                    m = re.search(rf"(=+\s*SCENE_{sc_num:03d}\b.*?)(?=\n=+\s*SCENE_|\Z)", c_text, re.DOTALL)

                    if m:

                        matched = m.group(1).strip()

                        # Strip delimiter banner line so only 9 fields are passed

                        clean_prompt = re.sub(r"^=+\s*SCENE_\d+.*?\n+", "", matched).strip()

                        scene["raw_9_fields"] = clean_prompt or matched

                        break

                except Exception:

                    pass



    # Pass the complete 9-field skill contract directly to Muse

    if scene.get("raw_9_fields") and str(scene["raw_9_fields"]).strip():

        return sanitize_forbidden_words(str(scene["raw_9_fields"]).strip())



    # 2. Extract clean text fields (no raw JSON dumping)

    visual_setup = str(scene.get("visual_setup") or scene.get("prompt") or scene.get("description") or "").strip()

    action = str(scene.get("action") or "").strip()

    dialogue = str(scene.get("dialogue") or scene.get("narration") or "").strip()

    camera = str(scene.get("camera") or scene.get("camera_motion") or "smooth cinematic camera movement").strip()



    # Determine genre & visual style

    genre = str(scene.get("genre") or bible.get("production_genre") or bible.get("genre") or "").lower().strip()

    style = str(scene.get("visual_style") or bible.get("visual_style_mode") or bible.get("visual_style") or "").lower().strip()

    master_setting = bible.get("master_setting") or bible.get("world") or "Cinematic dramatic environment"

    prod_mode = str(scene.get("production_mode") or bible.get("production_mode") or "").lower().strip()



    combined_text = f"{visual_setup} {master_setting} {scene.get('description', '')} {scene.get('summary', '')} {genre} {style}".lower()



    is_cinematic_live_action = (

        prod_mode == "cinematic_drama" or

        genre in ("drama", "family_drama", "action", "mafia_thriller", "romance_melodrama", "western", "history", "documentary") or

        style in ("color_cinematic", "cinematic_drama", "live_action")

    )



    # Detect style intent

    if is_cinematic_live_action and genre not in ("animation", "anime") and style not in ("color_animation", "animation_3d"):

        is_animation_3d = False

        is_animation_2d = False

    else:

        is_animation_3d = (

            genre in ("animation", "3d_animation", "hoạt hình") or

            style in ("color_animation", "animation_3d", "3d_cgi") or

            (not is_cinematic_live_action and any(k in combined_text for k in ["hoạt hình 3d", "3d cgi", "cgi điện ảnh", "3d animation", "pixar", "dreamworks", "disney 3d"]))

        )

        is_animation_2d = (

            not is_animation_3d and (

                genre in ("anime", "2d_animation") or

                (not is_cinematic_live_action and any(k in combined_text for k in ["hoạt hình 2d", "anime", "2d anime", "manga", "ghibli", "cel-shaded", "hand-drawn anime", "2d cartoon"]))

            )

        )

    is_stoic = (

        genre == "stoic" or

        any(k in combined_text for k in ["classical statue", "marble statue", "tượng đá", "tượng cẩm thạch", "sculpture", "carrara marble", "greco-roman statue"])

    )

    is_whiteboard = (

        genre in ("whiteboard", "colored_marker") or

        style in ("whiteboard", "colored_marker") or

        any(k in combined_text for k in ["whiteboard", "bảng trắng", "marker drawing", "after skool"])

    )



    # Extract character appearance descriptions cleanly from bible, scene, or drama_plan.json

    chars_info = []

    chars_present = scene.get("characters_present") or []

    bible_chars = bible.get("characters") or bible.get("cast") or scene.get("cast") or {}



    # If bible_chars is empty, fallback to drama_plan.json in episode folder

    if not bible_chars:

        cand_plans = []

        if scene.get("scene_dir"):

            sd = Path(scene["scene_dir"])

            cand_plans.extend([sd.parent.parent / "drama_plan.json", sd.parent / "drama_plan.json"])

        if scene.get("episode_dir"):

            cand_plans.extend([Path(scene["episode_dir"]) / "drama_plan.json", Path(scene["episode_dir"]) / "plan.json"])

        for cp in cand_plans:

            if cp and cp.is_file():

                try:

                    d_obj = json.loads(cp.read_text(encoding="utf-8"))

                    bible_chars = d_obj.get("cast", {})

                    if bible_chars:

                        break

                except Exception:

                    pass



    # Check 00_ASSET_PACK/characters for Master Turnaround Model Sheet DNA

    asset_chars_dir = None

    if scene.get("scene_dir"):

        sd = Path(scene["scene_dir"])

        for parent_cand in [sd.parent.parent, sd.parent]:

            if (parent_cand / "00_ASSET_PACK" / "characters").is_dir():

                asset_chars_dir = parent_cand / "00_ASSET_PACK" / "characters"

                break

    if not asset_chars_dir and scene.get("episode_dir"):

        ep_cand = Path(scene["episode_dir"]) / "00_ASSET_PACK" / "characters"

        if ep_cand.is_dir():

            asset_chars_dir = ep_cand



    # If explicit character DNA was cached in scene, prioritize it directly

    if scene.get("character_dna"):

        chars_info.append(str(scene["character_dna"]))

    elif isinstance(bible_chars, dict) and bible_chars:

        # If characters_present is defined, only include those present in this scene

        target_names = chars_present if chars_present else list(bible_chars.keys())

        sc_num = scene.get("scene_number", scene.get("number", 1))

        for name in target_names:

            if str(name).lower() in ("narrator", "người dẫn chuyện", "dẫn chuyện"):

                continue

            prof = bible_chars.get(name, {})

            # Check turnaround sheet first

            t_json = None

            if asset_chars_dir:

                from cinematic_engine.drama_asset_manager import slugify_name

                c_file = asset_chars_dir / f"{slugify_name(name)}_turnaround.json"

                if c_file.is_file():

                    try:

                        t_json = json.loads(c_file.read_text(encoding="utf-8"))

                    except Exception:

                        t_json = None



            try:
                from studio.cinematic_engine.character_isolator import extract_single_character_description
            except ImportError:
                try:
                    from cinematic_engine.character_isolator import extract_single_character_description
                except ImportError:
                    def extract_single_character_description(txt, n): return txt

            if t_json:

                app = t_json.get("appearance_dna", "")

                att = t_json.get("attire", "")

                if att and "locked complete wardrobe" not in att.lower():

                    app = f"{app} Wardrobe: {att}".strip()

                app = extract_single_character_description(app, name)
                chars_info.append(f"{name}: {app}")

            elif isinstance(prof, dict):

                app = prof.get("appearance_lock") or prof.get("appearance") or prof.get("description") or ""
                app = extract_single_character_description(app, name)

                # Also resolve wardrobe_by_act if present

                w_act = prof.get("wardrobe_by_act") or {}

                if w_act and isinstance(w_act, dict):

                    act_cloth = w_act.get("act_1", "") if sc_num <= 24 else (w_act.get("act_2", "") if sc_num <= 150 else w_act.get("act_3", ""))

                    if act_cloth:

                        app = f"{app} {act_cloth}".strip()

                if app:

                    chars_info.append(f"{name}: {app}" if not app.startswith(f"{name}:") else app)

                else:

                    chars_info.append(f"{name}: Authentic living actor with distinct facial features, cinematic wardrobe and lighting.")

            elif isinstance(prof, str):

                chars_info.append(f"{name}: {prof}")

    elif isinstance(bible_chars, list):

        for c in bible_chars:

            if isinstance(c, dict):

                c_name = c.get("name", "")

                if chars_present and c_name not in chars_present:

                    continue

                c_app = c.get("appearance") or c.get("appearance_lock") or c.get("description") or ""

                if c_name and c_app:

                    chars_info.append(f"{c_name}: {c_app}")

                elif c_name:

                    chars_info.append(c_name)

            elif isinstance(c, str):

                if not chars_present or c in chars_present:

                    chars_info.append(c)



    # Build genre-specific parts

    if is_animation_3d:

        default_chars = "Stylized 3D animated characters with expressive animated design"

        chars_str = "; ".join(chars_info) if chars_info else default_chars

        parts = [

            "FORMAT & STYLE: Premium 3D CGI animated feature film aesthetic (Pixar, DreamWorks, Disney 3D animation quality). Stylized 3D character design, velvety subsurface scattering, vibrant stylized textures, rich cinematic volumetric lighting, pristine CGI digital render. ABSOLUTELY NO live-action real footage, NO real human actors, NO photographic live skin pores, NO live human flesh tones.",

            f"CHARACTERS: {chars_str}.",

            f"SETTING & VISUAL SETUP: {visual_setup or master_setting}.",

            "LIGHTING & COLOR: Rich stylized cinematic 3D lighting, vibrant color palette, soft volumetric rim lights, atmospheric depth of field, clear expressive lighting.",

            f"CAMERA: {camera}, dynamic animated camera framing, pristine optical bokeh.",

            "PERFORMANCE & ANIMATION: Expressive stylized 3D character animation, fluid cartoon physics and timing, natural animated gestures, lively eyebrow and eye expressions, accurate expressive lip-sync matching speech.",

        ]

        if action:

            parts.append(f"TIMED ACTION: {action}.")

        if dialogue:

            parts.append(f"AUDIO & DIALOGUE: Animated characters speak with expressive animated voice acting, lively cadence, and animated mouth movement: \"{dialogue}\". Vibrant sound effects and ambient animation atmosphere.")

        else:

            parts.append("AUDIO: Atmospheric animation room tone and subtle stylized sound effects.")

        parts.append("CONSTRAINTS: ABSOLUTELY NO live-action film footage, NO real human photograph, NO real human pores or skin blemishes, NO frozen robotic stares, NO mannequin faces, NO frame glitching.")



    elif is_animation_2d:

        default_chars = "Stylized 2D anime characters with expressive anime design"

        chars_str = "; ".join(chars_info) if chars_info else default_chars

        parts = [

            "FORMAT & STYLE: High-end 2D animated feature film / anime aesthetic (Kyoto Animation, Makoto Shinkai quality). Clean expressive line art, vibrant cel-shaded color palette, hand-drawn anime aesthetic, cinematic depth and atmospheric lighting. ABSOLUTELY NO live-action real human footage, NO live human skin pores.",

            f"CHARACTERS: {chars_str}.",

            f"SETTING & VISUAL SETUP: {visual_setup or master_setting}.",

            "LIGHTING & COLOR: Atmospheric anime lighting, rich watercolor-inspired backgrounds, soft glowing rim light, clean vibrant anime colors.",

            f"CAMERA: {camera}, cinematic anime camera moves.",

            "PERFORMANCE & ANIMATION: Dynamic 2D animation, fluid anime motion, expressive stylized facial expressions, natural animated mouth flaps matching dialogue.",

        ]

        if action:

            parts.append(f"TIMED ACTION: {action}.")

        if dialogue:

            parts.append(f"AUDIO & DIALOGUE: Anime characters speak with expressive emotional voice acting: \"{dialogue}\". Crisp anime sound design.")

        else:

            parts.append("AUDIO: Atmospheric anime room tone and ambient sound effects.")

        parts.append("CONSTRAINTS: ABSOLUTELY NO live-action footage, NO photographic real human flesh, NO uncannily realistic human pores, NO glitching.")



    elif is_stoic:

        default_chars = "Marcus Aurelius / Classical Roman Philosopher Emperor (hyper-muscular chiseled demigod warrior build, massive broad shoulders, thick muscular neck, sculpted chest pecs, striated deltoids, vascular arms, weathered bronze skin, piercing contemplative gaze, salt-and-pepper curly beard, royal crimson draped toga draped over one shoulder leaving muscular chest and arm bare)"

        chars_str = "; ".join(chars_info) if chars_info else default_chars

        parts = [

            "FORMAT & STYLE: Cinematic 16:9 historical epic film still. Masterful live-action Greco-Roman cinematography with natural skin pores, realistic wrinkles, expressive eye gaze, and lifelike presence. Grand illuminated ancient Roman forum, majestic marble colonnades, and distant Acropolis at twilight under a starry sky with glowing torches and floating golden embers.",

            f"CHARACTERS: {chars_str}.",

            f"SETTING & VISUAL SETUP: {visual_setup or master_setting}.",

            "LIGHTING & COLOR: Dramatic cinematic chiaroscuro, warm amber golden key light with deep sapphire teal fill, delicate volumetric rim light outlining actor's massive muscular shoulders, sculpted pecs, and curls. Vibrant imperial crimson red and warm ivory textile togas. Never pitch black.",

            f"CAMERA: {camera}, smooth motivated cinematic tracking shot, natural depth of field with soft bokeh background.",

            "PERFORMANCE & PRESENCE: Commanding imperial warrior-philosopher presence, imposing athletic posture, organic subtle breathing and expressive eye gaze, natural contemplative movement (slow deliberate walking, gesturing thoughtfully, gazing out over the city). Authentic live-action dramatic performance.",

        ]

        if action:

            parts.append(f"TIMED ACTION: {action}.")

        if dialogue:

            parts.append(f"AUDIO & DIALOGUE: Deep resonant, dignified stoic philosophical narration echoing through ancient colonnades: \"{dialogue}\". Rich vocal warmth, subtle wind and ambient forum echoes.")

        else:

            parts.append("AUDIO: Atmospheric ancient forum room tone, distant night breeze, subtle torch fire crackles.")

        parts.append("CONSTRAINTS: BANNED: scrawny, skinny, frail, weak, unmuscular, flat chest, lifeless stone statue, severed torso, blank white eyes, plastic CGI render, cartoon, modern clothing, ugly artifacts, watermark.")



    elif is_whiteboard:

        default_chars = "Expressive hand-drawn whiteboard marker character sketches"

        chars_str = "; ".join(chars_info) if chars_info else default_chars

        parts = [

            "FORMAT & STYLE: Vibrant colored whiteboard marker illustration in the signature style of After Skool (16:9 widescreen). Clean pure white whiteboard backdrop, hand-drawn with expressive multicolored chisel-tip marker pens (deep crimson red, royal blue, warm amber yellow, emerald green, and bold ink black contours). Energetic sketchy marker cross-hatching, crisp marker lines with authentic dry-erase texture. No photorealism, no 3D render, no messy borders, pure whiteboard marker art.",

            f"CHARACTERS: {chars_str}.",

            f"SETTING & VISUAL SETUP: {visual_setup or master_setting}.",

            "LIGHTING & COLOR: Crisp high-key whiteboard lighting, pure white background #ffffff, high-contrast vibrant marker ink colors.",

            f"CAMERA: {camera}, smooth camera motion across the whiteboard canvas.",

            "PERFORMANCE & TIMING: Dynamic marker drawing animation unfolding in perfect real-time synchrony with the spoken narration. The marker sketches each visual metaphor steadily as it is explained, pacing the visual reveal to match the speech tempo so the audience can comfortably absorb every idea.",

        ]

        if action:

            parts.append(f"TIMED ACTION: {action}.")

        if dialogue:

            parts.append(f"AUDIO & DIALOGUE: Narration: \"{dialogue}\". Subtle dry-erase marker squeaks and drawing sounds.")

        else:

            parts.append("AUDIO: Clear whiteboard room tone, subtle marker sketching sounds.")

        parts.append("CONSTRAINTS: BANNED: live-action photorealism, realistic human flesh, 3D CGI, dark background, messy edges, drawing rushing ahead of speech, premature drawing completion.")



    else:

        # Standard live-action drama / thriller / cinema

        chars_str = "; ".join(chars_info) if chars_info else "Authentic cinematic actors"

        parts = [

            "FORMAT & STYLE: 8k master cinema live-action film, hyper-realistic cinematic realism, photorealistic 35mm anamorphic lens, organic skin texture with natural pores, subtle imperfections, authentic optical depth of field. ABSOLUTELY NO plastic or waxy skin, NO uncanny mannequin dolls, NO artificial CGI smoothing.",

            f"CHARACTERS: {chars_str}.",

            f"SETTING & VISUAL SETUP: {visual_setup or master_setting}.",

            "LIGHTING & COLOR: Cinematic volumetric 3-point lighting, dramatic soft rim light carving actor silhouettes, warm amber key light with deep sapphire fill, crystal clear visibility with rich lifted shadow pedestal (deep midnight navy, never pitch black). BANNED: pitch black, total darkness, crushed obsidian shadows, dark void.",

            f"CAMERA: {camera}, motivated cinematic framing, pristine optical bokeh.",

            "PERFORMANCE & REAL ACTING: Kinetic trigger initiates action. Character experiences sudden emotional tension: subtle gaze shift and eye focus adjustment, slight jaw tightening and natural breathing pause before speaking, authentic physical weight and convincing momentum. NO frozen stares, NO stiff robotic mannequin posture.",

        ]

        if action:

            parts.append(f"TIMED ACTION: {action}.")

        if dialogue:

            parts.append(f"AUDIO & DIALOGUE: Actors speak their lines with visceral emotional conviction, natural cadence, and realistic lip movements: \"{dialogue}\". Atmospheric environmental audio and subtle ambient sound effects.")

        else:

            parts.append("AUDIO: Authentic cinematic room tone, atmospheric tension, and subtle character movement sounds.")

        parts.append("CONSTRAINTS: No frozen robotic stares, no uncanny mannequin wax faces, no rubbery limbs, no pitch-black frames, no frame glitching or morphing.")



    return sanitize_forbidden_words("\n".join(parts))





def make_scene_media(scene: dict[str, Any], bible: dict[str, Any], output_image_path: Path,

                     width: int = 1280, height: int = 720, duration: int = 8,

                     account_id: str | None = None) -> str:

    import muse_accounts

    output = Path(output_image_path).resolve()

    output.parent.mkdir(parents=True, exist_ok=True)

    sc_num = scene.get("scene_number", scene.get("number", 1)) if isinstance(scene, dict) else getattr(scene, "scene_number", getattr(scene, "number", 1))

    # Keep durable Muse receipts: never clear an accepted or failed job implicitly.

    # Explicit recovery requires a separate verified terminal-job decision.

    # Resolve target account (Round-robin by scene number or explicit account)

    if not account_id and isinstance(scene, dict):

        account_id = scene.get("account_id")

    if account_id:

        acc = muse_accounts.get_account(account_id)

    else:

        acc = muse_accounts.get_account_for_scene(sc_num)



    if not acc:

        acc = {"id": "default", "name": "Mặc định", "profile_home": None}



    tried_accounts: set[str] = set()

    result = None



    while acc and acc["id"] not in tried_accounts:

        tried_accounts.add(acc["id"])

        acc_label = acc.get("name") or acc["id"]

        print(f"[MUSE] 🎬 Cảnh {sc_num}: Tạo video chuyển động trực tiếp (Direct T2V) bằng tài khoản '{acc_label}'...", flush=True)



        # Ensure scene has scene_dir and raw_9_fields if not explicitly passed

        if isinstance(scene, dict):

            if not scene.get("scene_dir"):

                scene["scene_dir"] = str(output.parent)

        if isinstance(scene, dict) and not scene.get("raw_9_fields"):

            for cand in [output.parent.parent.parent / "scene_prompts_9_fields.txt", output.parent.parent / "scene_prompts_9_fields.txt"]:

                if cand.is_file():

                    try:

                        c_text = cand.read_text(encoding="utf-8")

                        m = re.search(rf"(=+\s*SCENE_{sc_num:03d}\b.*?)(?=\n=+\s*SCENE_|\Z)", c_text, re.DOTALL)

                        if m:

                            matched = m.group(1).strip()

                            clean_prompt = re.sub(r"^=+\s*SCENE_\d+.*?\n+", "", matched).strip()

                            scene["raw_9_fields"] = clean_prompt or matched

                            print(f"[MUSE] 🎯 Cảnh {sc_num}: Đã nạp prompt 9 trường từ {cand.name} (Khóa nhận diện DNA đầy đủ nhân vật chính và phụ)", flush=True)

                            break

                    except Exception:

                        pass



        ref_img = scene.get("reference_image")
        char_anchors = list(scene.get("character_anchors") or [])
        if not ref_img and scene.get("scene_dir"):
            try:
                from cinematic_engine.drama_asset_manager import get_scene_character_anchors, get_primary_character_anchor
                s_path = Path(scene["scene_dir"])
                ep_d = s_path.parent.parent if s_path.parent.name == "scenes" else s_path.parent
                chars_p = scene.get("characters_present") or []
                prim_c = scene.get("primary_focus_character")
                prim_anc = get_primary_character_anchor(ep_d, chars_p, prim_c)
                if prim_anc and prim_anc.is_file():
                    ref_img = str(prim_anc)
                all_anc = get_scene_character_anchors(ep_d, chars_p)
                char_anchors = [a["image_path"] for a in all_anc if a.get("image_path")]
            except Exception:
                pass

        lock_name = f"muse_render_{acc['id']}.lock" if acc["id"] != "default" else "muse_render.lock"

        req = {

            "output_image_path": str(output),

            "prompt": format_real_acting_prompt(scene, bible),

            "width": width,

            "height": height,

            "duration": duration,

            "lock_path": str(HOME / "runtime" / lock_name),
            "reference_image": ref_img,
            "character_anchors": char_anchors,

        }

        if acc.get("profile_home"):

            req["account_home"] = str(acc["profile_home"])

            req["account_id"] = acc["id"]

            if acc.get("cookies_file"):

                req["cookies_file"] = str(acc["cookies_file"])

            if acc.get("vm_id"):

                req["vm_id"] = acc.get("vm_id")



        try:

            result = _worker("render", req, timeout=720)

            break

        except Exception as exc:

            err_msg = str(exc)

            print(f"[MUSE_FAILOVER] ⚠️ Cảnh {sc_num} - Tài khoản '{acc_label}' gặp sự cố: {err_msg}", flush=True)

            # Remote job finished without the required video: changing accounts blindly

            # repeats the same failed content and wastes tokens. Stop for scene review.

            if "Job kết thúc nhưng chưa có video gắn đúng mã cảnh" in err_msg:

                # If only 1 account, stop for scene review; if multiple accounts, let backup try once

                avail_backups = muse_accounts.list_accounts() if hasattr(muse_accounts, "list_accounts") else []

                if len(avail_backups) <= 1:

                    raise RuntimeError("MUSE_SCENE_REVIEW_REQUIRED: Muse completed without a valid scene video; inspect scene input before retrying.") from exc

            if any(code in err_msg for code in ("MUSE_JOB_PENDING", "MUSE_WORKER_FAILED", "MUSE_SCENE_INPUT_CHANGED", "MUSE_AUTH_REQUIRED", "MUSE_INTEGRITY_CHECK_FAILED")):

                raise

            # Any durable receipt proves a scene submission may already have been sent.

            # Never auto-switch accounts and delete it, regardless of status.

            receipt_path = output.parent / "muse_job.json"

            if receipt_path.is_file():

                try:

                    r_data = json.loads(receipt_path.read_text(encoding="utf-8"))

                    if r_data.get("state") in ("accepted", "downloading", "complete"):

                        raise RuntimeError("MUSE_RECEIPT_PROTECTED: Job đã có biên nhận đang xử lý...") from exc

                    # When failed, archive receipt so failover account can take over cleanly

                    archive_path = output.parent / f"muse_job_failed_failover_{int(time.time())}.json"

                    os.replace(receipt_path, archive_path)

                except (OSError, ValueError):

                    pass

            next_acc = muse_accounts.get_account_for_scene(sc_num, exclude_ids=list(tried_accounts))

            if next_acc and next_acc["id"] not in tried_accounts:

                print(f"[MUSE_FAILOVER] 🔄 Tự động chuyển cảnh {sc_num} sang tài khoản bọc lót: '{next_acc.get('name')}'...", flush=True)

                acc = next_acc

                continue

            raise



    if not output.is_file() or not (output.parent / "muse_clip.mp4").is_file():

        raise RuntimeError("MUSE_OUTPUT_MISSING: Thiếu ảnh hoặc video đã xác minh.")

    if result and "video" in result:

        print(f"[MUSE] Đã xác minh video {result['video']['width']}x{result['video']['height']}, {result['video']['duration_seconds']:.1f}s.", flush=True)

        if acc and acc.get("id"):

            try:

                import muse_accounts

                rem = muse_accounts.decrement_account_token(acc["id"], count=1)

                print(f"[MUSE_TOKEN] Tài khoản '{acc.get('name')}' còn lại {rem} tokens.", flush=True)

            except Exception:

                pass

    return str(output)

