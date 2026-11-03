from pathlib import Path
import py_compile,shutil,datetime
root=Path(r"D:\STORYBOARD_AI\studio")
files=[root/"engine"/"tools"/"tts.py",root/"series_studio.py",root/"web_server.py",
       root/"web"/"index.html",root/"web"/"app.js"]
bk=root/"checkpoints"/("narrator_voice_selector_"+datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
bk.mkdir(parents=True,exist_ok=True)
for i,p in enumerate(files):shutil.copy2(p,bk/(str(i)+"_"+p.name))
def edit(p,changes):
    s=p.read_text(encoding="utf-8")
    for label,old,new in changes:
        if old not in s: raise RuntimeError(p.name+":"+label+" missing")
        s=s.replace(old,new,1)
    p.write_text(s,encoding="utf-8")

p=files[0]
edit(p,[
("voice_import","from config import TTS_MODEL","from config import TTS_MODEL\nfrom studio_voices import validate_voice"),
("voice_arg",'language: str = "english") -> str:', 'language: str = "english", voice_name: str = "Kore") -> str:'),
("voice_validate","    if not utils.client:\n", "    voice_name=validate_voice(voice_name)\n    if not utils.client:\n"),
("legacy_default","prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name='Kore')",
 "prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name)"),
("new_tts_voice",'"speech_config":{"voice_config":{"voice":"Kore"}}', '"speech_config":{"voice_config":{"voice":voice_name}}'),
])
p=files[1]
edit(p,[
("voice_tts_call",'generated=generate_tts_audio_tool_fn(scene["narration"],language=job["language"])',
 'generated=generate_tts_audio_tool_fn(scene["narration"],language=job["language"],voice_name=job.get("voice_name","Kore"))'),
("voice_guard",'    plan=produce_plan(args,series_dir,episode_dir,prompt)',
'''    if args.mode=="live" and first_job.is_file():
        prior=read_json(first_job)
        previous_voice=prior.get("voice_name","Kore")
        if previous_voice!=args.voice_name and (
            episode_dir/"scenes"/"scene_0001"/"audio.wav").is_file():
            raise RuntimeError(
                "This episode contains audio from narrator voice '"+previous_voice+
                "'. Choose a new episode number to switch voice without reusing existing speech.")
    plan=produce_plan(args,series_dir,episode_dir,prompt)'''),
("voice_fingerprint",'''                "mode":args.mode,"subtitle":not args.no_subtitles,"reference":reference,''',
 '''                "mode":args.mode,"voice_name":args.voice_name,"subtitle":not args.no_subtitles,"reference":reference,'''),
("voice_job",'''             "width":width,"height":height,"language":args.language,"api_key":key,''',
'''             "width":width,"height":height,"language":args.language,
             "voice_name":args.voice_name,"api_key":key,'''),
("voice_argparse",'    r.add_argument("--language",default="English")',
'''    r.add_argument("--language",default="English")
    from studio_voices import VOICES,DEFAULT_VOICE
    r.add_argument("--voice-name",choices=list(VOICES),default=DEFAULT_VOICE)'''),
])
p=files[2]
edit(p,[
("voice_request",'                language = body.get("language", "Vietnamese").strip()',
'''                language = body.get("language", "Vietnamese").strip()
                from studio_voices import validate_voice
                try:
                    voice_name = validate_voice(body.get("voice_name","Kore"))
                except ValueError:
                    return self.end_json({"error":"Giọng kể không hợp lệ. Vui lòng chọn lại."},400)'''),
("voice_conflict",'''                if not reason and old_plan.is_file():''',
'''                if not reason and old_job.is_file() and (
                    ep_folder/"scenes"/"scene_0001"/"audio.wav").is_file():
                    try:
                        previous_voice = json.loads(old_job.read_text(encoding="utf-8")).get("voice_name","Kore")
                        if previous_voice!=voice_name:
                            reason=("Tập "+str(episode)+" đã có âm thanh bằng giọng "+
                                    previous_voice+". Chọn tập mới để đổi sang "+voice_name+".")
                    except (OSError,ValueError):
                        reason="Không thể xác minh giọng đọc cũ."
                if not reason and old_plan.is_file():'''),
("voice_cli",'                    "--language", language,',
'''                    "--language", language,
                    "--voice-name", voice_name,'''),
])
p=files[3]
edit(p,[
("voice_row",'''          <!-- MCP / VEO 3 OPTIONS BOX -->''',
'''          <div class="form-grid-2" id="narratorVoiceRow">
            <div class="field-wrap">
              <label for="inVoice">Giọng kể Gemini TTS</label>
              <select id="inVoice">
                <option value="Kore" selected>Kore — dứt khoát (mặc định)</option>
                <option value="Charon">Charon — thuyết minh, giàu thông tin</option>
                <option value="Orus">Orus — vững vàng</option>
                <option value="Puck">Puck — tươi sáng</option>
                <option value="Zephyr">Zephyr — sáng, trong</option>
                <option value="Fenrir">Fenrir — mạnh mẽ</option>
                <option value="Aoede">Aoede — nhẹ nhàng</option>
                <option value="Algieba">Algieba — điềm tĩnh</option>
              </select>
            </div>
            <div class="field-wrap">
              <label>Chế độ giọng</label>
              <div style="font-size:.75rem;color:#94a3b8;line-height:1.45;padding-top:7px;">
                Một người dẫn chuyện, giữ cùng giọng xuyên suốt tập.
                Phim đối thoại nhiều nhân vật cần chế độ phân vai riêng.
              </div>
            </div>
          </div>

          <!-- MCP / VEO 3 OPTIONS BOX -->''')
])
p=files[4]
edit(p,[
("voice_ref",'''  inLanguage: document.getElementById("inLanguage"),''',
'''  inLanguage: document.getElementById("inLanguage"),
  inVoice: document.getElementById("inVoice"),'''),
("voice_payload",'''    language: el.inLanguage.value,''',
'''    language: el.inLanguage.value,
    voice_name: el.inVoice ? el.inVoice.value : "Kore",'''),
])
for x in (root/"studio_voices.py",files[0],files[1],files[2]):
    py_compile.compile(str(x),doraise=True)
print("NARRATOR_VOICE_SELECTOR_PATCH_PASS")
print("CHECKPOINT",bk)
