# RenderY V2 — thoát khỏi nền Padoma

> **Cập nhật 07/09 chiều (user duyệt sau phản biện):** thứ tự ĐẢO — làm việc
> **C** (thay lõi) TRƯỚC, hoãn **A** (đổi tên package). Lý do: đổi tên không
> tạo giá trị vận hành nào hôm nay, trong khi rủi ro gãy production là thật
> (3 chỗ gọi `"-m", "autoedit.cli"` bằng CHUỖI + data root + hơn 20 file .md);
> team đang chờ dùng. Rủi ro pháp lý nằm ở phần người ngoài nhìn thấy (nhãn
> hiển thị + tài liệu + chuỗi "PADOMA") — phần đó rẻ, làm khi rảnh.
> Mục "bỏ `nhip/ep.py`" ở Đợt 4: **KHÔNG làm** — xem QĐ2 trong `SEQUENCE.md`.
> Thứ tự việc hiện hành nằm ở `SEQUENCE.md`, không phải file này.

> **Trạng thái: LỘ TRÌNH, CHỜ DUYỆT.** Lập 07/09/2026 theo yêu cầu user:
> tách RenderY thành tool độc lập, không còn tên gọi liên quan Padoma (tránh
> vấn đề pháp lý), giữ lại phần chất xám còn hữu dụng.

## Đo hiện trạng trước (07/09/2026)

Không đoán — mọi con số dưới đây đo tận tay hôm nay.

| | |
|---|---|
| Mã nguồn | **148 file .py · 34.682 dòng** |
| File lớn nhất | `cli.py` 2.909 dòng · `web/static/index.html` 3.195 dòng |
| Lịch sử | 163 commit · **1** commit message nhắc "padoma" |
| Dấu vết "padoma" trong code/tài liệu chính | **23 chỗ** |
| Di sản tài liệu ở gốc `F:\RenderY` | **74 file .md/.txt** |
| Dữ liệu — projects | **136 GB** (`F:\RenderY\autoedit\projects`, 48 thư mục) |
| Dữ liệu — sổ tra / Library | **16 GB** (`C:\Users\Administrator\AutoEdit\so_tra`) |
| Thư mục thừa | `autoedit-v2/` 2,5 GB (bản sao cũ, 193 file .py) |

**Module theo kích thước** (dòng code):

```
sourcer 4916 · packager 4567 · web 3775 · library 3124 · director 3096
sotra 1872 · offline 1620 · music 1340 · ambient 1300 · ranker 758
cutter 749 · kenh 686 · nhip 633 · aigen 587 · editor_learn 526
retention 423 · align 359 · report 315 · overlay 273 · sfx 153
```

## Ba việc phải phân biệt — đừng gộp

Yêu cầu "tách khỏi Padoma" thực chất là ba việc rất khác nhau về rủi ro:

| Việc | Bản chất | Rủi ro |
|---|---|---|
| **A. Đổi tên** | `autoedit` → `rendery`, xoá mọi chuỗi PADOMA | Cơ học nhưng chạm 148 file — gãy là chết production |
| **B. Dọn di sản** | 74 file .md cũ, `autoedit-v2/`, demo cũ | Thấp — chỉ là xoá/lưu trữ |
| **C. Thay lõi cũ** | bỏ logic Padoma không còn đúng (ép nhịp, pipeline 7 stage) | Cao — đây là thay đổi *hành vi*, phải nghiệm thu |

**A không đồng nghĩa với C.** Đổi tên xong tool vẫn chạy y hệt; thay lõi mới là
việc thật. Trộn hai thứ vào một đợt thì khi hỏng không biết hỏng vì đâu — đúng
vết xe đổ ngày 07/09 (bug "chương double" sinh ra vì `chi_chuan_bi` và
`_project_cu_dung_duoc` sửa lẫn nhau trong một lượt).

## `autoedit` chính là tên cần đổi

Không chỉ chuỗi "PADOMA" — **tên package `autoedit` là tên tool gốc của Padoma**
(`cli.py:34` ghi nguyên: *"AutoEdit — script + voice -> CapCut draft (PADOMA
MEDIA)"*). Đổi tên thật sự nghĩa là:

| Chỗ | Từ | Thành |
|---|---|---|
| Package | `autoedit/` | `rendery/` |
| Import | `from autoedit.x import y` (mọi file) | `from rendery.x import y` |
| Lệnh CLI | `autoedit make ...` | `rendery make ...` |
| `pyproject.toml` | `name = "autoedit"` | `name = "rendery"` |
| Data root | `C:\Users\Administrator\AutoEdit\` | `C:\Users\Administrator\RenderY\` |
| Chuỗi trong code | `PADOMA_AUTOEDIT_DEMO`, `PADOMA_OVERLAY_DEMO`, `PADOMA_TEST_V2` | tên trung tính |
| Docstring | 8 chỗ nhắc "padoma" như nguồn luật | viết lại thành luật của mình |
| Tài liệu | `CLAUDE_PADOMA_GOC.md` | viết lại nội dung, bỏ tên |

**136 GB + 16 GB dữ liệu KHÔNG copy** — chỉ trỏ đường dẫn sang chỗ mới, hoặc
đổi tên thư mục data root một lần.

## Lộ trình — 6 đợt, mỗi đợt một cổng nghiệm thu

Nguyên tắc xuyên suốt: **production không được chết quá 5 phút mỗi đợt**, và mỗi
đợt commit riêng để lùi được một bước.

### Đợt 0 — Chốt tên và dựng lưới an toàn (30 phút)

- Chốt tên package: đề xuất **`rendery`** (khớp tên tool, khớp repo GitHub)
- `git tag truoc-doi-ten` — điểm lùi
- Đóng băng bản hiện tại sang cổng 9119 cho team dùng trong lúc làm (đã nghiệm
  thu 07/09: C12 chạy trọn 6 stage, mã 0, 908s)

**Cổng:** team có đường chạy không phụ thuộc việc đang làm.

### Đợt 1 — Đổi tên package (nửa ngày)

Thuần cơ học, **không đổi một dòng logic nào**:

1. `git mv autoedit rendery`
2. Thay `from autoedit` / `import autoedit` → `rendery` trên toàn bộ 148 file
3. `pyproject.toml`: name + `[project.scripts]` + `packages`
4. `resolve_data_root()`: `AutoEdit` → `RenderY`, **kèm tương thích ngược** —
   thấy thư mục cũ thì dùng tiếp, không bắt chép 16 GB
5. Chuỗi `PADOMA_*` trong `packager/demo.py`, `cli.py` → tên trung tính

**Cổng:** `1338 test xanh` (con số hôm nay) · nghiệm thu 1 chương đầu-cuối ra
draft CapCut · `grep -ri padoma rendery/` trả về **0**.

> Rủi ro cao nhất của cả lộ trình nằm ở đây, nhưng là rủi ro *phát hiện được
> ngay*: sai import thì import lỗi lập tức, không âm thầm.

### Đợt 2 — Dọn di sản (2 giờ)

- 74 file .md/.txt ở gốc → `docs/luu_tru/` (giữ tra cứu, không xoá)
- Xoá `autoedit-v2/` (2,5 GB bản sao cũ) sau khi xác nhận không ai trỏ tới
- `CLAUDE_PADOMA_GOC.md`: rút phần còn đúng (5 luật CapCut, nguyên tắc kiến
  trúc) vào tài liệu mới **viết bằng lời của mình**, rồi đưa bản gốc vào lưu trữ
- 8 docstring nhắc "padoma" → viết lại nêu *luật*, không nêu *nguồn*

**Cổng:** `grep -ri padoma` trên toàn repo (trừ `docs/luu_tru/`) trả về 0.

### Đợt 3 — Bộ tài liệu sống (nửa ngày)

User nêu lý do thẳng: *"anh đã nhớ nhớ quên quên rất nhiều, ảnh hưởng tới công
việc của chúng ta"*. Nên tài liệu phải **cập nhật theo mốc**, không phải viết
một lần rồi bỏ.

| File | Chứa gì | Cập nhật khi nào |
|---|---|---|
| `CLAUDE.md` | kiến trúc: module nào làm gì, dữ liệu chảy ra sao, luật cứng | đổi kiến trúc |
| `METHODOLOGY.md` | phương pháp luận: nhìn dữ liệu trước, chạy mẫu nhỏ, không tin fail-soft im lặng, bàn trước khi code, nghiệm thu bằng chứng cứ | rút được bài học mới |
| `SEQUENCE.md` | mọi kết luận về New Sequence: cấu trúc thư mục, 3 kiểu chạy, nguồn | mỗi lần chốt |
| `OFFLINE_VERSION.md` | khối, khay ứng viên, animatic, hotkey, gen AI theo khối | mỗi lần chốt |
| `ONLINE_TIMELINE.md` | bản Online, tải bản sạch, nhạc + ducking, xuất draft | mỗi lần chốt |

Mỗi file mở đầu bằng **bảng mốc** (ngày · chốt gì · ai quyết) để đọc là biết
quyết định nào mới nhất.

**Cổng:** đọc 5 file đó là dựng lại được bức tranh mà không cần hỏi lại user.

### Đợt 4 — Thay lõi Padoma không còn đúng (1–2 ngày)

Đây là việc **C**, làm sau khi A và B đã xanh:

1. **Ép nhịp**: bỏ `nhip/ep.py` (dự báo shot_count + kẹp sàn của Padoma), thay
   bằng guide từ Framing Insight — user chốt 07/09
2. **Ba kiểu chạy** Manual / AVD Mode / Auto trên một đường Offline duy nhất
3. **Cấu trúc phẳng + `Rec/`**
4. Form New Sequence 6 ô

Chi tiết từng mục ở [FLOW_NEW_SEQUENCE_V2.md](FLOW_NEW_SEQUENCE_V2.md).

**Cổng:** mỗi mục một nghiệm thu riêng, chạy thật một chương, có số đo.

### Đợt 5 — Gỡ giàn giáo (2 giờ)

- Tắt cổng 9119 khi tool chính đã ổn định vài ngày
- Xoá pipeline 7 stage cũ nếu đường Offline đã phủ hết (**không xoá trước khi
  đường mới chạy thật ít nhất một tập trọn vẹn**)

## Cái gì của Padoma còn giữ (đã sửa, đổi tên)

Không bỏ hết — những thứ này đã trả giá bằng lỗi thật, giữ lại phần cơ chế:

| Giữ | Vì sao |
|---|---|
| 5 luật ghi draft CapCut | đo trên CapCut thật, sai là draft không mở được |
| Khuôn `Project` + `Stage` | mô hình chạy lại từng bước, đã dùng 163 commit |
| `packager/` (ráp draft) | phần khó nhất, đã chạy đúng qua nhiều tập |
| `align/`, `cutter/` | khớp voice–chữ, không dính gì Padoma về mặt logic |
| Nguyên tắc fail-open có ghi log | đã cứu nhiều job khỏi chết cả tập |

## Cái gì bỏ

| Bỏ | Vì sao |
|---|---|
| `nhip/ep.py` — ép nhịp Padoma | user: *"không còn đúng"*, thay bằng Framing Insight |
| Preset nhịp theo niche | đã gỡ 06/09, niche không được đổi nhịp |
| Overlay text + SFX của pipeline cũ | user: không dùng, sẽ xây bản riêng |
| `autoedit-v2/` | bản sao cũ 2,5 GB |

## Ba điểm cần user chốt trước khi bắt đầu

1. **Tên package**: `rendery` — đồng ý không?
2. **Chỗ đặt**: đổi tên tại chỗ (`F:\RenderY\rendery`, giữ nguyên git 163
   commit) hay dựng folder hoàn toàn mới và bỏ lịch sử? Đề xuất: **đổi tên tại
   chỗ** — lịch sử là tài sản để truy nguyên nhân, và chỉ có 1 commit message
   nhắc "padoma".
3. **Thứ tự**: làm A+B trước (đổi tên sạch, tool chạy y hệt) rồi mới tới C? Hay
   ưu tiên C (ép nhịp, 3 kiểu chạy) vì team đang chờ dùng?
