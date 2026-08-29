# C5 — LỌC & XẾP HẠNG FOOTAGE — TRỌNG TÀI PHỄU

> **Vị trí:** trọng tài DUY NHẤT của việc chọn footage. Mọi foundation khác ([[c2-an-du-veto]]
> nghĩa · [[b1-mood-tone]] mood/C2b · [[c7-shot-variety]] cỡ cảnh/góc · [[d1-pacing]] độ dài ·
> [[c6-footage-chu-ky]] chữ ký) chỉ ĐÓNG GÓP luật + trọng số vào phễu — **không foundation nào
> được tự quyền loại footage**.
> **Trạng thái phần 3: DỰ KIẾN 🔸. User duyệt file này = ĐÓNG BĂNG 4 nguyên tắc phễu.**
> Xuất phát từ mối lo của user (nguyên văn `GHI_CHEP_GOC.md §8`): *"khi có quá nhiều luật...
> các bước sau sẽ loại đi các footage quan trọng, luật của các foundation lệch nhau làm loại
> nhiều footage... bước nào loại mất nhiều footage chúng ta có thể cân nhắc loại bỏ."*

---

## 1. Là gì

Phễu = giai đoạn biến **danh sách ứng viên footage** (từ tìm kiếm) thành **1 lựa chọn cho mỗi
beat**. Khi hệ thống có ~17 foundation, nhiều luật cùng soi một footage; nếu mỗi luật tự quyền
loại thì lọc chồng lọc → mất footage quan trọng hoặc rỗng tay. Vì vậy cần MỘT trọng tài với
luật chơi thống nhất: **loại thì hiếm, chấm điểm là chính, không bao giờ về rỗng, và mọi cú
loại đều để lại dấu vết để truy xét.**

## 2. Yếu tố ảnh hưởng — các luật cắm vào phễu

| Luật | Nguồn foundation | Bản chất trong phễu |
|---|---|---|
| Sai nghĩa nghiêm trọng (footage về chủ đề khác hẳn) | [[c2-an-du-veto]] | **VETO CỨNG** |
| Hỏng kỹ thuật: watermark/bản quyền hãng, tải lỗi | kỹ thuật | **VETO CỨNG** (đã có trong code) |
| Khớp concept/nghĩa của beat (mức độ) | [[c2-an-du-veto]] | điểm, trọng số cao nhất |
| Khớp mood/màu/tông đoạn (C2b) | [[b1-mood-tone]] | điểm, trừ RẤT nặng khi lệch |
| Đổi cỡ cảnh hoặc góc ≥30° so shot liền trước | [[c7-shot-variety]] | điểm — xét theo CHUỖI (cần shot #n−1) |
| Clip đủ dài so với cửa sổ beat (≥1.2×) | [[d1-pacing]] | điểm (heuristic đã có) |
| Chống lặp footage đã dùng gần đây (P7) | kỹ thuật/đa dạng | điểm phạt mềm (đã có) |
| Footage chữ ký niche | [[c6-footage-chu-ky]] | điểm cộng (bonus) |

## 3. Cách làm THỰC TẾ ở project này — 🔸 DỰ KIẾN, chờ user duyệt

### BỐN NGUYÊN TẮC PHỄU (duyệt file này = đóng băng)

1. **Chỉ 2 veto cứng** — sai nghĩa nghiêm trọng + hỏng kỹ thuật/watermark. **Mọi luật khác là
   ĐIỂM có trọng số**, chọn footage tổng điểm cao nhất. Sai mood bị trừ rất nặng → khi pool
   còn ứng viên khá, footage lệch mood không bao giờ thắng; nhưng khi cả pool xoàng vẫn chọn
   được cái đỡ-tệ-nhất + cờ `needs_human`, thay vì rỗng.
2. **Sàn ứng viên = 3** — không bước chấm/lọc nào được kéo pool xuống dưới sàn; luật nào định
   loại mà phá sàn thì tự hạ cấp thành trừ điểm cho lần đó + ghi log. Pool nghèo từ khâu tìm
   → thang fallback sẵn có (specific → broad → thematic → `needs_human`), pipeline không bao
   giờ chết.
3. **Đếm xác chết theo luật** — mỗi cú loại/trừ nặng ghi `(footage, luật, lý do)` vào
   project.json (NT5); report tổng hợp bảng **"luật nào giết bao nhiêu % ứng viên"**. Việc
   cắt/nới một luật do USER quyết dựa trên số liệu này sau vài video thật — không đoán trước.
4. **Thứ tự ưu tiên khi luật vênh nhau: NGHĨA > MOOD > NHỊP/VARIETY > ĐẸP/CHỮ KÝ.** Trọng số
   cụ thể là dự kiến 🔸, tinh ở Level 2 + DNA niche.

### Kiến trúc phễu 5 bước (chạy cho từng beat, THEO THỨ TỰ beat vì variety cần shot liền trước)

1. **THU:** gom ứng viên qua thang fallback hiện có (local niche → Pexels 3 tier → entity).
2. **VETO CỨNG (2 cửa):** watermark/hỏng (code, đã có) · sai nghĩa nghiêm trọng (NÃO xét).
3. **CHẤM đa chiều — RẺ TRƯỚC, ĐẮT SAU** (để không nổ chi phí):
   - *Lớp rẻ (code thuần):* độ dài clip vs beat · phạt lặp P7 · histogram màu so nội bộ đoạn
     (C2b lớp rẻ) · metadata.
   - *Lớp NÃO (text):* khớp concept beat theo mô tả/title ứng viên.
   - *Lớp đắt (vision GLM-4V):* CHỈ gọi cho nhóm dẫn đầu sau 2 lớp trên, và chỉ ở beat
     mood-nhạy-cảm / beat quan trọng — không quét đại trà.
4. **SÀN + CHỌN:** áp sàn 3; chọn tổng điểm cao nhất; cả pool dưới ngưỡng chất lượng → chọn
   đỡ-tệ-nhất + cờ `needs_human`.
5. **GHI:** lựa chọn + 3 alternates (đã có) + kill-log từng luật → report.

### Bảng trọng số DỰ KIẾN 🔸 (con số chỉ là điểm xuất phát để tinh, KHÔNG phải luật)

| Chiều điểm | Trọng số khởi điểm |
|---|---|
| Khớp nghĩa/concept beat | ×3.0 |
| Khớp mood/màu đoạn (C2b) | ×2.5 (lệch nặng = trừ sập sàn) |
| Shot variety vs shot liền trước | ×1.5 |
| Độ dài clip đủ cửa sổ | ×1.5 |
| Chống lặp P7 | ×1.0 (phạt) |
| Chữ ký niche | ×1.0 (bonus) |

### 3b. PHÂN RÃ NĂNG LỰC

> Loại: **(a)** đã có sẵn · **(b)** cần code mới ỐNG · **(c)** NÃO quyết lúc chạy · **(d)** cần dữ liệu DNA (Phase B)

| Thành phần phễu | Hệ thống chạy thế nào | Loại | Trạng thái |
|---|---|---|---|
| Thu ứng viên + thang fallback + needs_human | `sourcer/runner.py` | (a) | ✅ đã có |
| Veto cứng watermark/bản quyền | `sourcer/entity.py` ("loại tuyệt đối") | (a) | ✅ đã có |
| Các heuristic cũ: local thắng · relevance · clip ≥1.2× · phạt lặp P7 · lưu 3 alternates | trở thành CHIỀU ĐIỂM trong phễu mới — không vứt | (a) | ✅ đã có, cần bọc lại thành điểm |
| **Khung phễu core:** veto 2 cửa + chấm trọng số + sàn 3 + kill-log | code mới đặt vào `ranker/` (package đang RỖNG — kiến trúc đã chừa chỗ: "vision rank là Phase 1") | **(b)** | ❌ **tính năng chính của c5** |
| Veto sai nghĩa + chấm khớp concept | NÃO xét mô tả ứng viên vs concept beat | (c) | ❌ chưa có — hiện "tin query", chưa ai kiểm lại kết quả tìm |
| Chấm mood: histogram nội bộ đoạn → vision chọn lọc | backlog 2+3 của [[b1-mood-tone]] | (b)+(d) | ❌ cắm vào phễu khi làm |
| Chấm variety theo chuỗi | cần tag cỡ cảnh/góc của ứng viên: stock không có sẵn → NÃO đoán từ mô tả/frame; footage DNA có tag từ Phase B | (b)+(d) | ❌ sau — phụ thuộc tag |
| Report kill-count theo luật | render bảng trong report.html từ kill-log | (b) | ❌ code nhỏ, đi cùng khung phễu |
| Trọng số/ngưỡng theo niche | hồ sơ DNA | (d) | ❌ Phase B |

**→ Backlog code rút ra (chờ user duyệt mô tả vận hành từng cái trước khi code):**
1. **Khung phễu core trong `ranker/`** — veto 2 cửa, chấm trọng số (bọc heuristic cũ thành
   chiều điểm), sàn 3, kill-log, cờ needs_human. Các "đầu chấm" (nghĩa/mood/variety) cắm dần
   sau, khung chạy được ngay với các chiều rẻ.
2. **Đầu chấm nghĩa (NÃO)** — kiểm ứng viên vs concept beat (hiện tin query mù).
3. **Report kill-count** — bảng "% chết theo luật" (đi cùng khung, code nhỏ).

## 4. Cạm bẫy / ranh giới

- **Veto-hóa luật mới:** foundation viết sau (c7, c6, F...) tuyệt đối không thêm veto cứng
  thứ 3 — mọi luật mới vào phễu dưới dạng điểm. Muốn nâng thành veto phải sửa file này + user duyệt.
- **Phễu đắt:** gọi vision cho mọi ứng viên = nổ chi phí (PRD §9.1 đã cảnh báo token). Kỷ
  luật rẻ-trước-đắt-sau: ứng viên chết vì luật rẻ thì không bao giờ tốn call vision.
- **Chết âm thầm:** mọi đường thất bại phải ra `needs_human` + ghi lý do — không bao giờ
  crash, không bao giờ lặng lẽ bỏ trống beat.
- **Tôn thờ trọng số:** bảng trọng số là điểm xuất phát; chỉnh bằng kill-log + phản hồi editor
  (Level 2) + DNA — đừng code cứng rồi quên.
- **Variety phá song song:** vì cần shot #n−1, phễu chạy tuần tự theo beat — đừng tối ưu chạy
  song song các beat mà làm luật chuỗi mù.

## 5. Học gì từ DNA niche (Phase B)

| Tín hiệu | Dùng để |
|---|---|
| Niche nhạy chiều nào (mood-driven như chill travel? variety-driven như cooking?) | tinh trọng số theo niche |
| Ngưỡng lệch màu chấp nhận được của niche | ngưỡng histogram C2b |
| Độ giàu footage của niche (dễ/khó tìm) | đặt sàn pool + độ sâu fallback hợp lý |
| Tỉ lệ kill bình thường của từng luật | mốc so sánh cho bảng kill-count (biết luật nào "quá tay" so với chuẩn) |
