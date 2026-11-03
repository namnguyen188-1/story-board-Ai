"""
Kinetic Keyword Stickers Engine (Milestone 4).
Detects narrative/emotional keywords and generates kinetic visual stickers (pop-in badges)
synchronized to the exact millisecond when the keyword is spoken.
Strictly localizes badges and keywords to the project's target language (Spanish, English, Vietnamese).
"""
import re
from typing import List, Dict, Any, Optional

# Master Keyword Trigger Taxonomy with Multi-Language Badge Localization
STICKER_TAXONOMY = [
    {
        "category": "mind",
        "badge_vi": "🧠 TÂM TRÍ",
        "badge_en": "🧠 MINDSET",
        "badge_es": "🧠 MENTE",
        "keywords": [
            "tâm trí", "suy nghĩ", "nhận thức", "bản ngã", "tư duy", "trí tuệ", "tâm hồn",
            "mind", "mindset", "thought", "thoughts", "awareness", "wisdom", "soul",
            "mente", "pensamiento", "sabiduría", "conciencia", "alma", "razón"
        ]
    },
    {
        "category": "time",
        "badge_vi": "⏳ THỜI GIAN",
        "badge_en": "⏳ TIME",
        "badge_es": "⏳ TIEMPO",
        "keywords": [
            "thời gian", "cuộc đời", "cái chết", "sinh tử", "khoảnh khắc", "vĩnh cửu", "năm tháng",
            "time", "lifetime", "death", "moment", "eternity", "years", "seconds",
            "tiempo", "vida", "muerte", "momento", "eterno", "eternidad", "existir"
        ]
    },
    {
        "category": "wealth",
        "badge_vi": "💰 TÀI SẢN",
        "badge_en": "💰 WEALTH",
        "badge_es": "💰 RIQUEZA",
        "keywords": [
            "tiền bạc", "tài sản", "giàu có", "di chúc", "gia tài", "vàng bạc", "kinh tế",
            "money", "wealth", "fortune", "assets", "inheritance", "rich", "estate",
            "riqueza", "dinero", "fortuna", "herencia", "posesiones"
        ]
    },
    {
        "category": "justice",
        "badge_vi": "⚖️ CÔNG LÝ",
        "badge_en": "⚖️ JUSTICE",
        "badge_es": "⚖️ JUSTICIA",
        "keywords": [
            "quy tắc", "luật lệ", "công lý", "trục xuất", "cảnh sát", "hình phạt", "pháp luật",
            "rule", "rules", "law", "justice", "police", "penalty", "order", "expulsion",
            "justicia", "ley", "regla", "orden", "juicio"
        ]
    },
    {
        "category": "secret",
        "badge_vi": "🎭 BÍ MẬT",
        "badge_en": "🎭 SECRET",
        "badge_es": "🎭 SECRETO",
        "keywords": [
            "bí mật", "dối trá", "phản bội", "âm mưu", "giả tạo", "mặt nạ", "manh mối",
            "secret", "secrets", "lie", "lies", "betrayal", "conspiracy", "mask", "clue",
            "secreto", "mentira", "traición", "máscara"
        ]
    },
    {
        "category": "power",
        "badge_vi": "🔥 SỨC MẠNH",
        "badge_en": "🔥 POWER",
        "badge_es": "🔥 PODER",
        "keywords": [
            "sức mạnh", "bùng cháy", "chiến thắng", "quyền lực", "khát vọng", "năng lượng",
            "power", "strength", "fire", "victory", "energy", "force", "determination",
            "poder", "fuerza", "energía", "victoria", "voluntad"
        ]
    },
    {
        "category": "danger",
        "badge_vi": "⚠️ NGUY HIỂM",
        "badge_en": "⚠️ DANGER",
        "badge_es": "⚠️ PELIGRO",
        "keywords": [
            "nguy hiểm", "đe dọa", "kẻ thù", "cảnh báo", "cạm bẫy", "khủng hoảng", "hiểm họa",
            "danger", "dangerous", "threat", "enemy", "warning", "trap", "crisis", "peril",
            "peligro", "amenaza", "enemigo", "trampa"
        ]
    },
    {
        "category": "discipline",
        "badge_vi": "🛡️ KỶ LUẬT",
        "badge_en": "🛡️ STOIC",
        "badge_es": "🛡️ DISCIPLINA",
        "keywords": [
            "kỷ luật", "vững vàng", "tĩnh lặng", "bình thản", "kiên cường", "kiểm soát",
            "discipline", "stoic", "calm", "serenity", "resilience", "control", "steadfast",
            "disciplina", "estoico", "serenidad", "calma", "resiliencia", "autocontrol"
        ]
    },
    {
        "category": "breakthrough",
        "badge_vi": "⚡ ĐỘT PHÁ",
        "badge_en": "⚡ BREAKTHROUGH",
        "badge_es": "⚡ REVELACIÓN",
        "keywords": [
            "đột phá", "bước ngoặt", "thay đổi", "thức tỉnh", "sự thật",
            "breakthrough", "turning point", "change", "awakening", "truth",
            "verdad", "despertar", "cambio", "revelación"
        ]
    }
]


def extract_kinetic_stickers_from_subtitles(
    subtitles: List[Dict[str, Any]],
    language: str = "en",
    max_stickers_per_video: int = 6
) -> List[Dict[str, Any]]:
    """
    Scans subtitle data for narrative keywords and generates timed sticker events.
    Strictly matches the sticker badge language to the subtitle target language.
    """
    if not subtitles:
        return []

    lang_str = str(language or "en").lower().strip()
    is_vietnamese = any(k in lang_str for k in ("vi", "viet", "tiếng việt"))
    is_spanish = any(k in lang_str for k in ("es", "span", "tây ban nha"))

    stickers_found = []
    last_sticker_end = -10.0

    for sub in subtitles:
        sub_text = str(sub.get("text", "")).lower()
        sub_start = float(sub.get("start", 0.0))
        sub_end = float(sub.get("end", 0.0))
        words_data = sub.get("words", [])

        for item in STICKER_TAXONOMY:
            matched_kw = None
            kw_start = sub_start

            for kw in item["keywords"]:
                if kw in sub_text:
                    matched_kw = kw
                    break

            if matched_kw:
                # If word-level timestamps are available, find exact start of keyword
                if words_data:
                    for w_entry in words_data:
                        w_clean = re.sub(r'[^\w\s]', '', str(w_entry.get("word", "")).lower()).strip()
                        if w_clean in matched_kw or matched_kw in w_clean:
                            kw_start = float(w_entry.get("start", sub_start))
                            break

                # Ensure stickers don't collide or overlap (allow 0.05s gap between stickers)
                if kw_start >= last_sticker_end + 0.05:
                    if is_spanish:
                        badge_text = item.get("badge_es", item.get("badge_en", item["badge_vi"]))
                    elif is_vietnamese:
                        badge_text = item["badge_vi"]
                    else:
                        badge_text = item.get("badge_en", item["badge_vi"])

                    display_dur = 1.20  # Punchy, dynamic retention badge
                    s_event = {
                        "badge": badge_text,
                        "category": item["category"],
                        "keyword": matched_kw,
                        "start": round(kw_start, 3),
                        "end": round(kw_start + display_dur, 3)
                    }
                    stickers_found.append(s_event)
                    last_sticker_end = s_event["end"]

                    if len(stickers_found) >= max_stickers_per_video:
                        return stickers_found

    return stickers_found


def generate_ass_sticker_events(
    stickers: List[Dict[str, Any]],
    format_ass_ts_func
) -> List[str]:
    """
    Generates ASS dialogue lines using the KineticSticker style with Spring Pop-In Physics:
    - Initial scale 0%
    - Overshoot pop to 122% in 220ms
    - Elastic settle back to 100% in 180ms
    - Gentle fade-out 200ms
    """
    lines = []
    for s in stickers:
        st = format_ass_ts_func(s["start"])
        et = format_ass_ts_func(s["end"])
        badge = s["badge"]
        # Spring pop animation transform: \fscx0\fscy0\t(0,220,\fscx122\fscy122)\t(220,400,\fscx100\fscy100)\fad(80,200)
        pop_effect = r"{\fscx0\fscy0\t(0,220,\fscx122\fscy122)\t(220,400,\fscx100\fscy100)\fad(80,200)}"
        lines.append(f"Dialogue: 1,{st},{et},KineticSticker,,0,0,0,,{pop_effect}{badge}")
    return lines
