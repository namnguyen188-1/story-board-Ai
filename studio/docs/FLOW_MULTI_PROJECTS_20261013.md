# Storyboard AI Studio — Google Flow nhiều dự án theo thể loại (13/10/2026)

## Hành vi mới
- Mỗi tài khoản Chrome Google Flow của Studio có registry `<state_dir>/studio_flow_projects.json` riêng. Chỉ lưu tên, thể loại, Project ID, Tool ID, dự án đang chọn và bảng gán thể loại. Không sao chép mật khẩu, cookie, token, profile Chrome hay API key.
- Giao diện **Cài đặt → MCP Riêng Storyboard → Dự án Google Flow theo thể loại** có: Quét các tab Flow, Thêm / Gán dự án, Dự án đã lưu, Chuyển sang dự án này, Mở dự án.
- Thêm dự án chỉ chấp nhận một tab URL `https://flow.google.com/project/<project-id>/tool/<tool-id>` đã thực sự mở trong **Chrome của tài khoản được chọn**, qua CDP riêng. Không thể nhập Project ID giả mạo hoặc gán tab thuộc V2.
- Có thể gán `stoic`, `family_drama`, `western`, `action`, `history`, `documentary`, `animation`, `whiteboard`. Studio phân luồng theo thể loại đã chọn. Với chế độ thể loại `auto`, ý tưởng/kịch bản được nhận diện bằng bộ phân loại hiện có; link đối thủ chưa phân tích thì dùng dự án mặc định mà người dùng chọn, không đoán trước.
- Khi sản xuất: chọn đúng URL của dự án đã gán, kiểm tra Chrome và tab chính xác **trước mọi cuộc gọi Gemini**, chuyển URL đã khóa vào worker dưới `--mcp-project-url`, cô lập thông qua `STORYBOARD_FROZEN_PROJECT_URL`. Không cho thay tài khoản/dự án khi sản xuất đang chạy.
- Web Tool khác thể loại có thể nằm ở các Project ID hoặc Tool ID khác nhau. **Không mặc định tương thích**: cầu nối `window.__STORYBOARD_MCP__`, các capability image và SDK được `health` xác minh ở preflight thực trước khi tạo ảnh. Nếu ứng dụng khác không có bridge, chặn `UI_NOT_FOUND` và giữ dữ liệu.
- Bản MCP của V2 không thay đổi; Studio dùng mã sao chép, Node riêng, Chrome 9550/9460..., trạng thái và output riêng. Hạn mức credit và cơ chế chống gửi trùng vẫn giữ nguyên.

## Hướng dẫn
1. Vào Cài đặt MCP, chọn tài khoản Google Flow cần dùng, bấm Mở đăng nhập nếu Chrome chưa mở.
2. Mở Web Tool tương ứng với dự án và thể loại, để Flow hiển thị trang `/project/.../tool/...` trong Chrome đó. Nếu chỉ thấy `/shared/tool/...`, nhấn sử dụng trong dự án theo giao diện Flow trước.
3. Trong Studio bấm **Quét các tab Flow**, chọn dự án trong danh sách; nhập tên và chọn thể loại; bấm **Thêm / Gán dự án**.
4. Chọn dự án đã lưu, bấm **Chuyển sang dự án này** rồi **Mở dự án**. Kiểm tra bằng **Xác minh MCP tạo ảnh**.
5. Lặp lại với thể loại khác. Khi chọn thể loại trên giao diện sản xuất, Studio tự lấy mapping tương ứng. Nếu chưa gán, Studio chặn, không gửi ảnh sang dự án lạ.

## Kiểm thử & giới hạn
- Python và JavaScript syntax PASS.
- Per-account isolated registry, two real-looking project/tool ID pairs, automatic stoic/family_drama routing and exact URL matching PASS in temporary tests.
- Chromium UI real layout and simulated register/switch/open buttons PASS.
- HTTP isolated live handler: unassigned genre and wrong tab both return 409 before creating worker/Gemini request PASS.
- Regressions image-budget guard, private runtime, portable Node, 4-scene image mocked render PASS.
- **Chưa xác minh sản xuất ảnh thật trong cả hai dự án**; riêng Web Tool mới `8fbef6e9-...` trước đó trả `UI_NOT_FOUND` do thiếu bridge. Không thay ứng dụng Flow hay âm thầm tắt guard để báo giả PASS.
- Người dùng cần mở tab từng dự án và gán với thể loại ở giao diện. Không tự thao tác bằng Google account chưa được phép.
- Backup: `checkpoints/multi_flow_projects_before_20261013`; checkpoint: `checkpoints/multi_flow_projects_verified_20261013`.
