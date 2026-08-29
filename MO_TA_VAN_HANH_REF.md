# MÔ TẢ VẬN HÀNH — REF: ưu tiên NGUỒN VIDEO MẪU CỦA BÀI (user chốt 2026-07-11)

> Bối cảnh: bug SP1-014 (user phát hiện) — beat thiết kế/sản xuất Artemis bị chọn footage
> Pexels generic dù kho có 61 cảnh assembly/cleanroom Artemis từ chính 4 video mẫu của bài.
> Truy vết đầy đủ: memory `sp1-014-generic-footage-bug`. User chốt 2 luật: (1) ưu tiên
> footage từ nguồn video mẫu của bài, (2) trần viral 15% riêng nguồn mẫu (nguồn khác giữ 8%).

## 1. Khai báo — NGƯỜI khai, máy không suy

```
uv run autoedit source <project_dir> --ref "F:\SPACE\VIDEO MAU\SP1-014"
```
- `--ref` lặp được (nhiều folder/file). Prefix so sánh với `library_assets.source_video`,
  KHÔNG phân hoa-thường (path Windows).
- Khai 1 lần → **dính vào `project.json::inputs.ref_sources`** — các lần chạy lại (kể cả
  `run` gọi source không cờ) tự dùng bản đã khai. Khai `--ref` mới = ghi đè.
- Đúng luật own-vs-viral 2026-07-11: phân loại/phạm vi do người nạp KHAI, máy không suy
  từ tên file, không đề xuất re-class.
- **Điều kiện tiên quyết (bài học DS084, 2026-07-16):** REF chỉ có tác dụng khi mẻ video mẫu
  ĐÃ nạp vào sổ (`library_assets`) — chưa nạp thì `--ref` chạy RỖNG, không báo lỗi (DS3-084
  khai ref nhưng 0 cảnh mẫu trong sổ → bài dựng bằng kho chung, 10 video mẫu không vào kho).
  Từ 2026-07-16 **LUẬT TỰ NẠP** (skill `/dung-video` + HUONG_DAN A4.3-4): máy dựng bài TỰ
  `library-ingest` mẻ mẫu TRƯỚC direct-context, mọi máy — đảm bảo REF không bao giờ chạy rỗng.

## 2. Ba tác dụng (đều là NỚI hoặc ĐIỂM — không đẻ cửa loại)

| # | Tầng | Cơ chế | Code |
|---|---|---|---|
| 1 | THU | **Chèn pool**: match NỚI (trúng ≥1 từ tier local/specific, bỏ từ chuyển động C6) CHỈ trong tập cảnh nguồn mẫu, ≤6 cảnh/beat (`REF_INJECT_CAP`), xếp sau local AND-match / trước Pexels. Không trúng từ nào (beat ẩn dụ chủ đích) → không chèn. | `sourcer/local.py::find_ref_candidates` |
| 2 | CHỌN | **`REF_BONUS = 1.0`** vào điểm máy (cùng chỗ PEAK_BONUS — chảy cả 2 đường per-beat/batch). Cỡ số: 1 điểm nghĩa = 3,0 → bonus thắng khi nghĩa NGANG, cố ý KHÔNG lật nổi 1 điểm nghĩa. Đánh dấu `is_ref` tại 1 chỗ duy nhất (`_gather_candidates`) — phủ cả ứng viên vào bằng đường local lẫn đường chèn. | `ranker/funnel.py::_diem_may` |
| 3 | PHÁP LÝ | **Trần 15%** (`REF_CAP_RATIO`) thay 8% cho nguồn thuộc ref; nguồn khác 8% y cũ. Luật kề + miễn-kề-điểm-nhô + rải mềm + trùng-cảnh GIỮ NGUYÊN. | `sourcer/viral.py::ViralLedger._cap_ratio` |

Số đo lúc chốt (SP1-014, video 44′): nguồn hợp nhất đã chạm 140s/159s trần 8% (7,0%);
15% mở dư địa 4 nguồn mẫu 441s→826s. Rải mềm tán pick sang nguồn ít dùng nên khó kịch
trần 1 nguồn.

## 3. Rà chồng chéo (P5 — kiểm từng tầng cùng quản)

- **Đạo diễn queries (C4):** không đổi; chèn ref là lưới vớt khi query trượt/rỗng. Kèm
  luật chữ NICHE-ANCHOR mới trong skill `dung-video` (concept máy móc/quy trình phải neo
  chủ thể niche; ẩn dụ chủ đích vẫn generic) — vì bonus 1,0 KHÔNG cứu được concept viết
  generic (bằng chứng b018: thua 6,0 điểm nghĩa).
- **Ledger C8:** cảnh chèn VẪN qua gate kề + trần (chèn ≠ miễn pháp lý); gate áp cả tại
  gather lẫn re-check tại pick như cũ.
- **Geo-gate PA2:** áp cho cảnh chèn y như local thường.
- **Phễu nghĩa/mood + veto c2:** vẫn chấm cảnh chèn như mọi ứng viên — tầng này ĐƯỢC PHÉP
  lật ưu tiên (nghĩa trên hết, đúng thiết kế).
- **C5 vision gate:** pick từ kho (gồm ref) vẫn bị soi — lưới vớt cho match nới. (Bất đối
  xứng cũ "Pexels không bị soi" còn ngỏ, không thuộc gói này.)
- **P7 chống lặp / rải mềm / PEAK_BONUS:** không đổi; REF_BONUS cộng dồn được với
  PEAK_BONUS (cùng triết lý điểm). Shot thở vốn đóng với viral — không đụng.
- **Không tầng nào bị lật ngược; không thêm cửa loại nào.** Điểm canh duy nhất: REF_BONUS
  quá cao sẽ đè nghĩa → giữ 1,0 🔸 chỉnh khi có bằng chứng (như PEAK_BONUS 0,5).

## 4. Kiểm chứng

- pytest hồi quy 4 bài mới (`tests/test_sourcer.py`): trần 15% + prefix không phân
  hoa-thường; OR-match chỉ trong tập ref + beat ẩn dụ không chèn; glue `is_ref` mọi
  đường vào pool + `_diem_may` cộng đúng bonus; nhãn ledger không rơi (vết PB7).
- FULL suite 429 pass (2026-07-11).
- Chạy thật: vá 12 beat SP1-014 bằng re-source per-beat (ledger nạp lại sổ từ các beat
  giữ nguyên) — kết quả ghi NHAT_KY_BUILD.md.

## 5. Số 🔸 (chỉnh khi có bằng chứng)

`REF_BONUS = 1.0` · `REF_CAP_RATIO = 0.15` · `REF_INJECT_CAP = 6`

## 6. REF THEO CHƯƠNG (VD2 — user chốt 2026-07-18, chế độ MỀM)

> Editor phân sẵn video mẫu theo chương ngay trong folder mẫu — máy scope ưu tiên REF
> theo chương beat đang dựng. Ví dụ thật: `F:\LIFE IN\VIDEO MAU\AMZ10000`.

### 6a. Khai báo — KHÔNG thêm cú pháp

```
F:\LIFE IN\VIDEO MAU\AMZ10000\
├── video-a.mp4               ← mẫu CHUNG cả bài (file nằm ngay gốc)
├── Chapter 1\video-b.mp4     ← mẫu RIÊNG chương 1
├── Chapter 2\video-c.mp4     ← mẫu RIÊNG chương 2
└── food market\video-d.mp4   ← folder con tên KHÁC khuôn chương → mẫu CHUNG
```

- Vẫn `--ref "F:\LIFE IN\VIDEO MAU\AMZ10000"` y cũ. Máy đọc PATH trong sổ (KHÔNG quét
  đĩa — máy nào cũng chạy được, không lệ thuộc F: mount): segment NGAY DƯỚI folder
  `--ref` khớp khuôn `chapter|chuong|chương|ch` + số (không phân hoa-thường) → cảnh
  thuộc RIÊNG chương đó; còn lại = mẫu chung. Số chương = `chapter_id` outline (cùng
  quy ước scope `chN` của BOOST VD3). ⚠ Tên folder phải ĐÚNG khuôn trọn vẹn — `Chapter
  1 - food` có hậu tố → bị coi là mẫu CHUNG (nhìn dòng ĐO `chung=` để phát hiện).
- Không có folder chương nào → map rỗng, hành xử y §1–2 (tương thích ngược 100%).
- Điều kiện tiên quyết y cũ (LUẬT TỰ NẠP 2026-07-16): TỪNG video mẫu — kể cả trong
  folder Chapter — vẫn nạp bằng draft tách cảnh riêng. ⚠ Path file nguồn trong draft
  editor phải trỏ đúng file TRONG folder chương (xếp video vào folder TRƯỚC, import
  draft SAU — dời file sau khi làm draft là path trong sổ mất thông tin chương).

### 6b. Cơ chế MỀM (user chốt: chỉ mất ưu tiên, KHÔNG cửa loại)

Với beat thuộc chương k:

| Tầng | Cảnh chương k + mẫu chung | Cảnh chương KHÁC k |
|---|---|---|
| CHÈN pool (≤6/beat) | có | KHÔNG (nhường slot cho đúng chương) |
| `REF_BONUS` 1,0 | có (nhãn `is_ref`) | KHÔNG (không gắn nhãn) |
| Search thường kho | y mọi asset | y mọi asset — nghĩa cao vẫn được chọn |
| Trần ledger | 15% | 15% (giữ CẢ mẻ — `_cap_ratio` không đọc map) |

Code: `sourcer/local.py::ref_chapter_scan` quét sổ 1 lần lúc vào stage source (substr,
không LIKE — bài học PG backslash 2026-07-17) → map `chương → prefix` treo trên
`ViralLedger.ref_chapter_prefixes` (không đổi chữ ký hàm nào — ledger vốn được luồn
sẵn) → `find_ref_candidates(exclude_prefixes=…)` chặn CHÈN + nhãn `is_ref` scoped theo
`beat.chapter`, cả hai tại chokepoint duy nhất `_gather_candidates`.

### 6c. Tầng ĐO

- Warning đầu source: `REF theo chương (mềm): ch1=X, ch2=Y, chung=Z cảnh`.
- Folder chương KHÔNG khớp `chapter_id` nào của outline → warning riêng (cảnh trong đó
  không được chèn/bonus ở beat nào — chỉ còn trần 15%; thường là editor đánh số lệch).

### 6d. Rà chồng chéo (P5)

- **Foundation filter-overload-guard:** user chủ động chốt MỀM (2026-07-18, có hỏi lại)
  để KHÔNG đẻ cửa loại — scope chỉ TƯỚC ưu tiên (chèn + bonus), không loại ứng viên nào
  khỏi pool. Phương án CỨNG (loại hẳn cảnh sai chương) bị bác.
- **Phễu nghĩa (NGHIA_W = 3,0):** vẫn trên hết — cảnh chương khác nghĩa cao vẫn thắng,
  ĐÚNG chủ đích mềm. Không tầng nào bị lật: bonus chỉ đổi có/không per-beat.
- **Ledger C8 / trần 15%:** không đụng — cảnh sai chương vào bằng search thường vẫn ăn
  trần 15% + luật kề y cũ.
- **BOOST (VD3):** độc lập — `is_boost` gắn theo term match, không đọc ref map; hai
  bonus cộng dồn như trước.
- **Signature / geo-gate PA2 / P7 / C5 gate:** không đọc `is_ref`/`ref_prefixes` —
  không đụng.
- **Mọi đường gọi** (per-beat, batch PA-1, heuristic không brain, chạy lại source) đều
  qua `_gather_candidates` + `ViralLedger` khởi tạo đúng 1 chỗ (runner.py::source) —
  đã grep, KHÔNG có call site thứ hai (chống vết bug B2 quên-consumer).

### 6e. Kiểm chứng

pytest: parse map (Chapter/CHUONG/ch + `chapter 1` không nuốt `chapter 10` + folder
thường → chung) · `exclude_prefixes` chặn chèn · nhãn `is_ref` mềm (cảnh sai chương
VẪN trong pool qua search thường, mất nhãn) · parity PG path backslash. FULL suite.
