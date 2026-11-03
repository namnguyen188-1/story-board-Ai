import sys
from pathlib import Path

svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 800" width="1200" height="800" style="background:#070b14;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
  <defs>
    <linearGradient id="gradOld" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#18101a"/>
      <stop offset="100%" stop-color="#0c1220"/>
    </linearGradient>
    <linearGradient id="gradNew" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#1e293b"/>
    </linearGradient>
    <linearGradient id="btnRed" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ef4444"/>
      <stop offset="100%" stop-color="#dc2626"/>
    </linearGradient>
  </defs>

  <!-- Title Top -->
  <text x="600" y="38" fill="#f8fafc" font-size="22" font-weight="bold" text-anchor="middle">KẾ HOẠCH TỐI ƯU GIAO DIỆN XUẤT BẢN CHUẨN YOUTUBE STUDIO 2026</text>
  <text x="600" y="62" fill="#94a3b8" font-size="13" text-anchor="middle">Chuyển đổi từ bố cục 1 cột đơn điệu kéo dài sang Bố cục 2 cột tiêu chuẩn của Google YouTube</text>

  <!-- ================= BÊN TRÁI: HIỆN TRẠNG (CŨ) ================= -->
  <g transform="translate(30, 85)">
    <!-- Panel Background -->
    <rect width="480" height="680" rx="12" fill="url(#gradOld)" stroke="#ef4444" stroke-width="1.5" opacity="0.95"/>
    
    <!-- Badge -->
    <rect x="16" y="16" width="160" height="24" rx="6" fill="#dc2626" fill-opacity="0.2" stroke="#ef4444" stroke-width="1"/>
    <text x="24" y="32" fill="#fca5a5" font-size="11" font-weight="bold">✕ HIỆN TRẠNG (CŨ): RỐI</text>

    <!-- Header info -->
    <text x="16" y="65" fill="#f8fafc" font-size="14" font-weight="bold">Cấu Hình Xuất Bản Chi Tiết</text>
    <text x="16" y="82" fill="#94a3b8" font-size="10">Các ô chức năng kéo dài 100%, lộn xộn, tốn diện tích cuộn</text>

    <!-- Box 1: Kênh YouTube -->
    <rect x="16" y="100" width="448" height="44" rx="6" fill="#090d16" stroke="#334155" stroke-width="1"/>
    <text x=\"26\" y="118" fill="#94a3b8" font-size="10">📺 KÊNH YOUTUBE: (Kéo dài hết mép ngang)</text>
    <text x="26" y="134" fill="#fca5a5" font-size="11" font-weight="bold">2. Stoic Sovereign (69 subs)</text>

    <!-- Box 2: Thumbnail & Title bị bóp méo chung hàng -->
    <rect x="16" y="154" width="448" height="72" rx="6" fill="#090d16" stroke="#334155" stroke-width="1"/>
    <rect x="24" y="162" width="75" height="56" rx="4" fill="#1e293b" stroke="#ef4444" stroke-width="1" stroke-dasharray="3,3"/>
    <text x="32" y="194" fill="#ef4444" font-size="9">Lỗi ảnh</text>
    <text x="110" y="174" fill="#f8fafc" font-size="10" font-weight="bold">TIÊU ĐỀ VIDEO (Bị co cụm vào 1 góc)</text>
    <rect x="110" y="182" width="344" height="36" rx="4" fill="#030712" stroke="#334155" stroke-width="1"/>
    <text x="118" y="204" fill="#cbd5e1" font-size="10">Suelta lo que no puedes: controlar...</text>

    <!-- Box 3: Mô tả video dài ngoằng -->
    <rect x="16" y="236" width="448" height="95" rx="6" fill="#090d16" stroke="#334155" stroke-width="1"/>
    <text x="26" y="254" fill="#f8fafc" font-size="10" font-weight="bold">MÔ TẢ VIDEO (Kéo dài ngang toàn màn hình)</text>
    <rect x="24" y="262" width="432" height="60" rx="4" fill="#030712" stroke="#334155" stroke-width="1"/>
    <text x="34" y="282" fill="#94a3b8" font-size="10">Gastamos nuestra vida intentando retener el viento...</text>

    <!-- Box 4: Danh sách phát -->
    <rect x="16" y="341" width="448" height="44" rx="6" fill="#090d16" stroke="#334155" stroke-width="1"/>
    <text x="26" y="359" fill="#f8fafc" font-size="10" font-weight="bold">DANH SÁCH PHÁT (Dài thượt đơn điệu)</text>
    <text x="26" y="375" fill="#cbd5e1" font-size="10">🔥 Tự động (Theo Series &amp; Chủ đề)</text>

    <!-- Box 5: Bình luận ghim chen ngang -->
    <rect x="16" y="395" width="448" height="52" rx="6" fill="#090d16" stroke="#eab308" stroke-width="1" stroke-opacity="0.4"/>
    <text x="26" y="413" fill="#fde047" font-size="10" font-weight="bold">📌 BÌNH LUẬN GHIM (Chen vào giữa COPPA &amp; Playlist)</text>
    <text x="26" y="432" fill="#cbd5e1" font-size="10">Cuál es esa carga externa que has estado intentando...</text>

    <!-- Box 6: COPPA -->
    <rect x="16" y="457" width="448" height="46" rx="6" fill="#090d16" stroke="#334155" stroke-width="1"/>
    <text x="26" y="475" fill="#f8fafc" font-size="10" font-weight="bold">ĐỐI TƯỢNG NGƯỜI XEM (COPPA):</text>
    <text x="26" y="492" fill="#ef4444" font-size="10">✕ Không dành cho trẻ em</text>

    <!-- Nhược điểm callouts -->
    <g transform="translate(16, 520)">
      <rect width="448" height="145" rx="6" fill="#1e1b2e" stroke="#e11d48" stroke-width="1" stroke-opacity="0.5"/>
      <text x="12" y="22" fill="#f43f5e" font-size="11" font-weight="bold">⚠️ Các vấn đề của giao diện cũ:</text>
      <text x="12" y="44" fill="#cbd5e1" font-size="10">1. Bố cục 1 cột kéo dài: Các ô nhập liệu bị bè ngang quá đà.</text>
      <text x="12" y="66" fill="#cbd5e1" font-size="10">2. Xếp Thumbnail cạnh Tiêu đề làm Thumbnail teo nhỏ, dễ lỗi.</text>
      <text x="12" y="88" fill="#cbd5e1" font-size="10">3. Thứ tự lộn xộn: Bình luận ghim chen trước COPPA; Thẻ bị đẩy sang Tab 2.</text>
      <text x="12" y="110" fill="#cbd5e1" font-size="10">4. Không có Card Preview Video &amp; Link YouTube như YouTube Studio thật.</text>
      <text x="12" y="130" fill="#fca5a5" font-size="10" font-weight="bold">➜ Trải nghiệm người dùng bị bí, thiếu tính chuyên nghiệp.</text>
    </g>
  </g>

  <!-- ================= BÊN PHẢI: ĐỀ XUẤT MỚI (CHUẨN YOUTUBE) ================= -->
  <g transform="translate(540, 85)">
    <!-- Panel Background -->
    <rect width="630" height="680" rx="12" fill="#0a0f1d" stroke="#3b82f6" stroke-width="1.5"/>
    
    <!-- Badge -->
    <rect x="18" y="16" width="200" height="24" rx="6" fill="#10b981" fill-opacity="0.2" stroke="#10b981" stroke-width="1"/>
    <text x="26" y="32" fill="#34d399" font-size="11" font-weight="bold">✓ ĐỀ XUẤT MỚI: 2 CỘT CHUẨN GOOGLE</text>

    <!-- Header info -->
    <text x="18" y="65" fill="#f8fafc" font-size="14" font-weight="bold">Thiên Sư: Huyền Phù Trấn Quỷ - Tập 1</text>
    <text x="18" y="82" fill="#94a3b8" font-size="10">Bố cục chuẩn YouTube Studio: Cột nhập liệu 62% + Cột Video Card 38%</text>

    <!-- Stepper Tabs -->
    <g transform="translate(18, 96)">
      <rect width="594" height="30" rx="6" fill="#0f172a" stroke="#1e293b" stroke-width="1"/>
      <!-- Step 1 Active -->
      <rect x="2" y="2" width="190" height="26" rx="4" fill="#1e293b" stroke="#3b82f6" stroke-width="1"/>
      <text x="16" y="19" fill="#38bdf8" font-size="10" font-weight="bold">1. Chi tiết video</text>
      <text x="220" y="19" fill="#64748b" font-size="10">2. Tối ưu &amp; Bản quyền</text>
      <text x="420" y="19" fill="#64748b" font-size="10">3. Chế độ hiển thị</text>
    </g>

    <!-- 2 COLUMNS CONTAINER -->
    <g transform="translate(18, 138)">
      <!-- CỘT TRÁI (360px): CÁC Ô NHẬP LIỆU GỌN GÀNG -->
      <g>
        <!-- 1. Tiêu đề (Full width cột trái, gọn gàng) -->
        <rect width="360" height="52" rx="6" fill="#090d16" stroke="#3b82f6" stroke-width="1.5"/>
        <text x="10" y="16" fill="#38bdf8" font-size="9" font-weight="bold">Tiêu đề (bắt buộc) - 48/100</text>
        <text x="10" y="36" fill="#f8fafc" font-size="11" font-weight="bold">Suelta lo que no puedes: controlar y la ansiedad</text>

        <!-- 2. Phần mô tả -->
        <rect y="60" width="360" height="110" rx="6" fill="#090d16" stroke="#334155" stroke-width="1"/>
        <text x="10" y="76" fill="#94a3b8" font-size="9" font-weight="bold">Phần mô tả - 796/5000</text>
        <text x="10" y="96" fill="#cbd5e1" font-size="10">Gastamos nuestra vida intentando retener el viento con las...</text>
        <text x="10" y="112" fill="#cbd5e1" font-size="10">manos, sufriendo por eventos que jamás podremos dominar...</text>
        <rect x="10" y="135" width="80" height="20" rx="4" fill="#1e293b"/>
        <text x="16" y="149" fill="#38bdf8" font-size="9">+ Link tập dài</text>
        <rect x="98" y="135" width="75" height="20" rx="4" fill="#1e293b"/>
        <text x="105" y="149" fill="#38bdf8" font-size="9">+ Mốc 00:00</text>

        <!-- 3. Hình thu nhỏ (Thumbnail tách riêng chuẩn YouTube) -->
        <g transform="translate(0, 180)">
          <text x="0" y="14" fill="#f8fafc" font-size="10" font-weight="bold">Hình thu nhỏ (Thumbnail 16:9)</text>
          <text x="0" y="28" fill="#64748b" font-size="9">Chọn ảnh bìa bắt mắt để tăng tỷ lệ nhấp chuột (CTR)</text>
          <rect y="36" width="120" height="68" rx="6" fill="#1e293b" stroke="#10b981" stroke-width="1.5"/>
          <text x="24" y="74" fill="#34d399" font-size="10" font-weight="bold">✓ Ảnh Chuẩn</text>
          <rect x="130" y="36" width="105" height="68" rx="6" fill="#090d16" stroke="#334155" stroke-width="1" stroke-dasharray="3,3"/>
          <text x="148" y="74" fill="#94a3b8" font-size="10">📁 Đổi ảnh...</text>
          <rect x="245" y="36" width="105" height="68" rx="6" fill="#090d16" stroke="#334155" stroke-width="1"/>
          <text x="260" y="74" fill="#eab308" font-size="10">✨ AI Tạo bìa</text>
        </g>

        <!-- 4. Danh sách phát -->
        <g transform="translate(0, 296)">
          <text x="0" y="14" fill="#f8fafc" font-size="10" font-weight="bold">Danh sách phát (Playlists)</text>
          <rect y="22" width="360" height="36" rx="6" fill="#090d16" stroke="#334155" stroke-width="1"/>
          <text x="10" y="45" fill="#e2e8f0" font-size="10">🔥 Thiên Sư: Huyền Phù Trấn Quỷ (Trọn bộ)</text>
        </g>

        <!-- 5. Đối tượng người xem -->
        <g transform="translate(0, 366)">
          <text x="0" y="14" fill="#f8fafc" font-size="10" font-weight="bold">Đối tượng người xem (COPPA)</text>
          <rect y="22" width="360" height="44" rx="6" fill="#090d16" stroke="#334155" stroke-width="1"/>
          <circle cx="20" cy="44" r="5" fill="#ef4444"/>
          <text x="34" y="48" fill="#f8fafc" font-size="10" font-weight="bold">Không, đây không phải nội dung cho trẻ em</text>
        </g>

        <!-- Nút HIỆN THÊM (Show More) -->
        <g transform="translate(0, 442)">
          <rect width="360" height="28" rx="4" fill="#1e293b" stroke="#475569" stroke-width="1"/>
          <text x="180" y="18" fill="#38bdf8" font-size="10" font-weight="bold" text-anchor="middle">HIỆN THÊM (Thẻ Tags 0/500, Nội dung AI, Ngôn ngữ, Ghim) ▼</text>
        </g>
      </g>

      <!-- CỘT PHẢI (220px): VIDEO PREVIEW CARD CHUẨN GOOGLE YOUTUBE -->
      <g transform="translate(374, 0)">
        <rect width="220" height="470" rx="8" fill="#0f172a" stroke="#1e293b" stroke-width="1"/>
        
        <!-- Video Preview 16:9 Screen -->
        <rect x="10" y="10" width="200" height="112" rx="6" fill="#020617" stroke="#334155" stroke-width="1"/>
        <polygon points="100,56 100,76 118,66" fill="#ef4444"/>
        <rect x="145" y="98" width="60" height="18" rx="3" fill="#000000" fill-opacity="0.8"/>
        <text x="150" y="111" fill="#ffffff" font-size="9" font-weight="bold">10:45 HD</text>

        <!-- Video Info -->
        <g transform="translate(12, 134)">
          <text x="0" y="14" fill="#64748b" font-size="9">Đường liên kết của video:</text>
          <text x="0" y="30" fill="#38bdf8" font-size="10" font-weight="bold">https://youtu.be/kX82v... 📋</text>

          <text x="0" y="56" fill="#64748b" font-size="9">Tên tệp:</text>
          <text x="0" y="72" fill="#f8fafc" font-size="10">episode_final.mp4</text>

          <text x="0" y="98" fill="#64748b" font-size="9">Chất lượng:</text>
          <text x="0" y="114" fill="#10b981" font-size="10" font-weight="bold">✓ 1080p HD (60fps)</text>

          <!-- Divider -->
          <line x1="0" y1="130" x2="196" y2="130" stroke="#1e293b" stroke-width="1"/>

          <!-- Kênh YouTube Đăng Bài Card -->
          <text x="0" y="150" fill="#64748b" font-size="9">Kênh đăng bài:</text>
          <rect y="158" width="196" height="46" rx="6" fill="#1e293b" stroke="#334155" stroke-width="1"/>
          <circle cx="24" cy="181" r="12" fill="#ef4444"/>
          <text x="18" y="185" fill="#ffffff" font-size="11" font-weight="bold">S</text>
          <text x="44" y="176" fill="#f8fafc" font-size="10" font-weight="bold">Stoic Sovereign</text>
          <text x="44" y="192" fill="#94a3b8" font-size="9">69 người đăng ký</text>

          <!-- Playlist tóm tắt -->
          <text x="0" y="226" fill="#64748b" font-size="9">Danh sách phát:</text>
          <text x="0" y="242" fill="#fde047" font-size="10">Thiên Sư Tập 1</text>

          <!-- Shorts Link -->
          <text x="0" y="268" fill="#64748b" font-size="9">Kèm YouTube Shorts:</text>
          <text x="0" y="284" fill="#ec4899" font-size="10" font-weight="bold">✓ 9:16 Sẵn sàng (45s)</text>
        </g>
      </g>
    </g>

    <!-- FOOTER MỚI -->
    <g transform="translate(18, 630)">
      <rect width="594" height="36" rx="6" fill="#0f172a" stroke="#1e293b" stroke-width="1"/>
      <text x="16" y="22" fill="#10b981" font-size="10">✓ Đã tự động lưu bản nháp</text>
      <rect x="310" y="5" width="120" height="26" rx="4" fill="#1e293b" stroke="#475569" stroke-width="1"/>
      <text x="370" y="22" fill="#cbd5e1" font-size="10" text-anchor="middle">Lưu Cấu Hình</text>
      <rect x="440" y="5" width="145" height="26" rx="4" fill="url(#btnRed)"/>
      <text x="512" y="22" fill="#ffffff" font-size="10" font-weight="bold" text-anchor="middle">🚀 Đăng Lên YouTube</text>
    </g>
  </g>
</svg>"""

out = Path(r"C:\Users\thean\.gemini\antigravity\brain\546909c0-dc2e-4f1c-bb37-21aa33365ca1\comparison_mockup.svg")
out.write_text(svg_content, encoding="utf-8")
print("WROTE_SVG_SUCCESS:", out.is_file(), out.stat().st_size)
