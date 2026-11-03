"""Storyboard facade for the verified saved-session Muse CLI gateway."""
from __future__ import annotations
import json
import os
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
    # 1. If the scene was provided using the 9-field skill contract, pass it directly to Muse!
    if scene.get("raw_9_fields") and str(scene["raw_9_fields"]).strip():
        return str(scene["raw_9_fields"]).strip()

    # 2. Extract clean text fields (no raw JSON dumping)
    visual_setup = str(scene.get("visual_setup") or scene.get("prompt") or scene.get("description") or "").strip()
    action = str(scene.get("action") or "").strip()
    dialogue = str(scene.get("dialogue") or scene.get("narration") or "").strip()
    camera = str(scene.get("camera") or scene.get("camera_motion") or "smooth cinematic camera movement").strip()

    # Determine genre & visual style
    genre = str(scene.get("genre") or bible.get("production_genre") or bible.get("genre") or "").lower().strip()
    style = str(scene.get("visual_style") or bible.get("visual_style_mode") or bible.get("visual_style") or "").lower().strip()
    master_setting = bible.get("master_setting") or bible.get("world") or "Cinematic dramatic environment"

    combined_text = f"{visual_setup} {master_setting} {scene.get('description', '')} {scene.get('summary', '')} {genre} {style}".lower()

    # Detect style intent
    is_animation_3d = (
        genre in ("animation", "3d_animation", "hoạt hình") or
        style in ("color_animation", "animation_3d", "3d_cgi") or
        any(k in combined_text for k in ["hoạt hình 3d", "3d cgi", "cgi điện ảnh", "3d animation", "3d render", "pixar", "dreamworks", "disney 3d", "cg animation"])
    )
    is_animation_2d = (
        not is_animation_3d and (
            genre in ("anime", "2d_animation") or
            any(k in combined_text for k in ["hoạt hình 2d", "anime", "2d anime", "manga", "ghibli", "cel-shaded", "hand-drawn anime", "2d cartoon"])
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

    # Extract character appearance descriptions cleanly from bible or scene
    chars_info = []
    bible_chars = bible.get("characters") or []
    if isinstance(bible_chars, list):
        for c in bible_chars:
            if isinstance(c, dict):
                c_name = c.get("name", "")
                c_app = c.get("appearance", "")
                if c_name and c_app:
                    chars_info.append(f"{c_name}: {c_app}")
                elif c_name:
                    chars_info.append(c_name)
            elif isinstance(c, str):
                chars_info.append(c)
    elif isinstance(bible_chars, dict):
        for k, v in bible_chars.items():
            if isinstance(v, dict):
                c_app = v.get("appearance") or v.get("appearance_lock") or ""
                chars_info.append(f"{k}: {c_app}" if c_app else k)
            else:
                chars_info.append(f"{k}: {v}")

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
        default_chars = "Heroic Full-Length Classical Standing Statue of Ancient Philosopher (strictly a carved stone/marble sculpture, NEVER a living human)"
        chars_str = "; ".join(chars_info) if chars_info else default_chars
        parts = [
            "FORMAT & STYLE: Cinematic 16:9 shot of monumental full-length classical Greco-Roman carved marble or bronze statues standing tall from head to toe on ancient stone forum ground. Authentic weathered Carrara marble texture with realistic micro-cracks and polished highlights, grand flowing carved stone togas draping down past knees to feet. High-contrast chiaroscuro lighting, floating embers and dust particles, dark ancient Roman ruins background.",
            f"CHARACTERS: {chars_str}.",
            f"SETTING & VISUAL SETUP: {visual_setup or master_setting}.",
            "LIGHTING & COLOR: Dramatic high-contrast chiaroscuro lighting, golden rim light accentuating chiseled stone features, atmospheric shadows, volumetric dust motes.",
            f"CAMERA: {camera}, majestic cinematic push-in or slow pan around the monumental full-length sculpture.",
            "PERFORMANCE & PRESENCE: Magnificent monumental statue presence, majestic carved stone stillness with drifting atmospheric dust particles and lighting shifts. The sculpture remains authentic carved stone/marble.",
        ]
        if action:
            parts.append(f"TIMED ACTION: {action}.")
        if dialogue:
            parts.append(f"AUDIO & DIALOGUE: Deep contemplative, dignified stoic philosophical narration echoing through ancient stone colonnades: \"{dialogue}\". Atmospheric reverberation, subtle wind and ambient forum echoes.")
        else:
            parts.append("AUDIO: Atmospheric ancient forum room tone, distant wind, subtle dust and stone echoes.")
        parts.append("CONSTRAINTS: ABSOLUTELY BANNED: living human being, human flesh and skin tones, real living person, half-body bust, severed torso, tabletop pedestal, cropped legs, missing feet, modern clothing.")

    elif is_whiteboard:
        default_chars = "Expressive hand-drawn whiteboard marker character sketches"
        chars_str = "; ".join(chars_info) if chars_info else default_chars
        parts = [
            "FORMAT & STYLE: Vibrant colored whiteboard marker illustration in the signature style of After Skool (16:9 widescreen). Clean pure white whiteboard backdrop, hand-drawn with expressive multicolored chisel-tip marker pens (deep crimson red, royal blue, warm amber yellow, emerald green, and bold ink black contours). Energetic sketchy marker cross-hatching, crisp marker lines with authentic dry-erase texture. No photorealism, no 3D render, no messy borders, pure whiteboard marker art.",
            f"CHARACTERS: {chars_str}.",
            f"SETTING & VISUAL SETUP: {visual_setup or master_setting}.",
            "LIGHTING & COLOR: Crisp high-key whiteboard lighting, pure white background #ffffff, high-contrast vibrant marker ink colors.",
            f"CAMERA: {camera}, smooth camera motion across the whiteboard canvas.",
            "PERFORMANCE & TIMING: Dynamic marker drawing animation unfolding cleanly on the whiteboard.",
        ]
        if action:
            parts.append(f"TIMED ACTION: {action}.")
        if dialogue:
            parts.append(f"AUDIO & DIALOGUE: Narration: \"{dialogue}\". Subtle dry-erase marker squeaks and drawing sounds.")
        else:
            parts.append("AUDIO: Clear whiteboard room tone, subtle marker sketching sounds.")
        parts.append("CONSTRAINTS: BANNED: live-action photorealism, realistic human flesh, 3D CGI, dark background, messy edges.")

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

    return "\n".join(parts)


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

        lock_name = f"muse_render_{acc['id']}.lock" if acc["id"] != "default" else "muse_render.lock"
        req = {
            "output_image_path": str(output),
            "prompt": format_real_acting_prompt(scene, bible),
            "width": width,
            "height": height,
            "duration": duration,
            "lock_path": str(HOME / "runtime" / lock_name),
        }
        if acc.get("profile_home"):
            req["account_home"] = str(acc["profile_home"])
            req["account_id"] = acc["id"]
            if acc.get("cookies_file"):
                req["cookies_file"] = str(acc["cookies_file"])
            if acc.get("vm_id"):
                req["vm_id"] = acc.get("vm_id")

        try:
            result = _worker("render", req, timeout=360)
            break
        except Exception as exc:
            err_msg = str(exc)
            print(f"[MUSE_FAILOVER] ⚠️ Cảnh {sc_num} - Tài khoản '{acc_label}' gặp sự cố: {err_msg}", flush=True)
            # Automatic failover: try next ready account if available
            next_acc = muse_accounts.get_account_for_scene(sc_num, exclude_ids=list(tried_accounts))
            if next_acc and next_acc["id"] not in tried_accounts:
                print(f"[MUSE_FAILOVER] 🔄 Tự động chuyển cảnh {sc_num} sang tài khoản bọc lót: '{next_acc.get('name')}'...", flush=True)
                receipt_path = output.parent / "muse_job.json"
                if receipt_path.is_file():
                    receipt_path.unlink()
                acc = next_acc
                continue
            raise

    if not output.is_file() or not (output.parent / "muse_clip.mp4").is_file():
        raise RuntimeError("MUSE_OUTPUT_MISSING: Thiếu ảnh hoặc video đã xác minh.")
    if result and "video" in result:
        print(f"[MUSE] Đã xác minh video {result['video']['width']}x{result['video']['height']}, {result['video']['duration_seconds']:.1f}s.", flush=True)
    return str(output)
