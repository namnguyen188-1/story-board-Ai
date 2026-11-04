---
name: publish-youtube-shorts
description: Tạo trọn bộ nội dung đăng YouTube Shorts (khung dọc 9:16, <60s) đồng bộ 100% từ kịch bản/video thực tế. Bao gồm tiêu đề siêu ngắn <50 ký tự kèm #Shorts, mô tả súc tích lọc sạch link đối thủ, đúng 5 hashtag, thẻ tag thực thể, gói prompt chi tiết cho Google Flow tạo thumbnail 9:16 kèm chữ 3D vàng kim/hổ phách rực rỡ bắt mắt né vùng an toàn UI, cấu hình xuất bản YouTube Studio (ngôn ngữ & chứng nhận phụ đề chuẩn FCC), và bình luận ghim kích thích tranh luận. Kiểm định kỹ thuật thực tế, không dùng điểm số ảo.
---

# publish-youtube-shorts — TRỌN BỘ XUẤT BẢN YOUTUBE SHORTS (9:16)

> [!IMPORTANT]
> **ĐẶC THÙ CỦA YOUTUBE SHORTS (KHUNG DỌC 9:16, THỜI LƯỢNG < 60S)**
> - Khán giả Shorts lướt cực nhanh, quyết định bấm vào hoặc xem tiếp chỉ trong **1.5 giây**.
> - Không dùng logic mô tả dài, timestamps nhiều chương hay thumbnail 16:9 của video dài.
> - Toàn bộ các thành phần xuất bản phải **đồng nhất 100% về ngôn ngữ và thông điệp cốt lõi** với kịch bản/video gốc.
> - **Màu sắc Thumbnail 3D phải bắt mắt:** Tuyệt đối không dùng chữ bạc đơn điệu; dùng màu vàng kim hoàng gia và cam hổ phách rực lửa để điểm bắt mắt (CTR) đạt tối đa.

---

## 1. QUY CHUẨN CÁC THÀNH PHẦN XUẤT BẢN SHORTS

### 1. Tiêu đề YouTube Shorts (Title)
- **Độ dài vàng:** Dưới **50 ký tự** (tối đa 60 ký tự) để hiển thị trọn vẹn trên màn hình điện thoại di động mà không bị dấu ba chấm `...` cắt cụt.
- **Cấu trúc:** `[CÂU HOOK KỊCH TÍNH IN HOA HOẶC KHƠI GỢI TÒ MÒ] #Shorts`
- **Ví dụ tiếng Tây Ban Nha:**
  * `EL SECRETO QUE CAMBIA TODO #Shorts`
  * `DOMINA TU MENTE EN 30 SEGUNDOS #Shorts`
  * `NO REACCIONES, OBSERVA #Shorts`
- **Ví dụ tiếng Việt:**
  * `ĐỪNG BẬT LẠI KHI BỊ COI THƯỜNG #Shorts`
  * `BÍ MẬT CỦA SỰ IM LẶNG #Shorts`

### 2. Mô tả video (Description)
- **Độ dài:** Cực kỳ súc tích (1 – 3 câu ngắn), tập trung vào thông điệp mở đầu gây chấn động.
- **Bộ lọc an toàn tuyệt đối:** **QUÉT SẠCH 100% LINK ĐỐI THỦ**, link donate, Telegram, hoặc liên kết ngoài bị sót từ transcript clone. Chỉ giữ lại CTA theo dõi kênh của chính mình.
- **Kèm 5 hashtag** ở cuối mô tả.

### 3. Đúng 5 Hashtag (Hashtags)
- Bắt buộc hashtag đầu tiên là `#shorts` (hoặc `#short`).
- 4 hashtag tiếp theo bám sát chủ đề ngách và ngôn ngữ của video:
  * *Tây Ban Nha (Stoic):* `#shorts #estoicismo #filosofia #disciplina #motivacion`
  * *Việt Nam (Kỹ năng/Triết lý):* `#shorts #baihoccuocsong #phattrienbanthan #tuduy #triethoc`

### 4. Thẻ Tag (Tags)
- Chọn lọc 8 – 15 thẻ tag bám sát thực thể chính, nhân vật, và từ khóa tìm kiếm cốt lõi.
- Tránh lặp từ vô nghĩa, tổng độ dài tags dưới **350 ký tự**.
- Đúng ngôn ngữ kịch bản.

### 5. Gói Thumbnail 9:16 (Google Flow Tự Vẽ Chữ 3D Vàng Kim Bắt Mắt + Khử Watermark)
- **Tỷ lệ:** **9:16 Dọc (1080 x 1920)**.
- **Câu chữ Hook trên ảnh:** Đúng **2 đến 3 từ** ngắn gọn, punchy, in hoa (ví dụ: `DOMINA TU MENTE`, `IM LẶNG LÀ VŨ KHÍ`).
- **Quy tắc đưa chữ vào Prompt gửi Google Flow:**
  * Google Flow (Imagen 3 / Nano Banana) tự dựng chữ 3D trực tiếp vào ảnh, hòa nhập hoàn hảo với ánh sáng và nếp áo nhân vật, không dùng font PIL 2D chèn đè.
  * **Màu sắc bắt mắt, tương phản cao (High-CTR):** Tuyệt đối không dùng chữ 1 màu bạc hoặc đá cẩm thạch trắng mờ nhạt (trùng màu tượng đá làm chìm chữ). Dùng chữ **Vàng kim hoàng gia 3D rực rỡ (Radiant 3D Imperial Gold)** và **Cam hổ phách rực lửa (Blazing Amber Gold)** kèm ánh viền warm rim lighting và bóng đổ khối chiaroscuro tương phản cực mạnh với nền tối. Cỡ chữ giữ nguyên chuẩn khổng lồ uy nghi.
  * Cú pháp prompt (2 dòng): `...featuring giant monumental 3D extruded typography stamped boldly across the chest and draped toga in the lower half reading "{LINE_1}" in radiant 3D burnished imperial gold with razor-sharp specular highlights and "{LINE_2}" in blazing molten amber-gold with intense electric warm rim lighting, heavy contact shadows, dramatic 3D block extrusion, tight heroic portrait, never a severed bust on a pedestal, photorealistic 8k, no watermark.`
  * Cú pháp prompt (1 dòng): `...featuring giant monumental 3D extruded typography stamped boldly across the chest and draped toga in the lower half reading "{HOOK}" in radiant 3D burnished imperial gold with glowing molten amber rim lighting, razor-sharp specular highlights, dramatic 3D block extrusion, and deep heavy contact shadows, tight heroic portrait, photorealistic 8k, no watermark.`
  * Né vùng an toàn UI Shorts: Chữ nằm ở nửa dưới phần thân (vùng y: 1100 – 1500), cách mép đáy >220px và mép phải >120px.
- **Khử Watermark:** Sau khi Flow tạo xong ảnh, hệ thống tự động chạy `clean_watermark.py` dùng thuật toán Navier-Stokes xoá sạch logo ngôi sao ở góc dưới phải.

### 6. Cấu hình YouTube Studio khi xuất bản
- **Ngôn ngữ video & phụ đề (Video Language):** Khớp 100% ngôn ngữ tập phim (Tây Ban Nha: `Tiếng Tây Ban Nha (es)`, Việt Nam: `Tiếng Việt (vi)`, Anh: `Tiếng Anh (en-US)`).
- **Ngôn ngữ âm thanh (Audio Voice Language):** Khớp 100% ngôn ngữ giọng đọc.
- **Chứng nhận phụ đề (Caption Certification):** "Nội dung này chưa từng phát sóng trên truyền hình tại Hoa Kỳ (Không áp dụng quy định phụ đề của FCC) — KHUYÊN CHỌN TRÊN YOUTUBE STUDIO".

### 7. Bình luận ghim (Pinned Comment)
- Một câu hỏi ngắn kích thích tranh luận hoặc suy ngẫm nhanh, thúc đẩy người xem bình luận ngay sau khi xem hết 30s.
- Đúng 100% ngôn ngữ của video.
  * *Tây Ban Nha:* `¿Eres capaz de mantener la calma en los momentos más difíciles? Déjame tu opinión en los comentarios.`
  * *Việt Nam:* `Bạn có giữ được bình tĩnh khi người khác cố tình khiêu khích mình không? Chia sẻ góc nhìn của bạn nhé.`

---

## 2. QUY TRÌNH THỰC THI KHÉP KÍN TRONG STORYBOARD AI

```
[Kịch bản / Video Shorts 9:16]
          │
          ▼
[Skill: publish-youtube-shorts]
   ├── Xác định Ngôn ngữ & Thể loại (Genre)
   ├── Trích xuất thông điệp cốt lõi & Entity
   ├── Sinh Tiêu đề (<50 char + #Shorts), Mô tả (lọc link đối thủ), 5 Hashtag, Tags, Pinned Comment
   ├── Cấu hình YouTube Studio: Ngôn ngữ chuẩn BCP-47 & Chứng nhận phụ đề FCC
   └── Xây dựng Prompt Thumbnail 9:16 chứa sẵn Hook chữ 3D Vàng kim / Hổ phách rực rỡ
          │
          ▼
[Google Flow MCP (Imagen 3 / Nano Banana)]
   ├── Nhận prompt chứa chữ 3D & render trực tiếp vào hình
   └── Tạo ảnh 9:16 hoàn chỉnh với chữ 3D vàng kim đổ bóng khối tự nhiên trong không gian
          │
          ▼
[Khử Logo Watermark (clean_watermark.py)]
   └── Tự động xoá sạch logo ngôi sao Google Flow bằng thuật toán Navier-Stokes
          │
          ▼
[Kiểm định kỹ thuật thực tế (Truthful Technical Checklist)]
   ├── Khớp ngôn ngữ 100% (Spanish / Vietnamese...)
   ├── Tiêu đề < 60 ký tự, có #Shorts
   ├── Đủ 5 hashtag, tags < 500 ký tự
   ├── Không có link đối thủ
   └── Vùng an toàn UI Shorts hợp lệ
          │
          ▼
[Lưu trực tiếp vào thumbnail_shorts.jpg & thư mục xuất bản 00_DANG_BAI_YOUTUBE]
```

---

## 3. CHECKLIST KIỂM ĐỊNH KỸ THUẬT THỰC TẾ (REAL TECHNICAL AUDIT)

> [!CAUTION]
> **KHÔNG SỬ DỤNG ĐIỂM SỐ ẢO (ZERO FAKE VIDIQ)**
> Kiểm tra các tiêu chí kỹ thuật cụ thể:

1. **Khớp ngôn ngữ 100%:** Tiêu đề, Mô tả, Hashtag, Tag, Chữ Thumbnail, Bình luận ghim, Cấu hình YouTube Studio cùng ngôn ngữ kịch bản.
2. **Độ dài tiêu đề thực tế:** Dưới 50 ký tự (chuẩn hiển thị di động).
3. **Số lượng Hashtag:** Đúng 5 hashtag liên quan trực tiếp.
4. **Tổng dung lượng thẻ Tag:** 250 – 350 / 500 ký tự tối đa của YouTube Studio.
5. **Kiểm tra mô tả:** Ngắn gọn, súc tích, 0 link đối thủ.
6. **Kiểm tra Thumbnail:**
   - Tỷ lệ đúng 9:16 (1080x1920).
   - Chữ 3D vàng kim / hổ phách rực rỡ, tương phản cao, dễ đọc từ khoảng cách xa.
   - Vùng an toàn UI Shorts hợp lệ (chừa đáy 220px, phải 120px).
