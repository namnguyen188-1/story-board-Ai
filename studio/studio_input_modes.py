"""Three exclusive Studio input modes: idea, publicly accessible YouTube reference, or locked user-owned screenplay."""
from __future__ import annotations
import json,re
from urllib.parse import urlsplit,parse_qs
HEADER = re.compile(r"(?im)^[ \t=*-]*(?:#{1,4}[ \t]*)?(?:SHOT|SCENE|CẢNH|PHÂN CẢNH|PHẦN|ĐOẠN|MỤC|BƯỚC|TẬP)[ \t_:]*(\d{1,4})(?:[ \t|–—:.-][^\r\n]*)?[ \t=*-]*$", re.M)
SPEECH=re.compile(r'(?im)(?:^|\n)[ \t]*(?:[-*][ \t]*)?(?:[^\n]{0,120}?(?:says|said|whispers?|cries out|speaks|shouts?|hét|nói|thì thầm|lời thoại|đối thoại|narration|voiceover)[^\n:]{0,90}:)[ \t]*["“]([^"”\r\n]+)["”]')
QUOTE=re.compile(r'["“]([^"”\r\n]{2,260})["”]')
def youtube_url(raw):
    url=str(raw or "").strip()
    p=urlsplit(url)
    host=(p.hostname or "").lower()
    if p.scheme!="https" or p.username or p.password or p.port not in (None,443):
        raise ValueError("Chỉ hỗ trợ liên kết YouTube HTTPS công khai")
    if host in ("youtu.be","www.youtu.be"):
        vid=p.path.strip("/").split("/")[0]
    elif host in ("www.youtube.com","youtube.com","m.youtube.com"):
        seg=p.path.strip("/").split("/")
        if seg[0]=="watch":
            vid=parse_qs(p.query).get("v",[""])[0]
        elif seg[0] in ("shorts","live","embed") and len(seg)>1:
            vid=seg[1]
        else:vid=""
    else:
        raise ValueError("Chỉ hỗ trợ youtube.com và youtu.be; không gửi link lạ tới API")
    if not re.fullmatch(r'[A-Za-z0-9_-]{11}',vid):
        raise ValueError("ID video YouTube không hợp lệ")
    return "https://www.youtube.com/watch?v="+vid

def analyze_reference(client,model,url):
    try:
        from google.genai import types
    except ImportError:
        class _Shim:
            class FileData:
                def __init__(self, file_uri): self.file_uri = file_uri
            class Part:
                def __init__(self, text=None, file_data=None):
                    self.text = text; self.file_data = file_data
            class Content:
                def __init__(self, parts=None): self.parts = parts or []
        types = _Shim()
    from studio_modes import GENRES
    canonical=youtube_url(url)
    try:
        response=client.models.generate_content(
            model=model,
            contents=types.Content(parts=[
            types.Part(file_data=types.FileData(file_uri=canonical)),
            types.Part(text=(
              "Analyze the PUBLIC YouTube video for an ORIGINAL film adaptation strategy. "
              "Return JSON only: keys genre (one of "+", ".join(GENRES.keys())+
              "), primary_language, country_region (e.g. VN, US, GB, ES, MX, FR, DE, JP, KR, CN, RU, BR, IT, TH, ID, IN, SA), "
              "duration_minutes (estimated length in minutes as float, e.g. 1.0, 2.0, 3.5), "
              "voice_tone (e.g. 'warm_deep' for trầm ấm, 'powerful_action' for mạnh mẽ, 'crisp_news' for dứt khoát, 'lively_cartoon' for vui vẻ hoạt hình, 'calm_wise' for điềm đạm), "
              "suggested_voice (recommend one of Gemini voices: Orus, Charon, Aoede, Kore, Fenrir, Puck, Zephyr, Alnilam, Gacrux, Schedar), "
              "visual_style, hook_technique, scene_pacing, "
              "music_and_sound, narrative_structure, new_original_story_seed, "
              "character_consistency_rules. "
              "Describe the techniques of the video as observed; do NOT copy dialogue, "
              "actual shots, identifiable characters or detailed plot. "
              "If inaccessible, return a JSON object with key 'error' and a brief reason."
            ))
        ]),
            config={"response_mime_type":"application/json"}
        )
    except Exception as exc:
        from resilient_gemini import status_code
        code=status_code(exc)
        if code in (429,500,502,503,504):
            raise RuntimeError(
                "VIDEO_REFERENCE_SERVICE_UNAVAILABLE: Gemini không phân tích "
                "được YouTube lúc này (HTTP "+str(code)+"). Hãy thử lại khi "
                "dịch vụ ổn định, hoặc chọn Kịch bản có sẵn / Ý tưởng. "
                "Studio không tự bịa nội dung từ link."
            ) from exc
        raise RuntimeError(
            "VIDEO_REFERENCE_REJECTED: không thể đọc video công khai. "
            "Kiểm tra liên kết, quyền truy cập và API key."
        ) from exc
    try:
        result=json.loads(response.text)
    except (ValueError,TypeError):
        raise RuntimeError("Gemini reference analysis returned invalid JSON")
    if not isinstance(result,dict) or result.get("error"):
        raise RuntimeError("YouTube reference could not be analyzed; check whether the video is public")
    if not (result.get("hook_technique") and result.get("new_original_story_seed")):
        raise RuntimeError("Gemini video analysis missing required details")
    result["source_url"]=canonical
    return result

VIETNAMESE_UNIQUE = set("ăâêôơưđăâêôơưđảãạẻẽẹỉĩịỏõọủũụỳỷỹỵẳẵặắằẩẫậấầểễệếềởỡợớờửữựứừ")
SPANISH_UNIQUE = set("ñ¿¡")

def extract_youtube_metadata(canonical: str) -> dict:
    import urllib.request, urllib.parse
    meta = {
        "title": "YouTube Reference Video",
        "author": "",
        "duration_seconds": 150,
        "description": "",
        "keywords": [],
        "asr_langs": [],
        "caption_langs": [],
    }
    try:
        req = urllib.request.Request(canonical, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'es,en,vi;q=0.9'
        })
        with urllib.request.urlopen(req, timeout=5) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            m = re.search(r'ytInitialPlayerResponse\s*=\s*(\{.*?\});(?:var\s|</script>)', html)
            if m:
                data = json.loads(m.group(1))
                vd = data.get('videoDetails', {})
                if vd.get('title'): meta['title'] = vd['title']
                if vd.get('author'): meta['author'] = vd['author']
                try:
                    sec = int(vd.get('lengthSeconds', 0))
                    if sec > 0: meta['duration_seconds'] = sec
                except Exception:
                    pass
                meta['description'] = vd.get('shortDescription', '')
                meta['keywords'] = vd.get('keywords', [])
                if not meta['keywords']:
                    m_meta = re.search(r'<meta name="keywords" content="(.*?)">', html)
                    if m_meta:
                        meta['keywords'] = [k.strip() for k in m_meta.group(1).split(",") if k.strip()]
                    else:
                        m_kws = re.findall(r'"keywords":\s*(\[[^\]]+\])', html)
                        if m_kws:
                            try:
                                parsed_kws = json.loads(m_kws[0])
                                if isinstance(parsed_kws, list):
                                    meta['keywords'] = [str(k).strip() for k in parsed_kws if str(k).strip()]
                            except Exception:
                                pass
                
                caps = data.get('captions', {}).get('playerCaptionsTracklistRenderer', {}).get('captionTracks', [])
                for c in caps:
                    lang_code = (c.get('languageCode') or '').lower()
                    meta['caption_langs'].append(lang_code)
                    if c.get('kind') == 'asr':
                        meta['asr_langs'].append(lang_code)
            else:
                m_title = re.search(r'<title>(.*?)</title>', html)
                if m_title: meta['title'] = m_title.group(1).replace(' - YouTube', '').strip()
                m_dur = re.search(r'"approxDurationMs":"(\d+)"', html)
                if m_dur: meta['duration_seconds'] = int(int(m_dur.group(1)) / 1000)
    except Exception:
        pass

    if meta['title'] in ("YouTube Reference Video", "") or not meta['author']:
        try:
            oembed_url = f"https://www.youtube.com/oembed?url={urllib.parse.quote(canonical)}&format=json"
            oreq = urllib.request.Request(oembed_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(oreq, timeout=3) as oresp:
                odata = json.loads(oresp.read().decode('utf-8'))
                if odata.get('title'): meta['title'] = odata['title']
                if odata.get('author_name'): meta['author'] = odata['author_name']
        except Exception:
            pass

    return meta

def classify_video_language_and_region(title: str, desc: str, tags: list, asr_langs: list = None) -> tuple[str, str]:
    text_title = title.lower()
    text_all = f"{title} {desc[:1500]} {' '.join(tags)}".lower()

    scores = {}

    vn_in_title = sum(1 for ch in text_title if ch in VIETNAMESE_UNIQUE)
    vn_in_all = sum(1 for ch in text_all if ch in VIETNAMESE_UNIQUE)
    vn_kw = sum(3 for w in ['thuyết minh', 'lồng tiếng', 'vietsub', 'tập ', 'phim ', 'bộ phim', 'kênh', 'đại việt', 'việt nam'] if w in text_all)
    scores['Vietnamese'] = vn_in_title * 8 + vn_in_all * 2 + vn_kw * 5

    jp_in_title = len(re.findall(r'[\u3040-\u309F\u30A0-\u30FF]', text_title))
    jp_in_all = len(re.findall(r'[\u3040-\u309F\u30A0-\u30FF]', text_all))
    scores['Japanese'] = jp_in_title * 8 + (jp_in_all if jp_in_all >= 15 else 0)

    ko_in_title = len(re.findall(r'[\uAC00-\uD7AF]', text_title))
    ko_in_all = len(re.findall(r'[\uAC00-\uD7AF]', text_all))
    scores['Korean'] = ko_in_title * 8 + (ko_in_all if ko_in_all >= 15 else 0)

    zh_in_title = len(re.findall(r'[\u4E00-\u9FFF]', text_title))
    zh_in_all = len(re.findall(r'[\u4E00-\u9FFF]', text_all))
    scores['Chinese'] = zh_in_title * 8 + (zh_in_all if zh_in_all >= 15 else 0)

    ru_in_title = len(re.findall(r'[\u0400-\u04FF]', text_title))
    ru_in_all = len(re.findall(r'[\u0400-\u04FF]', text_all))
    scores['Russian'] = ru_in_title * 8 + (ru_in_all if ru_in_all >= 15 else 0)

    scores['Thai'] = len(re.findall(r'[\u0E00-\u0E7F]', text_all))
    scores['Arabic'] = len(re.findall(r'[\u0600-\u06FF]', text_all))
    scores['Hindi'] = len(re.findall(r'[\u0900-\u097F]', text_all))

    words = set(re.findall(r'[a-záéíóúñçäöüßâêîôûãõèìòùà]+', text_all))
    es_vocab = {
        'canción', 'música', 'español', 'oficial', 'letra', 'vídeo', 'latino', 'estoicismo', 'capítulo',
        'temporada', 'despacito', 'amigos', 'historia', 'vida', 'tiempo', 'disciplina', 'filosofía',
        'lecciones', 'lección', 'aprende', 'superar', 'adversidad', 'reggaeton', 'fonsi', 'fonsivevo',
        'de', 'la', 'el', 'en', 'y', 'los', 'del', 'las', 'por', 'un', 'para', 'con', 'una', 'su', 'al',
        'como', 'más', 'pero', 'sus', 'este', 'esta', 'son', 'está', 'disponible', 'plataformas', 'digitales',
        'todos', 'todo', 'también', 'cuando', 'nada', 'siempre', 'hacer', 'bien', 'mundo', 'hombre'
    }
    es_matches = len(words.intersection(es_vocab))
    if 'despacito' in text_all: es_matches += 15
    if any(ch in text_title for ch in SPANISH_UNIQUE): es_matches += 10
    scores['Spanish'] = es_matches * 3

    fr_vocab = {'chanson', 'musique', 'français', 'officiel', 'épisode', 'saison', 'vidéo', 'pour', 'avec', 'dans', 'sur', 'cette', 'disponible', 'le', 'la', 'les', 'des', 'du'}
    scores['French'] = len(words.intersection(fr_vocab)) * 3

    de_vocab = {'deutsch', 'offiziell', 'lied', 'folge', 'staffel', 'musik', 'video', 'und', 'den', 'von', 'mit', 'sich', 'auf', 'für', 'nicht', 'eine', 'der', 'die', 'das'}
    scores['German'] = len(words.intersection(de_vocab)) * 3

    pt_vocab = {'música', 'português', 'oficial', 'episódio', 'temporada', 'vídeo', 'não', 'para', 'com', 'mais', 'dos', 'das', 'uma', 'como', 'disponível'}
    scores['Portuguese'] = len(words.intersection(pt_vocab)) * 3

    it_vocab = {'italiano', 'ufficiale', 'canzone', 'episodio', 'stagione', 'video', 'musica', 'per', 'con', 'gli', 'delle', 'nella'}
    scores['Italian'] = len(words.intersection(it_vocab)) * 3

    en_vocab = {'the', 'of', 'and', 'to', 'a', 'in', 'is', 'that', 'for', 'it', 'as', 'was', 'with', 'on', 'official', 'video', 'lyrics', 'remaster'}
    scores['English'] = len(words.intersection(en_vocab)) * 3

    best_lang = max(scores, key=scores.get)
    if scores[best_lang] < 4:
        if asr_langs:
            asr_clean = [a.lower() for a in asr_langs]
            if any(a.startswith('vi') for a in asr_clean):
                best_lang = 'Vietnamese'
            elif any(a.startswith('es') for a in asr_clean):
                best_lang = 'Spanish'
            elif any(a.startswith('en') for a in asr_clean):
                best_lang = 'English'
            elif any(a.startswith('ja') for a in asr_clean):
                best_lang = 'Japanese'
            elif any(a.startswith('ko') for a in asr_clean):
                best_lang = 'Korean'
            elif any(a.startswith('zh') for a in asr_clean):
                best_lang = 'Chinese'
            elif any(a.startswith('fr') for a in asr_clean):
                best_lang = 'French'
            elif any(a.startswith('de') for a in asr_clean):
                best_lang = 'German'
            else:
                best_lang = 'English'
        else:
            best_lang = 'English'

    reg_map = {
        'Vietnamese': 'VN',
        'Spanish': 'MX' if any(w in text_all for w in ['mexico', 'méxico', 'latino', 'reggaeton']) else 'ES',
        'Japanese': 'JP',
        'Korean': 'KR',
        'Chinese': 'CN',
        'Russian': 'RU',
        'Thai': 'TH',
        'Arabic': 'SA',
        'Hindi': 'IN',
        'French': 'FR',
        'German': 'DE',
        'Portuguese': 'BR',
        'Italian': 'IT',
        'English': 'GB' if any(w in text_all for w in ['british', 'uk ', 'bbc', 'london', 'england']) else 'US',
    }

    return best_lang, reg_map.get(best_lang, 'US')

def select_voice_for_tone(region: str, tone: str) -> tuple[str, str, str]:
    tone_lower = (tone or "warm_deep").lower()
    if any(k in tone_lower for k in ("power", "mạnh", "action", "hành động")):
        tone_key = "powerful_action"
        tone_label = "Mạnh mẽ, kịch tính"
    elif any(k in tone_lower for k in ("lively", "vui", "cartoon", "hoạt hình")):
        tone_key = "lively_cartoon"
        tone_label = "Tươi sáng, hoạt hình"
    elif any(k in tone_lower for k in ("crisp", "dứt", "news", "tin tức", "chuẩn")):
        tone_key = "crisp_news"
        tone_label = "Dứt khoát, chuẩn mực"
    elif any(k in tone_lower for k in ("calm", "điềm", "tri thức", "wise")):
        tone_key = "calm_wise"
        tone_label = "Điềm đạm, tri thức"
    else:
        tone_key = "warm_deep"
        tone_label = "Trầm ấm, truyền cảm"

    if region in ("ES", "MX"):
        if tone_key == "powerful_action": voice = "Algenib"
        elif tone_key == "lively_cartoon": voice = "Puck"
        elif tone_key == "crisp_news": voice = "Kore"
        else: voice = "Charon" if region == "ES" else "Orus"
    elif region == "VN":
        if tone_key == "powerful_action": voice = "Fenrir"
        elif tone_key == "lively_cartoon": voice = "Puck"
        elif tone_key == "crisp_news": voice = "Kore"
        elif tone_key == "calm_wise": voice = "Gacrux"
        else: voice = "Orus"
    elif region in ("US", "GB"):
        if region == "GB":
            voice = "Schedar" if tone_key == "warm_deep" else ("Charon" if tone_key == "powerful_action" else "Callirrhoe")
        else:
            if tone_key == "powerful_action": voice = "Fenrir"
            elif tone_key == "lively_cartoon": voice = "Puck"
            elif tone_key == "crisp_news": voice = "Pulcherrima"
            else: voice = "Orus"
    elif region == "JP":
        voice = "Enceladus" if tone_key == "warm_deep" else "Autonoe"
    elif region == "KR":
        voice = "Gacrux" if tone_key == "warm_deep" else "Pulcherrima"
    elif region == "CN":
        voice = "Zubenelgenubi" if tone_key == "warm_deep" else "Vindemiatrix"
    elif region == "FR":
        voice = "Charon" if tone_key == "warm_deep" else "Aoede"
    elif region == "DE":
        voice = "Alnilam" if tone_key == "warm_deep" else "Kore"
    else:
        voice = "Charon"

    from studio_voices import VOICES
    voice_name = VOICES.get(voice, voice)
    return voice, voice_name, tone_label

def inspect_youtube_reference(url: str, client=None, model="gemini-3.8-flash") -> dict:
    canonical = youtube_url(url)
    meta = extract_youtube_metadata(canonical)
    lang, reg = classify_video_language_and_region(meta["title"], meta["description"], meta["keywords"], meta.get("asr_langs"))
    
    dur_sec = meta.get("duration_seconds", 150)
    is_short_link = (dur_sec < 60) or ("/shorts/" in canonical)
    dur_min = round(dur_sec / 60.0, 2) if is_short_link else (max(0.5, round(dur_sec / 60.0, 1)) if dur_sec > 0 else 2.5)
    
    from studio_modes import detect_genre
    comb_text = f"{meta['title']} {meta['description']} {' '.join(meta['keywords'])}"
    gen = detect_genre(comb_text)
    
    tone_key = "warm_deep"
    if gen in ("action", "western"):
        tone_key = "powerful_action"
    elif gen in ("animation",):
        tone_key = "lively_cartoon"
    elif gen in ("stoic", "history", "documentary"):
        tone_key = "warm_deep"
        
    sug_voice, sug_voice_name, tone_label = select_voice_for_tone(reg, tone_key)
    
    result = {
        "ok": True,
        "canonical_url": canonical,
        "title": meta.get("title") or "YouTube Reference Video",
        "author": meta.get("author") or "",
        "duration_minutes": dur_min,
        "duration_seconds": dur_sec,
        "is_short": is_short_link,
        "language": lang,
        "region": reg,
        "genre": gen,
        "visual_style": "color_cinematic",
        "voice_tone": tone_key,
        "voice_tone_label": tone_label,
        "suggested_voice": sug_voice,
        "suggested_voice_name": sug_voice_name,
        "new_original_story_seed": "",
    }
    
    if client:
        try:
            prompt = (
                f"Analyze this public YouTube video for film production adaptation:\n"
                f"URL: {canonical}\n"
                f"Title: {meta.get('title')}\n"
                f"Author: {meta.get('author')}\n"
                f"Duration: {dur_min} minutes\n"
                f"Detected Language: {lang} ({reg})\n"
                f"Description: {meta.get('description')[:500]}\n"
                f"Tags: {', '.join(meta.get('keywords', [])[:10])}\n\n"
                f"Return JSON only with keys: genre, primary_language, country_region, voice_tone, "
                f"suggested_voice, visual_style, hook_technique, new_original_story_seed."
            )
            resp = client.models.generate_content(
                model=model,
                contents=prompt,
                config={"response_mime_type": "application/json"}
            )
            d = json.loads(resp.text)
            if d.get("primary_language"): result["language"] = d["primary_language"]
            if d.get("country_region"): result["region"] = d["country_region"]
            if d.get("genre"): result["genre"] = d["genre"]
            if d.get("visual_style"):
                from competitor_cloner import map_to_canonical_visual_style
                result["visual_style"] = map_to_canonical_visual_style(d["visual_style"], result.get("genre", "documentary"))
            if d.get("voice_tone"):
                result["voice_tone"] = d["voice_tone"]
                v, vn, tl = select_voice_for_tone(result["region"], d["voice_tone"])
                result["suggested_voice"] = v
                result["suggested_voice_name"] = vn
                result["voice_tone_label"] = tl
            if d.get("suggested_voice"):
                from studio_voices import VOICES
                if d["suggested_voice"] in VOICES:
                    result["suggested_voice"] = d["suggested_voice"]
            if d.get("new_original_story_seed"):
                result["new_original_story_seed"] = d["new_original_story_seed"]
        except Exception as e:
            result["ai_note"] = str(e)[:120]
            
    dur_display = f"{dur_sec}s (Short)" if is_short_link else f"{dur_min} phút"
    result["duration_display"] = dur_display
    result["aspect_ratio"] = "9:16" if is_short_link else "16:9"
    result["scenes_count"] = max(3, round(dur_sec / 7.0)) if is_short_link else max(1, round(dur_min * 60.0 / 25.0))
    result["summary"] = f"{dur_display} • {result['language']} ({result['region']}) • Giọng: {result['voice_tone_label']} ({result['suggested_voice']}) • Thể loại: {result['genre']}"
    return result

def extract_section(body,label,next_labels):
    match=re.search(r'(?im)^[ \t]*'+re.escape(label)+r'[ \t]*:[ \t]*(.*)$',body)
    if not match:return ""
    same_line=match.group(1).strip()
    after=body[match.start():]
    end=re.search(r'(?m)^\s*(?:'+ "|".join(next_labels)+r')\s*:',after[len(match.group(0)):],re.I)
    text=after[len(match.group(0)):]
    rest=text[:end.start()].strip() if end else text.strip()
    return (same_line + "\n" + rest).strip() if rest else same_line

def auto_segment_raw_script(script: str, scene_seconds: int = 7) -> list:
    """Tự động phân tách kịch bản tự do thành các phân cảnh hoàn chỉnh khớp thời lượng scene_seconds."""
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n+', script) if len(p.strip()) > 5]
    if not paragraphs or len(paragraphs) <= 1:
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', script) if len(s.strip()) > 5]
        if len(sentences) > 1:
            chunk_size = 2
            paragraphs = [" ".join(sentences[i:i+chunk_size]) for i in range(0, len(sentences), chunk_size)]
        else:
            paragraphs = [script.strip()]

    scenes = []
    sec = max(4, int(scene_seconds or 7))
    for idx, p in enumerate(paragraphs, 1):
        quotes = re.findall(r'["“]([^"”\r\n]{2,260})["”]', p)
        narration = " ".join(quotes) if quotes else p
        scenes.append({
            "script_seconds": sec,
            "scene_number": idx,
            "summary": p[:180],
            "narration": narration,
            "dialogue": narration,
            "dialogue_beats": [{
                "beat_id": 1,
                "speaker": "Narrator",
                "text": narration,
                "action": "",
                "tone": "natural"
            }],
            "description": p[:4000],
            "camera": "slow cinematic camera tracking",
            "action": p[:200],
            "setting": "cinematic scene",
            "characters": "",
            "visual_setup": "Cinematic visual composition matching the narration",
            "text_overlay": "",
            "locked_script": True,
            "has_9_fields": False,
            "raw_9_fields": ""
        })
    return scenes


def parse_locked_screenplay(script, scene_seconds=7):
    script = str(script or "").strip()
    if not script or len(script) < 5:
        raise ValueError("Vui lòng nhập nội dung kịch bản.")

    markers = list(HEADER.finditer(script))
    if not markers:
        # Thử nhận diện các dòng đánh số: 1. ... hoặc [Cảnh 1]
        numbered_header = re.compile(r"(?im)^[ \t]*(?:\[(?:CẢNH|SCENE|SHOT)?\s*(\d{1,4})\]|(\d{1,4})[./\-)][ \t]+[^\r\n]+)$", re.M)
        markers = list(numbered_header.finditer(script))

    # Nếu kịch bản không có đánh số phân cảnh, tự động phân đoạn thông minh theo scene_seconds (mặc định 7s)
    if not markers:
        return auto_segment_raw_script(script, scene_seconds=scene_seconds)

    scenes = []
    for idx, m in enumerate(markers):
        scene_num = idx + 1
        # Explicit three-digit skill scene IDs are authoritative. Refuse gaps,
        # duplicates or non-1 starts instead of silently renumbering locked scenes.
        # Keep legacy SHOT / CẢNH / plain-numbered headers compatible.
        skill_id = re.match(r"(?i)^[ \t=*-]*(?:#{1,4}[ \t]*)?SCENE_(\d{3})(?!\d)", m.group(0))
        if skill_id and int(skill_id.group(1)) != scene_num:
            raise ValueError(
                f"SCENE_SEQUENCE_INVALID: expected SCENE_{scene_num:03d}, "
                f"found SCENE_{int(skill_id.group(1)):03d}; locked scene IDs were not renumbered"
            )
        body = script[m.end():markers[idx+1].start() if idx+1 < len(markers) else len(script)]
        body = re.sub(r'^[\s=\-\*]+', '', body).strip()
        if not body:
            body = m.group(0).strip()

        # 9-fields extraction (100% skill write-video-scene-prompts compatible)
        format_style = extract_section(body, "FORMAT & STYLE", ["CHARACTERS", "SETTING", "LIGHTING", "CAMERA", "TIMED ACTION", "END STATE", "AUDIO", "CONSTRAINTS"])
        characters_str = extract_section(body, "CHARACTERS", ["SETTING", "SETTING & START STATE", "LIGHTING", "CAMERA", "TIMED ACTION", "END STATE", "AUDIO", "CONSTRAINTS"])
        setting_str = extract_section(body, "SETTING & START STATE", ["LIGHTING", "LIGHTING & COLOR", "CAMERA", "TIMED ACTION", "END STATE", "AUDIO", "CONSTRAINTS"])
        if not setting_str:
            setting_str = extract_section(body, "SETTING", ["LIGHTING", "CAMERA", "TIMED ACTION", "END STATE", "AUDIO", "CONSTRAINTS"])
        lighting_str = extract_section(body, "LIGHTING & COLOR", ["CAMERA", "TIMED ACTION", "END STATE", "AUDIO", "CONSTRAINTS"])
        if not lighting_str:
            lighting_str = extract_section(body, "LIGHTING", ["CAMERA", "TIMED ACTION", "END STATE", "AUDIO", "CONSTRAINTS"])
        camera_str = extract_section(body, "CAMERA", ["TIMED ACTION", "END STATE", "AUDIO", "CONSTRAINTS"])
        timed_action = extract_section(body, "TIMED ACTION", ["END STATE", "AUDIO", "CONSTRAINTS"])
        if not timed_action:
            timed_action = extract_section(body, "ACTION", ["END STATE", "AUDIO", "CONSTRAINTS"])
        end_state = extract_section(body, "END STATE", ["AUDIO", "CONSTRAINTS"])
        constraints_str = extract_section(body, "CONSTRAINTS", [])

        audio=extract_section(body,"AUDIO",["CONSTRAINTS","END STATE","CAMERA","TIMED ACTION"])
        if not audio: audio=extract_section(body,"LỜI THOẠI",["CONSTRAINTS","GHI CHÚ","END STATE"])
        if not audio: audio=extract_section(body,"THOẠI",["CONSTRAINTS","GHI CHÚ","END STATE"])
        if not audio: audio=extract_section(body,"THUYẾT MINH",["CONSTRAINTS","GHI CHÚ","END STATE"])
        if not audio: audio=extract_section(body,"LỜI BÌNH",["CONSTRAINTS","GHI CHÚ","END STATE"])
        if not audio: audio=extract_section(body,"LỜI KỂ",["CONSTRAINTS","GHI CHÚ","END STATE"])
        if not audio: audio=extract_section(body,"VOICEOVER",["CONSTRAINTS","GHI CHÚ","END STATE"])
        if not audio: audio=extract_section(body,"VO",["CONSTRAINTS","GHI CHÚ","END STATE"])
        speech=[x.group(1).strip() for x in SPEECH.finditer(audio or body)]
        if not speech and audio:
            speech=[x.group(1).strip() for x in QUOTE.finditer(audio)]
            if not speech:
                cleaned_audio = re.sub(r'["“”]', '', audio).strip()
                if cleaned_audio and not re.search(r'(?i)no spoken dialogue|không có lời thoại|no dialogue', cleaned_audio):
                    speech = [cleaned_audio]
        if re.search(r'(?i)no spoken dialogue|không có lời thoại|no dialogue',audio):
            speech=[]

        # Unstructured scene scripts often put a quoted spoken line on its own
        # line after the visual description. Do not interpret quoted text in a
        # structured visual field as dialogue, or override an explicit silence.
        if not audio and not speech and not (format_style or camera_str or timed_action or setting_str):
            if not re.search(r'(?i)no spoken dialogue|không có lời thoại|no dialogue', body):
                speech = [m.group(1).strip() for m in re.finditer(
                    r'(?m)^[ \t]*["“]([^\r\n]+?)["”][ \t]*$', body
                ) if m.group(1).strip()]

        # Parse dialogue beats with speaker identification
        dialogue_beats = []
        if audio:
            raw_lines = [l.strip() for l in audio.split("\n") if l.strip()]
            for b_idx, line in enumerate(raw_lines, 1):
                m_beat = re.match(r'^([A-Za-z0-9_\s\u00C0-\u1EF9\.\-]{2,35})(?:\s*\((.*?)\))?:\s*["“”]?([^"“”\r\n]+)["“”]?', line)
                if m_beat:
                    spk = m_beat.group(1).strip()
                    action_note = m_beat.group(2) or ""
                    spoken = m_beat.group(3).strip()
                    if spoken:
                        dialogue_beats.append({
                            "beat_id": b_idx,
                            "speaker": spk,
                            "text": spoken,
                            "action": action_note,
                            "tone": "natural"
                        })
        if not dialogue_beats and speech:
            for b_idx, sp_txt in enumerate(speech, 1):
                dialogue_beats.append({
                    "beat_id": b_idx,
                    "speaker": "Narrator" if len(speech) == 1 else f"Character {b_idx}",
                    "text": sp_txt,
                    "action": "",
                    "tone": "natural"
                })

        summary=re.sub(r'\s+',' ',(timed_action or body)[:180]).strip()
        seconds_match=re.search(r"(?i)\b(?:GENERATE\s+)?([5-9]|[1-5][0-9])(?:-second continuous shot|\s*SECONDS?)\b", m.group(0) + " " + body)
        locked_seconds=int(seconds_match.group(1)) if seconds_match else 8

        has_9_fields = bool(format_style or camera_str or timed_action or setting_str)
        scenes.append({
          "script_seconds": locked_seconds,
          "scene_number": scene_num,
          "summary": summary,
          "narration": " ".join(speech),
          "dialogue": " ".join(speech),
          "dialogue_beats": dialogue_beats,
          "description": body[:14500],
          "camera": camera_str or "slow cinematic camera tracking",
          "action": timed_action or summary,
          "setting": setting_str or "",
          "characters": characters_str or "",
          "visual_setup": f"{format_style} {setting_str} {lighting_str}".strip() or "Follow the detailed CAMERA, SETTING, LIGHTING and TIMED ACTION instructions in the supplied scene.",
          "text_overlay": "",
          "locked_script": True,
          "has_9_fields": has_9_fields,
          "raw_9_fields": body if has_9_fields else "",
        })
    if len(scenes)>1000:raise ValueError("Kịch bản quá nhiều cảnh")
    return scenes


def convert_locked_scenes_to_drama_plan(parsed_scenes, series_name="Cinematic Drama", episode_num=1, language="Vietnamese", genre="drama"):
    """Converts user-supplied locked scenes into a 100% compliant Drama Plan without calling an LLM."""
    try:
        from studio.cinematic_engine.character_isolator import extract_single_character_description
    except ImportError:
        try:
            from cinematic_engine.character_isolator import extract_single_character_description
        except ImportError:
            def extract_single_character_description(txt, name):
                return txt

    cast = {}
    drama_scenes = []

    # Aggregate character texts across scenes
    all_char_blocks = []
    for sc_scan in parsed_scenes:
        c_text = sc_scan.get("characters", "") or ""
        if c_text and c_text not in all_char_blocks:
            all_char_blocks.append(c_text)
    combined_char_text = "\n".join(all_char_blocks)

    for sc in parsed_scenes:
        sc_num = sc["scene_number"]
        beats = sc.get("dialogue_beats", [])
        chars_present = []

        for b in beats:
            spk = b.get("speaker", "Character")
            if spk not in chars_present and spk.lower() != "narrator":
                chars_present.append(spk)
            if spk not in cast and spk.lower() != "narrator":
                sc_char_text = sc.get("characters", "") or ""
                isolated_dna = extract_single_character_description(sc_char_text, spk)
                if not isolated_dna or (isolated_dna == sc_char_text and combined_char_text):
                    isolated_dna = extract_single_character_description(combined_char_text, spk)

                cast[spk] = {
                    "name": spk,
                    "gender": "male" if any(k in spk.lower() for k in ("anh", "ông", "mr", "marcus", "man", "boy")) else "female",
                    "role": "protagonist" if len(cast) == 0 else "supporting",
                    "voice_id": "Fenrir" if len(cast) == 0 else "Charon",
                    "voice_label": "Giọng nhân vật kịch bản",
                    "personality": "Kịch bản gốc người dùng",
                    "appearance_lock": isolated_dna or "Theo miêu tả kịch bản"
                }

        drama_scenes.append({
            "scene_number": sc_num,
            "setting": sc.get("setting") or sc.get("visual_setup") or f"Phân cảnh {sc_num}",
            "summary": sc.get("summary") or f"Cảnh {sc_num}",
            "visual_setup": sc.get("visual_setup") or sc.get("description", "")[:400],
            "camera_motion": sc.get("camera") or "slow cinematic camera tracking",
            "bgm_mood": "tense_investigation",
            "sfx_cues": [],
            "characters_present": chars_present,
            "dialogue_beats": beats or [{
                "beat_id": 1,
                "speaker": "Narrator",
                "text": sc.get("narration", ""),
                "tone": "natural",
                "action": sc.get("action", ""),
                "is_narrator": True
            }]
        })

    return {
        "series_name": series_name,
        "episode_num": episode_num,
        "language": language,
        "genre": genre,
        "title": f"{series_name} - Tập {episode_num}",
        "logline": parsed_scenes[0].get("summary", "") if parsed_scenes else "Kịch bản phân cảnh khóa lời thoại",
        "cast": cast,
        "scenes": drama_scenes
    }