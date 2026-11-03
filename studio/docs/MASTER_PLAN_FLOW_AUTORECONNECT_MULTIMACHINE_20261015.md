# MASTER PLAN — Storyboard AI tự kết nối Web Tool khi đổi dự án, đổi máy
Ngày 15/10/2026. Phạm vi D:\STORYBOARD_AI\studio. KHÔNG sửa V2; không dùng Git.
Trạng thái: NGHIÊN CỨU HOÀN TẤT, CHƯA TRIỂN KHAI CÁC PHASE NÂNG CẤP.

## Mục tiêu
Sau khi người dùng đăng nhập Google hợp lệ lần đầu trên mỗi máy bằng trình duyệt Chrome thật, mở Storyboard AI sẽ tự chạy Chrome của đúng tài khoản, mở đúng Google Flow project, định vị đúng Web Tool, kiểm chứng cầu nối MCP và sẵn sàng sản xuất. Người dùng không phải sao chép URL hay tự mở mục Công cụ khi đổi project. Không vượt CAPTCHA/2FA/đăng nhập Google.

## Kết quả kiểm tra mã nguồn thực tế
- Đã có studio_mcp/auto_flow_manager.py (bootstrap, open known project, kiểm chứng bridge, auto provision), không cần thay toàn bộ MCP.
- API tại thời điểm audit: AUTO_FLOW_READY trên tài khoản default; 4 project đã đăng ký; 9 biên nhận submit_uncertain phải giữ nguyên. Tài khoản thứ hai có profile nhưng 0 project đăng ký.
- studio_mcp/flow_tool.json tham chiếu Tool ID 8fbef6e9...; bridge V2 đã kiểm chứng trong tài khoản mặc định có Tool ID 642784b8...: không được coi hai Tool là tương đương.
- Auto manager chỉ mở URL dự án đã lưu hoặc quét tab có sẵn /project/.../tool/..., KHÔNG có bước đi vào trang dự án -> Tools -> My Tools -> chọn Tool; do đó project mới thiếu tab Tool không tự phục hồi được.
- studio_mcp.projects._parts không nhận /u/1/project/.../tool/... mặc dù accounts._canonical_storyboard_tool_url có nhận. Test thuần hàm: True/False.
- studio_mcp.accounts.add_account là đường helper cũ tạo thư mục .google-flow-* bị whitelist của transport._isolated từ chối; studio_flow_accounts.create là GUI đang dùng và có thư mục .storyboard-studio-* hợp lệ. Sửa/hợp nhất API đường dẫn nhưng không gán nhầm lỗi cho GUI.
- Registry hiện lưu user_data_dir, state_dir tuyệt đối theo Windows HOME và validate cứng default; copy config máy cũ sang Windows user/máy mới có thể bị lỗi.
- Cache READY 240 giây chỉ đảm bảo tab còn hiện diện, không nhất thiết bridge vẫn sống sau khi Google Flow reload.
- Đã có guard queue idempotency: không tự gửi lại 9 tác vụ submit_uncertain.

## Đề xuất kiến trúc v2
A. Browser Supervisor: Chrome thật, profile riêng/tài khoản/máy, CDP nội bộ local-only, xác nhận đúng process, port, profile. Tách CDP_CONNECTED và GOOGLE_SIGNED_IN. Nếu tab hỏng thì khôi phục tab do tool sở hữu; không đụng tab có dữ liệu người dùng.
B. Project+Tool Locator: sau khi mở dự án mới, dùng UI chính thức Google Flow: Tools/Công cụ -> My Tools/Công cụ của tôi -> Tool đã đánh dấu Favorite hoặc do người dùng chỉ định. Nếu không có, mở shared Tool link TRONG dự án được chọn. Chờ URL thật và canonicalize cả /u/N/; không dựng URL dựa vào Tool ID cũ khi không xác minh.
C. Capability Verification: kiểm tra tại exact CDP target và frame __STORYBOARD_MCP__, queue, addToQueue, startImageProduction, Flow SDK image; chỉ thử READ-ONLY và 0 credit. Đăng ký mapping (account + project + tool + version/hash) khi PASS.
D. Session Supervisor: state machine BROWSER_START -> CDP_READY -> AUTH_REQUIRED (chỉ người dùng nhập) -> PROJECT_RESOLVED -> TOOL_FOUND -> BRIDGE_VERIFIED -> READY. Heartbeat/backoff/idempotent; per-production target/tab/job/receipt; production đang chạy thì không đổi project. Remote result unknown thì freeze và reconcile, tuyệt đối không tự resubmit.
E. Machine Migration: export/import metadata dự án, tool fingerprint, genre mappings, profile alias; KHÔNG copy cookies, passwords, OAuth tokens, Chrome data directory, API keys hoặc CDP endpoint giữa máy. Trên máy mới tự cấp profile + state paths + CDP port phù hợp Windows HOME mới, người dùng đăng nhập Google một lần trong Chrome thật. Nếu Tool chưa cấp quyền cho account thì báo NEEDS_TOOL_ACCESS thay vì giả READY.
F. Desktop UX: Khối trạng thái Tài khoản / Chrome / Đăng nhập / Project / Tool / MCP / Queue, nút Tự kết nối, nút Chuyển dự án. Bỏ bước dán URL thủ công; nếu thất bại hiển thị nguyên nhân cụ thể.

## Triển khai tuần tự / acceptance gates
P0. Checkpoint + sửa router nhận /u/N/ + thống nhất whitelist/path tạo account + test migration từ Windows username khác. Không đụng V2.
P1. Thêm locator Node Playwright Tools -> My Tools, hỗ trợ hiển thị nhiều ngôn ngữ và mở shared link trong đúng project; probe bridge không credit.
P2. Persist project/tool registry portable + last-verified per-account + reconciliation queue + lifecycle supervisor tự kết nối sau đổi project, restart Chrome.
P3. GUI có trạng thái trung thực, thao tác không bật chớp Chrome, chỉ hiển thị cửa sổ đăng nhập khi cần; không làm mất bản nháp.
P4. E2E: Chrome tắt/mở lại; 2 project A-B-A; project chưa có Tool URL; /u/1; account thứ hai; machine B/Windows user khác; Chrome bị crash; duplicate Tool tabs; 9 receipts uncertain vẫn đóng băng. 0 paid request trong discovery. Chỉ sau toàn bộ đó mới canary 1 ảnh MCP có chủ ý, rồi 2 cảnh, nhiều cảnh; checkpoint và regression.

## Cơ sở bên ngoài
Google Flow official Help: https://support.google.com/labs/answer/17104535?hl=vi
Chrome 136 CDP changes: https://developer.chrome.com/blog/remote-debugging-port
Playwright CDP: https://playwright.dev/docs/api/class-browsertype
Google native OAuth: https://developers.googleblog.com/modernizing-oauth-interactions-in-native-apps-for-better-usability-and-security/

Không có mã nguồn nào được thay đổi bởi cuộc audit này. Kế hoạch là nghiên cứu/thiết kế, không phải tuyên bố đã hoàn thành E2E.
