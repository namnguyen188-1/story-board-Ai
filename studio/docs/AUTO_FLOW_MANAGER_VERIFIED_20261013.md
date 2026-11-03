# Storyboard AI — Auto Flow Manager v1, 13/10/2026

## Kết luận kiểm chứng
- Đã cài Auto Flow Manager vào chính Storyboard AI tại D:\STORYBOARD_AI\studio. Mọi thao tác MCP dùng Chrome/CDP/account riêng của Storyboard, **không sửa hoặc phụ thuộc runtime V2**.
- Auto bootstrap khi server khởi động: phục hồi phiên Chrome đúng profile, chọn dự án đã xác minh, phát hiện Web Tool V2, tự gán dự án theo thể loại khi thiếu mapping. Khi Google yêu cầu xác thực thì báo cho người dùng đăng nhập, không can thiệp CAPTCHA hoặc token.
- API GET `/api/mcp/auto/status` hiển thị trạng thái; POST `/api/mcp/auto` yêu cầu kết nối lại, thao tác được kiểm thử qua nút Auto Flow trong GUI.
- Auto Flow kiểm tra dự án trước `job_lock`: sửa lỗi thật `AUTO_FLOW_PRODUCTION_BUSY` tự phát sinh khi POST /api/produce giữ khóa và đồng thời đọc GET /api/status.
- Mỗi lần sản xuất tạo **tab Flow riêng** được gắn đúng target ID, bảo vệ tab gốc và ảnh/prompt hiện có. Chỉ đóng tab tạm sau khi MP4 đã hoàn tất; job không chắc chắn không tự gửi lại.

## Quản lý dự án và tạo dự án mới
- Flow homepage đã xác minh có nút `Dự án mới` thực. Đã tạo **một** dự án thử bằng nút UI chính thức: `1f806e0b-5184-448b-8ab4-eab64ee163f0`.
- Mở Web Tool V2-compatible Tool ID `642784b8-d39f-4e7b-b168-fe6218bbc45b` trong dự án mới; bridge `__STORYBOARD_MCP__`, `startImageProduction`, `addToQueue` và SDK image đều PASS. Không tạo ảnh trong bài tạo dự án.
- Đã đăng ký dự án mới làm dự phòng; dự án hoạt động mặc định vẫn là `7a7f7f89-c38d-4237-b4aa-ba499acd7507:642784b8-d39f-4e7b-b168-fe6218bbc45b`. Không đổi ánh xạ thể loại cũ.
- Thêm `studio_mcp/auto_project_provision.py` và `studio_mcp/node/auto-flow-provision-project.mjs`: chỉ tạo khi không còn dự án tương thích nào dùng được, dùng Tool ID đã từng xác minh, ghi journal **trước khi bấm tạo**, xác minh Web Tool sau khi tạo và chỉ đăng ký khi đạt chuẩn.
- Nếu việc tạo dự án bị gián đoạn trước khi nhận Project ID, journal giữ `create_requested`, **không tự tạo lại** (tránh dự án trùng). Khi có Project ID, journal giữ `project_created` để tiếp tục xác minh. Chỉ xoay vòng receipt sau khi dự án mới đã được đăng ký.
- Giới hạn an toàn tối đa 2 lần tạo dự án/ngày/tài khoản. Không tạo dự án mới mỗi lần khởi động. Không hứa chuyển dự án sẽ làm mới quota chung của tài khoản Google.
- Hai job ảnh lịch sử `submit_uncertain` tiếp tục được giữ nguyên, **không tự gửi lại**; Auto Flow chỉ chọn dự án cho các lượt sản xuất mới và độc lập.

## E2E thực tế bằng nút của Storyboard
- GUI Auto Flow: hiển thị READY, nút tự kết nối lại thực hiện POST API và xác minh tương thích V2 — PASS, không tốn credit.
- GUI Sản Xuất Test Offline vẽ màu: 2/2 cảnh, 640x360, MP4 H.264/AAC dài 6.043 giây, âm thanh, phụ đề và in-app playback PASS; `productions/AutoFlow-Manager-Color-Offline-QA-20261013---Offline-Test/episode_001/episode_final.mp4`.
- GUI Sản Xuất Test Offline đen trắng: 2/2 cảnh, 640x360, MP4 H.264/AAC dài 6.043 giây, âm thanh, phụ đề và in-app playback PASS; `productions/AutoFlow-Manager-Mono-Offline-QA-20261013---Offline-Test/episode_001/episode_final.mp4`.
- GUI Sản Xuất Bằng AI qua MCP live: lần đầu phát hiện 409 `AUTO_FLOW_PRODUCTION_BUSY` trước khi gửi ảnh; sửa deadlock trước khóa và chạy tập thử **mới**, không resubmit tập lỗi.
- GUI Live vẽ màu sau sửa: 1/1 cảnh, tạo đúng 1 ảnh MCP thật, có WAV/JSON phụ đề, MP4 H.264/AAC dài khoảng 5.28 giây, FFmpeg full decode PASS; trình xem Studio phát được. Tab production tự đóng và tab gốc giữ nguyên. `productions/Auto-Flow-Manager-Live-Color-20261013-B/episode_001/episode_final.mp4`.
- Kiểm tra độc lập: 10 bộ hồi quy no-paid bao gồm V2 baseline, browser/queue safety, project registration, receipt/daily creation cap, UI project, color engine đều PASS. Lõi Node V2 0.3.1: 38 file byte-identical, 4 adapter hash pinned.

## Vận hành và giới hạn còn lại
- Studio đang mở cửa sổ Desktop riêng; backend hiện thuộc tiến trình desktop_app.py, vì vậy **không ép khởi động lại UI đang mở** để tránh làm mất bản nháp chưa lưu. Những thay đổi code/provisioner cuối cùng cần mở lại ứng dụng một lần để được nạp vào tiến trình đang chạy. Đã kiểm tra mã nguồn bằng compile/tests.
- Auto-create dự án trên Google Flow đã được thực thi và kiểm chứng thực tế một lần. Nhánh auto-create dự phòng trong manager được kiểm thử mô phỏng an toàn (không tạo dự án thứ hai). Chưa chứng minh toàn bộ vòng đời trên tài khoản Google mới/trống hoặc trong sự cố quota thực tế.
- Khi tài khoản Google hết phiên, người dùng cần tự hoàn thành đăng nhập/Xác thực. Không bypass CAPTCHA. Switching project không đảm bảo cấp thêm credit khi tài khoản Google có quota chung.
- Chưa kiểm thử chạy đồng thời nhiều tài khoản, dài 62 cảnh, 1080p hoặc quay vòng khi project thật hết quota. Không công bố `commercial full GREEN` chỉ từ một cảnh live.

Backup trước sửa: `checkpoints/auto_flow_manager_before_20261013`.
Checkpoint hoàn tất: `checkpoints/auto_flow_manager_verified_20261013`.