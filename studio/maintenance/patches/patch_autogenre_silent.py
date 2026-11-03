from pathlib import Path
import py_compile,re
root=Path(r"D:\STORYBOARD_AI\studio")
genre=root/"studio_modes.py"
s=genre.read_text(encoding="utf-8")
marker="def resolve_genre(genre, suggested=None):"
assert marker in s
s=s.replace(marker,'''def detect_genre(text):
    """Cheap deterministic first-pass classifier for IDEAS and user scripts.

    Video URLs instead use Gemini's visual analysis output. Manual genre
    selections always override these textual heuristics.
    """
    t=str(text or "").lower()[:15000]
    triggers=[
      ("stoic",("stoic","stoicism","estoicismo","marco aurelio","marcus aurelius","séneca","seneca","epicteto","khắc kỷ","filosofía estoica")),
      ("family_drama",("drama gia đình","mẹ chồng","cô dâu","hoa president","hoa bylaws","homeowners association","family drama","mother in law","bà chủ tịch","cưới","gia đình")),
      ("western",("western frontier","cowboy","frontier drama","miền viễn tây","wild west","western")),
      ("history",("lịch sử","historia","historical drama","historical documentary","đế chế")),
      ("animation",("minecraft","stickman","hoạt hình","cartoon","mèo mập","anime")),
      ("action",("action film","phim hành động","chase scene","cuộc truy đuổi")),
      ("whiteboard",("whiteboard","vẽ bảng trắng","hand drawn board")),
    ]
    score=[(sum(t.count(x) for x in terms),category) for category,terms in triggers]
    score.sort(reverse=True)
    return score[0][1] if score and score[0][0] else "documentary"

'''+marker,1)
genre.write_text(s,encoding="utf-8")
file=root/"series_studio.py"
s=file.read_text(encoding="utf-8")
old='''from studio_modes import GENRES,STYLES,REGIONS,resolve_genre,resolve_style,voice_for,image_instruction,tts_style'''
new='''from studio_modes import GENRES,STYLES,REGIONS,resolve_genre,resolve_style,detect_genre,voice_for,image_instruction,tts_style'''
assert old in s;s=s.replace(old,new,1)
old='''    args.genre=resolve_genre(args.genre)
    args.visual_style=resolve_style(args.visual_style,args.genre)'''
new='''    args.genre=resolve_genre(args.genre,detect_genre(prompt) if args.input_mode!="link" else None)
    args.visual_style=resolve_style(args.visual_style,args.genre)'''
assert old in s;s=s.replace(old,new,1)
# For no-dialogue scenes, don't attempt to generate subtitles from an empty text.
old='''    if job["subtitles"]:
        if not final.exists() or not qc_complete(final,width,height):'''
new='''    if job["subtitles"] and scene["narration"].strip():
        if not final.exists() or not qc_complete(final,width,height):'''
assert old in s;s=s.replace(old,new,1)
file.write_text(s,encoding="utf-8")
ui=root/"web"/"app.js"
s=ui.read_text(encoding="utf-8")
old='''  if (el.inInputMode) {
    el.inInputMode.addEventListener("change", updateInputModeFields);
    updateInputModeFields();
  }'''
new='''  if (el.inInputMode) {
    el.inInputMode.addEventListener("change", updateInputModeFields);
    updateInputModeFields();
  }
  // Useful defaults, but the user may still change language, country and voice.
  if (el.inGenre) {
    el.inGenre.addEventListener("change", () => {
      const presets={stoic:["Spanish","ES"], western:["English","US"],
                     family_drama:["Vietnamese","VN"],
                     history:["Vietnamese","VN"]};
      const values=presets[el.inGenre.value];
      if (values) {
        if (el.inLanguage) el.inLanguage.value=values[0];
        if (el.inRegion) el.inRegion.value=values[1];
      }
      if (el.inVoice) el.inVoice.value="auto";
    });
  }'''
assert old in s;s=s.replace(old,new,1)
ui.write_text(s,encoding="utf-8")
for x in (genre,file):
    py_compile.compile(str(x),doraise=True)
print("AUTO_GENRE_AND_SILENT_DIALOGUE_PASS")
