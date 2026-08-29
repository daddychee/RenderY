# MÔ TẢ VẬN HÀNH — NHIỀU FOOTAGE / BEAT (thực thi shot_count)

> **Tài liệu CỔNG DUYỆT VẬN HÀNH** (2026-07-03). User đọc → duyệt → mới code.
> Nguồn: foundation **d1-pacing** (khe code lớn nhất: "cắt nhanh 0.5-1s/shot" hiện không
> xảy ra được) + **d2-hình-thở** (chuỗi nhiều footage/ô thở dùng CHUNG cơ chế chia-cửa-sổ).
> Tinh thần: [[filter-overload-guard]] — thêm năng lực nhưng KHÔNG đẻ thêm cửa loại; tái
> dùng phễu c5 + assembler đã đóng băng, chỉ CHIA nhỏ cửa sổ.

---

## 1. Vấn đề & phạm vi

**Hiện trạng:** `Beat.shot_count` được LLM đạo diễn quyết (pass 2: "1 thường, 2-3 khi beat
dài cần cắt") và lưu vào project.json, NHƯNG **không stage nào đọc**. Sourcer chọn đúng 1
clip/beat; assembler đặt 1 clip phủ trọn cửa sổ beat. → beat 6 giây luôn là MỘT hình giữ
6 giây, không thể cắt nhanh tạo năng lượng.

**Milestone này làm:** beat có `shot_count = N (>1)` → chọn **N clip video khác nhau**, cắt
NỐI TIẾP trong đúng cửa sổ beat đó (không tràn sang beat khác, không đổi tổng thời lượng).

**Chỉ áp cho route stock/local (đường phễu).** Route entity (ảnh), graphic (chart), beat có
info-card/chart-half → GIỮ 1 shot (N=1). Ảnh không "cắt nhanh"; các beat đặc biệt đã có layout
riêng.

## 2. Cách vận hành — 3 chỗ chạm

### A. Số N chốt thế nào (2 pha, không thêm call NÃO)

`shot_count` của LLM = **ý định**. Số CUỐI = ý định bị kẹp bởi 2 trần thực tế:

```
N = min( shot_count_LLM ,  floor(thời_lượng_beat / SÀN_MỖI_SHOT) ,  số_clip_tốt_trong_pool )
```

- **SÀN_MỖI_SHOT** (hằng, ~0.7s khởi điểm): mỗi shot con phải đủ dài để mắt kịp đọc — chặn
  cắt vụn 0.2s không xem được. Beat quá ngắn cho N shot → tự giảm N (không có shot nào dưới sàn).
- **số_clip_tốt_trong_pool**: pool chỉ có 2 clip hợp nghĩa thì N=2 dù LLM xin 3 — đây chính
  là "pha 2: kho footage quyết số cuối" của d1/d2, KHÔNG cần hỏi lại LLM.

→ N=1 khi beat ngắn / pool mỏng / LLM không xin cắt. Hành vi cũ giữ nguyên khi N=1.

### B. Sourcer chọn N clip — TÁI DÙNG phễu c5, KHÔNG call NÃO thêm

Phễu c5 hiện đã chấm & xếp hạng CẢ pool trong **1 call NÃO/beat** rồi trả `ranked` (danh sách
điểm giảm dần). Multi-shot chỉ việc **lấy top-N clip khác nhau** từ danh sách đã xếp đó thay vì
top-1:

- Đi từ đầu `ranked`, tải lần lượt; clip nào tải hỏng → bỏ, lấy clip kế (giữ nguyên luật 4.7).
- Lấy đủ N clip OK thì dừng. Cả N đều vào `used_in_video` (P7: không lặp ở beat sau).
- Variety c7 đã thưởng clip khác cỡ cảnh → top-N tự nhiên đa dạng góc/cỡ, không cần luật mới.

**→ Chi phí NÃO không đổi: vẫn đúng 1 call/beat.** Chỉ lấy nhiều clip hơn từ cùng kết quả.

### C. Assembler chia cửa sổ beat thành N khoảng con

Cửa sổ phủ của beat `[start, end]` (coverage.py) được **chia đều N khoảng con liền khít**,
mỗi clip phủ 1 khoảng:

- Ranh giới con làm tròn microsecond theo lối **cộng dồn** (đúng cách đã fix bug SegmentOverlap
  1µs [[assemble-segment-overlap-rounding]]): mép con sau = mép con trước, không hở/đè.
- Mỗi khoảng con dùng LẠI y nguyên logic đặt segment hiện có: clip ngắn hơn khoảng → slow-mo
  kéo cho đầy; ảnh giữ nguyên. Vì khoảng con NGẮN hơn cả beat → clip càng dễ đủ dài.
- Tổng N khoảng con = đúng cửa sổ beat cũ → **bất biến phủ kín timeline KHÔNG đổi** (không
  tràn beat, tổng thời lượng y hệt).

## 3. Data model (phẫu thuật tối thiểu — preserve-by-default)

`ShotPick` (1 bản ghi/beat) giữ NGUYÊN clip chính (shot 1) → mọi chỗ đọc `shot.asset_path`,
report, needs_human… chạy y cũ. Thêm 1 trường phụ:

```
ShotPick.extra_shots: list[ExtraShot] = []   # shot 2..N; rỗng = 1 shot như cũ
ExtraShot = { asset_path, asset_key, source, note }
```

Assembler: beat có `extra_shots` → chia N=1+len(extra) khoảng, đặt [clip chính, extra…] theo
thứ tự điểm. Không có → 1 khoảng như cũ. Report: cột footage ghi "3 shots" nếu N>1.

## 4. Cái gì KHÔNG làm milestone này (tránh phình)

| Để sau | Vì sao |
|---|---|
| Chuỗi nhiều footage cho Ô THỞ (d2) | tính năng riêng; DÙNG CHUNG cơ chế chia-cửa-sổ này, cắm sau |
| Khoảng con dài-ngắn KHÁC nhau (nhịp trong beat) | v1 chia ĐỀU; nhịp-trong-beat là nâng cấp sau |
| Chấm NÃO riêng cho từng shot con | v1: cả beat 1 concept, N clip cùng minh họa; đủ tốt |
| Pacing validator ("cắt đều tăm tắp") | backlog riêng của d1, milestone khác |

## 5. Xác định THÀNH CÔNG trước khi code (P4)

1. **pytest:** hàm chia cửa sổ N khoảng liền khít (không hở/đè, tổng = beat) — kể cả mốc lẻ;
   N tự kẹp theo sàn (beat ngắn) + theo pool (ít clip); N clip khác nhau + đều vào used_in_video;
   assembler đặt đúng N segment cho beat multi-shot; beat N=1 / entity / graphic KHÔNG đổi.
2. **Chạy thật video mẫu** (hook Ai Cập hoặc video có beat năng lượng cao): beat shot_count>1
   ra nhiều clip nối tiếp, draft mở được, tổng thời lượng không đổi.
3. **Cổng mắt:** user mở draft CapCut — đoạn liệt kê/năng lượng cắt nhanh nhiều shot, đoạn
   lắng vẫn giữ 1 hình; nhịp "dồn → thả" thấy được.

---

> **Chờ user duyệt tài liệu này.** Duyệt → code theo 3 chỗ chạm (A số N, B sourcer top-N,
> C assembler chia cửa sổ), pytest trước, rồi chạy thật + cổng mắt.
