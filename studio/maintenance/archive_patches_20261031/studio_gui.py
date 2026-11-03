"""Windows desktop UI for independent Storyboard AI Series Studio."""
from pathlib import Path
import json, os, queue, subprocess, sys, threading, tkinter as tk
from tkinter import ttk, messagebox, filedialog
import uuid

HOME=Path(__file__).resolve().parent
CLI=HOME/"series_studio.py"

class StudioApp:
    def __init__(self,root):
        self.root=root
        root.title("Storyboard AI Studio | Sản xuất phim dài tập")
        root.geometry("990x760")
        root.minsize(850,650)
        self.q=queue.Queue()
        self.running=False
        frm=ttk.Frame(root,padding=16)
        frm.pack(fill="both",expand=True)
        ttk.Label(frm,text="STORYBOARD AI  •  SERIES STUDIO",font=("Segoe UI",20,"bold")).pack(anchor="w")
        ttk.Label(frm,text="Sản xuất nhiều tập hoạt hình bảng trắng. Chạy độc lập với YouTube SEO Pro V2.").pack(anchor="w",pady=(0,12))
        head=ttk.Frame(frm);head.pack(fill="x")
        self.series=self.entry(head,"Tên bộ phim","Whiteboard Chronicles",0,0,32)
        self.episode=self.entry(head,"Tập số","1",0,2,8)
        self.minutes=self.entry(head,"Phút/tập","30",0,4,10)
        self.lang=self.entry(head,"Ngôn ngữ thoại","English",2,0,24)
        self.model=self.entry(head,"Gemini LLM","gemini-3.8-flash",2,2,24)
        ttk.Label(head,text="Render").grid(row=2,column=4,sticky="w",padx=5,pady=(8,0))
        self.res=ttk.Combobox(head,values=("1280x720","1920x1080"),width=12,state="readonly")
        self.res.set("1280x720");self.res.grid(row=3,column=4,sticky="w",padx=5)
        ttk.Label(head,text="Số luồng").grid(row=2,column=5,sticky="w",padx=5,pady=(8,0))
        self.workers=ttk.Combobox(head,values=("1","2","3"),width=8,state="readonly")
        self.workers.set("1");self.workers.grid(row=3,column=5,padx=5,sticky="w")
        ttk.Label(frm,text="Ý tưởng và mạch truyện tập phim",font=("Segoe UI",11,"bold")).pack(anchor="w",pady=(15,3))
        self.prompt=tk.Text(frm,height=8,wrap="word",font=("Segoe UI",11),undo=True)
        self.prompt.pack(fill="x")
        provider_row=ttk.Frame(frm)
        provider_row.pack(fill="x",pady=(8,2))
        ttk.Label(provider_row,text="Nguồn tạo ảnh:").pack(side="left")
        self.image_source=ttk.Combobox(provider_row,width=24,state="readonly",
                             values=("MCP V2 (web)","Tuấn Stor (V2)","Gemini trực tiếp"))
        self.image_source.set("Tuấn Stor (V2)")
        self.image_source.pack(side="left",padx=10)
        ttk.Label(provider_row,text="MCP: dọn hàng đợi web cũ trước khi chạy; giới hạn ảnh mới.").pack(side="left")
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
        self.mcp_limit.pack(side="left",padx=8)

        ttk.Label(frm,text="Mỗi tập giữ kịch bản và media đã hoàn thành. Chạy lại cùng cấu hình để tiếp tục từ cảnh lỗi.").pack(anchor="w",pady=(5,12))
        keyrow=ttk.Frame(frm);keyrow.pack(fill="x")
        ttk.Label(keyrow,text="Gemini API riêng (để trống nếu đã lưu):").pack(side="left")
        self.key=ttk.Entry(keyrow,show="*",width=43)
        self.key.pack(side="left",padx=(10,10))
        ttk.Button(keyrow,text="Lưu khóa riêng",command=self.save_key).pack(side="left")
        self.config_status=ttk.Label(keyrow,text="");self.config_status.pack(side="left",padx=12)
        self.refresh_key()
        controls=ttk.Frame(frm);controls.pack(fill="x",pady=14)
        self.btn_live=ttk.Button(controls,text="Sản xuất tập phim bằng AI",command=lambda:self.launch(False))
        self.btn_live.pack(side="left",padx=(0,10))
        self.btn_offline=ttk.Button(controls,text="Kiểm thử Offline",command=lambda:self.launch(True))
        self.btn_offline.pack(side="left",padx=(0,10))
        ttk.Button(controls,text="Mở thư mục sản phẩm",command=self.open_outputs).pack(side="left")
        self.status=ttk.Label(frm,text="Sẵn sàng • Bản offline chưa sử dụng Gemini hay tính phí")
        self.status.pack(anchor="w",pady=(0,6))
        logs=ttk.Frame(frm);logs.pack(fill="both",expand=True)
        ttk.Label(logs,text="Nhật ký / Tiến độ",font=("Segoe UI",11,"bold")).pack(anchor="w")
        self.console=tk.Text(logs,height=14,wrap="word",background="#101923",foreground="#d7e7f5",font=("Consolas",10))
        self.console.pack(fill="both",expand=True)
        self.root.after(150,self.pump)

    def entry(self,parent,label,value,row,column,width):
        ttk.Label(parent,text=label).grid(row=row,column=column,sticky="w",padx=5,pady=(0,2))
        ent=ttk.Entry(parent,width=width)
        ent.insert(0,value)
        ent.grid(row=row+1,column=column,sticky="w",padx=5)
        return ent

    def save_key(self):
        key=self.key.get().strip()
        if not key:
            messagebox.showinfo("Gemini API","Chưa nhập API key; khóa hiện tại không bị thay đổi.")
            return
        path=HOME/".env"
        path.write_text("GEMINI_API_KEY="+key+"\n",encoding="utf-8")
        self.key.delete(0,"end")
        self.refresh_key()
        self.append("Đã lưu khóa Gemini riêng tại studio/.env (không ghi khóa vào nhật ký).\n")

    def refresh_key(self):
        from series_studio import own_api_key
        self.config_status.configure(text="Đã cấu hình" if own_api_key() else "Chưa cấu hình")

    def append(self,msg):
        self.console.insert("end",msg)
        self.console.see("end")

    def open_outputs(self):
        path=HOME/"productions";path.mkdir(exist_ok=True)
        if hasattr(os,"startfile"):
            os.startfile(str(path))

    def launch(self,offline):
        if self.running:
            return
        premise=self.prompt.get("1.0","end").strip()
        if not premise:
            messagebox.showerror("Thiếu nội dung","Hãy nhập ý tưởng hoặc nội dung tập phim.")
            return
        try:
            number=int(self.episode.get().strip())
            minutes=float(self.minutes.get().strip())
            workers=int(self.workers.get())
            if number<1 or minutes<.1 or minutes>180:
                raise ValueError("Giới hạn 0.1–180 phút; tập số phải dương")
        except Exception:
            messagebox.showerror("Thông số không hợp lệ","Kiểm tra tập số và thời lượng.")
            return
        if not offline:
            from series_studio import own_api_key
            if not own_api_key():
                messagebox.showerror("Cần Gemini API riêng","Nhập API key riêng của Storyboard Studio trước khi sản xuất.")
                return
        provider={"MCP V2 (web)":"mcp_v2",
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
            return
        inbox=HOME/"inbox";inbox.mkdir(exist_ok=True)
        prompt_file=inbox/("prompt_"+uuid.uuid4().hex[:12]+".txt")
        prompt_file.write_text(premise,encoding="utf-8")
        command=[sys.executable,"-u",str(CLI),"run","--mode","offline" if offline else "live",
             "--series",self.series.get().strip()+(" - Offline Test" if offline else ""),
             "--episode",str(number),"--prompt-file",str(prompt_file),
             "--minutes",str(.15 if offline else minutes),
             "--scene-seconds",str(5 if offline else 30),
             "--workers",str(workers),"--size","640x360" if offline else self.res.get(),
             "--language",self.lang.get().strip() or "English",
             "--model",self.model.get().strip(),
             "--image-provider",provider,
             "--mcp-model-index",str(("Nano Banana Pro","Nano Banana 2 Lite",
                                      "Nano Banana 2.1").index(self.mcp_model.get())),
             "--mcp-max-images",str(mcp_budget if provider=="mcp_v2" else 0)]
        self.running=True
        self.btn_live.configure(state="disabled");self.btn_offline.configure(state="disabled")
        self.status.configure(text="Đang chạy • Nếu lỗi, chạy lại cùng tập để phục hồi")
        self.append("\n--- BẮT ĐẦU "+("OFFLINE TEST" if offline else "SẢN XUẤT AI")+" ---\n")
        threading.Thread(target=self.worker,args=(command,),daemon=True).start()

    def worker(self,command):
        env=os.environ.copy();env["PYTHONIOENCODING"]="utf-8"
        proc=subprocess.Popen(command,cwd=str(HOME),env=env,
             stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding="utf-8",errors="replace",
             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        for line in proc.stdout:
            self.q.put(("log",line))
        self.q.put(("end",proc.wait()))

    def pump(self):
        try:
            while True:
                kind,val=self.q.get_nowait()
                if kind=="log":self.append(val)
                else:
                    self.running=False
                    self.btn_live.configure(state="normal");self.btn_offline.configure(state="normal")
                    self.status.configure(text="HOÀN THÀNH" if val==0 else "DỪNG DO LỖI • Xem nhật ký và chạy lại để resume")
                    self.append("Kết thúc • Exit code: "+str(val)+"\n")
        except queue.Empty:
            pass
        self.root.after(150,self.pump)

if __name__=="__main__":
    root=tk.Tk()
    StudioApp(root)
    root.mainloop()
