# Storyboard AI — tích hợp lựa chọn Muse
Ngày: 21/10/2026, giờ Việt Nam.

## Trạng thái bàn giao

Đã cập nhật mã nguồn Storyboard AI trên máy DESKTOP-EE8BGVF, thư mục D:\\STORYBOARD_AI\\studio. Lựa chọn Muse có sẵn đã được nối sang gateway muse-cli đã xác minh, thay cho đường API Key/endpoint cũ chưa được kiểm chứng trong đợt này.

Cửa sổ Storyboard đang mở vẫn chạy backend đã nạp trước khi cập nhật. Tại lần kiểm tra cuối, dự án “v-tranh” đang ở GENERATING_IMAGES, 28%. Không khởi động lại hoặc dừng lượt sản xuất đó. **Sau khi lượt hiện tại kết thúc, thoát hẳn Storyboard rồi mở lại để nạp giao diện và backend mới.** Launcher EXE hiện tại đã được xác minh khởi chạy desktop_app.py từ chính thư mục mã nguồn này.

Không sửa YouTube SEO Pro V2. Không đẩy bản phát hành lên GitHub và không cập nhật máy thứ hai trong tác vụ này.

## Cách sử dụng

1. Sau khi mở lại Storyboard, vào **Cài đặt → Muse**, bấm **Kiểm tra kết nối**.
2. Tại **Nguồn ảnh / video**, chọn **Muse · Tự tạo ảnh → Video**.
3. Chọn tỷ lệ/kích thước đầu ra, nhập ý tưởng hoặc kịch bản có sẵn rồi sản xuất.
4. Với prompt từ skill, chọn chế độ kịch bản có sẵn và dán các cảnh đủ 9 mục, gồm cả dòng SCENE_001 — timeline. Không cần cung cấp ảnh tham chiếu.
5. Nếu gián đoạn, dùng chức năng chạy tiếp của tập hiện có. Bộ kết nối theo dõi mã job đã lưu thay vì tự gửi lại yêu cầu tạo media.

Muse tự tạo ảnh từ chữ rồi dùng ảnh đó làm nguồn cho video. Storyboard tiếp tục xử lý giọng kể và dựng phim theo cơ chế hiện có. **Bản tích hợp này chưa sử dụng lời thoại native của Muse để thay thế hệ thống giọng kể.**

## Kiểm chứng thực tế

| Phép thử | Kết quả |
|---|---|
| Unit: cấu hình và giữ prompt/nhân vật | 3/3 đạt |
| Unit: gateway, tải tiếp, job pending/failed, cache và khóa hàng đợi | 8/8 đạt |
| Unit: đầu vào SCENE_001, SHOT 1 cũ, thứ tự cảnh | 3/3 đạt |
| Logic trạng thái và lưu cấu hình giao diện bằng Node VM | 4/4 đạt |
| HTTP: trạng thái chưa xác minh, runtime sai, tắt Muse chặn sản xuất, khôi phục kết nối | 4/4 đạt |
| Hồi quy dựng cảnh dùng ảnh/audio lưu sẵn | 4/4 đạt: cinematic, whiteboard, hand_color, colored_marker |
| E2E thật qua HTTP Storyboard → Muse → MP4 → phát Range 206 | 2/2 đạt: ngang và dọc |
| Dùng lại job thật đã hoàn thành | Đạt: cùng session, cùng SHA-256 video, không gửi render mới |
| Toàn vẹn ảnh preview sau bước dựng cảnh | Đạt sau khi loại bước xử lý ảnh chung khỏi nguồn Muse |
| Mã chính và mã staging | 7/7 tệp có nội dung nguồn khớp; một số khác kiểu xuống dòng Windows |

Bộ unit được chạy lại trên mã chính sau khi áp dụng. JavaScript kiểm tra cú pháp đạt. Kiểm tra kết nối Muse từ mã chính trong tiến trình mới trả READY.

### Hai E2E thật

Cả hai dùng kịch bản im lặng 9 mục, không ảnh tham chiếu từ người dùng. Mỗi mẫu một cảnh để kiểm tra tích hợp và tỷ lệ, chưa phải phim dài.

| Đầu ra | Thời lượng phim | Thời gian E2E | Kết quả |
|---|---:|---:|---|
| 1280x720 (16:9) | 8.043 giây | 154.703 giây | PASS |
| 720x1280 (9:16) | 8.043 giây | 155.25 giây | PASS |

Tệp gốc Muse là clip 10 giây, 24 fps/240 khung hình; độ phân giải nguồn ngang 1248×704 và dọc 704×1248. Storyboard căn lại thành phim khoảng 8 giây theo kịch bản ở 1280×720 hoặc 720×1280. Việc chọn kích thước dựng không xác nhận độ phân giải native 1080p của Muse.

Đã tải đủ tệp ảnh/video, tính SHA-256, kiểm tra ảnh bằng Pillow và giải mã toàn bộ video/âm thanh bằng PyAV. MP4 dựng cuối được FFmpeg giải mã toàn bộ với chế độ lỗi nghiêm ngặt và kiểm tra khả năng phát HTTP Range 206.

Mẫu E2E có audio stream nhưng không có lời thoại. Chưa đánh giá giọng nói, lip-sync, chất lượng hình bằng mắt/tai hay độ nhất quán khuôn mặt qua phim dài.

## Thay đổi chính

- muse_video_provider.py: giao diện kết nối của Storyboard gọi worker bằng Python môi trường Muse riêng; không lưu cookie hay API key vào job.
- muse_gateway_worker.py: sử dụng phiên CLI đã lưu, tạo phiên riêng từng cảnh, lưu ý định gửi trước khi gửi, dùng --wait 1 rồi xác minh lịch sử và trạng thái thật.
- Job pending/uncertain được giữ để chạy tiếp; job thất bại không bị tự tạo lại. Đổi prompt trong cùng cảnh có job cũ sẽ bị chặn để tránh ghi đè hoặc tạo trùng.
- Tải bằng fs.stat/fs.read, kiểm tra từng chunk, hỗ trợ .part và tiếp tục từ offset; xác minh tệp hoàn chỉnh trước khi báo xong.
- series_studio.py: chọn Muse luôn kiểm tra cả clip lẫn ảnh; một ảnh preview không làm bỏ qua video. Muse chạy tuần tự; lỗi Muse ngăn cơ chế thử lại cảnh tự gửi yêu cầu mới.
- Clip Muse chỉ được dùng khi nguồn đang chọn là Muse; một muse_clip.mp4 cũ không chiếm luồng dựng của nguồn khác.
- Ảnh Muse đã xác minh được giữ nguyên trong bước dựng, tránh làm cache sai hash.
- studio_input_modes.py: bổ sung SCENE_001 và dấu phân cách timeline của skill, giữ SHOT/CẢNH cũ.
- web_server.py, web/app.js, web/index.html: cấu hình phiên đã lưu, kiểm tra kết nối thật và nhãn nguồn ảnh/video; bỏ giao diện API key/endpoint/model Muse giả định.
- Kiểm thử Muse cũ được cập nhật cho giao diện kết nối mới; thêm ba file kiểm thử provider, worker và đầu vào skill.

## Checkpoint và khôi phục

Checkpoint trước thay đổi: D:\\STORYBOARD_AI\\backups\\muse_cli_before_integration_20261021.

Để quay lại, dừng sản xuất và thoát hẳn Storyboard, khôi phục các tệp từ checkpoint vào đúng đường dẫn tương đối. muse_gateway_worker.py và ba test_muse_cli_provider.py, test_muse_gateway_worker.py, test_muse_skill_input.py là tệp mới. Checkpoint không chứa hoặc thay đổi cookie đăng nhập Muse.

Bằng chứng, mã thử và hai phim canary nằm dưới D:\\STORYBOARD_AI\\feature_staging\\muse_cli_20261021. Không ghi canary vào kho phim đang sản xuất của ứng dụng chính.

## Giới hạn còn lại

- Luồng tạo media vẫn qua agent gateway nội bộ; chưa xác minh endpoint render độc lập hoặc khả năng chọn model trực tiếp.
- Chưa kiểm tra cookie hết hạn thật, chạy song song nhiều tài khoản, vận hành dài ngày hoặc phim nhiều cảnh cùng nhân vật.
- Bộ kết nối hiện dùng môi trường muse-cli 0.3.2/Pillow 13.0.0/PyAV 19.0.1 đã cài trên máy chính; chưa đóng gói runtime Muse vào bộ cài phân phối.
- Chưa kiểm tra trực quan cửa sổ giao diện đang chạy bằng thao tác người dùng, vì backend chính đang sản xuất. Logic UI và HTTP đã được kiểm thử riêng.
- Chỉ chạy hồi quy trong phạm vi thay đổi và bốn chế độ dựng nêu trên; không chạy toàn bộ các script cũ có thể gọi dịch vụ hoặc điều khiển phiên sản xuất đang mở.
- Hai E2E hoàn chỉnh chạy trước chỉnh sửa nhỏ giữ nguyên preview; sau chỉnh sửa đã dựng lại cảnh dọc từ cùng job, xác minh ảnh/hash và không gửi render mới.
- Khác biệt hash byte giữa một tệp chính và staging là kiểu xuống dòng; kiểm tra nội dung đã chuẩn hóa LF xác nhận giống nhau.

Gói đi kèm gồm mã nguồn liên quan và JSON bằng chứng. Không có cookie, token, .env, dữ liệu tài khoản hay media nhị phân.
