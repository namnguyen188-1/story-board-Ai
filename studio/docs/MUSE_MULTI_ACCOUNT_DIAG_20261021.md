# Chẩn đoán tự nhận nhiều tài khoản Muse — 21/10/2026

Đã xác nhận ba hồ sơ có cookie đăng nhập hợp lệ. Kiểm tra trực tiếp https://muse.ai/api/session bằng cookie riêng từng hồ sơ trả HTTP 200, đều có VM; ba VM khác nhau. Không xuất giá trị cookie, token hoặc VM ID ra báo cáo.

Hiện trạng ban đầu: hai hồ sơ READY, hồ sơ thứ ba NEED_LOGIN/WAITING_FOR_LOGIN. Một cây tiến trình auth-export của hồ sơ thứ ba tồn tại hơn 349 giây và giữ muse_render_account_375f233c.lock. Các lần kiểm tra tiếp trả MUSE_QUEUE_BUSY. Đã dừng đúng cây tiến trình xác minh bị kẹt đó, không đóng các trình duyệt khác.

Thay đổi duy nhất ở mã chính: muse_login.py.
- Bỏ đoạn cập nhật legacy trùng lặp sau save_account_session. Đoạn cũ có thể ghi cookie của tài khoản mới đè lên phiên mặc định dù tài khoản đó không được chọn. save_account_session đã có cơ chế chỉ đồng bộ tài khoản đang chọn.
- Giới hạn 35 giây cho lời gọi xác minh Gateway trong auth worker riêng. SDK có recv() không có giới hạn chờ tường minh. Đây là giới hạn bước xác minh; không phải cam kết toàn bộ thao tác đăng nhập hoàn thành trong 35 giây.

Checkpoint mã trước sửa: D:\STORYBOARD_AI\backups\muse_autodetect_recovery_20261021\muse_login.py. Không sao lưu cookie/token vào gói này. Đã giữ nguyên mã multi-account của Antigravity; chỉ thay đổi hai đoạn trên, có đối chiếu nguồn trước khi triển khai. Lần kiểm tra điều kiện triển khai đầu tiên bị chặn do khác newline cuối tệp; xác nhận nội dung khác hoàn toàn chỉ ở newline, rồi triển khai với chuẩn hóa newline.

Kiểm thử: 3 regression mới đạt sau khi quan sát RED:
- test_other_account_export_preserves_active_session
- test_invalid_new_session_preserves_active_session
- test_gateway_verification_cannot_hold_login_indefinitely

14 unit Muse cũ đạt trong staging sau khi bổ sung worker còn thiếu vào bộ thử. Lượt dựng harness đầu có 8 lỗi vì chưa sao chép muse_gateway_worker.py, không phải kết quả hồi quy mã. Các tên ca đó:
test_changed_prompt_cannot_replace_pending_job; test_completed_job_reuses_verified_files; test_failed_remote_job_never_resubmits; test_partial_download_continues_at_saved_offset; test_pending_job_resumes_without_second_submission; test_persistent_lock_releases_after_exception; test_remote_path_cannot_escape_workspace; test_render_creates_real_image_and_video_without_user_reference.
Đã sửa harness và chạy lại đủ 14/14 đạt. Không chạy toàn bộ script dự án có thể tạo media/đụng phiên khác. Chưa chạy E2E luân phiên ba tài khoản.

Kết quả thực tế và giới hạn còn lại:
- Registry hiện có 3 hồ sơ READY và ba cookie REST-session đều hợp lệ.
- Kiểm tra gateway của hồ sơ thứ nhất và thứ ba đạt; hồ sơ thứ hai có hai lần MUSE_CONNECTION_INTERRUPTED.
- Một lần gọi login/complete vẫn trả MUSE_LOGIN_CHECK_TIMEOUT sau 121 giây, dù cookie tài khoản thứ ba đã lưu. Một probe auth-export với đầu ra tệp kết thúc trong 6,8 giây, trả MUSE_LOGIN_BROWSER_NOT_READY.
- Đã mở lại đúng profile thứ ba sau khi cửa sổ cũ bị đóng; không yêu cầu người dùng đăng nhập lại các cookie đã xác minh hợp lệ.
- Vì phản hồi tự nhận/gateway vẫn có lỗi nêu trên, chưa thể kết luận luồng tự nhận tài khoản đã ổn định. Không đánh dấu toàn bộ tính năng là hoàn tất.
