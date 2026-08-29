# MÔ TẢ VẬN HÀNH — KHUNG PHỄU CHỌN FOOTAGE (c5)

> ⚡ **CẬP NHẬT 2026-07-07:** câu "NÃO gọi đúng 1 lần mỗi beat" đã NÂNG thành "đúng 1 lần
> mỗi CHUNK ~10 beat" (đo thật 65s/beat không scale) — xem `MO_TA_VAN_HANH_PHEU_BATCH.md`.
> Mọi luật lọc/xếp hạng bên dưới GIỮ NGUYÊN.

> **Tài liệu CỔNG DUYỆT VẬN HÀNH** (2026-07-03). User đọc → duyệt → mới code.
> Gom spec từ 7 foundation đã duyệt: c5 (khung) · c1 (nguồn) · c4 (query) · c2 (veto nghĩa)
> · c3 (ngữ cảnh chuỗi) · c7 (variety) · c6 (chữ ký) · b1 (mood).
> **Tinh thần xuyên suốt (2 lời dặn của user):** (1) [[filter-overload-guard]] — tách rõ
> LỌC (đúng 2 cửa) khỏi XẾP HẠNG (mọi thứ khác), không chồng bộ lọc; (2) ĐƠN GIAN TỐI ĐA —
> ít bước, không chấm điểm cầu kỳ, NÃO gọi đúng 1 lần mỗi beat.

---

## 1. Phễu đứng ở đâu, làm gì

Trong pipeline `new → align → direct → cut → source → assemble → report`, phễu nằm trong
bước **source**: với MỖI beat, từ đống ứng viên footage → chọn ra 1 footage tốt nhất.

Hiện tại code chọn khá thô (lấy ứng viên đạt đầu tiên). Phễu thay chỗ đó bằng 4 bước rõ
ràng, **chạy tuần tự từng beat** (beat 1 xong mới sang beat 2 — giữ nguyên thiết kế cũ,
không tối ưu toàn chuỗi):

```
beat N ──► B1 THU ──► B2 LỌC (2 cửa) ──► B3 CHẤM (1 lần) ──► B4 CHỌN ──► ghi log ──► beat N+1
```

## 2. Bốn bước — chi tiết từng bước

### B1. THU (gom ứng viên) — máy làm, không AI

Đúng như code hiện có + 1 luật nhỏ của c6:
1. **Local trước** (kho là tuyến CHÍNH — c1): tìm theo `queries.specific`, geo-gate như cũ.
2. **Luật c6:** nếu beat là **HOOK** hoặc **SLOT CHÊM** (`visual_anchor=false`) → gom thêm
   từ thư mục `signature/` và xếp các ứng viên đó LÊN ĐẦU danh sách. Rỗng thì thôi.
3. **Pexels bù** khi local mỏng: 3 tầng specific → broad → thematic như cũ (cache, xoay key).

Kết quả: 1 danh sách ứng viên (mục tiêu ~5–10) kèm metadata sẵn có (tag, độ dài, cỡ cảnh,
nguồn, đã-dùng-lần-nào-chưa).

### B2. LỌC — đúng 2 cửa, không bao giờ thêm cửa thứ 3

| Cửa | Ai xử | Thế nào |
|---|---|---|
| **Hỏng kỹ thuật / watermark** | máy (metadata + luật có sẵn) | file hỏng, quá ngắn, watermark → loại |
| **Sai nghĩa NGHIÊM TRỌNG** (c2: chủ đề khác hẳn / thực thể sai / ngược trần cụ thể) | NÃO — nhưng chấm CHUNG trong B3, không gọi riêng | ứng viên bị NÃO đánh nhãn `veto` → loại |

Mọi tiêu chí khác (mood lệch, lặp cỡ cảnh, nhạt, dài ngắn…) **KHÔNG được loại ai cả** —
chỉ trừ điểm ở B3. Phân vân → không veto, chấm thấp thôi.

### B3. CHẤM — NÃO gọi ĐÚNG 1 LẦN cho cả beat, ra 1 điểm tổng

**Một call duy nhất** (Claude Code, JSON + Pydantic validate): đưa vào — câu script của
beat, `central_subject`, **footage đã chọn ở beat N−1** (luật c3: nghĩa theo mạch) + cờ
"beat này mở chương mới", và danh sách ứng viên (mô tả/tag). NÃO trả về cho MỖI ứng viên:

```json
{ "id": "...", "verdict": "ok | veto", "diem_nghia": 0-10, "diem_mood": 0-10, "ly_do": "1 câu" }
```

Máy cộng thêm phần của mình (số học thuần, không AI):

```
ĐIỂM TỔNG = điểm NÃO (nghĩa ×3 + mood ×2.5)          ← phần nặng, quyết định chính
          + điểm MÁY (variety c7 + độ-dài-khớp + chưa-dùng-lại P7)   ← phần nhẹ, cộng/trừ nhỏ
```

- Trọng số là **VÍ DỤ 🔸** (đóng băng thứ tự nghĩa > mood > nhịp > đẹp; số cụ thể chỉnh sau).
- Điểm MÁY được thiết kế **không bao giờ đủ lớn** để lật một ứng viên đúng-nghĩa xuống
  dưới ứng viên kém-nghĩa. Cộng MỘT PHÁT, xếp hạng, xong — không vòng lặp, không chấm lại.

### B4. CHỌN — kèm sàn an toàn

1. Loại ứng viên `veto` + hỏng kỹ thuật.
2. **Sàn 3 (đóng băng c5):** nếu sau lọc còn <3 → tự nới: các ứng viên NÃO `veto` vì lý do
   KHÔNG thuộc 3 dạng nghiêm trọng được trả lại pool với điểm trừ nặng (luật tự hạ cấp).
3. Lấy ứng viên **điểm tổng cao nhất**. Pool trống hoàn toàn → đánh dấu `needs_human`
   (mềm, pipeline chạy tiếp) — như hiện nay.

### Ghi log (mỗi beat, vào project.json + report)

- Footage được chọn + `ly_do` 1 câu của NÃO (editor đọc hiểu ngay vì sao).
- **Kill-log:** mỗi cửa lọc giết bao nhiêu ứng viên. Cuối video, report tổng "% chết theo
  luật" — cửa nào giết nhiều bất thường → nới ĐỊNH NGHĨA cửa đó, không siết footage.

## 3. Chi phí & độ phức tạp

- **NÃO: đúng 1 call / beat** (video 8 beat = 8 call; hook Ai Cập từng chạy direct ~3 call
  nên mức này chấp nhận được). Không call phụ, không chấm nhiều vòng.
- Code mới gọn: 1 module `ranker/` (chấm + chọn + log) + sửa `sourcer` gọi phễu thay vì
  chọn thô + 1 prompt chấm. Ước lượng ~200–300 dòng + pytest.

## 4. Cái gì CHƯA làm đợt này (tránh phình)

| Để sau | Vì sao |
|---|---|
| Query local theo controlled vocabulary (c4) | chờ chốt schema tag GLM (Phase B) |
| Thực thi `shot_count` nhiều footage/beat | tính năng lớn riêng của pacing (d1) |
| Nối `audience_bias` | c6 bản gọn đã cắt |
| Mood 2 lớp C2b (histogram + vision) | b1 — đợt sau, phễu này mới chấm mood bằng tag/mô tả |
| Sàn hình thở + cứu hộ 3 nấc (d2) | tính năng riêng, cắm sau khi phễu chạy ổn |

## 5. Xác định THÀNH CÔNG trước khi code (P4)

1. **pytest:** veto đúng 3 dạng c2; sàn 3 tự nới; điểm MÁY không lật được nghĩa; kill-log
   đếm đúng; beat hook gom `signature/` trước (mock).
2. **Chạy thật 1 video mẫu** (hook Ai Cập hoặc tương đương): pipeline chạy trọn, report
   hiện lý-do-chọn + kill-log.
3. **Cổng mắt:** user mở draft CapCut + report, thấy footage chọn hợp lý hơn bản chọn-thô.

---

> **Chờ user duyệt tài liệu này.** Duyệt → code theo đúng 4 bước trên, từng milestone nhỏ
> (ranker trước, nối sourcer sau), mỗi bước có pytest + báo cáo.
