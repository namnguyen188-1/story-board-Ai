from pathlib import Path
import shutil,py_compile
root=Path(r"D:\STORYBOARD_AI\studio")
targets=[root/"series_studio.py",root/"studio_gui.py"]
backup=root/"checkpoints"/"v2_tuanstor_bridge_20261011"
backup.mkdir(parents=True,exist_ok=True)
for p in targets:shutil.copy2(p,backup/p.name)
p=targets[0]
s=p.read_text(encoding="utf-8")
needle='''    print("Independent Gemini key configured:",bool(own_api_key()))'''
assert needle in s
s=s.replace(needle,needle+'''
    from v2_tuanstor_image import is_ready as v2_image_ready
    print("V2 Tuấn Stor image gateway available (read-only config):",v2_image_ready())''',1)
needle='''            generated=image_gen_tool_fn(imgprompt,reference_image_path=ref if Path(ref).is_file() else None)'''
assert needle in s
s=s.replace(needle,'''            if job.get("image_provider")=="v2_tuanstor":
                from v2_tuanstor_image import make_image
                generated=make_image(imgprompt,scene_dir/"image.png",
                        reference_path=ref if Path(ref).is_file() else None)
            else:
                generated=image_gen_tool_fn(imgprompt,
                        reference_image_path=ref if Path(ref).is_file() else None)''',1)
needle='''                "mode":args.mode,"subtitle":not args.no_subtitles,"reference":reference})'''
assert needle in s
s=s.replace(needle,'''                "mode":args.mode,"subtitle":not args.no_subtitles,"reference":reference,
                "image_provider":args.image_provider})''',1)
needle='''             "anchor_image":reference,"input_hash":fingerprint}'''
assert needle in s
s=s.replace(needle,'''             "anchor_image":reference,"input_hash":fingerprint,
             "image_provider":args.image_provider}''',1)
needle='''    r.add_argument("--model",default="gemini-3.8-flash")'''
assert needle in s
s=s.replace(needle,needle+'''
    r.add_argument("--image-provider",choices=["gemini","v2_tuanstor"],
                   default="v2_tuanstor")''',1)
needle='''    if args.mode=="live" and not own_api_key():
        raise RuntimeError("Add the separate Gemini API key to studio\\.env first; V2 keys are never used")'''
assert needle in s
s=s.replace(needle,'''    if args.mode=="live" and not own_api_key():
        raise RuntimeError("Gemini text/TTS key missing from Studio/.env")
    if args.mode=="live" and args.image_provider=="v2_tuanstor":
        from v2_tuanstor_image import config as v2_image_config
        v2_image_config()  # Read-only V2 provider configuration validation''',1)
p.write_text(s,encoding="utf-8")

p=targets[1]
s=p.read_text(encoding="utf-8")
needle='''        self.prompt.pack(fill="x")'''
assert needle in s
s=s.replace(needle,needle+'''
        provider_row=ttk.Frame(frm)
        provider_row.pack(fill="x",pady=(9,2))
        ttk.Label(provider_row,text="API tạo ảnh:").pack(side="left")
        self.image_source=ttk.Combobox(provider_row,width=24,state="readonly",
                              values=("Tuấn Stor (V2)","Gemini trực tiếp"))
        self.image_source.set("Tuấn Stor (V2)")
        self.image_source.pack(side="left",padx=10)
        ttk.Label(provider_row,text="Chỉ đọc khóa V2; không thay đổi V2.").pack(side="left")
''',1)
needle='''             "--language",self.lang.get().strip() or "English","--model",self.model.get().strip()]'''
assert needle in s
s=s.replace(needle,'''             "--language",self.lang.get().strip() or "English",
             "--model",self.model.get().strip(),
             "--image-provider","v2_tuanstor" if self.image_source.get()=="Tuấn Stor (V2)"
                     else "gemini"]''',1)
p.write_text(s,encoding="utf-8")
for p in targets+[root/"v2_tuanstor_image.py"]:
    py_compile.compile(str(p),doraise=True)
print("V2_TUANSTOR_BRIDGE_INTEGRATED_AND_COMPILED")
print("CHECKPOINT_CREATED",backup)
