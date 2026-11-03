---
name: write-video-scene-prompts
description: Viết kịch bản phim và prompt text-to-video theo 9 trường cố định, nhân vật diễn xuất tự nhiên như phim thật, không đứng đơ; hỗ trợ tự chọn thể loại, phim ngắn/dài, tiếp tục từng nhóm cảnh, lời thoại, 9:16/16:9 và QC.
---

# write-video-scene-prompts — REAL ACTING upgrade v1.1

## Mục tiêu
Viết **kịch bản có logic**, sau đó chia cảnh thành prompt **tạo video có diễn xuất tự nhiên**. Phim phải có con người sống động, chủ động, phản ứng đúng tình huống; cấm biến prompt thành chuỗi ảnh tĩnh biết nói. Không tạo cảm giác giả bằng cách chèn thật nhiều cử động không mục đích.

## Tương thích ngược — BẮT BUỘC
1. **Không đổi tên, thứ tự hoặc số lượng của 9 mục**; không đánh số `1.` trước trường. Xem `references/FORMAT_CONTRACT.md`.
2. Trong tệp TXT dùng để nhập tool, **chỉ có các block SCENE**; không thêm lời dẫn, bảng, hướng dẫn, ghi chú QA, mã Markdown hoặc kịch bản tổng trước/sau block.
3. Giữ đúng định dạng header SCENE đã được người dùng chấp nhận; dùng UTF-8 và dấu `–` (en dash) trong timecode.
4. Giữ text-to-video độc lập từng cảnh. **Không đòi ảnh tham chiếu**; mỗi prompt tự khai báo các đặc điểm cần giữ giống nhau. Không tự bổ sung subtitle, overlay, logo, watermark.
5. Giữ chế độ sao chép toàn bộ prompt; với phim dài cho phép tạo từng nhóm rồi nối vào kết quả hiện có, **không tái đánh số**.
6. Tôn trọng giọng nói/giọng clone đang chọn; không đổi người lồng tiếng nếu không được yêu cầu.

## Quy trình bắt buộc

### BƯỚC 0: KHƠI NGUỒN & SÁNG TẠO Ý TƯỞNG (CONCEPT IDEATION ENGINE)
Khi người dùng **chưa có kịch bản sẵn** hoặc chỉ đưa ra chủ đề sơ khai (ví dụ: *"nghĩ cho tôi ý tưởng về triết lý khắc kỷ/drama khu phố", "hãy sáng tạo tập tiếp theo"*):
1. **Tuyệt đối KHÔNG nhảy vào viết 9 trường ngay lập tức.** Bắt buộc phải khơi nguồn và chốt ý tưởng cốt truyện trước.
2. **Đề xuất 3 Góc nhìn Ý tưởng Đột phá (3-Angle Ideation Matrix)** (Xem chi tiết `references/CONCEPT_IDEATION_PLAYBOOK.md`):
   - **Concept 1 (High Conflict / Xung đột đỉnh điểm):** Đẩy nhân vật vào tình huống ngặt nghèo ngay giây đầu tiên, nhịp độ dồn dập, đối kháng trực diện.
   - **Concept 2 (Deep Emotion & Moral Dilemma / Chiều sâu tâm lý & Triết lý nhân sinh):** Khai thác bi kịch gia đình, sự tha thứ, phẩm giá con người hoặc bài học khắc kỷ sâu sắc.
   - **Concept 3 (Plot Twist / Cú lật mặt bất ngờ):** Dẫn dắt người xem theo hướng quen thuộc rồi bẻ lái 180 độ ở hồi 3 khiến người xem ngỡ ngàng.
3. **Mỗi ý tưởng đề xuất phải có đủ 3 yếu tố:**
   - **Tên tập phim lôi cuốn (Catchy Episode Title)**
   - **Logline 1 câu chuẩn Hollywood:** `[Nhân vật chính độc đáo] + [Biến cố bất ngờ / Inciting Incident] + [Mục tiêu sống còn] + [Đối thủ / Trở ngại khổng lồ] + [Cái giá phải trả nếu thất bại / Stakes]`.
   - **Hook 3 giây đầu (In Medias Res):** Mở màn trực tiếp giữa đỉnh điểm hành động để giữ chân người xem.
4. **Chốt ý tưởng & Xây dựng Dàn ý 3 Hồi (Beat Sheet):** Sau khi người dùng chọn hoặc phối hợp ý tưởng, phác thảo dàn khung 3 Hồi (Hồi 1: Biến cố khởi nguồn $\rightarrow$ Hồi 2: Leo thang & Đáy vực $\rightarrow$ Hồi 3: Cao trào & Khúc quanh) trước khi chuyển thể sang kịch bản phân cảnh 9 trường.

### BƯỚC 1: PHÂN LOẠI & THIẾT LẬP THỂ LOẠI
Phân loại thể loại: `stoic`, `HOA_drama`, `family_drama`, `horror`, `western`, `action`, `animation`, `comedy`, `clone` hoặc `generic`. Áp dụng đúng phong cách mỹ thuật và diễn xuất của thể loại theo `references/GENRES.md`.
3. Thiết lập **BỘ TÀI SẢN SẢN XUẤT ĐỒNG BỘ CHO MỖI TẬP (MASTER PRODUCTION ASSET PACK: NHÂN VẬT - BỐI CẢNH - ĐẠO CỤ)** (Xem chi tiết `references/ASSET_TURNAROUND_SHEET.md`):
   - **Bảng Xoay Nhân Vật 4 Góc Quay (4-Angle Character Turnaround Sheet):** Với mọi nhân vật chính và phụ, chuẩn bị cấu trúc prompt render ảnh Character Model Sheet gồm 4 góc chụp toàn thân (*Front View, 3/4 View, Side Profile, Back View / Close-up*) trên nền trung tính xám để cố định tỷ lệ cơ thể, góc nghiêng khuôn mặt và kiểu tóc 360 độ.
   - **Khóa DNA Vật Lý Siêu Chi Tiết (Hyper-Specific Facial Landmarks):** Tuổi chính xác, sắc tộc, undertone màu da (VD: warm dark-cocoa with golden undertones), cấu trúc xương gò má, dáng mắt, lông mi, dáng môi; **BẮT BUỘC có ít nhất 1 điểm neo nhận diện cố định** (nốt ruồi ở vị trí milimet cụ thể như "beauty mark mole 3mm above right upper lip", vết sẹo nhỏ, lúm đồng tiền) để ngăn AI Text-to-Video tự ý đổi mặt giữa các cảnh.
   - **Kiến trúc kiểu tóc cố định (Hair Architecture):** Chiều dài chính xác, vị trí rẽ ngôi, kiểu tết/búi, lọn tóc con buông rủ cụ thể.
   - **Khóa trang phục cố định theo từng Hồi (Strict Wardrobe per Act):** **TUYỆT ĐỐI CẤM** dùng các từ ngữ tiến trình mơ hồ như *"transitioning from vintage to silk"*, *"wears street clothes initially then gowns"*. Mỗi Hồi (Act) hoặc chuỗi cảnh Sequence Block BẮT BUỘC chỉ định một set trang phục cố định, chi tiết đến từng phụ kiện/chất liệu/màu sắc (áo, quần/váy, giày, thắt lưng, trang sức); toàn bộ các cảnh trong Hồi đó phải mang đồng nhất set này.
   - **Bảng Bối Cảnh Bất Biến (Master Location Sheet):** Định nghĩa trước danh sách 2–5 địa điểm chính của tập với kiến trúc, bảng màu và hướng ánh sáng cố định; trong `SETTING & START STATE:` chỉ mô tả không gian và vị trí đứng, **cấm tả lại trang phục** gây xung đột.
   - **Bảng Đạo Cụ Then Chốt (Key Story Props Sheet):** Định danh trước kích thước, chất liệu, màu sắc và đặc điểm nhận dạng của các đồ vật cốt lõi (gương nứt, bản di chúc, bật lửa bạc, khay dao mổ, v.v.) để hành động trong `TIMED ACTION:` luôn gọi đúng đạo cụ.
   - **Tuyệt đối không để sót nhân vật (Zero Bare Names):** Toàn bộ nhân vật xuất hiện trong cảnh (kể cả nhân vật phụ, bác sĩ, tài xế, sát thủ) đều phải có đầy đủ mô tả DNA nhận diện trong `CHARACTERS:`. Cấm để tên trần trụi dạng `Doctor.` hay `Eva.`.
4. Chọn shot length theo yêu cầu/provider (ví dụ 8s), tính tổng thời lượng trước khi viết. Với thời lượng không chia hết: xử lý cảnh cuối/trim hậu kỳ một cách minh bạch; không giả định engine hỗ trợ clip lẻ.
5. Phân bổ hook, điểm đảo chiều, mức căng thẳng, giải quyết. **Mỗi shot có 1 hành động chính + tối đa 1–2 phản ứng phụ liên quan đến mục tiêu**; tránh ép 5 hành động vào 8s.
6. Với mỗi cảnh, viết đủ 9 mục, theo `references/REALISTIC_ACTING.md`. Thời gian trong `TIMED ACTION` không chồng nhau; `AUDIO` phải khớp người nói và cửa sổ thời gian.
7. Trước khi xuất, kiểm tra `references/QC.md`; chạy `scripts/validate_prompts.py` cho TXT (nếu có terminal). Phân biệt **preflight bằng văn bản** với **QC video render thực tế**. Không gọi preflight là "phim đã đạt".
8. Phim dài: lưu danh sách cảnh đã hoàn thành, hồ sơ nhân vật, cốt truyện chưa giải quyết, timeline, thoại đã phát; khi "tiếp tục", chỉ viết tiếp, bảo toàn trạng thái nhân vật và thời lượng.

## Đạo diễn diễn xuất — 7 điều không thể bỏ qua
- **Có mục đích:** Nhân vật đang làm gì và *tại sao*? Cử động để đạt mục đích hoặc phản ứng, không vẫy tay/đi vòng vì sợ cảnh tĩnh.
- **Chuyển động vật lý:** Mắt chuyển tiêu điểm → đầu xoay → vai/thân điều chỉnh trọng tâm → hành động của tay/chân; đúng trọng lực, điểm tiếp xúc, quán tính, tầm với.
- **Biểu cảm tinh tế:** Thay đổi nhỏ ở mắt, hàm, nhịp thở, tư thế, khoảng ngừng trước thoại; cấm biểu cảm đóng băng hoặc cười vô cớ.
- **Nghe và phản ứng:** Người không nói vẫn nghe, quan sát, thay đổi nét mặt; chỉ nhân vật có lời thoại mới mấp máy môi cho câu đó.
- **Camera có động cơ:** Giữ máy cố định khi phù hợp, handheld nhẹ khi căng thẳng, tracking khi theo nhân vật. Không mặc định zoom liên tục; không ép one-take không cần thiết nếu workflow cho phép dựng giữa clip.
- **Liền mạch & Sequence Block:** Cố định một bối cảnh (Setting) trong suốt cả trường đoạn kịch tính (6–15 cảnh liên tiếp = 60–150 giây). Tuyệt đối không teleport đổi địa điểm sau mỗi 10 giây; chỉ thay đổi góc máy quay (toàn, trung, cận, qua vai, tracking). Tư thế/đạo cụ/điểm nhìn ở END STATE phải chuyển hợp lý sang START STATE cảnh kế tiếp; không teleport, pop-in, tay tự đổi, vật đi xuyên, mắt chết, face morph.
- **Đồng nhất nhân vật & DNA Lock:** Từng chi tiết vật lý (nốt ruồi ở tọa độ mm cụ thể, vết sẹo, undertone màu da, búi tóc bím tết) và trang phục cố định theo Hồi BẮT BUỘC phải được lặp lại chính xác trong mục CHARACTERS của mọi cảnh độc lập. Tuyệt đối cấm dùng từ chuyển dịch trang phục mơ hồ (như "transitioning", "initially wears...") để tránh AI tự vẽ lệch mặt và đổi quần áo giữa các cảnh.

## BỘ LỌC KIỂM DUYỆT AN TOÀN & CÂU LỆNH CẤM (SAFETY MODERATION & FORBIDDEN PROMPTS)
Mọi AI Video Engine (Muse, Google Flow, Kling, Runway, Sora) đều tích hợp bộ lọc kiểm duyệt an toàn cực kỳ khắt khe. Dù tài khoản có 1 tỷ token, việc xuất hiện từ khóa bạo lực/vũ khí sẽ khiến AI từ chối sinh video ngay lập tức (`provider_generation_error`). BẮT BUỘC tuân thủ:

### 1. CẤM TUYỆT ĐỐI HÀNH VI BẠO LỰC THỂ XÁC & TRẤN ÁP (Zero Physical Violence)
- **TỪ KHÓA CẤM:** `tackle`, `tackles to floor`, `pinned down`, `pinned on floor`, `kneels over him`, `shoved onto floor`, `punch`, `kick`, `choke`, `strangle`, `slap`, `beat`, `bloody`, `wound`, `stab`, `slash`, `kill`, `slay`, `corpse`, `flesh`, `mutilated`.
- **CHUYỂN HÓA DIỄN XUẤT ĐIỆN ẢNH HỢP LỆ:**
  - Thay vì xô ngã/quật xuống sàn $\rightarrow$ mô tả: *"firmly restrains by the arm"*, *"steps forward defensively"*, *"stands confronting firmly"*, *"firmly holds back in the room"*.
  - Thay vì đòn đánh bạo lực $\rightarrow$ nâng tầm kịch tính qua diễn xuất: *"intense verbal confrontation"*, *"sharp accusatory finger gesture"*, *"clenched jaw and cold defiant eyes"*, *"slams documents firmly onto desk"*.

### 2. CẤM TUYỆT ĐỐI VŨ KHÍ & SÚNG ỐNG (Zero Firearms & Lethal Weapons)
- **TỪ KHÓA CẤM:** `gun`, `pistol`, `rifle`, `sidearm`, `holster`, `sidearm holster`, `knife`, `blade`, `sword`, `dagger`, `spear`, `weapon`, `ammunition`.
- **CHUYỂN HÓA TRANG PHỤC HỢP LỆ:**
  - Nhân vật cảnh sát/bảo vệ: **CẤM** mô tả `sidearm holster`, `gun`. Thay bằng: *"formal municipal uniform with silver badge and badge holder, utility belt without weapons"*, *"tailored blazer with security crest"*.
  - Nhân vật cổ trang/hành động: Thay vũ khí sắc nhọn bằng *"ceremonial staff"*, *"scroll cylinder"*, *"leather ledger"*.

### 3. CẤM RÁC CONTAMINATION TỪ DỰ ÁN KHÁC (Zero Template Leakage)
- Tuyệt đối không copy-paste bừa bãi các đoạn mô tả mẫu có chứa tên nhân vật hoặc địa danh của phim khác (ví dụ: cấm để lọt *"Steadicam leading Lulu as she strides down VIP nightclub corridor"* vào phim của nhân vật khác).

### 4. BẮT BUỘC CÂU LỆNH BẢO VỆ AN TOÀN TRONG `CONSTRAINTS:` CỦA MỌI CẢNH
Mục `CONSTRAINTS:` trong mọi cảnh bắt buộc phải chứa câu lệnh an toàn:
`CONSTRAINTS: ... Use non-graphic depiction. No weapons, no firearms, no physical violence or bodily harm. Intense dramatic conflict portrayed strictly through credible verbal performance, sharp eye contact, tense body language and professional cinema staging.`

## Ngôn ngữ, âm thanh
- Prompt kỹ thuật có thể viết bằng tiếng Anh để video model hiểu; lời thoại là **ngôn ngữ của câu chuyện** (VD tiếng Việt/Tây Ban Nha). Không dịch câu thoại sai ngôn ngữ.
- `AUDIO` định danh duy nhất người nói, thời điểm bắt đầu/kết thúc, giọng/cảm xúc và tiếng động có nguồn. Giữ đúng tốc độ phát âm; không kéo dài âm tiết vô cớ để lấp thời gian.
- Nếu người dùng muốn giọng kể, nêu rõ narration là offscreen và tránh dựng nhân vật đang đọc thoại vào camera kiểu tượng nói.

## Bảo vệ chế độ clone
Chỉ tái tạo các yếu tố mà video nguồn đã phân tích/được người dùng cung cấp. **Không thêm nhân vật, sự kiện hoặc tình tiết suy diễn**. Nếu URL/trích xuất không có dữ liệu thì yêu cầu transcript/tệp gốc thay vì bịa.

## Đầu ra
- Nếu người dùng yêu cầu kịch bản hoàn chỉnh: trả logline/tóm tắt/hồi/thoại trước ở phần riêng.
- File nhập tool: **chỉ các block cảnh đúng hợp đồng 9 mục**, không nội dung bổ trợ.
- Báo cáo kiểm tra: scene count, thời lượng, đủ nhãn, continuity, audio và các cảnh cần review. Chỉ kết luận chất lượng video chuyển động sau khi xem clip render thực tế.

Xem: `references/FORMAT_CONTRACT.md`, `references/REALISTIC_ACTING.md`, `references/QC.md`, `references/GENRES.md`, `references/ASSET_TURNAROUND_SHEET.md`, `references/CINEMATIC_MASTER_SHOTS.md`.
