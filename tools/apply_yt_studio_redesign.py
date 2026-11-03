from pathlib import Path
import re

html_path = Path(r"D:\STORYBOARD_AI\studio\web\index.html")
html = html_path.read_text(encoding="utf-8")

start_marker = '  <div class="modal-overlay" id="modalYouTubeAdvancedPublish">'
end_marker = '  <!-- FLOATING AI ROBOT ASSISTANT (V2 FLOW ASSISTANT & MONITOR) -->'

if start_marker not in html:
    print("ERROR: start_marker not found")
    exit(1)

if end_marker not in html:
    print("ERROR: end_marker not found")
    exit(1)

start_idx = html.find(start_marker)
end_idx = html.find(end_marker)

old_modal = html[start_idx:end_idx]
print(f"Found old modal from {start_idx} to {end_idx} ({len(old_modal)} chars)")

new_modal = """  <div class="modal-overlay" id="modalYouTubeAdvancedPublish">
    <div class="modal-dialog" style="max-width:1040px;width:96vw;max-height:92vh;padding:0;background:#1f1f1f;border:1px solid #383838;border-radius:8px;box-shadow:0 20px 60px rgba(0,0,0,0.95);overflow:hidden;display:flex;flex-direction:column;font-family:Roboto,'Segoe UI',Arial,sans-serif;color:#f1f1f1;">
      
      <!-- TOP BAR CHUẨN YOUTUBE STUDIO (MỘT MỤC DUY NHẤT) -->
      <div style="padding:14px 24px;border-bottom:1px solid #383838;background:#212121;display:flex;justify-content:space-between;align-items:center;">
        <div style="display:flex;align-items:center;gap:12px;">
          <span style="font-size:1.25rem;font-weight:500;color:#fff;">Chi tiết video</span>
          <span id="advYtCurrentChannelTag" style="font-size:0.75rem;background:#282828;color:#aaa;border:1px solid #383838;padding:3px 10px;border-radius:12px;font-weight:500;">Kênh 1</span>
        </div>
        <div style="display:flex;align-items:center;gap:12px;">
          <button type="button" onclick="closeAllModals()" style="background:transparent;border:none;color:#aaa;font-size:0.88rem;font-weight:500;cursor:pointer;padding:6px 12px;border-radius:4px;">
            Hủy thay đổi
          </button>
          <button type="button" onclick="saveCurrentChannelPublishSettings()" style="background:#282828;border:1px solid #383838;color:#e2e8f0;font-size:0.85rem;font-weight:600;padding:7px 14px;border-radius:4px;cursor:pointer;display:inline-flex;align-items:center;gap:6px;">
            💾 Lưu Cấu Hình
          </button>
          <button type="button" id="btnAdvModalSubmitUpload" onclick="triggerYouTubeUploadFromAdvancedModal()" style="background:#3ea6ff;color:#0f0f0f;border:none;font-size:0.88rem;font-weight:700;padding:8px 18px;border-radius:4px;cursor:pointer;display:inline-flex;align-items:center;gap:6px;">
            🚀 Đăng Video
          </button>
          <button class="modal-close" onclick="closeAllModals()" style="font-size:1.4rem;color:#aaa;background:transparent;border:none;cursor:pointer;line-height:1;padding:0 4px;" title="Đóng">&times;</button>
        </div>
      </div>

      <!-- BODY: 2 CỘT CHUẨN YOUTUBE STUDIO (KHÔNG CHIA TAB) -->
      <div style="flex:1;overflow-y:auto;padding:22px 26px;background:#181818;display:grid;grid-template-columns:1fr 340px;gap:26px;">
        
        <!-- ============================================================== -->
        <!-- CỘT TRÁI: FORM LIỀN MẠCH THEO THỨ TỰ YOUTUBE                    -->
        <!-- ============================================================== -->
        <div style="display:flex;flex-direction:column;gap:20px;">
          
          <!-- 0. KÊNH YOUTUBE ĐĂNG BÀI -->
          <div style="background:#212121;border:1px solid #383838;border-radius:6px;padding:10px 14px;display:flex;justify-content:space-between;align-items:center;gap:12px;">
            <div style="flex:1;">
              <label style="font-size:0.75rem;color:#aaa;display:block;margin-bottom:3px;">📺 Kênh YouTube Đăng Bài:</label>
              <select id="advYtChannelSelect" onchange="syncSelectedYouTubeChannel(this.value)" style="color:#fff;font-weight:600;width:100%;padding:6px 10px;background:#121212;border:1px solid #484848;border-radius:4px;font-size:0.85rem;outline:none;">
                <option value="">Đang tải danh sách kênh...</option>
              </select>
            </div>
            <div>
              <a id="advYtStudioEditorLink" href="https://studio.youtube.com" target="_blank" style="font-size:0.75rem;color:#3ea6ff;text-decoration:none;display:inline-flex;align-items:center;gap:4px;padding:6px 10px;background:#282828;border:1px solid #383838;border-radius:4px;" title="Mở YouTube Studio trên trình duyệt">
                🔗 YouTube Studio ↗
              </a>
            </div>
          </div>

          <!-- 1. TIÊU ĐỀ (BẮT BUỘC) -->
          <div>
            <div style="border:1px solid #606060;border-radius:4px;padding:10px 14px;background:#121212;display:flex;flex-direction:column;gap:4px;">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <label style="font-size:0.75rem;color:#aaa;">Tiêu đề (bắt buộc)</label>
                <span id="advYtTitleCount" style="font-size:0.75rem;color:#aaa;font-family:inherit;">0/100</span>
              </div>
              <input type="text" id="advYtTitle" maxlength="100" placeholder="Thêm tiêu đề mô tả video của bạn..." oninput="updateYtTitleCount(this.value)" style="background:transparent;border:none;color:#fff;font-size:0.92rem;font-weight:500;outline:none;width:100%;">
            </div>
            <div style="font-size:0.75rem;color:#888;margin-top:4px;">Tiêu đề kịch tính, ngắn gọn giúp tăng tỷ lệ nhấp chuột (CTR).</div>
          </div>

          <!-- 2. PHẦN MÔ TẢ -->
          <div>
            <div style="border:1px solid #606060;border-radius:4px;padding:10px 14px;background:#121212;display:flex;flex-direction:column;gap:4px;">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <label style="font-size:0.75rem;color:#aaa;">Phần mô tả</label>
                <span id="advYtDescCount" style="font-size:0.75rem;color:#aaa;font-family:inherit;">0/5000</span>
              </div>
              <textarea id="advYtDescription" maxlength="5000" rows="6" placeholder="Kể cho người xem biết về video của bạn..." oninput="updateYtDescCount(this.value)" style="background:transparent;border:none;color:#fff;font-size:0.88rem;outline:none;width:100%;resize:vertical;line-height:1.45;font-family:inherit;"></textarea>
            </div>
            <div style="font-size:0.75rem;color:#888;margin-top:4px;">Kể ngắn gọn cốt truyện, gắn mốc thời gian (00:00) và các thẻ hashtag chính.</div>
          </div>

          <!-- 3. HÌNH THU NHỎ (THUMBNAIL 16:9) -->
          <div>
            <div style="font-size:0.92rem;font-weight:500;color:#fff;margin-bottom:3px;">Hình thu nhỏ</div>
            <div style="font-size:0.78rem;color:#aaa;line-height:1.4;margin-bottom:8px;">Chọn hoặc tải một hình ảnh lên để thể hiện nội dung trong video của bạn.</div>
            <div style="display:flex;gap:12px;align-items:center;">
              <div style="width:140px;aspect-ratio:16/9;background:#121212;border:2px solid #3ea6ff;border-radius:4px;overflow:hidden;position:relative;">
                <img id="advYtThumbnailPreview" src="" alt="Thumbnail" style="width:100%;height:100%;object-fit:cover;display:block;">
              </div>
              <div style="display:flex;flex-direction:column;gap:6px;">
                <button type="button" class="btn btn-secondary btn-xs" onclick="const inEl=document.getElementById('inCustomThumbnailFile'); if(inEl) inEl.click();" style="padding:6px 12px;font-size:0.78rem;background:#282828;border:1px solid #484848;color:#e2e8f0;border-radius:4px;cursor:pointer;">
                  📁 Đổi ảnh thu nhỏ...
                </button>
                <span style="font-size:0.72rem;color:#888;">Tỷ lệ 16:9 (1280x720) định dạng JPG hoặc PNG.</span>
              </div>
            </div>
          </div>

          <!-- 4. DANH SÁCH PHÁT (PLAYLISTS) -->
          <div>
            <div style="font-size:0.92rem;font-weight:500;color:#fff;margin-bottom:3px;">Danh sách phát</div>
            <div style="font-size:0.78rem;color:#aaa;line-height:1.4;margin-bottom:8px;">Thêm video của bạn vào một hoặc nhiều danh sách phát để người xem khám phá dễ dàng hơn.</div>
            <div style="display:flex;gap:8px;">
              <select id="advYtPlaylistSelect" onchange="syncPlaylistChoice(this.value)" style="flex:1;background:#121212;border:1px solid #606060;color:#fff;padding:8px 12px;border-radius:4px;font-size:0.88rem;outline:none;">
                <option value="auto" selected>🔥 Tự động theo Series &amp; Chủ đề</option>
                <option value="none">Không gán danh sách phát</option>
                <option value="__new__">➕ Tạo danh sách phát mới trên YouTube...</option>
              </select>
              <button type="button" onclick="refreshYouTubePlaylistsFromModal()" title="Làm mới danh sách phát từ kênh" style="padding:0 12px;background:#282828;border:1px solid #484848;color:#aaa;border-radius:4px;cursor:pointer;">🔄</button>
            </div>
            <div id="advYtNewPlaylistWrap" style="display:none;width:100%;margin-top:6px;">
              <input type="text" id="advYtNewPlaylistTitle" placeholder="Nhập tên danh sách phát mới muốn tạo trên YouTube..." style="width:100%;border:1px solid #3ea6ff;background:#121212;color:#3ea6ff;padding:8px 12px;border-radius:4px;font-size:0.85rem;outline:none;">
            </div>
          </div>

          <!-- 5. ĐỐI TƯỢNG NGƯỜI XEM (COPPA) - DẤU CHẤM ĐẦU ĐŨA CHUẨN YOUTUBE -->
          <div>
            <div style="font-size:0.92rem;font-weight:500;color:#fff;margin-bottom:3px;">Đối tượng người xem</div>
            <div style="font-size:0.78rem;color:#aaa;line-height:1.4;margin-bottom:8px;">Dù hoạt động ở quốc gia nào, bạn cũng có nghĩa vụ tuân thủ Đạo luật COPPA.</div>
            
            <div style="background:#242424;border-radius:4px;padding:8px 12px;font-size:0.78rem;color:#bbb;margin-bottom:10px;line-height:1.4;">
              ℹ️ Các tính năng như quảng cáo được cá nhân hoá và thông báo sẽ không hoạt động trên video dành cho trẻ em.
            </div>

            <div style="display:flex;flex-direction:column;gap:8px;">
              <label style="display:inline-flex;align-items:center;gap:10px;font-size:0.85rem;color:#f1f1f1;cursor:pointer;">
                <input type="radio" name="advYtMadeForKids" id="advYtKidsYes" value="1" style="width:16px;height:16px;accent-color:#3ea6ff;cursor:pointer;margin:0;">
                <span>Có, nội dung này dành cho trẻ em</span>
              </label>
              <label style="display:inline-flex;align-items:center;gap:10px;font-size:0.85rem;color:#f1f1f1;cursor:pointer;">
                <input type="radio" name="advYtMadeForKids" id="advYtKidsNo" value="0" checked style="width:16px;height:16px;accent-color:#3ea6ff;cursor:pointer;margin:0;">
                <span>Không, nội dung này không dành cho trẻ em</span>
              </label>
            </div>
          </div>

          <!-- 6. NỘI DUNG TÀI TRỢ & TIẾT LỘ NỘI DUNG AI -->
          <div>
            <div style="font-size:0.92rem;font-weight:500;color:#fff;margin-bottom:3px;">Nội dung được trả tiền để quảng cáo &amp; Nội dung AI</div>
            <div style="display:flex;flex-direction:column;gap:8px;margin-top:6px;">
              <label style="display:inline-flex;align-items:center;gap:10px;font-size:0.85rem;color:#f1f1f1;cursor:pointer;">
                <input type="checkbox" id="advYtContainsSyntheticMedia" checked style="width:16px;height:16px;accent-color:#3ea6ff;cursor:pointer;margin:0;">
                <span>Nội dung đã qua chỉnh sửa hoặc tạo bằng AI (Synthetic / Altered Media - Chuẩn YouTube 2024–2026)</span>
              </label>
              <label style="display:inline-flex;align-items:center;gap:10px;font-size:0.85rem;color:#aaa;cursor:pointer;">
                <input type="checkbox" id="advYtPaidPromotion" style="width:16px;height:16px;accent-color:#3ea6ff;cursor:pointer;margin:0;">
                <span>Video của tôi có chứa nội dung được trả tiền để quảng cáo</span>
              </label>
            </div>
          </div>

          <!-- NÚT HIỆN THÊM (SHOW MORE) -->
          <div>
            <button type="button" onclick="const ex=document.getElementById('advYtExtraSection'); const isHidden = ex.style.display==='none'; ex.style.display=isHidden?'flex':'none'; this.innerText=isHidden?'ẨN BỚT ▲':'HIỆN THÊM (Thẻ Tags, Ngôn ngữ, Danh mục, Bình luận ghim) ▼';" style="background:transparent;border:none;color:#3ea6ff;font-size:0.85rem;font-weight:500;cursor:pointer;padding:4px 0;">
              HIỆN THÊM (Thẻ Tags, Ngôn ngữ, Danh mục, Bình luận ghim) ▼
            </button>
          </div>

          <!-- KHỐI MỞ RỘNG (HIỆN KHI BẤM HIỆN THÊM) -->
          <div id="advYtExtraSection" style="display:none;flex-direction:column;gap:18px;border-top:1px solid #383838;padding-top:16px;">
            
            <!-- THẺ TỪ KHÓA (TAGS 0/500) -->
            <div>
              <div style="border:1px solid #606060;border-radius:4px;padding:10px 14px;background:#121212;display:flex;flex-direction:column;gap:4px;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                  <label style="font-size:0.75rem;color:#aaa;">Thẻ từ khóa (Tags)</label>
                  <span id="advYtTagsCount" style="font-size:0.75rem;color:#aaa;font-family:inherit;">0/500</span>
                </div>
                <textarea id="advYtTags" maxlength="500" rows="3" placeholder="Nhập các từ khóa phân cách bằng dấu phẩy..." oninput="updateYtTagsCount(this.value)" style="background:transparent;border:none;color:#fff;font-size:0.85rem;outline:none;width:100%;resize:vertical;line-height:1.4;font-family:inherit;"></textarea>
              </div>
              <div style="font-size:0.75rem;color:#888;margin-top:4px;">Thẻ từ khóa giúp người xem tìm thấy video khi họ gõ sai chính tả.</div>
            </div>

            <!-- NGÔN NGỮ VIDEO & ÂM THANH -->
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
              <div>
                <label style="font-size:0.75rem;color:#aaa;display:block;margin-bottom:3px;">Ngôn ngữ video &amp; phụ đề:</label>
                <select id="advYtDefaultLang" onchange="onAdvVideoLangChange(this.value)" style="width:100%;background:#121212;border:1px solid #606060;color:#fff;padding:8px 10px;border-radius:4px;font-size:0.82rem;outline:none;">
                  <option value="vi" selected>🇻🇳 vi (Tiếng Việt)</option>
                  <option value="en-US">🇺🇸 en-US (Tiếng Anh Mỹ)</option>
                  <option value="es">🇪🇸 es (Tiếng Tây Ban Nha)</option>
                  <option value="pt-BR">🇧🇷 pt-BR (Tiếng Bồ Đào Nha)</option>
                  <option value="ru">🇷🇺 ru (Tiếng Nga)</option>
                  <option value="ja">🇯🇵 ja (Tiếng Nhật)</option>
                  <option value="ko">🇰🇷 ko (Tiếng Hàn)</option>
                  <option value="zh-CN">🇨🇳 zh-CN (Tiếng Trung)</option>
                </select>
              </div>
              <div>
                <label style="font-size:0.75rem;color:#aaa;display:block;margin-bottom:3px;">Ngôn ngữ âm thanh (Audio Voice):</label>
                <select id="advYtAudioLang" style="width:100%;background:#121212;border:1px solid #606060;color:#fff;padding:8px 10px;border-radius:4px;font-size:0.82rem;outline:none;">
                  <option value="vi" selected>🎙️ vi (Tiếng Việt)</option>
                  <option value="en-US">🎙️ en-US (Mỹ / American)</option>
                  <option value="es">🎙️ es (Tây Ban Nha)</option>
                  <option value="ru">🎙️ ru (Nga)</option>
                </select>
              </div>
            </div>

            <!-- DANH MỤC & GIẤY PHÉP -->
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
              <div>
                <label style="font-size:0.75rem;color:#aaa;display:block;margin-bottom:3px;">Danh mục:</label>
                <select id="advYtCategory" style="width:100%;background:#121212;border:1px solid #606060;color:#fff;padding:8px 10px;border-radius:4px;font-size:0.82rem;outline:none;">
                  <option value="1" selected>🎬 Phim và Hoạt ảnh</option>
                  <option value="24">🎭 Giải trí</option>
                  <option value="27">🎓 Giáo dục</option>
                  <option value="22">👥 Mọi người và Blog</option>
                </select>
              </div>
              <div>
                <label style="font-size:0.75rem;color:#aaa;display:block;margin-bottom:3px;">Giấy phép:</label>
                <select id="advYtLicense" style="width:100%;background:#121212;border:1px solid #606060;color:#fff;padding:8px 10px;border-radius:4px;font-size:0.82rem;outline:none;">
                  <option value="youtube" selected>Giấy phép chuẩn của YouTube</option>
                  <option value="creativeCommon">Creative Commons (Ghi nhận tác giả)</option>
                </select>
              </div>
            </div>

            <!-- PHỐI LẠI SHORTS & QUYỀN NHÚNG -->
            <div>
              <label style="font-size:0.75rem;color:#aaa;display:block;margin-bottom:6px;">Phối lại Shorts &amp; Quyền nhúng:</label>
              <div style="display:flex;gap:16px;align-items:center;font-size:0.82rem;">
                <label style="display:inline-flex;align-items:center;gap:6px;cursor:pointer;color:#f1f1f1;">
                  <input type="radio" name="advYtShortsRemix" id="advYtRemixNone" value="none" checked style="width:15px;height:15px;accent-color:#3ea6ff;margin:0;">
                  <span>Tắt phối lại (Chống reup)</span>
                </label>
                <label style="display:inline-flex;align-items:center;gap:6px;cursor:pointer;color:#aaa;">
                  <input type="radio" name="advYtShortsRemix" id="advYtRemixAudio" value="audio_only" style="width:15px;height:15px;accent-color:#3ea6ff;margin:0;">
                  <span>Chỉ Audio</span>
                </label>
                <label style="display:inline-flex;align-items:center;gap:6px;cursor:pointer;color:#aaa;">
                  <input type="radio" name="advYtShortsRemix" id="advYtRemixAll" value="all" style="width:15px;height:15px;accent-color:#3ea6ff;margin:0;">
                  <span>Cho phép tất cả</span>
                </label>
              </div>
              <div style="display:flex;gap:20px;font-size:0.82rem;margin-top:8px;">
                <label style="display:inline-flex;align-items:center;gap:6px;cursor:pointer;color:#bbb;">
                  <input type="checkbox" id="advYtEmbeddable" checked style="width:15px;height:15px;accent-color:#3ea6ff;margin:0;">
                  <span>Cho phép nhúng video vào trang web bên ngoài</span>
                </label>
                <label style="display:inline-flex;align-items:center;gap:6px;cursor:pointer;color:#bbb;">
                  <input type="checkbox" id="advYtPublishStats" checked style="width:15px;height:15px;accent-color:#3ea6ff;margin:0;">
                  <span>Hiển thị số lượt thích</span>
                </label>
              </div>
            </div>

            <!-- BÌNH LUẬN GHIM TỰ ĐỘNG -->
            <div>
              <div style="border:1px solid #606060;border-radius:4px;padding:10px 14px;background:#121212;display:flex;flex-direction:column;gap:4px;">
                <label style="font-size:0.75rem;color:#3ea6ff;font-weight:500;">📌 Bình luận ghim tự động (Auto Pinned Comment)</label>
                <textarea id="advYtPinnedComment" rows="2" placeholder="Tự động đăng &amp; ghim lên đầu video ngay sau khi xuất bản..." style="background:transparent;border:none;color:#fff;font-size:0.85rem;outline:none;width:100%;resize:vertical;"></textarea>
              </div>
              <div style="font-size:0.75rem;color:#888;margin-top:4px;">Bình luận sẽ được tự động đăng và ghim lên đầu video ngay sau khi xuất bản.</div>
            </div>

            <select id="advYtCaptionCert" style="display:none;"><option value="none">none</option></select>
            <input type="text" id="advYtVideoLocation" style="display:none;">

          </div>

        </div>

        <!-- ============================================================== -->
        <!-- CỘT PHẢI: VIDEO CARD PREVIEW CỐ ĐỊNH & CHẾ ĐỘ HIỂN THỊ          -->
        <!-- ============================================================== -->
        <div style="display:flex;flex-direction:column;gap:16px;">
          
          <!-- VIDEO PREVIEW CARD CHUẨN YOUTUBE -->
          <div style="background:#282828;border-radius:4px;overflow:hidden;display:flex;flex-direction:column;">
            <div style="width:100%;aspect-ratio:16/9;background:#000;display:flex;align-items:center;justify-content:center;position:relative;">
              <div style="width:40px;height:40px;border-radius:50%;background:rgba(0,0,0,0.7);display:flex;align-items:center;justify-content:center;color:#fff;font-size:1.1rem;">▶</div>
              <span style="position:absolute;bottom:6px;right:6px;background:rgba(0,0,0,0.8);font-size:0.72rem;padding:1px 4px;border-radius:2px;font-weight:500;">11:00 HD</span>
            </div>
            <div style="padding:14px 16px;display:flex;flex-direction:column;gap:12px;">
              <div style="display:flex;flex-direction:column;gap:2px;">
                <span style="font-size:0.72rem;color:#aaa;">Đường liên kết của video:</span>
                <span style="font-size:0.84rem;color:#3ea6ff;display:flex;align-items:center;justify-content:space-between;">
                  <span id="advYtPreviewVideoUrl">https://youtu.be/kX82vY1...</span>
                  <button type="button" onclick="navigator.clipboard.writeText(document.getElementById('advYtPreviewVideoUrl').innerText); showToast('Đã sao chép link!');" style="background:transparent;border:none;color:#aaa;cursor:pointer;font-size:0.85rem;" title="Sao chép link">📋</button>
                </span>
              </div>
              <div style="display:flex;flex-direction:column;gap:2px;">
                <span style="font-size:0.72rem;color:#aaa;">Tên tệp gốc:</span>
                <span style="font-size:0.82rem;color:#fff;">episode_final.mp4</span>
              </div>
              <div style="display:flex;flex-direction:column;gap:2px;">
                <span style="font-size:0.72rem;color:#aaa;">Chất lượng:</span>
                <span style="font-size:0.82rem;color:#2ba640;font-weight:500;">✓ 1080p Full HD (60fps)</span>
              </div>
            </div>
          </div>

          <!-- CHẾ ĐỘ HIỂN THỊ (GỘP LUÔN VÀO CỘT PHẢI) -->
          <div style="background:#282828;border-radius:4px;padding:14px 16px;display:flex;flex-direction:column;gap:10px;">
            <div style="font-size:0.88rem;font-weight:500;color:#fff;">Chế độ hiển thị</div>
            
            <div style="display:flex;flex-direction:column;gap:8px;">
              <label style="display:inline-flex;align-items:center;gap:10px;font-size:0.85rem;color:#f1f1f1;cursor:pointer;">
                <input type="radio" name="ytStudioPublishMode" id="radioYtModePublic" value="public" onchange="onYtStudioModeChange('public')" style="width:16px;height:16px;accent-color:#3ea6ff;margin:0;">
                <span>Công khai (Public)</span>
              </label>
              <label style="display:inline-flex;align-items:center;gap:10px;font-size:0.85rem;color:#f1f1f1;cursor:pointer;">
                <input type="radio" name="ytStudioPublishMode" id="radioYtModeUnlisted" value="unlisted" checked onchange="onYtStudioModeChange('unlisted')" style="width:16px;height:16px;accent-color:#3ea6ff;margin:0;">
                <span>Không công khai (Unlisted)</span>
              </label>
              <label style="display:inline-flex;align-items:center;gap:10px;font-size:0.85rem;color:#f1f1f1;cursor:pointer;">
                <input type="radio" name="ytStudioPublishMode" id="radioYtModePrivate" value="private" onchange="onYtStudioModeChange('private')" style="width:16px;height:16px;accent-color:#3ea6ff;margin:0;">
                <span>Riêng tư (Private)</span>
              </label>
              <label style="display:inline-flex;align-items:center;gap:10px;font-size:0.85rem;color:#f1f1f1;cursor:pointer;">
                <input type="radio" name="ytStudioPublishMode" id="radioYtModeSchedule" value="schedule_seo" onchange="onYtStudioModeChange('schedule_seo')" style="width:16px;height:16px;accent-color:#3ea6ff;margin:0;">
                <span>Lên lịch phát hành</span>
              </label>
            </div>

            <!-- KHỐI LÊN LỊCH KHI CHỌN LÊN LỊCH -->
            <div id="advYtScheduleWrap" style="display:none;padding:10px 12px;border:1px solid #383838;border-radius:4px;flex-direction:column;gap:8px;background:#181818;margin-top:4px;">
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
                <div>
                  <label style="font-size:0.7rem;color:#aaa;display:block;margin-bottom:2px;">Ngày:</label>
                  <select id="advYtScheduleDateSelect" onchange="onCustomScheduleChange()" style="width:100%;background:#121212;border:1px solid #484848;color:#fff;padding:6px;border-radius:4px;font-size:0.78rem;outline:none;"></select>
                </div>
                <div>
                  <label style="font-size:0.7rem;color:#aaa;display:block;margin-bottom:2px;">Giờ:</label>
                  <select id="advYtScheduleTimeSelect" onchange="onCustomScheduleChange()" style="width:100%;background:#121212;border:1px solid #484848;color:#fff;padding:6px;border-radius:4px;font-size:0.78rem;outline:none;">
                    <option value="11:30">11:30 Trưa</option>
                    <option value="18:00">18:00 Chiều</option>
                    <option value="20:00" selected>20:00 Tối (Giờ vàng)</option>
                    <option value="21:00">21:00 Tối</option>
                  </select>
                </div>
              </div>
              <label style="display:inline-flex;align-items:center;gap:6px;font-size:0.75rem;color:#bbb;margin-top:2px;">
                <input type="checkbox" id="advYtSetPremiere" style="accent-color:#3ea6ff;width:14px;height:14px;margin:0;">
                <span>Đặt làm buổi Công chiếu (Premiere)</span>
              </label>
              <div style="font-size:0.72rem;color:#3ea6ff;" id="advYtScheduleSummaryText">20:00 - Tối nay</div>
            </div>

          </div>

          <!-- Compatibility Hidden Inputs -->
          <select id="advYtPrivacySelect" onchange="syncPrivacyChoice(this.value)" style="display:none;">
            <option value="unlisted">unlisted</option>
            <option value="public">public</option>
            <option value="schedule_seo">schedule_seo</option>
            <option value="private">private</option>
          </select>
          <input type="radio" name="advYtScheduleRadio" id="advYtRadioNow" value="now" style="display:none;">
          <input type="radio" name="advYtScheduleRadio" id="advYtRadioSchedule" value="schedule" style="display:none;">
          <input type="datetime-local" id="advYtPublishAt" style="display:none;">

        </div>

      </div>

    </div>
  </div>

"""

html = html[:start_idx] + new_modal + html[end_idx:]
html_path.write_text(html, encoding="utf-8")
print("SUCCESSFULLY_UPDATED_INDEX_HTML!")
