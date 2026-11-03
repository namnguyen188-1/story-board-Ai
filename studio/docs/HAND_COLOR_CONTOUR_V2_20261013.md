# Storyboard AI — Hand Color Contour Fill v2 (2026-10-13)

## Mục tiêu và triển khai
- Nâng cấp duy nhất chế độ `hand_color` từ 18 dải ngang lên hiệu ứng **phác nét đối tượng → tô vùng màu → hoàn thiện**. Không sửa engine đen trắng `engine/tools/draw_animation.py`, Google Flow MCP, provider, giọng, phụ đề hay mã API sản xuất.
- File `studio_hand_color.py` giữ nguyên encoder FFmpeg, overlay bàn tay và API cũ `iter_color_frames()`; gọi engine tách riêng tại `studio_hand_color_strokes.py` để dễ bảo trì.
- Phác contour bằng OpenCV GaussianBlur/Canny/findContours, lọc viền và lấy mẫu theo polyline; bàn tay di chuyển qua tọa độ vẽ thực thay vì di chuyển dọc 18 hàng ngang.
- Tô màu bằng LAB color prototypes + connectedComponents tại độ phân giải nhỏ; chỉ giữ vùng đáng kể, gộp vùng màu vụn vào vùng lân cận; nội suy mềm mép tô tại độ phân giải đầu ra. Mỗi vùng lan màu từ tâm, giúp tránh các vệt ngang và ô vuông trắng ở cuối.
- Giữ đúng pixel ảnh BGR gốc từ nguồn ở frame hoàn thiện; tắt overlay tay trong final hold. Tổng số frame và thời lượng bám WAV (25fps). Không tạo ảnh mới; hoạt động offline.
- `series_studio.py` ghi `hand_color_engine: contour_fill_v2_20261013` trong `render_style.json`; nếu gặp cache màu kiểu cũ, chỉ tái tạo silent/merged/final/result, không xóa ảnh hoặc WAV; lần chạy kế tiếp dùng cache. Các cảnh đen trắng không bị thay đổi.

## Kiểm thử thực tế trên DESKTOP-EE8BGVF
- Bộ unit `test_hand_color_no_api.py` (3/3 PASS), `test_hand_color_contour_no_paid_20261013.py` PASS: bắt đầu trắng, outline theo nét, tô vùng không theo băng ngang, không flash, tất định, giữ đúng pixel nguồn cuối.
- E2E thực bằng **ảnh Google Flow MCP đã tạo trước đó** và WAV thật đã lưu từ `MCP-Live-Hand-Draw-E2E-Oct13-2026`. Tạo riêng `Hand-Color-Contours-V2-E2E-Oct13-2026/episode_001`, hoàn thiện hand-color video có phụ đề/giọng đọc; 1280x720, 9.406 giây, 234 frames, H.264/AAC, 1,632,102 bytes, full FFmpeg decode PASS. Render wall ~15.39s. Không gọi tạo ảnh API mới.
- `test_hand_color_engine_cache_version_20261013.py` PASS: dựng lại clip cũ một lần, rồi dùng cache; SHA256 của ảnh MCP và WAV giữ nguyên.
- Xem khung hình ở sáu mốc đã xác nhận đường viền hiện trước rồi màu lan theo vùng. Ban đầu thử nghiệm còn ô trắng; đã giảm số vùng lẻ từ 172 xuống 71 và làm mềm front tô, bản v2 đạt E2E.
- Bản so sánh ảnh cũ/mới: `productions/Hand-Color-Contours-V2-E2E-Oct13-2026/episode_001/compare_old_new_hand_color.jpg`.
- Video mẫu: `productions/Hand-Color-Contours-V2-E2E-Oct13-2026/episode_001/episode_final.mp4`.

## Giới hạn và kế hoạch tiếp theo
- Đây là thuật toán tô vùng bằng OpenCV (heuristic), không phải vector stroke nhân vật thực hoặc segmentation 3D; với ảnh quang thực phức tạp vẫn có thể xuất hiện các mảng tô theo vùng chứ không hoàn toàn giống bàn tay họa sĩ.
- Đã kiểm tra 1 cảnh 720p với ảnh MCP thực có sẵn; **chưa chạy phim dài 62 cảnh** sau sửa, chưa chứng minh 1080p hoặc hiệu năng multi-scene.
- Khi đóng gói thương mại cần **đảm bảo mang theo module mới** `studio_hand_color_strokes.py` bên cạnh `studio_hand_color.py`; cần smoke clean install tại môi trường phát hành.
- Backup trước sửa: `checkpoints/hand_color_contour_before_20261013`; verified checkpoint `checkpoints/hand_color_contour_verified_20261013`.
