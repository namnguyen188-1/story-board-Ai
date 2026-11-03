# Storyboard AI Studio Pro — MCP riêng hoàn toàn (12/10/2026)

## Kiến trúc sau khi tách
- **Studio app**: `D:\STORYBOARD_AI\studio`
- **MCP Node riêng**: `studio\studio_mcp\node\` (dist, node_modules, CLI và RPC riêng; không chạy trong FLOW_MCP_SERVER của V2)
- **Python backend tạo ảnh riêng**: `studio\studio_mcp\image_backend.py`, `transport.py`
- **Registry Studio**: `studio\runtime\storyboard_accounts.json` (chỉ lưu metadata; không có mật khẩu/cookie)
- **Đầu ra MCP Studio**: `studio\runtime\private_mcp_outputs\`
- **Tài khoản mặc định mới**: Chrome user-data `.storyboard-studio-private-chrome-default`, CDP 9550, state `.storyboard-studio-private-state-default`.
- **Tài khoản Studio thứ hai có sẵn**: account_... với CDP 9460 và đường dẫn riêng thuộc Storyboard, được giữ nguyên. Không di chuyển/copy profile Chrome, cookie hay token.
- **V2**: vẫn dùng `D:\FLOW_MCP_SERVER` và Chrome riêng của V2, không sửa hoặc tắt V2, không sử dụng lại session.
- Provider nội bộ `mcp_v2` chỉ là key tương thích trong config và chỉ gọi module PRIVATE tại Studio; **không còn import auto_studio V2 hoặc dùng Flow MCP server V2**.
- Những chế độ cũ khác như `v2_tuanstor` (nếu được chọn thủ công) vẫn là provider V2 riêng, không nằm trong phạm vi MCP mới. Không nhầm nguồn đó với `Google Flow MCP riêng`.

## Thiết lập lần đầu (cần người dùng thực hiện)
1. Tại Storyboard AI Studio Pro, nhấn Ctrl+R để cập nhật giao diện (hoặc mở lại bằng LAUNCH_STUDIO.bat).
2. Vào **Cài đặt API & Veo 3 → MCP Riêng Storyboard**.
3. Chọn **Storyboard MCP riêng (đăng nhập mới)** hoặc thêm một hồ sơ Storyboard khác.
4. Nhấn **Mở đăng nhập Google Flow**, đăng nhập **tài khoản Google riêng** trực tiếp trong Chrome. Không cần nhập mật khẩu vào Studio.
5. Truy cập dự án/tác vụ Web Tool của tài khoản riêng và sao chép URL dạng `https://flow.google.com/project/<uuid>/tool/<uuid>?mode=APP`.
6. Dán vào **URL Web Tool riêng của tài khoản này** và nhấn **Lưu URL Web Tool riêng**.
7. Nhấn **Kiểm tra phiên duyệt** và **Xác minh MCP tạo ảnh**. Chỉ khi đạt health/capability mới nên bấm Sản Xuất.
8. Trong mục Nguồn Vẽ Ảnh, chọn **Google Flow MCP riêng (Nano Banana)** và đặt hạn mức khung hình.

## Tính đúng đắn & an toàn
- Nếu URL riêng chưa lưu, production live bị chặn HTTP 409 **trước khi gọi Gemini tạo kịch bản** hoặc tác vụ tạo ảnh.
- Private RPC chỉ chấp nhận `flow_storyboard_native_image` và bốn action có kiểm soát (health, receipts, dry_run, render_batch).
- Nút xác minh chỉ thực hiện health; không tạo ảnh/trừ credit.
- Trình duyệt sử dụng CDP khác 9333 V2. Mỗi account giữ state riêng, cấm lẫn đường dẫn `.google-flow-chrome` / `.google-flow-mcp` legacy.
- Hạn mức credit kiểm tra cả trong Python lẫn Node; image job journal nằm trong Studio. Lệnh không xác định không được tự gửi lại.
- Media V2 gốc, profile/cookie V2 và các job cũ V2 không được di chuyển; chúng vẫn có thể được quản lý ở V2 nhưng không được Studio dùng chung nữa.
- **Chưa xác nhận tạo ảnh thật**: cần đăng nhập account Studio và dán URL của Flow Tool riêng, sau đó thực hiện một canary được người dùng duyệt. Chưa thực hiện yêu cầu tạo ảnh tiêu phí nào trong đợt tách.

## Kiểm thử đã thực hiện
- Python py_compile + node --check PASS
- Offline account registry/profiles/CDP disjoint PASS
- Local Node RPC spend/budget/tool-url guard PASS (0 credit)
- Mock MCP 4 scenes → imported valid 4 images PASS, một batch duy nhất
- Chromium cài đặt account + nút lưu URL (mock POST) PASS
- HTTP live server ngăn bắt đầu production khi thiếu URL, giữ nguyên inbox và không tạo project PASS
- Chromium chạy nút sản xuất/khóa trạng thái PASS
- HTTP live /api/mcp/accounts PASS; tool-url không hợp lệ trả HTTP 400
- V2 worker và robot còn chạy tại thời điểm kiểm tra; không bị stop.
- No-Git checkpoint trước sửa: `studio\checkpoints\private_mcp_before_20261012`
