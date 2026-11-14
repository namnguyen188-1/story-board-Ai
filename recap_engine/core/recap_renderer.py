"""
Recap Video Renderer.
Slices source movie, applies Fair-Use transformations, concatenates footage,
mixes Gemini TTS voiceover with BGM auto-ducking, and burns ASS subtitles.
"""

from pathlib import Path
import sys
import subprocess
import shutil
import tempfile
import time
from typing import List, Dict, Any, Optional, Callable

WIN_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0

try:
    from .ffmpeg_utils import get_ffmpeg_path, check_nvenc_available
    from .fair_use_fx import (
        build_fair_use_video_filter, get_target_dimensions,
        build_watermark_drawtext, build_cta_drawtext,
        compute_cta_times, get_cta_asset_path, build_cta_chromakey_filter
    )
except (ImportError, ValueError):
    from core.ffmpeg_utils import get_ffmpeg_path, check_nvenc_available
    from core.fair_use_fx import (
        build_fair_use_video_filter, get_target_dimensions,
        build_watermark_drawtext, build_cta_drawtext,
        compute_cta_times, get_cta_asset_path, build_cta_chromakey_filter
    )


class RecapRenderer:
    """Orchestrates video rendering for movie recap output."""

    def __init__(self):
        self.ffmpeg = get_ffmpeg_path()
        self.use_nvenc = check_nvenc_available()

    def render_recap_video(
        self,
        source_video: str,
        timeline_cuts: List[Dict[str, Any]],
        voice_files: List[str],
        subtitle_ass_file: Optional[str] = None,
        bgm_file: Optional[str] = None,
        output_file: str = "recap_final.mp4",
        aspect_ratio: str = "16:9",
        vertical_style: str = "blurred_background",
        speed_factor: float = 1.04,
        ken_burns: bool = True,
        film_grain: bool = True,
        hflip: bool = False,
        watermark_text: Optional[str] = None,
        watermark_size: int = 38,
        watermark_color: str = "gold",
        watermark_motion: str = "floating",
        cta_overlay: bool = True,
        cta_text: Optional[str] = None,
        movie_audio_vol: float = 0.10,
        bgm_volume: float = 0.15,
        export_srt: bool = True,
        export_thumbnails: bool = True,
        progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> str:
        """
        Renders complete movie recap video.
        """
        out_path = Path(output_file).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)

        work_dir = Path(tempfile.mkdtemp(prefix="recap_render_"))

        try:
            total_cuts = len(timeline_cuts)
            slice_files = []

            # 1. Video filter for each slice
            v_filter = build_fair_use_video_filter(
                aspect_ratio=aspect_ratio,
                vertical_style=vertical_style,
                speed_factor=speed_factor,
                ken_burns=ken_burns,
                film_grain=film_grain,
                hflip=hflip
            )

            v_codec = "h264_nvenc" if self.use_nvenc else "libx264"
            target_w, target_h = get_target_dimensions(aspect_ratio)

            # 2. Slice cuts in parallel (4 workers GPU accelerated)
            import concurrent.futures
            import threading
            completed_slices = 0
            slice_lock = threading.Lock()

            def process_slice(item):
                nonlocal completed_slices
                idx, cut = item
                slice_path = work_dir / f"slice_{idx:04d}.mp4"

                target_dur = float(cut["duration"])
                exact_frames = max(1, int(round(target_dur * 30.0)))

                # Khớp 100% thời lượng với giọng đọc TTS:
                # Nếu có tăng tốc Fair-Use (speed_factor != 1.0), phải đọc thêm nguồn = target_dur * speed_factor + đệm
                # để sau khi chạy filter setpts=(1/speed_factor)*PTS, thời lượng video thành phẩm KHÔNG BỊ HỤT!
                if abs(speed_factor - 1.0) > 0.001:
                    src_read_dur = round(target_dur * speed_factor + 0.2, 4)
                else:
                    src_read_dur = round(target_dur + 0.2, 4)

                slice_v_filter = f"{v_filter},fps=30" if "fps=30" not in v_filter else v_filter

                # Cấu hình âm thanh gốc của phim (Ambience):
                if movie_audio_vol > 0.001:
                    a_filters = ["aresample=48000"]
                    if abs(speed_factor - 1.0) > 0.001:
                        a_filters.append(f"atempo={speed_factor:.4f}")
                    audio_slice_args = [
                        "-af", ",".join(a_filters),
                        "-c:a", "aac",
                        "-b:a", "128k",
                        "-ac", "2"
                    ]
                else:
                    audio_slice_args = ["-an"]

                cmd_slice = [
                    self.ffmpeg, "-y",
                    "-ss", str(cut["source_start"]),
                    "-t", f"{src_read_dur:.4f}",
                    "-i", str(source_video),
                    "-vf", slice_v_filter,
                    "-frames:v", str(exact_frames),
                    "-c:v", v_codec,
                    "-pix_fmt", "yuv420p",
                    "-r", "30"
                ] + audio_slice_args + [
                    str(slice_path)
                ]

                res = subprocess.run(cmd_slice, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=WIN_NO_WINDOW)
                if res.returncode != 0:
                    # Fallback to libx264 if nvenc failed
                    if v_codec == "h264_nvenc":
                        cmd_fallback = list(cmd_slice)
                        cmd_fallback[cmd_fallback.index("h264_nvenc")] = "libx264"
                        res = subprocess.run(cmd_fallback, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=WIN_NO_WINDOW)

                    if res.returncode != 0:
                        raise RuntimeError(f"Lỗi cắt video phân đoạn {idx+1}: {res.stderr.decode('utf-8', errors='replace')}")

                with slice_lock:
                    completed_slices += 1
                    if progress_callback:
                        pct = (completed_slices / max(1, total_cuts)) * 0.5  # 0% - 50%
                        progress_callback(f"Đang trích xuất cảnh {completed_slices}/{total_cuts} (GPU Turbo)...", round(pct * 100, 1))

                return (idx, slice_path)

            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                items = list(enumerate(timeline_cuts))
                results = list(executor.map(process_slice, items))

            results.sort(key=lambda x: x[0])
            slice_files = [r[1] for r in results]

            # 3. Concatenate video slices
            if progress_callback:
                progress_callback("Đang nối các trích đoạn video...", 55.0)

            concat_list = work_dir / "concat_slices.txt"
            concat_lines = [f"file '{p.as_posix()}'" for p in slice_files]
            concat_list.write_text("\n".join(concat_lines), encoding="utf-8")

            raw_video_path = work_dir / "raw_concat_video.mp4"
            cmd_concat = [
                self.ffmpeg, "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_list),
                "-c", "copy",
                str(raw_video_path)
            ]
            subprocess.run(cmd_concat, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=WIN_NO_WINDOW)

            # 4. Assemble Voice Audio Track (Chuẩn hóa PCM WAV để triệt tiêu hoàn toàn delay đệm MP3)
            if progress_callback:
                progress_callback("Đang ghép nối dải âm thanh giọng đọc (Zero-drift)...", 65.0)

            # Giải mã từng câu voice sang PCM 48kHz WAV trung gian để ghép nối không một mili-giây độ trễ
            wav_files = []
            for v_idx, v_path in enumerate(voice_files):
                w_path = work_dir / f"voice_{v_idx:04d}.wav"
                cmd_wav = [
                    self.ffmpeg, "-y",
                    "-i", str(v_path),
                    "-ar", "48000",
                    "-ac", "2",
                    "-c:a", "pcm_s16le",
                    str(w_path)
                ]
                subprocess.run(cmd_wav, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True, creationflags=WIN_NO_WINDOW)
                wav_files.append(w_path)

            voice_concat_list = work_dir / "concat_voice.txt"
            voice_lines = [f"file '{Path(p).resolve().as_posix()}'" for p in wav_files]
            voice_concat_list.write_text("\n".join(voice_lines), encoding="utf-8")

            master_voice_path = work_dir / "master_voice.wav"
            cmd_voice = [
                self.ffmpeg, "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(voice_concat_list),
                "-c:a", "pcm_s16le",
                str(master_voice_path)
            ]
            subprocess.run(cmd_voice, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=WIN_NO_WINDOW)

            # 5. Final Assembly: Video + Master Voice + BGM Auto-Ducking + Subtitles + Watermark + Chromakey CTA
            if progress_callback:
                progress_callback("Đang dập phụ đề, hiệu ứng CTA và xuất bản phẩm hoàn thiện...", 75.0)

            # Determine video duration for CTA scheduling
            total_dur = 0.0
            try:
                ffprobe_path = Path(self.ffmpeg).parent / ("ffprobe.exe" if sys.platform == "win32" else "ffprobe")
                cmd_probe = [
                    str(ffprobe_path), "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    str(raw_video_path)
                ]
                p_res = subprocess.run(cmd_probe, capture_output=True, text=True, creationflags=WIN_NO_WINDOW)
                total_dur = float(p_res.stdout.strip())
            except Exception:
                total_dur = sum(float(c.get("end", 0)) - float(c.get("start", 0)) for c in timeline_cuts)
                if speed_factor and abs(speed_factor - 1.0) > 0.01:
                    total_dur /= speed_factor

            inputs = ["-i", str(raw_video_path), "-i", str(master_voice_path)]
            next_idx = 2

            # CTA Chromakey setup
            cta_input_idx = None
            cta_times = []
            cta_asset = get_cta_asset_path() if cta_overlay else None
            if cta_overlay and cta_asset and cta_asset.is_file():
                cta_times = compute_cta_times(total_dur, is_vertical=(aspect_ratio == "9:16"))
                if cta_times:
                    cta_input_idx = next_idx
                    inputs.extend(["-i", str(cta_asset)])
                    next_idx += 1

            # BGM setup
            bgm_input_idx = None
            if bgm_file and Path(bgm_file).is_file():
                bgm_input_idx = next_idx
                inputs.extend(["-stream_loop", "-1", "-i", str(bgm_file)])
                next_idx += 1

            # Filter complex constructions
            fc_parts = []
            curr_v = "0:v"

            # Step 5A: Subtitle and Watermark
            base_vf = []
            if subtitle_ass_file and Path(subtitle_ass_file).is_file():
                escaped_sub = Path(subtitle_ass_file).as_posix().replace(":", r"\:")
                base_vf.append(f"ass='{escaped_sub}'")

            if watermark_text:
                wm_f = build_watermark_drawtext(
                    text=watermark_text,
                    font_size=watermark_size,
                    color_scheme=watermark_color,
                    motion_type=watermark_motion,
                    aspect_ratio=aspect_ratio
                )
                if wm_f:
                    base_vf.append(wm_f)

            # Fallback text CTA if video asset is missing
            if cta_overlay and not cta_input_idx:
                cta_f = build_cta_drawtext(
                    text=cta_text or "🔔 ĐĂNG KÝ KÊNH • BẤM LIKE & CHIA SẺ",
                    font_size=32 if aspect_ratio != "9:16" else 28,
                    aspect_ratio=aspect_ratio
                )
                if cta_f:
                    base_vf.append(cta_f)

            if base_vf:
                fc_parts.append(f"[{curr_v}]{','.join(base_vf)}[v_base]")
                curr_v = "v_base"

            # Step 5B: Chromakey CTA Overlay (Transparent Green Screen)
            if cta_input_idx is not None and cta_times:
                target_w, _ = get_target_dimensions(aspect_ratio)
                cta_clauses, out_v_tag = build_cta_chromakey_filter(
                    cta_idx=cta_input_idx,
                    times=cta_times,
                    base_stream=curr_v,
                    target_w=target_w,
                    is_vertical=(aspect_ratio == "9:16")
                )
                fc_parts.extend(cta_clauses)
                curr_v = out_v_tag

            # Step 5C: Audio Mixing (Voice 100% + Movie Ambience + BGM + CTA SFX)
            has_movie_audio = (movie_audio_vol > 0.001)
            a_inputs_list = []

            # Voice is always index 1
            fc_parts.append("[1:a]volume=1.0[v_voice]")
            a_inputs_list.append("[v_voice]")

            # Movie original ambience
            if has_movie_audio:
                fc_parts.append(f"[0:a]volume={movie_audio_vol:.2f}[v_movie]")
                a_inputs_list.append("[v_movie]")

            # Background music
            if bgm_input_idx is not None:
                fc_parts.append(f"[{bgm_input_idx}:a]volume={bgm_volume:.2f}[v_bgm]")
                a_inputs_list.append("[v_bgm]")

            # CTA Sound Effects (Whoosh, Pop, Bell Chime)
            if cta_input_idx is not None and cta_times:
                try:
                    if len(cta_times) == 1:
                        fc_parts.append(f"[{cta_input_idx}:a]adelay={int(cta_times[0]*1000)}|{int(cta_times[0]*1000)},volume=0.85[cta_a_0]")
                        a_inputs_list.append("[cta_a_0]")
                    elif len(cta_times) > 1:
                        asplit_tags = "".join([f"[cta_as_{k}]" for k in range(len(cta_times))])
                        fc_parts.append(f"[{cta_input_idx}:a]asplit={len(cta_times)}{asplit_tags}")
                        for k, t_sec in enumerate(cta_times):
                            fc_parts.append(f"[cta_as_{k}]adelay={int(t_sec*1000)}|{int(t_sec*1000)},volume=0.85[cta_a_{k}]")
                            a_inputs_list.append(f"[cta_a_{k}]")
                except Exception as _cta_err:
                    logger.warning(f"Could not add CTA SFX audio: {_cta_err}")

            if len(a_inputs_list) > 1:
                fc_parts.append(
                    f"{''.join(a_inputs_list)}amix=inputs={len(a_inputs_list)}:duration=first:dropout_transition=2[a_out]"
                )
                audio_map_tag = "[a_out]"
            else:
                audio_map_tag = "1:a"

            # Build command arguments
            filter_complex_str = ";".join(fc_parts)
            if filter_complex_str:
                v_audio_args = [
                    "-filter_complex", filter_complex_str,
                    "-map", f"[{curr_v}]" if not curr_v.startswith("[") else curr_v,
                    "-map", audio_map_tag
                ]
            else:
                v_audio_args = [
                    "-map", "0:v",
                    "-map", "1:a"
                ]

            cmd_final = [
                self.ffmpeg, "-y"
            ] + inputs + v_audio_args + [
                "-c:v", v_codec,
                "-c:a", "aac",
                "-b:a", "192k",
                "-pix_fmt", "yuv420p",
                str(out_path)
            ]

            res_final = subprocess.run(cmd_final, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=WIN_NO_WINDOW)
            if res_final.returncode != 0:
                # Fallback to libx264 if nvenc failed
                if v_codec == "h264_nvenc":
                    idx_v = cmd_final.index("h264_nvenc")
                    cmd_final[idx_v] = "libx264"
                    res_final = subprocess.run(cmd_final, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=WIN_NO_WINDOW)

                if res_final.returncode != 0:
                    raise RuntimeError(f"Lỗi xuất video hoàn thiện: {res_final.stderr.decode('utf-8', errors='replace')}")

            # Step 6: Tự động xuất file phụ đề rời .SRT & .ASS (Tính năng 4)
            if export_srt and subtitle_ass_file and Path(subtitle_ass_file).is_file():
                try:
                    target_ass = out_path.with_suffix(".ass")
                    shutil.copy2(subtitle_ass_file, target_ass)
                    target_srt = out_path.with_suffix(".srt")
                    cmd_conv_srt = [
                        self.ffmpeg, "-y",
                        "-i", str(subtitle_ass_file),
                        str(target_srt)
                    ]
                    subprocess.run(cmd_conv_srt, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=WIN_NO_WINDOW)
                except Exception as e:
                    print(f"[RECAP_RENDERER_WARN] Export SRT error: {e}", flush=True)

            # Step 7: Tự động trích xuất 3 ảnh Thumbnail HD (Tính năng 7)
            if export_thumbnails:
                try:
                    dur_for_thumb = max(10.0, total_dur)
                    thumb_points = [
                        round(dur_for_thumb * 0.25, 2),
                        round(dur_for_thumb * 0.55, 2),
                        round(dur_for_thumb * 0.85, 2)
                    ]
                    for idx_th, th_time in enumerate(thumb_points, 1):
                        thumb_file = out_path.parent / f"{out_path.stem}_thumb_{idx_th}.jpg"
                        cmd_thumb = [
                            self.ffmpeg, "-y",
                            "-ss", str(th_time),
                            "-i", str(raw_video_path),
                            "-vf", "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,eq=contrast=1.12:saturation=1.15",
                            "-vframes", "1",
                            "-q:v", "2",
                            str(thumb_file)
                        ]
                        subprocess.run(cmd_thumb, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=WIN_NO_WINDOW)
                except Exception as e:
                    print(f"[RECAP_RENDERER_WARN] Export Thumbnail error: {e}", flush=True)

            if progress_callback:
                progress_callback("Hoàn thành xuất video!", 100.0)

            return str(out_path)

        finally:
            try:
                shutil.rmtree(work_dir, ignore_errors=True)
            except Exception:
                pass
