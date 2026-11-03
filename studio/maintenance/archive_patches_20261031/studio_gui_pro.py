"""Storyboard AI Studio Pro - Native CustomTkinter Desktop Application.
Features modern Dark Mode UI, Storyboard Scene Cards with Image Previews and Video Player launching.
"""
from __future__ import annotations

import json
import os
import queue
import re
import subprocess
import sys
import threading
import time
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk
from PIL import Image

HOME = Path(__file__).resolve().parent
CLI = HOME / "series_studio.py"
PRODUCTIONS = HOME / "productions"

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class StudioProApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Storyboard AI Studio Pro | Phần Mềm Sản Xuất Phim Hoạt Hình Bảng Trắng")
        self.geometry("1240x840")
        self.minsize(1050, 720)

        self.q = queue.Queue()
        self.running = False
        self.current_series_slug = ""
        self.current_episode_num = 1
        self.cached_images = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # 1. TOP HEADER BAR
        self.header_frame = ctk.CTkFrame(self, height=60, corner_radius=0, fg_color="#0F172A")
        self.header_frame.grid(row=0, column=0, sticky="ew")
        self.header_frame.grid_columnconfigure(0, weight=1)

        header_title = ctk.CTkLabel(
            self.header_frame,
            text="🎬 STORYBOARD AI STUDIO PRO",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#F8FAFC",
        )
        header_title.grid(row=0, column=0, padx=20, pady=12, sticky="w")

        self.btn_open_cinema = ctk.CTkButton(
            self.header_frame,
            text="🖥️ Mở Cửa Sổ Cinema Player",
            command=self.open_cinema_window,
            fg_color="#4F46E5",
            hover_color="#4338CA",
            width=200,
        )
        self.btn_open_cinema.grid(row=0, column=1, padx=20, pady=12, sticky="e")

        # 2. MAIN TABVIEW
        self.tabs = ctk.CTkTabview(self, corner_radius=12, fg_color="#1E293B")
        self.tabs.grid(row=1, column=0, padx=16, pady=(10, 16), sticky="nsew")

        self.tab_setup = self.tabs.add("⚙️ Thiết Lập & Sản Xuất")
        self.tab_preview = self.tabs.add("🎞️ Storyboard & Xem Trước (Preview)")

        self.setup_production_tab()
        self.setup_preview_tab()

        self.after(100, self.pump_logs)

    def setup_production_tab(self):
        tab = self.tab_setup
        tab.grid_columnconfigure((0, 1, 2, 3), weight=1)
        tab.grid_rowconfigure(5, weight=1)

        # Row 0: Basic Series Configuration
        self.entry_series = self.create_input(tab, "Tên bộ phim / Series:", "Whiteboard Chronicles", 0, 0)
        self.entry_episode = self.create_input(tab, "Tập số:", "1", 0, 1)
        self.entry_minutes = self.create_input(tab, "Thời lượng (Phút):", "1.0", 0, 2)
        self.entry_scene_sec = self.create_input(tab, "Mỗi cảnh (Giây):", "25", 0, 3)

        # Row 1: Advanced Settings
        lbl_lang = ctk.CTkLabel(tab, text="Ngôn ngữ thuyết minh:", font=ctk.CTkFont(size=12, weight="bold"))
        lbl_lang.grid(row=2, column=0, padx=10, pady=(10, 2), sticky="w")
        self.opt_lang = ctk.CTkOptionMenu(tab, values=["Vietnamese", "English", "Hindi", "Japanese"])
        self.opt_lang.set("Vietnamese")
        self.opt_lang.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="ew")

        lbl_prov = ctk.CTkLabel(tab, text="Nguồn tạo hình ảnh:", font=ctk.CTkFont(size=12, weight="bold"))
        lbl_prov.grid(row=2, column=1, padx=10, pady=(10, 2), sticky="w")
        self.opt_prov = ctk.CTkOptionMenu(tab, values=["MCP V2 (web)", "Tuấn Stor (V2)", "Gemini trực tiếp"])
        self.opt_prov.set("MCP V2 (web)")
        self.opt_prov.grid(row=3, column=1, padx=10, pady=(0, 10), sticky="ew")

        lbl_res = ctk.CTkLabel(tab, text="Độ phân giải video:", font=ctk.CTkFont(size=12, weight="bold"))
        lbl_res.grid(row=2, column=2, padx=10, pady=(10, 2), sticky="w")
        self.opt_res = ctk.CTkOptionMenu(tab, values=["1280x720", "1920x1080", "640x360"])
        self.opt_res.set("1280x720")
        self.opt_res.grid(row=3, column=2, padx=10, pady=(0, 10), sticky="ew")

        lbl_workers = ctk.CTkLabel(tab, text="Số luồng Worker:", font=ctk.CTkFont(size=12, weight="bold"))
        lbl_workers.grid(row=2, column=3, padx=10, pady=(10, 2), sticky="w")
        self.opt_workers = ctk.CTkOptionMenu(tab, values=["1", "2", "3"])
        self.opt_workers.set("1")
        self.opt_workers.grid(row=3, column=3, padx=10, pady=(0, 10), sticky="ew")

        # Row 2: Prompt Script Idea
        lbl_prompt = ctk.CTkLabel(tab, text="Ý tưởng và cốt truyện tập phim:", font=ctk.CTkFont(size=13, weight="bold"))
        lbl_prompt.grid(row=4, column=0, columnspan=4, padx=10, pady=(6, 2), sticky="w")

        self.txt_prompt = ctk.CTkTextbox(tab, height=90, font=ctk.CTkFont(size=13), corner_radius=8)
        self.txt_prompt.grid(row=5, column=0, columnspan=4, padx=10, pady=(0, 10), sticky="nsew")
        self.txt_prompt.insert("1.0", "Hành trình hào hùng của vua tôi nhà Trần trong cuộc kháng chiến chống quân Nguyên Mông. Trận Bạch Đằng giang rực lửa với bãi cọc ngầm lịch sử.")

        # Row 3: API Key Configuration
        key_frame = ctk.CTkFrame(tab, fg_color="#0F172A", corner_radius=8)
        key_frame.grid(row=6, column=0, columnspan=4, padx=10, pady=(6, 12), sticky="ew")
        key_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(key_frame, text="Gemini API Key riêng:").grid(row=0, column=0, padx=12, pady=10)
        self.entry_key = ctk.CTkEntry(key_frame, show="*", placeholder_text="Nhập khóa API mới nếu cần đổi...")
        self.entry_key.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        self.btn_save_key = ctk.CTkButton(key_frame, text="Lưu Khóa", width=100, command=self.save_key)
        self.btn_save_key.grid(row=0, column=2, padx=10, pady=10)

        self.lbl_key_status = ctk.CTkLabel(key_frame, text="Đang kiểm tra...", text_color="#10B981")
        self.lbl_key_status.grid(row=0, column=3, padx=12, pady=10)
        self.refresh_key_status()

        # Row 4: Action Controls & Progress
        act_frame = ctk.CTkFrame(tab, fg_color="transparent")
        act_frame.grid(row=7, column=0, columnspan=4, padx=10, pady=(4, 8), sticky="ew")

        self.btn_live = ctk.CTkButton(act_frame, text="🚀 Sản Xuất Bằng AI", command=lambda: self.launch(False),
                                     fg_color="#6366F1", hover_color="#4F46E5", font=ctk.CTkFont(size=14, weight="bold"), height=36)
        self.btn_live.pack(side="left", padx=(0, 10))

        self.btn_offline = ctk.CTkButton(act_frame, text="🧪 Kiểm Thử Offline", command=lambda: self.launch(True),
                                        fg_color="#334155", hover_color="#475569", height=36)
        self.btn_offline.pack(side="left", padx=(0, 10))

        self.btn_play_final = ctk.CTkButton(act_frame, text="▶ Xem Video Thành Phẩm", command=self.play_final_video,
                                           fg_color="#059669", hover_color="#047857", height=36)
        self.btn_play_final.pack(side="left", padx=(0, 10))

        self.btn_open_folder = ctk.CTkButton(act_frame, text="📁 Mở Thư Mục Chứa", command=self.open_outputs,
                                            fg_color="#1E293B", hover_color="#334155", height=36)
        self.btn_open_folder.pack(side="left")

        # Progress bar
        self.prog_bar = ctk.CTkProgressBar(tab, height=10, corner_radius=5)
        self.prog_bar.set(0)
        self.prog_bar.grid(row=8, column=0, columnspan=4, padx=10, pady=(6, 4), sticky="ew")

        self.lbl_status = ctk.CTkLabel(tab, text="Trạng thái: Sẵn sàng sản xuất", font=ctk.CTkFont(size=12))
        self.lbl_status.grid(row=9, column=0, columnspan=4, padx=10, sticky="w")

        # Row 5: Console Logs
        self.txt_console = ctk.CTkTextbox(tab, height=140, font=ctk.CTkFont(family="Consolas", size=11), fg_color="#0A0E17", text_color="#94A3B8")
        self.txt_console.grid(row=10, column=0, columnspan=4, padx=10, pady=(6, 8), sticky="nsew")

    def setup_preview_tab(self):
        tab = self.tab_preview
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # Toolbar
        bar = ctk.CTkFrame(tab, fg_color="#0F172A", height=50, corner_radius=8)
        bar.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(bar, text="DANH SÁCH CÁC THẺ CẢNH (STORYBOARD SCENE CARDS)", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=16, pady=10)

        self.btn_refresh_preview = ctk.CTkButton(bar, text="🔄 Làm Mới Thẻ Cảnh", width=140, command=self.load_storyboard_scenes)
        self.btn_refresh_preview.pack(side="right", padx=12, pady=8)

        # Scrollable Cards View
        self.scroll_cards = ctk.CTkScrollableFrame(tab, corner_radius=10, fg_color="#0B0F17")
        self.scroll_cards.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")

    def create_input(self, parent, label, val, r, c):
        lbl = ctk.CTkLabel(parent, text=label, font=ctk.CTkFont(size=12, weight="bold"))
        lbl.grid(row=r*2, column=c, padx=10, pady=(8, 2), sticky="w")
        ent = ctk.CTkEntry(parent, font=ctk.CTkFont(size=13))
        ent.insert(0, val)
        ent.grid(row=r*2+1, column=c, padx=10, pady=(0, 8), sticky="ew")
        return ent

    def save_key(self):
        key = self.entry_key.get().strip()
        if not key:
            messagebox.showinfo("Gemini API", "Chưa nhập khóa mới.")
            return
        p = HOME / ".env"
        p.write_text("GEMINI_API_KEY=" + key + "\n", encoding="utf-8")
        self.entry_key.delete(0, "end")
        self.refresh_key_status()
        messagebox.showinfo("Gemini API", "Đã lưu khóa API riêng tại studio/.env thành công!")

    def refresh_key_status(self):
        from series_studio import own_api_key
        has_key = bool(own_api_key())
        self.lbl_key_status.configure(
            text="Đã cấu hình" if has_key else "Chưa cấu hình",
            text_color="#10B981" if has_key else "#EF4444"
        )

    def launch(self, offline: bool):
        if self.running:
            return
        premise = self.txt_prompt.get("1.0", "end").strip()
        if not premise:
            messagebox.showerror("Thiếu cốt truyện", "Vui lòng nhập ý tưởng kịch bản cho tập phim.")
            return

        series_title = self.entry_series.get().strip() or "Whiteboard Series"
        ep_num = int(self.entry_episode.get().strip() or "1")
        minutes = float(self.entry_minutes.get().strip() or "1.0")
        scene_sec = int(self.entry_scene_sec.get().strip() or "25")
        workers = int(self.opt_workers.get())
        lang = self.opt_lang.get()
        res = self.opt_res.get()
        is_mcp = self.opt_prov.get() == "MCP V2 (web)"
        if is_mcp:
            img_src = "mcp_v2"
            workers = 1
        elif self.opt_prov.get() == "Tuấn Stor (V2)":
            img_src = "v2_tuanstor"
        else:
            img_src = "gemini"

        from series_studio import slug
        self.current_series_slug = slug(series_title) + ("-offline-test" if offline else "")
        self.current_episode_num = ep_num

        inbox = HOME / "inbox"
        inbox.mkdir(exist_ok=True)
        prompt_file = inbox / f"prompt_native_{int(time.time())}.txt"
        prompt_file.write_text(premise, encoding="utf-8")

        cmd = [
            sys.executable, "-u", str(CLI), "run",
            "--mode", "offline" if offline else "live",
            "--series", series_title + (" - Offline Test" if offline else ""),
            "--episode", str(ep_num),
            "--prompt-file", str(prompt_file),
            "--minutes", str(0.15 if offline else minutes),
            "--scene-seconds", str(5 if offline else scene_sec),
            "--workers", str(workers),
            "--size", "640x360" if offline else res,
            "--language", lang,
            "--image-provider", img_src,
        ]

        if is_mcp:
            cmd.extend([
                "--mcp-model-index", "1",
                "--mcp-max-images", "25",
            ])

        self.running = True
        self.btn_live.configure(state="disabled")
        self.btn_offline.configure(state="disabled")
        self.prog_bar.set(0.05)
        self.lbl_status.configure(text="Đang xử lý... Xem nhật ký bên dưới hoặc chuyển qua tab Storyboard để xem thẻ cảnh.")

        self.append_log(f"\n--- BẮT ĐẦU SẢN XUẤT ({'OFFLINE' if offline else 'AI LIVE'}) ---\n")
        threading.Thread(target=self.worker_thread, args=(cmd,), daemon=True).start()

    def worker_thread(self, cmd):
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        proc = subprocess.Popen(cmd, cwd=str(HOME), env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        for line in proc.stdout:
            self.q.put(("log", line))
        code = proc.wait()
        self.q.put(("end", code))

    def pump_logs(self):
        try:
            while True:
                kind, val = self.q.get_nowait()
                if kind == "log":
                    self.append_log(val)
                    # Check for scene pass to update progress bar
                    m = re.search(r"SCENE_PASS\s+(\d+)", val)
                    if m:
                        self.prog_bar.set(min(0.9, self.prog_bar.get() + 0.15))
                        self.after(500, self.load_storyboard_scenes)
                elif kind == "end":
                    self.running = False
                    self.btn_live.configure(state="normal")
                    self.btn_offline.configure(state="normal")
                    if val == 0:
                        self.prog_bar.set(1.0)
                        self.lbl_status.configure(text="✅ HOÀN THÀNH XUẤT SẮC! Bấm 'Xem Video Thành Phẩm' để mở video.")
                        self.append_log("Đã hoàn tất tập phim!\n")
                        self.load_storyboard_scenes()
                    else:
                        self.lbl_status.configure(text="❌ DỪNG DO LỖI. Xem chi tiết trong nhật ký bên dưới.")
        except queue.Empty:
            pass
        self.after(150, self.pump_logs)

    def append_log(self, text):
        self.txt_console.insert("end", text)
        self.txt_console.see("end")

    def load_storyboard_scenes(self):
        for w in self.scroll_cards.winfo_children():
            w.destroy()

        if not self.current_series_slug:
            from series_studio import slug
            self.current_series_slug = slug(self.entry_series.get().strip() or "series")
            self.current_episode_num = int(self.entry_episode.get().strip() or "1")

        ep_dir = PRODUCTIONS / self.current_series_slug / f"episode_{self.current_episode_num:03d}"
        plan_p = ep_dir / "plan.json"

        if not plan_p.exists():
            lbl = ctk.CTkLabel(self.scroll_cards, text="Chưa có kịch bản phân cảnh cho tập này.\nHãy bấm 'Sản xuất' hoặc chọn đúng tập đã tạo.", text_color="#94A3B8")
            lbl.pack(pady=40)
            return

        try:
            plan = json.loads(plan_p.read_text(encoding="utf-8"))
            scenes = plan.get("scenes", [])
            for sc in scenes:
                self.create_scene_card(ep_dir, sc)
        except Exception as e:
            self.append_log(f"Lỗi khi tải Storyboard: {e}\n")

    def create_scene_card(self, ep_dir: Path, sc: dict):
        num = int(sc.get("scene_number", 1))
        sc_dir = ep_dir / "scenes" / f"scene_{num:04d}"
        img_p = sc_dir / "image.png"
        clip_p = sc_dir / "final.mp4"

        card = ctk.CTkFrame(self.scroll_cards, fg_color="#1E293B", corner_radius=10)
        card.pack(fill="x", padx=10, pady=8)
        card.grid_columnconfigure(1, weight=1)

        # Thumbnail Image Preview
        thumb_label = ctk.CTkLabel(card, text="[Chưa có ảnh]", width=160, height=90, fg_color="#0F172A", corner_radius=6)
        thumb_label.grid(row=0, column=0, rowspan=2, padx=12, pady=12)

        if img_p.exists():
            try:
                pil_img = Image.open(str(img_p))
                pil_img = pil_img.resize((160, 90), Image.Resampling.LANCZOS)
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(160, 90))
                thumb_label.configure(image=ctk_img, text="")
                self.cached_images[f"sc_{num}"] = ctk_img
            except Exception:
                pass

        # Text Details
        title = ctk.CTkLabel(card, text=f"Cảnh {num}: {sc.get('summary', 'Phân cảnh')}", font=ctk.CTkFont(size=14, weight="bold"), text_color="#F8FAFC")
        title.grid(row=0, column=1, padx=10, pady=(10, 2), sticky="w")

        narration = ctk.CTkLabel(card, text=sc.get("narration", sc.get("description", "")), font=ctk.CTkFont(size=12), text_color="#CBD5E1", wraplength=600, justify="left")
        narration.grid(row=1, column=1, padx=10, pady=(0, 10), sticky="nw")

        # Action Button for this Scene
        if clip_p.exists():
            btn_play_scene = ctk.CTkButton(card, text="▶ Xem Video Cảnh", width=130, fg_color="#4F46E5", hover_color="#4338CA",
                                           command=lambda p=clip_p: self.open_file_media(p))
            btn_play_scene.grid(row=0, column=2, rowspan=2, padx=14, pady=12)
        else:
            lbl_wait = ctk.CTkLabel(card, text="Đang đợi render...", text_color="#94A3B8")
            lbl_wait.grid(row=0, column=2, rowspan=2, padx=14, pady=12)

    def play_final_video(self):
        if not self.current_series_slug:
            from series_studio import slug
            self.current_series_slug = slug(self.entry_series.get().strip() or "series")
            self.current_episode_num = int(self.entry_episode.get().strip() or "1")

        final_path = PRODUCTIONS / self.current_series_slug / f"episode_{self.current_episode_num:03d}" / "episode_final.mp4"
        if final_path.exists():
            self.open_file_media(final_path)
        else:
            # Fallback to offline smoke test sample if exists
            fallback = HOME.parent / "offline_smoke" / "storyboard_offline_test.mp4"
            if fallback.exists():
                self.open_file_media(fallback)
            else:
                messagebox.showinfo("Chưa có video", f"Chưa tìm thấy video thành phẩm tại:\n{final_path}")

    def open_file_media(self, path: Path):
        if hasattr(os, "startfile"):
            os.startfile(str(path))
        else:
            subprocess.run(["start", str(path)], shell=True)

    def open_outputs(self):
        PRODUCTIONS.mkdir(exist_ok=True)
        if hasattr(os, "startfile"):
            os.startfile(str(PRODUCTIONS))

    def open_cinema_window(self):
        import desktop_app
        threading.Thread(target=desktop_app.main, daemon=True).start()


def main():
    app = StudioProApp()
    app.mainloop()


if __name__ == "__main__":
    main()
