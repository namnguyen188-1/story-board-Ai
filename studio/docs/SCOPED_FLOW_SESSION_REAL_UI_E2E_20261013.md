# Storyboard AI Studio — sửa lỗi nút Sản Xuất bị chặn bởi Web Tool đã có ảnh
Ngày 13/10/2026, máy DESKTOP-EE8BGVF, root D:\STORYBOARD_AI\studio.

## Hiện tượng đã tái hiện trực tiếp
- Người dùng gửi ảnh thông báo: 'Chrome Google Flow riêng chưa kết nối hoặc chưa mở đúng Web Tool'.
- Bấm thực tế nút Sản Xuất Bằng AI trên GUI (Edge Playwright không mock) với 1 ảnh: server HTTP 409 MCP_QUEUE_PREFLIGHT_BLOCKED, vì tab Flow duy nhất còn ảnh hoàn thành từ job trước. Bridge MCP vẫn hoạt động, browser vẫn đăng nhập và chính tab đó chứa ảnh của người dùng.
- Trước đó Studio từng báo UI_NOT_FOUND khi 2 tab cùng Web Tool, vì Native V2 yêu cầu một tab; không thể giải quyết bằng xóa hàng đợi hoặc bắt người dùng tự đóng tab sau mỗi video.

## Sửa theo kiểu tab sản xuất độc lập (không thay lõi V2)
- studio_mcp/node/production-job-tab.mjs: Playwright CDP trong Chrome của đúng tài khoản Storyboard, tạo tab tạm của chính Studio cho mỗi lượt phim; xác minh bridge V2, SDK tạo ảnh và trạng thái tab ban đầu; lấy target ID Chrome. Bảo vệ URL đúng Project/Tool, không truy cập V2. Đóng *chỉ tab tạm* nếu output MP4 hoàn chỉnh/queue image completed; với job lỗi không chắc chắn giữ tab để điều tra. Có chế độ abandon chỉ khi tab vẫn là trạng thái khởi tạo.
- studio_mcp/production_tab.py: API Python cho chuẩn bị và dọn phiên, xác minh account PID/profile và tool ID đã đăng ký. Không sửa cookies, Google key, browser của V2.
- studio_mcp/transport.py: nhận target_id giới hạn 32 hex, truyền scoped target đến đúng Node MCP qua biến worker nội bộ, không can thiệp server/global hoặc V2. studio_mcp/accounts.py: duy trì chốt nghiêm 1-tab bình thường, cho phép production khi có target tách biệt đã được Studio cấp.
- studio_mcp/image_backend.py: phân biệt tab do Studio cấp với hàng đợi thuộc người dùng; vẫn cấm xóa/ghi đè tab gốc. web_server.py: trước khi tạo inbox/Gemini chuẩn bị tab riêng, xác minh read-only MCP health đúng target; truyền target riêng cho worker, dọn tab sau MP4 hoàn thành. series_studio.py: đúng worker được cấp target mới được chạy khi Chrome có nhiều tab.
- web_server.py: nếu thể loại UI để 'Tự nhận diện' nhưng chưa gán project theo thể loại được phát hiện, dùng project V2-compatible đang được chọn thay vì báo nhầm lỗi Chrome. Lựa chọn thể loại thủ công chưa gán vẫn FAIL FAST.
- studio_mcp/RELEASE_CONTENTS.json: thêm hai helper mới để tránh lỗi thiếu dependency khi đóng gói.
- Hai script thử Live trước đây đã khóa chống chạy nhầm gây tốn credit khi bug 409 được sửa.

## Bằng chứng E2E thực tế
- No-paid scoped tab test: tạo tab tạm, health V2 SDK TRUE và queue_count=1 (placeholder), đóng tab tạm, tab cũ không đổi: PASS.
- GUI live qua nút thật, riêng loạt QA 'Scoped Web Tool E2E Mono 20261013 C': POST /api/produce 200 STARTED; MCP mới tạo 1 ảnh (image.png 1,153,724 bytes), scene 1/1, audio/TTS và phụ đề; MP4 5.403 giây H.264/AAC 309,844 bytes; ffmpeg full decode PASS; Cinema UI video ready; backend COMPLETED exit_code=0.
- Nhật ký xác nhận FLOW_PRODUCTION_TAB_CLOSED_AFTER_MP4_PASS; browser private trở lại 1 tab gốc, không thay đổi queue cũ.
- POST read-only /api/mcp/account verify sau khi hoàn tất và sau restart backend: MCP_APP_CAPABILITIES_PASS; Studio IDLE.
- Các bài no-paid regression về V2 pinned core 0.3.1, user prompt protection, stale queue, genre routing, duplicate tabs, hand_color unit PASS; auto genre fallback mô phỏng HTTP 409 trước khi tạo ảnh và không gửi lệnh paid: PASS.
- Tập QA màu ở chế độ offline chạy trực tiếp GUI bị gián đoạn khi backend port 8765 được thay thế/khởi chạy lại bởi một tiến trình khác trên máy. Tập đó ở trạng thái manifest RUNNING, không có episode_final.mp4, KHÔNG được tính PASS; đây không phải lỗi MCP trả phí, cần audit supervisor backend/desktop app nếu tiếp diễn.
- Chưa kiểm chứng 62 cảnh hoặc 1080p sau thay đổi; chỉ 1 scene live mono mới PASS. Live hand_color trước thay đổi có mẫu PASS, sau thay đổi chưa có paid color E2E. Không tuyên bố phát hành thương mại hoàn chỉnh.

## An toàn/rollback
- Không sửa D:\YOUTUBE_SEO_PRO_V2 hay D:\FLOW_MCP_SERVER; 38/42 file core Node vẫn byte-identical V2, 4 adapter fork cũ không đổi hash. Không dùng Git.
- Video và journal gốc để nguyên; không reset credit; chỉ giới hạn một ảnh mới cho live canary. Thư mục QA mono live khác tên phim/tập của người dùng.
- Backup trước sửa: checkpoints/isolated_production_tab_before_20261013.
- Checkpoint sau kiểm chứng: checkpoints/isolated_production_tab_live_e2e_verified_20261013.
- File video: productions/Scoped-Web-Tool-E2E-Mono-20261013-C/episode_001/episode_final.mp4.