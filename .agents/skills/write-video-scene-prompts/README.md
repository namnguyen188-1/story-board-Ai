# Bản cập nhật cho write-video-scene-prompts — natural acting

Đây là **bộ SKILL.md và tài liệu bổ sung để nhập/thay thế sau khi đối chiếu skill gốc**, không phải thao tác cập nhật từ xa đã được thực hiện.

Giữ nguyên tên gọi: `write-video-scene-prompts`.

## Cách sử dụng
- Nếu hệ thống hỗ trợ nhập custom skill từ ZIP, chỉ nhập gói sau khi đã sao lưu skill hiện hành và so sánh lệnh/định dạng gốc.
- Nếu hệ thống không hỗ trợ ghi đè: đưa các file trong `references` vào thư mục skill và ghép những quy tắc bổ sung từ `SKILL.md` vào skill cũ, không xóa các quy tắc genre đặc thù đang dùng.
- File `scripts/validate_prompts.py` chạy bằng `python scripts/validate_prompts.py tests/fixtures/camera_tang_13_64s.txt --seconds 64 --aspect 9:16`.
- Kết quả kiểm tra TXT chỉ là hợp đồng prompt, không chứng minh độ chân thật của render.

## Tính tương thích
- 9 trường cố định: FORMAT & STYLE; CHARACTERS; SETTING & START STATE; LIGHTING & COLOR; CAMERA; TIMED ACTION; END STATE; AUDIO; CONSTRAINTS.
- 1 cảnh độc lập, không tham chiếu ảnh.
- Hỗ trợ lựa chọn thể loại tự động, hook, lời thoại, nội dung dài có nút tiếp tục ở tầng giao diện.
- Không sửa trực tiếp Storyboard AI / YouTube SEO Pro V2 hoặc engine trên máy người dùng.
