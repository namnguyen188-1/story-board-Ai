# Audit MCP V2 gốc và bản riêng Storyboard AI — 13/10/2026
Máy: DESKTOP-EE8BGVF. Audit chỉ đọc nguồn V2, không tạo ảnh/video hoặc sửa V2.

## Sự thật kiểm chứng
- V2 thật gọi D:\FLOW_MCP_SERVER qua auto_studio/flow_mcp_backend.py.
- Storyboard sở hữu D:\STORYBOARD_AI\studio\studio_mcp\node, không chạy chung browser hay profile V2.
- Cả hai package.json: @park-sang-gwon/google-flow-mcp 0.3.1.
- So sánh SHA256 42 file JS/JSON tương ứng trong dist: 38 GIỐNG, 4 KHÁC, không thiếu JS/JSON được đối chiếu.
- Khác biệt: dist/browser/session.js (routing CDP tab thử), dist/browser/tool-tab.js (mode=APP/URL), dist/flow/storyboard-native-image.js (output, credit, queue guard), dist/flow/storyboard-native.js (Web Tool URL cố định thành động).
- Node --check cả 4 file Studio PASS, chỉ chứng minh cú pháp không phải ổn định E2E.
- V2 có package-lock.json, Studio runtime bản sao không có file package-lock.json.

## Tại sao Studio lỗi khác V2
1. V2 dùng một Web Tool Storyboard Director cố định: project ed57618a-88b4-4be3-a429-0e08c506f0fa; tool 642784b8-d39f-4e7b-b168-fe6218bbc45b; ?mode=APP.
2. Studio dùng biến STORYBOARD_STUDIO_TOOL_URL để chọn dự án/tài khoản/thể loại. Tuy nhiên studio_mcp/flow_tool.json mặc định đang khai báo share tool 8fbef6e9-a6e4-4b21-a8b0-0be7a559273d KHÁC tool gốc. Studio đã E2E màu thành công với tool 642784b8... trong project 7a7f7f89-c38d-4237-b4aa-ba499acd7507. Không mặc định coi 8fb... là cùng bridge.
3. Studio có Chrome riêng CDP 9550, nhiều account/project, nhiều quy tắc nhận diện tab và guard hàng đợi. V2 dùng profile/môi trường và cách điều phối riêng, không chung CDP.
4. Python orchestration khác: V2 auto_studio/flow_mcp_backend.py và flow_storyboard_backend.py; Studio studio_mcp/transport.py, image_backend.py, mcp_v2_batch.py, series_studio.py và web_server.py. Thế nên lõi Node giống không đồng nghĩa E2E giống.
5. Lỗi đã được xác minh ở Studio: Python worker thiếu cv2; open_project từng báo success khi chưa thấy cửa sổ/tab; lượt mono live submit_uncertain sau khi tab thử còn ảnh completed. Một số đã có guard, biên nhận mono cũ vẫn chưa giải quyết.

## Kế hoạch ổn định cần làm
- Khóa baseline MCP V2 0.3.1 theo hash, để nguyên V2. Giảm chỉnh sửa dist, đưa account/project/credit policy ra adapter riêng.
- Chỉ gán một Tool có bridge Storyboard Director và kiểm tra image SDK + native capabilities trước Gemini; không tự chuyển sang Tool không tương thích.
- Mỗi lượt ảnh phải có ngữ cảnh queue riêng hoặc tab thử rỗng, không xóa dữ liệu người dùng; xử lý submit_uncertain theo receipts trước khi xét retry.
- Test E2E cùng input cả hand_color và whiteboard qua nút sản xuất thật: canary một ảnh, 2 cảnh rồi nhiều cảnh. Đối chiếu latency, media, log, request, recovery, không fake PASS.
- V2 CDP 9333 hiện không nghe; audit này KHÔNG phải benchmark thời gian thực hai chương trình đang chạy cùng lúc.

Không dùng Git, không đụng Chrome profile V2, không thay key/credit, không sửa V2.