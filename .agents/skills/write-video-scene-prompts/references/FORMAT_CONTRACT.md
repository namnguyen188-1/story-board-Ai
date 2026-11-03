# Hợp đồng 9 mục — KHÔNG ĐỔI

## Header mỗi cảnh — literal (với timecode tương ứng)

`========== SCENE_001 | TIMELINE 00:00–00:08 | GENERATE 8 SECONDS ==========`

Theo ngay sau header là **chính xác 9 nhãn**, mỗi nhãn xuất hiện **một lần**, theo thứ tự:

```text
FORMAT & STYLE:
CHARACTERS:
SETTING & START STATE:
LIGHTING & COLOR:
CAMERA:
TIMED ACTION:
END STATE:
AUDIO:
CONSTRAINTS:
```

Nội dung sau dấu `:` có thể đặt cùng dòng hoặc xuống dòng; mỗi mục bắt buộc có nội dung, không chèn mục thứ 10, không `1. FORMAT & STYLE`. Khi xuất TXT, các cảnh cách nhau một dòng trống. Mọi phần tổng hợp được đặt ở tài liệu khác.

## Quy tắc thời gian
Tự lấy thời lượng từ header thay vì cố định 8s nếu yêu cầu khác. `TIMED ACTION` chia các khoảng con thành dải 0.0–... đến n giây không chồng lấn; `AUDIO` định thời lời nói trong khoảng tồn tại. Đảm bảo cảnh bắt đầu đúng tại thời điểm kết thúc cảnh trước. Nếu render nhà cung cấp chỉ hỗ trợ 8s, dùng 8s và hậu kỳ trim trong trường hợp cần thiết, ghi rõ trong ghi chú riêng ngoài file nhập.

## Quy tắc giữ hợp đồng
Không dùng JSON để thay file TXT tool đang nhận. JSON nội bộ có thể dùng làm metadata riêng. Không thêm Markdown code fence trong file máy đọc. Không sửa header đang dùng chỉ vì muốn đẹp hơn.
