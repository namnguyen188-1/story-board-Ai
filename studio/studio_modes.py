"""Studio genre/region presets. Strict values, no speculative web lookups."""
from __future__ import annotations
GENRES = {
 "drama":("Phim kịch, Drama","color_cinematic"),
 "auto":("Tự nhận diện thể loại","color_cinematic"),
 "stoic":("Khắc kỷ, triết học","color_cinematic"),
 "family_drama":("Drama gia đình","color_cinematic"),
 "mafia_thriller":("Trinh thám, Mafia, Đấu trí","color_cinematic"),
 "psychological_horror":("Kinh dị tâm lý, Giật gân","color_cinematic"),
 "romance_melodrama":("Ngôn tình, Mối tình trắc trở","color_cinematic"),
 "western":("Western miền Viễn Tây","color_cinematic"),
 "action":("Hành động, phiêu lưu","color_cinematic"),
 "history":("Lịch sử, tài liệu","color_cinematic"),
 "documentary":("Phim tài liệu, kể chuyện","color_cinematic"),
 "animation":("Hoạt hình 2D/3D","color_animation"),
 "whiteboard":("Vẽ bảng trắng","whiteboard"),
}
STYLES = {"auto","color_cinematic","color_animation","whiteboard","hand_color","flow_video","colored_marker"}
REGIONS = {"auto","AUTO","VN","ES","MX","US","GB","FR","BR","JP","CN","KR","TH","ID","MY","PH","IN","DE","RU","IT","NL","PL","TR","SE","GR","SA"}
ART = {
 "drama":"Photorealistic contemporary cinematic drama, rich natural skin tones and believable atmospheric interiors.",
 "stoic":"Cinematic Greco-Roman classical antiquity (16:9 widescreen). Depicts the Stoic philosopher emperor Marcus Aurelius as a monumental heroic carved Carrara marble statue amidst ancient Roman architectural ruins. Noble chiseled stone features, intricately sculpted curly marble hair and textured beard, wise contemplative stone gaze (carved stone eyes without biological pupils), broad sculpted stone shoulders draped in an authentic Roman stone toga cascading across one shoulder with a circular imperial brooch medallion. Dramatic golden chiaroscuro rim lighting outlining the cold white marble contours, warm volumetric god rays, atmospheric ancient Roman colonnades and distant Acropolis ruins at golden hour with floating embers. Masterpiece 8k classical fine art sculpture, completely inanimate solid Carrara marble stone, NEVER living human flesh, NEVER real human skin pores, NEVER flesh tones, NEVER modern human actors, NEVER bodybuilder cosplay.",
 "family_drama":"Photorealistic contemporary family drama, rich natural skin tones and realistic clothing textures, consistent adult character facial identities, cinematic three-point lighting, natural color grading, believable interiors.",
 "mafia_thriller":"Cinematic dark crime thriller atmosphere (16:9 widescreen). Gritty noir aesthetics, rain-slicked neon-lit urban streets, shadowy back alleys, smoke-filled poker tables and mob meeting rooms. High-contrast low-key chiaroscuro lighting, tense realistic character expressions, sharp depth of field, authentic tailored suits and leather coats.",
 "psychological_horror":"Cinematic psychological horror and mystery (16:9 widescreen). Atmospheric dread, haunting shadows, dim candlelit or flickering fluorescent interiors, cold desaturated color palette with unsettling warm accents, subtle creeping tension, lifelike human expressions of paranoia and dread, natural skin tones with realistic fine details.",
 "romance_melodrama":"Cinematic modern romance and emotional drama (16:9 widescreen). Soft warm golden hour lighting, gentle bokeh, contemporary stylish wardrobe, tender and expressive character facial nuances, believable emotional tension, high aesthetic color grading.",
 "western":"Cinematic American frontier atmosphere, lifelike western wardrobe, realistic landscape, warm sunset and natural shadows, continuity across shots.",
 "action":"Cinematic action staging and dynamic camera composition, vivid yet realistic colors, consistent characters and environments, plausible movement and natural textures.",
 "history":"Historically plausible costumes, architecture and props, lifelike materials, calibrated documentary color grading.",
 "documentary":"Photorealistic documentary illustrations, accurate props and environments, natural cinematic colors, documentary composition.",
 "animation":"Colorful polished family-friendly 3D/2D animated movie aesthetic, coherent character sheets, lively backgrounds and vibrant but controlled palette.",
 "whiteboard":"Professional whiteboard line illustration, black ink contours on clean white backdrop, concise composition, minimal selective colors.",
 "colored_marker":"Vibrant colored whiteboard marker illustration in the signature style of After Skool (16:9 widescreen). Clean pure white whiteboard backdrop, hand-drawn with expressive multicolored chisel-tip marker pens (deep crimson red, royal blue, warm amber yellow, emerald green, and bold ink black contours). Energetic sketchy marker cross-hatching, conceptual philosophical visual metaphors, expressive caricature character designs, crisp marker lines with authentic dry-erase texture. No photorealism, no 3D render, no messy borders, pure whiteboard marker art.",
 "auto":"Cinematic full-color scene based on narrative, realistic lighting and textures with consistent art direction.",
}

try:
    from east_asia_hook import get_ea_bridge as _get_ea_bridge
    _ea = _get_ea_bridge()
    if _ea is not None:
        _ea.register_east_asia_modes(GENRES, ART)
except Exception:
    _get_ea_bridge = lambda: None
import re

def is_vietnamese_lang(language: str) -> bool:
    l = str(language or "").lower().strip()
    if not l:
        return False
    return bool(re.search(r"(?:^|[\s_\-/,(])(?:vi|vi-[a-z]{2}|vie|vn|viet|vietnamese|tiếng việt|tieng viet)(?:$|[\s_\-/,)])", l)) or ("tiếng việt" in l) or ("vietnam" in l)

def is_spanish_lang(language: str) -> bool:
    l = str(language or "").lower().strip()
    if not l or is_vietnamese_lang(l):
        return False
    return bool(re.search(r"(?:^|[\s_\-/,(])(?:es|es-[a-z]{2}|esp|spa|spanish|español|espanol|tây ban nha|tay ban nha)(?:$|[\s_\-/,)])", l))

def detect_language(text):
    import re
    t = str(text or "").strip()
    tl = t.lower()
    # 1. Russian / Cyrillic
    if re.search(r"[\u0400-\u04FF]", t):
        return "Russian"
    # 2. Asian Scripts
    if re.search(r"[\u3040-\u30FF\u31F0-\u31FF]", t):
        return "Japanese"
    if re.search(r"[\uAC00-\uD7AF]", t):
        return "Korean"
    if re.search(r"[\u4E00-\u9FFF]", t):
        return "Chinese"
    if re.search(r"[\u0E00-\u0E7F]", t):
        return "Thai"
    if re.search(r"[\u0600-\u06FF]", t):
        return "Arabic"

    # 3. Vietnamese (Exclusive characters or distinct Vietnamese stop words)
    vi_exclusive = (
        "ăằắẳẵặâầấẩẫậêềếểễệôồốổỗộơờớởỡợưừứửữựđ"
        "ảãạẻẽẹỉĩịỏõọủũụỷỹỵ"
    )
    if any(c in tl for c in vi_exclusive):
        return "Vietnamese"
    if re.search(r"\b(và|của|những|người|chúng ta|trong khi|nhưng mà|tại sao|không phải|với|được|cho|một|các|hành trình|cuộc sống|bài học|tập|phim)\b", tl):
        return "Vietnamese"

    # 4. Spanish
    if any(c in tl for c in ("¿", "¡", "ñ")) or re.search(r"\b(el|los|las|del|por|para|como|estoicismo|filosofía|español|sabiduría|misterio|lecciones|vida)\b", tl):
        return "Spanish"

    # 5. German
    if any(c in tl for c in ("ä", "ö", "ü", "ß")) or re.search(r"\b(der|die|das|und|nicht|mit|ein|eine|leben|geheimnis|geschichte)\b", tl):
        return "German"

    # 6. French
    if any(c in tl for c in ("ç", "œ", "æ")) or re.search(r"\b(le|les|une|dans|pour|avec|mystère|histoire|secret|sagesse)\b", tl):
        return "French"

    return "English"

def detect_genre(text):
    """Cheap deterministic first-pass classifier for IDEAS and user scripts.

    Video URLs instead use Gemini's visual analysis output. Manual genre
    selections always override these textual heuristics.
    """
    t=str(text or "").lower()[:15000]
    triggers=[
      ("stoic",("stoic","stoicism","estoicismo","marco aurelio","marcus aurelius","séneca","seneca","epicteto","khắc kỷ","filosofía estoica")),
      ("family_drama",("drama gia đình","mẹ chồng","cô dâu","hoa president","hoa bylaws","homeowners association","family drama","mother in law","bà chủ tịch","cưới","gia đình")),
      ("mafia_thriller",("mafia","trinh thám","bố già","tội phạm","gangster","đấu trí","án mạng","thám tử")),
      ("psychological_horror",("kinh dị","ma quái","giật gân","rùng rợn","tâm lý kinh dị","horror","thriller")),
      ("romance_melodrama",("tổng tài","ngôn tình","mối tình","hôn nhân","tình yêu","romance","melodrama")),
      ("western",("western frontier","cowboy","frontier drama","miền viễn tây","wild west","western")),
      ("history",("lịch sử","historia","historical drama","historical documentary","đế chế")),
      ("animation",("minecraft","stickman","hoạt hình","cartoon","mèo mập","anime")),
      ("action",("action film","phim hành động","chase scene","cuộc truy đuổi")),
      ("whiteboard",("whiteboard","vẽ bảng trắng","hand drawn board")),
      ("jp_zen_story",("禅","沈黙","メンタルケア","自己啓発","手描き","人生哲学")),
      ("jp_edo_sleepless",("江戸","侍","睡眠用","聞き流し","日本史")),
      ("kr_yadam_joseon",("조선야담","야담","선비","한옥")),
      ("kr_sayeon_drama",("사연","가족갈등","인생사연","시댁","2chスカッと")),
    ]
    score=[(sum(t.count(x) for x in terms),category) for category,terms in triggers]
    score.sort(reverse=True)
    return score[0][1] if score and score[0][0] else "documentary"

def resolve_genre(genre, suggested=None):
    value=str(genre or "auto").lower().strip()
    if value not in GENRES:
        raise ValueError("Unsupported genre")
    if value=="auto" and suggested in GENRES and suggested!="auto":
        return suggested
    return "documentary" if value=="auto" else value
def resolve_style(style,genre):
    style=str(style or "auto").lower()
    if style not in STYLES:
        raise ValueError("Unsupported visual style")
    return GENRES[genre][1] if style=="auto" else style
def voice_for(language,genre,region="auto",requested="auto"):
    from studio_voices import validate_voice
    if requested!="auto":
        return validate_voice(requested)
    try:
        ea = _get_ea_bridge()
        if ea is not None:
            ea_voice = ea.resolve_voice(language=language, genre=genre, region=region)
            if ea_voice:
                return ea_voice
    except Exception:
        pass
    reg=str(region or "auto").upper()
    lang=str(language or "").lower()

    # 1. Tự động chọn theo Quốc gia / Vùng lãnh thổ
    if reg=="ES":
        return "Charon" if genre in ("stoic","documentary","history","psychological_horror") else "Alnilam"
    if reg=="MX":
        return "Puck" if genre=="animation" else "Orus"
    if reg=="GB":
        return "Charon" if genre in ("history","documentary","stoic","psychological_horror") else "Algieba"
    if reg=="US":
        if genre in ("stoic","psychological_horror"):return "Charon"
        if genre in ("western","action","mafia_thriller"):return "Fenrir"
        if genre=="animation":return "Puck"
        if genre in ("family_drama","romance_melodrama"):return "Aoede"
        return "Orus"
    if reg=="VN" or lang=="vietnamese":
        if genre in ("stoic","history","psychological_horror"):return "Charon"
        if genre in ("action","western","mafia_thriller"):return "Fenrir"
        if genre=="animation":return "Puck"
        if genre in ("family_drama","healing","romance","romance_melodrama"):return "Aoede"
        return "Orus"
    if reg in ("FR","IT"):
        return "Algieba" if genre in ("family_drama","romance_melodrama") else "Charon"
    if reg in ("JP","KR"):
        return "Zephyr" if genre in ("animation","family_drama","romance_melodrama") else "Aoede"
    if reg=="DE":
        return "Alnilam" if genre in ("history","documentary") else "Kore"
    if reg=="CN":
        return "Aoede" if genre in ("family_drama","animation","romance_melodrama") else "Orus"
    if reg in ("BR","PT"):
        return "Leda" if genre=="animation" else "Fenrir"
    if reg in ("IN","SA","RU","TR","PL"):
        return "Orus"

    # 2. Tự động theo Thể loại phim
    if genre=="stoic":return "Charon"
    if genre in ("western","action","mafia_thriller"):return "Fenrir"
    if genre=="psychological_horror":return "Charon"
    if genre=="animation":return "Puck"
    if genre in ("family_drama","romance_melodrama"):return "Aoede"
    if genre in ("history","documentary"):return "Orus"

    # 3. Mặc định theo Ngôn ngữ
    return "Orus" if lang in ("spanish","english") else "Kore"

def tts_style(language,genre,region="auto",pacing="slow"):
    language=str(language).strip()
    locale={
        "ES":"Spain Spanish",
        "MX":"Mexican Spanish",
        "VN":"Vietnamese as spoken in Vietnam",
        "US":"American English",
        "GB":"British English",
        "FR":"French as spoken in France",
        "BR":"Brazilian Portuguese",
        "JP":"Japanese as spoken in Japan",
        "CN":"Mandarin Chinese",
        "KR":"Korean",
        "TH":"Thai",
        "ID":"Indonesian",
        "MY":"Malay",
        "PH":"Filipino",
        "IN":"Indian English",
        "DE":"German as spoken in Germany",
        "RU":"Russian",
        "IT":"Italian",
        "NL":"Dutch",
        "PL":"Polish",
        "TR":"Turkish",
        "SE":"Swedish",
        "GR":"Greek",
        "SA":"Modern Standard Arabic"
    }
    region_str=str(region or "auto").strip()
    reg_upper=region_str.upper()
    upper_set={r.upper() for r in REGIONS}
    if reg_upper not in upper_set:
        raise ValueError("Unsupported region: "+str(region))

    lang_lower = language.lower()
    is_vietnamese = "vietnam" in lang_lower or "tiếng việt" in lang_lower
    if is_vietnamese:
        dialect = locale["VN"]
    elif reg_upper == "AUTO":
        if "spain" in lang_lower or "spanish" in lang_lower or "tây ban nha" in lang_lower:
            dialect = locale["ES"]
        elif "english" in lang_lower or "tiếng anh" in lang_lower:
            dialect = locale["US"]
        elif "russ" in lang_lower or "tiếng nga" in lang_lower:
            dialect = locale["RU"]
        elif "germ" in lang_lower or "tiếng đức" in lang_lower:
            dialect = locale["DE"]
        elif "fren" in lang_lower or "tiếng pháp" in lang_lower:
            dialect = locale["FR"]
        elif "jap" in lang_lower or "tiếng nhật" in lang_lower:
            dialect = locale["JP"]
        elif "chin" in lang_lower or "tiếng trung" in lang_lower:
            dialect = locale["CN"]
        elif "kor" in lang_lower or "tiếng hàn" in lang_lower:
            dialect = locale["KR"]
        elif "port" in lang_lower or "bồ đào nha" in lang_lower:
            dialect = locale["BR"]
        elif "ital" in lang_lower or "tiếng ý" in lang_lower:
            dialect = locale["IT"]
        elif "thai" in lang_lower or "tiếng thái" in lang_lower:
            dialect = locale["TH"]
        elif "arab" in lang_lower or "ả rập" in lang_lower:
            dialect = locale["SA"]
        else:
            dialect = language
    else:
        dialect = locale.get(reg_upper, language)

    pace_desc = {
        "slow": "measured, deeply engaging narrative pacing (~125 words per minute) with expressive dramatic breaths between thoughts",
        "normal": "fluent, compelling storytelling pacing (~148 words per minute) with smooth natural phrasing",
        "fast": "energetic, gripping pacing (~168 words per minute)"
    }.get(pacing, "fluent, engaging storytelling pacing (~140 words per minute)")

    delivery={
      "stoic":"calm, reflective philosophical narration with dignified warmth and deliberate pauses",
      "family_drama":"vivid, emotionally expressive human storytelling with authentic tension and shifting intonation between narrative and sharp dialogue",
      "mafia_thriller":"tense, gripping noir delivery with calculating pauses, sharp weight, and dramatic intensity",
      "psychological_horror":"eerie, intimate, suspenseful delivery with hushed dread and atmospheric tension",
      "romance_melodrama":"tender, deeply heartfelt and emotionally resonant storytelling with warm expressive inflection",
      "western":"warm cinematic frontier storytelling, natural tension, confident pronunciation",
      "action":"energetic yet articulate suspenseful narration, dynamic pacing",
      "documentary":"vivid, captivating storyteller narration with rich emotional inflection, warm presence, and dramatic intrigue (never dry or robotic)",
      "history":"authoritative, cinematic epic narration with dramatic cadence and human warmth",
      "animation":"lively expressive storytelling, vivid vocal character",
      "whiteboard":"engaging, witty conversational narration, clearly articulated"
    }.get(genre,"vivid, expressive storytelling")
    try:
        ea = _get_ea_bridge()
        if ea is not None:
            ea_del = ea.resolve_tts_delivery(genre)
            if ea_del:
                delivery = ea_del
    except Exception:
        pass
    return "Read the supplied transcript exactly, in "+language+". Pronunciation and accent: "+dialect+". Delivery: "+delivery+". Pace: "+pace_desc+". Keep speaker identity steady throughout this segment; no singing, no additional words."
def image_instruction(genre,style):
    try:
        ea = _get_ea_bridge()
        if ea is not None:
            ea_art = ea.resolve_image_instruction(genre=genre, style=style)
            if ea_art:
                if style == "hand_color":
                    return ea_art + " Full-color completed artwork across the entire scene. No artist, hand, pen or brush in the source artwork."
                return ea_art
    except Exception:
        pass
    if style=="hand_color":
        art=ART["animation"] if genre=="whiteboard" else ART.get(genre, ART["auto"])
        return art+" Full-color completed artwork across the entire scene. Rich but natural colors on subjects and background. No monochrome-only line art; no artist, hand, pen or brush in the source artwork."
    if style=="flow_video":
        art=ART["animation"] if genre=="animation" else ART.get(genre, ART["auto"])
        return art+" Full-color cinematic keyframe artwork with rich texture, expressive lighting, and clean composition ready for generative AI video motion synthesis."
    if style=="colored_marker":return ART["colored_marker"]
    if style=="whiteboard":return ART["whiteboard"]
    if style=="color_animation":return ART["animation"]
    return ART.get(genre, ART["auto"])

