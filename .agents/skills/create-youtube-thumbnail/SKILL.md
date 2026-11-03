---
name: create-youtube-thumbnail
description: Chuyên gia thiết kế thumbnail YouTube độc lập qua Google Flow. Đọc kịch bản/chủ đề để viết Prompt tạo ảnh thumbnail chuyên dụng riêng biệt (tuyệt đối không nhặt ảnh từ video), đưa câu chữ Hook 3D trực tiếp vào trong Prompt với công thức 3 màu bắt mắt đỉnh cao Vàng kim hoàng gia + Đỏ thẫm điện ảnh + Trắng tinh khiết titan (tuyệt đối không dùng 1 màu đơn điệu hay chữ bạc làm chìm ảnh), Google Flow tự vẽ chữ 3D hoà nhập vào không gian ánh sáng chiaroscuro, tải ảnh về khử sạch logo watermark là hoàn tất 100%. Hỗ trợ cả 9:16 Shorts và 16:9 Video dài, đạt 95-100 điểm VidIQ thực chiến.
---

# create-youtube-thumbnail — THIẾT KẾ THUMBNAIL YOUTUBE ĐỘC LẬP QUA GOOGLE FLOW

> [!IMPORTANT]
> **NGUYÊN TẮC CỐT LÕI: GOOGLE FLOW TỰ VẼ CHỮ 3D VỚI CÔNG THỨC 3 MÀU BẮT MẮT ĐỈNH CAO (VÀNG + ĐỎ + TRẮNG)**
> - **TUYỆT ĐỐI KHÔNG NHẶT ẢNH TỪ VIDEO RA LÀM THUMBNAIL:** Khung hình cắt từ video không có độ sắc nét, không có bố cục chừa cho chữ và không đạt chuẩn visual của thumbnail triệu view.
> - **CÔNG THỨC 3 MÀU ĐỈNH CAO (TRI-CHROMATIC HIGH-CTR PALETTE):** 
>   * **Dòng 1 (Từ khóa Hook / Power Word):** Chữ **Vàng kim hoàng gia 3D rực rỡ (Radiant 3D Imperial Gold - #FFD700)**, điểm chói phản chiếu ánh mặt trời (sun-flare specular highlights) thu hút ánh nhìn ngay trong 0.05 giây đầu tiên.
>   * **Đường cắt / Viền vát (Razor Divider / Bevel Trim):** **Đỏ thẫm điện ảnh sắc lẹm (Cinematic Crimson Red - #DC2626)** tạo độ căng thẳng tâm lý, cảnh báo và phân tách sắc nét.
>   * **Dòng 2 (Chủ đề cốt lõi / Body Topic):** Chữ **Trắng tinh khiết titan 3D (Crisp Pure 3D Titanium White - #FFFFFF)** với khối bóng đổ đen sâu thẳm (deep extruded black block shadows) đảm bảo đọc rõ 100% trên màn hình điện thoại di động nhỏ (120x68px).
>   * **TUYỆT ĐỐI KHÔNG DÙNG 1 MÀU ĐƠN ĐIỆU HOẶC CHỮ BẠC:** Chữ 1 màu hoặc màu bạc mờ nhạt sẽ bị chìm nghỉm vào nền tượng đá và kiến trúc cổ, làm tụt điểm visual và giảm CTR.
> - **KHÔNG CẦN DÙNG CODE PIL PHỦ CHỮ:** Tránh hoàn toàn việc dùng script Python chèn font 2D phẳng lì hay gắn pod làm mờ cục mịch.
> - **QUY TRÌNH TINH GỌN TUYỆT ĐỐI:** Viết Prompt kèm chữ 3D theo công thức Vàng + Đỏ + Trắng → Gửi lên Google Flow MCP → Tải ảnh về → Chạy khử watermark logo ngôi sao Flow (`clean_watermark.py`) → Xuất bản ngay vào `00_DANG_BAI_YOUTUBE` đạt 95–100 điểm VidIQ.

---

## 1. QUY TRÌNH THIẾT KẾ THUMBNAIL TINH GỌN (3 BƯỚC)

```
[Kịch bản / Ý tưởng video]
           │
           ▼
[Bước 1: Viết Prompt Thumbnail Kèm Chữ 3D Rực Rỡ Bắt Mắt]
   ├── Xác định Thể loại & Tỷ lệ (9:16 Shorts hoặc 16:9 Video dài)
   ├── Câu chữ Hook: 2-3 từ (Shorts) hoặc 3-5 từ (16:9)
   └── Đưa text vào prompt với màu vàng kim / hổ phách:
       `featuring giant 3D extruded typography reading "HOOK" in radiant 3D burnished imperial gold...`
           │
           ▼
[Bước 2: Gửi Prompt lên Google Flow MCP]
   ├── Gọi API / MCP Google Flow để sinh ảnh mới 100%
   └── Flow tự động vẽ chủ thể + chữ 3D vàng kim bắt mắt hòa quyện cùng ánh sáng chiaroscuro
           │
           ▼
[Bước 3: Tải về & Khử Logo Watermark]
   ├── Chạy clean_watermark.py (Navier-Stokes inpainting) xoá sạch logo ngôi sao ở góc
   └── Lưu ngay thành thumbnail_shorts.jpg hoặc thumbnail_seo.jpg sẵn sàng đăng bài!
```

---

## 2. CÔNG THỨC VIẾT PROMPT KÈM CHỮ 3D CHO GOOGLE FLOW

### A. Định dạng YouTube Shorts (Khung Dọc 9:16 — 1080 x 1920)
- **Bố cục khung hình:**
  * **Nửa trên (Upper 55%):** Chân dung cận cảnh uy nghiêm (tượng thần, nhân vật chính biểu cảm mãnh liệt), ánh sáng viền vàng kim sắc nét (dramatic golden rim lighting).
  * **Nửa dưới (Lower 45%):** Bờ vai cơ bắp và nếp áo toga/trang phục trải dài đến tận mép đáy (không bao giờ vẽ tượng cụt lủn trên đôn).
- **Cú pháp gắn chữ 3D theo công thức 3 màu (Vàng + Đỏ + Trắng) trong Prompt:**
  * **Khi có 2 dòng chữ:**
    `featuring giant monumental 3D extruded typography stamped boldly across the chest and draped toga in the lower half reading "LINE_1" in radiant 3D burnished imperial gold (#FFD700) with brilliant specular highlights and accentuated by an electric cinematic crimson red 3D razor divider line and crimson bevel trims (#DC2626), and "LINE_2" in crisp pure 3D titanium white (#FFFFFF) with heavy black block extrusion and deep chiaroscuro contact shadows, tight heroic portrait, never a severed bust on a pedestal, never cut off, photorealistic 8k, no watermark.`
  * **Khi có 1 dòng chữ / 1 cụm từ:**
    `featuring giant monumental 3D extruded typography stamped boldly across the chest and draped toga in the lower half reading "HOOK" in radiant 3D burnished imperial gold (#FFD700) with electric crimson red bevel trims (#DC2626), crisp pure titanium white specular edge highlights (#FFFFFF), razor-sharp 3D block extrusion, and deep chiaroscuro contact shadows, tight heroic portrait, photorealistic 8k, no watermark.`
- **Ví dụ thực tế:**
  `...reading "DOMINA" in radiant 3D burnished imperial gold (#FFD700) with electric crimson red razor divider (#DC2626) and "TU MENTE" in crisp pure 3D titanium white (#FFFFFF) with heavy black block extrusion...`

### B. Định dạng Video Dài (Khung Ngang 16:9 — 1280 x 720 hoặc 1920 x 1080)
- **Bố cục 50/50:**
  * **Nửa bên phải (Right 50%):** Chủ thể cận cảnh nhìn hướng sang trái.
  * **Nửa bên trái (Left 50%):** Dành trọn vẹn cho bộ chữ 3D khổng lồ với ánh sáng thể tích (volumetric lighting) và bóng đổ khối chiaroscuro.
- **Cú pháp gắn chữ 3D theo công thức 3 màu (Vàng + Đỏ + Trắng) trong Prompt:**
  * **Khi có 2 dòng chữ:**
    `occupying the entire LEFT 50% with giant monumental 3D extruded typography reading "LINE_1" in radiant 3D burnished imperial gold (#FFD700) with brilliant specular highlights and accentuated by an electric cinematic crimson red 3D razor divider line and crimson bevel trims (#DC2626), and "LINE_2" in crisp pure 3D titanium white (#FFFFFF) with heavy black block extrusion, deep contact shadows, cinematic volumetric lighting, 16:9 horizontal, photorealistic 8k render, no watermark.`
  * **Khi có 1 dòng chữ / 1 cụm từ:**
    `occupying the entire LEFT 50% with giant monumental 3D extruded typography reading "HOOK" in radiant 3D burnished imperial gold (#FFD700) with electric crimson red bevel trims (#DC2626), crisp pure titanium white specular edge highlights (#FFFFFF), razor-sharp 3D block extrusion, deep contact shadows, cinematic volumetric lighting, 16:9 horizontal, photorealistic 8k render, no watermark.`
- **Ví dụ thực tế:**
  `...reading "ALÉJATE" in radiant 3D burnished imperial gold (#FFD700) with electric crimson red bevel trims (#DC2626) and "EN SILENCIO" in crisp pure 3D titanium white (#FFFFFF) with heavy black block extrusion...`

---

## 3. BẢNG MẪU PROMPT THEO THỂ LOẠI (CÔNG THỨC 3 MÀU VÀNG + ĐỎ + TRẮNG)

| Thể loại (Genre) | Prompt Mẫu Gửi Lên Google Flow (Màu Sắc 3D Bắt Mắt Vàng + Đỏ + Trắng) | Hook Chữ 3D |
| :--- | :--- | :--- |
| **Stoic (Khắc kỷ 9:16)** | `Monumental heroic classical sculpted marble statue of a Stoic philosopher god, towering heroic portrait in vertical 9:16 framing filling canvas from top to bottom, majestic chiseled stone head occupying upper 55%, broad muscular shoulders and draped Roman toga flowing to the bottom border, dramatic warm golden rim lighting, ancient ruins in background, featuring giant monumental 3D extruded typography stamped boldly across the chest reading "DOMINA" in radiant 3D burnished imperial gold (#FFD700) with brilliant specular highlights and electric crimson red razor divider (#DC2626) and "TU MENTE" in crisp pure 3D titanium white (#FFFFFF) with heavy black block extrusion and deep chiaroscuro contact shadows, never a bust on a pedestal, photorealistic 8k, no watermark.` | `DOMINA` / `TU MENTE` |
| **Stoic (Khắc kỷ 16:9)** | `Monumental heroic classical sculpted marble and bronze statue of a Stoic philosopher god, deeply chiseled stone anatomy, massive sculpted bare shoulder, deeply carved curly stone beard, draped crimson toga, magnificent illuminated Acropolis on distant hill under deep starry twilight, sculpture strictly occupying the RIGHT 50% facing left, occupying the entire LEFT 50% with giant monumental 3D extruded typography reading "ALÉJATE" in radiant 3D burnished imperial gold (#FFD700) with brilliant specular highlights and accentuated by an electric cinematic crimson red 3D razor divider line and crimson bevel trims (#DC2626), and "EN SILENCIO" in crisp pure 3D titanium white (#FFFFFF) with heavy black block extrusion, deep contact shadows, cinematic volumetric lighting, 16:9 horizontal, photorealistic 8k render, no watermark.` | `ALÉJATE` / `EN SILENCIO` |
| **Drama (Phim kịch)** | `High-stakes intense cinematic drama film still about the conflict, emotional close-up portrait of character with piercing fierce defiant gaze on the right, warm volumetric 3-point rim lighting carving facial contours, blurred dramatic confrontation in background, deep sapphire and golden amber grading, occupying the entire left 50% with giant monumental 3D typography reading "LA TRAICIÓN" in radiant 3D imperial gold (#FFD700) with sharp specular highlights, razor divider in electric crimson red (#DC2626), and "LA VERDAD" in crisp pure 3D titanium white (#FFFFFF) with heavy black block extrusion and dramatic shadows, 8k resolution, no watermark.` | `LA TRAICIÓN` / `LA VERDAD` |
| **Whiteboard (Vẽ tay)** | `After Skool viral YouTube illustration: vibrant colorful POSCA markers on off-white art paper, intricate sacred geometry, glowing third eye, detailed Tree of Life, rich vivid rainbow marker colors with crisp black ink outlines, featuring giant hand-drawn 3D block lettering reading "THỨC TỈNH" in radiant sunburst yellow with electric marker red bevel outlines, and "TÂM TRÍ" in crisp clean white block lettering with bold black 3D shadow outlines and red accent underlines, surreal and highly detailed, no watermark.` | `THỨC TỈNH` / `TÂM TRÍ` |

---

## 4. LỆNH GỌI THỰC THI TRONG STORYBOARD AI

```python
from studio.seo_packager import generate_thumbnail_with_flow

result = generate_thumbnail_with_flow(
    episode_dir="path/to/episode",
    series_name="tên_series",
    genre="stoic",                     # Thể loại video
    aspect_ratio="9:16",               # '9:16' cho Shorts, '16:9' cho video dài
    hook_text="DOMINA TU MENTE",       # Câu chữ 3D Flow tự vẽ vào ảnh với màu vàng kim / hổ phách
    custom_prompt=None                 # Tự động ráp prompt kèm text nếu None
)

# Kết quả: Flow tự vẽ ảnh + chữ 3D vàng kim rực rỡ, code tự xoá watermark ngôi sao, lưu thẳng vào:
# - thumbnail_shorts.jpg (nếu 9:16)
# - thumbnail_seo.jpg (nếu 16:9)
# - 00_DANG_BAI_YOUTUBE/
```
