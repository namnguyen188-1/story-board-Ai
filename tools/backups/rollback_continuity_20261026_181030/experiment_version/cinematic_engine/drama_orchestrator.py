"""Cinematic Drama Orchestrator - Main Production Pipeline for Branch B.

Handles multi-character dialogue generation, voice casting, scene assembly, BGM/SFX mixing,

cinematic video generation, and final episode stitching.

"""

from __future__ import annotations



import os

import sys

import json

import time

import subprocess

import concurrent.futures

import threading

from pathlib import Path

from typing import Any, List, Dict



# Reconfigure stdout/stderr for clean utf-8 logging on Windows

if hasattr(sys.stdout, "reconfigure"):

    try:

        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    except Exception:

        pass



# Add paths to sys.path if not present

CURRENT_DIR = Path(__file__).resolve().parent

STUDIO_DIR = CURRENT_DIR.parent

ENGINE_DIR = STUDIO_DIR / "engine"

WORKSPACE_DIR = STUDIO_DIR.parent

for p in [str(STUDIO_DIR), str(ENGINE_DIR), str(WORKSPACE_DIR)]:

    if p not in sys.path:

        sys.path.insert(0, p)



from .drama_planner import generate_drama_screenplay

from .drama_schema import EpisodeDramaPlan, CharacterProfile

from .drama_audio_engine import DramaAudioEngine

from .drama_sound_mixer import DramaSoundMixer

from .drama_video_engine import DramaVideoEngine



PRODUCTIONS_DIR = STUDIO_DIR / "productions"





def concatenate_scene_videos(scene_videos: List[Path], output_episode_mp4: Path) -> Path:

    """Concatenates all scene MP4 videos into a single master episode video."""

    out_path = Path(output_episode_mp4)

    out_path.parent.mkdir(parents=True, exist_ok=True)



    if not scene_videos:

        raise ValueError("No scene videos provided for concatenation.")



    if len(scene_videos) == 1:

        import shutil

        shutil.copy2(str(scene_videos[0]), str(out_path))

        return out_path



    concat_txt = out_path.parent / "scene_concat_list.txt"

    with open(concat_txt, "w", encoding="utf-8") as f:

        for v in scene_videos:

            clean_path = str(v.resolve()).replace("\\", "/")

            f.write(f"file '{clean_path}'\n")



    cmd = [

        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",

        "-f", "concat",

        "-safe", "0",

        "-i", str(concat_txt),

        "-c", "copy",

        str(out_path)

    ]



    try:

        subprocess.run(cmd, check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))

    finally:

        if concat_txt.exists():

            try:

                concat_txt.unlink()

            except Exception:

                pass

    # Hollywood Cinematic Color Grading & Exposure Normalization
    try:
        from .drama_color_grader import grade_video_cinematic
        print(f"[CONCAT] Dang tu dong ap dung Hollywood Master Color Grade & Can bang anh sang cho tap phim...", flush=True)
        grade_video_cinematic(out_path, out_path)
    except Exception as grade_err:
        print(f"[CONCAT_WARN] Bo qua color grade tu dong: {grade_err}", flush=True)

    return out_path





def run_cinematic_drama(args: Any) -> int:

    """Executes the complete Cinematic Drama production pipeline."""

    series_name = getattr(args, "series", "Cinematic Drama")

    episode_num = int(getattr(args, "episode", 1))

    language = getattr(args, "language", "Vietnamese")

    genre = getattr(args, "genre", "drama")

    prompt = getattr(args, "prompt", "") or getattr(args, "series", "")

    minutes = float(getattr(args, "minutes", 2.0))

    image_provider = getattr(args, "image_provider", "muse_video")

    # In Cinematic Drama with Muse, each motion clip is strictly 10.0 seconds

    clip_duration = 10.0

    if image_provider == "muse_video":

        scene_seconds = clip_duration

    else:

        scene_seconds = float(getattr(args, "scene_seconds", clip_duration) or clip_duration)

    scene_count = max(1, int(round((minutes * 60) / scene_seconds)))

    aspect_ratio = getattr(args, "aspect_ratio", "16:9")

    visual_style = getattr(args, "visual_style", "cinematic_drama")

    size = getattr(args, "size", "1280x720")



    no_subtitles = bool(getattr(args, "no_subtitles", False))

    subtitle_style = "none" if no_subtitles else getattr(args, "subtitle_style", "karaoke_viral")

    subtitle_size = int(getattr(args, "subtitle_size", 0) or 0)



    try:

        w_str, h_str = str(size).lower().split("x")

        width, height = int(w_str), int(h_str)

        if width < height:

            aspect_ratio = "9:16"

        else:

            aspect_ratio = "16:9"

    except Exception:

        width, height = (1280, 720) if aspect_ratio == "16:9" else (720, 1280)



    print(f"\n=======================================================", flush=True)

    print(f"🎬 KHỞI ĐỘNG SẢN XUẤT: PHIM KỊCH ĐIỆN ẢNH (CINEMATIC DRAMA)", flush=True)

    print(f"   Series: {series_name} | Tập: {episode_num} | Ngôn ngữ: {language}", flush=True)

    print(f"   Động cơ hình ảnh/video: {image_provider} ({width}x{height} - {aspect_ratio})", flush=True)

    print(f"   Kiểu phụ đề: {subtitle_style} | Cỡ chữ: {subtitle_size or 'Mặc định (52px)'} | Tắt phụ đề: {no_subtitles}", flush=True)

    print(f"   Số phân cảnh mục tiêu: {scene_count} cảnh đối thoại", flush=True)

    print(f"=======================================================\n", flush=True)



    # 1. Prepare Episode Directory

    from series_studio import slug

    series_slug = slug(series_name)

    episode_dir = PRODUCTIONS_DIR / series_slug / f"episode_{episode_num:03d}"

    episode_dir.mkdir(parents=True, exist_ok=True)



    plan_file = episode_dir / "drama_plan.json"



    # 2. Generate or Load Drama Screenplay

    input_mode = getattr(args, "input_mode", "idea")

    raw_plan = None



    if plan_file.exists():

        try:

            candidate_plan = json.loads(plan_file.read_text(encoding="utf-8"))

            candidate_scenes = candidate_plan.get("scenes", [])

            # Incomplete plan guard: If requested duration is long (e.g. 21 mins = 126 scenes) but plan only has 5 scenes

            if len(candidate_scenes) < scene_count * 0.7 and scene_count > 8:

                print(f"[DRAMA] Kịch bản cũ chỉ có {len(candidate_scenes)} cảnh, không đủ cho thời lượng {minutes:.1f} phút ({scene_count} cảnh mục tiêu)!", flush=True)

                print(f"[DRAMA] Đang tự động biên kịch lại đầy đủ {scene_count} cảnh cho phim dài...", flush=True)

                plan_file.unlink(missing_ok=True)

                part_dir = episode_dir / "drama_plan_parts"

                if part_dir.exists():

                    import shutil

                    shutil.rmtree(part_dir, ignore_errors=True)

            else:

                raw_plan = candidate_plan

                print(f"[DRAMA] Phát hiện drama_plan.json. Đang tải kịch bản hiện có...", flush=True)

                print(f"[DRAMA] Đã tải thành công: {raw_plan.get('title')} ({len(candidate_scenes)} cảnh)", flush=True)

        except Exception as plan_err:

            print(f"[DRAMA_WARN] Lỗi đọc drama_plan cũ: {plan_err}. Sẽ biên kịch mới.", flush=True)



    if raw_plan is None:

        if input_mode == "script":

            print(f"[DRAMA] Phát hiện Kịch bản có sẵn (Input Mode: Script). Đang nạp và giữ nguyên 100% kịch bản gốc...", flush=True)

            from studio_input_modes import parse_locked_screenplay, convert_locked_scenes_to_drama_plan

            parsed_scenes = parse_locked_screenplay(prompt)

            raw_plan = convert_locked_scenes_to_drama_plan(parsed_scenes, series_name, episode_num, language, genre)

            plan_file.write_text(json.dumps(raw_plan, indent=2, ensure_ascii=False), encoding="utf-8")

            print(f"[DRAMA] Đã nạp thành công {len(parsed_scenes)} cảnh kịch bản gốc của bạn (bỏ qua LLM viết kịch bản)!", flush=True)

        elif input_mode == "link":

            ref_url = getattr(args, "reference_url", "") or prompt

            print(f"[DRAMA] Phát hiện chế độ phân tích liên kết YouTube (Input Mode: Link): {ref_url[:80]}", flush=True)



            transcript_context = ""

            try:

                from transcript_cloner import fetch_youtube_transcript

                sub_info = fetch_youtube_transcript(ref_url, preferred_lang=language)

                if sub_info.get("ok") and sub_info.get("lines"):

                    lines = sub_info.get("lines", [])

                    print(f"[DRAMA] Đã trích xuất {len(lines)} dòng phụ đề từ video gốc ({sub_info.get('language_code', '')})!", flush=True)

                    transcript_timeline = []

                    step = max(1, len(lines) // min(scene_count, 35))

                    for i in range(0, len(lines), step):

                        chunk = lines[i:i + step]

                        t_start = chunk[0].get("start", 0)

                        m_start, s_start = int(t_start // 60), int(t_start % 60)

                        txt = " ".join(c.get("text", "") for c in chunk)

                        transcript_timeline.append(f"[{m_start:02d}:{s_start:02d}] {txt[:220]}")

                    transcript_context = "\n".join(transcript_timeline)

            except Exception as tr_err:

                print(f"[DRAMA_WARN] Không thể tải phụ đề YouTube: {tr_err}", flush=True)



            enriched_prompt = (

                f"REFERENCE SOURCE VIDEO: {ref_url}\n"

                f"TARGET MOVIE DURATION: {minutes:.1f} minutes ({scene_count} motion scenes, 10s per scene)\n"

            )

            if transcript_context:

                enriched_prompt += f"\nCHRONOLOGICAL TRANSCRIPT & STORY TIMELINE FROM ORIGINAL VIDEO:\n{transcript_context}\n\n"

                enriched_prompt += (

                    f"MANDATORY INSTRUCTION: You must adapt this complete {minutes:.1f}-minute original story "

                    f"into a full-length, multi-character cinematic drama with exactly {scene_count} scenes. "

                    f"Distribute the dramatic plot evenly across all {scene_count} scenes so the narrative spans the entire duration!"

                )

            else:

                enriched_prompt += f"\nPREMISE / STORY BRIEF:\n{prompt}\n\n"

                enriched_prompt += (

                    f"MANDATORY INSTRUCTION: Expand this story into a full-length {minutes:.1f}-minute cinematic drama "

                    f"with exactly {scene_count} scenes (10s each)."

                )



            print(f"[DRAMA] Đang kết nối AI biên kịch viết kịch bản phân vai & lời thoại đối đáp ({scene_count} cảnh)...", flush=True)

            drama_plan = generate_drama_screenplay(

                prompt=enriched_prompt,

                series_name=series_name,

                episode_num=episode_num,

                language=language,

                genre=genre,

                scene_count=scene_count,

                model=getattr(args, 'model', 'gemini-3.8-flash'),

                episode_dir=episode_dir,

            )



            raw_plan = drama_plan.to_dict()

            raw_plan["prompt"] = prompt

            raw_plan["input_mode"] = input_mode

            plan_file.write_text(json.dumps(raw_plan, indent=2, ensure_ascii=False), encoding="utf-8")

            print(f"[DRAMA] Đã biên kịch thành công tập phim: '{drama_plan.title}' ({len(raw_plan.get('scenes', []))} cảnh)!", flush=True)

        else:

            print(f"[DRAMA] Đang kết nối AI biên kịch viết kịch bản phân vai & lời thoại đối đáp ({scene_count} cảnh)...", flush=True)

            drama_plan = generate_drama_screenplay(

                prompt=prompt,

                series_name=series_name,

                episode_num=episode_num,

                language=language,

                genre=genre,

                scene_count=scene_count,

                model=getattr(args, 'model', 'gemini-3.8-flash'),

                episode_dir=episode_dir,

            )



            raw_plan = drama_plan.to_dict()

            raw_plan["prompt"] = prompt

            raw_plan["input_mode"] = input_mode

            plan_file.write_text(json.dumps(raw_plan, indent=2, ensure_ascii=False), encoding="utf-8")

            print(f"[DRAMA] Đã biên kịch thành công tập phim: '{drama_plan.title}' ({len(raw_plan.get('scenes', []))} cảnh)!", flush=True)



    # Convert cast to CharacterProfile objects

    cast_map: Dict[str, CharacterProfile] = {

        name: CharacterProfile(

            name=name,

            gender=data.get("gender", "male"),

            role=data.get("role", "supporting"),

            voice_id=data.get("voice_id", "Charon"),

            voice_label=data.get("voice_label", ""),

            personality=data.get("personality", ""),

            appearance_lock=data.get("appearance_lock", "") or data.get("appearance", "")

        )

        for name, data in raw_plan.get("cast", {}).items()

    }



    print("\n--- DÀN DIỄN VIÊN & GIỌNG LỒNG TIẾNG (CASTING) ---", flush=True)

    for char_name, c_prof in cast_map.items():

        print(f"  🎭 {char_name:18s}: Giọng '{c_prof.voice_id}' ({c_prof.voice_label})", flush=True)



    scenes_data = raw_plan.get("scenes", [])

    print(f"\n--- TIẾN HÀNH SẢN XUẤT {len(scenes_data)} PHÂN CẢNH ---", flush=True)



    # Export initial compatibility bridge IMMEDIATELY so Storyboard Deck populates in UI

    export_legacy_compatibility_bridge(

        episode_dir, raw_plan, [], None,

        image_provider=image_provider,

        subtitle_style=subtitle_style,

        subtitle_size=subtitle_size

    )

    print(f"PLAN_READY scenes {len(scenes_data)}", flush=True)

    print(f"[DRAMA] Phân cảnh Storyboard ({len(scenes_data)} cảnh) đã sẵn sàng hiển thị trên giao diện Studio!", flush=True)



    bible = {

        "title": raw_plan.get("title", series_name),

        "world": raw_plan.get("synopsis", "") or raw_plan.get("logline", "") or prompt,

        "visual_style": visual_style if visual_style != "auto" else "Cinematic Film Drama, Photorealistic 8k, Atmospheric Moody Lighting, Masterpiece",

        "characters": [

            {

                "name": name,

                "description": prof.appearance_lock or prof.personality,

                "role": prof.role,

                "gender": prof.gender

            }

            for name, prof in cast_map.items()

        ]

    }



    audio_engine = DramaAudioEngine(target_sample_rate=24000)

    sound_mixer = DramaSoundMixer()

    video_engine = DramaVideoEngine(fps=24)



    scenes_root = episode_dir / "scenes"

    scenes_root.mkdir(parents=True, exist_ok=True)

    bridge_lock = threading.Lock()



    def render_single_scene(sc_idx: int, sc_data: dict, anchor_ref: Path | None) -> tuple[int, Path]:

        sc_num = sc_data.get("scene_number", sc_idx)

        sc_dir = scenes_root / f"scene_{sc_num:04d}"

        if not sc_dir.exists() and (scenes_root / f"scene_{sc_num:03d}").exists():

            sc_dir = scenes_root / f"scene_{sc_num:03d}"

        sc_dir.mkdir(parents=True, exist_ok=True)



        final_scene_mp4 = sc_dir / "scene_final.mp4"

        muse_clip = sc_dir / "muse_clip.mp4"

        render_style_file = sc_dir / "render_style.json"

        style_matches = False

        if render_style_file.exists():

            try:

                saved_style = json.loads(render_style_file.read_text(encoding="utf-8"))

                if (saved_style.get("subtitle_style") == subtitle_style and

                    int(saved_style.get("subtitle_size") or 0) == subtitle_size and

                    bool(saved_style.get("no_subtitles")) == no_subtitles):

                    style_matches = True

            except Exception:

                pass



        if getattr(args, "resume", False) and final_scene_mp4.exists() and final_scene_mp4.stat().st_size > 100000:

            if not style_matches:

                print(f"[CẢNH {sc_num:02d}] Phát hiện cập nhật thiết lập phụ đề (Kiểu: {subtitle_style}, Cỡ: {subtitle_size or 52}px) -> Áp dụng ngay...", flush=True)

            elif image_provider == "muse_video":

                if muse_clip.is_file() and muse_clip.stat().st_size > 1024:

                    from .drama_video_engine import get_media_duration

                    muse_dur = get_media_duration(muse_clip)

                    final_dur = get_media_duration(final_scene_mp4)

                    if abs(final_dur - muse_dur) > 0.6:

                        print(f"[CẢNH {sc_num:02d}] Phát hiện video cũ ghép giọng nhân tạo ({final_dur:.1f}s != Muse gốc {muse_dur:.1f}s), đang tạo lại bằng âm thanh & giọng nói gốc của Muse...", flush=True)

                    else:

                        print(f"[CẢNH {sc_num:02d}] Đã hoàn thiện chuẩn khớp phụ đề & âm thanh gốc ({final_scene_mp4.name}, {final_dur:.1f}s), bỏ qua.", flush=True)

                        print(f"SCENE_PASS {sc_num}", flush=True)

                        return sc_num, final_scene_mp4

                else:

                    print(f"[CẢNH {sc_num:02d}] Cảnh cũ thiếu muse_clip.mp4 (dùng ảnh ghép giọng) -> Bắt buộc dựng lại 100% video chuyển động Muse!", flush=True)

            else:

                print(f"[CẢNH {sc_num:02d}] Đã hoàn thiện từ trước, bỏ qua ({final_scene_mp4.name})", flush=True)

                print(f"SCENE_PASS {sc_num}", flush=True)

                return sc_num, final_scene_mp4



        print(f"\n=======================================================", flush=True)

        print(f"🎬 [CẢNH {sc_num:02d}/{len(scenes_data):02d}] {sc_data.get('summary', '')[:60]}", flush=True)

        print(f"SCENE_START {sc_num}/{len(scenes_data)}", flush=True)

        print(f"   Bối cảnh: {sc_data.get('setting', '')[:50]}", flush=True)

        print(f"   BGM Mood: {sc_data.get('bgm_mood', 'tense_investigation')}", flush=True)

        print(f"=======================================================", flush=True)



        # Step A & B: Audio & Sound Mixing

        if image_provider == "muse_video":

            print(f"\n[ÂM THANH GỐC NGUYÊN BẢN] Sử dụng trực tiếp giọng nói & hiệu ứng âm thanh gốc từ Muse AI Video (không ghép giọng nhân tạo ngoài)...", flush=True)

        else:

            master_wav = sc_dir / "scene_master_audio.wav"

            if not master_wav.exists() or master_wav.stat().st_size < 1000:

                print(f"\n[BƯỚC 1/3] Lồng tiếng đa nhân vật & nhịp thoại đối đáp...", flush=True)

                audio_res = audio_engine.assemble_scene_dialogue(

                    scene=sc_data,

                    language=language,

                    scene_dir=sc_dir,

                    cast_map=cast_map

                )

                dialogue_master = Path(audio_res["master_audio_path"])



                print(f"\n[BƯỚC 2/3] Hòa âm BGM điện ảnh (Auto-Ducking) & hiệu ứng âm thanh...", flush=True)

                sound_mixer.mix_scene_audio(

                    dialogue_master_wav=dialogue_master,

                    bgm_mood=sc_data.get("bgm_mood", "tense_investigation"),

                    sfx_cues=sc_data.get("sfx_cues", []),

                    output_master_wav=master_wav

                )

            else:

                print(f"[ÂM THANH] Phát hiện scene_master_audio.wav ({master_wav.stat().st_size / 1024:.1f} KB), tái sử dụng.", flush=True)



        print(f"\n[BƯỚC 3/3] Tạo hình ảnh, chuyển động máy quay & chèn phụ đề phân vai ({subtitle_style}, {subtitle_size or 52}px)...", flush=True)

        # MUSE_CONTINUITY_V1: pass the previous real screenplay beat into the next render.
        if image_provider == "muse_video" and sc_idx > 1:
            from .scene_continuity import continuity_instruction
            sc_data = dict(sc_data)
            sc_data["continuity_context"] = continuity_instruction(scenes_data[sc_idx - 2], sc_data)

        max_scene_retries = 3
        last_scene_exc = None
        for attempt in range(1, max_scene_retries + 1):
            try:
                video_res = video_engine.render_scene(
                    scene=sc_data,
                    scene_dir=sc_dir,
                    aspect_ratio=aspect_ratio,
                    cast_map=cast_map,
                    reference_image_path=anchor_ref,
                    image_provider=image_provider,
                    bible=bible,
                    width=width,
                    height=height,
                    subtitle_style=subtitle_style,
                    subtitle_size=subtitle_size,
                    no_subtitles=no_subtitles
                )
                scene_video = Path(video_res["final_video_path"])
                if image_provider == "muse_video":
                    try:
                        from .scene_continuity import extract_last_frame
                        extract_last_frame(scene_video, sc_dir / "continuity_last_frame.jpg")
                    except Exception as frame_exc:
                        print(f"[CONTINUITY_QA_WARN] Cannot save tail frame: {frame_exc}", flush=True)
                print(f"SCENE_PASS {sc_num}", flush=True)
                return sc_num, scene_video
            except Exception as render_err:
                last_scene_exc = render_err
                print(f"[CẢNH {sc_num:02d}] ⚠️ Sự cố dựng cảnh (Lần {attempt}/{max_scene_retries}): {render_err}", flush=True)
                if attempt < max_scene_retries:
                    try:
                        for partial_f in [sc_dir / "scene_final.mp4", sc_dir / "muse_clip.mp4", sc_dir / "muse_job.json"]:
                            if partial_f.is_file() and partial_f.stat().st_size < 100000:
                                partial_f.unlink()
                    except Exception:
                        pass
                    retry_wait = 5 * attempt
                    print(f"[CẢNH {sc_num:02d}] 🔄 Tự động thử lại cảnh sau {retry_wait}s...", flush=True)
                    time.sleep(retry_wait)
        raise RuntimeError(f"Cảnh {sc_num:02d} không thể hoàn thành sau {max_scene_retries} lần thử: {last_scene_exc}")



    # Determine concurrency

    configured_workers = max(1, min(int(getattr(args, "workers", 1) or 1), 3))

    if image_provider == "muse_video":

        try:

            import muse_accounts

            ready_accs = muse_accounts.get_ready_accounts()

            if len(ready_accs) >= 2:

                configured_workers = min(len(ready_accs), max(configured_workers, len(ready_accs)))

        except Exception:

            pass



    print(f"\n=======================================================", flush=True)

    print(f"🎬 SẢN XUẤT {len(scenes_data)} PHÂN CẢNH (Số luồng Muse song song: {configured_workers})...", flush=True)

    print(f"=======================================================", flush=True)



    # MUSE_CONTINUITY_V1: require preceding clip to finish before next starts.
    if image_provider == "muse_video":
        configured_workers = 1
        print("[CONTINUITY] Muse sequential continuity enabled (workers=1).", flush=True)

    # 1. SCENE 1: Always rendered first to establish visual actor anchor

    first_sc = scenes_data[0]

    sc1_num = first_sc.get("scene_number", 1)

    print(f"[NEO NHÂN VẬT] 🎯 Đang dựng Cảnh 1 để chốt diện mạo và trang phục nhân vật chuẩn...", flush=True)

    _, sc1_video = render_single_scene(1, first_sc, anchor_ref=None)



    anchor_ref = (scenes_root / "scene_0001" / "scene_base.png")

    if not anchor_ref.exists():

        anchor_ref = (scenes_root / "scene_001" / "scene_base.png")

    if not anchor_ref.exists():

        anchor_ref = None

    else:

        print(f"[NEO NHÂN VẬT] ✅ Đã chốt khuôn mặt diễn viên mỏ neo ({anchor_ref.name}).", flush=True)



    produced_dict = {sc1_num: sc1_video}

    with bridge_lock:

        export_legacy_compatibility_bridge(

            episode_dir, raw_plan, [sc1_video], None,

            image_provider=image_provider,

            subtitle_style=subtitle_style,

            subtitle_size=subtitle_size

        )



    # 2. REMAINING SCENES: Run concurrently across multiple accounts!

    remaining_scenes = list(enumerate(scenes_data[1:], start=2))

    if remaining_scenes:

        if configured_workers > 1:

            print(f"\n⚡ [ĐA LUỒNG SONG SONG] Kích hoạt {configured_workers} luồng xử lý đồng thời cho {len(remaining_scenes)} cảnh còn lại...", flush=True)

            with concurrent.futures.ThreadPoolExecutor(max_workers=configured_workers) as pool:

                futures = {

                    pool.submit(render_single_scene, sc_idx, sc_d, anchor_ref): sc_idx

                    for sc_idx, sc_d in remaining_scenes

                }

                for fut in concurrent.futures.as_completed(futures):

                    sc_curr_num = futures[fut]

                    try:

                        s_num, s_vid = fut.result()

                        produced_dict[s_num] = s_vid

                        with bridge_lock:

                            curr_ordered = [produced_dict[s.get("scene_number", i)] for i, s in enumerate(scenes_data, 1) if s.get("scene_number", i) in produced_dict]

                            export_legacy_compatibility_bridge(

                                episode_dir, raw_plan, curr_ordered, None,

                                image_provider=image_provider,

                                subtitle_style=subtitle_style,

                                subtitle_size=subtitle_size

                            )

                    except Exception as scene_err:

                        print(f"[CẢNH {sc_curr_num}] ❌ Lỗi dựng cảnh: {scene_err}", flush=True)

        else:

            for sc_idx, sc_d in remaining_scenes:

                try:

                    s_num, s_vid = render_single_scene(sc_idx, sc_d, anchor_ref)

                    produced_dict[s_num] = s_vid

                    with bridge_lock:

                        curr_ordered = [produced_dict[s.get("scene_number", i)] for i, s in enumerate(scenes_data, 1) if s.get("scene_number", i) in produced_dict]

                        export_legacy_compatibility_bridge(

                            episode_dir, raw_plan, curr_ordered, None,

                            image_provider=image_provider,

                            subtitle_style=subtitle_style,

                            subtitle_size=subtitle_size

                        )

                except Exception as scene_err:

                    print(f"[CẢNH {sc_d.get('scene_number', sc_idx)}] ❌ Lỗi dựng cảnh: {scene_err}", flush=True)



    # Kiểm tra toàn bộ cảnh đã hoàn tất trước khi tiến hành ghép phim

    missing_nums = [s.get("scene_number", i) for i, s in enumerate(scenes_data, 1) if s.get("scene_number", i) not in produced_dict]

    # MUSE_CONTINUITY_V1: blank three-second filler is not a valid film scene.
    if missing_nums and image_provider == "muse_video":
        raise RuntimeError(f"MUSE_CONTINUITY_MISSING_SCENES: {missing_nums}. Preserve all existing clips and retry failed scenes; do not insert black fillers.")

    if missing_nums:
        print(f"\n[BẢO VỆ TIẾN ĐỘ] ⚠️ Có {len(missing_nums)} cảnh chưa hoàn thành sau các lần thử lại (Cảnh: {missing_nums}).", flush=True)
        print(f"[BẢO VỆ TIẾN ĐỘ] 🛠️ Tự động tạo clip chuyển cảnh an toàn (3s) để KHÔNG LÀM DỪNG TIẾN TRÌNH CẢ TẬP...", flush=True)
        for m_num in missing_nums:
            m_dir = scenes_root / f"scene_{m_num:04d}"
            if not m_dir.exists():
                m_dir = scenes_root / f"scene_{m_num:03d}"
            if not m_dir.exists():
                m_dir = scenes_root / f"scene_{m_num}"
            m_dir.mkdir(parents=True, exist_ok=True)
            bridge_mp4 = m_dir / "scene_final.mp4"
            if not bridge_mp4.is_file() or bridge_mp4.stat().st_size < 1000:
                base_img = m_dir / "scene_base.png"
                if not base_img.is_file():
                    try:
                        from PIL import Image
                        Image.new("RGB", (width, height), (10, 15, 29)).save(base_img, format="PNG")
                    except Exception:
                        pass
                try:
                    cmd_b = [
                        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                        "-loop", "1", "-i", str(base_img.resolve()),
                        "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
                        "-t", "3", "-pix_fmt", "yuv420p", "-c:v", "libx264", "-c:a", "aac",
                        "-shortest", str(bridge_mp4.resolve())
                    ]
                    subprocess.run(cmd_b, check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                except Exception as b_err:
                    print(f"[CẢNH {m_num}] Không thể tạo bridge clip: {b_err}", flush=True)
            if bridge_mp4.is_file():
                produced_dict[m_num] = bridge_mp4
                print(f"[CẢNH {m_num}] ⏭️ Đã tự động chèn clip cầu nối (3s) để bảo toàn tiến trình tập phim.", flush=True)



    # Assemble final list in exact scene order

    produced_scene_videos = [produced_dict[s.get("scene_number", i)] for i, s in enumerate(scenes_data, 1)]



    # 4. Final Episode Concatenation

    print(f"\n=======================================================", flush=True)

    print(f"EPISODE_CONCAT_START", flush=True)

    print(f"🎞️ ĐANG NỐI CÁC PHÂN CẢNH THÀNH PHIM HOÀN CHỈNH...", flush=True)

    print(f"=======================================================", flush=True)



    episode_final_mp4 = episode_dir / f"episode_{episode_num:03d}_final.mp4"

    concatenate_scene_videos(produced_scene_videos, episode_final_mp4)



    # 4.1 Tự động gắn Call-to-Action (Nút Sub, Like, Chuông) đa điểm: Xuất hiện từ phút đầu & định kỳ mỗi 2.5 phút
    enable_cta = getattr(args, "enable_cta", True)
    if enable_cta:
        try:
            from .drama_cta_overlay import apply_cta_overlay_to_video
            apply_cta_overlay_to_video(
                input_video_path=episode_final_mp4,
                output_video_path=episode_final_mp4,
                aspect_ratio=aspect_ratio,
                cta_duration=4.5
            )
        except Exception as cta_err:
            print(f"[CTA_WARN] Bỏ qua gắn CTA: {cta_err}", flush=True)



    ep_size_mb = episode_final_mp4.stat().st_size / (1024 * 1024)

    from .drama_audio_engine import get_wav_duration

    # Measure episode duration with ffprobe

    cmd = [

        "ffprobe", "-v", "quiet", "-print_format", "json",

        "-show_format", str(episode_final_mp4)

    ]

    ep_duration = 0.0

    try:

        res = subprocess.run(cmd, capture_output=True, text=True, check=True)

        ep_duration = float(json.loads(res.stdout)["format"]["duration"])

    except Exception:

        pass



    # 5. Create 100% Studio Compatibility Bridge (Scene Gallery, SEO Packager, YouTube Uploader)

    export_legacy_compatibility_bridge(

        episode_dir, raw_plan, produced_scene_videos, episode_final_mp4,

        image_provider=image_provider,

        subtitle_style=subtitle_style,

        subtitle_size=subtitle_size

    )



    # 6. Automatically generate complete vidIQ SEO publishing package and 50/50 Rule of Thirds thumbnail

    try:

        from seo_packager import generate_seo_package

        print("[SEO] Đang tự động phân tích video kịch và tạo bộ SEO YouTube vidIQ 100/100 + Ảnh Thumbnail HD...", flush=True)

        seo_data = generate_seo_package(

            episode_dir=episode_dir,

            series_name=str(raw_plan.get("series_name") or getattr(args, "series", "Cinematic Drama")),

            episode_num=int(raw_plan.get("episode_num") or getattr(args, "episode", 1)),

            language=str(raw_plan.get("language") or getattr(args, "language", "Vietnamese")),

            genre=str(raw_plan.get("genre") or getattr(args, "genre", "drama")),

            include_shorts=getattr(args, "with_shorts", False),

            force_regenerate=True,

        )

        print(f"[SEO] Đã tạo thành công bộ SEO vidIQ cho tập {raw_plan.get('episode_num', 1)}! Điểm vidIQ: {seo_data.get('vidiq_score', {}).get('total_score', 100)}/100", flush=True)

    except Exception as seo_err:

        print(f"[SEO_WARN] Không thể tự động tạo gói SEO: {seo_err}", flush=True)



    print(f"\n🎉 HOÀN THÀNH TẬP PHIM KỊCH ĐIỆN ẢNH!", flush=True)

    print(f"   Tên tập: {raw_plan.get('title')}", flush=True)

    print(f"   Đường dẫn: {episode_final_mp4}", flush=True)

    print(f"   Thời lượng: {ep_duration:.2f} giây (~{ep_duration / 60:.1f} phút)", flush=True)

    print(f"   Dung lượng: {ep_size_mb:.2f} MB", flush=True)

    print(f"   Số phân cảnh: {len(produced_scene_videos)} cảnh đối thoại sống động", flush=True)

    print(f"EPISODE_RESULT {json.dumps({'path': str(episode_final_mp4.resolve())})}", flush=True)

    print(f"   Số phân cảnh: {len(produced_scene_videos)} cảnh đối thoại sống động")

    print(f"   Tương thích Studio: Đã đồng bộ Gallery, SEO Packager & YouTube Manager\n", flush=True)



    return 0





def export_legacy_compatibility_bridge(

    episode_dir: Path,

    raw_plan: Dict[str, Any],

    scene_videos: Optional[List[Path]] = None,

    final_episode_mp4: Optional[Path] = None,

    image_provider: str = "muse_video",

    subtitle_style: str = "karaoke_viral",

    subtitle_size: int = 0

):

    """Bridges Cinematic Drama output with legacy Studio features:

    Scene Gallery, SEO Packager, YouTube Uploader, and Monitor Video Player.

    """

    import shutil

    from .drama_audio_engine import get_wav_duration



    scene_videos = scene_videos or []



    # 1. Provide episode_final.mp4 link/copy

    legacy_ep_final = episode_dir / "episode_final.mp4"

    if final_episode_mp4 and final_episode_mp4.exists():

        try:

            shutil.copy2(str(final_episode_mp4), str(legacy_ep_final))

        except Exception:

            pass



    # 2. Build legacy scenes and sync media files

    scenes_dir = episode_dir / "scenes"

    scenes_dir.mkdir(parents=True, exist_ok=True)

    legacy_scenes = []

    scenes_data = raw_plan.get("scenes", [])



    for idx, sc in enumerate(scenes_data, 1):

        sc_num = sc.get("scene_number", idx)

        sc_dir = scenes_dir / f"scene_{sc_num:04d}"

        if not sc_dir.exists():

            if (scenes_dir / f"scene_{sc_num:03d}").exists():

                sc_dir = scenes_dir / f"scene_{sc_num:03d}"

            else:

                sc_dir.mkdir(parents=True, exist_ok=True)



        beats = sc.get("dialogue_beats", [])

        narration_text = "\n".join([f"{b.get('speaker', '')}: {b.get('text', '')}" for b in beats])



        base_png = sc_dir / "scene_base.png"

        img_png = sc_dir / "image.png"

        if base_png.exists() and not img_png.exists():

            try:

                shutil.copy2(str(base_png), str(img_png))

            except Exception:

                pass



        master_audio = sc_dir / "scene_master_audio.wav"

        if not master_audio.exists():

            master_audio = sc_dir / "dialogue_master.wav"

        audio_wav = sc_dir / "audio.wav"

        if master_audio.exists() and not audio_wav.exists():

            try:

                shutil.copy2(str(master_audio), str(audio_wav))

            except Exception:

                pass



        scene_mp4 = sc_dir / "scene_final.mp4"

        final_mp4 = sc_dir / "final.mp4"

        if scene_mp4.exists() and not final_mp4.exists():

            try:

                shutil.copy2(str(scene_mp4), str(final_mp4))

            except Exception:

                pass



        dur = 30.0

        if master_audio.exists():

            dur = get_wav_duration(master_audio)



        is_scene_done = (

            (final_mp4.exists() and final_mp4.stat().st_size > 1000) or

            (scene_mp4.exists() and scene_mp4.stat().st_size > 1000)

        )



        # Write result.json and job.json for QC and Gallery

        result_json = sc_dir / "result.json"

        if is_scene_done:

            result_payload = {"status": "PASS", "qc": {"duration_seconds": dur, "duration": dur}}

            result_json.write_text(json.dumps(result_payload, ensure_ascii=False), encoding="utf-8")

        elif not result_json.exists():

            result_payload = {"status": "PENDING", "qc": {}}

            result_json.write_text(json.dumps(result_payload, ensure_ascii=False), encoding="utf-8")



        job_json = sc_dir / "job.json"

        job_payload = {

            "scene_number": sc_num,

            "summary": sc.get("summary", ""),

            "title": sc.get("summary", ""),

            "text_overlay": sc.get("summary", ""),

            "narration": narration_text,

            "visual_setup": sc.get("visual_setup", ""),

            "description": sc.get("visual_setup", "") or sc.get("description", ""),

            "subtitle_style": subtitle_style,

            "subtitle_size": subtitle_size

        }

        job_json.write_text(json.dumps(job_payload, ensure_ascii=False), encoding="utf-8")



        legacy_scenes.append({

            "scene_number": sc_num,

            "summary": sc.get("summary", ""),

            "title": sc.get("summary", ""),

            "narration": narration_text,

            "visual_setup": sc.get("visual_setup", ""),

            "description": sc.get("visual_setup", "") or sc.get("description", ""),

            "characters_present": sc.get("characters_present", [])

        })



    # 3. Write plan.json

    legacy_plan = {

        "config": {

            "series": raw_plan.get("series_name", "Cinematic Drama"),

            "episode": raw_plan.get("episode_num", 1),

            "language": raw_plan.get("language", "Vietnamese"),

            "genre": raw_plan.get("genre", "drama"),

            "production_mode": "cinematic_drama",

            "image_provider": image_provider,

            "subtitle_style": subtitle_style,

            "subtitle_size": subtitle_size,

            "prompt": raw_plan.get("prompt") or raw_plan.get("title", ""),

            "input_mode": raw_plan.get("input_mode", "idea")

        },

        "title": raw_plan.get("title", ""),

        "logline": raw_plan.get("logline", ""),

        "scenes": legacy_scenes

    }

    plan_json = episode_dir / "plan.json"

    plan_json.write_text(json.dumps(legacy_plan, indent=2, ensure_ascii=False), encoding="utf-8")

