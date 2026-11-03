"""Cinematic Drama Planner - AI Screenwriter for Multi-Character Theatrical Productions.
Generates structured scenes containing character dialogue beats, camera directions,
BGM moods, and ambient SFX cues.
Supports long-form movies (10, 20, 30+ minutes) via intelligent multi-batch screenplay planning.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

from resilient_gemini import ResilientClient
from .drama_schema import EpisodeDramaPlan, SceneDrama, DialogueBeat, CharacterProfile
from .drama_voice_director import VoiceDirector
from .drama_skill9 import writing_rules


def extract_json_payload(text: str) -> dict:
    """Safely extracts JSON dictionary from LLM response text."""
    raw = str(text or "").strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE).strip()
    m = re.search(r"(\{.*\})", cleaned, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    try:
        return json.loads(cleaned)
    except Exception as e:
        raise RuntimeError(f"CINEMATIC_PLANNER_FAILED: AI did not return valid JSON screenplay: {e}")


def _ensure_language_consistency(
    scenes: list,
    target_lang_name: str,
    client: ResilientClient,
    model: str
) -> list:
    """Verifies that dialogue beats match target_lang_name, translating if necessary."""
    from series_studio import validate_scene_language
    needs_trans = False
    for sc in scenes:
        for b in sc.get("dialogue_beats", []):
            txt = b.get("text", "")
            if txt and not validate_scene_language(txt, target_lang_name):
                needs_trans = True
                break
        if needs_trans:
            break

    if needs_trans:
        print(f"[DRAMA_PLANNER] Phát hiện lời thoại sai ngôn ngữ mục tiêu ({target_lang_name})! Đang tự động dịch sang {target_lang_name} chuẩn xác...", flush=True)
        trans_prompt = (
            f"You are an expert dialogue screenwriter and translator.\n"
            f"Translate all 'text' and 'summary' fields of the following scenes into native, natural, dramatic {target_lang_name}.\n"
            f"CRITICAL: All spoken lines ('text') MUST be 100% in {target_lang_name}.\n"
            f"Return JSON only with key 'scenes' containing the translated scenes array.\n\n"
            f"Scenes to translate:\n{json.dumps(scenes, ensure_ascii=False)}"
        )
        try:
            t_resp = client.models.generate_content(model=model, contents=trans_prompt)
            t_text = t_resp.text if hasattr(t_resp, "text") else str(t_resp)
            t_json = extract_json_payload(t_text)
            if t_json.get("scenes"):
                print(f"[DRAMA_PLANNER] Đã dịch toàn bộ lời thoại sang {target_lang_name} thành công!", flush=True)
                return t_json["scenes"]
        except Exception as t_err:
            print(f"[DRAMA_PLANNER] Lỗi dịch lời thoại: {t_err}", flush=True)
    return scenes


def _generate_master_outline(
    prompt: str,
    series_name: str,
    episode_num: int,
    target_lang_name: str,
    genre: str,
    visual_style: str,
    scene_count: int,
    client: ResilientClient,
    model: str,
    part_dir: Optional[Path] = None
) -> dict:
    """Generates the Master Bible (cast, setting) and high-level scene outline covering all scene_count scenes."""
    master_file = (part_dir / "master_outline.json") if part_dir else None
    if master_file and master_file.exists():
        try:
            cached = json.loads(master_file.read_text(encoding="utf-8"))
            if cached.get("characters") and len(cached.get("outline", [])) >= min(scene_count, 6):
                print(f"[DRAMA_PLANNER] Đã nạp Master Outline & Cast có sẵn ({len(cached.get('outline', []))} cảnh nét)...", flush=True)
                return cached
        except Exception:
            pass

    print(f"[DRAMA_PLANNER] Đang khởi tạo Master Story Arc & Tuyển chọn dàn diễn viên ({scene_count} cảnh mục tiêu)...", flush=True)
    
    target_lang_upper = target_lang_name.upper()
    is_vi = any(k in target_lang_name.lower() for k in ("vi", "viet"))
    lang_mandate = f"- TARGET LANGUAGE: {target_lang_upper}\n- Title, logline, and scene summaries MUST be strictly in {target_lang_upper}!\n"
    if is_vi:
        lang_mandate += "- Tiếng Việt đời sống, sắc sảo, dằn vặt, sức nặng cảm xúc điện ảnh.\n"

    sys_instruction = f"""You are an elite Showrunner and Master Screenwriter for award-winning Television & Cinema Dramas.
We are creating a full-length Cinematic Drama episode of '{series_name}' (Episode {episode_num}).
Genre: {genre}
{writing_rules(genre, visual_style)}
Target Duration: {scene_count * 10 / 60:.1f} minutes ({scene_count} motion scenes, 10 seconds per scene).
Target Language: {target_lang_name}

MANDATE:
{lang_mandate}
- 'master_setting' and character 'appearance' must be written in English for AI video generator visual anchoring.
- OUTPUT actual locations and props registries with stable IDs; each scene references these exact IDs, never a new ID for the same room/prop. Preserve prop owner, hand, position and changes across adjacent scenes.
- HIGH-RETENTION DRAMATIC STRUCTURE (COLD OPEN HOOK & PACING):
  1. SCENE 1 MUST BE AN 'IN MEDIAS RES' COLD OPEN HOOK:
     Drop the audience directly into the highest-stakes moment, an unmasked betrayal, a dangerous confrontation, a discovery of forbidden evidence, or an imminent catastrophe.
     NEVER start with slow exposition, waking up, or walking into a room. The first 10-30 seconds must seize viewer attention immediately with an intense curiosity gap!
  2. CAMERA DYNAMICS & PATTERN INTERRUPTS:
     Mandate alternating camera shot types and perspectives across consecutive scenes (e.g., tight macro emotion close-up -> wide atmospheric establishing -> dynamic over-the-shoulder confrontation -> cinematic tracking) so the video never feels visually monotonous.
  3. CLIFFHANGER RESOLUTION:
     The final scene MUST end on an unresolved high-stakes cliffhanger (Zeigarnik open loop effect) that compels viewers to watch the next episode!
- CINEMATIC SEQUENCE BLOCK ARCHITECTURE (CHỐNG NHẢY BỐI CẢNH / LIỀN MẠCH TUYỆT ĐỐI):
  1. DO NOT change locations every 10 seconds! Teleporting characters every single shot destroys cinematic continuity.
  2. The episode must be structured into 5 to 10 major continuous DRAMATIC SEQUENCES.
  3. EACH DRAMATIC SEQUENCE must be anchored in ONE single location (setting) spanning 6 to 15 consecutive scenes (60 to 150 seconds).
  4. WITHIN a sequence, the physical room, time of day, lighting palette, and characters present must remain 100% STABLE and CONTINUOUS.
  5. What changes from cut to cut within a sequence is STRICTLY THE CAMERA PERSPECTIVE (shot coverage):
     - Cut 1: Wide establishing master shot
     - Cut 2: Medium two-shot establishing spatial relationship
     - Cut 3: Over-the-shoulder confrontation angle on Speaker A
     - Cut 4: Intense emotional close-up on Speaker B's eyes and expressions
     - Cut 5: Dynamic tracking cut moving with the character
     - Cut 6: Low-angle or high-angle dramatic reaction
  6. A change of setting ONLY happens when a dramatic sequence concludes and the story logically transitions to the next major story location.
- CINEMATOGRAPHY & LIGHTING RULES (ANTI-BLACK / HOLLYWOOD STANDARD):
  NEVER use words that produce pitch-black or unviewable frames ('pitch black', 'total darkness', 'crushing obsidian black', 'zero light', 'dark void', 'haunting gloom').
  For night, abyss, deep ocean, or dark interior scenes: ALWAYS mandate vibrant cinematic lighting: 'cinematic volumetric lighting', 'piercing electric cyan and deep sapphire god-rays', 'dramatic 3-point rim lighting carving creature/actor silhouette', 'luminous bioluminescent glow (electric cyan, amber, violet) casting bright reflections on skin and scales', 'crystal clear visibility with rich lifted shadow pedestal (deep midnight navy, never pitch black)', '8k master cinema shot'.
- ANATOMICAL FIDELITY & LIVING CREATURE REALISM:
  When characters include animals, marine life, or creatures (e.g. Sperm Whale, Giant Squid, Orca, Shark):
  MANDATORY: Anchor exact biological anatomy (e.g., Sperm Whale: massive blunt box-shaped rectangular head 1/3 body, flat vertical forehead, narrow underslung lower jaw hinged open with conical white teeth, dark charcoal wrinkled skin with white sucker scars, paddle flippers; never a generic fish).

TASK:
Create the Master Bible and a comprehensive scene-by-scene outline for ALL {scene_count} SCENES from Scene 1 to Scene {scene_count}.
1. 'title': Dramatic episode title in {target_lang_name}
2. 'logline': 1-sentence hook summarizing the climax in {target_lang_name}
3. 'master_setting': English physical description of primary environment, atmosphere, and lighting
4. 'characters': 3 to 6 distinct characters with rich dramatic tension:
   - name: Character Name
   - gender: 'male' or 'female'
   - role: 'protagonist', 'antagonist', or 'supporting'
   - personality: Deep inner drive, flaw, and psychology
   - appearance: HYPER-SPECIFIC PHYSICAL DNA LOCK in English:
     * Facial landmarks: exact age, skin tone with precise undertone (e.g. warm dark-cocoa with golden undertones), bone structure, and MANDATORY permanent facial marker (e.g. beauty mark mole 3mm above lip, faint eyebrow scar, dimples) to eliminate AI face-swapping across cuts.
     * Hair architecture: exact length, parting, styling (braided bun, blunt bob), framing strands.
     * Wardrobe locked per Act: NEVER use vague progression words ('transitioning', 'initially wears'). Explicitly define immutable wardrobe per Act.
     * ZERO BARE NAMES: Any supporting character (doctor, driver, enforcer, rival) who appears in any scene must be fully defined with appearance DNA here.
5. 'locations': Registry with STABLE location IDs shared by all scenes in one physical place. Each ID includes name, exact architecture layout, furniture, wall/door/window geometry and lighting.\n6. 'props': Registry with STABLE prop IDs, physical color/material/size and ownership/hand placement. No random renaming of the same prop.\n7. 'outline': Array of EXACTLY {scene_count} scene outlines covering the entire story arc from Scene 1 to Scene {scene_count}:
   MANDATORY: Group all {scene_count} scenes into continuous Sequence Blocks (6 to 15 consecutive scenes per setting). All scenes within the same block MUST have the exact same 'setting'.
   [
     {{
       "scene_number": 1,
       "sequence_name": "Sequence 1: Royal Banquet Accusation",
       "setting": "Royal Banquet Hall",
       "location_id": "royal_banquet_hall",
       "props_required": [],
       "camera_coverage": "wide_establishing_master",
       "characters_present": ["Char 1", "Char 2"],
       "primary_focus_character": "Char 1",
       "beat_summary": "Intense conflict / action in {target_lang_name}",
       "bgm_mood": "tense_investigation"
     }},
     {{
       "scene_number": 2,
       "sequence_name": "Sequence 1: Royal Banquet Accusation",
       "setting": "Royal Banquet Hall",
       "location_id": "royal_banquet_hall",
       "props_required": [],
       "camera_coverage": "over_the_shoulder_confrontation",
       "characters_present": ["Char 1", "Char 2"],
       "primary_focus_character": "Char 1",
       "beat_summary": "Ugomma recoils in shock as Obaza points accusing finger in {target_lang_name}",
       "bgm_mood": "tense_investigation"
     }},
     ...
     {{
       "scene_number": {scene_count},
       "sequence_name": "Sequence N: Chamber Climax",
       "setting": "Ugomma's Private Chamber",
       "camera_coverage": "tight_macro_reaction",
       "characters_present": ["Char 1", "Char 2"],
       "primary_focus_character": "Char 1",
       "beat_summary": "Climax and suspenseful cliffhanger in {target_lang_name}",
       "bgm_mood": "epic_tension"
     }}
   ]

CRITICAL: You MUST provide outline entries covering ALL {scene_count} scenes from Scene 1 to Scene {scene_count}!
Return strictly JSON only.
"""

    user_prompt = f"""SERIES: {series_name}
EPISODE: {episode_num}
GENRE: {genre}
TARGET LANGUAGE: {target_lang_name}
TARGET SCENE COUNT: {scene_count} scenes

STORY BRIEF / TRANSCRIPT / SOURCE MATERIAL:
{prompt}

Create the complete Master Bible and the {scene_count}-scene outline array now in JSON format.
"""

    resp = client.models.generate_content(model=model, contents=f"{sys_instruction}\n\n{user_prompt}")
    resp_text = resp.text if hasattr(resp, "text") else str(resp)
    master_data = extract_json_payload(resp_text)

    # Pad or expand outline if LLM provided fewer than scene_count entries
    outline = master_data.get("outline", [])
    chars = master_data.get("characters", [])
    char_names = [c.get("name") for c in chars if c.get("name")] or ["Nhân vật 1", "Nhân vật 2"]

    if len(outline) < scene_count:
        print(f"[DRAMA_PLANNER] AI lập {len(outline)} nét phân cảnh. Đang tự động điền nhịp diễn biến phủ trọn vẹn {scene_count} cảnh...", flush=True)
        last_item = outline[-1] if outline else {
            "setting": "Không gian chính",
            "characters_present": char_names[:2],
            "beat_summary": "Diễn biến kịch tính",
            "bgm_mood": "tense_investigation"
        }
        for idx in range(len(outline) + 1, scene_count + 1):
            outline.append({
                "scene_number": idx,
                "setting": last_item.get("setting") or "Không gian chính",
                "characters_present": last_item.get("characters_present") or char_names[:2],
                "beat_summary": f"Diễn biến cao trào phân cảnh {idx} tiếp nối cốt truyện",
                "bgm_mood": "epic_tension" if idx >= scene_count - 2 else "tense_investigation"
            })
        master_data["outline"] = outline

    if master_file:
        try:
            master_file.write_text(json.dumps(master_data, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    return master_data


def _generate_batch_scenes(
    batch_idx: int,
    total_batches: int,
    start_sc: int,
    end_sc: int,
    characters_def: list,
    master_setting: str,
    outline_slice: list,
    prev_summary: str,
    prev_dialogue: str,
    series_name: str,
    genre: str,
    visual_style: str,
    target_lang_name: str,
    client: ResilientClient,
    model: str,
    part_dir: Optional[Path] = None,
    total_scene_count: int = 6
) -> list:
    """Generates detailed screenplay scenes for a specific batch with retry handling."""
    batch_file = (part_dir / f"part_{batch_idx:03d}.json") if part_dir else None
    if batch_file and batch_file.exists():
        try:
            b_data = json.loads(batch_file.read_text(encoding="utf-8"))
            scs = b_data.get("scenes", [])
            if len(scs) == (end_sc - start_sc + 1):
                print(f"PLAN_BATCH_DONE {batch_idx}/{total_batches} scenes {start_sc}-{end_sc} loaded from cache", flush=True)
                return scs
        except Exception:
            pass

    print(f"PLAN_BATCH_START {batch_idx}/{total_batches} scenes {start_sc}-{end_sc}...", flush=True)

    target_lang_upper = target_lang_name.upper()
    is_vi = any(k in target_lang_name.lower() for k in ("vi", "viet"))

    special_rule = ""
    if start_sc == 1:
        special_rule = (
            "SCENE 1 HOOK MANDATE: Scene 1 Beat 1 MUST open in media res with an explosive hook: "
            "a devastating confrontation, an unmasked betrayal, an ultimatum, or life-and-death secret. "
            "NO slow exposition! Hook the audience instantly within the first 3 seconds!"
        )
    elif end_sc == total_scene_count:
        special_rule = (
            "FINAL SCENE CLIFFHANGER: Deliver the emotional climax and end on a powerful, unresolved "
            "cliffhanger or suspenseful twist (Zeigarnik open loop) that makes the audience eager for the next episode!"
        )
    else:
        special_rule = "MAINTAIN RISING TENSION: Deepen interpersonal conflict, sharp subtext, and escalate stakes."

    sys_instruction = f"""You are an elite Television & Cinema Drama Screenwriter.
Write detailed screenplay scenes for Scenes {start_sc} to {end_sc} of '{series_name}'.
Language: {target_lang_name}
Genre: {genre}
{writing_rules(genre, visual_style)}

CRITICAL MANDATES:
1. All spoken lines ('text') in 'dialogue_beats' MUST be 100% natural, visceral, dramatic dialogue in {target_lang_upper}.
2. 'visual_setup', character 'appearance', and actor 'action' MUST be written in English for the AI video generator.
3. Strict Character & Visual Consistency: Adhere strictly to the Master Cast:
{json.dumps(characters_def, ensure_ascii=False, indent=2)}
4. Master Setting: {master_setting}
5. CINEMATOGRAPHY & LIGHTING RULES (ANTI-BLACK / HOLLYWOOD STANDARD):
   NEVER use words that produce pitch-black or unviewable frames ('pitch black', 'total darkness', 'crushing obsidian black', 'zero light', 'dark void', 'haunting gloom').
   For night, abyss, deep ocean, or dark interior scenes: ALWAYS mandate vibrant cinematic lighting: 'cinematic volumetric lighting', 'piercing electric cyan and deep sapphire god-rays', 'dramatic 3-point rim lighting carving creature/actor silhouette', 'luminous bioluminescent glow (electric cyan, amber, violet) casting bright reflections on skin and scales', 'crystal clear visibility with rich lifted shadow pedestal (deep midnight navy, never pitch black)', '8k master cinema shot'.
6. ANATOMICAL FIDELITY & LIVING CREATURE REALISM:
   When characters include animals, marine life, or creatures (e.g. Sperm Whale, Giant Squid, Orca, Shark):
   MANDATORY: Anchor exact biological anatomy (e.g., Sperm Whale: massive blunt box-shaped rectangular head 1/3 body, flat vertical forehead, narrow underslung lower jaw hinged open with conical white teeth, dark charcoal wrinkled skin with white sucker scars, paddle flippers; never a generic fish).
7. STRICT SPEAKER ATTRIBUTION & ROLE SEPARATION:
   In 'dialogue_beats', EACH entry MUST represent exactly ONE character speaking.
   NEVER combine lines or reactions from different characters into a single beat.
   'speaker' MUST be the exact name from 'characters_present' (no parenthetical notes, no titles, no generic labels).
   In dialogue exchanges, alternate beats cleanly (e.g. Beat 1: Speaker A, Beat 2: Speaker B).
   Character lines must stay strictly faithful to that character's established persona, status, and vocabulary.
8. CINEMATIC DIALOGUE PACING & WORD BUDGET (CHUẨN ĐIỆN ẢNH):
   For a 10-second scene, dialogue MUST be punchy, rhythmic, and restrained: MAXIMUM 12–18 WORDS TOTAL per scene across all beats (e.g. 6–9 words per beat for a 2-beat exchange).
   NEVER write long paragraphs or fast-rambling speeches. Cinema dialogue relies on subtext, silence, intense eye contact, and dramatic weight.
   Every spoken beat must leave room for natural human breathing (0.3–0.5s pause) and physical reaction.
9. HOLLYWOOD CINEMATIC SHOT COVERAGE & DYNAMIC PATTERN INTERRUPTS:
   - Strictly honor the Sequence Block from the outline (stable location, locked lighting).
   - MANDATORY: NEVER repeat the same camera shot size across consecutive cuts! Alternate dynamically across the 12 Hollywood Master Shot Archetypes:
     * High Shock/Revelation beats: 'DOLLY_ZOOM_VERTIGO' or 'WHIP_PAN_REVEAL'
     * Intense Confrontation/Debate: 'DIRTY_OVER_THE_SHOULDER' or 'COWBOY_CONFRONTATION'
     * Imposing Power / Monumental Presence: 'LOW_ANGLE_TITAN' or 'SILHOUETTE_RIM_LIT'
     * Micro-emotion & Suspicion: 'EXTREME_MACRO_ECU' or 'FOCUS_PULL_REVEAL'
     * Paranoia & Psychological Crisis: 'DUTCH_ANGLE_PARANOIA'
     * Forward Journey & Infiltration: 'PARALLAX_STEADICAM_FOLLOW'
     * Turning Point & Epiphany: 'ORBITAL_ARC_360'
     * Solitude & Destiny: 'GODS_EYE_OVERHEAD'
10. MULTI-CHARACTER IDENTITY ANCHORING & ZERO FACE DRIFT:
   When multiple characters are present, designate exactly ONE character as 'primary_focus_character' (the actor in front of the lens delivering dialogue or reacting). The secondary character MUST be framed in over-the-shoulder, soft background profile, or listening eye-line. NEVER prompt two competing full-frontal close-ups in one 10s shot, which causes AI facial morphing and attribute blending.

{special_rule}

STRICT JSON OUTPUT FORMAT:
{{
  "scenes": [
    {{
      "scene_number": {start_sc},
      "setting": "Specific sub-location",
      "location_id": "stable_location_id_from_master_outline",
      "sequence_id": "sequence_01",
      "props_required": ["stable_prop_ids_used_in_this_scene"],
      "wardrobe_state": {{"Character 1": "outfit_id_stable_for_this_act"}},
      "prop_state": {{"hero_prop_id": {{"holder": "Character 1", "hand": "left", "position": "held"}}}},
      "summary": "1-2 sentence dramatic summary in {target_lang_name}",
      "start_state": "Exact character locations, costume, hand-held props, eye lines and physical states inherited from prior end, written in English",
      "end_state": "Exact resulting positions, props, eye lines, lighting, and motion state to continue into the next scene, written in English",
      "visual_setup": "Detailed English visual prompt for AI video generator: environment, lighting, color palette, camera angle, character appearance anchors, 8k cinematic film still",
      "camera_motion": "DOLLY_ZOOM_VERTIGO" or "LOW_ANGLE_TITAN" or "EXTREME_MACRO_ECU" or "DIRTY_OVER_THE_SHOULDER" or "ORBITAL_ARC_360" or "DUTCH_ANGLE_PARANOIA" or "PARALLAX_STEADICAM_FOLLOW" or "FOCUS_PULL_REVEAL" or "GODS_EYE_OVERHEAD" or "SILHOUETTE_RIM_LIT" or "COWBOY_CONFRONTATION" or "WHIP_PAN_REVEAL",
      "bgm_mood": "tense_investigation" or "epic_tension" or "emotional_revelation",
      "sfx_cues": ["heavy_rain_on_roof", "fireplace_crackling", "door_slam"],
      "characters_present": ["Character 1", "Character 2"],
      "primary_focus_character": "Character 1",
      "dialogue_beats": [
        {{
          "speaker": "Character Name",
          "tone": "menacing" or "defiant" or "whisper" or "trembling" or "commanding" or "sarcastic",
          "text": "Spoken dialogue line 100% in {target_lang_name}",
          "action": "Physical action or facial micro-expression in English"
        }}
      ]
    }}
  ]
}}
"""

    user_prompt = f"""Write the full detailed screenplay for Scenes {start_sc} to {end_sc} based on this planned outline:
{json.dumps(outline_slice, ensure_ascii=False, indent=2)}

PREVIOUS SCENE CONTEXT FOR SEAMLESS CONTINUITY:
Summary: {prev_summary or "Beginning of episode."}
Last spoken dialogue: {prev_dialogue or "None."}

Write all {len(outline_slice)} scenes now in valid JSON format.
"""

    for attempt in range(3):
        try:
            resp = client.models.generate_content(model=model, contents=f"{sys_instruction}\n\n{user_prompt}")
            resp_text = resp.text if hasattr(resp, "text") else str(resp)
            batch_data = extract_json_payload(resp_text)
            scenes = batch_data.get("scenes", [])
            if not scenes:
                raise ValueError("No scenes found in batch JSON response.")

            # Renumber sequentially
            for i, sc in enumerate(scenes):
                sc["scene_number"] = start_sc + i

            # Language check
            scenes = _ensure_language_consistency(scenes, target_lang_name, client, model)

            if batch_file:
                batch_file.write_text(json.dumps({"scenes": scenes}, indent=2, ensure_ascii=False), encoding="utf-8")

            print(f"PLAN_BATCH_DONE {batch_idx}/{total_batches} scenes {start_sc}-{end_sc} saved", flush=True)
            return scenes
        except Exception as exc:
            print(f"[DRAMA_PLANNER_RETRY] Đợt {batch_idx} gặp sự cố ({type(exc).__name__}: {exc}). Thử lại lần {attempt+1}/3...", flush=True)
            time.sleep(2 * (attempt + 1))

    raise RuntimeError(f"Planning batch {batch_idx} (scenes {start_sc}-{end_sc}) failed after 3 attempts.")


def generate_drama_screenplay(
    prompt: str,
    series_name: str,
    episode_num: int = 1,
    language: str = "Vietnamese",
    genre: str = "drama",
    scene_count: int = 6,
    model: str = "gemini-3.8-flash",
    episode_dir: Optional[Path] = None,
    visual_style: str = "auto",
) -> EpisodeDramaPlan:
    """Invokes Resilient Gemini to write a full cinematic drama screenplay with multi-character dialogue beats.
    Automatically uses intelligent multi-batch generation when scene_count > 6 to support full-length movies (10-30+ mins).
    """
    client = ResilientClient()
    target_lang_name = str(language or "Vietnamese").strip()
    target_lang_upper = target_lang_name.upper()
    is_vi = any(k in target_lang_name.lower() for k in ("vi", "viet"))

    part_dir = (episode_dir / "drama_plan_parts") if episode_dir else None
    if part_dir:
        part_dir.mkdir(parents=True, exist_ok=True)

    # BRANCH 1: Single-Turn Generation for Short Form (scene_count <= 6)
    if scene_count <= 6:
        lang_mandate = (
            f"- TARGET LANGUAGE: {target_lang_upper}\n"
            f"- ALL SPOKEN DIALOGUE ('text'), scene summaries ('summary'), episode title ('title'), and loglines ('logline') MUST BE 100% WRITTEN IN {target_lang_upper}!\n"
        )
        if is_vi:
            lang_mandate += "- Tiếng Việt đời sống, sắc sảo, kịch tính, dằn vặt, giàu sức nặng cảm xúc.\n"
        else:
            lang_mandate += f"- Dialogue MUST be natural, contemporary {target_lang_name} (ABSOLUTELY NO Vietnamese characters or words).\n"

        system_instruction = f"""You are an elite Showrunner and Screenwriter for award-winning Television & Cinema Dramas.
Your task is to write a GRIPPING, HIGH-STAKES CINEMATIC DRAMA SCREENPLAY for Episode {episode_num} of '{series_name}'.
{writing_rules(genre, visual_style)}

CRITICAL TARGET LANGUAGE MANDATE:
{lang_mandate}
- 'visual_setup', 'appearance', and 'action' must be written in English for the AI image/video generator.

CRITICAL SCREENWRITING MANDATES:
1. EXPLOSIVE 30S COLD OPEN HOOK (IN MEDIAS RES): Scene 1 Beat 1 MUST drop the audience right into the boiling point crisis: a devastating confrontation, an unmasked betrayal, an ultimatum, or discovery of a life-and-death secret. NO slow exposition! Hook the audience within the first 3 seconds with an irresistible curiosity gap!
2. DYNAMIC CAMERA PACING & PATTERN INTERRUPTS: Alternate camera perspective rhythmically (tight macro reaction close-up -> wide atmospheric establishing -> over-the-shoulder confrontation -> dynamic tracking) to eliminate visual fatigue and keep viewer engagement peaking.
3. VISCERAL, NATURAL DIALOGUE IN {target_lang_upper}: Spoken lines clashing directly with emotional tone and physical action.
3. CHARACTER VISUAL CONTINUITY & DNA LOCK: Detailed English appearance descriptions locked across scenes.
   ASSET-FIRST: create stable location_id and props_required for every scene; record wardrobe_state and prop_state, retaining the same room geometry, props and hand ownership across adjacent shots.
4. SETTING CONTINUITY: Unified master physical environment.
5. SOUND DESIGN: 'bgm_mood' and 'sfx_cues' (2-3 atmospheric sound cues per scene).
6. CINEMATOGRAPHY & LIGHTING RULES (ANTI-BLACK / HOLLYWOOD STANDARD):
   NEVER use words that produce pitch-black or unviewable frames ('pitch black', 'total darkness', 'crushing obsidian black', 'zero light', 'dark void', 'haunting gloom').
   For night, abyss, deep ocean, or dark interior scenes: ALWAYS mandate vibrant cinematic lighting: 'cinematic volumetric lighting', 'piercing electric cyan and deep sapphire god-rays', 'dramatic 3-point rim lighting carving creature/actor silhouette', 'luminous bioluminescent glow (electric cyan, amber, violet) casting bright reflections on skin and scales', 'crystal clear visibility with rich lifted shadow pedestal (deep midnight navy, never pitch black)', '8k master cinema shot'.
7. ANATOMICAL FIDELITY & LIVING CREATURE REALISM:
   When characters include animals, marine life, or creatures (e.g. Sperm Whale, Giant Squid, Orca, Shark):
   MANDATORY: Anchor exact biological anatomy (e.g., Sperm Whale: massive blunt box-shaped rectangular head 1/3 body, flat vertical forehead, narrow underslung lower jaw hinged open with conical white teeth, dark charcoal wrinkled skin with white sucker scars, paddle flippers; never a generic fish).

STRICT OUTPUT FORMAT (JSON ONLY):
{{
  "title": "Dramatic episode title in {target_lang_name}",
  "logline": "1-sentence hook summarizing the climax in {target_lang_name}",
  "master_setting": "Master physical environment description across scenes",
  "locations": {{"living_room": {{"name": "Living room", "spec": "Exact furniture, windows, door and lighting layout; same across all scenes"}}}},
  "props": {{"black_phone": {{"name": "Lan black phone", "spec": "Same exact model, color, size, finish throughout story"}}}},
  "characters": [
    {{
      "name": "Character Name",
      "gender": "male" or "female",
      "role": "protagonist" or "antagonist" or "supporting",
      "personality": "Deep inner drive, ambition, and psychological flaw",
      "appearance": "HYPER-SPECIFIC PHYSICAL DNA LOCK in English: exact age, facial landmarks with permanent identifying mole/scar, skin undertone, exact hair styling, and immutable wardrobe per Act (NO 'transitioning' words). Zero bare names."
    }}
  ],
  "scenes": [
    {{
      "scene_number": 1,
      "setting": "Specific location within master setting",
      "location_id": "living_room",
      "sequence_id": "sequence_01",
      "props_required": ["black_phone"],
      "wardrobe_state": {{"Character 1": "outfit_act_1"}},
      "prop_state": {{"black_phone": {{"holder": "Character 1", "hand": "left", "position": "held"}}}},
      "summary": "Dramatic turning point in {target_lang_name}",
      "start_state": "Exact initial positions, attire, hands/props, gaze and light matching the prior shot, in English",
      "end_state": "Exact final positions, attire, hands/props, gaze and light for the next shot, in English",
      "visual_setup": "Detailed English visual prompt: setting architecture, lighting, color tone, character appearance anchors, 8k cinematic film still",
      "camera_motion": "DOLLY_ZOOM_VERTIGO" or "LOW_ANGLE_TITAN" or "EXTREME_MACRO_ECU" or "DIRTY_OVER_THE_SHOULDER" or "ORBITAL_ARC_360" or "DUTCH_ANGLE_PARANOIA" or "PARALLAX_STEADICAM_FOLLOW" or "FOCUS_PULL_REVEAL" or "GODS_EYE_OVERHEAD" or "SILHOUETTE_RIM_LIT" or "COWBOY_CONFRONTATION" or "WHIP_PAN_REVEAL",
      "bgm_mood": "tense_investigation" or "epic_tension" or "emotional_revelation",
      "sfx_cues": ["heavy_rain_on_roof", "fireplace_crackling", "thunder_crack"],
      "characters_present": ["Character 1", "Character 2"],
      "dialogue_beats": [
        {{
          "speaker": "Character name or Narrator",
          "tone": "defiant" or "menacing" or "whisper" or "trembling" or "commanding" or "sarcastic",
          "text": "Spoken dialogue line 100% in {target_lang_name} full of emotion and dramatic weight",
          "action": "Physical action or facial micro-expression in English"
        }}
      ]
    }}
  ]
}}
"""

        user_prompt = f"""SERIES: {series_name}
EPISODE: {episode_num}
GENRE: {genre}
TARGET LANGUAGE: {target_lang_name} (MANDATORY: All dialogue beats must be strictly in {target_lang_name})
TARGET SCENE COUNT: {scene_count} scenes

PREMISE / STORY BRIEF:
{prompt}

Write the complete {scene_count}-scene screenplay now with multi-character dialogue beats strictly in {target_lang_name}.
"""

        resp = client.models.generate_content(model=model, contents=f"{system_instruction}\n\n{user_prompt}")
        resp_text = resp.text if hasattr(resp, "text") else str(resp)
        data = extract_json_payload(resp_text)
        data["scenes"] = _ensure_language_consistency(data.get("scenes", []), target_lang_name, client, model)

    # BRANCH 2: Intelligent Multi-Batch Screenplay Generation for Long Form (scene_count > 6)
    else:
        print(f"\n=======================================================", flush=True)
        print(f"🎬 [KỊCH BẢN PHIM DÀI] KÍCH HOẠT QUY TRÌNH BIÊN KỊCH ĐA PHÂN ĐOẠN", flush=True)
        print(f"   Thời lượng: {scene_count * 10 / 60:.1f} phút | Số phân cảnh: {scene_count} cảnh Muse Video (10s/cảnh)", flush=True)
        print(f"   Ngôn ngữ: {target_lang_name} | Thể loại: {genre}", flush=True)
        print(f"=======================================================\n", flush=True)

        master_data = _generate_master_outline(
            prompt=prompt,
            series_name=series_name,
            episode_num=episode_num,
            target_lang_name=target_lang_name,
            genre=genre,
            visual_style=visual_style,
            scene_count=scene_count,
            client=client,
            model=model,
            part_dir=part_dir
        )

        characters_def = master_data.get("characters", [])
        master_setting = master_data.get("master_setting", "Cinematic dramatic set")
        outline = master_data.get("outline", [])

        batch_size = 6
        total_batches = (scene_count + batch_size - 1) // batch_size
        all_raw_scenes = []
        prev_summary = ""
        prev_dialogue = ""

        for b_idx in range(1, total_batches + 1):
            start_sc = (b_idx - 1) * batch_size + 1
            end_sc = min(scene_count, b_idx * batch_size)
            outline_slice = outline[start_sc - 1 : end_sc]

            b_scenes = _generate_batch_scenes(
                batch_idx=b_idx,
                total_batches=total_batches,
                start_sc=start_sc,
                end_sc=end_sc,
                characters_def=characters_def,
                master_setting=master_setting,
                outline_slice=outline_slice,
                prev_summary=prev_summary,
                prev_dialogue=prev_dialogue,
                series_name=series_name,
                genre=genre,
                visual_style=visual_style,
                target_lang_name=target_lang_name,
                client=client,
                model=model,
                part_dir=part_dir,
                total_scene_count=scene_count
            )

            all_raw_scenes.extend(b_scenes)
            if b_scenes:
                last_sc = b_scenes[-1]
                prev_summary = last_sc.get("summary", "")
                beats = last_sc.get("dialogue_beats", [])
                if beats:
                    prev_dialogue = f"{beats[-1].get('speaker')}: \"{beats[-1].get('text')}\""

        data = {
            "title": master_data.get("title") or f"{series_name} - Tập {episode_num}",
            "logline": master_data.get("logline") or "",
            "master_setting": master_setting,
            "characters": characters_def,
            "locations": master_data.get("locations") or {},
            "props": master_data.get("props") or {},
            "scenes": all_raw_scenes
        }

    # Voice Director Casting
    director = VoiceDirector(language=language)
    char_defs = data.get("characters") or []
    known_names = {str(c.get("name", "")).strip().lower() for c in char_defs if isinstance(c, dict)}
    for sc in (data.get("scenes") or []):
        for c_cand in (sc.get("characters_present") or []):
            c_cand_str = str(c_cand).strip()
            if c_cand_str and c_cand_str.lower() not in ("narrator", "người dẫn chuyện", "dẫn chuyện") and c_cand_str.lower() not in known_names:
                is_f = any(w in c_cand_str.lower() for w in ("mimi", "anna", "eva", "mary", "lisa", "hoa", "linh", "lan", "mai", "bà", "cô", "chị", "em", "woman", "girl"))
                char_defs.append({
                    "name": c_cand_str,
                    "role": "supporting",
                    "gender": "female" if is_f else "male",
                    "appearance": f"Photorealistic supporting character {c_cand_str}"
                })
                known_names.add(c_cand_str.lower())
    cast_map = director.cast_characters(char_defs)

    # Assemble Structured Scenes
    scenes_list: List[SceneDrama] = []
    raw_scenes = data.get("scenes") or []

    for sc_data in raw_scenes:
        s_num = int(sc_data.get("scene_number", len(scenes_list) + 1))
        beats: List[DialogueBeat] = []
        for b_idx, b_data in enumerate(sc_data.get("dialogue_beats") or []):
            spk = str(b_data.get("speaker") or "Narrator").strip()
            is_narr = spk.lower() in ("narrator", "người dẫn chuyện", "dẫn chuyện")
            clean_spk = re.sub(r'\(.*?\)', '', spk).strip()
            cast_profile = cast_map.get(spk) or cast_map.get(clean_spk)
            if not cast_profile:
                for c_name, c_prof in cast_map.items():
                    if clean_spk.lower() in c_name.lower() or c_name.lower() in clean_spk.lower():
                        cast_profile = c_prof
                        break
            if not cast_profile:
                cast_profile = cast_map.get("Narrator")
            v_id = cast_profile.voice_id if cast_profile else "Charon"
            g_val = cast_profile.gender if cast_profile else "male"

            beat = DialogueBeat(
                beat_id=b_idx + 1,
                speaker=spk,
                text=str(b_data.get("text") or "").strip(),
                tone=str(b_data.get("tone") or "natural"),
                voice_id=v_id,
                gender=g_val,
                is_narrator=is_narr,
                action=str(b_data.get("action") or ""),
                pause_after_seconds=0.35
            )
            beats.append(beat)

        scene_obj = SceneDrama(
            scene_number=s_num,
            setting=str(sc_data.get("setting") or ""),
            summary=str(sc_data.get("summary") or ""),
            visual_setup=str(sc_data.get("visual_setup") or ""),
            camera_motion=str(sc_data.get("camera_motion") or "slow_zoom_in"),
            bgm_mood=str(sc_data.get("bgm_mood") or "tense_investigation"),
            sfx_cues=[str(s) for s in sc_data.get("sfx_cues") or []],
            characters_present=[str(c) for c in sc_data.get("characters_present") or []],
            dialogue_beats=beats,
            visual_prompt=str(sc_data.get("visual_setup") or ""),
            start_state=str(sc_data.get("start_state") or ""),
            end_state=str(sc_data.get("end_state") or ""),
            sequence_id=str(sc_data.get("sequence_id") or ""),
            location_id=str(sc_data.get("location_id") or ""),
            props_required=[str(x) for x in sc_data.get("props_required") or []],
            wardrobe_state=sc_data.get("wardrobe_state") or {},
            prop_state=sc_data.get("prop_state") or {},
            transition_action=str(sc_data.get("transition_action") or ""),
            transition_props=[str(x) for x in sc_data.get("transition_props") or []],
            wardrobe_transition_authorized=bool(sc_data.get("wardrobe_transition_authorized",False)),
        )
        scenes_list.append(scene_obj)

    plan = EpisodeDramaPlan(
        series_name=series_name,
        episode_num=episode_num,
        language=language,
        genre=genre,
        title=str(data.get("title") or f"{series_name} - Tập {episode_num}"),
        logline=str(data.get("logline") or ""),
        cast=cast_map,
        scenes=scenes_list,
        created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        locations=data.get("locations") or {},
        props=data.get("props") or {}
    )

    return plan
