# Master Production Asset Pack & 4-Angle Turnaround Sheet
## Hướng Dẫn Thiết Lập Bộ Tài Sản Sản Xuất & Bảng Xoay Nhân Vật 4 Góc

Tài liệu này chuẩn hóa quy trình tiền sản xuất (Pre-production Asset Phase) cho từng tập phim: Tạo trước **Bộ 3 Trụ Cột Tài Sản (Nhân Vật - Bối Cảnh - Đạo Cụ)** trước khi phân cảnh thành prompt 9 trường.

---

## 1. 🧍 Bảng Xoay Nhân Vật 4 Góc Quay (4-Angle Character Turnaround Sheet)

Để AI sinh video và ảnh không bị lệch mặt, đổi dáng hay biến dạng trang phục, mỗi nhân vật chính và phụ trong tập phim đều có một bức ảnh chuẩn **Character Model Sheet / Turnaround Sheet** ghép 4 góc quay:

### Cấu trúc 4 góc nhìn chuẩn:
1. **Front View (Góc chính diện):** Toàn thân thẳng góc, thấy rõ ngũ quan, tỷ lệ cơ thể, nốt ruồi/vết sẹo và mặt trước trang phục.
2. **Three-Quarter View (Góc nghiêng 3/4):** Thấy rõ độ nhô của sống mũi, gò má, cấu trúc xương hàm và phom dáng trang phục khi nhìn nghiêng.
3. **Side Profile View (Góc nhìn ngang 90 độ):** Khóa đường viền cằm, tai, kiểu tóc/búi tóc từ phía bên.
4. **Back View / Close-up Portrait (Góc sau lưng hoặc Cận cảnh chân dung):** Khóa kiểu dáng tóc từ phía sau lưng hoặc đặc tả chi tiết ánh mắt, bờ môi và nốt ruồi định danh.

### Mẫu Prompt Chuẩn Tạo Ảnh Turnaround Sheet 4 Góc:
```text
Full-body character turnaround sheet, cinematic character model sheet, 4 distinct camera views of the exact same character displayed horizontally side-by-side in a single cohesive image: front view, three-quarter perspective view, side profile view, and rear back view. 
Character description: [TÊN NHÂN VẬT]: [ĐỘ TUỔI], [GIỚI TÍNH], [CHIỀU CAO/THỂ HÌNH], [SẮC TỘC/MÀU DA KÈM UNDERTONE], [CẤU TRÚC GÒ MÁ/CẰM], [DÁNG MẮT/MÀU MẮT], [ĐIỂM NEO NHẬN DIỆN: nốt ruồi vị trí mm cụ thể hoặc vết sẹo], [KIỂU TÓC CỤ THỂ].
Wearing: [TRANG PHỤC ĐÓNG ĐINH CỦA HỒI: chi tiết áo, quần/váy, giày, thắt lưng, trang sức].
Pristine studio neutral medium-grey backdrop, uniform commercial studio lighting, naturalistic skin texture, razor-sharp focus, consistent anatomical scale, height and proportions across all 4 perspectives, 8k master photography. NO cartoon distortion, NO mismatched faces across angles.
```

---

## 2. 🏛️ Bảng Bối Cảnh Bất Biến (Master Location / Environment Sheet)

Mỗi tập phim chỉ diễn ra trong một số lượng bối cảnh giới hạn (thường từ 2–5 địa điểm chính). Mỗi địa điểm được quy định trước:
* **Tên bối cảnh (Location ID):** Ví dụ: `Soweto_Market_Aisle`, `Sandton_Penthouse_LivingRoom`, `Doctor_Secret_Clinic`.
* **Kiến trúc & Bố cục:** Kích thước không gian, vật liệu tường/sàn (gỗ gụ bóng, tường gạch bong tróc, sàn phẫu thuật trắng bóng).
* **Nguồn sáng & Palette màu:** Hướng ánh sáng chính (nắng chiều vàng ấm, ánh đèn bàn banker lamp cổ, đèn huỳnh quang y tế xanh lạnh), màu sắc chủ đạo.
* **Quy tắc vàng:** Trong trường `SETTING & START STATE:`, **TUYỆT ĐỐI CHỈ MÔ TẢ BỐI CẢNH VÀ VỊ TRÍ ĐỨNG/NGỒI**, không tả lại quần áo nhân vật để tránh xung đột với trường `CHARACTERS:`.

---

## 3. 📦 Bảng Đạo Cụ Then Chốt (Key Story Props Sheet)

Những vật dụng có tính dẫn dắt cốt truyện hoặc nhân vật tương tác trực tiếp:
* **Tên đạo cụ (Prop ID):** Ví dụ: `Cracked_Hand_Mirror`, `Forged_Will_Document`, `Silver_Zippo_Lighter`, `Lion_Head_Signet_Ring`.
* **Quy cách vật lý chi tiết:**
  * Kích thước (bỏ túi, cầm tay, khổ A4).
  * Chất liệu (bạc mờ, vàng chạm khắc, giấy ố vàng có dấu mộc đỏ, kính nứt hình mạng nhện viền đồng).
  * Trạng thái (mới toanh, cũ mòn, dính vết máu, sứt mẻ).
* **Quy tắc:** Khi nhân vật thực hiện hành động trong `TIMED ACTION:`, gọi đúng tên và quy cách của đạo cụ từ bảng này để đảm bảo đạo cụ không bị AI vẽ khác đi qua các cú cắt máy.

---

## 4. ⚙️ Quy Trình Gắn Tự Động Vào 9 Trường Của Mỗi Cảnh

Khi chia cảnh từ kịch bản phân đoạn:
1. **Trường `CHARACTERS:`** -> Tự động nạp chuỗi DNA vật lý đã khóa từ *Character Sheet*.
2. **Trường `SETTING & START STATE:`** -> Tự động nạp mô tả không gian, ánh sáng từ *Location Sheet*.
3. **Trường `TIMED ACTION:` & `END STATE:`** -> Gọi đúng tên và tương tác của đạo cụ từ *Prop Sheet*.
4. **Trường `CONSTRAINTS:`** -> Giữ nguyên câu lệnh nghiêm cấm biến đổi nhân vật, trang phục và đạo cụ giữa các cú cắt.
