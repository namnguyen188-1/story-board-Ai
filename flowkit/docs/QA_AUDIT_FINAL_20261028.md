# FlowKit — Báo cáo audit & E2E (28-10-2026)

Trạng thái: **R&D / RELEASE_BLOCKED**. Động cơ render độc lập, **chưa gắn Storyboard AI hoặc MCP V2**. Không sửa các dự án khác, không tải bản này lên GitHub và không đóng gói phát hành.

## E2E đã thực hiện thật (profile FlowKit trên máy chính)
Profile duy nhất: `D:\FLOWKIT\runtime\flow_profile`, Chrome CDP `9233`. Động cơ sản xuất ảnh/video trong các bài dưới: `provider=webtool`, `webtool_mode=hidden`.

| Bài thử | Job ID | Kết quả | Kiểm chứng |
|---|---|---|---|
| Ảnh ngang 16:9 | 4482cdaf-3ea2-4c89-819f-e0d9322be786 | succeeded, 1376×768 PNG | tải API và SHA256 PASS |
| Video ngang 16:9 | 84d286f0-f4ae-49ac-bbbf-638208fa8aa6 | succeeded, 1280×720 MP4 | tải API, SHA, ffprobe, full ffmpeg decode PASS |
| Ảnh dọc 9:16 | 43714a14-0608-466f-986f-7897c66f741e | succeeded, 768×1376 PNG | tải API và SHA256 PASS |
| Video dọc 9:16 | 3b54b67c-cb4e-46d9-af56-ccc6fdfbd427 | succeeded, 720×1280 MP4 | tải API, SHA, ffprobe, full ffmpeg decode PASS |

Các bài E2E riêng trước đó: ảnh `21c859da-8a88-4b30-9a3f-42cd6e92927e`, video từ Chrome đã đóng `70f37044-abc1-436e-8dd0-920414a9c17b`, đều succeeded.

## Lỗi đã sửa và thử lại
1. Chrome bật lại dùng **đúng profile có phiên đăng nhập**; thiếu profile/config không tự tạo Chrome/profile khác.
2. Cold restart sau khi job lỗi được lưu để điều tra: sửa chặn cài extension gây `FLOW_JOBS_ACTIVE_EXTENSION_CHANGE_BLOCKED`.
3. Chrome restore hai tab trùng: kiểm tra Bridge React và chỉ hợp nhất khi cả hai an toàn, không có cảnh duy nhất chưa lưu; sau sửa lần thử lạnh PASS `ENSURE True, BRIDGE True, UNIQUE_WEBTOOL_TABS 1`.
4. Job Flow Direct `1da7ab3e-814d-4d93-a348-484976fde3e1` trả HTTP 502 `RpcError` lúc `image_submitting` không có media ID; giữ `recovery_needed`, không render lại, chuyển trạng thái duyệt `parked_unverified_502`. Job vẫn còn nguyên lịch sử và API resume trả HTTP 409, nhưng không còn chặn trình duyệt tự ngủ.
5. Web Tool và Flow Direct khi Chrome đóng có trạng thái `sleeping=true, available_on_request=true`, không báo thành lỗi mất kết nối.
6. Browser tự đóng sau thời gian nghỉ (90s cấu hình), API sống; tình trạng sau hồi quy: Chrome không mở, 0 active, 1 parked, 0 blocker.

## API và an toàn — không phát sinh credit trong lượt kiểm tra
- `app/test_gateway.py`: 4/4 PASS. Unit test không khởi động Chrome thật.
- `state/test_recovery_parking.py`: PASS, từ chối park job thực sự chạy/đã có media ID, không cho gửi lại job unknown.
- `state/test_recovery_safety.py`: PASS, chỉ nối lại job với đúng remote shot và trạng thái đủ an toàn.
- `state/qa_final_api_no_credit.py`: PASS, 401 khi thiếu API key; 4 lần gửi lại cùng idempotency key đều reuse đúng job cũ, prompt khác cùng key trả 409, tải 4 file API và so SHA đúng; batch/create/cancel trong môi trường riêng PASS, không gửi job sản xuất thật mới.
- Chrome extension Web Tool sau cold restart `connected=true` và chỉ một tab đúng tool. Đã dọn Chrome profile tạm do unit test cũ, không đụng Chrome của Storyboard AI (9550).
- `state/qa_multiround_20261028.json` lưu bài E2E và kết quả theo từng cảnh.

## Những phần CHƯA ĐẠT, không được báo hoàn thiện 100%
1. **Flow Direct tạo ảnh**: HTTP 502 RpcError; không có server media ID để biết có tạo ảnh trên máy chủ hay không. Chưa được xác nhận phương án khôi phục hay sửa động cơ.
2. **Muse**: 6 tài khoản lưu và cục bộ ready, nhưng kiểm tra kết nối trực tiếp trả `MUSE_AUTH_REQUIRED`. Chưa sản xuất E2E thực tế bằng phiên Muse hiện tại; cần đăng nhập hợp lệ theo tài khoản được phép.
3. **Mất điện/Chrome sập giữa render**: Web Tool dùng React queue tạm; không có durable server job lookup được chứng minh. Chưa bảo đảm phục hồi ảnh/video bị mất trên trang; KHÔNG tự retry với outcome unknown.
4. **Đa cảnh dài/đồng thời, stress test số lượng lớn, hai máy, bản portable**: chưa được xác minh đầy đủ.
5. Chưa xây dựng/kiểm thử gói cài đặt trên máy phụ; không được phát hành.

## Nguyên tắc tiếp tục
- Giữ `RELEASE_BLOCKED`. Không sửa Storyboard AI/MCP V2, không phát hành, không nạp key chung hai máy.
- Không tự gửi lại yêu cầu không rõ trạng thái từ Flow Direct hay Muse; không silent fallback.
- Khi có phiên Muse hợp lệ, chạy một E2E độc lập trước; với Flow Direct cần xác định 502 từ API upstream hoặc hợp đồng request trước khi gửi thêm lệnh tính phí.
- Trước khi release phải PASS kiểm thử sản xuất dài, failure/recovery, cài trên máy thứ hai và xác nhận quyền truy cập riêng.

## Mã và test
- `D:\FLOWKIT\app\browser_lifecycle.py`
- `D:\FLOWKIT\app\flow_browser.py`
- `D:\FLOWKIT\app\gateway.py`
- `D:\FLOWKIT\state\test_dedup_live_browser.py`
- `D:\FLOWKIT\state\test_reuse_authenticated_profile.py`
- `D:\FLOWKIT\state\test_recovery_parking.py`
- `D:\FLOWKIT\state\qa_final_api_no_credit.py`
