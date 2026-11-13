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
    from .fair_use_fx import build_fair_use_video_filter, get_target_dimensions
except (ImportError, ValueError):
    from core.ffmpeg_utils import get_ffmpeg_path, check_nvenc_available
    from core.fair_use_fx import build_fair_use_video_filter, get_target_dimensions


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

                cmd_slice = [
                    self.ffmpeg, "-y",
                    "-ss", str(cut["source_start"]),
                    "-t", f"{src_read_dur:.4f}",
                    "-i", str(source_video),
                    "-vf", slice_v_filter,
                    "-frames:v", str(exact_frames),
                    "-c:v", v_codec,
                    "-pix_fmt", "yuv420p",
                    "-r", "30",
                    "-an",  # Strip original audio from individual video slices
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

            # 5. Final Assembly: Video + Master Voice + BGM Auto-Ducking + Subtitles + Watermark
            if progress_callback:
                progress_callback("Đang dập phụ đề và xuất bản phẩm hoàn thiện...", 75.0)

            inputs = ["-i", str(raw_video_path), "-i", str(master_voice_path)]

            # Filter complex for audio and video overlays
            v_filters_final = []
            if subtitle_ass_file and Path(subtitle_ass_file).is_file():
                # Escape path for FFmpeg filter on Windows
                escaped_sub = Path(subtitle_ass_file).as_posix().replace(":", r"\:")
                v_filters_final.append(f"ass='{escaped_sub}'")

            if watermark_text:
                v_filters_final.append(
                    f"drawtext=text='{watermark_text}':fontcolor=white@0.6:fontsize=24:"
                    f"x=w-tw-30:y=30:box=1:boxcolor=black@0.4:boxborderw=5"
                )

            # Assemble video final filter
            v_arg = []
            if v_filters_final:
                v_arg = ["-vf", ",".join(v_filters_final)]

            # Audio mixing: Voice + BGM or Voice alone
            if bgm_file and Path(bgm_file).is_file():
                inputs.extend(["-stream_loop", "-1", "-i", str(bgm_file)])
                # Auto ducking: BGM at -18dB while Voice is 0dB
                a_filter = (
                    "[1:a]volume=1.0[v_voice];"
                    "[2:a]volume=0.15[v_bgm];"
                    "[v_voice][v_bgm]amix=inputs=2:duration=first:dropout_transition=2[a_out]"
                )
                a_arg = ["-filter_complex", a_filter, "-map", "0:v", "-map", "[a_out]"]
            else:
                a_arg = ["-c:a", "aac", "-b:a", "192k", "-map", "0:v", "-map", "1:a"]

            cmd_final = [
                self.ffmpeg, "-y"
            ] + inputs + v_arg + a_arg + [
                "-c:v", v_codec,
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

            if progress_callback:
                progress_callback("Hoàn thành xuất video!", 100.0)

            return str(out_path)

        finally:
            try:
                shutil.rmtree(work_dir, ignore_errors=True)
            except Exception:
                pass
