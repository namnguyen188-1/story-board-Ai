# FlowKit — R&D audit sau stress test và Muse E2E (2026-10-28)

**Trạng thái: RELEASE_BLOCKED.** Chỉ thay đổi dự án độc lập `D:\FLOWKIT` trên máy chính. Không tạo dự án Google Flow mới; giữ `CLI_LAB_20261021` và đúng Chrome profile `D:\FLOWKIT\runtime\flow_profile`. Không sửa Storyboard AI hay MCP V2, không đóng gói và không cập nhật máy phụ.

## Bài test ảnh/video thật
- Batch 3 job qua Web Tool Remix ẩn, một hàng đợi:
  - `89f0d632-5528-4077-b56d-4203e8ecccb7`: 9:16 PNG, 768×1376, 942655 bytes, succeeded
  - `5afa89c6-31d2-4b10-9aab-618df1ead65f`: 16:9 PNG, 1376×768, 1539713 bytes, succeeded
  - `be9bce98-5f6d-4d15-9b21-7a9bc31a023e`: 16:9 MP4, 1280×720, 4484901 bytes, succeeded
- Cả 3 file đều đối chiếu SHA256 với kết quả tải có xác thực qua API; video FFprobe và giải mã FFmpeg toàn bộ PASS. Không có trùng job. Nhật ký: `state/stress_e2e_20261028.json`.
- Trước đó Web Tool đã có 4/4 lượt ảnh/video dọc-ngang thành công và lượt cold-start thật; lưu tại `state/qa_multiround_20261028.json`.

## Muse
- `state/qa_muse_auth_checks_20261028.json`: **6** tài khoản cục bộ lưu phiên, **1** kết nối trực tiếp thành công (`account_d028a244`), 5 trả `MUSE_AUTH_REQUIRED`.
- FlowKit giờ chọn tài khoản Muse có xác nhận kết nối gần đây, nhưng không tự đổi tài khoản người dùng chủ động chỉ định. `GET /v1/accounts/muse` trả thêm trạng thái `authenticated_recently`; `GET /v1/providers` phân biệt sẵn cookie và đăng nhập thật.
- E2E Muse `d7ddc347-588e-4378-9476-dadac4733cc4`: succeeded; PNG **1152×2048**, 3237899 bytes; MP4 **8.000s 704×1248**, 4032484 bytes, có âm thanh. API download, SHA256, FFprobe, full FFmpeg decode đều PASS. Nhật ký `state/muse_real_scene_e2e_20261028.json`.
- Thêm Muse read-only auth preflight trước mọi `render`/`text`. Nếu hết hạn phiên, chặn trước khi gửi media. `state/test_muse_auth_preflight_blocks_render.py`: 2/2 PASS (mock, không tiêu credit). Muse 5 tài khoản chưa thể coi là READY khi gọi từ xa.

## Flow Direct (không phải Web Tool)
- Image Direct trước đây trả HTTP 502 `RpcError`, job `1da7ab3e-814d-4d93-a348-484976fde3e1` không có remote media ID. Giữ nguyên `recovery_needed`, `browser_hold=false`, không tự resubmit; không được gọi là đã phục hồi.
- Trong động cơ **chỉ thuộc FlowKit**, chặn auto retry hình ảnh khi `RPC_GEN_IMAGE` trả `RpcError [8]` không có media ID; không tái gửi mù có thể phát sinh credit trùng. `state/test_flow_direct_no_ambiguous_retry.py`: PASS (một RPC mock thay vì hai). Đã khởi động lại **chỉ** FlowKit Flow Engine tại 18100.
- Vẫn **chưa giải quyết được root cause upstream 502** và không có xác thực rằng Flow Direct có thể tạo ảnh thật. Đừng tự tạo thêm dự án hay sử dụng model khác để che lỗi. Kiểm tra credit/read-only RPC từ kết nối này chưa xác minh xong; endpoint thử nghiệm chưa được kích hoạt.

## On-Demand, an toàn và kiểm thử phụ
- API `127.0.0.1:18110`, engine `127.0.0.1:18100`; chỉ khi job render cần mới mở Chrome riêng cổng `9233` từ cùng profile và đúng Web Tool.
- Khóa chống chạy song song, idempotency theo request ID, không tự retry kết quả không chắc chắn; lưu job/ảnh/video. Không dùng chung profile/key với Storyboard AI.
- `app/test_gateway.py`: 4/4 PASS sau cập nhật. Sơ bộ cold-start/duplicate tab, queue, download, SHA256, và on-demand đã có các test thành công trước đó.
- Máy phụ `DESKTOP-2CP0L6S` chỉ kiểm tra đọc: **không có ổ D:**, Chrome có, cổng 9550 đang có người sử dụng và chưa có `D:\FLOWKIT`. Không chép hồ sơ đăng nhập hay cài đặt R&D sang máy phụ.

## Điều kiện chưa đạt để phát hành
1. Xử lý/đối soát upstream Flow Direct 502 thực sự; không giả vờ đã hoạt động.
2. Muse 5 tài khoản còn lại cần xác thực hợp lệ nếu muốn vận hành 6 tài khoản; không dùng cookie cũ như bằng chứng.
3. Kiểm thử gián đoạn mạng/Chrome giữa **render có tác vụ thật**, mất điện/hàng đợi bị mất, khả năng phục hồi remote job ID chưa có.
4. Kiểm chứng sản xuất dài nhiều cảnh, stress cao hơn và QA gói cài đặt sau khi thích ứng thư mục cho máy phụ.
5. Giữ `RELEASE_BLOCKED`, không đóng gói, không tích hợp Storyboard AI/MCP V2.

**Nhật ký là dữ liệu riêng tư cục bộ, không chứa cookies hay API keys.** 
