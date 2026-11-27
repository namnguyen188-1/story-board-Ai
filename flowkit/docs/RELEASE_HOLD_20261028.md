# FlowKit — RELEASE BLOCKED (28/10/2026)

Trạng thái: **R&D / QA — KHÔNG PHÁT HÀNH, KHÔNG ĐẨY LÊN GITHUB, KHÔNG TRIỂN KHAI MÁY PHỤ, KHÔNG GẮN STORYBOARD AI**.

**Bằng chứng hiện có**
- Web Tool Remix ẩn / ảnh: 1 job 768×1376 PNG, `succeeded` (21c859da-8a88-4b30-9a3f-42cd6e92927e).
- Web Tool Remix ẩn / video: 1 job 8 giây MP4, `succeeded` (70f37044-abc1-436e-8dd0-920414a9c17b).
- On-demand đóng/mở Chrome và chống gửi trùng: đã qua một số hồi quy.
- Flow Direct tạo ảnh: trả HTTP 502, job 1da7ab3e-814d-4d93-a348-484976fde3e1 ở `recovery_needed`. Tuyệt đối không gửi lại mù.
- Đã thử bắt đầu đóng ZIP nhưng dừng theo yêu cầu; ZIP dở bị xóa, chưa phát hành.

**Cổng kiểm thử bắt buộc trước khi xét đóng gói**
1. Tạo ảnh lặp lại nhiều lần, cả 9:16 và 16:9; kiểm chứng PNG/JPG, độ phân giải, SHA và tải qua API.
2. Tạo video nhiều job tuần tự; xác nhận không lẫn cảnh, không tạo trùng, MP4 có âm thanh và ffmpeg giải mã PASS.
3. Kiểm tra job lỗi, hết quota, mạng đứt, treo trang, mất extension, restart API và Chrome, không tiêu credit thêm khi trạng thái không rõ.
4. Kiểm tra On-Demand từ Chrome đóng, Chrome mở một tab đúng dự án, không đóng khi đang render hoặc còn media chưa lưu; tự đóng sau thời gian nghỉ.
5. Xác thực riêng Flow Direct / Web Tool / Muse: không silent fallback và không sửa động cơ cũ.
6. Kiểm chứng dữ liệu riêng tư không nằm trong archive, runtime đầy đủ, máy thứ hai chạy E2E sau đăng nhập hợp lệ.
7. Đạt tất cả regression và xác nhận chính thức mới đặt trạng thái QA approved.

Mã build `D:\FLOWKIT\tools\build_portable_release.py` hiện **fail-closed** nếu chưa có `state/RELEASE_APPROVED.json` ghi rõ image_video_e2e và cross_machine_e2e đều được duyệt.

Không thay đổi Storyboard AI, MCP V2, YouTube SEO Pro V2.

## Khóa profile đã tạo ảnh thành công — 2026-10-28

- Profile Chrome sản xuất đã xác minh: `D:\FLOWKIT\runtime\flow_profile`, CDP `9233`; tab chuẩn là Web Tool Remix của `flow_hidden_webtool_url` trong `settings.json`.
- `app/flow_browser.py::machine()` yêu cầu `state/machine.json` chỉ rõ profile và cổng; nếu thiếu hoặc thư mục profile không còn thì **báo lỗi**, không tạo profile mới.
- Khi Chrome đã mở, xác minh chủ sở hữu CDP và đúng **một tab** Web Tool: gọi lại không gửi Chrome URL lần nữa, không tạo tab khác; nếu thiếu/trùng tab thì báo lỗi để kiểm tra.
- Nếu cổng CDP không phản hồi nhưng process Chrome sử dụng profile đã chọn vẫn chạy, không khởi động bản sao.
- Chỉ khi chưa có process profile đó mới được mở Chrome và Web Tool theo chế độ On-Demand.
- Giữ nguyên cookie, lịch sử đăng nhập, extension và phiên sản xuất của profile chuẩn; không lấy profile tạm `%TEMP%` để kiểm thử thực tế.
- Profile test sinh ra do unit test cũ đã đóng. Bài kiểm thử hiện tại dùng mocks và không mở Chrome thật.
- Bài `state/test_reuse_authenticated_profile.py`: PASS — dùng lại profile/tab đang đăng nhập không tăng số tab; thiếu cấu hình hoặc sai profile bị chặn; thiếu tab không tạo Chrome mới.
- `app/test_gateway.py`: PASS 4/4.
- Tab Google Flow trang chủ trống (không có nội dung soạn, đăng nhập hay hội thoại đang mở) của profile FlowKit được đóng an toàn; giữ nguyên một tab Web Tool đã tạo ảnh.
- Dịch vụ API FlowKit được khởi động lại để nhận thay đổi; Chrome sản xuất không bị khởi động lại.
- Lưu ý: job Flow Direct tạo ảnh lỗi trước đây còn `recovery_needed`, không gửi lại khi chưa xác nhận remote. Cơ chế chặn tự đóng Chrome khi có job chưa rõ kết quả vẫn giữ nguyên.
- FlowKit tiếp tục R&D, **RELEASE_BLOCKED**; không đóng gói hay tích hợp Storyboard AI/MCP V2.
