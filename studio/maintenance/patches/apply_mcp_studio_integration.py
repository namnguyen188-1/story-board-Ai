"""Integrate existing V2 MCP as selectable provider without touching V2 code."""
from pathlib import Path
import shutil,py_compile
root=Path(r"D:\STORYBOARD_AI\studio")
paths=[root/"series_studio.py",root/"studio_gui.py"]
checkpoint=root/"checkpoints"/"mcp_provider_integration_20261012"
checkpoint.mkdir(parents=True,exist_ok=True)
for p in paths: shutil.copy2(p,checkpoint/p.name)
p=paths[0];s=p.read_text(encoding="utf-8")
def sub(old,new):
    global s
    if old not in s:
        raise RuntimeError("Missing patch anchor: "+old[:100])
    s=s.replace(old,new,1)

sub('''    print("V2 Tuan Stor image gateway available (read-only config):",v2_image_ready())''',
'''    print("V2 Tuan Stor image gateway available (read-only config):",v2_image_ready())
    try:
        from mcp_v2_images import preflight
        preflight()
        print("MCP V2 image bridge installed:", True)
    except Exception:
        print("MCP V2 image bridge installed:", False)''')
sub('''            imgprompt=prompt_tool_fn(scene["description"],visual_setup=scene.get("visual_setup",""),
                                    text_overlay=scene.get("text_overlay",""),
                                    global_plan=job["bible"])
            if not isinstance(imgprompt,str) or "error" in imgprompt.lower():
                raise RuntimeError("Image prompt generation failed")
            ref=job.get("anchor_image","")
            if job.get("image_provider")=="v2_tuanstor":''',
'''            if job.get("image_provider")=="mcp_v2":
                from mcp_v2_images import make_image
                # No extra Gemini prompt call: scene + Story Bible already contain
                # the approved visual instructions and character definitions.
                names=[]
                for char in job["bible"].get("characters",[]):
                    if isinstance(char,dict):
                        names.append(" ".join(str(char.get(k,"")) for k in
                                          ("name","appearance","attire","personality")))
                imgprompt=(
                    "Original cinematic WHITEBOARD INK ART, 16:9 wide landscape, "
                    "white background, black outlines, subtle selective color. "
                    "Scene: "+str(scene["description"])+". Composition: "+
                    str(scene.get("visual_setup",""))+
                    ". Story style: "+str(job["bible"].get("visual_style","whiteboard"))+
                    ". Recurring characters: "+"; ".join(names)[:1200]+
                    ". No text overlays, no artist hands, no marker pens, no watermarks."
                )[:19000]
                generated=make_image(
                    imgprompt,image,
                    series=job["series"],episode=job["episode"],
                    scene=scene["scene_number"],
                    max_new_images=job["mcp_max_images"],
                    model_index=job["mcp_model_index"],
                    fallback=False
                )
            else:
                imgprompt=prompt_tool_fn(scene["description"],visual_setup=scene.get("visual_setup",""),
                                        text_overlay=scene.get("text_overlay",""),
                                        global_plan=job["bible"])
                if not isinstance(imgprompt,str) or "error" in imgprompt.lower():
                    raise RuntimeError("Image prompt generation failed")
                ref=job.get("anchor_image","")
                if job.get("image_provider")=="v2_tuanstor":''')
# restore existing nested blocks indentation
sub('''                from v2_tuanstor_image import make_image
                generated=make_image(imgprompt,scene_dir/"image.png",
                        reference_path=ref if Path(ref).is_file() else None)
            else:
                generated=image_gen_tool_fn(imgprompt,
                        reference_image_path=ref if Path(ref).is_file() else None)
            if not Path(generated).is_file():
                raise RuntimeError("Image generation failed: "+str(generated)[:200])
            shutil.copy2(generated,image)''',
'''                    from v2_tuanstor_image import make_image
                    generated=make_image(imgprompt,scene_dir/"image.png",
                            reference_path=ref if Path(ref).is_file() else None)
                else:
                    generated=image_gen_tool_fn(imgprompt,
                            reference_image_path=ref if Path(ref).is_file() else None)
            if not Path(generated).is_file():
                raise RuntimeError("Image generation failed: "+str(generated)[:200])
            if Path(generated).resolve()!=image.resolve():
                shutil.copy2(generated,image)''')
sub('''    if args.mode=="live" and args.image_provider=="v2_tuanstor":
        from v2_tuanstor_image import config as v2_image_config
        v2_image_config()  # Read-only access; never write to V2''',
'''    if args.mode=="live" and args.image_provider=="v2_tuanstor":
        from v2_tuanstor_image import config as v2_image_config
        v2_image_config()  # Read-only access; never write to V2
    if args.mode=="live" and args.image_provider=="mcp_v2":
        if args.workers != 1:
            raise RuntimeError("MCP V2 image mode needs 1 worker: the web queue is shared")
        if not 1<=args.mcp_max_images<=1000:
            raise RuntimeError("Approve MCP image budget of 1..1000 for this episode")
        from mcp_v2_images import preflight
        preflight()''')
sub('''    plan=produce_plan(args,series_dir,episode_dir,prompt)
    scenes=plan["scenes"]''',
'''    # Prevent silent reuse of an existing V2-TuanStor/Gemini image when switching providers.
    first_job=episode_dir/"scenes"/"scene_0001"/"job.json"
    if args.mode=="live" and first_job.is_file():
        prior=read_json(first_job)
        old_provider=prior.get("image_provider","gemini")
        if old_provider!=args.image_provider:
            previous_assets=episode_dir/"scenes"/"scene_0001"
            if any((previous_assets/x).is_file() for x in ("image.png","final.mp4","result.json")):
                raise RuntimeError("This episode contains assets from provider '"+old_provider+
                      "'. Choose a new episode number to switch image provider.")
    plan=produce_plan(args,series_dir,episode_dir,prompt)
    scenes=plan["scenes"]''')
sub('''                "image_provider":args.image_provider})''',
'''                "image_provider":args.image_provider,
                "mcp_model_index":args.mcp_model_index if args.image_provider=="mcp_v2" else None})''')
sub('''             "image_provider":args.image_provider}''',
'''             "image_provider":args.image_provider,
             "mcp_model_index":args.mcp_model_index,
             "mcp_max_images":args.mcp_max_images,
             "series":args.series,"episode":args.episode}''')
sub('''    r.add_argument("--image-provider",choices=["gemini","v2_tuanstor"],
                   default="v2_tuanstor")''',
'''    r.add_argument("--image-provider",choices=["gemini","v2_tuanstor","mcp_v2"],
                   default="v2_tuanstor")
    r.add_argument("--mcp-model-index",type=int,choices=[0,1,2],default=1)
    r.add_argument("--mcp-max-images",type=int,default=0,
                   help="Approved maximum NEW MCP images for this episode")''')
sub('''                    "429 quota_or_rate_limit")):''',
'''                    "429 quota_or_rate_limit",
                    "storyboard_image_remote_uncertain_no_resubmit",
                    "flow_mcp_call_failed",
                    "storyboard_image_partial_uncertain_no_resubmit",
                    "storyboard_image_budget_exhausted",
                    "existing queue work must not be altered")):''')
p.write_text(s,encoding="utf-8")
p=paths[1];s=p.read_text(encoding="utf-8")
def gui(old,new):
    global s
    if old not in s: raise RuntimeError("GUI anchor missing: "+old[:90])
    s=s.replace(old,new,1)
gui('''                             values=("Tuấn Stor (V2)","Gemini trực tiếp"))''',
'''                             values=("MCP V2 (web)","Tuấn Stor (V2)","Gemini trực tiếp"))''')
gui('''        ttk.Label(provider_row,text="Chỉ đọc cấu hình V2; không sửa V2.").pack(side="left")''',
'''        ttk.Label(provider_row,text="MCP cần duyệt số ảnh; chỉ dùng lượt web được phép.").pack(side="left")
        mcp_row=ttk.Frame(frm)
        mcp_row.pack(fill="x",pady=(4,1))
        ttk.Label(mcp_row,text="MCP model:").pack(side="left")
        self.mcp_model=ttk.Combobox(mcp_row,width=24,state="readonly",
                    values=("Nano Banana Pro","Nano Banana 2 Lite","Nano Banana 2.1"))
        self.mcp_model.set("Nano Banana 2 Lite")
        self.mcp_model.pack(side="left",padx=(8,20))
        ttk.Label(mcp_row,text="Giới hạn ảnh MCP mới mỗi tập:").pack(side="left")
        self.mcp_limit=ttk.Entry(mcp_row,width=7)
        self.mcp_limit.insert(0,"1")
        self.mcp_limit.pack(side="left",padx=8)''')
gui('''        if not offline and not messagebox.askyesno("Xác nhận chi phí API",
                 f"Tập {number}: sẽ có khoảng {int(minutes*2)} cảnh, mỗi cảnh dùng nhiều lượt Gemini (ảnh, TTS, lời thoại). Tiếp tục?"):
            return''',
'''        provider={"MCP V2 (web)":"mcp_v2",
                  "Tuấn Stor (V2)":"v2_tuanstor",
                  "Gemini trực tiếp":"gemini"}.get(self.image_source.get(),"v2_tuanstor")
        try:
            mcp_budget=int(self.mcp_limit.get().strip())
        except ValueError:
            mcp_budget=0
        if not offline and provider=="mcp_v2":
            if workers!=1:
                messagebox.showerror("MCP chỉ chạy một luồng",
                     "MCP dùng chung hàng đợi web, hãy chọn Số luồng = 1.")
                return
            if not 1<=mcp_budget<=1000:
                messagebox.showerror("Giới hạn ảnh",
                     "Nhập số ảnh MCP được phép tạo mới cho một tập (1–1000).")
                return
            message=(f"MCP V2: tạo tối đa {mcp_budget} ảnh mới bằng lượt web cho tập {number}. "
                     "Các lượt có thể bị giới hạn hoặc trừ tín dụng. "
                     "Có dùng thêm Gemini TTS cho lời thoại. Tiếp tục?")
        else:
            message=(f"Tập {number}: khoảng {int(minutes*2)} cảnh, "
                     "mỗi cảnh có thể dùng API ảnh, TTS và lời thoại. Tiếp tục?")
        if not offline and not messagebox.askyesno("Xác nhận chi phí / số ảnh",message):
            return''')
gui('''             "--image-provider","v2_tuanstor" if self.image_source.get()=="Tuấn Stor (V2)" else "gemini"]''',
'''             "--image-provider",provider,
             "--mcp-model-index",str(("Nano Banana Pro","Nano Banana 2 Lite",
                                      "Nano Banana 2.1").index(self.mcp_model.get())),
             "--mcp-max-images",str(mcp_budget if provider=="mcp_v2" else 0)]''')
p.write_text(s,encoding="utf-8")
for p in paths+[root/"mcp_v2_images.py"]:
    py_compile.compile(str(p),doraise=True)
print("MCP_STUDIO_INTEGRATION_COMPILE_PASS")
print("PATCH_BACKUP",checkpoint)
