---
name: create-youtube-thumbnail
description: Chuyên gia thiết kế thumbnail YouTube độc lập qua Google Flow. Đọc kịch bản/chủ đề để viết Prompt tạo ảnh thumbnail chuyên dụng riêng biệt (tuyệt đối không nhặt ảnh từ video), đưa câu chữ Hook 3D trực tiếp vào trong Prompt với màu sắc vàng kim / hổ phách rực rỡ bắt mắt (tuyệt đối không dùng chữ bạc đơn điệu làm chìm ảnh), Google Flow tự vẽ chữ 3D hoà nhập vào không gian ánh sáng, tải ảnh về khử sạch logo watermark là hoàn tất 100%. Hỗ trợ cả 9:16 Shorts và 16:9 Video dài.
---

# create-youtube-thumbnail — THIẾT KẾ THUMBNAIL YOUTUBE ĐỘC LẬP QUA GOOGLE FLOW

> [!IMPORTANT]
> **NGUYÊN TẮC CỐT LÕI: GOOGLE FLOW TỰ VẼ CHỮ 3D VỚI MÀU SẮC RỰC RỠ BẮT MẮT**
> - **TUYỆT ĐỐI KHÔNG NHẶT ẢNH TỪ VIDEO RA LÀM THUMBNAIL:** Khung hình cắt từ video không có độ sắc nét, không có bố cục chừa cho chữ và không đạt chuẩn visual của thumbnail triệu view.
> - **ĐƯA CÂU CHỮ HOOK VỚI MÀU SẮC BẮT MẮT VÀO PROMPT:** 
>   * Google Flow (Imagen 3 / Nano Banana) có năng lực dựng Typography 3D đỉnh cao.
>   * **TUYỆT ĐỐI KHÔNG DÙNG CHỮ BẠC / ĐÁ CẨM THẠCH TRẮNG ĐƠN ĐIỆU:** Chữ bạc hoặc cẩm thạch trắng trùng màu tượng đá sẽ bị chìm nghỉm vào hậu cảnh, làm tụt điểm bắt mắt và giảm tỷ lệ nhấp chuột (CTR).
>   * **BẢNG MÀU BẮT MẮT (HIGH-CTR PALETTES):** Sử dụng chữ **Vàng kim hoàng gia 3D rực rỡ (Radiant 3D Imperial Gold)**, kết hợp ánh viền cam hổ phách rực lửa (Blazing Amber Rim Lighting), vát cạnh 3D đổ bóng khối chiaroscuro tương phản cực mạnh với nền tối. Cỡ chữ giữ nguyên chuẩn khổng lồ uy nghi.
> - **KHÔNG CẦN DÙNG CODE PIL PHỦ CHỮ:** Tránh hoàn toàn việc dùng script Python chèn font 2D phẳng lì hay gắn pod làm mờ cục mịch.
> - **QUY TRÌNH TINH GỌN TUYỆT ĐỐI:** Viết Prompt kèm chữ 3D màu rực rỡ → Gửi lên Google Flow MCP → Tải ảnh về → Chạy khử watermark logo ngôi sao Flow (`remove_gemini_watermark`) → Xuất bản ngay vào `00_DANG_BAI_YOUTUBE`.

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
- **Cú pháp gắn chữ 3D màu sắc bắt mắt trong Prompt:**
  * **Khi có 2 dòng chữ:**
    `featuring giant monumental 3D extruded typography stamped boldly across the chest and draped toga in the lower half reading "LINE_1" in radiant 3D burnished imperial gold with razor-sharp specular highlights and "LINE_2" in blazing molten amber-gold with intense electric warm rim lighting, heavy contact shadows, dramatic 3D block extrusion, tight heroic portrait, never a severed bust on a pedestal, never cut off, photorealistic 8k, no watermark.`
  * **Khi có 1 dòng chữ / 1 cụm từ:**
    `featuring giant monumental 3D extruded typography stamped boldly across the chest and draped toga in the lower half reading "HOOK" in radiant 3D burnished imperial gold with glowing molten amber rim lighting, razor-sharp specular highlights, dramatic 3D block extrusion, and deep heavy contact shadows, tight heroic portrait, photorealistic 8k, no watermark.`
- **Ví dụ thực tế:**
  `...reading "DOMINA" in radiant 3D burnished imperial gold and "TU MENTE" in blazing molten amber-gold with intense electric warm rim lighting...`

### B. Định dạng Video Dài (Khung Ngang 16:9 — 1280 x 720 hoặc 1920 x 1080)
- **Bố cục 50/50:**
  * **Nửa bên phải (Right 50%):** Chủ thể cận cảnh nhìn hướng sang trái.
  * **Nửa bên trái (Left 50%):** Dành trọn vẹn cho bộ chữ 3D khổng lồ với ánh sáng thể tích (volumetric lighting) và bóng đổ khối.
- **Cú pháp gắn chữ 3D màu sắc bắt mắt trong Prompt:**
  * **Khi có 2 dòng chữ:**
    `occupying the entire LEFT 50% with giant monumental 3D extruded typography reading "LINE_1" in radiant 3D burnished imperial gold with razor-sharp specular highlights and "LINE_2" in blazing molten amber-gold with intense electric warm rim lighting, with dramatic 3D block extrusion, contact shadows, cinematic volumetric lighting, 16:9 horizontal, photorealistic 8k render, no watermark.`
  * **Khi có 1 dòng chữ / 1 cụm từ:**
    `occupying the entire LEFT 50% with giant monumental 3D extruded typography reading "HOOK" in radiant 3D burnished imperial gold with glowing molten amber rim lighting, razor-sharp specular highlights, dramatic 3D block extrusion, heavy contact shadows, cinematic volumetric lighting, 16:9 horizontal, photorealistic 8k render, no watermark.`
- **Ví dụ thực tế:**
  `...reading "ALÉJATE" in radiant 3D burnished imperial gold and "EN SILENCIO" in blazing molten amber-gold with intense electric warm rim lighting...`

---

## 3. BẢNG MẪU PROMPT THEO THỂ LOẠI (FLOW TỰ VẼ CHỮ BẮT MẮT)

| Thể loại (Genre) | Prompt Mẫu Gửi Lên Google Flow (Màu Sắc 3D Bắt Mắt) | Hook Chữ 3D |
| :--- | :--- | :--- |
| **Stoic (Khắc kỷ 9:16)** | `Monumental heroic classical sculpted marble statue of a Stoic philosopher god, towering heroic portrait in vertical 9:16 framing filling canvas from top to bottom, majestic chiseled stone head occupying upper 55%, broad muscular shoulders and draped Roman toga flowing to the bottom border, dramatic warm golden rim lighting, ancient ruins in background, featuring giant monumental 3D extruded typography stamped boldly across the chest reading "DOMINA" in radiant 3D burnished imperial gold with razor-sharp specular highlights and "TU MENTE" in blazing molten amber-gold with intense electric warm rim lighting, heavy contact shadows, never a bust on a pedestal, photorealistic 8k, no watermark.` | `DOMINA` / `TU MENTE` |
| **Stoic (Khắc kỷ 16:9)** | `Monumental heroic classical sculpted marble and bronze statue of a Stoic philosopher god, deeply chiseled stone anatomy, massive sculpted bare shoulder, deeply carved curly stone beard, draped crimson toga, magnificent illuminated Acropolis on distant hill under deep starry twilight, sculpture strictly occupying the RIGHT 50% facing left, occupying the entire LEFT 50% with giant monumental 3D extruded typography reading "ALÉJATE" in radiant 3D burnished imperial gold with razor-sharp specular highlights and "EN SILENCIO" in blazing molten amber-gold with intense electric warm rim lighting, dramatic 3D block extrusion, contact shadows, cinematic 16:9, photorealistic 8k, no watermark.` | `ALÉJATE` / `EN SILENCIO` |
| **Drama (Phim kịch)** | `High-stakes intense cinematic drama film still about the conflict, emotional close-up portrait of character with piercing fierce defiant gaze on the right, warm volumetric 3-point rim lighting carving facial contours, blurred dramatic confrontation in background, deep sapphire and golden amber grading, occupying the entire left 50% with giant monumental 3D typography reading "LA TRAICIÓN" in radiant 3D warm gold with sharp specular highlights and "LA VERDAD" in electric crimson red bevel and heavy contact shadows, 8k resolution, no watermark.` | `LA TRAICIÓN` / `SỰ THẬT TÀN NHẪN` |
| **Whiteboard (Vẽ tay)** | `After Skool viral YouTube illustration: vibrant colorful POSCA markers on off-white art paper, intricate sacred geometry, glowing third eye, detailed Tree of Life, rich vivid rainbow marker colors with crisp black ink outlines, featuring giant hand-drawn 3D block lettering reading "THỨC TỈNH" in radiant sunburst yellow and "TÂM TRÍ" in vibrant electric orange-amber with bold black 3D shadow outlines, surreal and highly detailed, no watermark.` | `THỨC TỈNH` / `TÂM TRÍ` |

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
