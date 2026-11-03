# Storyboard AI Studio — Kiểm thử sản xuất video vẽ thực tế 13/10/2026

## Phạm vi và kết quả
Máy: DESKTOP-EE8BGVF; thư mục: D:\STORYBOARD_AI\studio. Không dùng Git, không sửa V2, không đụng _STORYBOARD_RECYCLE_BIN.

### A. E2E qua API Studio → engine render màu bằng ảnh/âm thử (PASS)
- API POST /api/produce, status INITIALIZING → scene 1/2 → scene 2/2 → CONCAT → COMPLETED 100%, exit_code=0.
- Dữ liệu mode=offline; image_provider=gemini chỉ là tên cấu hình, offline_fixtures tự tạo hình/âm máy và KHÔNG gọi Gemini.
- Output: `productions/E2E-Drawn-Video-Oct13-2026---Offline-Test/episode_001/episode_final.mp4`.
- 2 scenes, tổng 6.043 s, 640×360, video H.264, audio AAC, 230,363 bytes.
- 150 frames, MP4 giải mã toàn bộ bằng FFmpeg không lỗi, manifest PASS, đủ ảnh/audio/clip/phụ đề của 2 cảnh, HTTP Range 206 PASS.
- Contact sheet 6 khung hình: `.../preview_contact_sheet.jpg`.
- Lỗi trong *script test* ban đầu: truy vấn API /api/episode thiếu một dấu nối '-'; production vẫn đã PASS. Khắc phục bằng cách dùng path chính xác lấy từ /api/status. Không chạy lại sản xuất tốn lượt.

### B. E2E render với ảnh đã tạo trước đây + giọng đọc Windows + phụ đề thực (PASS)
- Lấy ảnh thật đã có `mcp_image_test_result/city_lost_time_mcp_scene_001.jpg` (chỉ đọc); tạo hai cách crop làm artwork từng cảnh; không tạo hình bằng API mới.
- TTS *đọc văn bản thành tiếng thật*, Microsoft David Desktop (System.Speech, tiếng Anh). Hai câu chuyện liên tiếp về clockmaker; WAV tự tạo tại chỗ.
- Engine `render_one` với `visual_style=hand_color` (bàn tay vẽ từng hàng lên khung hình, giữ nguyên màu nguồn), 1280×720, karaoke subtitles; FFmpeg merge/concat, qc_clip.
- Output: `productions/Drawing-Color-Real-Art-Voice-E2E-20261013/episode_001/episode_final.mp4`.
- Cảnh 1: 9.04 s, 672,874 B; cảnh 2: 9.16 s, 652,025 B.
- MP4 hoàn thành 18.246 s, 1280×720, H.264/AAC, 1,323,610 B, 455 frames, full FFmpeg decode PASS, 6 thời điểm khung hình kiểm tra có thay đổi, manifest PASS, API /api/episode và HTTP 206 PASS.
- Preview: `.../preview_contact_sheet.jpg`.
- Không gửi yêu cầu ảnh mới Google Flow, không gửi yêu cầu Gemini/TTS qua API trong hai phép thử.

### C. Trạng thái tích hợp online Google Flow (CHƯA PASS)
- Chưa có video live end-to-end với ảnh *mới* tạo qua Web Tool trên tài khoản Flow. Tại thời điểm kiểm tra, Chrome riêng 9550 mở project/tool khác với mapping đã đăng ký trong Studio, API /api/mcp/projects báo không có matching tool tab.
- Không tự động chuyển tài khoản/dự án hoặc gửi job ảnh có thể tiêu credit. Cần người dùng mở đúng Web Tool có cầu nối native image MCP và bấm Xác minh; sau đó mới chạy canary 1 ảnh và tiếp tục E2E online.
- Bài thử offline dùng beep ở nhóm A; nhóm B dùng lời kể TTS Windows thực, không phải giọng F5/Gemini thương mại.

## Bằng chứng và mã hồi quy
- `test_real_hand_drawing_video_e2e_20261013.py`: HTTP full offline production.
- `diagnostics/verify_real_drawn_e2e_mp4_20261013.py`: FFprobe, WAV/MP4/subtitle, Range HTTP, frame differences.
- `diagnostics/create_real_color_draw_voice_e2e_20261013.py`: ảnh cache + Windows voice + vẽ màu.
- `diagnostics/audit_drawn_e2e_media_after_render.py`: decode full video và preview contact sheets.
- `runtime/drawing_e2e_report_20261013.json`: QC máy đọc.
