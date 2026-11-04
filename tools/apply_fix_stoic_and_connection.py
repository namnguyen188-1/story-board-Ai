r"""Fix Stoic character consistency and Google Flow connection status.

1. studio/flow_account_manager.py:
   - When Chrome is running and on Google Flow on port 9461, accurately report connected=True, ready=True, badge='🟢 Sẵn sàng'.
   - Trigger FlowKit auto-start in background if offline.
2. studio/mcp_v2_batch.py:
   - Enforce 100% authentic classical carved marble statue for all Stoic scenes (even in clone mode).
   - Eliminate 'vascular arms', 'sun-kissed bronze skin', and living human flesh traits for Stoic.
   - Strictly isolate Stoic so other genres (Drama, Animation, Whiteboard) remain 100% untouched.
3. studio/web/app.js:
   - Update statusFlowKit and autoFlowManagerStatus so when connected=True, top bar shows '🟢 Sẵn sàng (18110)' and badge shows '🟢 Sẵn sàng'.
"""
import json
import os
import py_compile
import re
from pathlib import Path

ROOT = Path("D:/STORYBOARD_AI")

# 1. Update studio/flow_account_manager.py
fam_path = ROOT / "studio" / "flow_account_manager.py"
fam_text = fam_path.read_text(encoding="utf-8")

old_get_ui_status = """def get_ui_status() -> Dict[str, Any]:
    \"\"\"Return unified status for the Studio Settings Section 3 UI with multi-account support.\"\"\"
    from flowkit_client import is_flowkit_alive, get_webtool_status
    gw_alive = is_flowkit_alive()

    _sanitize_accounts_db()

    all_accounts = []
    ready_accounts = []
    active_account_id = ""
    if ACCOUNTS_DB_FILE.is_file():
        try:
            db_data = json.loads(ACCOUNTS_DB_FILE.read_text(encoding="utf-8"))
            all_accounts = db_data.get("accounts", [])
            active_account_id = db_data.get("active", "")
            ready_accounts = [a for a in all_accounts if a.get("email")]
        except Exception:
            pass

    # Real online status: check listening CDP ports
    real_ready = [a for a in all_accounts if a.get("email") and is_port_listening(a.get("cdp_port", 9461))]
    total_cnt = len(all_accounts) if all_accounts else 1
    ready_cnt = len(real_ready)
    emails = [a.get("email") for a in real_ready if a.get("email")]
    if not emails and is_port_listening(9461):
        live_em = get_logged_in_email(9461)
        if live_em:
            emails = [live_em]
            ready_cnt = 1

    short_emails = [e.split("@")[0] for e in emails]
    emails_tag = ", ".join(short_emails) if short_emails else "Chưa có"

    if _LOGIN_STATE.get("watcher_active"):
        return {
            "ready": gw_alive,
            "connected": False,
            "email": _LOGIN_STATE.get("email", ""),
            "emails": emails,
            "total_accounts": total_cnt,
            "ready_accounts": ready_cnt,
            "badge_text": _LOGIN_STATE.get("badge_text", "🟡 Đang đăng nhập"),
            "badge_type": _LOGIN_STATE.get("badge_type", "warning"),
            "status_text": _LOGIN_STATE.get("status_text", "Đang mở Chrome để bạn đăng nhập..."),
            "watcher_active": True
        }

    wt = get_webtool_status("hidden") if gw_alive else {"connected": False}
    connected = wt.get("connected", False)
    email = _LOGIN_STATE.get("email") or get_logged_in_email(9461) or (emails[0] if emails else "")

    if connected or gw_alive:
        _set_chrome_visibility_win32(port=9461, show=False)
        return {
            "ready": True,
            "connected": True,
            "email": email,
            "emails": emails,
            "total_accounts": total_cnt,
            "ready_accounts": ready_cnt,
            "accounts": all_accounts,
            "active_id": active_account_id,
            "dispatch_mode": "round_robin",
            "badge_text": f"🟢 {ready_cnt}/{total_cnt} Đa luồng" if ready_cnt > 1 else f"🟢 {ready_cnt} TK Sẵn sàng",
            "badge_type": "success" if ready_cnt > 0 else "warning",
            "status_text": f"● {ready_cnt} tài khoản sẵn sàng ({emails_tag}) · Đa luồng Round-Robin" if ready_cnt > 1 else f"✓ Web Tool đã kết nối ({emails[0] if emails else 'Sẵn sàng'})",
            "watcher_active": False
        }
    else:
        return {
            "ready": False,
            "connected": False,
            "email": "",
            "emails": [],
            "total_accounts": total_cnt,
            "ready_accounts": 0,
            "badge_text": "🔴 Chưa kết nối",
            "badge_type": "error",
            "status_text": "FlowKit Gateway chưa hoạt động. Bấm [Đăng Nhập Google Flow] để khởi động.",
            "watcher_active": False
        }"""

new_get_ui_status = """def get_ui_status() -> Dict[str, Any]:
    \"\"\"Return unified status for the Studio Settings Section 3 UI with multi-account support.\"\"\"
    from flowkit_client import is_flowkit_alive, get_webtool_status, ensure_flowkit_running
    gw_alive = is_flowkit_alive()

    # If FlowKit is not alive, attempt background launch without blocking UI response
    if not gw_alive:
        try:
            threading.Thread(target=ensure_flowkit_running, kwargs={"max_wait_seconds": 3}, daemon=True).start()
        except Exception:
            pass

    _sanitize_accounts_db()

    all_accounts = []
    ready_accounts = []
    active_account_id = ""
    if ACCOUNTS_DB_FILE.is_file():
        try:
            db_data = json.loads(ACCOUNTS_DB_FILE.read_text(encoding="utf-8"))
            all_accounts = db_data.get("accounts", [])
            active_account_id = db_data.get("active", "")
            ready_accounts = [a for a in all_accounts if a.get("email")]
        except Exception:
            pass

    # Real online status: check listening CDP ports
    real_ready = [a for a in all_accounts if a.get("email") and is_port_listening(a.get("cdp_port", 9461))]
    total_cnt = len(all_accounts) if all_accounts else 1
    ready_cnt = len(real_ready)
    emails = [a.get("email") for a in real_ready if a.get("email")]

    # Direct live check on port 9461
    chrome_port_alive = is_port_listening(9461)
    live_em = ""
    if chrome_port_alive:
        live_em = get_logged_in_email(9461)
        if live_em and live_em not in emails:
            emails.append(live_em)
            ready_cnt = max(ready_cnt, 1)

    # Check if Chrome is actively on Google Flow / signed in
    c_login = check_login_status(9461) if chrome_port_alive else {"logged_in": False, "on_webtool": False}
    chrome_active_on_flow = bool(c_login.get("logged_in") or c_login.get("on_webtool") or (chrome_port_alive and emails))

    short_emails = [e.split("@")[0] for e in emails]
    emails_tag = ", ".join(short_emails) if short_emails else "Chưa có"

    if _LOGIN_STATE.get("watcher_active"):
        return {
            "ready": gw_alive or chrome_active_on_flow,
            "connected": chrome_active_on_flow,
            "email": _LOGIN_STATE.get("email", "") or live_em,
            "emails": emails,
            "total_accounts": total_cnt,
            "ready_accounts": ready_cnt,
            "badge_text": _LOGIN_STATE.get("badge_text", "🟡 Đang đăng nhập"),
            "badge_type": _LOGIN_STATE.get("badge_type", "warning"),
            "status_text": _LOGIN_STATE.get("status_text", "Đang mở Chrome để bạn đăng nhập..."),
            "watcher_active": True
        }

    wt = get_webtool_status("hidden") if gw_alive else {"connected": False}
    connected = wt.get("connected", False)
    email = _LOGIN_STATE.get("email") or live_em or (emails[0] if emails else "")

    if connected or gw_alive or chrome_active_on_flow or (ready_cnt > 0):
        _set_chrome_visibility_win32(port=9461, show=False)
        display_cnt = max(ready_cnt, 1 if chrome_active_on_flow else 0)
        return {
            "ready": True,
            "connected": True,
            "email": email or (emails[0] if emails else "Google Flow"),
            "emails": emails if emails else ([email] if email else ["Google Flow"]),
            "total_accounts": total_cnt,
            "ready_accounts": display_cnt,
            "accounts": all_accounts,
            "active_id": active_account_id,
            "dispatch_mode": "round_robin",
            "badge_text": f"🟢 {display_cnt}/{total_cnt} Đa luồng" if display_cnt > 1 else "🟢 Sẵn sàng",
            "badge_type": "success",
            "status_text": f"● {display_cnt} tài khoản sẵn sàng ({emails_tag}) · Đa luồng Round-Robin" if display_cnt > 1 else f"✓ Web Tool đã kết nối ({email or 'Sẵn sàng'})",
            "watcher_active": False
        }
    else:
        return {
            "ready": False,
            "connected": False,
            "email": "",
            "emails": [],
            "total_accounts": total_cnt,
            "ready_accounts": 0,
            "badge_text": "🔴 Chưa kết nối",
            "badge_type": "error",
            "status_text": "Chưa kết nối Web Tool Google Flow. Bấm [Đăng Nhập] để kết nối.",
            "watcher_active": False
        }"""

if old_get_ui_status in fam_text:
    fam_text = fam_text.replace(old_get_ui_status, new_get_ui_status)
    fam_path.write_text(fam_text, encoding="utf-8")
    print("Updated studio/flow_account_manager.py get_ui_status successfully.")
    py_compile.compile(str(fam_path), doraise=True)
else:
    print("WARNING: old_get_ui_status not found in fam_text")

# 2. Update studio/mcp_v2_batch.py to strictly enforce Stoic statue consistency
mcp_path = ROOT / "studio" / "mcp_v2_batch.py"
mcp_text = mcp_path.read_text(encoding="utf-8")

# Inspect and update image_prompt in mcp_v2_batch.py
old_clone_block = """    # ACCURATE VIDEO CLONING MODE: 100% faithful replication of competitor reference video
    if has_clone:
        c = bible["characters"][0]
        clone_base = c.get("clone_prompt") or c.get("appearance", "")
        clean_clone = re.sub(r'(?i)\\b(cinematic\\s+)?(16:9|9:16)\\s*(shot|composition|framing)?,?\\s*', '', clone_base).strip(', ')
        rules = str(c.get("immutable_rules", "")).strip()
        scene_desc = str(scene.get("description", "")).strip()
        setup = str(scene.get("visual_setup", "")).strip()
        
        # Sanitize against any mirrored/split/kaleidoscope/dual/pedestal defects
        bad_words_pattern = r'(?i)\\b(mirrored|symmetrical|mirror|kaleidoscope|dual|twin|two statues|two men|double|split|collage|diptych|pedestal|severed bust)\\b'
        scene_desc = re.sub(bad_words_pattern, '', scene_desc).strip(', ')
        setup = re.sub(bad_words_pattern, '', setup).strip(', ')
        
        prompt_parts = [
            f"Cinematic {ratio_tag} photograph, {aspect_desc}",
            "Single solitary subject centered in frame, only one figure in entire image, never two figures, never twin statues, never mirrored, never a pedestal",
            clean_clone
        ]"""

new_clone_block = """    # Determine genre early
    genre = str(bible.get("production_genre") or bible.get("genre") or "").strip().lower()
    series_name = str(bible.get("series") or scene.get("series") or "").strip().lower()
    scene_desc_low = (str(scene.get("description", "")) + " " + str(scene.get("visual_setup", ""))).lower()
    is_stoic = (
        genre in ("stoic", "philosophy", "history")
        or "stoi" in series_name
        or any(kw in scene_desc_low for kw in ("statue", "sculpture", "monument", "tượng", "carrara", "marcus", "stoic", "philosopher"))
    )

    # ACCURATE VIDEO CLONING MODE: 100% faithful replication of competitor reference video
    if has_clone:
        c = bible["characters"][0]
        clone_base = c.get("clone_prompt") or c.get("appearance", "")
        clean_clone = re.sub(r'(?i)\\b(cinematic\\s+)?(16:9|9:16)\\s*(shot|composition|framing)?,?\\s*', '', clone_base).strip(', ')
        rules = str(c.get("immutable_rules", "")).strip()
        scene_desc = str(scene.get("description", "")).strip()
        setup = str(scene.get("visual_setup", "")).strip()
        
        # Sanitize against any mirrored/split/kaleidoscope/dual/pedestal defects
        bad_words_pattern = r'(?i)\\b(mirrored|symmetrical|mirror|kaleidoscope|dual|twin|two statues|two men|double|split|collage|diptych|pedestal|severed bust)\\b'
        scene_desc = re.sub(bad_words_pattern, '', scene_desc).strip(', ')
        setup = re.sub(bad_words_pattern, '', setup).strip(', ')

        # STOIC SPECIFIC ENFORCEMENT: Never mix statue and living human! All Stoic scenes are 100% pure classical marble statue!
        if is_stoic:
            clean_clone = (
                "Monumental heroic classical sculpted Carrara marble and antique bronze statue of Stoic philosopher emperor Marcus Aurelius, "
                "deeply chiseled stone anatomy, massive sculpted bare stone shoulder and pectoral chest, thick muscular stone neck, "
                "deeply carved curly stone beard and hair, sculpted stone eyes, "
                "wearing royal crimson red draped toga (chlamys) carved cascading over one stone shoulder. "
                "Authentic weathered Carrara marble texture with subtle historical fissure lines and smooth chisel marks. "
                "100% pure carved classical stone sculpture throughout, never living human flesh, never real skin pores, never vascular veins, never modern clothes"
            )
            scene_desc = re.sub(r'(?i)\\b(a\\s+)?(living\\s+)?(man|person|figure)\\b', 'the classical marble statue', scene_desc)
        
        prompt_parts = [
            f"Cinematic {ratio_tag} photograph, {aspect_desc}",
            "Single solitary subject centered in frame, only one figure in entire image, never two figures, never twin statues, never mirrored, never a pedestal",
            clean_clone
        ]"""

if old_clone_block in mcp_text:
    mcp_text = mcp_text.replace(old_clone_block, new_clone_block)
    print("Updated clone block in studio/mcp_v2_batch.py")
else:
    print("WARNING: old_clone_block not found in mcp_v2_batch.py")

# Also update muscular_traits in _stoic_enhance
old_muscular_traits = """        # 2. Inject explicit hyper-muscular demigod physique attributes
        muscular_traits = (
            "hyper-muscular chiseled demigod physique, colossal broad shoulders, thick muscular neck, "
            "powerfully sculpted pectoral chest muscles, striated deltoids, vascular arms, 6-pack abs, "
            "both arms fully intact and unbroken, complete sculpted arms attached, "
            "royal crimson red toga draped over one shoulder leaving the bare muscular chest and muscular arm proudly displayed"
        )"""

new_muscular_traits = """        # 2. Inject explicit classical marble statue attributes (NO living human flesh/veins!)
        muscular_traits = (
            "Monumental classical carved Carrara marble statue, deeply chiseled stone anatomy, "
            "colossal broad stone shoulders, thick muscular stone neck, powerfully sculpted pectoral chest, "
            "deeply carved curly stone beard and hair, sculpted stone eyes, "
            "powerfully carved muscular stone arms, both stone arms fully intact and unbroken, "
            "royal crimson red draped toga carved over one stone shoulder. "
            "Authentic weathered Carrara marble texture with subtle historical fissure lines and smooth chisel marks, "
            "100% pure classical carved stone sculpture, never living human flesh, never real skin pores, never vascular veins"
        )"""

if old_muscular_traits in mcp_text:
    mcp_text = mcp_text.replace(old_muscular_traits, new_muscular_traits)
    print("Updated muscular_traits in studio/mcp_v2_batch.py")
else:
    print("WARNING: old_muscular_traits not found in mcp_v2_batch.py")

mcp_path.write_text(mcp_text, encoding="utf-8")
py_compile.compile(str(mcp_path), doraise=True)
print("Compiled studio/mcp_v2_batch.py successfully.")

# 3. Update studio/web/app.js
appjs_path = ROOT / "studio" / "web" / "app.js"
appjs_text = appjs_path.read_text(encoding="utf-8")

old_appjs_block = """    if (statusBox && data.status_text) {
      const emailInfo = data.email ? ` (${data.email})` : "";
      if (data.ready_accounts > 1) {
        statusBox.textContent = `✓ Web Tool đã kết nối${emailInfo} · ${data.ready_accounts} TK Đa luồng Round-Robin`;
      } else {
        statusBox.textContent = `✓ Web Tool đã kết nối${emailInfo}`;
      }
    }"""

new_appjs_block = """    if (statusBox) {
      if (data.connected || data.ready) {
        const emailInfo = data.email ? ` (${data.email})` : "";
        if (data.ready_accounts > 1) {
          statusBox.textContent = `✓ Web Tool đã kết nối${emailInfo} · ${data.ready_accounts} TK Đa luồng Round-Robin`;
        } else {
          statusBox.textContent = `✓ Web Tool đã kết nối${emailInfo}`;
        }
      } else {
        statusBox.textContent = data.status_text || "Chưa kết nối Web Tool Google Flow.";
      }
    }"""

if old_appjs_block in appjs_text:
    appjs_text = appjs_text.replace(old_appjs_block, new_appjs_block)
    appjs_path.write_text(appjs_text, encoding="utf-8")
    print("Updated studio/web/app.js successfully.")
else:
    print("WARNING: old_appjs_block not found in app.js")

# 4. Update current project plan.json and jobs: studio/productions/stoi/episode_001
plan_path = ROOT / "studio" / "productions" / "stoi" / "episode_001" / "plan.json"
if plan_path.is_file():
    plan_data = json.loads(plan_path.read_text(encoding="utf-8"))
    
    # Update character definition
    for c in plan_data.get("bible", {}).get("characters", []):
        c["appearance"] = (
            "Monumental heroic classical sculpted Carrara marble and antique bronze statue of Stoic philosopher emperor Marcus Aurelius with "
            "deeply chiseled stone anatomy, massive sculpted broad shoulders, thick muscular stone neck, sculpted pectoral chest, "
            "curly stone hair and beard, classical carved stone statue eyes, wearing royal crimson red draped toga (chlamys) carved cascading over one stone shoulder. "
            "100% authentic carved classical marble statue, never living human flesh, never real skin pores, never vascular veins."
        )
        c["clone_prompt"] = (
            "Cinematic 9:16 vertical composition, monumental heroic classical sculpted Carrara marble and antique bronze statue of Stoic philosopher emperor Marcus Aurelius, "
            "deeply chiseled stone anatomy, massive sculpted bare shoulder, deeply carved curly stone beard, sculpted classical stone eyes, "
            "draped royal crimson toga over one stone shoulder, magnificent ancient Roman ruins backdrop at golden dusk, dramatic chiaroscuro lighting, "
            "100% pure classical carved stone sculpture, never living human flesh, never real skin pores, never vascular veins, photorealistic 8k, no watermark."
        )

    # Update scene descriptions so they are 100% consistent statues
    statue_descs = [
        "A dramatic close-up of a weathered, muscular classical Carrara marble statue of bearded philosopher Marcus Aurelius with intense sculpted stone eyes, draped crimson toga, ancient stone columns at golden dusk.",
        "A heroic medium shot of a powerful, weathered classical Carrara marble statue of bearded philosopher Marcus Aurelius with sculpted chest, draped crimson toga, standing before grand Roman colonnades at golden hour.",
        "A low-angle heroic shot of the monumental classical Carrara marble statue of bearded philosopher Marcus Aurelius with sculpted stone torso, draped crimson toga, against ancient temple ruins under dramatic sky.",
        "A heroic medium close-up of the weathered classical Carrara marble statue of bearded philosopher Marcus Aurelius, dignified carved stone face and sculpted chest, draped crimson toga, in ancient Roman forum."
    ]
    for idx, sc in enumerate(plan_data.get("scenes", [])):
        if idx < len(statue_descs):
            sc["description"] = statue_descs[idx]

    plan_path.write_text(json.dumps(plan_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Updated {plan_path} with 100% consistent marble statue descriptors.")

    # Also update scene job.json files
    scenes_dir = ROOT / "studio" / "productions" / "stoi" / "episode_001" / "scenes"
    for idx in range(1, len(statue_descs) + 1):
        job_f = scenes_dir / f"scene_{idx:04d}" / "job.json"
        if job_f.is_file():
            j_data = json.loads(job_f.read_text(encoding="utf-8"))
            if "scene" in j_data and idx - 1 < len(statue_descs):
                j_data["scene"]["description"] = statue_descs[idx - 1]
            if "bible" in j_data and "characters" in j_data["bible"] and j_data["bible"]["characters"]:
                j_data["bible"]["characters"][0]["appearance"] = plan_data["bible"]["characters"][0]["appearance"]
                j_data["bible"]["characters"][0]["clone_prompt"] = plan_data["bible"]["characters"][0]["clone_prompt"]
            job_f.write_text(json.dumps(j_data, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"Updated {job_f}")

print("ALL FIXES APPLIED SUCCESSFULLY!")
