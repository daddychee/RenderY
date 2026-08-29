# MÔ TẢ VẬN HÀNH — DRAFT PORTABLE + FOLDER XUẤT `E:\CapCut Drafts`

> User chốt 2026-07-13 sau ca SP1-014 bàn giao máy editor. Cổng mắt ĐẠT trên 2 máy
> (máy này + máy editor thật) với draft `SP1_014_ARTEMIS_2_FULL_..._PORTABLE`.

## 1. Bài toán

Draft do tool sinh ghi path media **tuyệt đối máy gốc** (`C:\Users\NBPC\...\<draft>\materials\...`).
Copy sang máy editor khác → path chết:
- Audio (`check_flag=3`) → CapCut coi "thiếu file local" → **cho relink** (sống được).
- Video (dict pycapcut tối giản, `check_flag=63487` thiếu bit verified-local) → CapCut coi
  **"cloud material thiếu"** → báo **"Không thể tải xuống tài liệu"**, **KHÔNG cho relink** → chết.
  (Khớp bài học AutoClone `KINH_NGHIEM_CHUNG.md §B4` + `NHAT_KY_BUILD.md mục 15` — REAL71.)

## 2. Cách giải (đã kiểm chứng bằng mắt 2 máy, 2026-07-13)

Bắt chước **đúng dạng draft native của CapCut** (soi DS3_003, AMZ33... của editor):

1. **Path trong CONTENT** (`draft_content.json`/`draft_info.json`) →
   `##_draftpath_placeholder_0E685133-18CE-45ED-8CB8-2904A212EC80_##/materials/<tên>`
   (separator `/`). GUID là **hằng số toàn cục CapCut** — quét 401 file draft từ máy
   Mac + Windows editor khác nhau: tất cả cùng đúng 1 GUID. CapCut resolve placeholder
   = "folder draft này", bất kể draft nằm đâu.
2. **check_flag video** 63487 → **62978047** (native verified-local). Audio giữ nguyên.
3. **Sổ đăng ký meta** (`draft_materials[].file_Path`) ghi **tương đối** `./materials/<tên>`
   (đúng quy ước native); link `local_material_id` khớp theo TÊN file (tên duy nhất do
   `_embed_media` chống trùng).
4. **`draft_meta_info.json` các trường khác GIỮ NGUYÊN** — `draft_fold_path` tuyệt đối của
   máy sinh; stale trên máy khác **vô hại** (bằng chứng: draft editor archive fold_path
   trỏ NAS chết vẫn mở tốt).

Code: `autoedit/packager/packager.py::_to_portable` (chạy TỰ ĐỘNG trong `package_draft`
— mọi draft mới đều portable, không có núm tắt). `_to_portable` trả cây MỚI: dict content
của caller giữ path tuyệt đối → re-package/overwrite vẫn chạy.

## 3. Folder xuất draft: `set-draft-root`

- `machine.json` thêm `draft_out_root` (rỗng = như cũ ghi vào `capcut_root`).
- Máy này đã đặt: `autoedit set-draft-root "E:\CapCut Drafts"` (2026-07-13, theo user chốt).
- Draft mới (assemble / demo-draft / mọi caller `package_draft`) ghi vào đó, tự mkdir.
- Donor/register-machine KHÔNG đổi — donor vẫn ở `capcut_root` (com.lveditor.draft),
  cover draft lấy từ donor như cũ.
- **Muốn thấy draft trong CapCut máy này:** Settings CapCut → Draft location trỏ
  `E:\CapCut Drafts` (một lần). Bàn giao editor = copy nguyên folder draft, mở là chạy,
  không relink. KHÔNG đè folder draft trùng tên bên máy editor (luật C5) — bản hỏng cũ
  phải xóa khỏi CapCut trước.

## 4. Rà chồng chéo (bắt buộc theo P5)

| Tầng cùng quản path/draft | Ngược chiều? | Có thể âm thầm lật? |
|---|---|---|
| **Luật C2 "path tuyệt đối"** (CLAUDE.md §4) | KHÔNG — C2 ghi rõ 2 dạng ĐÚNG: tuyệt đối HOẶC placeholder; cấm là `./materials/` trong CONTENT. Placeholder là dạng đúng thứ 2. Bài học 15.1 AutoClone (package_embedded hỏng) là do path `./` TƯƠNG ĐỐI trong content — KHÁC placeholder. | Không |
| **`verify_assets`** (đòi path tuyệt đối tồn tại) | KHÔNG — chạy TRƯỚC `_embed_media`/`_to_portable`, trên path nguồn. | Không |
| **`verify_draft`** (fold_path == folder thật) | KHÔNG — meta giữ tuyệt đối, check nguyên như cũ. | Không |
| **Reader draft về sau**: `library/ingest.py` (tag own/viral), `editor_learn/mine.py`, `library/tcf_gen.py` | KHÔNG — cả 3 đã xử lý placeholder sẵn (draft editor native vốn dùng placeholder; regex `_PLACEHOLDER` ingest.py:59). | Không |
| **Sổ đăng ký ↔ content** (bài học relink 12/06: local_material_id phải khớp sổ) | Đổi cách khớp: path → TÊN file. An toàn vì tên trong `materials/` duy nhất (dedupe `_embed_media`). Test `test_package_draft_portable_cross_machine` khóa. | Không |
| **Resume/re-assemble** (NT5 draft tên mới `_V2`…) | KHÔNG — `_next_version` giờ soi out_root (nhất quán chỗ ghi). Draft cũ trong com.lveditor.draft KHÔNG bị đếm nữa → SCRIPT_*_V15 mới sẽ bắt đầu lại ở E: (chấp nhận — series test cũ đã xong). | Đã cân nhắc |
| **Music-sync M4 / report** | KHÔNG — music vào content trước package; report chỉ đọc project.json + tên draft. | Không |

## 5. Kiểm chứng

- Cổng mắt: SP1-014 PORTABLE mở tốt máy này + máy editor (user xác nhận 2026-07-13).
- Hồi tố tay: SP1-014 FULL + SP1-017 (F:\SPACE\PROJECT TOOL CHAY XONG) đã portable-hóa,
  backup JSON gốc ở `<draft>_backup_json_truoc_portable\`.
- pytest: **469 passed** (FULL suite; 4 test mới packager + 2 test cập nhật).
