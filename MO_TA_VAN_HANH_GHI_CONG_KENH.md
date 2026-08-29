# MÔ TẢ VẬN HÀNH — GHI CÔNG KÊNH NGUỒN (VD4, 2026-07-17)

> User chốt 2026-07-17: (a) mỗi footage cắt từ video nguồn phải ghi vào SỔ là lấy của
> KÊNH nào; (b) ghi được cả cho footage CŨ trong kho; (c) editor muốn ghi công thì BẬT
> tính năng — tool đặt TÊN KÊNH ở 1 trong 4 góc màn hình (random).

## 1. Thiết kế

### 1a. Cột `source_channel` trong `library_assets`
- Tên cột theo HỌ `source_*` sẵn có (`source_video`/`source_class`/`source_duration`) —
  **KHÔNG đặt `channel`** vì codebase đã có 2 chỗ `channel` mang nghĩa KHÁC:
  `Inputs.channel` + `asset_usage.channel` = kênh SẢN XUẤT của mình (P7 phạt mềm).
- Giá trị điền theo 3 ngả, ưu tiên từ trên xuống (explicit thắng — cùng luật `--topic`):
  1. `library-ingest ... --channel "Tên Kênh"` — người nạp khai cho CẢ mẻ.
  2. Mẻ **viral** có YouTube ID: yt-dlp `--dump-json` có sẵn field `channel`/`uploader`
     → tự điền TỪNG file nguồn (1 draft có thể trộn nhiều kênh). Trước giờ code fetch
     mà bỏ qua field này (`ytpeaks.py`).
  3. Kho cũ: lệnh backfill `channel-set` (mục 2).
- **Luật preserve (chống footgun):** upsert với `source_channel` RỖNG → GIỮ giá trị cũ
  (`CASE WHEN excluded.source_channel='' THEN ...`). Nghĩa là re-ingest resume/retag
  KHÔNG `--channel` sẽ **không xóa** kênh đã backfill. Muốn xóa kênh → `channel-set`
  với giá trị mới. (Khác họ `source_video='' THEN giữ` — vì ingest LUÔN có source_video
  nhưng thường KHÔNG khai channel; nếu theo khuôn cũ thì mỗi lần resume là mất backfill.)
- `needs_index` KHÔNG xét cột mới → không re-tag oan cả kho (bài học mtime REAL-PG).

### 1b. Backfill kho cũ — người khai, máy không suy
Máy KHÔNG đoán kênh từ tên folder (luật own-vs-viral 2026-07-11: class/nguồn gốc do
NGƯỜI NẠP khai). 2 lệnh:
- `uv run autoedit channel-audit [--niche X]` — liệt kê FOLDER nguồn (gom theo thư mục
  cha của `source_video`) + số asset + kênh đã điền/chưa → user/editor nhìn là biết
  còn thiếu gì.
- `uv run autoedit channel-set "<prefix folder nguồn>" "<Tên Kênh>" [--niche X] [--dry-run]`
  — gán kênh cho MỌI asset có `source_video` bắt đầu bằng prefix (không phân hoa-thường).
  So prefix làm ở **Python trên danh sách DISTINCT source_video, update theo GIÁ TRỊ
  CHÍNH XÁC** — né hẳn LIKE (xem 3b). `--dry-run` đếm trước khi ghi.

### 1c. Kênh chảy vào draft — stamp lúc SOURCE, không mở sổ lúc assemble (NT1)
`ShotPick`/`ExtraShot`/`BreathShot` thêm field `source_channel`, copy từ ứng viên tại
5 điểm pick (funnel lead + extra / heuristic / sàn niche / shot thở). `_row_to_candidate`
PHẢI mang cột này lên ứng viên (vết bug PB7 cột-rơi). Assemble chỉ đọc project.json.
Hệ quả chấp nhận: project source TRƯỚC khi backfill → không có kênh; muốn có thì chạy
lại `source` (hiếm — tính năng dùng cho video mới).

### 1d. `assemble --credit` — chữ ghi công ở góc
- Mặc định TẮT. Bật: mỗi segment footage L1 có `source_channel` → 1 TextSegment nhỏ
  (size 8, anim none, viền đen như mọi text) đặt tại 1 trong 4 GÓC màn hình.
- Góc chọn **crc32(asset + mốc đặt) % 4** — random giữa các segment nhưng deterministic
  (dựng lại ra đúng góc cũ, cùng khuôn seed Ken Burns/shot thở).
- Track text riêng `credit` (CapCut cấm 2 segment đè nhau 1 track — `_safe_add_segment`).
- Text góc cần `transform_x` — `build_text_overlay` thêm `x_override` (pipeline đã dùng
  transform_x cho card PiP, chỉ là expose cho text).
- Slug "EDITOR ĐẮP", chart, info-card, beat graphic nền lót: KHÔNG credit (không phải
  footage nguồn thật / sẽ bị editor thay).

## 2. Cách dùng (editor)
```
# Nạp mẻ mới có khai kênh (viral có YouTube ID thì --channel khỏi cần, tự lấy):
uv run autoedit library-ingest space "E:\...\SP1 - 020" --source-class viral --channel "Astrum"

# Soát kho cũ còn folder nào chưa có kênh:
uv run autoedit channel-audit --niche space

# Điền kênh cho kho cũ theo folder nguồn:
uv run autoedit channel-set "F:\SPACE\VIDEO MAU\SP1-017" "Astrum" --dry-run   # đếm trước
uv run autoedit channel-set "F:\SPACE\VIDEO MAU\SP1-017" "Astrum"

# Dựng có ghi công:
uv run autoedit assemble <project_dir> --credit
```

## 3. RÀ CHỒNG CHÉO (P5 — bắt buộc)

### 3a. Các tầng CÙNG QUẢN thứ sắp đụng
| Tầng | Đụng? | Kết luận |
|---|---|---|
| Phễu source / ranker (điểm, veto, trần viral) | KHÔNG | `source_channel` KHÔNG vào điểm/lọc — cột chỉ để truy vết + hiển thị. ViralLedger vẫn gate theo `source_video` y cũ. |
| Upsert 2 đường (index thường vs ống nạp) | CÓ | Luật preserve 1a: rỗng không đè. Re-index thường (extra rỗng) giữ kênh. `editor-learn`/`library-index` không khai channel → giữ. |
| `move_asset` (file đổi chỗ) | KHÔNG | UPDATE path/category/folder_path, không đụng cột mới. |
| `needs_index` (quyết định re-tag) | KHÔNG | Không xét `source_channel` — backfill không kích re-tag. |
| Track text (overlay/kinetic/chart) | CÓ | Track TÊN RIÊNG `credit` + `_safe_add_segment` — không đè track `text`/`kinetic{k}`. |
| Ducking/nhạc/SFX | KHÔNG | Text track không có volume keyframe/audio. |
| Sổ 2 lưng SQLite/PG (G2) | CÓ | Cột mới đi qua `_SCHEMA` + `_migrate` (chạy CẢ 2 lưng, TEXT không dính bẫy REAL). Backfill update theo giá trị chính xác — không LIKE (3b). |
| Máy editor ghi song song (M4) | KHÔNG | Thêm cột idempotent; UPDATE theo path/giá trị — cùng hàng ghi đè theo luật preserve, không khóa dài. |

### 3b. Bug ANH EM phát hiện khi rà (sửa kèm M1)
`find_ref_candidates` (`sourcer/local.py`) build `lower(source_video) LIKE '<prefix>%'`.
Trên **PostgreSQL, `\` trong pattern LIKE là ký tự ESCAPE** → prefix Windows
`f:\space\video mau\...` match hụt → **REF chạy RỖNG im lặng trên máy đã flip PG**
(SQLite không sao — test cũ dùng `F:/` nên không lộ). Fix: so prefix bằng
`substr(lower(source_video), 1, ?) = ?` — không pattern language, 2 lưng như nhau.
`channel-set` mới cũng cùng nguy cơ → thiết kế né LIKE từ đầu (1b).
Các chỗ LIKE khác đã rà: `search_assets` (term là TỪ, không có `\`) — an toàn;
`ViralLedger`/`runner.py:642` dùng `str.startswith` Python — an toàn.

### 3c. Câu hỏi 2 chiều
- Luật mới có NGƯỢC CHIỀU tầng nào không? **Không** — không tầng nào đang quản "kênh
  nguồn footage"; cột mới chỉ thêm dữ kiện, không đổi quyết định pick/gate nào.
- Tầng nào có thể ÂM THẦM LẬT quyết định của tầng mới? **Upsert re-ingest** (đã chặn
  bằng luật preserve 1a) và **re-source project cũ** (pick mới copy kênh mới — đúng ý).

## 4. Còn ngỏ
- Vị trí 4 góc (±x, ±y) là số v1 — CHỜ CỔNG MẮT CapCut, chỉnh theo mắt user/editor.
- `report.html` chưa hiện cột kênh nguồn theo beat (thêm sau nếu editor cần soát).
- Kho cũ: giá trị kênh do user/editor điền dần bằng `channel-set` — tool chỉ audit.
- Beat `graphic` nền lót không credit (v1) — nếu editor muốn thì mở rộng sau.
