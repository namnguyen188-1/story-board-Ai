# QC 2 cấp: kịch bản và video đã render

## PRE-FLIGHT TXT — kiểm tra tự động hoặc thủ công
- Đúng nhãn/chính tả/thứ tự của chín mục, không thừa phần ngoài scene blocks.
- Scene IDs tuần tự, timecode liên tục, tổng duration đúng, ratio 9:16/16:9 nhất quán.
- Mỗi shot có hành động chính và phản ứng, mô tả hoạt ảnh cụ thể trong `TIMED ACTION`.
- Không giao hai nhân vật cùng đọc một câu; nhân vật không nói không mấp máy.
- Đạo cụ, ngoại hình, không gian, hướng nhìn nhất quán; không quá tải hành động/thoại.
- Nếu là clone, nguồn đã có, nội dung không đoán; nếu chưa phân tích nguồn → chặn clone.

## RENDER-QC — không thể giả lập bằng text
Chỉ áp dụng khi có clip xuất ra. Quan sát từng clip, nhất là keyframe/khung chuyển động:
1. **Freeze / mannequin**: đứng cứng vô cớ, mắt/môi vô hồn.
2. **Physical plausibility**: tay không xuyên đồ, chân không trượt sàn, trọng tâm hợp lý.
3. **Performance**: người nghe phản ứng; cảm xúc đi theo diễn biến, không nhún/giơ tay ngẫu nhiên.
4. **Lip sync & audio**: đúng speaker, ngôn ngữ, thời điểm; âm thanh môi trường có nguồn.
5. **Consistency**: khuôn mặt, quần áo, đồ vật, địa hình, ánh sáng không nhảy.
6. **Timing & transitions**: thời lượng render thực, chuỗi nhân quả và góc máy.

Đánh dấu mỗi clip `PASS`, `REVIEW`, `REGENERATE`. Nếu có lỗi nghiêm trọng ở các mục 1, 2, 4, 5 → `REGENERATE` cảnh đó và xác minh lại; không kết luận một bộ prompt văn bản là E2E pass. Không đảm bảo "giống người thật 100%" chỉ bằng prompt.

## Ghi nhận lỗi
`SCENE_ID | ERROR_CODE | OBSERVED | PROPOSED_FIX | RETRY_COUNT | VIDEO_QC`.
Lỗi ví dụ: `FROZEN_ACTOR`, `RUBBER_MOTION`, `LIPSYNC_DRIFT`, `CHARACTER_DRIFT`, `PROP_TELEPORT`, `DURATION_MISMATCH`.
