# MÔ TẢ VẬN HÀNH — C ĐỢT 4: C2 PUNCH-IN (chờ user duyệt trước khi code)

> Viết 2026-07-10. Nguồn luật: `foundation/f2-ken-burns-punch-in.md` §1/§3/§4 +
> DINH_HUONG_VIEC_TIEP_THEO.md dòng C2. Cổng cuối: **MẮT** (1 video kiểm — nhạc editor
> mới nạp đi ké cổng TAI cùng video này, xem NHAT_KY §NẠP-KHO-0710).

---

## 0. Punch-in là gì (f2 §1)

Phóng khung **đột ngột 10–20% ngay một nhịp** rồi GIỮ — nhấn từ khóa thoại, hoặc "đổi
khung" khi một shot đứng lâu không có footage mới. Khác Ken Burns (trôi chậm liên tục,
CHỈ ảnh — đã đóng): punch-in là CÚ rời rạc, đánh trên **VIDEO đang chạy**.

## 1. M0 — PB14: ĐO EDITOR TRƯỚC, chưa viết luật đặt (bài học PB12)

**Vì sao bắt buộc:** whoosh auto từng chết vì suy diễn "bám cut" — PB12 đo thật ra 0/88.
Foundation f2 §5 cũng ghi rõ: "có punch-in không, ở đâu" là câu hỏi **Phase B chưa đo**.
Hiện KHÔNG có số nào chứng minh editor space dùng punch-in. Nên đợt 4 mở màn bằng đo,
không phải code.

**Đo gì (4 draft SP1-001/003/004/012 có sẵn):** quét `draft_content.json` track video —
segment nào có **keyframe scale GIỮA clip** (loại keyframe mép = Ken Burns/fade):
- Có bao nhiêu cú / video? (0 = punch-in KHÔNG PHẢI ngôn ngữ editor niche này → **DỪNG
  đợt 4 phần code, chỉ ghi kết luận** — giống số phận whoosh auto)
- Mức zoom (10–20%? hơn?), tốc độ cú (ramp mấy frame?), giữ đến hết clip hay thả về?
- **Vị trí tương quan với cái gì:** text overlay hiện lên? từ khóa thoại (nghe voice quanh
  mốc)? shot đứng quá lâu (đổi khung)? — đo trực tiếp từng giả thuyết như PB12.

**Sản phẩm M0:** bảng số + verdict "có/không + luật đặt rút từ số đo". Script đo giữ
trong repo (khuôn `scripts_phan_tich_pb13`). **User duyệt verdict rồi mới sang M1.**

## 2. M1 — luật đặt + code (CHỈ khi PB14 nói "có")

Thiết kế dưới đây là KHUNG dự kiến — tham số cuối lấy từ số đo PB14, không bịa:

- **Mốc punch = anchor_word có sẵn của overlay** (NÃO đã quyết nghĩa khi direct — KHÔNG
  thêm field LLM mới, không đẻ tầng quyết định mới; NT4 timestamp từ alignment). Nếu PB14
  ra "bám text hiện lên" thì càng khớp — overlay chính là text hiện lên của máy.
- **Lọc mốc:** chỉ beat VIDEO (ảnh đã có Ken Burns — chồng 2 zoom là say sóng, f2 §4) ·
  clip phải còn đứng đủ lâu sau mốc (≥~2s, số chốt theo PB14) · trần/video + giãn cách
  tối thiểu (chống "rắc đều như trang trí" — f2 §4; con số theo PB14) · KHÔNG punch trong
  shot thở (ô thở là nghỉ, không có thoại để nhấn) · viral clip: theo số PB14, nghiêng
  về KHÔNG (clip có chủ đích sẵn).
- **Hình cú punch:** keyframe `uniform_scale` (đường đã verify render đúng ở Ken Burns):
  giữ 1.0 tới sát mốc → ramp nhanh lên 1.10–1.20 (tốc độ theo PB14) → GIỮ tới hết clip.
  Zoom về tâm; mức zoom deterministic crc32 theo tên clip (cùng khuôn Ken Burns/seed
  shot thở — dựng lại ra đúng số).
- **⚠ BẪY TIME_OFFSET THEO NGUỒN (lý do cổng mắt đợt này phải soi kỹ):** keyframe tính
  theo thời gian FILE NGUỒN. Video ngắn bị kéo **slow-mo (`speed<1`)** trong
  `_place_video_l1` → mốc trên timeline phải quy đổi `t_nguồn = t_trong_ô × speed`
  (video hiện luôn `source_start=0` nên chỉ nhân speed, chưa phải cộng offset — nhưng
  viết hàm quy đổi dùng chung + pytest riêng ca slow-mo). Ken Burns ảnh không dính vì
  ảnh luôn 1:1.
- Log `project.punch_log` + card report (giữ nếp drone/subject_sfx) để editor kiểm.

## 3. M2 — video kiểm (cổng MẮT + TAI ké)

Dựng 1 video kiểm: **MẮT** soi punch-in (đúng mốc? có say sóng? có bị nhồi khi trùng
overlay+SFX?) + **TAI ké** cho 17 bài nhạc editor mới vào pool (mood máy-map từ tên
tiếng Việt — nếu nhạc lệch chương, núm chỉnh là TÊN FILE `__mood`, không phải code).
Claude Code KHÔNG tự báo đạt — chờ user phán.

## 4. RÀ CHỒNG CHÉO (P5 — tầng nào cùng quản "cú nhấn tại từ khóa"?)

| Tầng hiện có | Đụng thế nào | Kết luận |
|---|---|---|
| **Overlay text + overlay-SFX** (bám anchor_word) | CÙNG MỐC với punch → 3 lớp nhấn chồng (bệnh e1/d3 "nhồi") | PB14 quyết: editor punch NGAY MỐC text hay tránh? Nếu đi cùng → punch là lớp phối hợp, trần chung; nếu không thấy pattern → không code |
| **Ken Burns ảnh** (keyframe scale mép clip) | Cùng cơ chế keyframe, khác nhánh asset | Tách tuyệt đối photo/video trong `_place_video_l1` — không chồng |
| **Slow-mo phủ ô** (`speed<1`) | Đổi hệ quy chiếu time_offset keyframe | Hàm quy đổi + pytest ca slow-mo (bẫy chính đợt này) |
| **V1 cover-scale ảnh** (`ClipSettings` tĩnh) | Bài học F8: keyframe + scale tĩnh không trộn | Video hiện `clip=None` — punch chỉ áp video nên không đụng; assert trong code |
| **Ducking F8 / volume keyframe** | Khác property (volume vs scale), khác track | Không đụng — chỉ chung bài học time_offset |
| **C3 so màu, phễu, cutter, pacing** | Punch không đổi pick/không đổi timeline | Không đụng gì (f2 §3: "không nhét vào phễu") |
| **Mood → mức zoom** (f2 §2: punch nhanh = năng lượng) | 2-tầng-cùng-quản nếu cho NÃO quyết số | Luật §6b: số KHÔNG in cho NÃO — code quyết theo luật cố định từ PB14 |

## 5. Trình tự + cổng

1. **M0 PB14** đo 4 draft → bảng số + verdict → **user duyệt** (có thể ra "KHÔNG làm").
2. **M1** code theo luật từ số đo → pytest FULL (≥1 test/luật + ca slow-mo).
3. **M2** video kiểm → cổng MẮT (+ TAI ké nhạc editor) → user phán → đóng đợt 4, commit,
   cập nhật NHAT_KY/memory/foundation f2 (phần 3 hết "DỰ KIẾN").
