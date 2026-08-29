# MÔ TẢ VẬN HÀNH — FILE `topic + chapter video.txt` CHO PROJECT CÔNG TY (tag bối cảnh own)

> Trạng thái: **USER DUYỆT 2026-07-11** ("duyệt. bạn hãy tiếp tục") — M1 code xong cùng ngày.
> Gốc vấn đề: tag vision cho draft công ty (own) chưa có bối cảnh chủ đề/chương — viral
> đã có từ ytref §3i (title thật + chapters YouTube + --topic), own mới chỉ có stem tên
> file material + flag `--topic` CLI (ít ai nhớ gõ). Luật phân loại own/viral: memory
> `own-vs-viral-phan-loai` — file này CHỈ nâng chất lượng tag, không đụng gate pháp lý.

## 1. Logic user chốt

Editor để 1 file **`topic + chapter video.txt`** vào NGAY TRONG folder project CapCut:
```
E:\PROJECT NHAN BAN\SPACE 1\SP1 - 012\topic + chapter video.txt
```
- Có ĐỦ chapter (kèm dấu thời gian) → hệ thống dựa mốc thời gian lấy **cả chapter làm
  bối cảnh ĐOẠN** cho từng cảnh.
- Không đủ chapter → **chỉ lấy tiêu đề** làm chủ đề video.

## 2. Format file (editor copy từ mô tả video YouTube đã đăng là chạy)

```
Vì sao Mặt Trăng chỉ cho ta thấy một mặt — bí ẩn tidal locking
00:00 Mở đầu
02:15 Vì sao Mặt Trăng bị khóa thủy triều
05:40 Mặt tối có thật sự tối?
09:10 Các sứ mệnh thăm dò mặt xa
```
- **Mọi dòng TRƯỚC dòng chapter đầu tiên** = tiêu đề/chủ đề (nhiều dòng thì gộp).
- **Dòng chapter** = bắt đầu bằng timestamp `M:SS` / `MM:SS` / `H:MM:SS`, sau đó là tên
  chương. Đúng format YouTube ghi trong mô tả video → copy-paste nguyên khối.
- **"Đủ chapter" = ≥2 dòng chapter** (1 dòng = cả video 1 chương, không có giá trị chia
  đoạn → coi như "không đủ", chỉ lấy tiêu đề).
- Dòng hỏng/parse không được → bỏ đúng dòng đó. File không có → im lặng, tag y cũ
  (fail-open toàn tầng). UTF-8 (chấp nhận BOM), tên file đọc không phân biệt hoa thường.

> **📌 LỆCH SO VỚI BẢN GỐC (2026-07-11, M1):** file THẬT editor đặt ở SP1-012 có thêm
> dòng NHÃN (`Topic video:` trên dòng riêng, `chapter` trên dòng riêng) — parser dung nạp:
> dòng chỉ-có-nhãn (topic/topic video/chapter(s)/tiêu đề/chủ đề/chương, kèm/không kèm `:`)
> bị BỎ; nhãn dính đầu dòng nội dung chỉ strip khi CÓ dấu `:` (tiêu đề bắt đầu bằng chữ
> "Chapter..." không bị cắt oan). Regression test theo đúng nội dung file thật.

## 3. Chi tiết kỹ thuật

### 3a. Dữ liệu file đi đâu (prompt KHÔNG đổi khuôn — field có sẵn từ ytref M2)
- Tiêu đề trong file → field **`topic`** của TagJob (cùng bậc source_title trong prompt).
- Chapter chứa cảnh → field **`section_hint`** ("gợi ý về ĐOẠN, không chắc từng cảnh").
- **`source_title` per-material GIỮ NGUYÊN stem** — với own, stem stock thường mô tả tốt
  (`vecteezy_man-silhouetted...`), không đè.

### 3b. ⚠ BẪY HỆ QUY CHIẾU THỜI GIAN (điểm dễ sai nhất)
- Chapter video công ty tính theo **TIMELINE video** = timeline draft → map chapter bằng
  **`scene.target_start + target_duration/2`**.
- Viral giữ nguyên map theo **`scene.start`** (giây FILE NGUỒN — chapter của video nguồn).
- Cùng 1 hàm `_chapter_title`, 2 đường truyền mốc KHÁC NHAU — ghi test riêng từng đường.
- Draft có intro/đầu đuôi lệch bản đăng vài giây → chấp nhận (chapter là gợi ý ĐOẠN,
  cùng tinh thần fail-open §3i).

### 3c. Thứ tự ưu tiên nguồn bối cảnh
| Class | Ưu tiên |
|---|---|
| own | file txt (chính) → CLI `--topic` **ĐÈ file nếu truyền** (explicit thắng, warning khi cả 2 khác nhau) → không có gì: **warning nhắc** (luật vận hành mới) |
| viral | YouTube tự tra (title+chapters) → file txt làm **fallback** khi không rút được ID/yt-dlp chết → stem |

### 3d. Dry-run soi trước khi tốn tiền (văn hóa PB6)
`library-ingest --dry-run` in thêm: topic đọc được + số chapter hợp lệ + 2 chapter đầu
làm mẫu — editor soi format đúng chưa rồi mới chạy thật.

## 4. Rà chồng chéo (P5)

| Tầng cùng quản | Quan hệ với file txt | Kết luận |
|---|---|---|
| Prompt `_tag_instruction` (§3i) | topic/section_hint là field CÓ SẴN — chỉ thêm nguồn dữ liệu, khuôn prompt không đổi | Không ngược chiều |
| Luật không-đoán 2b | Vẫn là PHANH: hình mâu thuẫn bối cảnh → tag theo HÌNH | Giữ nguyên |
| `stock_tags` + C5 vision gate | KHÔNG đổi — mắt độc lập bắt tag nói dối | Giữ nguyên |
| yt_infos viral (§3b/3c) | File chỉ LẤP khi YouTube trống — không đè dữ liệu tra được | Cùng chiều |
| CLI `--topic` (M2) | Đổi vai: từ nguồn duy nhất → override; hành vi cũ (không file) y nguyên | Ghi rõ trong help |
| db / consumer | topic/section_hint KHÔNG lưu db (y title §3i) — không consumer nào đổi | Không đụng |
| dna d1/c7 (`target_start`) | Chỉ ĐỌC thêm target_start, không sửa giá trị | Không đụng |

Không tầng nào âm thầm lật tầng mới; tầng mới không ngược chiều tầng nào.

## 5. Lộ trình + cổng

| Mốc | Nội dung | Cổng |
|---|---|---|
| M1 | Parser file + nối ingest (own chính / viral fallback) + warning own-thiếu-topic + dry-run in số | pytest (parser, 2 hệ quy chiếu, ưu tiên nguồn, fail-open) + **dry-run trên SP1-012 thật** (user đặt file mẫu, soi bằng mắt số in ra) |
| M2 | Hồi tố kho cũ: núm ép tag lại (needs_index đang skip asset đã tag) + danh sách draft nguồn cho editor điền topic/file + chạy re-tag `nap` 619 + `signature` 1108 (địa danh 6.300 KHÔNG re-tag — folder ground-truth đã gánh) | soi ~10–15 tag trước/sau (A/B lớn đã chứng minh ở MOON, không cần lặp) + user duyệt |

## 6. Chi phí
- M1: ~0đ (không thêm call GLM — chỉ thêm chữ vào prompt sẵn có).
- M2 hồi tố: ~1.700 asset × ~$0,00093 ≈ **$1,6–2**, vài giờ GLM (3 luồng/key, xoay key).
