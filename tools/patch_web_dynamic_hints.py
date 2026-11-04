import re

def patch():
    html_path = "D:/STORYBOARD_AI/studio/web/index.html"
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Add btnSuggestIdea next to btnAnalyzeLink
    old_btn = '<button type="button" class="btn btn-secondary btn-xs" id="btnAnalyzeLink"'
    new_btn = '<button type="button" class="btn btn-secondary btn-xs" id="btnSuggestIdea" style="display:inline-flex;padding:2px 7px;font-size:0.66rem;color:#f59e0b;border-color:rgba(245,158,11,0.4);" title="Gợi ý cốt truyện triệu view chuẩn thể loại">✨ Gợi Ý Ý Tưởng</button>\n                <button type="button" class="btn btn-secondary btn-xs" id="btnAnalyzeLink"'

    if "btnSuggestIdea" not in html:
        if old_btn not in html:
            print("ERROR: old_btn not found in index.html")
            return False
        html = html.replace(old_btn, new_btn, 1)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        print("SUCCESS: index.html patched with btnSuggestIdea")
    else:
        print("INFO: index.html already has btnSuggestIdea")

    # Patch app.js
    app_path = "D:/STORYBOARD_AI/studio/web/app.js"
    with open(app_path, "r", encoding="utf-8") as f:
        app = f.read()

    genre_presets_block = '''
const GENRE_PROMPT_PRESETS = {
  stoic: [
    { label: "🏛️ Làm chủ tâm trí", text: "Làm chủ tâm trí: Khám phá triết lý Khắc kỷ của hoàng đế Marcus Aurelius. Nghệ thuật giữ tâm bất biến giữa dòng đời vạn biến, buông bỏ những điều nằm ngoài tầm kiểm soát và đánh thức sức mạnh nội tâm vững vàng như tượng đá cẩm thạch trước bão giông." },
    { label: "⚡ Nghệ thuật buông bỏ", text: "Nghệ thuật buông bỏ và tĩnh lặng: Bí quyết người thông thái im lặng rút lui khỏi những ồn ào vô nghĩa, thanh lọc các mối quan hệ độc hại và tìm thấy tự do đích thực trong tâm hồn." },
    { label: "🛡️ Bản lĩnh nghịch cảnh", text: "Bản lĩnh trước nghịch cảnh: Chuyển hóa khó khăn thành đòn bẩy phát triển bản thân. Bài học từ những suy tưởng sâu sắc giúp vượt qua mọi khủng hoảng cuộc đời với sự điềm tĩnh phi thường." }
  ],
  family_drama: [
    { label: "💔 Bữa cơm chia tài sản", text: "Bữa cơm gia đình định mệnh: Đêm họp mặt đầy sóng gió của ba thế hệ khi bức di chúc bí mật của người cha bất ngờ được mở ra. Những mâu thuẫn âm ỉ bùng nổ, sự thật cay đắng về lòng hiếu thảo và bài học xót xa về tình thân." },
    { label: "⚖️ Bí mật của người cha", text: "Gánh nặng của người cha thợ may: 30 năm hy sinh thầm lặng của người cha nghèo nuôi hai đứa con ăn học thành tài, chỉ đến ngày con thành đạt mới thấu hiểu vết sẹo hằn sâu trên lưng cha và bài học nghẹn ngào về sự tha thứ." },
    { label: "🏡 Căn nhà cổ 3 đời", text: "Trận chiến giữ căn nhà từ đường: Mối giằng xé giữa người con cả muốn bảo tồn cội nguồn gia tộc và các em muốn bán đất đổi đời. Cuộc đối đầu đẫm nước mắt trong ngày giỗ mẹ." }
  ],
  mafia_thriller: [
    { label: "🌧️ Đêm mưa trừng phạt", text: "Thế giới ngầm và luật im lặng: Trận đấu trí nghẹt thở giữa viên thanh tra dày dạn kinh nghiệm và ông trùm mafia quyền lực bậc nhất thành phố trong một đêm mưa bão rực sáng ánh đèn neon, nơi ranh giới giữa chính nghĩa và phản bội bị xóa nhòa." },
    { label: "♟️ Bẫy gián điệp", text: "Cán cân quyền lực: Cuộc thanh trừng nội bộ trong tập đoàn mafia khi phát hiện kẻ chỉ điểm. Kế hoạch lật mặt tinh vi đến từng giây phút nghẹt thở." }
  ],
  psychological_horror: [
    { label: "🕯️ Tiếng gõ cửa 3h sáng", text: "Cơn ác mộng lúc 3 giờ sáng: Người đàn ông một mình trong căn hộ tầng 13 bắt đầu nghe thấy những tiếng thì thầm sau bức tường và chiếc gương soi phản chiếu một hành động mà anh ta không hề làm. Ranh giới mong manh giữa sự hoang tưởng và thực tại rùng rợn." },
    { label: "🪞 Ảo giác gương vỡ", text: "Bí mật dưới tầng hầm: Chuyến trở về ngôi nhà thời thơ ấu và những ký ức kinh hoàng bị chôn vùi bắt đầu thức giấc theo từng tiếng tích tắc của chiếc đồng hồ quả lắc." }
  ],
  romance_melodrama: [
    { label: "🌧️ Chia tay dưới mưa", text: "Mối tình thanh xuân trắc trở: Cuộc gặp lại bất ngờ sau 7 năm chia ly giữa hai người từng thề non hẹn biển. Giọt nước mắt nghẹn ngào dưới cơn mưa chiều khi nhận ra tình cảm năm xưa chưa từng phai nhạt, nhưng khoảng cách cuộc đời đã quá lớn." },
    { label: "💍 Hôn ước không tình yêu", text: "Hi sinh vì gia đình: Cuộc hôn nhân sắp đặt và hành trình chạm tới trái tim người lạnh lùng bằng sự chân thành, vượt qua định kiến xã hội và những hiểu lầm nghiệt ngã." }
  ],
  whiteboard: [
    { label: "🧠 Hiệu ứng Dunning-Kruger", text: "Tâm lý học hành vi: Giải mã hiệu ứng Dunning-Kruger và cái bẫy của sự tự tin mù quáng. Tại sao người càng thiếu hiểu biết lại càng tự tin, và bí quyết rèn luyện tư duy phản biện để làm chủ cuộc đời qua các hình vẽ minh họa bảng trắng After Skool." },
    { label: "⏳ Định luật Parkinson", text: "Nghệ thuật quản lý thời gian: Tại sao công việc luôn kéo dài tương ứng với lượng thời gian được giao? Bí quyết áp dụng định luật Parkinson và quy tắc 80/20 để nhân 10 hiệu suất làm việc." },
    { label: "💰 Tư duy người giàu", text: "Tâm lý học về tiền bạc: Sự khác biệt cốt lõi giữa tài sản và tiêu sản, cách người giàu tư duy về đòn bẩy và sự kiên nhẫn tích lũy giá trị dài hạn." }
  ],
  colored_marker: [
    { label: "🧠 Hiệu ứng Dunning-Kruger", text: "Tâm lý học hành vi: Giải mã hiệu ứng Dunning-Kruger và cái bẫy của sự tự tin mù quáng. Tại sao người càng thiếu hiểu biết lại càng tự tin, và bí quyết rèn luyện tư duy phản biện để làm chủ cuộc đời qua các hình vẽ minh họa bảng trắng After Skool." },
    { label: "⏳ Định luật Parkinson", text: "Nghệ thuật quản lý thời gian: Tại sao công việc luôn kéo dài tương ứng với lượng thời gian được giao? Bí quyết áp dụng định luật Parkinson và quy tắc 80/20 để nhân 10 hiệu suất làm việc." }
  ],
  animation: [
    { label: "🐾 Chú mèo ma thuật", text: "Cuộc phiêu lưu vào Rừng Đom Đóm: Chú mèo mướp tinh nghịch vô tình nhặt được chiếc la bàn cổ tích và bước vào chuyến thám hiểm kỳ thú giải cứu vương quốc bánh kẹo khỏi phù thủy bóng đêm, bài học xúc động về lòng dũng cảm và tình bạn." },
    { label: "🚀 Cậu bé và vì sao nhỏ", text: "Chuyến bay vượt dải ngân hà: Hành trình của chú robot nhỏ đi tìm nguồn năng lượng ánh sáng để cứu hành tinh quê hương, ngập tràn màu sắc rực rỡ và những điều kỳ diệu." }
  ],
  history: [
    { label: "⚔️ Hào khí Bạch Đằng", text: "Bạch Đằng giang dậy sóng: Chiến thuật cắm cọc gỗ đi vào huyền thoại của Trần Hưng Đạo đánh tan đoàn thuyền giặc Nguyên Mông. Khí thế ngút trời của quân dân Đại Việt bảo vệ từng tấc đất quê hương." },
    { label: "🏛️ Thành Đa Bang bất khuất", text: "Hành trình hào hùng: Cuộc vây hãm thành Đa Bang và ý chí quật cường của nhân dân Đại Việt. Mở đầu bằng sự uy nghi của kinh thành, cao trào là trận chiến quyết định với hỏa hổ và voi chiến." }
  ],
  documentary: [
    { label: "🌌 Bí ẩn hố đen", text: "Bí ẩn hố đen vũ trụ: Chuyến du hành xuyên không gian giải mã điểm kỳ dị Gravitational Singularity và Chân trời sự kiện Event Horizon. Cách mà lực hấp dẫn bẻ cong ánh sáng và thời gian ngừng trôi." },
    { label: "🚢 Thảm kịch Titanic", text: "Đêm định mệnh của con tàu không thể chìm: Giải mã chuỗi sai lầm định mệnh dẫn đến thảm kịch Titanic năm 1912 và những câu chuyện xúc động về danh dự con người trong giây phút sinh tử." }
  ],
  western: [
    { label: "🤠 Đấu súng hoàng hôn", text: "Hoàng hôn trên miền Viễn Tây: Cuộc chạm trán sinh tử giữa tay súng cô độc và băng cướp khét tiếng tại thị trấn cát bụi rực đỏ ánh tà dương, bảo vệ công lý và danh dự người quân tử." }
  ],
  action: [
    { label: "🏎️ Rượt đuổi nghẹt thở", text: "Cuộc đào thoát trong gang tấc: 24 giờ nghẹt thở của người cựu điệp viên bị gài bẫy, đơn độc truy tìm sự thật giữa vòng vây sát thủ và máy bay không người lái của tổ chức phản diện." }
  ]
};

function updateHintChipsForGenre(genre) {
  const row = document.getElementById("hintChipsRow");
  if (!row) return;
  const g = String(genre || "stoic").trim().toLowerCase();
  const presets = GENRE_PROMPT_PRESETS[g] || GENRE_PROMPT_PRESETS["stoic"] || [];
  row.innerHTML = "";
  presets.forEach((item, idx) => {
    const chip = document.createElement("span");
    chip.className = "hint-chip";
    chip.textContent = item.label;
    chip.title = item.text;
    chip.addEventListener("click", () => {
      if (el.inPrompt) {
        el.inPrompt.value = item.text;
        el.inPrompt.focus();
        showToast("💡 Đã nạp ý tưởng: " + item.label);
      }
    });
    row.appendChild(chip);
  });
}
'''

    if "function updateHintChipsForGenre" not in app:
        # Replace applyPromptPreset
        target_fn = 'function applyPromptPreset(type) {'
        if target_fn not in app:
            print("ERROR: target_fn not found in app.js")
            return False

        # Find the end of applyPromptPreset
        p1 = app.find(target_fn)
        p2 = app.find('}', p1)
        p2 = app.find('}', p2 + 1) # inner dict and fn closing

        # Let's cleanly insert GENRE_PROMPT_PRESETS right before applyPromptPreset
        app = app[:p1] + genre_presets_block + "\n" + app[p1:]
        print("SUCCESS: genre_presets_block injected into app.js")

    # Connect inGenre change and DOMContentLoaded
    target_change = 'updateMcpProjectForGenre();'
    if target_change in app and 'updateHintChipsForGenre(el.inGenre.value);' not in app:
        app = app.replace(target_change, target_change + '\n      if (typeof updateHintChipsForGenre === "function") updateHintChipsForGenre(el.inGenre.value);')
        print("SUCCESS: connected updateHintChipsForGenre to inGenre change")

    # Connect updateInputModeFields
    target_mode = 'if (hintChips) hintChips.style.display = "flex";'
    if target_mode in app and 'updateHintChipsForGenre' not in app[app.find(target_mode):app.find(target_mode)+150]:
        app = app.replace(target_mode, target_mode + '\n    const btnSuggest = document.getElementById("btnSuggestIdea");\n    if (btnSuggest) btnSuggest.style.display = "inline-flex";\n    if (typeof updateHintChipsForGenre === "function") updateHintChipsForGenre(el.inGenre ? el.inGenre.value : "stoic");')
        print("SUCCESS: connected updateHintChipsForGenre to updateInputModeFields")

    # Connect btnSuggestIdea click listener
    init_hook = 'const btnSuggestIdea = document.getElementById("btnSuggestIdea");'
    if init_hook not in app:
        btn_listener = '''
  const btnSuggestIdea = document.getElementById("btnSuggestIdea");
  if (btnSuggestIdea) {
    let _suggestIdx = 0;
    btnSuggestIdea.addEventListener("click", () => {
      const g = el.inGenre ? el.inGenre.value : "stoic";
      const presets = GENRE_PROMPT_PRESETS[g] || GENRE_PROMPT_PRESETS["stoic"] || [];
      if (!presets.length) return;
      const pick = presets[_suggestIdx % presets.length];
      _suggestIdx++;
      if (el.inPrompt) {
        el.inPrompt.value = pick.text;
        el.inPrompt.focus();
        showToast("✨ AI Gợi ý: " + pick.label);
      }
    });
  }
'''
        # Inject right after Quick Prompt Chips
        target_chips = '// Quick Prompt Chips'
        if target_chips in app:
            pos = app.find(target_chips)
            app = app[:pos] + btn_listener + "\n  " + app[pos:]
            print("SUCCESS: btnSuggestIdea listener injected")

    # Also hide btnSuggestIdea in script and link modes
    target_hide_link = 'if (btnScan) btnScan.style.display = "inline-flex";'
    if target_hide_link in app and 'btnSuggest.style.display = "none"' not in app:
        app = app.replace(target_hide_link, target_hide_link + '\n    const btnSuggest = document.getElementById("btnSuggestIdea");\n    if (btnSuggest) btnSuggest.style.display = "none";')
        print("SUCCESS: hide btnSuggest in link mode")

    with open(app_path, "w", encoding="utf-8") as f:
        f.write(app)
    print("All frontend dynamic hint patches applied to app.js successfully!")
    return True

if __name__ == "__main__":
    patch()
