# Báo cáo E2E thực tế hai chế độ vẽ — Storyboard AI (13/10/2026)

Máy: DESKTOP-EE8BGVF, thư mục D:\STORYBOARD_AI\studio.

## Chạy trực tiếp bằng nút của Storyboard AI
- Real Edge click nút Test Offline và Sản Xuất Tập Phim Bằng AI (không mock POST /api/produce, không gọi riêng render_one để thay cho E2E).
- Vẽ màu Test Offline: PASS, 2/2 cảnh, MP4 640x360 dài 6.043 giây, H.264/AAC, phụ đề, phát trực tiếp trên Studio.
- Vẽ đen trắng Test Offline: PASS, 2/2 cảnh, MP4 640x360 dài 6.043 giây, H.264/AAC, phụ đề, phát trực tiếp trên Studio.
- Vẽ màu Live Google Flow MCP: PASS, 1 ảnh MCP thật, 1/1 cảnh, MP4 640x360 dài 5.843 giây, H.264/AAC, phụ đề và phát được trong Studio.
- Vẽ đen trắng Live Google Flow MCP: BLOCKED, không có MP4. Lỗi STORYBOARD_IMAGE_REMOTE_UNCERTAIN_NO_RESUBMIT, manifest BLOCKED_MCP_IMAGE. Không gửi lại yêu cầu ảnh.

## Lỗi phát hiện và đã khắc phục
1. Backend HTTP chạy bằng D:\python.exe thiếu cv2, trong khi Studio/.venv có cv2. Đã sửa web_server.py chọn Studio/.venv/Scripts/python.exe cho worker và kiểm tra cv2, numpy, PIL trước khi nhận job. Hai bài Test Offline đạt khi chạy lại qua UI thật.
2. Sau khi tạo ảnh màu, tab Flow thử giữ ảnh trạng thái completed. Đoạn MCP Node trước đó từ chối hàng đợi cũ, nhưng lớp Python đã ghi submit_uncertain từ trước. Đã thêm kiểm tra chỉ đọc queue_items ở nativeImageHealth và StoryboardImageBackend.preflight, chặn completed/busy/foreign trước khi đặt chỗ credit hoặc journal.
3. Phát hiện tab Flow chính có video shot_1 pending chứa 2348 ký tự prompt của người dùng. Đã bổ sung has_prompt dạng boolean và chốt bảo vệ ở Python preflight + Node render_batch. Không được tự clearQueue khi shot_1 đã có prompt, ngoại trừ CDP-target test canary tách biệt được chỉ định rõ ràng.

## Điều tra yêu cầu đen trắng không chắc chắn
- Biên nhận local của job cũ được giữ nguyên tại runtime/private_mcp_outputs/storyboard_studio_mcp_STUDIO-LIVE-MCP-Mono-UI-QA-20261013_ep001/.storyboard_image_jobs/6601d99e4015740fb8c43c60.json (state: submit_uncertain).
- Kiểm tra nhận biên lai read-only qua tool receipts: không có ảnh hoàn tất để khôi phục; kết quả STORYBOARD_IMAGE_PARTIAL_UNCERTAIN_NO_RESUBMIT:1. Không thể kết luận khoản credit đã trừ hay chưa; KHÔNG phát lại chính job cũ.
- Tab Flow chính và shot_1 pending được kiểm chứng không thay đổi; tab thử tạm đóng khi không hoạt động. Studio IDLE, MCP_APP_CAPABILITIES_PASS sau khi khôi phục backend bình thường.
- Bộ chốt bảo vệ vừa được chạy trực tiếp với tab chính (health only): LIVE_USER_PENDING_SHOT_PROTECTED_BEFORE_ANY_RESERVATION_PASS.

## Bằng chứng
- Runtime report: runtime/actual_studio_ui_e2e_both_modes_report_20261013.json (cả 4 kết quả, 3 PASS + 1 BLOCKED).
- MP4 vẽ màu offline: productions/E2E-UI-Real-Fixed-Color-20261013---Offline-Test/episode_001/episode_final.mp4
- MP4 đen trắng offline: productions/E2E-UI-Real-Fixed-Mono-20261013---Offline-Test/episode_001/episode_final.mp4
- MP4 vẽ màu MCP online: productions/STUDIO-LIVE-MCP-Color-UI-QA-20261013/episode_001/episode_final.mp4
- Mã kiểm thử: test_actual_studio_ui_both_modes_20261013.py, test_actual_studio_ui_live_mcp_modes_20261013.py, test_mcp_queue_stale_preflight_no_paid_20261013.py, test_user_prompt_queue_protection_no_paid_20261013.py, diagnostics/read_only_reconcile_mono_mcp_20261013.py, diagnostics/read_only_verify_user_pending_protection.py.
- Mã sửa: web_server.py (đã sửa trước khi khôi phục backend), studio_mcp/image_backend.py, studio_mcp/node/dist/flow/storyboard-native-image.js.
- Các hồi quy no-paid: 6 queue states, populated prompt protection, batch 4 images mocked, private node guards, hand_color tests PASS; Node --check và Python compile PASS.

## Giới hạn
- Ba video đã PASS nhưng mới là E2E 1–2 cảnh. Chưa chứng minh ổn định video dài 62 cảnh, 1080p hoặc full load.
- Đen trắng MCP thực còn BLOCKED ở biên nhận job cũ; muốn chạy mới cần yêu cầu khác và kiểm tra hàng đợi riêng, không được tái gửi job chưa rõ.
- Không sửa V2, không xóa phim cũ, không xóa nhật ký không chắc chắn hoặc nội dung Google Flow của người dùng.
- Backup trước sửa queue: checkpoints/mcp_queue_preflight_before_20261013. Backup trước sửa worker Python: checkpoints/real_tool_e2e_python_fix_before_20261013.
