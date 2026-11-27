"""Phase 3 Studio Integration & Regression Test Suite.

Directly imports wired modules in D:\\STORYBOARD_AI\\studio\\ to verify:
1. Legacy pipelines (English, Spanish, Vietnamese, Stoic, Drama) have ZERO regressions.
2. Japanese & Korean pipelines (modes, skills, voices, subtitles, ASS, word aligner,
   3D thumbnails, SEO quality, shot bank guards, YouTube BCP-47) work seamlessly end-to-end.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile

STUDIO_DIR = Path(r"D:\STORYBOARD_AI\studio")
ROOT_DIR = STUDIO_DIR.parent
for p in (str(STUDIO_DIR), str(ROOT_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import studio_modes
import story_skill_bridge
import thumbnail_studio
import seo_quality
import seo_packager
import youtube_manager
import series_studio
import cinematic_shot_bank
from engine.tools import video_subtitle, word_aligner


def _assert_monotonic_ass(ass_path: Path) -> None:
    prev_end = -1.0
    events = 0
    for line in ass_path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("Dialogue:"):
            continue
        events += 1
        parts = line.split(",", 3)
        def _sec(ts: str) -> float:
            h, m, s = ts.strip().split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
        st, en = _sec(parts[1]), _sec(parts[2])
        assert st < en, f"Invalid ASS timing: {line}"
        assert st >= prev_end - 0.02, f"Overlapping ASS timing ({prev_end} > {st}): {line}"
        prev_end = en
    assert events > 0, f"No dialogue events in {ass_path}"


def run_phase3_tests() -> None:
    # 1. Modes, Voices & Image Instructions (Legacy + East Asia)
    for k in ("stoic", "family_drama", "drama", "western", "whiteboard", "auto"):
        assert k in studio_modes.GENRES, f"Missing legacy genre: {k}"
    for k in ("jp_zen_story", "jp_edo_sleepless", "kr_yadam_joseon", "kr_sayeon_drama"):
        assert k in studio_modes.GENRES and k in studio_modes.ART, f"Missing EA genre: {k}"

    assert studio_modes.voice_for("Spanish", "stoic", "ES") == "Charon"
    assert studio_modes.voice_for("English", "western", "US") == "Fenrir"
    assert studio_modes.voice_for("Japanese", "jp_zen_story") == "Sulafat"
    assert studio_modes.voice_for("Korean", "kr_yadam_joseon") == "Gacrux"
    assert "Marcus Aurelius" in studio_modes.image_instruction("stoic", "color_cinematic")
    assert "#FFFFFF" in studio_modes.image_instruction("jp_zen_story", "colored_marker")
    print("PHASE3_1_MODES_VOICES_PASS")

    # 2. Skill Bridge Routing & Addenda
    assert story_skill_bridge.resolve_skill_name("stoic", aspect_ratio="16:9") == "write-video-scene-prompts"
    assert story_skill_bridge.resolve_skill_name("kr_sayeon_drama", aspect_ratio="16:9") == "write-video-scene-prompts"
    assert story_skill_bridge.resolve_skill_name("jp_zen_story", aspect_ratio="16:9") == "write-narrative-scene-prompts"
    assert story_skill_bridge.resolve_skill_name("jp_zen_story", aspect_ratio="9:16", is_short=True) == "write-viral-shorts-prompts"
    assert "EAST ASIA" not in story_skill_bridge.skill_prompt("stoic")
    assert "EAST ASIA GENRE ADDENDUM" in story_skill_bridge.skill_prompt("jp_zen_story")
    print("PHASE3_2_SKILL_BRIDGE_PASS")

    # 3. Subtitles + ASS + Word Aligner across ES/EN vs JP/KR
    with tempfile.TemporaryDirectory() as tmp:
        td = Path(tmp)

        # Spanish legacy check
        es_json = td / "es_sub.json"
        assert series_studio.subtitle_json({"narration": "Tu silencio impone respeto. No reacciones ante el insulto."}, 5.0, es_json)
        es_data = json.loads(es_json.read_text(encoding="utf-8"))
        assert es_data.get("subtitles") and not es_data.get("cjk_segmented")
        es_ass = video_subtitle.generate_styled_ass(str(es_json), str(td / "es.ass"), subtitle_style="karaoke_viral", language="Spanish")
        assert "Style: StudioSub,Arial," in Path(es_ass).read_text(encoding="utf-8")

        # Japanese wired check
        jp_json = td / "jp_sub.json"
        jp_narr = "本当に強い人は、侮辱されてもすぐには反応しません。沈黙が最大の武器です！"
        assert series_studio.subtitle_json({"narration": jp_narr}, 5.0, jp_json)
        jp_data = json.loads(jp_json.read_text(encoding="utf-8"))
        assert jp_data.get("cjk_segmented") is True and len(jp_data["subtitles"]) >= 3
        jp_ass = video_subtitle.generate_styled_ass(str(jp_json), str(td / "jp.ass"), subtitle_style="karaoke_viral", language="auto")
        assert "Style: StudioSub,Yu Gothic," in Path(jp_ass).read_text(encoding="utf-8")
        _assert_monotonic_ass(Path(jp_ass))

        # Korean wired check (9:16 vertical safe-zone)
        kr_json = td / "kr_sub.json"
        kr_narr = "정말 강한 사람은 모욕을 당해도 즉시 반응하지 않습니다."
        assert series_studio.subtitle_json({"narration": kr_narr}, 4.5, kr_json, is_vertical=True)
        kr_ass = video_subtitle.generate_styled_ass(
            str(kr_json), str(td / "kr.ass"), subtitle_style="karaoke_viral",
            video_width=720, video_height=1280, language="Korean"
        )
        assert "Style: StudioSub,Malgun Gothic," in Path(kr_ass).read_text(encoding="utf-8")
        _assert_monotonic_ass(Path(kr_ass))

        # Word aligner checks
        jp_aligned = word_aligner.chunk_words_into_subtitle_phrases([
            {"word": "本当に", "start": 0.1, "end": 0.4},
            {"word": "強い人は", "start": 0.41, "end": 0.8},
            {"word": "沈黙します。", "start": 0.81, "end": 1.3},
        ])
        assert jp_aligned and " " not in jp_aligned[0]["text"], jp_aligned
        en_aligned = word_aligner.chunk_words_into_subtitle_phrases([
            {"word": "Silence", "start": 0.1, "end": 0.4},
            {"word": "is", "start": 0.41, "end": 0.6},
            {"word": "power.", "start": 0.61, "end": 1.0},
        ])
        assert en_aligned and en_aligned[0]["text"] == "Silence is power."
    print("PHASE3_3_SUBTITLES_ALIGNER_PASS")

    # 4. 3D Thumbnails & Hook Splitting (Latin + CJK)
    assert seo_packager._parse_hook_lines("SILENCE / IS POWER", "stoic") == ["SILENCE", "IS POWER"]
    jp_hook = seo_packager._parse_hook_lines("沈黙が最大の武器", "jp_zen_story")
    assert len(jp_hook) == 2 and all(isinstance(x, str) and x for x in jp_hook), jp_hook

    im_latin = thumbnail_studio.render_tall_3d_viral_typography((1280, 720), ["SILENCE", "WINS"], (40, 80, 620, 640), genre="stoic")
    im_jp = thumbnail_studio.render_tall_3d_viral_typography((1280, 720), ["沈黙の力", "禅の教え"], (40, 80, 620, 640), genre="jp_zen_story")
    im_kr = thumbnail_studio.render_tall_3d_viral_typography((1280, 720), ["침묵의 힘", "조선야담"], (40, 80, 620, 640), genre="kr_yadam_joseon")
    for name, img in (("latin", im_latin), ("jp", im_jp), ("kr", im_kr)):
        assert img.getbbox() is not None, f"Empty 3D overlay for {name}"
    print("PHASE3_4_THUMBNAILS_PASS")

    # 5. SEO Quality, Shot Bank Isolation & YouTube BCP-47
    assert "Korean" in seo_quality.LOCALE and "Japanese" in seo_quality.LOCALE
    assert seo_quality.canonical_language("ko") == "Korean" and seo_quality.canonical_language("ja") == "Japanese"
    jp_ctx = {
        "language": "Japanese",
        "genre": "jp_zen_story",
        "title": "心の整理",
        "summary": "感情を乱されない習慣",
        "scenes": [{"narration": "本当に強い人は、侮辱されてもすぐには反応しません。", "summary": "沈黙の教え"}],
    }
    fb = seo_quality.fallback_content(jp_ctx)
    assert len(fb["titles"]) == 3 and all(seo_quality.words(t["title"]) for t in fb["titles"]), fb
    kept_short_jp = seo_quality.ensure_high_ctr_title(
        "沈黙が最大の武器である理由", "High-CTR", {"language": "Japanese", "genre": "jp_zen_story", "is_short": True}
    )
    assert "沈黙が最大の武器" in kept_short_jp and "#Shorts" in kept_short_jp, kept_short_jp
    es_stoic = seo_quality.ensure_high_ctr_title("Regla", "High-CTR", {"language": "Spanish", "genre": "stoic", "episode": 1})
    assert "ESTOICISMO" in es_stoic, es_stoic

    assert youtube_manager.normalize_language_code("Tiếng Nhật") == "ja"
    assert youtube_manager.normalize_language_code("Korean") == "ko"
    assert youtube_manager.to_youtube_bcp47("Japanese") == "ja"
    assert youtube_manager.to_youtube_bcp47("Korean") == "ko"

    # Guard ensures jp_zen_story / drama never trigger Stoic shot bank
    with tempfile.TemporaryDirectory() as tmp2:
        ep_dir = Path(tmp2)
        cinematic_shot_bank.ensure_shot_bank_and_montage(ep_dir, [{"scene_number": 1}], genre="jp_zen_story")
        assert not (ep_dir / "shot_bank").exists()
    print("PHASE3_5_SEO_OAUTH_SHOTBANK_PASS")
    print("ALL_PHASE3_STUDIO_WIRING_PASS")


if __name__ == "__main__":
    run_phase3_tests()
