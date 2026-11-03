# KẾ HOẠCH KHẮC PHỤC NHÁNH PHIM KỊCH ĐA VAI — STORYBOARD AI
Audit trực tiếp máy DESKTOP-EE8BGVF, ngày 31/10/2026. **CHỈ LẬP KẾ HOẠCH — CHƯA THỰC HIỆN BẢN VÁ KIẾN TRÚC NÀY.**

## A. Phạm vi không được vi phạm
- Chỉ sửa nhánh production_mode=cinematic_drama (phim kịch đa vai). Không sửa pipeline thuyết minh, SEO V2, động cơ Muse CLI / Flow MCP nền tảng, thông tin đăng nhập, thread scheduler không liên quan.
- Không phát hành EXE, không sao chép ngược V2, không tự đăng hoặc tự chạy hàng loạt E2E tính phí khi chưa có bằng chứng pass cảnh mẫu.
- Giữ nguyên đúng 9 tên và thứ tự trường skill (FORMAT & STYLE, CHARACTERS, SETTING & START STATE, LIGHTING & COLOR, CAMERA, TIMED ACTION, END STATE, AUDIO, CONSTRAINTS). Ảnh tham chiếu là metadata/attachment của job, KHÔNG thay đổi hợp đồng TXT của skill dùng ở nhánh khác.
- Phục hồi bằng backup có đối chiếu diff, không ghi đè tập đã xuất; phiên bản cũ không được âm thầm "nâng cấp" PASS.

## B. Kết quả audit: các lỗi đã tận mắt đọc trong mã
1. **P0 Character 4-angle không đúng thực chất.** drama_asset_manager.py: render_character_turnaround_sheet dùng Pillow tạo layout 4 ô; nếu chỉ có ảnh 1 góc thì copy cùng ảnh, lật/mờ; không có ảnh thì vẽ silhouette. In log "4 góc" nhưng không có AI render 4 góc thật.
2. **P0 Nhầm nhân vật.** generate_master_asset_pack có fallback lấy image.png của scene đầu tiên thành master tham chiếu cho các nhân vật chưa có ảnh; rủi ro một mặt thay cho nhiều người.
3. **P0 Location/props chưa là ảnh.** generate_master_asset_pack ghi locations/*.json và props/*.json với prompt, không tạo/duyệt ảnh bố cục bối cảnh và đạo cụ, không có version ID xuyên cảnh; props tìm bằng regex từ khóa giới hạn (6 món).
4. **P0 Skill trái yêu cầu sản xuất I2V.** .agents/skills/write-video-scene-prompts/SKILL.md ghi text-to-video độc lập, không đòi ảnh. drama_skill9.py xuất 9 trường cho direct T2V, không tham chiếu scene_image_id, location_id, prop_id.
5. **P0 Muse image-to-video chưa được chứng minh.** muse_gateway_worker.py tải JPG qua fs.write rồi gửi chat prompt hướng dẫn media.generate_video sử dụng ảnh; không truyền input_image/video-tool typed parameter được kiểm chứng. Video có thể là T2V. muse_video_provider.py ghi Direct T2V.
6. **P0 Bỏ qua lỗi asset.** drama_orchestrator.py bao generate_master_asset_pack trong try/except rồi ASSET_PACK_WARN vẫn chạy tiếp.
7. **P0 QC sai.** drama_orchestrator.py đánh SCENE_PASS dù Muse lỗi và dùng still-motion fallback; khi ghép xong PASS_WITH_FALLBACKS bị đổi thành PASS và publish_allowed=True; QC hiện chủ yếu kích thước/thời lượng MP4.
8. **P1 Schema nghèo.** drama_schema.py có characters_present, setting (text), start/end_state (text); không có stable character_id, location_id, prop_id, outfit_id, ownership/position, asset approval/version.
9. **P1 Cảnh Muse nhận chủ yếu ảnh nhân vật, chưa nhận asset bối cảnh và đạo cụ.** drama_video_engine.py -> make_scene_media(...); không có scene image đã tạo trước.
10. **P1 ComfyUI vá gần đây chỉ tạo still fallback.** cinematic_engine/drama_video_engine.py -> comfyui_image_provider.py + comfyui_identity_refs.py đã chạy một cảnh nhưng không giải quyết asset-first hoặc Muse I2V. Giữ nó như lựa chọn có kiểm soát, KHÔNG coi là triển khai đúng luồng đích.
11. **P1 Đầu vào ba loại có tồn tại** web/app.js, web_server.py, drama_orchestrator.py nhưng link transcript thiếu có thể còn mở rộng từ premise; cần nguồn dữ liệu rõ và quy tắc thiếu transcript, không phỏng đoán nguồn.
12. **P1 Asset validation hiện chỉ kiểm tồn tại file** get_scene_character_anchors; không kiểm duyệt ảnh 4 góc, đúng mặt, ảnh nơi chốn/đạo cụ, độ phân giải hay sự toàn vẹn.

## C. Kiến trúc đích của riêng nhánh phim kịch đa vai
INPUT [idea | script | competitor link]
  -> Screenplay Normalizer/Source Evidence -> Story Bible, Cast Registry, Location Registry, Prop Registry
  -> Global Timeline / Sequence Blocks / 9-field scene prompts
  -> ASSET PREPRODUCTION (CHARACTER 4 REAL VIEWS -> ENVIRONMENT MASTER PLATES -> HERO PROP MASTER VIEWS)
  -> ASSET VALIDATION & APPROVAL (image hashes, per-asset ID, version, no placeholders)
  -> SCENE ASSET BINDING (cast IDs / location ID / prop IDs / wardrobe IDs / prop states)
  -> SCENE IMAGE GENERATION (scene composition image from verified references)
  -> SCENE IMAGE QC (face/clothes/set/props + physical state)
  -> MUSE IMAGE-TO-VIDEO (actual scene image attached in supported typed provider operation, if available)
  -> SCENE VIDEO QC (continuity, action, speech/lip sync and audio captions)
  -> ASSEMBLY -> EPISODE QC -> PUBLISH ELIGIBILITY

Không gọi Muse Video khi scene_image chưa đạt. Không biến một ảnh 4 góc bị copy thành 4 góc có thật. Không dùng ảnh tham chiếu thay cho ảnh cảnh. Không phát hành khi QC thiếu.

## D. Triển khai theo giai đoạn (mỗi giai đoạn có điều kiện nghiệm thu)
### G0 — Đóng băng, backup, đồ thị luồng
- Sao lưu mã/tệp cấu hình phim kịch đã chỉnh trước đó, lưu baseline SHA-256 và project tree; không sửa V2; giữ phim cũ và receipts.
- Viết bản đồ call graph 3 input -> planner -> asset -> scene -> Muse -> QC -> UI. Liệt kê chỉ rõ phần từ đợt sửa ComfyUI cần giữ có tùy chọn / bỏ khỏi đường sản xuất chính.
- PASS G0: có diff/backup khôi phục được, test các nhánh cũ còn chạy.

### G1 — Chuẩn hóa 3 đầu vào, story bible
- idea: 3 đề xuất ý tưởng (khi cần), chọn concept; screenplay hoàn chỉnh đủ 3 hồi và 9 mục.
- script: khóa cảnh/thoại nguyên văn người dùng, chỉ tách thực thể, không tự viết lại.
- link: lấy metadata/transcript có chứng cứ, hiển thị nguồn và phần thiếu; nếu thiếu dữ liệu thiết yếu thì dừng/yêu cầu nguồn, không bịa tình tiết đối thủ.
- Từ screenplay tạo registry với stable IDs: character_id, location_id, prop_id, scene_id, sequence_id, voice_id, outfit_id, time_of_day, script_source.
- PASS G1: cả 3 đầu vào cho cùng schema và không mất dialogue beats; cảnh gọi được IDs, không tách từng bối cảnh cùng tên thành nhiều location ảo.

### G2 — Character Master (bắt buộc đủ 4 ảnh thật)
- Cho mỗi actor trích cast metadata, prompt master, identity token/appearance, trang phục theo timeline.
- Tạo 4 ảnh độc lập nhưng cùng 1 identity: front_full, three_quarter, side_profile, back_full; close_face tùy chọn. Có thể gom thành contact sheet khi duyệt, nhưng master nguồn giữ tách file.
- Render bằng Muse Image nếu xác minh Muse hỗ trợ và đã kiểm tra transport thực; không tự giả định tính năng. Phương án khác chỉ kích hoạt theo cấu hình rõ (Flow/MCP/ComfyUI); không Gemini ảnh.
- QC: bốn ảnh có góc đúng, cùng khuôn mặt/tóc/quần áo/tỷ lệ, đủ full-body, không trùng file, không ảnh ảo/Pillow; lưu checksum + status approved.
- Nếu một ảnh fail: chỉ sửa góc lỗi; không tạo lại nhân vật khác hoặc toàn bộ 4 góc.
- PASS G2: 2 nhân vật chính + 1 phụ có ảnh 4 góc khác biệt thực, được duyệt.

### G3 — Environment Master
- Xây Location Registry ổn định theo sequence; mô hình không gian: sơ đồ cửa/cửa sổ/bàn/sofa/vị trí camera, ánh sáng, palette và hướng nhìn.
- Mỗi location: master_wide, reverse, left/right, detail_anchor khi cần. Các ảnh phải nhất quán hình học; không chỉ JSON prompt.
- Liên kết scene.location_id + camera zone; thời gian ban ngày/ban đêm là lighting_variant không được làm đổi layout.
- PASS G3: hai cảnh ở cùng phòng giữ được nội thất và trục quay dù thay góc máy.

### G4 — Props Master + state tracker
- Trích toàn bộ đồ vật quan trọng dựa trên kịch bản và hành động, không giới hạn regex 6 món; lọc đồ không cần khóa để tiết kiệm.
- Mỗi hero prop có ID cố định, ảnh front/angle/detail hoặc trạng thái đặc thù, vật liệu/màu/kích thước/đặc điểm và phiên bản.
- Scene graph ghi ai sở hữu/cầm gì, tay nào, ở đâu, trạng thái ra sao; đầu cảnh N+1 kế thừa cuối cảnh N trừ khi script có hành động chuyển.
- PASS G4: điện thoại/hồ sơ/chiếc gương không đổi màu, kích cỡ hay tự biến mất qua cảnh nối.

### G5 — Scene Reference Binder và prompt skill
- Không sửa hợp đồng 9 nhãn TXT. Chuyển nội dung asset IDs vào scene metadata; chèn mô tả chính xác đã khóa vào các mục đúng như skill.
- Tạo binding manifest cho mỗi cảnh: character refs+outfit variants, location refs, prop refs & state, camera/framing, starting/ending state, checksums.
- Thiếu bất kỳ asset bắt buộc hoặc approved=false -> BLOCKED_ASSET, không khởi tạo render.
- Input quan trọng nhất cho cảnh: ảnh master character/environment/prop, không phải ảnh tùy hứng từ mô tả text.
- PASS G5: 6 cảnh của một sequence sinh đúng 6 manifest, file ảnh và IDs đúng mỗi cảnh, không gửi nhầm nhân vật.

### G6 — Tạo ảnh cảnh trước
- Adapter Muse Image riêng (nếu được chứng minh bằng test ảnh thật; không dùng sai phương thức media.generate_video để giả tạo ảnh); nếu không có khả năng tham chiếu thật thì dừng và báo capability unavailable.
- Trình tạo ảnh cảnh nhận scene asset binding; tự compose prompt và ảnh liên quan, xuất scene_0001/scene_master.png.
- Scene image QC: so sánh nhân vật, bối cảnh, đạo cụ, trạng thái và framing; có preview nhỏ gọn để duyệt/bấm sửa đúng cảnh.
- Cache key = SHA256(script shot + toàn bộ ảnh master + location/prop/version + provider settings). Thay master -> tự đánh dấu cảnh phụ thuộc là STALE.
- PASS G6: một cảnh 2 người có phòng, vật dụng, tư thế và ánh sáng đúng asset; scene image khác master portrait.

### G7 — Muse I2V đúng nghĩa
- Trước hết đọc method schema tool Muse hoặc Flow dùng thực tế; xác minh cách gửi image bytes/image path/image ID có ràng buộc vào chính job và đầu ra có provenance. Upload tệp vào VM chưa đủ.
- Worker chỉ nhận đã duyệt scene_master.png làm frame chuẩn kèm IDs; prompt 9 mục là motion/dialogue instruction, không phải bằng chứng ảnh.
- Nếu Muse CLI không hỗ trợ I2V được kiểm chứng, hiển thị NOT_SUPPORTED và chọn adapter đã xác minh khác; tuyệt đối không tuyên bố Muse I2V thành công nếu dùng T2V.
- Bảo vệ biên nhận pending, không tự gửi lại tốn token, repair chỉ cảnh lỗi.
- PASS G7: video scene1 có hash/provenance của scene_master.png, đối chiếu khung đầu và identity không trôi; thử lại không trùng request.

### G8 — Đồng bộ tiếng/nhân vật/âm thanh/continuity
- Xác định một nguồn thoại chính nhất quán: Muse-native khi video thật có đúng giọng từng người, hoặc TTS đã tạo trước + lip-sync được kiểm chứng. Không tự đổi giọng trong một tập.
- ASR/VAD+word timings từ audio thực, ánh xạ từng beat về đúng speaker; QC trước chữ/đúng ngôn ngữ/pause.
- So sánh END_STATE cảnh N với START_STATE cảnh N+1: người/vật/đạo cụ/tay/cửa/ánh sáng và hướng nhìn; flag deviation có evidence.
- PASS G8: tối thiểu 6 cảnh liền nhau với 2-3 nhân vật, 2 bối cảnh, 3 đạo cụ, không đảo quần áo hoặc mất đồ.

### G9 — QC và phân quyền xuất bản
- Patches drama_orchestrator.py: không đổi PASS_WITH_FALLBACKS thành PASS, không publish_allowed=True chỉ vì ghép được mp4. Scene PASS chỉ khi đúng mode đích, input image hợp lệ, ảnh+video asset QC pass, âm thanh/sub QC pass.
- Phân biệt PASS_VIDEO_I2V / PASS_STILL_FALLBACK_REVIEW / FAIL / BLOCKED_ASSET / PENDING_REMOTE / NEEDS_REVIEW. Still-mode không được tính là Muse I2V đạt.
- Chỉ đăng YouTube khi episode QC xác nhận đủ scene và trạng thái approved; không auto-upload mẫu E2E chưa duyệt.
- PASS G9: diễn tập 1 cảnh Muse thất bại phải giữ FAIL/REVIEW, không đăng và không báo PASS giả.

### G10 — UI, resume, hiệu năng, đóng gói
- Tại mode phim kịch hiển thị một thanh tiến trình gọn: Script -> Master 3 nhóm -> Scene Images -> Muse Videos -> QC -> Export. Cho mở asset review và retry từng lỗi.
- Giữ UI mode thuyết minh, SEO, login Muse, Flow MCP và đa luồng. Không mở thêm popup Chrome/cửa sổ lặp.
- Auto-resume theo hash và receipts: máy mất điện/đứt kết nối không làm lại asset/video đã pass.
- Tạo build staging; regression các nhánh cũ trước khi phát hành. Chỉ đóng EXE và phát hành sau PASS end-to-end.

## E. File thay đổi dự kiến (KHÔNG TỰ ĐỘNG SỬA TRƯỚC KHI QUA GATE)
- cinematic_engine/drama_schema.py: bổ sung stable IDs, asset state, sequence continuity.
- cinematic_engine/drama_planner.py: normalize từ idea/script/link + Cast/Location/Prop Registry, sequence.
- cinematic_engine/drama_asset_manager.py: bỏ model-sheet Pillow giả làm '4 ảnh thật', thêm master images + validation + approval.
- cinematic_engine/drama_skill9.py: giữ 9 mục; bổ sung scene asset bindings external metadata; yêu cầu video shot respect approved assets.
- .agents/skills/write-video-scene-prompts/SKILL.md: giữ nguyên hợp đồng 9 trường/toàn bộ chế độ hiện có. Tạo profile/overlay *riêng nhánh đa vai* (ví dụ references/MULTI_ROLE_ASSET_FIRST.md) để yêu cầu asset-first + I2V mà không làm hỏng các nhánh text-only khác; drama_skill9.py gọi profile này có điều kiện.
- cinematic_engine/drama_orchestrator.py: reorder gates, fail-closed, staged resume; sửa duplicate primary anchor, scene/episode QC giả.
- cinematic_engine/drama_video_engine.py: điều phối scene image -> proper Muse I2V; bỏ gọi still fallback đồng nghĩa PASS Muse.
- muse_video_provider.py + muse_gateway_worker.py: chỉ adapter I2V sau capability proof; bổ sung image adapter độc lập nếu provider thực hỗ trợ. Không sửa lõi CLI credentials/Flow.
- web/app.js + web/index.html + web_server.py: UI nhỏ gọn cho trạng thái tài sản/duyệt ảnh, 3 input giữ nguyên.
- tests/new_*: case giả lập + live E2E + regression, bản audit kiểm chứng.

## F. Ma trận E2E bắt buộc trước release
- INPUT idea / script / link: 3/3 chạy qua cùng asset schema, link thiếu transcript báo thiếu thay vì bịa.
- Character: 3 nhân vật x 4 góc thật; không có 2 ảnh bằng nhau, không chứa ảnh chân dung lấy từ scene khác.
- Environment: >=2 địa điểm x >=3 góc, giữ kiến trúc/chỗ đặt đồ giống nhau.
- Props: >=3 hero props, thay người cầm qua 6 cảnh; continuity state đúng.
- Video: >=6 cảnh có scene images đã duyệt trước video; verify I2V media output attached/anchored, lip-sync/voice/srt có minh chứng.
- Resume: ngắt ngang sau cảnh 3 -> tiếp tục chỉ cảnh lỗi/chưa làm, không trùng charge.
- Fault injection: thiếu reference, Muse auth fail, 429, timeout, scene changed, invalid 4-angle -> dừng an toàn, giữ receipts, KHÔNG PASS giả.
- Regression: narrator, whiteboard, SEO, clone link độc lập, giao diện, login, multi-thread, package/update không giảm chức năng.
- PASS tổng chỉ khi video xem thực tế, continuity QC và toàn bộ trạng thái chấp thuận; unit tests không thay thế xem video.

## G. Điều kiện cần quyết định về công nghệ
- Ưu tiên Muse tạo ảnh và video theo yêu cầu, NHƯNG cần test nhận diện capability image-generation + image-to-video với reference typed argument. Không có bằng chứng -> không tự suy diễn; có thể giữ các provider đã cài dưới dạng lựa chọn, không ép thay Muse.
- Chỉ làm từng giai đoạn sau khi E2E của giai đoạn trước đạt; không đóng gói bản chạy sai luồng.
- Không nên triển khai đồng loạt vào production trước khi lưu backup và soát các lỗi source/asset đang tồn tại.
