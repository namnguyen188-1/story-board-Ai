from pathlib import Path
import py_compile
root=Path(r"D:\STORYBOARD_AI\studio")
html=root/"web"/"index.html"
s=html.read_text(encoding="utf-8")
old='''<select id="inLanguage">'''
assert old in s
s=s.replace(old,'''<select id="inLanguage">
                <option value="Auto">Tự nhận diện ngôn ngữ (khi dùng link)</option>''',1)
html.write_text(s,encoding="utf-8")
js=root/"web"/"app.js"
s=js.read_text(encoding="utf-8")
old='''  if (linkRow) linkRow.style.display=mode==="link"?"block":"none";'''
assert old in s
s=s.replace(old,'''  if (linkRow) linkRow.style.display=mode==="link"?"block":"none";
  if (mode==="link" && el.inLanguage && el.inLanguage.value==="Vietnamese") {
    el.inLanguage.value="Auto";
  }''',1)
js.write_text(s,encoding="utf-8")
modes=root/"studio_modes.py"
s=modes.read_text(encoding="utf-8")
add='''def detect_language(text):
    t=str(text or "").lower()
    if any(c in t for c in "ăâêôơưđặẳẫấềệộờỡứữị"):
        return "Vietnamese"
    if any(x in t for x in ("¿","¡","estoicismo","filosofía","español","marco aurelio")):
        return "Spanish"
    return "English"

'''
assert "def detect_language(" not in s
s=s.replace("def detect_genre(text):",add+"def detect_genre(text):",1)
modes.write_text(s,encoding="utf-8")
py=root/"series_studio.py"
s=py.read_text(encoding="utf-8")
needle='''    original_genre=args.genre
    original_visual_style=args.visual_style
    original_voice=args.voice_name'''
replace='''    original_genre=args.genre
    original_visual_style=args.visual_style
    original_voice=args.voice_name
    original_language=args.language
    if args.language=="Auto":
        from studio_modes import detect_language
        args.language=("English" if args.input_mode=="link" else detect_language(prompt))'''
assert needle in s;s=s.replace(needle,replace,1)
needle='''            if original_genre=="auto" and str(details.get("genre")) in GENRES:'''
replace='''            if original_language=="Auto":
                guess=str(details.get("primary_language","English")).strip().lower()
                known={"vietnamese":"Vietnamese","spanish":"Spanish","english":"English",
                       "french":"French","german":"German","portuguese":"Portuguese",
                       "japanese":"Japanese","hindi":"Hindi","korean":"Korean",
                       "chinese":"Chinese","italian":"Italian","russian":"Russian"}
                args.language=next((name for key,name in known.items() if guess.startswith(key)),"English")
            if original_genre=="auto" and str(details.get("genre")) in GENRES:'''
assert needle in s;s=s.replace(needle,replace,1)
needle='''                args.voice_name=voice_for(args.language,args.genre,args.region,original_voice)
            prompt=("Create an ORIGINAL story'''
replace='''                args.voice_name=voice_for(args.language,args.genre,args.region,original_voice)
            elif original_language=="Auto":
                args.voice_name=voice_for(args.language,args.genre,args.region,original_voice)
            prompt=("Create an ORIGINAL story'''
assert needle in s;s=s.replace(needle,replace,1)
py.write_text(s,encoding="utf-8")
for f in (modes,py):
    py_compile.compile(str(f),doraise=True)
print("YOUTUBE_LANGUAGE_AUTO_DETECTION_PATCH_PASS")
