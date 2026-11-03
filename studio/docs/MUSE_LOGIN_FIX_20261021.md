# Sửa đăng nhập Muse trong Storyboard AI — 21/10/2026

Trang chủ https://muse.ai/ được kiểm tra bằng HTTP không mang cookie: tự chuyển qua auth.muse.ai/aymh/, www.facebook.com/aymh/redirect-cycle/, www.instagram.com/aymh/redirect-cycle/ rồi www.instagram.com/accounts/login/. Đây là chuỗi chuyển hướng của dịch vụ; tool không tự chọn nút Instagram.

Đổi điểm mở sang https://muse.ai/business. Đã xác minh trang chính thức này ở lại muse.ai và chứa form số điện thoại/email. Dùng đúng tài khoản Muse hiện có; không tự tạo hay liên kết tài khoản Instagram. Cửa sổ đăng nhập riêng cũ được giữ, mở thêm đúng một tab cho điểm vào mới và các lần bấm tiếp dùng lại cùng trình duyệt.

Thêm nút Đăng nhập Muse và Đã đăng nhập · Kết nối trong mục cài đặt Muse. Tool chỉ lưu phiên sau khi đọc cookie đúng miền Muse và xác minh gateway/VM. Khi chưa đăng nhập hoặc xác minh thất bại, phiên đang hoạt động được giữ nguyên. Không đổi tài khoản khi còn job chưa hoàn thành của VM khác. Cookie không đi qua giao diện hoặc phản hồi HTTP.

Sửa timeout kiểm tra đăng nhập thành MUSE_LOGIN_CHECK_TIMEOUT, dọn đúng cây tiến trình worker và cho phép giao diện thử lại. Không báo nhầm đang render video. Giới hạn kiểm tra 120 giây; chỉ theo dõi đăng nhập trong 20 phút.

Kiểm thử: 25 unit đạt (11 đăng nhập + 14 hồi quy Muse), 6 tình huống logic giao diện đạt, JavaScript đúng cú pháp. Năm kiểm tra HTTP thực tế đạt: phiên cũ hợp lệ; mở cửa sổ; dùng lại khi bấm hai lần; chưa đăng nhập không ghi đè cookie/cấu hình; phiên cũ vẫn dùng được sau đó. Không tạo thêm ảnh/video trong lượt sửa đăng nhập. Chưa kiểm tra hoàn tất đăng nhập mới bằng tài khoản thật vì cần người dùng tự nhập thông tin.

Đã triển khai và đối chiếu 7 tệp với staging. Checkpoint trước thay đổi: D:\STORYBOARD_AI\backups\muse_login_before_20261021. Mã chính tại D:\STORYBOARD_AI\studio. Bản đang chạy chưa nạp backend mới vì v-tranh đang dựng cảnh 60/72 ở lần kiểm tra cuối. Cần thoát/mở lại Storyboard sau khi sản xuất xong để kích hoạt toàn bộ nút và API. Không dừng tiến trình sản xuất.

Bằng chứng và staging: D:\STORYBOARD_AI\feature_staging\muse_login_20261021. Khôi phục năm tệp cũ trong checkpoint; muse_login.py và tests/test_muse_login.py là tệp mới của thay đổi này. Không khôi phục hoặc xóa các tệp phiên Muse khi rollback mã.


## Đã kích hoạt và kiểm thử trên ứng dụng chính

Sau khi v-tranh hoàn tất 100% (exit code 0), đã khởi động lại backend chính và làm mới cửa sổ Storyboard. Cổng 8765 có API đăng nhập mới; HTML chứa cả hai nút đăng nhập/kết nối. Cửa sổ ứng dụng được đóng/mở lại, có handle mới và vẫn chỉ một cửa sổ chính. Phiên Muse đã lưu xác minh READY.

Năm kiểm tra HTTP đăng nhập/kết nối trên ứng dụng chính đều PASS: phiên cũ hợp lệ, mở cửa sổ đăng nhập, bấm lại dùng cùng trình duyệt, đăng nhập chưa hoàn tất giữ nguyên cookie/cấu hình, phiên cũ vẫn hoạt động sau đó. Người dùng chưa hoàn tất đăng nhập tài khoản mới trong lượt kiểm thử; hai phim dưới đây sử dụng phiên Muse đã lưu.

Hai E2E mới qua HTTP Storyboard chính → Muse tạo ảnh → tạo video → ghép MP4 đều PASS:

| Mẫu | MP4 cuối | Thời gian E2E | Kết quả |
|---|---|---:|---|
| Muse Main Login Canary 16x9 20261021 | 1280×720, 8,043 giây | 155,093 giây | PASS |
| Muse Main Login Canary 9x16 20261021 | 720×1280, 8,043 giây | 134,344 giây | PASS |

Đã kiểm tra đầy đủ khung hình/âm thanh nguồn, manifest PASS, giải mã toàn bộ MP4 cuối bằng FFmpeg và phát HTTP Range 206. Đây là mẫu im lặng với tiếng nước, chưa đánh giá thoại, lip-sync hay độ nhất quán nhân vật qua phim dài. Tệp nguồn Muse vẫn là 10 giây, 24 fps; kích thước MP4 cuối là kích thước dựng của Storyboard. Phim v-tranh trước đó vẫn tồn tại với dung lượng 183.435.350 byte. Không cần khởi động lại ứng dụng thêm để dùng bản sửa này.

Bằng chứng mới: main_actual_login_results.json, main_e2e_results.json, main_activation_result.json trong thư mục staging của bản sửa. Hai phim mẫu nằm trong productions/Muse-Main-Login-Canary-16x9-20261021 và productions/Muse-Main-Login-Canary-9x16-20261021 (episode_001).
