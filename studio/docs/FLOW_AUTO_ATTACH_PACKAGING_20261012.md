# Storyboard AI — Google Flow Web Tool tự liên kết (12/10/2026)

## Thiết kế cho bản đóng gói

- Nhận diện Google Flow Web Tool cố định được lưu trong `studio_mcp/flow_tool.json`, thuộc **mã nguồn Storyboard**, không lưu cứng URL dự án của một khách hàng.
- Link chia sẻ là điểm mở công cụ. Google Flow có thể chuyển nó thành `/project/{project-id}/tool/{tool-id}` khác nhau tùy tài khoản và quyền truy cập.
- **Mỗi tài khoản có riêng** Chrome profile, cổng CDP và file `studio_private_tool_url.json` trong state dir; tự phát hiện và ghi khi trình duyệt của chính tài khoản đó mở đúng tool ID.
- Khi người dùng nhấn **Mở đăng nhập Google Flow**, Chrome của Storyboard mở link chia sẻ tích hợp; người dùng đăng nhập Google thủ công. **Kiểm tra phiên duyệt** và **Xác minh MCP tạo ảnh** tự đồng bộ đường dẫn dự án hiện tại, không yêu cầu nhập URL.
- UI không có ô nhập URL; API `/api/mcp/accounts` chỉ trả `tool_linked: true/false`, không trả đường dẫn.
- Không sao chép cookie, mật khẩu, token, tài khoản Google hoặc hồ sơ Chrome của người làm tool hay V2 sang máy khách.
- V2 và Storyboard hoạt động độc lập. Tài khoản khách cần được Google Flow cấp quyền dùng công cụ; chỉ đăng nhập không bảo đảm quyền sử dụng và không bảo đảm công cụ còn tồn tại.
- Không tạo ảnh có credit trong kiểm thử thiết lập này. Xác minh kết nối riêng không tương đương E2E tạo ảnh trả phí.

## Các thành phần MCP phải đưa vào bản đóng gói
- `studio_mcp/flow_tool.json` (thông tin công cụ chia sẻ, KHÔNG phải bí mật)
- `studio_mcp/*.py` (Python adapter/account/transport/identity)
- `studio_mcp/node/dist/`, `node_modules/`, `studio-flow-rpc.mjs`, `package.json`, `studio-flow-config.json`
- `studio_mcp/node/node.exe` (Node.js v24.19.0, cục bộ ~89 MB)
- Bộ Python runtime của Studio và các dependencies thường dùng theo Master Plan (đóng gói riêng)
- Trình duyệt Chrome phải có trên máy khách, hoặc installer phải có cơ chế cài hợp lệ và thông báo rõ nếu thiếu.

## KHÔNG mang sang bản đóng gói
- `studio/runtime/` (lịch sử dự án, registry tài khoản cá nhân, nhận diện phiên của chủ máy)
- `studio/productions/`, `studio/checkpoints/`, `studio/inbox/`, output và nhật ký thực thi
- Cookie, token, Chrome profile, các key .env (chỉ tạo cấu hình người dùng mới khi cài)
- `D:\FLOW_MCP_SERVER` hoặc bất kỳ thư mục `D:\YOUTUBE_SEO_PRO_V2` nào

## An toàn và công khai mã nguồn
- Giấu URL trong **giao diện** để khách không phải sao chép/dán, nhưng đường dẫn chia sẻ không thể giữ bí mật tuyệt đối trong phần mềm phát hành offline: người có quyền đọc package có thể xem tài nguyên hoặc lưu lượng mạng.
- Không coi URL chia sẻ là thông tin xác thực. Quyền truy cập Google Flow phải được kiểm soát phía dịch vụ và tài khoản.
- Bản Node.exe cục bộ có thể dùng để chạy mà không cần Node.js hệ thống. **Trước khi phân phối thương mại, lấy và kèm đầy đủ bản quyền/NOTICE đúng của Node.js và thư viện phụ thuộc**; máy này chưa có file LICENSE của Node.js trong Program Files.
- Đây là bước chuẩn bị cho đóng gói; chưa tạo bộ cài đặt và chưa kiểm tra máy khách sạch.

## Luồng sử dụng trên bản phát hành
1. Mở Storyboard AI → Cài đặt MCP.
2. Chọn hoặc thêm tài khoản.
3. Nhấn mở đăng nhập → Chrome hồ sơ riêng mở Web Tool đã tích hợp.
4. Đăng nhập Google. Nếu Flow yêu cầu chấp nhận quyền truy cập/chia sẻ, người dùng thực hiện trong Flow.
5. Quay lại Studio → Kiểm tra phiên duyệt / Xác minh MCP. Studio tự nhận đúng project/tool theo account và lưu riêng.
6. Chỉ khi xác minh thành công mới nên chạy phim. Không bao giờ fallback sang V2.
