# F2 — KEN BURNS & PUNCH-IN (chuyển động nhân tạo trên khung hình)

> **Vị trí:** hai kỹ thuật "tạo chuyển động khi không có chuyển động": Ken Burns cho ẢNH
> TĨNH, punch-in cho điểm nhấn. File NHỎ NHẤT bộ foundation — và sau quyết định video-first
> ([[video-first-routing]], F5 Lớp 1) vai trò của nó CÀNG hẹp: ảnh giờ là ngoại lệ hiếm.
> Không có nguyên văn user riêng — chưng cất từ FOUNDATION.md cũ (§9, §4.1, §2.1 ngoại lệ
> thực thể). **Trạng thái phần 3: DỰ KIẾN 🔸 — ưu tiên THẤP có chủ đích.**

> **📌 LỆCH SO VỚI BẢN GỐC** (luật ghi-lệch user chốt 2026-07-10: thực tế đã khác phần
> dưới thì ghi tại đây, KHÔNG xóa bản gốc):
> - **Ken Burns v1 ĐÃ ĐÓNG 2026-07-09** — zoom chốt **cover→120–130%** (bản gốc dự kiến
>   105→115%); keyframe `uniform_scale` pycapcut RENDER ĐÚNG trong CapCut (nỗi lo "chưa
>   kiểm API" ở §3 đã giải), cổng mắt đạt. Xem memory `ken-burns-scale-keyframe`.
>   "Hiện trạng code" §3 bên dưới là ảnh chụp TRƯỚC 07/09 — nay ảnh đã Ken Burns,
>   pipeline đã dùng keyframe scale (f2) lẫn volume (F8).
> - **Punch-in: C đợt 4 mở 2026-07-10** (`MO_TA_VAN_HANH_C_DOT_4.md`) — KHÔNG code ngay,
>   mở màn bằng **PB14 đo 4 draft editor** đúng tinh thần §5. Số đo: punch kiểu "nhấn
>   từ khóa 10–20%" KHÔNG thấy; chỉ 5–7 cú zoom/104 phút, mức to x1.3–1.9, tại khoảnh
>   khắc drama đặc biệt — kết quả + verdict: NHAT_KY §C-DOT-4-PB14.

---

## 1. Là gì

- **Ken Burns:** pan/zoom chậm trên ảnh tĩnh — luật gốc: **"ảnh không bao giờ được đứng
  yên hoàn toàn"**. Chuẩn mực thể loại commentary: ảnh báo chí thật + Ken Burns; một ảnh
  đắt giữ trọn 5–6s là bình thường (khán giả cần thời gian đọc chi tiết ảnh trong lúc
  nghe voice).
- **Punch-in:** phóng khung đột ngột 10–20% ngay một nhịp — nhấn mạnh từ khóa, hoặc "đổi
  khung" khi một shot phải đứng lâu mà không có footage mới. Khác Ken Burns: punch-in là
  CÚ nhấn rời rạc (theo nhịp), Ken Burns là TRÔI liên tục (theo thời lượng ảnh).

## 2. Yếu tố ảnh hưởng

| Yếu tố | Ảnh hưởng thế nào |
|---|---|
| **Loại asset của beat** | Ken Burns CHỈ cho ảnh (route entity). Video có chuyển động thật — Ken Burns lên video là thừa. |
| **Sau F5 video-first** | Ảnh chỉ còn ở 3 ca entity hẹp (người/sự kiện/hiện vật) → số beat cần Ken Burns/video RẤT ít; nhiều video = 0. |
| **Nội dung ảnh** | Pan/zoom phải HƯỚNG VỀ chủ thể (mặt người, chi tiết đắt), không trôi vô hướng; ảnh tư liệu đông chi tiết cần zoom chậm hơn. |
| **Điểm nhấn thoại** | Punch-in bám từ khóa (như overlay bám anchor_word); không có lý do nội dung thì không punch. |
| **Mood/tone** | Zoom chậm = trầm/trang nghiêm; punch nhanh = năng lượng — cùng hệ tín hiệu với [[b1-mood-tone]]/[[b3-pattern-interrupt]]. |

## 3. Cách làm THỰC TẾ ở project này — 🔸 DỰ KIẾN

### Hiện trạng code

- **Ảnh đặt TĨNH nguyên ô** trong assembler (`_place_video_l1`: photo → giữ nguyên cả ô;
  comment chừa sẵn "Ken Burns là Phase 1"). Sàn phân giải 1280px (F5 Lớp 2) đảm bảo ảnh
  nào vào được draft cũng đủ nét để zoom nhẹ mà không vỡ (trần phóng ~120%).
- **Punch-in chưa có** dưới mọi dạng; các cú nhấn hiện do overlay+SFX đảm nhiệm.
- pycapcut: pipeline đã dùng keyframe? — CHƯA (volume/scale đều chưa keyframe). Làm Ken
  Burns/punch-in = mở vùng keyframe transform trong pycapcut → cần kiểm API + luật C1–C5
  trước (CỔNG DUYỆT VẬN HÀNH khi làm).

### Hướng dự kiến 🔸 (ưu tiên THẤP — có chủ đích)

1. **Ken Burns v1 — CHỈ cho ảnh entity, khi gặp video thật có beat entity:** zoom chậm
   một chiều (~105→115%) hướng về chủ thể; mặc định zoom-in về tâm; NÃO chỉ quyết
   HƯỚNG (về đâu) nếu cần — phần HÌNH là code thuần như style map của overlay.
   Trước lúc đó: ảnh tĩnh + overlay đang chấp nhận được, KHÔNG chặn pipeline.
2. **Punch-in — để SAU Ken Burns**, vì (i) overlay+SFX đã phủ nhu cầu nhấn; (ii) đụng
   video đang chạy (keyframe giữa clip) rủi ro hơn ảnh; (iii) chưa có số DNA nào nói
   niche cần. Mở khi cổng mắt/DNA đòi.
3. **Không nhét vào phễu:** f2 là chuyện assemble (asset đã chọn xong) — không phải tiêu
   chí chấm footage, không thêm gì vào c5.

### 3b. PHÂN RÃ NĂNG LỰC

> Loại: **(a)** đã có sẵn · **(b)** cần code mới ỐNG · **(c)** NÃO quyết lúc chạy · **(d)** cần dữ liệu DNA (Phase B)

| Luật ngôn-ngữ-editor | Hệ thống chạy thế nào | Loại | Trạng thái |
|---|---|---|---|
| Ảnh đủ nét để zoom không vỡ | sàn phân giải 1280px (F5 Lớp 2) | (a) | ✅ đã có |
| Ảnh đứng trọn ô hợp lệ (ảnh đắt 5–6s bình thường) | assembler photo phủ nguyên ô | (a) | ✅ đã có (dạng tĩnh) |
| **Ken Burns trên ảnh entity** | keyframe transform pycapcut — kiểm API + C1–C5, mô tả vận hành riêng khi làm | (b) | ✅ ĐÓNG 2026-07-09 (v1 zoom về tâm, cover→120–130%) |
| Hướng zoom về chủ thể | NÃO quyết hướng (nếu cần), code lo hình — theo khuôn "NÃO nghĩa, code hình" của overlay | (c)+(b) | ⏸ v1 zoom về TÂM; hướng-chủ-thể chưa làm |
| Punch-in nhấn từ khóa | keyframe giữa clip, bám anchor_word | (b treo) | ✅ ĐÓNG 2026-07-10 dạng KHÔNG-CODE (user duyệt PB14: editor không punch theo từ khóa; 1–2 cú zoom-drama/video để editor thêm tay — NHAT_KY §C-DOT-4-PB14) |
| Niche có dùng punch-in/Ken Burns không, mức zoom | đo từ video viral | (d) | 🔄 PB14 2026-07-10 đo từ 4 DRAFT EDITOR (thay video viral) — xem block LỆCH đầu file |

**→ Backlog code rút ra: KHÔNG mở mục nào đợt này.** Cả hai (b) đều treo chờ nhu cầu thật
— f2 tồn tại để khi nhu cầu đến thì làm ĐÚNG cách (zoom hướng chủ thể, cổng duyệt vận
hành), không phải để làm NGAY.

## 4. Cạm bẫy / ranh giới

- **Ken Burns lên video** — video có chuyển động thật; chồng zoom nhân tạo = say sóng.
  Chỉ ảnh.
- **Zoom vô hướng / zoom ra khỏi chủ thể** — chuyển động phải dẫn mắt VỀ cái đáng nhìn;
  zoom ngẫu nhiên còn tệ hơn ảnh tĩnh.
- **Punch-in rắc đều như hiệu ứng trang trí** — cùng bệnh với lạm transition (d3) và nhồi
  SFX (e1): không bám nội dung thì là nhiễu.
- **Phóng quá trần** — ảnh 1280px phóng >~120% bắt đầu vỡ; mức zoom phải tính từ phân
  giải thật của ảnh, không cố định mù.
- **Làm sớm vì "dễ thấy"** — sau video-first, số beat hưởng lợi rất nhỏ; công sức nên đổ
  vào phễu/DNA trước. Ưu tiên thấp của f2 là QUYẾT ĐỊNH, không phải bỏ sót.

## 5. Học gì từ DNA niche (Phase B)

| Tín hiệu | Dùng để |
|---|---|
| Video viral niche xử lý ảnh tĩnh thế nào (tĩnh hẳn? Ken Burns? tốc độ?) | quyết mở gói Ken Burns + tham số zoom |
| Có punch-in không, ở đâu (từ khóa? beat drop nhạc?) | quyết mở punch-in + luật vị trí |
| Thời lượng ảnh đứng được trước khi khán giả chán (theo niche) | trần thời lượng beat entity |
