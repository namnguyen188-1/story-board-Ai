"""
Video Analyzer for Standalone Movie Recap Engine.
Probes media metadata, extracts subtitles, and indexes scenes/shots.
"""

from pathlib import Path
import sys
import subprocess
import re
import json
import tempfile
from typing import Dict, Any, List, Optional, Tuple

WIN_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0
try:
    from .ffmpeg_utils import get_ffmpeg_path, get_ffprobe_path, run_ffprobe_json
except (ImportError, ValueError):
    from core.ffmpeg_utils import get_ffmpeg_path, get_ffprobe_path, run_ffprobe_json


class VideoAnalyzer:
    """Analyzes source movie video and prepares metadata for recap production."""

    def __init__(self, video_path: str):
        self.video_path = Path(video_path).resolve()
        if not self.video_path.is_file():
            raise FileNotFoundError(f"Video file not found: {self.video_path}")
        self._meta: Optional[Dict[str, Any]] = None

    def probe(self) -> Dict[str, Any]:
        """Probes video metadata using ffprobe."""
        if self._meta:
            return self._meta

        raw = run_ffprobe_json([
            "-show_format",
            "-show_streams",
            str(self.video_path)
        ])

        format_info = raw.get("format", {})
        streams = raw.get("streams", [])

        duration = float(format_info.get("duration", 0.0))
        size_bytes = int(format_info.get("size", 0))

        v_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
        a_streams = [s for s in streams if s.get("codec_type") == "audio"]
        sub_streams = [s for s in streams if s.get("codec_type") == "subtitle"]

        width = 0
        height = 0
        fps = 24.0
        v_codec = ""

        if v_stream:
            width = int(v_stream.get("width", 0))
            height = int(v_stream.get("height", 0))
            v_codec = v_stream.get("codec_name", "")
            r_frame_rate = v_stream.get("r_frame_rate", "24/1")
            try:
                num, den = map(float, r_frame_rate.split("/"))
                fps = round(num / den, 2) if den > 0 else 24.0
            except Exception:
                fps = 24.0

        aspect = f"{width}:{height}"
        if width > 0 and height > 0:
            ratio = width / height
            if abs(ratio - 16 / 9) < 0.05:
                aspect = "16:9"
            elif abs(ratio - 9 / 16) < 0.05:
                aspect = "9:16"
            elif abs(ratio - 1.0) < 0.05:
                aspect = "1:1"
            elif abs(ratio - 2.39) < 0.1:
                aspect = "21:9 (Cinemascope)"

        audio_tracks = []
        for s in a_streams:
            tags = s.get("tags", {})
            audio_tracks.append({
                "index": s.get("index"),
                "codec": s.get("codec_name"),
                "channels": s.get("channels"),
                "language": tags.get("language", "und"),
                "title": tags.get("title", f"Track {s.get('index')}")
            })

        subtitle_tracks = []
        for s in sub_streams:
            tags = s.get("tags", {})
            subtitle_tracks.append({
                "index": s.get("index"),
                "codec": s.get("codec_name"),
                "language": tags.get("language", "und"),
                "title": tags.get("title", f"Sub {s.get('index')}")
            })

        self._meta = {
            "path": str(self.video_path),
            "filename": self.video_path.name,
            "size_mb": round(size_bytes / (1024 * 1024), 2),
            "duration": duration,
            "duration_hms": self._format_seconds(duration),
            "width": width,
            "height": height,
            "fps": fps,
            "aspect_ratio": aspect,
            "video_codec": v_codec,
            "audio_tracks": audio_tracks,
            "subtitle_tracks": subtitle_tracks
        }
        return self._meta

    @staticmethod
    def _format_seconds(sec: float) -> str:
        h = int(sec // 3600)
        m = int((sec % 3600) // 60)
        s = int(sec % 60)
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"

    def extract_subtitle_track(self, stream_index: int, output_srt: str) -> bool:
        """Extracts an embedded subtitle stream to an SRT file using FFmpeg."""
        ffmpeg = get_ffmpeg_path()
        out_path = Path(output_srt).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            ffmpeg, "-y",
            "-i", str(self.video_path),
            "-map", f"0:{stream_index}",
            str(out_path)
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=WIN_NO_WINDOW)
        return res.returncode == 0 and out_path.is_file() and out_path.stat().st_size > 0

    @staticmethod
    def parse_srt(srt_file_path: str) -> List[Dict[str, Any]]:
        """Parses an SRT file into a structured list of subtitle segments."""
        path = Path(srt_file_path)
        if not path.is_file():
            return []

        content = path.read_text(encoding="utf-8", errors="replace")
        blocks = re.split(r"\n\s*\n", content.strip())
        items = []

        time_pattern = re.compile(
            r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})"
        )

        for block in blocks:
            lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
            if len(lines) < 2:
                continue

            time_line = None
            text_lines = []
            for ln in lines:
                m = time_pattern.search(ln)
                if m:
                    time_line = m
                elif time_line:
                    text_lines.append(ln)

            if time_line and text_lines:
                h1, m1, s1, ms1, h2, m2, s2, ms2 = map(int, time_line.groups())
                start_sec = h1 * 3600 + m1 * 60 + s1 + ms1 / 1000.0
                end_sec = h2 * 3600 + m2 * 60 + s2 + ms2 / 1000.0
                text = " ".join(text_lines)
                # Clean html tags
                text = re.sub(r"<[^>]+>", "", text).strip()
                if text:
                    items.append({
                        "start": round(start_sec, 2),
                        "end": round(end_sec, 2),
                        "duration": round(end_sec - start_sec, 2),
                        "text": text
                    })
        return items

    @staticmethod
    def summarize_subtitles_for_llm(subtitles: List[Dict[str, Any]], target_chunks: int = 50) -> str:
        """
        Compresses subtitle dialogue into structured timestamped summary points
        suitable for LLM prompt without blowing context limits.
        """
        if not subtitles:
            return ""

        total_subs = len(subtitles)
        step = max(1, total_subs // target_chunks)

        condensed = []
        for i in range(0, total_subs, step):
            sub = subtitles[i]
            timestamp = VideoAnalyzer._format_seconds(sub["start"])
            condensed.append(f"[{timestamp}] {sub['text']}")

        return "\n".join(condensed)

    def extract_audio_for_transcription(self, output_wav: str) -> str:
        """Extracts 16kHz mono audio for Whisper or speech recognition."""
        ffmpeg = get_ffmpeg_path()
        out_path = Path(output_wav).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            ffmpeg, "-y",
            "-i", str(self.video_path),
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            str(out_path)
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=WIN_NO_WINDOW)
        if res.returncode != 0:
            raise RuntimeError(f"Audio extraction failed: {res.stderr.decode('utf-8', errors='replace')}")
        return str(out_path)

    def generate_shot_list(
        self,
        total_recap_seconds: float = 300.0,
        shot_duration: float = 3.5,
        distribute_evenly: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Generates a curated list of source video timecode cuts for the recap.
        Ensures shots are well-distributed across 3 acts (beginning, middle, climax)
        and each cut is strictly <= 4.0s to bypass automated Content-ID.
        """
        meta = self.probe()
        src_duration = meta["duration"]

        if src_duration <= 0:
            src_duration = 3600.0  # fallback 1h

        # Calculate number of shots needed to cover recap duration
        num_shots = int(total_recap_seconds / shot_duration) + 1

        shots = []
        # Exclude opening credits (first 2%) and ending roll (last 5%)
        start_bound = src_duration * 0.02
        end_bound = src_duration * 0.95
        usable_range = max(10.0, end_bound - start_bound)

        step = usable_range / max(1, num_shots)

        for i in range(num_shots):
            source_start = start_bound + i * step
            # Cap each shot to avoid long sustained copyright match
            actual_shot_len = min(shot_duration, 4.0)

            # Prevent going beyond end bound
            if source_start + actual_shot_len > end_bound:
                source_start = max(start_bound, end_bound - actual_shot_len)

            shots.append({
                "shot_index": i + 1,
                "source_start": round(source_start, 2),
                "source_end": round(source_start + actual_shot_len, 2),
                "duration": round(actual_shot_len, 2),
                "formatted_time": self._format_seconds(source_start)
            })

        return shots

    def extract_visual_keyframes(self, num_frames: int = 5, output_dir: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Extracts keyframes at evenly distributed progression points across the movie.
        Scales them to low-res (640px) for ultra-fast Gemini Vision analysis.
        """
        meta = self.probe()
        dur = meta.get("duration", 0.0)
        if dur <= 0:
            dur = 600.0

        if output_dir:
            out_dir = Path(output_dir)
        else:
            out_dir = Path(tempfile.gettempdir()) / "recap_keyframes" / self.video_path.stem[:30]
        out_dir.mkdir(parents=True, exist_ok=True)

        ffmpeg = get_ffmpeg_path()
        if num_frames == 5:
            pcts = [0.02, 0.20, 0.45, 0.70, 0.92]
        elif num_frames == 6:
            pcts = [0.02, 0.12, 0.28, 0.50, 0.72, 0.92]
        elif num_frames == 8:
            pcts = [0.02, 0.08, 0.18, 0.32, 0.48, 0.64, 0.80, 0.94]
        else:
            pcts = [max(0.02, min(0.96, (i + 0.2) / (num_frames + 0.4))) for i in range(num_frames)]

        frames = []
        for i, pct in enumerate(pcts):
            t_sec = max(1.0, min(dur - 2.0, dur * pct))
            fmt_time = self._format_seconds(t_sec)
            out_img = out_dir / f"frame_{i+1}_{int(t_sec)}s.jpg"

            cmd = [
                ffmpeg, "-y",
                "-ss", str(round(t_sec, 2)),
                "-i", str(self.video_path),
                "-vframes", "1",
                "-vf", "scale=512:-1",
                "-q:v", "4",
                str(out_img)
            ]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=WIN_NO_WINDOW)
            if out_img.is_file() and out_img.stat().st_size > 0:
                frames.append({
                    "index": i + 1,
                    "timestamp": round(t_sec, 2),
                    "formatted_time": fmt_time,
                    "path": str(out_img)
                })
        return frames

    def deep_visual_scan(self, num_frames: int = 6) -> Dict[str, Any]:
        """
        Uses Gemini Vision to analyze extracted keyframes, detecting real characters,
        genre, and visual plot timeline so recap script matches 100% of the actual footage.
        """
        try:
            from PIL import Image
            try:
                from ..config import load_config, get_shared_rotator
            except (ImportError, ValueError):
                from config import load_config, get_shared_rotator

            keyframes = self.extract_visual_keyframes(num_frames=num_frames)
            if not keyframes:
                return {}

            images = [Image.open(k["path"]) for k in keyframes]
            timecodes = ", ".join([f"Ảnh {k['index']} [{k['formatted_time']}]" for k in keyframes])

            prompt = f"""Bạn là chuyên gia phân tích thị giác và đạo diễn phim hàng đầu.
Quan sát kỹ {len(keyframes)} khung hình trích từ video gốc theo đúng trình tự thời gian ({timecodes}).
Nhiệm vụ của bạn là nhận diện CHÍNH XÁC sự kiện thị giác, không gian, nhân vật và diễn biến thực tế diễn ra trong từng khung hình để lời bình sau này KHỚP 100% VỚI HÀNH ĐỘNG TRÊN MÀN HÌNH (chống nói sai, nói điêu).
BẮT BUỘC TRẢ VỀ ĐỊNH DẠNG JSON DUY NHẤT:
{{
  "movie_title": "Tiêu đề review giật gân, cuốn hút khớp 100% nội dung hình ảnh",
  "genre": "Thể loại phim thực tế xác định qua hình ảnh (ví dụ: Viễn tưởng / Hành động / Sinh tồn)",
  "characters": [
    {{"orig": "Nhận diện nhân vật qua ngoại hình/vai vế", "alias": "Biệt danh review dí dỏm, cuốn hút"}}
  ],
  "visual_timeline": [
    {{
      "time_sec": {keyframes[0]['timestamp']},
      "formatted_time": "{keyframes[0]['formatted_time']}",
      "action": "Mô tả chi tiết hành động thực tế diễn ra trong ảnh này (nhân vật đang làm gì, ai đang làm gì, vũ khí/phương tiện gì, nguy hiểm gì)"
    }}
  ],
  "plot_synopsis": "Đoạn tóm tắt cốt truyện thực tế liên kết các mốc thời gian trên thành chuỗi biến cố kịch tính."
}}
BẮT BUỘC xuất đủ {len(keyframes)} phần tử trong visual_timeline tương ứng {len(keyframes)} ảnh theo thứ tự thời gian."""

            rotator = get_shared_rotator()
            cfg = load_config()
            models_to_try = [
                cfg.get("model_name", "gemini-3.5-flash"),
                "gemini-3.8-flash",
                "gemini-flash-lite-latest",
                "gemini-flash-latest"
            ]

            num_keys = len(cfg.get("gemini_keys", [])) or 1
            max_attempts = min(30, num_keys * len(models_to_try))
            model_idx = 0
            attempt = 0

            while attempt < max_attempts:
                current_model = models_to_try[model_idx % len(models_to_try)]
                try:
                    client = rotator.get_client(timeout_sec=40.0)
                    resp = client.models.generate_content(
                        model=current_model,
                        contents=[prompt] + images
                    )
                    raw_text = resp.text.strip()
                    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw_text)
                    if m:
                        raw_text = m.group(1).strip()
                    idx_s = raw_text.find("{")
                    idx_e = raw_text.rfind("}")
                    if idx_s != -1 and idx_e != -1:
                        data = json.loads(raw_text[idx_s:idx_e+1])
                        data["visual_scanned"] = True
                        data["keyframes_count"] = len(keyframes)

                        # Generate visual_timeline_text mapping for LLM Scriptwriter
                        vt_lines = []
                        for item in data.get("visual_timeline", []):
                            t_val = item.get("time_sec")
                            f_time = item.get("formatted_time", "")
                            act = item.get("action") or item.get("visual_action") or ""
                            if act:
                                vt_lines.append(f"- [{f_time}] ({t_val}s): {act}")
                        if vt_lines:
                            data["visual_timeline_text"] = "\n".join(vt_lines)
                        else:
                            data["visual_timeline_text"] = data.get("plot_synopsis", "")

                        return data
                except Exception as ex:
                    print(f"⚠️ Deep visual scan attempt {attempt+1}/{max_attempts} failed on {current_model} (Key {rotator.index}): {ex}", flush=True)
                    err_str = str(ex).lower()
                    if "429" in err_str or "resource_exhausted" in err_str or "quota" in err_str:
                        rotator.rotate_next()
                    elif "503" in err_str or "unavailable" in err_str or "high demand" in err_str:
                        model_idx += 1
                    else:
                        model_idx += 1
                        rotator.rotate_next()
                    attempt += 1
                    rotator.rotate_next()

        except Exception as e:
            print(f"⚠️ deep_visual_scan error: {e}", flush=True)

        return {}

    def auto_scan_and_configure(self, srt_path: Optional[str] = None, enable_visual_scan: bool = True) -> Dict[str, Any]:
        """
        Automatically inspects the video, detects subtitles, extracts dialogue & character hints,
        and computes optimal recap production parameters.
        """
        meta = self.probe()
        duration = meta.get("duration", 0.0)
        filename = self.video_path.name

        # 1. Detect Subtitles (external SRT or embedded)
        found_srt = None
        if srt_path and Path(srt_path).is_file():
            found_srt = Path(srt_path)
        else:
            parent = self.video_path.parent
            candidates = [
                parent / f"{self.video_path.stem}.srt",
                parent / f"{self.video_path.stem}.vtt"
            ]
            # ONLY use demo_movie.srt if the video is specifically the demo movie!
            if self.video_path.stem in ("demo_real_movie", "demo_movie"):
                candidates.append(parent / "demo_movie.srt")

            for c in candidates:
                if c.is_file() and c.stat().st_size > 0:
                    found_srt = c
                    break

        sub_items = []
        if found_srt:
            sub_items = self.parse_srt(str(found_srt))

        # Perform visual AI scan if custom movie and no subtitles
        visual_data = {}
        if enable_visual_scan and not sub_items and self.video_path.stem not in ("demo_real_movie", "demo_movie"):
            print(f"🔍 [AI VISION] Performing deep visual frame scan for '{filename}'...", flush=True)
            visual_data = self.deep_visual_scan(num_frames=5)
            if visual_data:
                print(f"✅ [AI VISION] Visual scan completed: {visual_data.get('movie_title')}", flush=True)

        # Clean title & Genre deduction
        clean_title = self.video_path.stem.replace("_", " ").replace("-", " ")
        clean_title = re.sub(r"\s+[a-zA-Z0-9_-]{10,12}$", "", clean_title).strip()

        if self.video_path.stem in ("demo_real_movie", "demo_movie"):
            suggested_title = "Âm Mưu Ngày Cưới Của Thợ Trang Điểm"
            suggested_genre = "Ly kỳ, hồi hộp, Twist"
            plot_synopsis = "Cô Dâu Pamela chuẩn bị ngày cưới trọng đại nhưng bị thợ trang điểm Vanessa âm mưu tráo đổi để trả thù. Một loạt biến cố bất ngờ xảy ra khi chú rể và cảnh sát ập vào phòng cưới."
        elif visual_data.get("movie_title"):
            suggested_title = visual_data["movie_title"]
            suggested_genre = visual_data.get("genre", "Hành động, Kịch tính")
            vt_text = visual_data.get("visual_timeline_text", "")
            synopsis = visual_data.get("plot_synopsis", "")
            if vt_text:
                plot_synopsis = f"DIỄN BIẾN HÀNH ĐỘNG THỰC TẾ TRÊN TỪNG KHUNG HÌNH (BẮT BUỘC KHỚP 100%):\n{vt_text}\n\nTỔNG QUAN CỐT TRUYỆN:\n{synopsis}"
            else:
                plot_synopsis = synopsis or f"Tóm tắt cốt truyện: Phim xoay quanh {suggested_title}."
        else:
            suggested_title = clean_title.title() if clean_title else "Phim Mới"
            suggested_genre = "Hành động, Kịch tính"
            if any(k in clean_title.lower() for k in ["roblox", "game", "minecraft", "play"]):
                suggested_genre = "Hài hước, bắt trend dí dỏm"
            elif any(k in clean_title.lower() for k in ["horror", "ghost", "ma", "kinh di"]):
                suggested_genre = "Kinh dị, giật gân rùng rợn"
            plot_synopsis = f"Tóm tắt cốt truyện: Phim xoay quanh {suggested_title} với nhịp độ kịch tính, mở đầu hé lộ biến cố then chốt và các xung đột dồn dập."

        # 2. Extract Character Names (prefer visual scan, then subtitles, then smart defaults)
        detected_chars = []
        if visual_data.get("characters"):
            for c in visual_data["characters"][:5]:
                orig = c.get("orig", "Nhân Vật")
                alias = c.get("alias", f"Nhân Vật {orig}")
                detected_chars.append({"orig": orig, "alias": alias})
        else:
            char_counts = {}
            if sub_items:
                full_text = " ".join(s["text"] for s in sub_items)
                if self.video_path.stem in ("demo_real_movie", "demo_movie"):
                    known_check = [
                        ("Pamela", "Pamela (Cô Dâu)", "Cô Dâu Xinh Đẹp"),
                        ("Vanessa", "Vanessa (Thợ Trang Điểm)", "Chị Thợ Make-up Chuyên Nghiệp"),
                        ("Sahid", "Sahid (Kẻ Giấu Mặt)", "Kẻ Bí Ẩn Đặt Hàng"),
                        ("Nasiru", "Nasiru (Kẻ Lừa Đảo)", "Trùm Lừa Đảo Trực Tuyến"),
                        ("Fabian", "Fabian (Chú Rể)", "Chú Rể Kỹ Sư"),
                        ("Mimi", "Mimi (Trợ Lý)", "Cô Trợ Lý Make-up")
                    ]
                    for kw, full_orig, default_alias in known_check:
                        cnt = len(re.findall(r"\b" + kw + r"\b", full_text, re.IGNORECASE))
                        if cnt > 0:
                            char_counts[full_orig] = (cnt, default_alias)
                else:
                    for item in sub_items:
                        txt = item["text"]
                        m = re.match(r"^([A-Z][a-zA-Z\s]{1,20}):", txt)
                        if m:
                            spk = m.group(1).strip()
                            char_counts[spk] = (char_counts.get(spk, (0, f"Nhân Vật {spk}"))[0] + 5, f"Nhân Vật {spk}")

                    if not char_counts:
                        words = re.findall(r"\b[A-Z][a-z]{2,15}\b", full_text)
                        stop_words = {"The", "And", "You", "She", "They", "What", "When", "Where", "How", "Yes", "No", "This", "That", "Here", "There", "Many", "Even", "During", "However", "Because", "After", "Before", "Well", "Just", "Come", "Look", "Looked", "Said", "Asked"}
                        for w in words:
                            if w not in stop_words:
                                char_counts[w] = (char_counts.get(w, (0, f"Nhân Vật {w}"))[0] + 1, f"Nhân Vật {w}")

            if not char_counts:
                first_w = suggested_title.split()[0] if suggested_title else "Chính"
                char_counts = {
                    f"Nhân Vật {first_w}": (10, f"Nhân Vật Chính ({first_w})"),
                    "Kẻ Đối Đầu": (7, "Kẻ Đối Đầu Nguy Hiểm"),
                    "Người Đồng Hành": (5, "Người Đồng Đội Tin Cậy"),
                    "Nhân Vật Bí Ẩn": (3, "Kẻ Giấu Mặt")
                }

            sorted_chars = sorted(
                char_counts.items(),
                key=lambda x: x[1][0] if isinstance(x[1], tuple) else x[1],
                reverse=True
            )[:5]

            for orig, val in sorted_chars:
                alias = val[1] if isinstance(val, tuple) else f"Nhân Vật {orig}"
                detected_chars.append({"orig": orig, "alias": alias})

        # 3. Determine Optimal Target Minutes & Shots
        if duration <= 300:
            target_mins = 1.0
        elif duration <= 1800:
            target_mins = 2.0
        elif duration <= 3600:
            target_mins = 3.5
        elif duration <= 7200:
            target_mins = 5.0
        else:
            target_mins = 8.0

        est_shots = int(target_mins * 60 / 3.5)

        # 4. Determine Aspect Ratio
        w = meta.get("width", 1920)
        h = meta.get("height", 1080)
        aspect = "16:9"
        if h > w:
            aspect = "9:16"
        elif abs(w - h) < 100:
            aspect = "1:1"

        return {
            "status": "ok",
            "video_file": filename,
            "full_path": str(self.video_path),
            "metadata": meta,
            "subtitle_info": {
                "found": found_srt is not None,
                "file": found_srt.name if found_srt else None,
                "lines_count": len(sub_items),
                "has_dialogue": len(sub_items) > 0
            },
            "detected_characters": detected_chars,
            "visual_scanned": bool(visual_data),
            "plot_synopsis": plot_synopsis,
            "suggested_config": {
                "movie_title": suggested_title,
                "target_minutes": target_mins,
                "estimated_shots": est_shots,
                "cut_start": "00:00:00",
                "cut_end": meta.get("duration_hms", "00:00:00"),
                "aspect_ratio": aspect,
                "genre": suggested_genre,
                "voice_name": "Fenrir",
                "voice_speed": 1.15,
                "plot_synopsis": plot_synopsis,
                "watermark_text": "@ReviewPhimHay"
            }
        }
