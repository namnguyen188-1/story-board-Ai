# Sửa lỗi xác minh MCP do trùng tab Google Flow — 13/10/2026

Máy: DESKTOP-EE8BGVF. Root: D:\STORYBOARD_AI\studio. Không sửa V2, không tạo ảnh trả phí.

## Chẩn đoán thực tế
- Storyboard dùng MCP V2 lõi 0.3.1, yêu cầu chính xác một tab công cụ được chọn. `flow_storyboard_native_image` từng trả `UI_NOT_FOUND: Expected exactly one Storyboard APP tab; found 2`.
- Chrome Studio cổng 9550 có HAI tab cùng project 7a7f7f89-c38d-4237-b4aa-ba499acd7507 / tool 642784b8-d39f-4e7b-b168-fe6218bbc45b.
- Tab A: image `completed`, có mediaId/jobId và đã có output MP4 thật từ lần E2E đen trắng 15:07. Tab B: video `shot_1` `pending`, chứa prompt do người dùng nhập. Cả hai không đang chạy nhưng đều có nội dung nên không tự đóng tab nào.
- `/api/mcp/account` action=verify trước sửa đôi lúc PASS nếu chỉ có một tab, FAIL khi hai tab xuất hiện. Sau E2E 15:07, `/api/produce` nhiều lần trả 409; lần kiểm tra mới không tiêu credit.

## Sửa
- Thêm `studio_mcp/projects.py::exact_tool_tab_count` đọc đúng Chrome CDP của tài khoản, đếm số tab khớp cả Project ID và Tool ID, không gộp hai tab thành một, không đọc prompt.
- `studio_mcp/accounts.py` xác minh trả `FLOW_MCP_DUPLICATE_TOOL_TABS`, có `tab_count=2` thay vì lỗi chung; sản xuất từ chối ngay nếu nhiều tab trước bước Gemini hoặc tạo ảnh.
- `studio_flow_accounts.py` ngăn nút Mở dự án báo success khi đã có nhiều tab khớp.
- `web_server.py` trả lỗi production 409 giải thích chính xác cần xem xét tab trùng và bảo vệ dữ liệu/credit.
- `web/app.js` hiển thị thông báo tiếng Việt nêu số tab; `web/index.html` đổi phiên bản script để không dùng cache cũ.

## Kiểm thử
- Real MCP `health` trước sửa: `UI_NOT_FOUND: Expected exactly one ... found 2`.
- Đọc riêng metadata trong hai tab Chrome thực: cả hai bridge hợp lệ; image completed + video pending, không đóng hoặc sửa queue.
- `/api/mcp/account` sau sửa trả `{ok:false, reason:FLOW_MCP_DUPLICATE_TOOL_TABS,tab_count:2}` (đúng và không tốn credit).
- Real Edge/Playwright click Xác minh MCP: giao diện hiển thị thông điệp đúng số tab và không tự xóa ảnh/prompt. PASS.
- Test no-paid: duplicate verify, chặn sản xuất, một tab được phép; V2 pinned 0.3.1 kiểm tra SHA256; HTTP genre guard; bảo vệ prompt; GUI project manager — 5 nhóm PASS.
- Backend được khởi động lại chỉ khi IDLE, Studio vẫn IDLE. Hai tab người dùng được giữ nguyên.

## Cần người dùng lựa chọn
- Muốn xác minh PASS trở lại phải **chỉ giữ một tab cùng công cụ**. Một tab đã có ảnh hoàn thành, tab khác giữ kịch bản chưa chạy. Không tự đóng vì có thể làm mất trạng thái đang xem hoặc prompt trong Chrome.
- Khuyến nghị xem và lưu kết quả ảnh/video của tab completed, sau đó đóng chính tab completed, giữ tab chứa prompt chưa chạy. Người dùng có thể chọn ngược lại nếu muốn; không đóng qua MCP khi chưa xác nhận.
- Sau khi chỉ còn một tab: Cài đặt MCP → Xác minh MCP. Hệ thống có thể PASS chức năng, nhưng luồng tạo ảnh mới còn phải vượt chốt queue, không tự xóa shot_1 có prompt.
- E2E live mono gần nhất tại `productions/STUDIO-V2SYNC-LIVE-MONO-20261013-A/episode_001/episode_final.mp4` đã PASS trước khi xuất hiện lỗi trùng tab. Không suy diễn đã PASS nhiều cảnh hoặc tải nặng.

Backup: `checkpoints/duplicate_flow_tabs_before_20261013`. Verified: `checkpoints/duplicate_flow_tabs_verified_20261013`.