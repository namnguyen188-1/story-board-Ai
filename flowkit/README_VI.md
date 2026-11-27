# Bộ điều phối Flow + Muse độc lập

Bản này được sao chép vào FlowKit, có runtime riêng. Không cần mở hay sửa
Storyboard AI để chạy. Storyboard gốc không phải thư mục làm việc của bộ này.

1. Chạy `START.cmd`, hoặc `Start_API.vbs` để khởi động ẩn.
2. Mở `http://127.0.0.1:18110/docs` trên máy đang chạy. Nếu là bản sao mới,
   xem cổng trong `settings.json`.
3. Bấm **Authorize**, nhập khóa từ `state/api.key`.
4. Tool khác gửi yêu cầu đến `/v1/jobs`; lấy kết quả bằng mã job.

| Nhà cung cấp | Loại yêu cầu | Kết quả |
|---|---|---|
| Flow | `image` | 1 ảnh |
| Flow | `video` | 1 video Omni Flash, 8 giây |
| Flow | `scene` | 1 ảnh rồi 1 video Veo từ ảnh |
| Muse | `scene` | 1 ảnh và 1 video, 8 giây |

Thông số khác, danh sách API, phục hồi tác vụ và ví dụ JSON: `docs/API.md`.
Dùng `Idempotency-Key` ổn định để gửi lại cùng yêu cầu mà không tạo thêm job.
Hai nhà cung cấp có hàng đợi riêng. Tạo media vẫn dùng credit của tài khoản.

## Tạo bộ mới cho dự án khác

Chạy `NEW_PROJECT.cmd`, nhập đường dẫn một thư mục mới nằm ngoài bộ hiện tại.
Bản sao có runtime và tài khoản Muse được sao chép, khóa API mới, cổng API mới,
hàng đợi và đầu ra rỗng. Chạy `START.cmd` trong thư mục mới để dùng.

Đổi `flow_project_id` trong `settings.json`, hoặc truyền `project_id` trong yêu
cầu, để dùng một dự án Flow khác. Thao tác copy không tự tạo dự án trên Google.
Các bộ trên cùng máy có thể dùng chung cầu nối Flow và Chrome đã đăng nhập.
Không chạy đồng thời cùng tài khoản Muse từ nhiều bộ.

Nếu copy nguyên thư mục bằng Explorer thì cả lịch sử job và kết quả cũng được
copy; dùng `NEW_PROJECT.cmd` khi cần một dự án sạch.

## Đăng nhập khi cần

- `START.cmd` tự nhận extension Flow Kit đã có hoặc tự nạp bản trong
  `extensions/flow` vào profile Chrome chuyên dụng nếu còn thiếu. Không cần
  mở trang Extensions hay chọn Load unpacked.
- `SETUP_FLOW.cmd`: hiện đúng Chrome chuyên dụng và tự chuẩn bị extension.
  Bạn chỉ cần đăng nhập Google Flow và mở dự án khi phiên đã hết hạn.
- `LOCK_FLOW.cmd`: ẩn và khóa cửa sổ đó lại; Chrome tiếp tục chạy nền.
- `SETUP_MUSE.cmd`: đăng nhập Muse bằng bản sao riêng, không qua Storyboard.

Máy Windows khác cần Chrome hỗ trợ Extensions CDP API; đã kiểm thử Chrome 156.
Extension được nạp tự động; tài khoản Google vẫn có thể cần đăng nhập lại.
Phiên Google được bảo vệ theo tài khoản Windows, không bảo đảm copy sang máy
khác là còn đăng nhập. Không cần cài Python riêng.

Bộ đang chứa phiên tài khoản riêng của bạn; không phát hành nguyên thư mục cho
người khác. Công cụ kết nối chỉ cần URL API và `X-API-Key`, không cần cookie.

`VERIFY.cmd` kiểm tra runtime, file kết quả và tính toàn vẹn nguồn đã ghi nhận;
không tạo media và không tiêu credit. Kết quả lưu trong `state/verification.json`.

Kiểm tra tự nạp extension: `state/extension_install_test.json`; trạng thái đang
dùng: `state/flow_extension.json`. Kiểm thử dùng profile trống, kiểm tra không cài
trùng và tự chuẩn bị lại extension sau khi khởi động lại Chrome, không tạo media. Nếu Chrome
chặn API nạp extension, chương trình báo lỗi; không tự đổi chính sách Chrome.
