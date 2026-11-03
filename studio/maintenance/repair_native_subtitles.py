"""Rebuild existing native-video captions without provider calls or publishing."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime

STUDIO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STUDIO))
sys.path.insert(0, str(STUDIO / "engine"))
os.environ["PATH"] = str(STUDIO / "engine" / "bin") + os.pathsep + os.environ.get("PATH", "")
from cinematic_engine.drama_video_engine import DramaVideoEngine, get_media_duration
from cinematic_engine.native_audio_subtitles import srt_time, atomic_json
from tools.video_subtitle import generate_styled_ass

def pcm_hash(path):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path),
                        "-map", "0:a:0", "-f", "hash", "-hash", "sha256", "-"],
                       capture_output=True, check=True)
    return r.stdout.strip().decode()

def main():
    episode = Path(sys.argv[1]).resolve()
    plan = json.loads((episode / "drama_plan.json").read_text(encoding="utf-8"))
    stage = Path(sys.argv[2]) if len(sys.argv) > 2 else episode / "_du_lieu_tam" / ("subtitle_sync_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    stage.mkdir(parents=True, exist_ok=True)
    atomic_json(episode / "subtitle_sync_status.json", {"state": "running", "stage": str(stage)})
    engine = DramaVideoEngine()
    videos, results, episode_subs, episode_words = [], [], [], []
    offset = 0.0
    for scene in plan["scenes"]:
        number = int(scene["scene_number"])
        original = episode / "scenes" / f"scene_{number:04d}"
        target = stage / "scenes" / original.name
        target.mkdir(parents=True, exist_ok=True)
        for name in ["muse_clip.mp4", "scene_base.png", "image.png", "job.json",
                     "native_audio_alignment.json", "render_style.json"]:
            if (original / name).is_file() and not (target / name).is_file():
                shutil.copy2(original / name, target / name)
        style = json.loads((original / "render_style.json").read_text(encoding="utf-8"))
        raw = target / "muse_clip.mp4"
        info = json.loads(subprocess.check_output(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height", "-of", "json", str(raw)]))["streams"][0]
        print(f"ALIGN_RENDER_START scene={number}", flush=True)
        rendered = engine.render_scene(scene, target, image_provider="muse_video",
            bible={"language": plan.get("language", "auto")},
            width=info["width"], height=info["height"],
            subtitle_style=style.get("subtitle_style", "karaoke_viral"),
            subtitle_size=int(style.get("subtitle_size", 0)),
            no_subtitles=style.get("no_subtitles", False))
        final = Path(rendered["final_video_path"])
        data = json.loads((target / "subtitles.json").read_text(encoding="utf-8"))
        assert data["timing_source"] == "native-audio-v1"
        assert pcm_hash(original / "muse_clip.mp4") == pcm_hash(final), "Native audio changed"
        duration = get_media_duration(final)
        assert abs(duration - get_media_duration(original / "muse_clip.mp4")) < 0.05
        generate_styled_ass(str(target / "subtitles.json"), str(target / "dialogue_subtitles.ass"),
            subtitle_style=style.get("subtitle_style", "karaoke_viral"),
            video_width=info["width"], video_height=info["height"],
            custom_font_size=int(style.get("subtitle_size", 0)), enable_stickers=False)
        for sub in data["subtitles"]:
            episode_subs.append({"start": offset + sub["start"], "end": offset + sub["end"], "text": sub["text"]})
        for word in data["words"]:
            episode_words.append({"start": offset + word["start"], "end": offset + word["end"], "text": word["word"]})
        results.append({"scene": number, "first_word": data["words"][0]["start"] if data["words"] else None,
                        "last_word": data["words"][-1]["end"] if data["words"] else None,
                        "words": len(data["words"]), "script_mismatch": data["script_mismatch"],
                        "transcript": data["transcript"], "expected_text": data["expected_text"],
                        "audio_hash_unchanged": True, "duration": duration})
        offset += duration
        videos.append(final)
        atomic_json(stage / "report.json", {"scenes": results, "state": "rendering"})
        print(f"ALIGN_RENDER_OK scene={number} words={len(data['words'])} first={results[-1]['first_word']} mismatch={data['script_mismatch']}", flush=True)
    from cinematic_engine.drama_orchestrator import concatenate_scene_videos
    from cinematic_engine.drama_cta_overlay import apply_cta_overlay_to_video
    final_episode = stage / "episode_subtitles_synced.mp4"
    concatenate_scene_videos(videos, final_episode, bgm_mood=plan.get("genre", "drama"))
    apply_cta_overlay_to_video(final_episode, final_episode, aspect_ratio="16:9", cta_duration=4.5)
    (stage / "episode_subtitles_synced.srt").write_text("\n".join(
        f"{i}\n{srt_time(s['start'])} --> {srt_time(s['end'])}\n{s['text']}\n"
        for i,s in enumerate(episode_subs, 1)), encoding="utf-8")
    # Additional word-accurate SRT for workflows requiring no future words on screen.
    # Keep the original grouped SRT for compatibility with existing editors.
    (stage / "episode_subtitles_synced.words.srt").write_text("\n".join(
        f"{i}\n{srt_time(w['start'])} --> {srt_time(w['end'])}\n{w['text']}\n"
        for i,w in enumerate(episode_words, 1)), encoding="utf-8")
    final_duration = get_media_duration(final_episode)
    assert abs(final_duration - offset) < 0.5, (final_duration, offset)
    atomic_json(stage / "report.json", {"scenes": results, "state": "ready_for_review",
        "stage": str(stage), "video": str(final_episode), "duration": final_duration,
        "expected_duration": offset})
    atomic_json(episode / "subtitle_sync_status.json", {"state": "ready_for_review", "stage": str(stage)})
    print("REBUILD_READY", stage, flush=True)

if __name__ == "__main__":
    main()
