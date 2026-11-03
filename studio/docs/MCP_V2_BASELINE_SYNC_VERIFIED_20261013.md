# Storyboard AI – Đồng bộ baseline MCP V2 0.3.1, 13/10/2026

**Phạm vi:** DESKTOP-EE8BGVF; Storyboard `D:\STORYBOARD_AI\studio`; bản đối chứng V2 `D:\FLOW_MCP_SERVER`. Không sửa nội dung V2, không dùng Git, không gọi tạo ảnh/video trả phí.

## Thực hiện
- Giữ 38/42 file JavaScript/JSON lõi trong `studio_mcp/node/dist` giống hệt SHA256 V2 0.3.1.
- Ghim bốn fork bắt buộc tại `browser/session.js`, `browser/tool-tab.js`, `flow/storyboard-native-image.js`, `flow/storyboard-native.js` bằng SHA256. Các fork phục vụ Chrome riêng, URL dự án động, output/credit riêng; **không chép đè V2**.
- Sao chép không sửa `package-lock.json` từ V2 vào runtime Node của Storyboard, đối chiếu SHA256 và module cài đặt thực tế: @modelcontextprotocol/sdk 1.32.1, playwright-core 1.62.1, zod 4.5.4; `package.json` V2 và Studio giống hoàn toàn.
- Thêm `studio_mcp/MCP_V2_PINNED_BASELINE.json`, `studio_mcp/v2_baseline.py`; `LocalFlowMcpTransport` kiểm tra hash lõi, fork, lock và phiên bản dependency trước mọi lệnh RPC; lỗi drift chặn trước khi gửi tới Flow.
- Thêm `studio_mcp/node/verify-v2-compatible-tool.mjs` và `projects.probe_v2_compatible_tool`: trước khi **đăng ký dự án mới**, bắt buộc xác minh tab đúng trên Chrome riêng có `__STORYBOARD_MCP__`, addToQueue, startImageProduction và Flow image SDK. Không dùng ID của project V2 để đoán ID tài khoản khác. Chỉ đọc, không tạo ảnh và không xóa prompt.
- Cập nhật `studio_mcp/RELEASE_CONTENTS.json` để đóng gói hash manifest, verifier, lockfile và probe. Không truy cập thư mục V2 khi Studio chạy bình thường.

## Kết quả kiểm chứng
- V2 baseline hash scan: 38/38 lõi và 4/4 adapter, package lock PASS.
- Thử bốn tình huống drift có chủ đích trên **manifest thử riêng**: lỗi file V2, adapter, lockfile, thiếu file đều bị từ chối 4/4; không chỉnh file thật.
- Đăng ký project qua mock contract: tương thích được nhận, khác cầu nối bị chặn trước khi lưu; probe truyền chính xác CDP của account và project ID; 4 phép kiểm PASS.
- 9 bộ hồi quy: baseline pin, compatibility project registration, private MCP guards, queue guard, bảo vệ user prompt, direct image failfast, HTTP genre mapping, hand_color unit, UI project manager: toàn bộ PASS.
- Các tập tin cấu hình phát hành kiểm tra tồn tại: 17 mục; cú pháp Node mới và Python PASS.
- Mở đúng tool đăng ký thật của tài khoản `7a7f7f89... / 642784b8...`: cửa sổ và tab xác minh PASS; `probe_v2_compatible_tool` trả True.
- Khởi động lại **chỉ Studio backend khi IDLE** để nạp mã đồng bộ. POST read-only `/api/mcp/account` verify trả `MCP_APP_CAPABILITIES_PASS`, `open_tabs=1`, Studio IDLE; không gửi lệnh tạo ảnh trả phí.

## Chưa hoàn tất / không được giả PASS
- Share link mặc định `https://flow.google.com/shared/tool/8fbef6e9-a6e4-4b21-a8b0-0be7a559273d` **khác** Tool ID `642784b8-...` đã chứng minh hoạt động. Không thể xác nhận share hiện tại tương thích với app kiểu V2. Bộ kiểm tra mới chặn Tool không có cầu nối; vẫn cần share V2-compatible để cài mới cho khách.
- Chưa chạy E2E trả phí sau đồng bộ hoặc 62-cảnh/1080p. E2E màu Live trước đây từng PASS; E2E đen trắng Live có journal `submit_uncertain`, không được tự retry.
- V2 CDP 9333 không đang chạy, nên không tuyên bố đã so tốc độ E2E V2 và Storyboard song song.
- Bản này là **MCP-core baseline synchronized + guard/regression verified**, không phải tuyên bố toàn bộ Storyboard đã tương đương chất lượng sản xuất V2.

Backup trước chỉnh: `checkpoints/v2_baseline_sync_before_20261013`.
Checkpoint sau xác minh: `checkpoints/v2_baseline_sync_verified_20261013`.