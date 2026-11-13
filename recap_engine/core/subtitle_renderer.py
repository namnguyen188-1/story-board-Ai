"""
Subtitle Renderer for Movie Recap Engine.
Generates styled Advanced SubStation Alpha (.ass) files with cinema-grade typography:
- Automatic short chunking (3-5 words per screen) for fast-paced viral recap pacing
- Real progressive Karaoke effect with ASS \\k tags synchronized to voiceover
- Pixel-perfect custom positioning from UI drag coordinates (\\pos(X, Y))
- Scaled font size matching canvas preview accurately
- Safe margins for TikTok/Reels/Shorts UI overlay protection
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import re


ASS_TEMPLATE = """[Script Info]
Title: Movie Recap Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
PlayResX: {res_x}
PlayResY: {res_y}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: RecapDefault,{font_name},{font_size},{primary_color},{secondary_color},{outline_color},&H80000000,{bold},0,0,0,100,100,0,0,{border_style},{outline_width},{shadow_depth},{alignment},{margin_l},{margin_r},{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def hex_to_ass_color(hex_str: str) -> str:
    """Converts #RRGGBB hex color to ASS format &H00BBGGRR&."""
    clean = hex_str.lstrip("#").strip()
    if len(clean) == 6:
        r, g, b = clean[0:2], clean[2:4], clean[4:6]
        return f"&H00{b.upper()}{g.upper()}{r.upper()}&"
    return "&H0015CCFA&"  # Default gold yellow


def format_ass_time(seconds: float) -> str:
    """Converts seconds into ASS time format H:MM:SS.cs"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int(round((seconds - int(seconds)) * 100))
    if cs >= 100:
        cs = 99
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def split_into_chunks(text: str, max_words: int = 4) -> List[List[str]]:
    """
    Splits long sentences into bite-sized 3-5 word chunks.
    Avoids lone single-word orphaned lines.
    """
    words = text.strip().split()
    if not words:
        return []
    if len(words) <= 5:
        return [words]

    chunks = []
    i = 0
    while i < len(words):
        rem = len(words) - i
        if rem == 5:
            take = 3
        elif rem in (2, 3, 4):
            take = rem
        elif rem == 1:
            if chunks:
                chunks[-1].extend(words[i:])
                break
            take = 1
        else:
            take = min(max_words, rem)
        chunks.append(words[i:i+take])
        i += take
    return chunks


class SubtitleRenderer:
    """Builds cinema-grade ASS subtitles for video rendering matching UI drag coordinates."""

    def __init__(
        self,
        aspect_ratio: str = "16:9",
        font_name: str = "Montserrat",
        font_size: Optional[int] = None,
        color_hex: str = "#facc15",
        pos_x_pct: float = 50.0,
        pos_y_pct: float = 90.0,
        sub_style: str = "karaoke_box"
    ):
        self.aspect_ratio = aspect_ratio
        if aspect_ratio == "9:16":
            self.res_x = 1080
            self.res_y = 1920
            scale_factor = 1.45
        elif aspect_ratio == "1:1":
            self.res_x = 1080
            self.res_y = 1080
            scale_factor = 1.25
        else:  # 16:9
            self.res_x = 1920
            self.res_y = 1080
            scale_factor = 1.35

        ui_size = int(font_size) if font_size else 24
        self.scaled_font_size = max(20, int(ui_size * scale_factor))

        clean_font = font_name.replace("'", "").replace('"', '').split(",")[0].strip()
        self.font_name = clean_font if clean_font else "Montserrat"
        self.highlight_color = hex_to_ass_color(color_hex)
        self.outline_color = "&H00000000&"
        self.shadow_depth = 2.0
        self.alignment = 5  # 5 = Middle Center for exact \pos(X, Y)

        # Hỗ trợ 100% hộp đen che phụ đề gốc cho cả Karaoke và Chữ Tĩnh
        if sub_style in ("box", "karaoke_box"):
            self.border_style = 3  # 100% Opaque solid background box to cover original subtitles
            self.outline_color = "&H00000000&"  # Pure solid black (&H00BBGGRR& -> alpha=00 is 100% opaque)
            self.outline_width = 12.0  # Box padding rộng rãi đảm bảo che phủ kín phụ đề gốc
            self.primary_color = self.highlight_color
            self.secondary_color = "&H00FFFFFF&"
        elif sub_style == "outline":
            self.border_style = 1
            self.outline_width = 5.2
            self.primary_color = "&H00FFFFFF&"
            self.secondary_color = "&H00FFFFFF&"
        else:
            self.border_style = 1
            self.outline_width = 4.2
            self.primary_color = self.highlight_color
            self.secondary_color = "&H00FFFFFF&"

        # Compute exact pixel coordinates from percentage
        self.pos_x_px = int(self.res_x * (float(pos_x_pct) / 100.0))
        self.pos_y_px = int(self.res_y * (float(pos_y_pct) / 100.0))
        self.sub_style = sub_style

    def generate_ass(self, segments: List[Dict[str, Any]], output_ass_path: str) -> str:
        """
        Creates an .ass subtitle file from timed segments.
        Splits long sentences into 3-5 word chunks with synchronized \\k karaoke highlighting.
        Burned-in coordinates match exact UI drag positions via \\pos(X, Y).
        """
        out_file = Path(output_ass_path).resolve()
        out_file.parent.mkdir(parents=True, exist_ok=True)

        header = ASS_TEMPLATE.format(
            res_x=self.res_x,
            res_y=self.res_y,
            font_name=self.font_name,
            font_size=self.scaled_font_size,
            primary_color=self.primary_color,
            secondary_color=self.secondary_color,
            outline_color=self.outline_color,
            bold=-1,
            border_style=self.border_style,
            outline_width=self.outline_width,
            shadow_depth=self.shadow_depth,
            alignment=self.alignment,
            margin_l=20,
            margin_r=20,
            margin_v=20
        )

        events = []
        for seg in segments:
            seg_start = float(seg.get("timeline_start", 0.0))
            seg_end = float(seg.get("timeline_end", 0.0))
            seg_dur = max(0.4, seg_end - seg_start)
            raw_text = seg.get("text", "").strip()

            # Clean up text for ASS
            text = raw_text.replace("{", "(").replace("}", ")").replace("\n", " ").strip()
            if not text:
                continue

            chunks = split_into_chunks(text, max_words=4)
            if not chunks:
                continue

            total_chars = max(1, sum(len(w) for chunk in chunks for w in chunk))
            cur_time = seg_start

            for c_idx, chunk in enumerate(chunks):
                chunk_chars = sum(len(w) for w in chunk)
                if c_idx == len(chunks) - 1:
                    chunk_end = seg_end
                    chunk_dur = max(0.2, chunk_end - cur_time)
                else:
                    chunk_dur = seg_dur * (chunk_chars / total_chars)
                    chunk_end = cur_time + chunk_dur

                start_t = format_ass_time(cur_time)
                end_t = format_ass_time(chunk_end)

                if self.sub_style in ("karaoke", "karaoke_box"):
                    # Build progressive \k tags: each word lights up as it's spoken
                    total_cs = max(10, int(round(chunk_dur * 100)))
                    tagged_words = []
                    accum_cs = 0
                    for w_idx, w in enumerate(chunk):
                        if w_idx == len(chunk) - 1:
                            w_cs = max(1, total_cs - accum_cs)
                        else:
                            w_cs = max(1, int(round(total_cs * (len(w) / max(1, chunk_chars)))))
                            accum_cs += w_cs
                        tagged_words.append(f"{{\\k{w_cs}}}{w}")
                    chunk_display = " ".join(tagged_words)
                else:
                    chunk_display = " ".join(chunk)

                line = f"Dialogue: 0,{start_t},{end_t},RecapDefault,,0,0,0,,{{\\pos({self.pos_x_px},{self.pos_y_px})}}{chunk_display}"
                events.append(line)
                cur_time = chunk_end

        content = header + "\n".join(events) + "\n"
        out_file.write_text(content, encoding="utf-8")
        return str(out_file)
