# STORYBOARD AI STUDIO — bản độc lập, sản xuất phim dài tập

Thư mục: D:\STORYBOARD_AI\studio
Bản nguồn upstream (không sửa): D:\STORYBOARD_AI\storyboard-ai-main
Engine đã sửa: studio\engine
Ứng dụng desktop: studio\studio_gui.py
Bộ điều phối: studio\series_studio.py
Điểm mở ứng dụng: D:\STORYBOARD_AI\LAUNCH_STUDIO.bat

## Cách chạy

1. Nhấp đúp LAUNCH_STUDIO.bat.
2. Nhập tên series, số tập, thời lượng, ngôn ngữ và nội dung/cốt truyện.
3. Dùng nút "Kiểm thử Offline" trước: dựng ảnh và âm thanh mô phỏng, KHÔNG tính phí Gemini.
4. Để sản xuất thật, dán API key Gemini riêng vào ô khóa, bấm Lưu khóa riêng.
   Khóa chỉ lưu ở studio\.env. Không dùng chung với YouTube SEO Pro V2.
5. Bấm "Sản xuất tập phim bằng AI". Nút này dùng Gemini thật, có thể phát sinh chi phí.
6. Thành phẩm: studio\productions\<ten-series>\episode_NNN\episode_final.mp4.
7. Chạy lại với cùng series, tập, prompt, cấu hình để tiếp tục từ cảnh thiếu hoặc lỗi.

## Khuyến cáo trước khi sản xuất 30 phút

- Công cụ này làm WHITEBOARD ANIMATION (phim minh họa vẽ tay), không phải phim người thật điện ảnh.
- Mặc định 1 cảnh ~30 giây, 30 phút có khoảng 60 cảnh. Đây là kế hoạch, không phải cam kết thời lượng.
- Quá trình tạo hàng chục hình, lời thoại và phụ đề dùng API Gemini có chi phí và hạn mức.
- Run 1 luồng để ưu tiên giữ bối cảnh, hoặc 2-3 luồng để nhanh hơn, dùng hình cảnh đầu làm anchor.
- Veo không bật, để tránh chi phí tạo video. Có thể phát triển thành chế độ chọn sau.
- Thời lượng thực tế được kiểm tra bằng FFprobe; nếu lệch >20% tool ghi DURATION_REVIEW.
- Phụ đề hiện chia theo thời lượng dựa trên lời thoại; đây là timing ước tính, CHƯA phải căn chữ chính xác từng từ.
- Nên thử một tập 1–2 phút bằng Gemini trước khi chạy 30 phút.
- Nếu Gemini API key chưa có, công cụ chỉ kiểm thử được render offline, KHÔNG thể xác nhận E2E AI thật.
- Nếu thay prompt hoặc thông số đã khóa cho một tập, dùng số tập khác (tránh ghép dữ liệu cũ với nội dung mới).

## Kỹ thuật và phục hồi

- Mã nguồn đã đổi tên file từ timestamp giây sang UUID ở image, voice, render và các asset liên quan.
- Render từng cảnh ở subprocess riêng, trong thư mục riêng, với temp scratch tách khỏi output.
- Có retries phần lập kế hoạch Gemini theo từng nhóm 8 cảnh.
- Kịch bản được ghi plan.json, từng nhóm ở plan_parts/part_NNN.json.
- Mỗi cảnh có image.png, audio.wav, silent.mp4, merged.mp4, final.mp4, result.json, run.log.
- Khi chạy lại: cảnh đã PASS qua ffprobe và hash input được dùng lại, không render lại.
- Kịch bản/tập khác fingerprint sẽ được từ chối overwrite.
- Không chấp nhận thiếu cảnh: đánh dấu INCOMPLETE và không xuất final cho các tập thiếu.
- FFprobe kiểm tra codec, khung hình và stream audio/video trước khi ghép.
- Video tập được ghép bằng FFmpeg concat demuxer với đầu ra MP4 final_pending -> atomically rename.
- Tình trạng: manifest.json (PASS, INCOMPLETE, DURATION_REVIEW).
- Không cần SAM3 riêng; mặc định animation một lượt.
- Quyền truy cập và secrets: .env riêng, không ghi API key vào job.json hoặc nhật ký.

## Lệnh dòng lệnh

Dùng PowerShell:

  cd D:\STORYBOARD_AI\studio
  .\.venv\Scripts\python.exe series_studio.py doctor

Offline:
  .\.venv\Scripts\python.exe series_studio.py run --mode offline --series "My Movie" --episode 1 --prompt "An original adventure" --minutes 0.2 --scene-seconds 5 --size 640x360 --workers 2

Gemini thật (cần studio\.env có GEMINI_API_KEY):
  .\.venv\Scripts\python.exe series_studio.py run --mode live --series "My Movie" --episode 1 --prompt-file "D:\some-prompt.txt" --minutes 30 --scene-seconds 30 --workers 1 --size 1280x720 --language English

## Kiểm thử đã thực hiện

- Source compileall PASS.
- Engine offline 2 cảnh tuần tự PASS (6.043 giây video).
- Engine offline 3 cảnh song song PASS (9.043 giây video).
- Kiểm thử full HD bản gốc dùng mẫu đơn giản: PASS, 4.629 giây render/10.24 giây video.
- Kiểm thử 3 cảnh song song bản gốc trước sửa: FAIL (1/3 cảnh).
- Chưa chạy Gemini live E2E vì không có khóa API riêng được cấu hình.

Bản đã nâng cấp là code cục bộ; chưa chứng minh chất lượng lồng tiếng, thoại thực tế hoặc độ chính xác căn phụ đề với một khóa Gemini đang hoạt động.
