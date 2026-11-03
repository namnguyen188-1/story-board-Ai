"""Safe, curated narrator voice names for Studio.
Full catalog of 30 official Gemini 3.8 studio voices.
"""
VOICES = {
    # 👩 NỮ (FEMALE VOICES)
    "Kore": "👩 Kore — Nữ dứt khoát, chuẩn mực",
    "Aoede": "👩 Aoede — Nữ nhẹ nhàng, truyền cảm",
    "Puck": "👩 Puck — Nữ tươi sáng, hoạt hình",
    "Zephyr": "👩 Zephyr — Nữ trong trẻo, tri thức",
    "Algieba": "👩 Algieba — Nữ êm dịu, điềm tĩnh",
    "Leda": "👩 Leda — Nữ trẻ trung, hiện đại",
    "Callirrhoe": "👩 Callirrhoe — Nữ thân thiện, tự nhiên",
    "Despina": "👩 Despina — Nữ mượt mà, cuốn hút",
    "Autonoe": "👩 Autonoe — Nữ rạng rỡ, sôi nổi",
    "Sulafat": "👩 Sulafat — Nữ ấm áp, cảm xúc",
    "Laomedeia": "👩 Laomedeia — Nữ lạc quan, năng động",
    "Achernar": "👩 Achernar — Nữ thủ thỉ, êm ái",
    "Vindemiatrix": "👩 Vindemiatrix — Nữ trang nhã, dịu dàng",
    "Sadachbia": "👩 Sadachbia — Nữ sống động, sắc sảo",
    "Erinome": "👩 Erinome — Nữ rõ ràng, rành mạch",

    # 👨 NAM (MALE VOICES)
    "Charon": "👨 Charon — Nam trầm, đĩnh đạc, tài liệu",
    "Orus": "👨 Orus — Nam trung, kể chuyện ấm áp",
    "Fenrir": "👨 Fenrir — Nam mạnh mẽ, hành động",
    "Alnilam": "👨 Alnilam — Nam uy quyền, điện ảnh",
    "Iapetus": "👨 Iapetus — Nam trong sáng, khám phá",
    "Algenib": "👨 Algenib — Nam khàn phong trần, viễn tây",
    "Schedar": "👨 Schedar — Nam điềm đạm, triết lý",
    "Gacrux": "👨 Gacrux — Nam trưởng thành, sâu sắc",
    "Rasalgethi": "👨 Rasalgethi — Nam thông thái, học thuật",
    "Enceladus": "👨 Enceladus — Nam hơi trầm, bí ẩn",
    "Umbriel": "👨 Umbriel — Nam tự nhiên, phóng khoáng",
    "Pulcherrima": "👨 Pulcherrima — Nam trực diện, dứt khoát",
    "Achird": "👨 Achird — Nam thân tình, gần gũi",
    "Zubenelgenubi": "👨 Zubenelgenubi — Nam mộc mạc, đời thường",
    "Sadaltager": "👨 Sadaltager — Nam hiểu biết, dẫn dắt",
}
DEFAULT_VOICE = "Kore"

VOICES_BY_REGION = {
    "VN": {
        "region_name": "Việt Nam (Hà Nội & Sài Gòn)",
        "female": [
            ("Aoede", "Aoede — Nữ Hà Nội truyền cảm, kể chuyện ấm áp"),
            ("Kore", "Kore — Nữ Sài Gòn dứt khoát, tin tức & tài liệu"),
            ("Leda", "Leda — Nữ trẻ trung, hiện đại, năng động"),
            ("Puck", "Puck — Nữ hoạt hình, nhí nhảnh, tươi vui"),
            ("Zephyr", "Zephyr — Nữ trong trẻo, khoa học & tri thức"),
        ],
        "male": [
            ("Orus", "Orus — Nam truyền cảm, ấm áp, đời thường"),
            ("Charon", "Charon — Nam trầm đĩnh đạc, tài liệu lịch sử"),
            ("Gacrux", "Gacrux — Nam trưởng thành, sâu sắc, triết lý"),
            ("Fenrir", "Fenrir — Nam mạnh mẽ, hành động, kịch tính"),
            ("Alnilam", "Alnilam — Nam uy quyền, điện ảnh"),
        ],
    },
    "US": {
        "region_name": "Mỹ (American English)",
        "female": [
            ("Puck", "Puck — Female Lively & Cartoon"),
            ("Zephyr", "Zephyr — Female Clear & Knowledge"),
            ("Despina", "Despina — Female Smooth & Engaging"),
            ("Callirrhoe", "Callirrhoe — Female Friendly & Conversational"),
            ("Autonoe", "Autonoe — Female Bright & Upbeat Commercial"),
        ],
        "male": [
            ("Orus", "Orus — Male Warm Storyteller"),
            ("Fenrir", "Fenrir — Male Action, Dynamic & Punchy"),
            ("Alnilam", "Alnilam — Male Deep Cinematic Trailer"),
            ("Umbriel", "Umbriel — Male Casual & Conversational"),
            ("Pulcherrima", "Pulcherrima — Male Confident & Direct"),
        ],
    },
    "GB": {
        "region_name": "Anh (British English)",
        "female": [
            ("Algieba", "Algieba — Female Calm & Aristocratic RP"),
            ("Callirrhoe", "Callirrhoe — Female Friendly British"),
            ("Vindemiatrix", "Vindemiatrix — Female Elegant BBC Style"),
        ],
        "male": [
            ("Schedar", "Schedar — Male Wise & Classic Documentarian"),
            ("Charon", "Charon — Male Solemn & Historical"),
            ("Rasalgethi", "Rasalgethi — Male Academic & Oxford Tone"),
        ],
    },
    "JP": {
        "region_name": "Nhật Bản (Japanese)",
        "female": [
            ("Autonoe", "Autonoe — 女性 明るく快活 (Anime / Vibrant)"),
            ("Sulafat", "Sulafat — 女性 穏やか・感情豊か (Warm Narrative)"),
            ("Kore", "Kore — 女性 凛としたアナウンサー調 (Crisp News)"),
        ],
        "male": [
            ("Enceladus", "Enceladus — 男性 落ち着いた重低音 (Deep Mystery)"),
            ("Achird", "Achird — 男性 親しみやすい語り (Friendly Male)"),
            ("Charon", "Charon — 男性 威厳あるナレーション (Epic Voice)"),
        ],
    },
    "KR": {
        "region_name": "Hàn Quốc (Korean)",
        "female": [
            ("Laomedeia", "Laomedeia — 여성 밝고 당찬 보이스 (Bright & Modern)"),
            ("Achernar", "Achernar — 여성 차분한 감성 드라마 (Calm Drama)"),
            ("Aoede", "Aoede — 여성 감미로운 내레이션 (Melodic Tone)"),
        ],
        "male": [
            ("Pulcherrima", "Pulcherrima — 남성 신뢰감 있는 보이스 (Confident News)"),
            ("Iapetus", "Iapetus — 남성 담백하고 진솔한 톤 (Sincere Narrative)"),
            ("Gacrux", "Gacrux — 남성 묵직한 다큐멘터리 (Deep Doc)"),
        ],
    },
    "CN": {
        "region_name": "Trung Quốc (Mandarin Chinese)",
        "female": [
            ("Vindemiatrix", "Vindemiatrix — 优雅抒情女声 (Elegant Doc)"),
            ("Sadachbia", "Sadachbia — 生动自然女声 (Natural Narrative)"),
            ("Aoede", "Aoede — 温柔治愈女声 (Gentle Story)"),
        ],
        "male": [
            ("Zubenelgenubi", "Zubenelgenubi — 稳重大气男声 (Steady Baritone)"),
            ("Sadaltager", "Sadaltager — 知识导师男声 (Knowledge Mentor)"),
            ("Orus", "Orus — 温暖叙事男声 (Warm Storyteller)"),
        ],
    },
    "ES": {
        "region_name": "Tây Ban Nha (España)",
        "female": [
            ("Despina", "Despina — Femenina Cautivadora y Fluida"),
            ("Kore", "Kore — Femenina Clara e Informativa"),
            ("Puck", "Puck — Femenina Animada y Juvenil"),
        ],
        "male": [
            ("Charon", "Charon — Masculino Solemne y Épico"),
            ("Algenib", "Algenib — Masculino Aventurero y Firme"),
            ("Orus", "Orus — Masculino Cálido y Narrativo"),
        ],
    },
    "MX": {
        "region_name": "Mexico / Mỹ Latinh",
        "female": [
            ("Despina", "Despina — Femenina Suave y Envolvente"),
            ("Puck", "Puck — Femenina Divertida y Dinámica"),
        ],
        "male": [
            ("Orus", "Orus — Masculino Amable y Expresivo"),
            ("Algenib", "Algenib — Masculino Intrépido"),
        ],
    },
    "FR": {
        "region_name": "Pháp (France)",
        "female": [
            ("Aoede", "Aoede — Féminin Doux et Poétique"),
            ("Algieba", "Algieba — Féminin Calme et Distingué"),
        ],
        "male": [
            ("Charon", "Charon — Masculin Profond et Historique"),
            ("Gacrux", "Gacrux — Masculin Posé et Élégant"),
        ],
    },
    "DE": {
        "region_name": "Đức (Germany)",
        "female": [
            ("Kore", "Kore — Weiblich Klar und Präzise"),
            ("Zephyr", "Zephyr — Weiblich Sachlich und Wissen"),
        ],
        "male": [
            ("Alnilam", "Alnilam — Männlich Kraftvoll und Episch"),
            ("Fenrir", "Fenrir — Männlich Dynamisch und Direkt"),
        ],
    },
    "RU": {
        "region_name": "Nga (Russian)",
        "female": [
            ("Erinome", "Erinome — Женский Чёткий и Уверенный"),
            ("Algieba", "Algieba — Женский Спокойный и Глубокий"),
        ],
        "male": [
            ("Charon", "Charon — Мужской Монументальный"),
            ("Alnilam", "Alnilam — Мужской Кинематографичный"),
        ],
    },
    "BR": {
        "region_name": "Brazil (Portuguese)",
        "female": [
            ("Leda", "Leda — Feminina Jovem e Envolvente"),
            ("Autonoe", "Autonoe — Feminina Vibrante e Expressiva"),
        ],
        "male": [
            ("Umbriel", "Umbriel — Masculino Natural e Espontâneo"),
            ("Fenrir", "Fenrir — Masculino Enérgico e Marcante"),
        ],
    },
    "IT": {
        "region_name": "Ý (Italian)",
        "female": [
            ("Algieba", "Algieba — Femminile Elegante e Morbido"),
            ("Despina", "Despina — Femminile Caldo e Avvolgente"),
        ],
        "male": [
            ("Charon", "Charon — Maschile Solenne e Storico"),
            ("Achird", "Achird — Maschile Empatico e Vicino"),
        ],
    },
    "TH": {
        "region_name": "Thái Lan (Thai)",
        "female": [
            ("Aoede", "Aoede — หญิง อ่อนหวานและนุ่มนวล (Soft)"),
            ("Puck", "Puck — หญิง สดใส ร่าเริง (Animation)"),
        ],
        "male": [
            ("Orus", "Orus — ชาย อบอุ่น ชวนฟัง (Storyteller)"),
            ("Gacrux", "Gacrux — ชาย สุขุม หนักแน่น (Deep)"),
        ],
    },
    "ID": {
        "region_name": "Indonesia / Đông Nam Á",
        "female": [
            ("Aoede", "Aoede — Wanita Lembut & Menyentuh"),
            ("Puck", "Puck — Wanita Ceria Animasi"),
        ],
        "male": [
            ("Orus", "Orus — Pria Hangat & Ramah Narasi"),
            ("Gacrux", "Gacrux — Pria Berkarakter & Mendalam"),
        ],
    },
    "IN": {
        "region_name": "Ấn Độ (India / Hindi)",
        "female": [
            ("Callirrhoe", "Callirrhoe — Female Clear & Expressive"),
            ("Zephyr", "Zephyr — Female Intelligent & Smooth"),
        ],
        "male": [
            ("Orus", "Orus — Male Engaging Storyteller"),
            ("Rasalgethi", "Rasalgethi — Male Articulate & Wise"),
        ],
    },
    "SA": {
        "region_name": "Ả Rập (Arabic)",
        "female": [
            ("Sulafat", "Sulafat — أنثى دافئة ومؤثرة"),
            ("Algieba", "Algieba — أنثى هادئة ورصينة"),
        ],
        "male": [
            ("Alnilam", "Alnilam — ذكر فخم وسينمائي"),
            ("Schedar", "Schedar — ذكر حكيم ورزين"),
        ],
    },
}

def validate_voice(value):
    voice=str(value or DEFAULT_VOICE)
    if voice not in VOICES:
        raise ValueError("Unsupported Gemini narrator voice: "+voice[:70])
    return voice

def get_voices_for_region(region="VN", language=None):
    reg = str(region or "VN").upper()
    if reg == "AUTO" and language:
        l = str(language).lower()
        lang_to_reg = {
            "vietnamese": "VN", "english": "US", "chinese": "CN",
            "japanese": "JP", "korean": "KR", "spanish": "ES",
            "french": "FR", "german": "DE", "russian": "RU",
            "portuguese": "BR", "italian": "IT", "thai": "TH",
            "indonesian": "ID", "malay": "ID", "filipino": "ID",
            "hindi": "IN", "arabic": "SA",
        }
        reg = lang_to_reg.get(l, "VN")
    return VOICES_BY_REGION.get(reg, VOICES_BY_REGION["VN"])

