"""Expose the three Studio modes, language/country voice presets and color styles.
Back up real Studio Pro Desktop assets first; never touch V2.
"""
from pathlib import Path
import shutil,py_compile,datetime
home=Path(r"D:\STORYBOARD_AI\studio")
srv=home/"web_server.py"
html=home/"web"/"index.html"
js=home/"web"/"app.js"
back=home/"checkpoints"/("multigenre_desktop_"+datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
back.mkdir(parents=True,exist_ok=True)
for p in (srv,html,js):shutil.copy2(p,back/p.name)
def edit(p,arr):
    s=p.read_text(encoding="utf-8")
    for tag,a,b in arr:
        if a not in s: raise RuntimeError("Missing anchor "+p.name+"::"+tag)
        s=s.replace(a,b,1)
    p.write_text(s,encoding="utf-8")

edit(srv,[
 ("input_req",'''                prompt = body.get("prompt", "").strip()
                if not prompt:
                    return self.end_json({"error": "Vui lòng nhập ý tưởng kịch bản!"}, 400)''',
 '''                prompt = str(body.get("prompt", "")).strip()
                input_mode = str(body.get("input_mode","idea"))
                reference_url = str(body.get("reference_url","")).strip()
                if input_mode not in ("idea","link","script"):
                    return self.end_json({"error":"Chế độ nhập không hợp lệ."},400)
                if input_mode=="link":
                    from studio_input_modes import youtube_url
                    try:
                        reference_url=youtube_url(reference_url)
                    except ValueError as exc:
                        return self.end_json({"error":str(exc)},400)
                elif not prompt:
                    return self.end_json({"error":"Vui lòng nhập ý tưởng hoặc kịch bản!"},400)
                if input_mode=="script":
                    from studio_input_modes import parse_locked_screenplay
                    try:
                        parse_locked_screenplay(prompt)
                    except ValueError as exc:
                        return self.end_json({"error":str(exc)},400)'''),
 ("genre_read",'''                mcp_max_images = int(body.get("mcp_max_images", 20))''',
 '''                mcp_max_images = int(body.get("mcp_max_images", 20))
                from studio_modes import GENRES,STYLES,REGIONS
                genre=str(body.get("genre","auto"))
                visual_style=str(body.get("visual_style","auto"))
                region=str(body.get("region","auto"))
                if genre not in GENRES or visual_style not in STYLES or region not in REGIONS:
                    return self.end_json({"error":"Thể loại, kiểu màu hoặc khu vực không hợp lệ"},400)'''),
 ("voice_auto",'''                    voice_name = validate_voice(body.get("voice_name","Kore"))''',
 '''                    raw_voice=body.get("voice_name","auto")
                    voice_name="auto" if raw_voice=="auto" else validate_voice(raw_voice)'''),
 ("cli_add",'''                    "--voice-name", voice_name,''',
 '''                    "--voice-name", voice_name,
                    "--input-mode", input_mode,
                    "--reference-url", reference_url,
                    "--genre", genre,
                    "--visual-style", visual_style,
                    "--region", region,'''),
])
# script UI additional controls, keep original right-side panels and app layout.
edit(html,[
 ("voice_auto",'''<option value="Kore" selected>Kore — dứt khoát (mặc định)</option>''',
 '''<option value="auto" selected>Tự chọn theo ngôn ngữ & thể loại</option>
                <option value="Kore">Kore — dứt khoát</option>'''),
 ("input_controls",'''        <!-- SECTION 3: KỊCH BẢN & CỐT TRUYỆN -->''',
 '''        <!-- MULTIGENRE / INPUT-MODE CONTROLS -->
        <div class="form-section" id="genreProductionMode">
          <div class="section-title">Thể Loại & Phong Cách Phim</div>
          <div class="form-grid-2">
            <div class="field-wrap">
              <label for="inGenre">Thể loại phim</label>
              <select id="inGenre">
                <option value="auto" selected>Tự nhận diện (mặc định)</option>
                <option value="stoic">Khắc kỷ / Stoicism Tây Ban Nha</option>
                <option value="family_drama">Drama gia đình</option>
                <option value="western">Western miền Viễn Tây</option>
                <option value="action">Hành động, phiêu lưu</option>
                <option value="history">Lịch sử</option>
                <option value="documentary">Phim tài liệu / kể chuyện</option>
                <option value="animation">Hoạt hình 2D/3D</option>
                <option value="whiteboard">Vẽ bảng trắng</option>
              </select>
            </div>
            <div class="field-wrap">
              <label for="inVisualStyle">Hình ảnh & dựng phim</label>
              <select id="inVisualStyle">
                <option value="auto" selected>Tự chọn theo thể loại</option>
                <option value="color_cinematic">Phim màu điện ảnh / Photorealistic</option>
                <option value="color_animation">Hoạt hình màu 2D/3D</option>
                <option value="whiteboard">Vẽ tay trên bảng trắng</option>
              </select>
            </div>
          </div>
          <div class="form-grid-2">
            <div class="field-wrap">
              <label for="inRegion">Quốc gia / kiểu phát âm</label>
              <select id="inRegion">
                <option value="auto" selected>Tự theo ngôn ngữ</option>
                <option value="ES">Tây Ban Nha (España)</option>
                <option value="MX">Mexico / Mỹ Latinh</option>
                <option value="VN">Việt Nam</option>
                <option value="US">Mỹ</option>
                <option value="GB">Anh</option>
                <option value="FR">Pháp</option>
                <option value="BR">Brazil</option>
                <option value="JP">Nhật Bản</option>
              </select>
            </div>
            <div class="field-wrap">
              <label for="inInputMode">Nguồn kịch bản</label>
              <select id="inInputMode">
                <option value="idea" selected>Ý tưởng — AI viết kịch bản</option>
                <option value="link">Link YouTube — AI phân tích tham khảo</option>
                <option value="script">Kịch bản hoàn chỉnh — khóa lời thoại</option>
              </select>
            </div>
          </div>
          <div class="field-wrap" id="youtubeUrlRow" style="display:none;margin-top:8px;">
            <label for="inReferenceUrl">Link YouTube công khai</label>
            <input type="url" id="inReferenceUrl" placeholder="https://www.youtube.com/watch?v=... hoặc https://youtu.be/...">
            <p style="font-size:.73rem;color:#94a3b8;margin-top:5px;">
              Gemini phân tích video trực tiếp để học bố cục và nhịp kể; tạo nội dung mới, không sao chép nguyên video.
            </p>
          </div>
        </div>

        <!-- SECTION 3: KỊCH BẢN & CỐT TRUYỆN -->'''),
 ("idea_label",'''          <textarea id="inPrompt" placeholder="Nhập tóm tắt kịch bản, hành trình nhân vật hoặc ý tưởng câu chuyện..."></textarea>''',
 '''          <textarea id="inPrompt" placeholder="Nhập ý tưởng phim. Chọn Link YouTube hoặc Kịch bản hoàn chỉnh ở trên nếu muốn dùng nguồn khác."></textarea>
          <p id="inputModeHint" style="font-size:.72rem;color:#94a3b8;margin:6px 0 0;">
            Chế độ Ý tưởng: AI sáng tác một kịch bản mới.
          </p>'''),
])
# Add listeners via core DOM definitions; keep other UI logic intact.
edit(js,[
 ("refs",'''  inVoice: document.getElementById("inVoice"),''',
 '''  inVoice: document.getElementById("inVoice"),
  inGenre: document.getElementById("inGenre"),
  inVisualStyle: document.getElementById("inVisualStyle"),
  inRegion: document.getElementById("inRegion"),
  inInputMode: document.getElementById("inInputMode"),
  inReferenceUrl: document.getElementById("inReferenceUrl"),'''),
 ("events",'''  // Image source toggle (MCP options)''',
 '''  if (el.inInputMode) {
    el.inInputMode.addEventListener("change", updateInputModeFields);
    updateInputModeFields();
  }

  // Image source toggle (MCP options)'''),
 ("insert_funcs",'''async function submitProduction(mode) {''',
 '''function updateInputModeFields() {
  const mode=el.inInputMode ? el.inInputMode.value : "idea";
  const linkRow=document.getElementById("youtubeUrlRow");
  const hint=document.getElementById("inputModeHint");
  if (linkRow) linkRow.style.display=mode==="link"?"block":"none";
  if (hint) hint.textContent=mode==="script" ?
    "Kịch bản sẽ giữ nguyên cảnh và câu thoại. Mỗi cảnh bắt đầu bằng SHOT 1, SHOT 2... hoặc CẢNH 1, CẢNH 2... Không viết lại nội dung." :
    mode==="link" ?
    "Gemini sẽ phân tích video công khai trực tiếp. Có thể ghi thêm ý tưởng riêng vào ô dưới." :
    "Chế độ Ý tưởng: AI sáng tác kịch bản mới.";
  if (el.inPrompt) {
    el.inPrompt.placeholder=mode==="script" ?
      "SHOT 1\\nFORMAT & STYLE: ...\\nAUDIO: ...\\nEvelyn says: \\"Lời thoại...\\"\\n\\nSHOT 2\\n..." :
      mode==="link" ?
      "Ý tưởng riêng (không bắt buộc) để tạo câu chuyện mới từ phong cách video tham khảo..." :
      "Nhập ý tưởng phim hoặc cốt truyện...";
  }
}

async function submitProduction(mode) {'''),
 ("payload",'''    language: el.inLanguage.value,
    voice_name: el.inVoice ? el.inVoice.value : "Kore",''',
 '''    language: el.inLanguage.value,
    voice_name: el.inVoice ? el.inVoice.value : "auto",
    genre: el.inGenre ? el.inGenre.value : "auto",
    visual_style: el.inVisualStyle ? el.inVisualStyle.value : "auto",
    region: el.inRegion ? el.inRegion.value : "auto",
    input_mode: el.inInputMode ? el.inInputMode.value : "idea",
    reference_url: el.inReferenceUrl ? el.inReferenceUrl.value.trim() : "",'''),
 ("empty_prompt",'''  if (!prompt) return alert("Vui lòng nhập ý tưởng cốt truyện cho tập phim!");''',
 '''  if (!prompt && !(el.inInputMode && el.inInputMode.value==="link" &&
          el.inReferenceUrl && el.inReferenceUrl.value.trim())) {
    return alert("Vui lòng nhập ý tưởng, kịch bản hoặc link YouTube công khai!");
  }'''),
])
for p in (srv,home/"series_studio.py",home/"studio_modes.py",home/"studio_input_modes.py"):
    py_compile.compile(str(p),doraise=True)
print("DESKTOP_GENRE_INPUT_LINK_SCRIPT_UI_PATCH_PASS")
print("UI_CHECKPOINT",back)
