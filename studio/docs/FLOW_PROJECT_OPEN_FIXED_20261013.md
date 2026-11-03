# Storyboard AI — Khắc phục nút Mở dự án Google Flow không mở cửa sổ
Ngày: 2026-10-13. Máy: DESKTOP-EE8BGVF. Root: D:\STORYBOARD_AI\studio.

## Triệu chứng / nguyên nhân
- Chrome riêng của Storyboard chạy ngầm với CDP 9550, nhưng GET /api/mcp/projects trả open_tabs=[] và người dùng không thấy Web Tool.
- Hàm studio_flow_accounts.open_project() trước đây trả {opened:true} ngay sau subprocess.Popen, không chờ xác nhận cửa sổ và tab cụ thể. UI thông báo "Đã mở dự án" mặc dù Chrome chưa chắc mở được.
- Không liên quan lỗi render/credit; không được dùng Studio MCP V2 chung hoặc xử lý bằng ComfyUI.

## Khắc phục
- Thêm _confirmed_visible_project(account,ref,wait_seconds) trong studio_flow_accounts.py: xác minh browser PID thuộc account, chính xác Project ID/Tool ID qua CDP riêng và HWND cửa sổ Chrome hiển thị.
- Khi tab đúng đã tồn tại, đưa Chrome riêng ra trước, không tạo tab trùng. Nếu cửa sổ vẫn ẩn, trả lỗi rõ ràng FLOW_PROJECT_OPEN_BUT_CHROME_HIDDEN.
- Khi chưa có tab, mở cửa sổ Google Flow trong Chrome riêng, đợi tối đa 12 giây cho cả tab và cửa sổ trước khi báo opened=true. Nếu không, trả FLOW_PROJECT_WINDOW_NOT_VISIBLE_OR_TAB_NOT_READY (không giả PASS).
- Không sửa V2; không xóa Chrome profile, token, cookies hoặc queue. Không cần gọi paid image.

## Kiểm thử
- Trước sửa đã tái hiện trạng thái connected:true, tool_open:false, open_tabs:[]; đã dùng POST /api/mcp/project action=open để mở đúng Web Tool và quan sát HWND thật.
- Sau sửa: 4 trường hợp unit mocked PASS: tab đã mở+hiện; Chrome ẩn phải FAIL; tab mới mở+thực sự hiện; khởi chạy không thành công phải FAIL.
- Real Edge/Playwright click nút Mở dự án trong Cài đặt MCP trên giao diện Studio thật; HTTP /api/mcp/project 200; server trả opened:true, window_visible:true, tool_tab_verified:true; GET /api/mcp/projects open_tabs=1 đúng cặp 7a7f7f89-c38d-4237-b4aa-ba499acd7507 : 642784b8-d39f-4e7b-b168-fe6218bbc45b. PASS.
- POST /api/mcp/account action=verify genre=whiteboard read-only trả ok:true reason=MCP_APP_CAPABILITIES_PASS. Không gửi yêu cầu tạo ảnh hoặc video.
- Studio IDLE. Tab riêng vẫn mở, V2 không bị thay đổi.

## Rollback và báo cáo
- Backup trước sửa: checkpoints/flow_open_project_before_20261013
- Checkpoint đã kiểm chứng: checkpoints/flow_open_project_verified_20261013
- Đường dẫn nhật ký: docs/FLOW_PROJECT_OPEN_FIXED_20261013.md

Giới hạn: chưa chứng minh tự mở Google Flow sau khi Chrome bị treo/hỏng profile hoặc mất quyền đăng nhập. Nếu ứng dụng yêu cầu xác thực, vẫn cần người dùng đăng nhập thủ công.
