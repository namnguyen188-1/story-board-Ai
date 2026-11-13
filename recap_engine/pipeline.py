"""
Full Movie Recap Pipeline Orchestrator.
Executes end-to-end automated movie recap production:
Video Analysis -> Scriptwriting -> Voiceover (Gemini TTS) -> Subtitling -> Fair-Use Video Rendering.
"""

from pathlib import Path
import json
import time
import re
from typing import Dict, Any, List, Optional, Callable

try:
    from .config import load_config, get_safe_export_dir
    from .core.video_analyzer import VideoAnalyzer
    from .core.scriptwriter import RecapScriptwriter
    from .core.voice_engine import RecapVoiceEngine
    from .core.subtitle_renderer import SubtitleRenderer
    from .core.timeline_builder import TimelineBuilder
    from .core.recap_renderer import RecapRenderer
except (ImportError, ValueError):
    from config import load_config, get_safe_export_dir
    from core.video_analyzer import VideoAnalyzer
    from core.scriptwriter import RecapScriptwriter
    from core.voice_engine import RecapVoiceEngine
    from core.subtitle_renderer import SubtitleRenderer
    from core.timeline_builder import TimelineBuilder
    from core.recap_renderer import RecapRenderer


class MovieRecapPipeline:
    """Master pipeline for producing automated movie recaps."""

    def __init__(self):
        self.config = load_config()
        self.scriptwriter = RecapScriptwriter()
        self.voice_engine = RecapVoiceEngine()
        self.renderer = RecapRenderer()

    def run(
        self,
        source_video: str,
        movie_title: str,
        genre: str = "Hành động, Kịch tính",
        target_minutes: int = 5,
        aspect_ratio: str = "16:9",
        vertical_style: str = "blurred_background",
        voice_name: Optional[str] = None,
        voice_speed: Optional[float] = None,
        user_aliases: Optional[Dict[str, str]] = None,
        subtitle_file: Optional[str] = None,
        subtitle_config: Optional[Dict[str, Any]] = None,
        custom_script: Optional[str] = None,
        bgm_file: Optional[str] = None,
        watermark_text: Optional[str] = None,
        watermark_size: int = 38,
        watermark_color: str = "gold",
        watermark_motion: str = "floating",
        cta_overlay: bool = True,
        cta_text: Optional[str] = None,
        language: str = "vi",
        output_filename: Optional[str] = None,
        progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> Dict[str, Any]:
        """
        Executes end-to-end recap generation.
        """
        t0 = time.time()
        export_dir = get_safe_export_dir(self.config.get("export_dir"))
        export_dir.mkdir(parents=True, exist_ok=True)

        session_id = f"recap_{int(time.time())}"
        session_dir = export_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        def report(msg: str, pct: float):
            if progress_callback:
                progress_callback(msg, pct)
            print(f"[{pct:.1f}%] {msg}", flush=True)

        # STAGE 1: Video Analysis & Subtitle Parsing
        report("Đang quét và bóc tách thông tin phim nguồn...", 5.0)
        analyzer = VideoAnalyzer(source_video)
        meta = analyzer.probe()

        plot_context = ""
        # Check if subtitle file provided or embedded subtitles exist
        if subtitle_file and Path(subtitle_file).is_file():
            report("Đang phân tích phụ đề SRT đính kèm...", 8.0)
            subs = analyzer.parse_srt(subtitle_file)
            plot_context = analyzer.summarize_subtitles_for_llm(subs)
        elif meta.get("subtitle_tracks"):
            first_sub = meta["subtitle_tracks"][0]
            extracted_srt = session_dir / "extracted_sub.srt"
            if analyzer.extract_subtitle_track(first_sub["index"], str(extracted_srt)):
                report("Đã trích xuất phụ đề gốc từ phim...", 10.0)
                subs = analyzer.parse_srt(str(extracted_srt))
                plot_context = analyzer.summarize_subtitles_for_llm(subs)
        else:
            report("Đang quét khung hình thị giác video gốc bằng AI Vision...", 9.0)
            try:
                vscan = analyzer.deep_visual_scan(num_frames=6)
                if vscan and vscan.get("plot_synopsis"):
                    vt_text = vscan.get("visual_timeline_text") or vscan["plot_synopsis"]
                    plot_context = f"DIỄN BIẾN HÀNH ĐỘNG THỰC TẾ TRÊN TỪNG KHUNG HÌNH (BẮT BUỘC KHỚP 100%):\n{vt_text}\n\nTỔNG QUAN:\n{vscan['plot_synopsis']}"
                    if not user_aliases and vscan.get("characters"):
                        user_aliases = {c["orig"]: c["alias"] for c in vscan["characters"] if isinstance(c, dict)}
            except Exception as e_v:
                print(f"⚠️ Visual scan error in pipeline: {e_v}", flush=True)

        # STAGE 2: 3-Act Scriptwriting via Gemini or Custom Script/Idea
        if custom_script and custom_script.strip() and not custom_script.strip().startswith("⏳"):
            raw_input = custom_script.strip()
            lines = [l.strip() for l in raw_input.splitlines() if l.strip()]
            if len(lines) >= 3 and any(len(l) > 20 for l in lines) and not any("đang tự động" in l for l in lines):
                report(f"Đang sử dụng kịch bản tùy chỉnh do bạn cung cấp ({len(lines)} phân đoạn)...", 20.0)
                segments = []
                for idx, line in enumerate(lines):
                    # Parse explicit scene timecode like [02:15] or (02:15) or [00:02:15]
                    m_tc = re.search(r'[\(\[]\s*(?:(\d{1,2}):)?(\d{1,2}):(\d{2})\s*[\)\]]', line)
                    source_time = None
                    if m_tc:
                        h_str, m_str, s_str = m_tc.groups()
                        h = int(h_str) if h_str else 0
                        m = int(m_str) if m_str else 0
                        s = int(s_str) if s_str else 0
                        source_time = h * 3600 + m * 60 + s

                    # Strip scene prefix and timecode for spoken voice
                    clean_line = re.sub(r'^(Cảnh\s*\d+[:\.\-]?|Hồi\s*\d+[:\.\-]?|\d+[\.\:\-])\s*', '', line, flags=re.I)
                    clean_line = re.sub(r'[\(\[]\s*(?:\d{1,2}:)?\d{1,2}:\d{2}\s*[\)\]]', '', clean_line)
                    clean_line = re.sub(r'^[\s:.\-]+', '', clean_line).strip()
                    if clean_line:
                        word_count = len(clean_line.split())
                        est_sec = max(2.5, round(word_count / 3.0, 1))
                        seg_item = {
                            "id": idx + 1,
                            "act": "body",
                            "text": clean_line,
                            "scene_mood": "suspense",
                            "film_pos_pct": round(idx / max(1, len(lines)), 2),
                            "est_duration": est_sec
                        }
                        if source_time is not None:
                            seg_item["source_time"] = float(source_time)
                        segments.append(seg_item)
                script_data = {
                    "title": movie_title,
                    "hook": segments[0]["text"] if segments else "",
                    "character_aliases": user_aliases or {},
                    "segments": segments,
                    "total_est_seconds": round(sum(s["est_duration"] for s in segments), 1),
                    "model_used": "custom_user_script"
                }
            else:
                report(f"Đang biên kịch 3 hồi theo ý tưởng của bạn: '{raw_input[:50]}...'...", 15.0)
                full_plot_context = f"Ý TƯỞNG CỐT TRUYỆN YÊU CẦU: {raw_input}\n\n{plot_context}".strip()
                script_data = self.scriptwriter.generate_recap_script(
                    movie_title=movie_title,
                    genre=genre,
                    target_minutes=target_minutes,
                    plot_context=full_plot_context,
                    user_aliases=user_aliases,
                    language=language
                )
        else:
            report(f"Đang biên kịch tóm tắt 3 hồi cho phim '{movie_title}'...", 15.0)
            script_data = self.scriptwriter.generate_recap_script(
                movie_title=movie_title,
                genre=genre,
                target_minutes=target_minutes,
                plot_context=plot_context,
                user_aliases=user_aliases,
                language=language
            )

        script_file = session_dir / "recap_script.json"
        script_file.write_text(json.dumps(script_data, indent=2, ensure_ascii=False), encoding="utf-8")
        report(f"Đã hoàn thành kịch bản ({len(script_data['segments'])} phân đoạn)!", 30.0)

        # STAGE 3: Gemini TTS Voiceover Generation
        report("Đang lồng tiếng thuyết minh qua Google Gemini TTS...", 35.0)
        voice_dir = session_dir / "voices"
        voice_dir.mkdir(parents=True, exist_ok=True)

        def voice_progress(cur, total, seg):
            pct = 35.0 + (cur / total) * 25.0  # 35% to 60%
            report(f"Đang tạo giọng đọc câu {cur}/{total}...", pct)

        segments = self.voice_engine.batch_generate(
            segments=script_data["segments"],
            output_dir=str(voice_dir),
            voice_name=voice_name or self.config.get("gemini_voice", "Fenrir"),
            speed=voice_speed or float(self.config.get("voice_speed", 1.15)),
            progress_callback=voice_progress
        )

        voice_files = [s["audio_file"] for s in segments]
        total_voice_duration = sum(s["duration"] for s in segments)

        # STAGE 4: Subtitles & Timeline Matching
        report("Đang tính toán timeline khớp hình và sinh phụ đề ASS...", 65.0)
        sub_cfg = subtitle_config or {}
        sub_renderer = SubtitleRenderer(
            aspect_ratio=aspect_ratio,
            font_name=sub_cfg.get("font_family", "Montserrat"),
            font_size=sub_cfg.get("font_size", 24),
            color_hex=sub_cfg.get("color", "#facc15"),
            pos_x_pct=float(sub_cfg.get("pos_x_pct", 50.0)),
            pos_y_pct=float(sub_cfg.get("pos_y_pct", 90.0)),
            sub_style=sub_cfg.get("style", "karaoke_box")
        )
        ass_path = session_dir / "recap_subtitles.ass"
        sub_renderer.generate_ass(segments, str(ass_path))

        timeline_builder = TimelineBuilder(
            source_duration=meta["duration"],
            max_clip_seconds=float(self.config.get("anti_content_id", {}).get("max_clip_seconds", 4.0))
        )
        timeline_cuts = timeline_builder.build_timeline(
            segments,
            subtitles=subs if 'subs' in locals() else None
        )

        timeline_file = session_dir / "timeline_cuts.json"
        timeline_file.write_text(json.dumps(timeline_cuts, indent=2, ensure_ascii=False), encoding="utf-8")

        # STAGE 5: Fair-Use Video Rendering
        final_filename = output_filename or f"recap_{Path(source_video).stem}_{aspect_ratio.replace(':', 'x')}.mp4"
        final_output_path = session_dir / final_filename

        def render_progress(msg, pct):
            mapped_pct = 70.0 + (pct / 100.0) * 28.0  # 70% to 98%
            report(msg, mapped_pct)

        anti_cfg = self.config.get("anti_content_id", {})
        rendered_path = self.renderer.render_recap_video(
            source_video=source_video,
            timeline_cuts=timeline_cuts,
            voice_files=voice_files,
            subtitle_ass_file=str(ass_path),
            bgm_file=bgm_file,
            output_file=str(final_output_path),
            aspect_ratio=aspect_ratio,
            vertical_style=vertical_style,
            speed_factor=float(anti_cfg.get("speed_factor", 1.04)),
            ken_burns=bool(anti_cfg.get("ken_burns_zoom", True)),
            film_grain=bool(anti_cfg.get("film_grain", True)),
            hflip=bool(anti_cfg.get("selective_flip", False)),
            watermark_text=watermark_text,
            watermark_size=watermark_size,
            watermark_color=watermark_color,
            watermark_motion=watermark_motion,
            cta_overlay=cta_overlay,
            cta_text=cta_text,
            progress_callback=render_progress
        )

        total_time = round(time.time() - t0, 1)
        report(f"🎉 Xuất video review thành công trong {total_time}s!", 100.0)

        return {
            "status": "success",
            "session_dir": str(session_dir),
            "video_path": rendered_path,
            "script": script_data,
            "duration": total_voice_duration,
            "total_render_time": total_time,
            "cuts_count": len(timeline_cuts)
        }
