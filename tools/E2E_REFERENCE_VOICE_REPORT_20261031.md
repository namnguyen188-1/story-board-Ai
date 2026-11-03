# Storyboard AI — Kiểm thử ảnh tham chiếu và giọng đọc (31/10/2026)

## Tổng trạng thái: E2E KHÔNG PASS HOÀN TOÀN

Máy chính DESKTOP-EE8BGVF. App launcher giữ nguyên; backend đã được tải lại sau sửa (PID 40800, HTTP /api/status = 200). Hàng đợi sản xuất trống trong lúc kiểm tra. Không can thiệp dự án YouTube SEO Pro V2, không xóa tập sản xuất hoặc tài khoản.

## Các lỗi tìm thấy và thay đổi

1. Cảnh nhiều nhân vật trước đây có thể chỉ gửi ảnh một nhân vật và ảnh tham chiếu bị coi là ảnh phong cách. Đã thêm chế độ character_identity, chuyển ảnh chính và các ảnh nhân vật phụ cùng yêu cầu đa phương thức, ghi SHA-256 từng ảnh; thay đổi bất kỳ ảnh nào thì cache phải dựng lại.
2. Bộ chọn ảnh mốc mặc định có thể chọn nhân vật đầu danh sách chứ không phải người đang nói. Đã ưu tiên primary_focus_character hoặc speaker đầu tiên trong dialogue_beats.
3. Muse CLI tải ảnh nhưng không xác nhận công cụ sinh video thực sự dùng ảnh. Đã bắt buộc ảnh tồn tại, upload lỗi phải dừng và phân biệt xác nhận upload với xác nhận condition image-to-video. Tách thư mục upload theo tag để tránh trùng tên giữa công việc.
4. Khi Muse kết thúc không có video, không tự động đổi tài khoản để gửi lại cùng nội dung. Giữ biên nhận để xem xét / phục hồi.
5. Phụ đề TTS từng sử dụng phân phối độ dài từ thay cho timestamp âm thanh. Đã buộc nhánh dựng ảnh dùng căn chữ native ASR/VAD từ WAV, phát hiện script mismatch, không cho từ nằm trong khoảng im lặng.
6. Cảnh dựng ảnh nếu dịch vụ tạo ảnh thất bại chỉ còn ảnh chân dung thì báo SCENE_COMPOSITION_MISSING — không được đánh dấu cảnh đã hoàn thành.

## Kết quả kiểm thử thực tế

### NHÁNH DỰNG ẢNH — PARTIAL_REFERENCE_IMAGE_FALLBACK (KHÔNG PASS)
- Cảnh: Dưới Bóng Tội Lỗi, tập 1, cảnh 1, Lan + Minh.
- TTS Gemini thật: Lan = Sadachbia, Minh = Fenrir, âm thanh tổng 10.272 giây.
- ASR/VAD native: 30 từ, script_mismatch=false.
- Video có audio+video, duration 10.272 s, size 3,675,017 byte. Audio/video duration delta trước cuối khoảng 0.02 s.
- Image generation: hết quota 429 trên các khóa/mô hình đã thử; ảnh cảnh hoàn chỉnh KHÔNG tạo được.
- Bản xem thử tạo trước khi áp quy tắc fail-closed: D:\STORYBOARD_AI\studio\scratch\E2E_REFERENCE_VOICE_20261031\gemini\episode_001\scenes\scene_0001\scene_final.mp4
- KHÔNG dùng file thử này để đăng YouTube hay xem là video phim chuẩn.
- Báo cáo: D:\STORYBOARD_AI\studio\scratch\E2E_REFERENCE_VOICE_20261031\gemini\episode_001\live_e2e_report.json

### NHÁNH MUSE — FAIL
- Hai ảnh tham chiếu: minh_turnaround.jpg và lan_turnaround.jpg.
- Muse VM xác nhận upload 2/2 ảnh, tác vụ được chấp nhận.
- Lần chạy tài khoản đầu kết thúc nhưng không có video đúng mã cảnh.
- Bản cũ tự chuyển tài khoản; đã ngắt kiểm thử tránh tiếp tục lặp và vá chặn failover cho trường hợp này.
- Biên nhận tác vụ còn trạng thái accepted. Không gửi thêm tác vụ cho đến khi đối chiếu phiên Muse cũ.
- Báo cáo: D:\STORYBOARD_AI\studio\scratch\E2E_REFERENCE_VOICE_20261031\muse_video\episode_001\live_e2e_report.json
- Upload thành công KHÔNG chứng minh Muse đã dùng ảnh làm điều kiện tạo video, nên QC danh tính chưa thể PASS.

## Kiểm thử hồi quy
- test_reference_voice_guards_20261031.py : 4/4 PASS
- test_extra_reference_guards_20261031.py : 3/3 PASS
- test_native_audio_subtitle_sync.py : 3/3 PASS
- test_muse_cli_provider.py : 3/3 PASS
- Tổng 13/13 PASS, py_compile các module chỉnh sửa thành công.

## Điều kiện PASS E2E cuối cùng
1. Nhà cung cấp ảnh trả về ảnh cảnh hoàn chỉnh có chứa cả hai nhân vật đúng tham chiếu, không phải chân dung fallback.
2. Nhà cung cấp Muse trả clip video thực có biên nhận/truy vết rõ đầu vào ảnh; đối chiếu nhân vật, trang phục, khung hình với nguồn tham chiếu.
3. ASR/VAD xác nhận lời đọc đúng kịch bản, từ khớp thời điểm phát âm, không lên chữ trước tiếng; QC với video có audio hợp lệ.
4. Chạy UI/người dùng thật một luồng tạo cảnh đến file xuất cuối rồi QC lại, không tự động đánh PASS khi có fallback không đạt.

## Vị trí
- Script E2E live: D:\STORYBOARD_AI\tools\e2e_reference_voice_live_20261031.py
- Code backup ban đầu: D:\STORYBOARD_AI\tools\backups\reference_voice_20261031_020810
- Hai bản E2E cô lập: D:\STORYBOARD_AI\studio\scratch\E2E_REFERENCE_VOICE_20261031\
- Không sửa các phim đã xuất bản.

## Cập nhật 31/10/2026 — LOẠI GEMINI KHỎI DỰNG ẢNH PHIM KỊCH

- Người dùng xác nhận không dùng Gemini làm động cơ tạo ảnh.
- Đã chuyển cinematic_engine/drama_video_engine.py dùng ComfyUI SDXL local + IP-Adapter; không gọi engine/tools/image_gen.py của Gemini trong nhánh phim kịch.
- Đã sửa cinematic_engine/drama_orchestrator.py: Muse fallback image_provider='comfyui' thay vì 'gemini'.
- Đã thêm studio/comfyui_identity_refs.py: trực tiếp nạp CLIPVision + IPAdapter SDXL + các ảnh tham chiếu của nhân vật, tách từng ảnh; nếu thiếu model hoặc node sẽ lỗi rõ ràng, không giả lập khóa danh tính bằng prompt.
- Đã sửa comfyui_image_provider.py để sử dụng IP-Adapter khi có reference_path hoặc character_reference_paths; không thay đổi hoạt động text-to-image không có ảnh tham chiếu.
- Dịch vụ tạo ảnh nội bộ ComfyUI: D:\ComfyUI, NVIDIA RTX 3060 Ti (8GB), RealVisXL Lightning/SDXL Turbo, IP-Adapter model + CLIP Vision thật. Ban đầu lỗi loader nhận nhầm tên CLIP Vision; đã sửa sang loader trực tiếp, E2E chạy thành công.
- E2E ảnh mới 2 nhân vật (KHÔNG Gemini): D:\STORYBOARD_AI\studio\scratch\E2E_REFERENCE_VOICE_20261031\comfyui\two_character_reference_scene.png ; 768x448 ; 400698 byte ; PASS_FILE; 54.1 giây.
- E2E dựng cảnh từ bản thoại thật đã có, tạo ảnh mới bằng ComfyUI 2 tham chiếu, tiếng thật + phụ đề ASR/VAD: D:\STORYBOARD_AI\studio\scratch\E2E_REFERENCE_VOICE_20261031\comfy_scene\episode_001\scenes\scene_0001\scene_final.mp4 ; 10.272 giây, 3,414,933 byte, ảnh cảnh 1024x576, 30 word timestamps, script_mismatch=false; PASS_TECHNICAL.
- Test regression 4+3+3+3 = 13/13 PASS; py_compile PASS.
- Backend Python đã khởi động lại thành công (PID mới 49096), ứng dụng chính vẫn chạy, HTTP 200.
- CHƯA đánh giá bằng mắt chính xác khuôn mặt/trang phục Minh và Lan của file mới. IP-Adapter có điều kiện ảnh thật nhưng không bảo đảm 100% identity; cần QC nhìn trước khi công bố sản phẩm.
- Giọng Gemini TTS tạo trước đó được tái sử dụng, không phải tạo ảnh Gemini. Video là ảnh tĩnh với chuyển động dựng hậu kỳ, không phải phim AI chuyển động nhân vật thật.
- Vẫn chưa test toàn bộ tập/mọi thể loại; không coi là E2E full tool PASS.
