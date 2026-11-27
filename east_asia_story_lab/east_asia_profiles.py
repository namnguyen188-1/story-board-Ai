"""Japanese & Korean Storytelling Presets, SEO Metadata Templates, and 24-Shot ComfyUI Banks."""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

EAST_ASIA_LOCALE: Dict[str, tuple[str, str, str, str, str]] = {
    "Japanese": (
        "エピソード",
        "チャプター",
        "チャンネル登録と高評価で次の物語もお届けします。",
        "一番心に残った場面や感想をぜひコメントで教えてください。",
        "本編の続きはチャンネルでご覧いただけます。",
    ),
    "Korean": (
        "에피소드",
        "챕터",
        "구독과 좋아요를 누르시면 다음 이야기도 가장 먼저 받아보실 수 있습니다.",
        "가장 인상 깊었던 장면이나 생각을 댓글로 남겨주세요.",
        "전체 영상은 채널에서 확인하실 수 있습니다.",
    ),
}

EAST_ASIA_GENRES: Dict[str, Dict[str, Any]] = {
    "jp_zen_story": {
        "display_name": "🇯🇵 Triết lý & Tâm lý Nhật (Vẽ tay After Skool)",
        "recommended_style": "colored_marker",
        "recommended_motion": "ken_burns",
        "language": "Japanese",
        "region": "JP",
        "recommended_voices": ("Sulafat", "Enceladus", "Charon"),
        "art_direction": (
            "Vibrant minimalist Japanese Zen ink and colored marker illustration on clean pure #FFFFFF white sketchbook paper. "
            "After Skool hand-drawn style, crisp bold sumi black line art contours, selective crimson red, amber gold, "
            "and indigo blue marker accents, simple symbolic compositions (torii gate, bamboo, enso circle, quiet figure in reflection), "
            "high contrast black ink lines on pure white background."
        ),
        "primary_kw": "人生哲学 朗読",
        "hashtags": ["#人生哲学", "#禅の教え", "#メンタルケア", "#自己啓発", "#朗読"],
    },
    "jp_edo_sleepless": {
        "display_name": "🏯 Lịch sử Edo & Samurai Nghe Đêm (Sleepless Nhật)",
        "recommended_style": "color_cinematic",
        "recommended_motion": "ken_burns",
        "language": "Japanese",
        "region": "JP",
        "recommended_voices": ("Enceladus", "Charon", "Sulafat"),
        "art_direction": (
            "Atmospheric Edo-period Japan historical cinematic art inspired by classic Ukiyo-e woodblock prints and moody chiaroscuro film stills. "
            "Warm paper lantern glow against deep twilight indigo shadows, subtle falling snow or gentle rain over wooden machiya streets, "
            "samurai barracks, candlelit tatami study, calm contemplative nocturnal mood, 8k detail."
        ),
        "primary_kw": "睡眠用 日本史 朗読",
        "hashtags": ["#日本史", "#睡眠用", "#江戸時代", "#朗読", "#聞き流し"],
    },
    "kr_yadam_joseon": {
        "display_name": "🏮 Dã sử Yadam Triều Tiên (조선야담)",
        "recommended_style": "color_cinematic",
        "recommended_motion": "ken_burns",
        "language": "Korean",
        "region": "KR",
        "recommended_voices": ("Gacrux", "Iapetus", "Achernar"),
        "art_direction": (
            "Cinematic Joseon Dynasty Korea historical drama atmosphere, traditional tiled-roof hanok courtyard under moonlight, "
            "soft warm silk cheongsachorong lantern lighting, scholarly wooden study with inkstone and folded scrolls, "
            "authentic traditional Korean hanbok silhouettes, moody atmospheric mist, photorealistic cinema film still."
        ),
        "primary_kw": "조선야담 오디오북",
        "hashtags": ["#조선야담", "#야담", "#한국사", "#수면용", "#옛이야기"],
    },
    "kr_sayeon_drama": {
        "display_name": "🎬 Drama Đời Thực Hàn / Nhật (사연 · 2chスカッと)",
        "recommended_style": "color_cinematic",
        "recommended_motion": "ken_burns",
        "language": "Korean",
        "region": "KR",
        "recommended_voices": ("Achernar", "Laomedeia", "Pulcherrima"),
        "art_direction": (
            "Contemporary Seoul / Tokyo emotional cinematic drama film still, expressive East Asian adult characters with lifelike skin texture, "
            "warm cafe interiors, rainy glass windows with city neon reflections, tense quiet living room confrontations, "
            "35mm anamorphic depth of field, rich film color grading."
        ),
        "primary_kw": "사연 드라마",
        "hashtags": ["#사연", "#인생사연", "#가족갈등", "#인생역전", "#오디오드라마"],
    },
}

# 24-Shot Bank (12 A-Roll + 12 B-Roll) for long-form Edo/Japan sleep & history videos
JP_EDO_SHOT_BANK: List[Dict[str, Any]] = [
    {"id": f"jp_a_{i:02d}", "type": "a_roll", "title": title, "keywords": kws, "prompt": prm}
    for i, (title, kws, prm) in enumerate([
        ("Edo Lantern Corridor", ["城", "廊下", "武士", "侍", "夜", "castle", "samurai"], "Cinematic 16:9 dark Edo castle wooden corridor illuminated by warm hanging paper lanterns, silhouettes of armored samurai armor stand, rain mist outside shoji screen, twilight indigo grading, 8k."),
        ("Tatami Calligraphy Study", ["書", "手紙", "日記", "筆", "学ぶ", "scroll", "write"], "Low-key candlelit Japanese tatami room at night, bamboo brush resting on inkstone beside unrolled rice paper scroll, warm amber candlelight, peaceful quiet atmosphere, 8k."),
        ("Raining Kyoto Shrine Gate", ["神社", "鳥居", "雨", "神", "祈り", "shrine", "rain"], "Atmospheric vermilion torii gate standing under gentle evening rain in mossy cedar forest, soft mist floating between stone lanterns, deep tranquil mood."),
        ("Quiet Tea Pavilion Dusk", ["茶", "心", "静か", "無", "禅", "tea", "zen"], "Minimalist Kyoto tea pavilion with sliding shoji doors open to a raked zen gravel garden, steam rising softly from dark ceramic chawan bowl."),
        ("Ronin Overlooking Valley", ["浪人", "旅", "道", "山", "峠", "mountain", "road"], "Wide cinematic vista of an Edo period traveler in woven bamboo kasa hat walking distant Tokaido mountain pass at misty dawn."),
        ("Samurai Blade Forge Embers", ["刀", "鍛冶", "鉄", "魂", "火", "sword", "forge"], "Close-up of glowing red embers inside a dark traditional Japanese blacksmith hearth, hammered steel katana blade cooling beside water trough."),
        ("Cherry Blossom Midnight Bridge", ["桜", "橋", "春", "川", "月", "moon", "bridge"], "Wooden arched bridge over calm dark river reflecting full moon and drifting pale sakura petals under deep midnight sky."),
        ("Old Merchant Ledger Desk", ["金", "商", "町", "江戸", "暮らし", "merchant", "money"], "Edo period wooden abacus soroban, copper mon coins, and aged paper ledger illuminated by a single oil andon lamp."),
        ("Temple Bell Twilight", ["寺", "鐘", "僧", "仏", "響", "temple", "bell"], "Ancient bronze temple bonsho bell hanging inside dark timber belfry overlooking misty Kyoto tiled rooftops at twilight."),
        ("Winter Pine Watchtower", ["冬", "雪", "松", "寒", "城下", "snow", "winter"], "Snowfall blanketing gnarled pine tree outside dark feudal stone castle wall, single warm window glowing softly in cold blue night."),
        ("Ukiyo-e Harbor Dawn", ["海", "港", "船", "波", "魚", "harbor", "sea"], "Moody Edo wooden fishing boats moored in misty bay at sunrise, atmospheric Japanese woodblock inspired palette."),
        ("Ancient Bamboo Grove Wind", ["竹", "風", "道", "孤独", "自然", "bamboo", "wind"], "Tall towering emerald-dark bamboo grove in soft morning fog, sunbeams slicing obliquely through swaying leaves."),
    ], start=1)
] + [
    {"id": f"jp_b_{i:02d}", "type": "b_roll", "title": title, "keywords": kws, "prompt": prm}
    for i, (title, kws, prm) in enumerate([
        ("Andon Candle Flame Detail", ["灯", "夜", "眠", "夢", "flame", "sleep"], "Macro shot of steady warm oil lamp flame inside paper andon frame against deep dark background, soothing gentle flicker."),
        ("Raindrops On Roof Tiles", ["雨", "屋根", "音", "静", "rain", "tile"], "Close-up of silver raindrops sliding off dark wet kawara clay roof tiles into shadowy courtyard pond."),
        ("Unrolled Edo Map Scroll", ["地図", "街道", "江戸", "場所", "map", "travel"], "Top-down dim warm spotlight on aged hand-drawn Japanese Tokaido route map scroll with worn edges."),
        ("Ink Wash Brush Dip", ["墨", "絵", "歴史", "記録", "ink", "history"], "Macro close-up of traditional ink brush tip touching dark sumi inkwell on stone desk, serene dark mood."),
        ("Stone Lantern Moss Shadow", ["石", "苔", "庭", "古", "stone", "moss"], "Weathered moss-covered stone toro lantern glowing dimly beside still koi pond at night."),
        ("Drifting Mountain Fog", ["霧", "山", "朝", "空", "fog", "mist"], "Slow atmospheric drift of low clouds weaving through dark cedar mountain ridges in Japan."),
        ("Wooden Sandal At Threshold", ["家", "家族", "玄関", "日常", "home", "daily"], "Quiet wooden genkan entrance threshold with neat straw geta sandals lit softly by amber hallway light."),
        ("Ceramic Sake Flask Hearth", ["酒", "囲炉裏", "夜", "冬", "hearth", "night"], "Sunken irori charcoal hearth glowing gently with cast-iron tetsubin kettle steaming in dark timber farmhouse."),
        ("Folded Silk Kimono Texture", ["着物", "絹", "礼儀", "身分", "silk", "robe"], "Rich close-up texture of dark indigo woven silk kimono fabric beside antique lacquered box."),
        ("Moonlight Through Shoji", ["月", "障子", "影", "時間", "moonlight", "shadow"], "Soft pale moonlight casting delicate bamboo leaf shadows onto closed translucent shoji paper door."),
        ("Falling Autumn Maple Leaves", ["秋", "紅葉", "時", "別", "autumn", "leaf"], "Deep crimson momiji maple leaves drifting slowly over dark wet stone temple steps."),
        ("Starlit Quiet Courtyard", ["星", "夜空", "眠り", "終わり", "stars", "calm"], "Wide serene view of midnight starry sky above quiet traditional Japanese wooden eaves."),
    ], start=1)
]

# 24-Shot Bank (12 A-Roll + 12 B-Roll) for Joseon Yadam / Korean historical stories
KR_JOSEON_SHOT_BANK: List[Dict[str, Any]] = [
    {"id": f"kr_a_{i:02d}", "type": "a_roll", "title": title, "keywords": kws, "prompt": prm}
    for i, (title, kws, prm) in enumerate([
        ("Joseon Hanok Moonlight Courtyard", ["한옥", "달밤", "집", "조선", "마당", "hanok", "moon"], "Cinematic 16:9 dark traditional Korean hanok courtyard bathed in silver moonlight, curved giwa clay eaves, soft warm paper door glow, peaceful misty night."),
        ("Scholar Wooden Study Candlelight", ["서재", "책", "선비", "글", "붓", "study", "scholar"], "Atmospheric Joseon scholar room with hanji bookshelves, brass candlestick, bamboo brush and old stitched Korean chronicle open on low wood table."),
        ("Palace Gate Crimson Twilight", ["궁궐", "왕", "대감", "조정", "성문", "palace", "king"], "Grand ancient Korean palace stone courtyard at blue twilight, warm cheongsachorong silk lanterns casting golden reflections on damp stone."),
        ("Mountain Seowon Autumn Mist", ["산", "서원", "안개", "마을", "길", "mountain", "mist"], "Quiet Joseon hillside academy wooden pavilion surrounded by golden autumn mist and dark pine forests at dawn."),
        ("Rain On Giwa Courtyard", ["비", "밤", "눈물", "슬픔", "한숨", "rain", "tears"], "Moody nighttime Korean courtyard under steady silver rain, dripping eaves illuminated by warm room window light."),
        ("Stone Wall Village Lane Night", ["골목", "담장", "밤길", "비밀", "그림자", "lane", "secret"], "Narrow traditional earthen and stone damjang village lane in old Korea lit softly by single distant lantern in fog."),
        ("Royal Throne Hall Shadows", ["임금", "권력", "음모", "비밀", "어명", "throne", "court"], "Imposing dark timber interior of Joseon throne hall with intricate painted ceiling beams, dim golden sunbeam cutting through dust."),
        ("River Ferry Foggy Dawn", ["강", "배", "나루터", "길", "이별", "river", "ferry"], "Lonely wooden ferry boat waiting beside misty Korean river reed bank at quiet blue sunrise."),
        ("Herbal Apothecary Drawer Chest", ["약", "의원", "병", "목숨", "치료", "medicine", "doctor"], "Dimly lit traditional Joseon herbalist room with aged wooden medicine chest, brass mortar and warm oil lamp."),
        ("Temple Stone Pagoda Dusk", ["절", "스님", "운명", "인연", "기도", "temple", "fate"], "Ancient moss-covered Korean granite pagoda silhouetted against deep indigo and warm amber dusk sky."),
        ("Market Street Lantern Dusk", ["장터", "사람", "소문", "이야기", "저잣거리", "market", "rumor"], "Atmospheric twilight street of old Korean village with timber stalls and warm paper lanterns fading into night mist."),
        ("Snowy Pine Hanok Roof", ["겨울", "눈", "세월", "노인", "인생", "winter", "snow"], "Quiet white snow settling gently onto curved dark Korean roof tiles beside ancient twisted pine tree."),
    ], start=1)
] + [
    {"id": f"kr_b_{i:02d}", "type": "b_roll", "title": title, "keywords": kws, "prompt": prm}
    for i, (title, kws, prm) in enumerate([
        ("Cheongsachorong Lantern Macro", ["등불", "희망", "빛", "밤", "lantern", "light"], "Close-up of traditional red-and-blue silk cheongsachorong lantern swaying gently in night breeze with warm inner glow."),
        ("Brass Candle Snuff Smoke", ["촛불", "시간", "죽음", "끝", "candle", "smoke"], "Macro view of delicate white smoke ribbon curling from warm brass Joseon candleholder in dark quiet room."),
        ("Hanji Door Silhouette Shadow", ["그림자", "문", "기다림", "침묵", "shadow", "door"], "Lattice wood and translucent hanji paper door casting soft warm shadow silhouettes in quiet nighttime stillness."),
        ("Antique Jade Seal Desk", ["도장", "문서", "유언", "약속", "seal", "will"], "Close-up of carved jade royal stamp beside red cinnabar paste box and folded hanji letter."),
        ("Black Ink Grinding Stone", ["먹", "글씨", "마음", "ink", "brush"], "Overhead view of black ink stick gleaming wet inside carved dark slate inkstone on warm wood desk."),
        ("Simmering Clay Herbal Pot", ["차", "약탕", "정성", "사랑", "tea", "care"], "Warm dark earthenware kettle gently releasing soft white steam over low glowing charcoal embers."),
        ("Autumn Ginkgo Temple Steps", ["단풍", "은행나무", "추억", "세월", "autumn", "time"], "Golden ginkgo leaves scattered across weathered temple granite steps in soft afternoon shadows."),
        ("Lotus Pond Ripple Moonlight", ["연못", "물", "달", "마음", "pond", "water"], "Calm dark palace pond reflecting silver moon ripples under overhanging weeping willow branches."),
        ("Brass Lock Wooden Chest", ["금고", "재산", "비밀", "상자", "chest", "wealth"], "Aged Korean wooden bandaji chest secured by heavy antique brass swallowtail clasp under low warm side light."),
        ("Plowed Mist Rice Terraces", ["논", "가난", "백성", "삶", "village", "field"], "Serene early morning mist drifting quietly over terraced valleys in rural historical Korea."),
        ("Strings Of Gayageum Dusk", ["소리", "음악", "여운", "그리움", "music", "sound"], "Artistic low-key close-up of twisted silk strings stretching across carved wooden gayageum instrument."),
        ("Silent Dawn Horizon Korea", ["아침", "해", "희망", "교훈", "dawn", "hope"], "Soft golden dawn breaking calmly over distant layered Korean mountain ridges under clearing mist."),
    ], start=1)
]


def normalize_east_asia_bcp47(language: str) -> str:
    l = str(language or "").strip().lower()
    if any(k in l for k in ("jap", "ja", "nhật", "nhat")):
        return "ja"
    if any(k in l for k in ("kor", "ko", "hàn", "han")):
        return "ko"
    if any(k in l for k in ("spa", "es")):
        return "es"
    if any(k in l for k in ("vie", "vi")):
        return "vi"
    return "en-US"


def build_east_asia_seo_seed(genre_id: str, title_topic: str, episode_num: int = 1) -> Dict[str, Any]:
    """Builds a grounded JP/KR metadata starter structure respecting character limits (<500 tag chars)."""
    prof = EAST_ASIA_GENRES.get(genre_id, EAST_ASIA_GENRES["jp_zen_story"])
    lang = prof["language"]
    bcp = normalize_east_asia_bcp47(lang)
    loc = EAST_ASIA_LOCALE[lang]
    topic = str(title_topic or "").strip() or prof["primary_kw"]

    if lang == "Japanese":
        titles = [
            f"【{prof['primary_kw']}】{topic}｜心が静かに整う物語（第{episode_num}話）"[:100],
            f"なぜ{topic}で人生が劇的に変わるのか？静かな夜の朗読"[:100],
            f"知らないと損する{topic}の本質｜聞き流し用エピソード{episode_num}"[:100],
        ]
        hook = f"{topic[:8]}" if len(topic) <= 10 else f"{topic[:6]}/静寂の知恵"
        tags = [
            "日本史", "朗読", "睡眠用", "聞き流し", "人生哲学", "心の整理", "禅の知恵", "夜の本音",
            "メンタルケア", "自己啓発", "江戸時代", "侍の知恵", "静かな時間", "オーディオブック",
            topic[:25], prof["primary_kw"],
        ]
    else:
        titles = [
            f"[{prof['primary_kw']}] {topic} | 깊은 여운을 남기는 이야기 (제{episode_num}화)"[:100],
            f"{topic}에 숨겨진 진짜 이유 — 잠들기 전 듣는 인생 이야기"[:100],
            f"인생이 달라지는 {topic}의 교훈 | 오디오북 제{episode_num}화"[:100],
        ]
        hook = f"{topic[:10]}" if len(topic) <= 10 else f"{topic[:8]}/숨겨진 진실"
        tags = [
            "조선야담", "야담", "사연", "오디오북", "수면용", "인생교훈", "한국사", "옛이야기",
            "가족사연", "인생역전", "조용한이야기", "잠잘때듣는이야기", "지혜이야기",
            topic[:25], prof["primary_kw"],
        ]

    # Deduplicate and enforce YouTube's internal quoted tag ceiling (< 485 chars)
    clean_tags: List[str] = []
    seen = set()
    yt_cost = 0
    for tg in tags:
        t = str(tg or "").strip()
        if not t or t.lower() in seen:
            continue
        item_cost = (len(t) + 2) if " " in t else len(t)
        delim = 1 if clean_tags else 0
        if yt_cost + delim + item_cost > 480:
            break
        seen.add(t.lower())
        clean_tags.append(t)
        yt_cost += delim + item_cost

    return {
        "genre": genre_id,
        "language": lang,
        "default_language": bcp,
        "default_audio_language": bcp,
        "primary_keyword": prof["primary_kw"],
        "titles": [{"type": t_type, "title": t} for t_type, t in zip(("High-CTR", "Curiosity Hook", "Authority Rule"), titles)],
        "thumbnail_hook_text": hook,
        "hashtags": list(prof["hashtags"]),
        "tags": clean_tags,
        "tags_char_count": yt_cost,
        "pinned_comment": loc[3],
        "subscribe_cta": loc[2],
    }


EAST_ASIA_UI_PRESETS: Dict[str, List[Dict[str, str]]] = {
    "jp_zen_story": [
        {
            "label": "🧘 禅・沈黙の力 (Vẽ tay)",
            "text": "感情を乱されない人の静かな習慣。理不尽な言葉に反応せず、自分の心の平和を守る禅の3つの教えをホワイトボードの手描きイラストで分かりやすく解説。",
        },
        {
            "label": "🎍 人間関係を手放す技術",
            "text": "他人の評価を気にしすぎて疲れた夜に聞く話。静かに距離を置く勇気と、本当の自由を取り戻す心の整理術。",
        },
    ],
    "jp_edo_sleepless": [
        {
            "label": "🏯 江戸の夜・眠れる歴史",
            "text": "眠れない夜に聞く江戸時代の静かな物語。侍が夜明けの城下で守った小さな約束と、忘れられた知恵の記録。",
        },
    ],
    "kr_yadam_joseon": [
        {
            "label": "🏮 조선야담・침묵의 지혜",
            "text": "달빛 아래 한옥 마당에 전해지는 조선 시대의 기이한 야담. 작은 친절과 침묵이 한 선비의 운명을 바꾼 깊은 밤의 이야기.",
        },
    ],
    "kr_sayeon_drama": [
        {
            "label": "💔 가족 갈등・눈물의 반전",
            "text": "10년 동안 묵묵히 가족을 지킨 막내아들을 내쫓은 날 밤, 낡은 상자 속에서 발견된 비밀 유언장이 모든 것을 뒤집는다.",
        },
    ],
}


def voice_for_east_asia(language: str = "", genre: str = "auto", region: str = "auto") -> Optional[str]:
    """Resolves optimal Gemini studio voice for Japanese/Korean content, or None if not JP/KR."""
    g = str(genre or "auto").lower().strip()
    if g in EAST_ASIA_GENRES:
        return EAST_ASIA_GENRES[g]["recommended_voices"][0]

    l = str(language or "").lower().strip()
    reg = str(region or "auto").upper().strip()
    is_jp = reg == "JP" or any(k in l for k in ("jap", "ja", "nhật", "nhat"))
    is_kr = reg == "KR" or any(k in l for k in ("kor", "ko", "hàn", "han"))

    if is_jp:
        if g in ("stoic", "history", "documentary", "psychological_horror"):
            return "Enceladus"
        if g in ("animation", "whiteboard", "colored_marker"):
            return "Autonoe"
        if g in ("family_drama", "romance_melodrama"):
            return "Sulafat"
        return "Kore"

    if is_kr:
        if g in ("history", "documentary", "stoic"):
            return "Gacrux"
        if g in ("family_drama", "romance_melodrama"):
            return "Achernar"
        if g in ("animation", "whiteboard", "colored_marker"):
            return "Laomedeia"
        return "Aoede"

    return None


def tts_delivery_for_east_asia(genre: str) -> Optional[str]:
    """Returns curated TTS vocal delivery direction for East Asia genres, or None."""
    deliveries = {
        "jp_zen_story": "calm, mindful, warm Japanese reflective narration with gentle pauses between insights",
        "jp_edo_sleepless": "soothing, unhurried late-night Japanese audiobook cadence, soft low warmth ideal for sleep",
        "kr_yadam_joseon": "deep, atmospheric, dignified Korean traditional folktale narration with steady gravity",
        "kr_sayeon_drama": "intimate, emotionally nuanced contemporary Korean storytelling with natural dramatic pauses",
    }
    return deliveries.get(str(genre or "").lower().strip())


def get_east_asia_shot_bank(genre: str) -> Optional[Tuple[str, List[Dict[str, Any]]]]:
    """Returns (prefix, 24-shot bank) for Edo/Joseon long-form genres, or None otherwise."""
    g = str(genre or "").lower().strip()
    if g == "jp_edo_sleepless":
        return "jp_edo", JP_EDO_SHOT_BANK
    if g == "kr_yadam_joseon":
        return "kr_joseon", KR_JOSEON_SHOT_BANK
    return None


def map_east_asia_shots_to_scenes(
    scenes: List[Dict[str, Any]],
    genre: str,
    shot_map: Dict[str, Path],
    scenes_dir: Path,
) -> List[Dict[str, Any]]:
    """Applies the 24-shot A-Roll / B-Roll montage grammar for JP Edo / KR Joseon productions."""
    bank_info = get_east_asia_shot_bank(genre)
    if not bank_info:
        return scenes

    _, bank = bank_info
    a_roll_shots = [s for s in bank if s["type"] == "a_roll"]
    b_roll_shots = [s for s in bank if s["type"] == "b_roll"]
    camera_motions = ["zoom_in", "pan_right", "zoom_out", "orbit_drift", "tilt_up", "pan_left"]
    object_hints = ("灯", "雨", "地図", "墨", "石", "霧", "茶", "月", "紅葉", "촛불", "등불", "도장", "먹", "차", "연못", "단풍", "소문")

    last_shot_id = ""
    last_was_b_roll = False
    consecutive_a_roll = 0

    for idx, sc in enumerate(scenes):
        scene_num = int(sc.get("scene_number", idx + 1) or (idx + 1))
        sc_dir = scenes_dir / f"scene_{scene_num:04d}"
        sc_dir.mkdir(parents=True, exist_ok=True)
        target_img = sc_dir / "image.png"

        combined = f"{sc.get('narration', '')} {sc.get('summary', '')} {sc.get('description', '')}".lower()
        prefer_b_roll = (
            (any(kw in combined for kw in object_hints) and not last_was_b_roll)
            or (consecutive_a_roll >= 3 and not last_was_b_roll)
        )
        if last_was_b_roll:
            prefer_b_roll = False

        pool = b_roll_shots if prefer_b_roll else a_roll_shots
        best_score = -1
        best_cand = pool[0]
        for cand in pool:
            if cand["id"] == last_shot_id:
                continue
            score = sum(1 for kw in cand["keywords"] if kw in combined)
            if score > best_score:
                best_score = score
                best_cand = cand

        if best_score <= 0:
            valid = [c for c in pool if c["id"] != last_shot_id]
            if valid:
                best_cand = valid[idx % len(valid)]

        selected_id = best_cand["id"]
        src_img = shot_map.get(selected_id)
        if src_img and Path(src_img).is_file():
            shutil.copy2(src_img, target_img)

        last_shot_id = selected_id
        if best_cand["type"] == "b_roll":
            last_was_b_roll = True
            consecutive_a_roll = 0
        else:
            last_was_b_roll = False
            consecutive_a_roll += 1

        meta = {
            "scene_number": scene_num,
            "shot_id": selected_id,
            "shot_type": best_cand["type"],
            "shot_title": best_cand["title"],
            "camera_motion": camera_motions[(scene_num - 1) % len(camera_motions)],
        }
        (sc_dir / "montage_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    return scenes
