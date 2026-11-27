"""CJK (Japanese & Korean) script detection, Windows font mapping, and safe wrapping."""
from __future__ import annotations

import os
from pathlib import Path
import re
from typing import List, Optional

_JA_KANA_RE = re.compile(r"[\u3040-\u30FF\u31F0-\u31FF]")
_KO_HANGUL_RE = re.compile(r"[\uAC00-\uD7AF\u1100-\u11FF\u3130-\u318F]")
_HAN_RE = re.compile(r"[\u4E00-\u9FFF]")

JP_FONT_CANDIDATES = (
    r"C:\Windows\Fonts\YuGothB.ttc",
    r"C:\Windows\Fonts\meiryob.ttc",
    r"C:\Windows\Fonts\YuGothM.ttc",
    r"C:\Windows\Fonts\msgothic.ttc",
    r"C:\Windows\Fonts\YuGothR.ttc",
)

KR_FONT_CANDIDATES = (
    r"C:\Windows\Fonts\malgunbd.ttf",
    r"C:\Windows\Fonts\malgun.ttf",
    r"C:\Windows\Fonts\gulim.ttc",
)

LATIN_FONT_CANDIDATES = (
    r"D:\STORYBOARD_AI\studio\web\fonts\Anton.ttf",
    r"D:\STORYBOARD_AI\studio\web\fonts\BebasNeue.ttf",
    r"C:\Windows\Fonts\ariblk.ttf",
    r"C:\Windows\Fonts\arialbd.ttf",
)


def contains_cjk(text: str) -> bool:
    s = str(text or "")
    return bool(_JA_KANA_RE.search(s) or _KO_HANGUL_RE.search(s) or _HAN_RE.search(s))


def detect_cjk_language(text: str, hint: Optional[str] = None) -> Optional[str]:
    """Returns 'Japanese', 'Korean', 'Chinese', or None based on script first, then hint."""
    s = str(text or "")
    if _JA_KANA_RE.search(s):
        return "Japanese"
    if _KO_HANGUL_RE.search(s):
        return "Korean"
    h = str(hint or "").strip().lower()
    if any(k in h for k in ("jap", "ja", "nhật", "nhat")):
        return "Japanese"
    if any(k in h for k in ("kor", "ko", "hàn", "han")):
        return "Korean"
    if _HAN_RE.search(s):
        if any(k in h for k in ("kor", "ko", "hàn", "han")):
            return "Korean"
        if any(k in h for k in ("jap", "ja", "nhật", "nhat")):
            return "Japanese"
        return "Chinese"
    return None


def resolve_cjk_font_path(text: str = "", language: Optional[str] = None, fallback: str = "") -> str:
    """Picks an installed Windows TrueType/Collection font supporting JP, KR, or Latin."""
    lang = detect_cjk_language(text, language)
    if lang == "Japanese":
        for p in JP_FONT_CANDIDATES:
            if os.path.isfile(p):
                return p
    elif lang == "Korean":
        for p in KR_FONT_CANDIDATES:
            if os.path.isfile(p):
                return p
    elif lang == "Chinese":
        for p in (r"C:\Windows\Fonts\msyhbd.ttc", r"C:\Windows\Fonts\simhei.ttf", *JP_FONT_CANDIDATES):
            if os.path.isfile(p):
                return p

    for p in LATIN_FONT_CANDIDATES:
        if os.path.isfile(p):
            return p
    if fallback and os.path.isfile(fallback):
        return fallback
    return r"C:\Windows\Fonts\arialbd.ttf"


def resolve_ass_font_name(text: str = "", language: Optional[str] = None) -> str:
    """Returns libass Fontname so subtitles never render tofu boxes on Japanese/Korean."""
    lang = detect_cjk_language(text, language)
    if lang == "Japanese":
        if os.path.isfile(r"C:\Windows\Fonts\YuGothB.ttc"):
            return "Yu Gothic"
        if os.path.isfile(r"C:\Windows\Fonts\meiryob.ttc"):
            return "Meiryo"
        return "MS Gothic"
    if lang == "Korean":
        if os.path.isfile(r"C:\Windows\Fonts\malgunbd.ttf") or os.path.isfile(r"C:\Windows\Fonts\malgun.ttf"):
            return "Malgun Gothic"
        return "Gulim"
    if lang == "Chinese":
        return "Microsoft YaHei"
    return "Arial"


def split_cjk_sentences(text: str) -> List[str]:
    """Splits Japanese, Korean, or mixed prose along CJK and ASCII sentence terminators."""
    raw = re.sub(r"\s+", " ", str(text or "").replace("\r", " ").replace("\n", " ")).strip()
    if not raw:
        return []

    parts = re.split(r"([。！？.!?]+(?:\s+|$)|[。！？])", raw)
    out: List[str] = []
    cur = ""
    for p in parts:
        if not p:
            continue
        cur += p
        if re.fullmatch(r"[。！？.!?]+\s*", p):
            s = cur.strip()
            if s:
                out.append(s)
            cur = ""
    if cur.strip():
        out.append(cur.strip())
    return out


def _split_long_spaceless_clause(clause: str, max_chars: int) -> List[str]:
    """Breaks long spaceless Japanese clauses smoothly on natural particles/chunks (respecting compound particles)."""
    s = clause.strip()
    if len(s) <= max_chars:
        return [s] if s else []

    pieces: List[str] = []
    buf = ""
    particle_breaks = set("はがをにでとのもへや、")
    no_start_chars = set("はがをにでとのもへや、。！？っゃゅょッャュョー")
    n = len(s)
    for idx, ch in enumerate(s):
        buf += ch
        nxt = s[idx + 1] if idx + 1 < n else ""
        # Never break right before a following particle/small-kana/punctuation (e.g. には, では, 反応しません。)
        can_break = nxt not in no_start_chars
        if can_break and len(buf) >= max(4, int(max_chars * 0.58)) and ch in particle_breaks:
            pieces.append(buf)
            buf = ""
        elif len(buf) >= max_chars and (can_break or len(buf) >= max_chars + 2):
            pieces.append(buf)
            buf = ""
    if buf:
        if pieces and len(buf) <= 2 and len(pieces[-1]) + len(buf) <= max_chars + 2:
            pieces[-1] += buf
        else:
            pieces.append(buf)
    return [p for p in pieces if p.strip()]


def chunk_cjk_text(text: str, is_vertical: bool = False, language: Optional[str] = None) -> List[str]:
    """Segments JP/KR narration into clean, balanced subtitle chunks (never overflowing canvas)."""
    max_chars = 10 if is_vertical else 16
    sentences = split_cjk_sentences(text)
    if not sentences:
        return []

    lang = detect_cjk_language(text, language)
    chunks: List[str] = []
    for sent in sentences:
        # Sub-split by commas / pause punctuation first
        subclauses = [c.strip() for c in re.split(r"(?<=[、,，;；:：])", sent) if c.strip()]
        for clause in subclauses:
            has_spaces = " " in clause and (lang == "Korean" or clause.count(" ") >= 2)
            if has_spaces:
                words = clause.split()
                cur_line = ""
                for w in words:
                    cand = f"{cur_line} {w}".strip() if cur_line else w
                    if len(cand) <= max_chars:
                        cur_line = cand
                    else:
                        if cur_line:
                            chunks.append(cur_line)
                        if len(w) > max_chars:
                            parts = _split_long_spaceless_clause(w, max_chars)
                            chunks.extend(parts[:-1])
                            cur_line = parts[-1] if parts else ""
                        else:
                            cur_line = w
                if cur_line:
                    chunks.append(cur_line)
            else:
                chunks.extend(_split_long_spaceless_clause(clause, max_chars))
    return [c.strip() for c in chunks if c.strip()]


def split_cjk_hook_lines(hook: str, max_lines: int = 3) -> List[str]:
    """Splits a short Japanese/Korean thumbnail hook into 1-3 bold stacked lines cleanly."""
    clean = re.sub(r"\s+", " ", str(hook or "")).strip()
    if not clean:
        return []
    for sep in ("\n", "/"):
        if sep in clean:
            parts = [p.strip() for p in clean.split(sep) if p.strip()]
            if parts:
                return parts[:max_lines]

    lang = detect_cjk_language(clean)
    # Korean uses spaces naturally: group into 1-2 words per line
    if " " in clean and lang == "Korean":
        words = clean.split()
        if len(words) <= 2:
            return words
        if len(words) <= 4:
            mid = len(words) // 2
            return [" ".join(words[:mid]), " ".join(words[mid:])]
        t1 = max(1, len(words) // 3)
        t2 = max(t1 + 1, (2 * len(words)) // 3)
        return [" ".join(words[:t1]), " ".join(words[t1:t2]), " ".join(words[t2:])][:max_lines]

    # Japanese (usually no spaces): split on comma or balanced CJK chunks (4-7 chars)
    comma_parts = [p.strip() for p in re.split(r"[、,・：:]", clean) if p.strip()]
    if 2 <= len(comma_parts) <= max_lines:
        return comma_parts

    n = len(clean)
    if n <= 6:
        return [clean]
    if n <= 12:
        # Prefer particle boundary near midpoint for natural Japanese phrasing
        mid = n // 2
        best_cut = mid
        for offset in range(0, min(3, mid)):
            for cand in (mid - offset, mid + offset):
                if 2 < cand < n - 1 and clean[cand - 1] in "はがをにでとのもへ、":
                    best_cut = cand
                    break
            if best_cut != mid:
                break
        return [clean[:best_cut], clean[best_cut:]]

    chunk_target = max(4, (n + max_lines - 1) // max_lines)
    lines = _split_long_spaceless_clause(clean, chunk_target)
    return lines[:max_lines]


def chunk_cjk_word_timestamps(
    words: list,
    language: Optional[str] = None,
    is_vertical: bool = False,
    max_duration_seconds: float = 3.5,
) -> Optional[list]:
    """Groups word timestamps into CJK-safe subtitle phrases without spaces inside Japanese glyphs.

    Returns None for non-CJK inputs so callers fall back to their Latin aligner unchanged.
    """
    if not words:
        return None

    joined_probe = "".join(str(w.get("word", "")) for w in words[:24] if isinstance(w, dict))
    cjk_lang = detect_cjk_language(joined_probe, language)
    if cjk_lang not in ("Japanese", "Korean"):
        return None

    joiner = " " if cjk_lang == "Korean" else ""
    max_chars = (10 if is_vertical else 18) if cjk_lang == "Japanese" else (16 if is_vertical else 28)
    max_tokens = 6 if cjk_lang == "Japanese" else (3 if is_vertical else 4)
    sentence_ends = ("。", "！", "？", ".", "!", "?", "…")
    clause_pauses = ("、", "，", ",", ";", "；", ":", "：")

    subtitles = []
    current_chunk = []
    chunk_start = None
    total_words = len(words)

    for idx, w_entry in enumerate(words):
        if not isinstance(w_entry, dict):
            continue
        w_text = str(w_entry.get("word", "")).strip()
        if not w_text:
            continue
        w_start = float(w_entry.get("start", 0.0))
        w_end = max(w_start + 0.02, float(w_entry.get("end", w_start + 0.1)))

        if chunk_start is None:
            chunk_start = w_start
        current_chunk.append({"word": w_text, "start": round(w_start, 3), "end": round(w_end, 3)})

        char_len = sum(len(x["word"]) for x in current_chunk) + (len(current_chunk) - 1 if joiner else 0)
        chunk_dur = w_end - chunk_start
        ends_sentence = any(w_text.endswith(p) for p in sentence_ends)
        has_pause = any(w_text.endswith(p) for p in clause_pauses)

        should_split = (
            ends_sentence
            or len(current_chunk) >= max_tokens
            or chunk_dur >= max_duration_seconds
            or char_len >= max_chars
            or (has_pause and len(current_chunk) >= 2)
        )
        if should_split or idx == total_words - 1:
            subtitles.append({
                "start": round(chunk_start, 3),
                "end": round(max(chunk_start + 0.08, w_end), 3),
                "text": joiner.join(x["word"] for x in current_chunk),
                "words": list(current_chunk),
            })
            current_chunk = []
            chunk_start = None

    return subtitles
