---
name: write-narrative-scene-prompts
description: Viết kịch bản kể chuyện/thuyết minh (1 giọng đọc) và prompt tạo ảnh (Image Prompt) ngắn gọn, súc tích, chuyên sâu cho nhánh Kể Chuyện. Tách biệt hoàn toàn lời thoại/phụ đề khỏi prompt tạo ảnh; prompt ảnh chỉ mô tả thị giác thuần túy (40-80 từ), chống nghẽn Google Flow / ImageFX / Cloud AI.
---

# write-narrative-scene-prompts — KỊCH BẢN KỂ CHUYỆN & TẠO ẢNH CHUẨN ĐƠN GIẢN

## 1. Nguyên Tắc Cốt Lõi: Tách Biệt Tuyệt Đối 2 Nhánh
- **Nhánh Kể Chuyện (Narrative Storytelling)** hoạt động hoàn toàn khác **Nhánh Phim Kịch Đa Vai (Cinematic Drama)**:
  * **Chỉ tạo ảnh tĩnh / hình ảnh minh họa** (Image Generation Prompt) cho từng cảnh.
  * **Lời thoại thuyết minh (Voiceover/Narration)** và **Phụ đề (Subtitles/SRT)** được xử lý và ghép vào video ở các bước RIÊNG BIỆT sau đó qua TTS và Audio Merger.
  * **TUYỆT ĐỐI CẤM** nhét lời thoại, audio cues, timed actions, phụ đề hay quy tắc nhân vật cồng kềnh vào trong prompt tạo ảnh.
  * **CẤM** đụng chạm hay can thiệp vào skill `write-video-scene-prompts` của nhánh Phim Kịch Đa Vai.

---

## 2. Tiêu Chuẩn Prompt Tạo Ảnh (Image Prompt)
Mỗi cảnh trong nhánh Kể Chuyện chỉ cần **1 prompt ảnh cực kỳ ngắn gọn, sắc nét**:
- **Độ dài**: Từ **40 đến tối đa 80 từ tiếng Anh** (khoảng 250 – 500 ký tự).
- **Cấu trúc 3 thành phần**:
  1. `[Chủ thể & Góc máy]`: Ví dụ: `Cinematic 16:9, medium close-up shot of a weathered marble Stoic philosopher statue...`
  2. `[Bối cảnh & Ánh sáng]`: Ví dụ: `against majestic ancient Roman colonnades at golden hour, volumetric warm sunlight, floating dust embers...`
  3. `[Chất lượng & Mỹ thuật]`: Ví dụ: `photorealistic, detailed stone fissures, chiaroscuro lighting, 8k.`
- **Điều cấm kỵ**:
  - KHÔNG đưa câu thoại, tên người nói, hoặc hướng dẫn diễn xuất vào prompt ảnh.
  - KHÔNG lặp lại các đoạn văn tiểu sử, quy tắc bất biến dài dòng.
  - KHÔNG dùng từ khóa nhạy cảm / bạo lực / khỏa thân khiến bộ lọc Google Flow / ImageFX báo lỗi.

---

## 3. Cấu Trúc Phân Cảnh Chuẩn (Scene Block Contract)

Khi xuất kịch bản phân cảnh cho nhánh Kể Chuyện, trình bày theo đúng định dạng độc lập:

```markdown
### SCENE {index} ({start_time} – {end_time})
- **IMAGE PROMPT** (Tiếng Anh, 40–80 từ cho AI tạo ảnh):
  Cinematic 16:9, low-angle chest-up shot of monumental weathered bronze philosopher emperor Marcus Aurelius with chiseled physique, royal crimson toga draped over one shoulder. Grand ancient Roman temple forum backdrop, soft golden dusk light, drifting golden embers, photorealistic 8k.

- **THUYẾT MINH / VOICEOVER** (Tiếng Việt hoặc ngôn ngữ kịch bản - Dành cho TTS & Phụ đề):
  Chúng ta thường tiêu tốn cả đời để cố nắm giữ những điều ngoài tầm kiểm soát, mà quên mất rằng sự bình yên thực sự chỉ đến khi ta học được cách buông bỏ.

- **CAMERA MOTION**: Ken Burns zoom in (hoặc Slow pan left / right)
- **DURATION**: 25s
```

---

## 4. Quy Trình Sản Xuất Nhánh Kể Chuyện
1. **Bước 1: Kịch bản Thuyết Minh**: Viết bài thuyết minh sâu sắc, truyền cảm hứng, tính toán thời lượng đọc khớp với từng phân cảnh (khoảng 2–2.5 từ/giây).
2. **Bước 2: Phân Cảnh Thị Giác**: Với mỗi phân đoạn thuyết minh, tạo 1 Image Prompt ngắn gọn (40–80 từ) mô tả hình ảnh minh họa tương ứng.
3. **Bước 3: Tạo Ảnh Tuần Tự**: Đẩy prompt ngắn gọn sang Google Flow (`mcp_v2`) hoặc Cloud AI (`v2_tuanstor`). Prompt ngắn giúp Flow sinh ảnh siêu tốc, không bị nghẽn quota hay lỗi timeout.
4. **Bước 4: Ghép Âm Thanh & Phụ Đề**: Engine lấy trường `THUYẾT MINH` chuyển thành giọng đọc TTS (`audio.wav`), căn chỉnh từ (Word Alignment) tạo phụ đề Karaoke, và áp hiệu ứng chuyển động máy quay (Ken Burns) lên ảnh để tạo video hoàn chỉnh.
