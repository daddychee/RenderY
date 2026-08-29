# MÔ TẢ VẬN HÀNH — NHẠC CHO ĐOẠN CHÈN Δ (NHIP-M3)

> Gói CẮT THEO NHỊP NHẠC, mốc M3 (`BAN_GIAO_NHIP_NHAC.md` §3). Viết 2026-07-20.
> Trạng thái: 🔄 **CODE ĐÓNG, CHỜ CỔNG TAI USER**. pytest 670 (+9).
> Đọc kèm: `MO_TA_VAN_HANH_DOAN_CHEN.md` (M2 — cơ chế chèn Δ).

---

## 1. Làm gì

Editor đưa **bài nhạc riêng** cho đoạn chèn Δ. Bài đó **THAY** nhạc của chương từ
mép VÀO Δ cho tới **HẾT CHƯƠNG** — không quay lại bài cũ (**phương án B**, user chốt
2026-07-19; phương án A "chỉ trong Δ rồi trả về" đã BÁC vì 2 lần chuyển nhạc trong
vài chục giây nghe rối).

Tầm phủ "tới hết chương" user chốt 2026-07-20: sang chương sau thì đổi nhạc bình
thường theo kế hoạch cũ — đi **cùng chiều** thiết kế "đổi nhạc theo chương".

## 2. Editor dùng thế nào

```bash
autoedit insert <project> --after-beat 57 --dur 20 \
    --music "E:\NHỊP NHANH\ĐÀN DỒN DẬP NHỊP NHANH\Class Act.mp3"
autoedit insert <project>            # liệt kê — có ♪ tên bài nếu đã đưa nhạc
# rồi chạy lại: cut -> music (nếu music-sync) -> source -> assemble
```

- File nằm **đâu cũng được** (ngoài kho nhạc), máy tự chuẩn hóa WAV như nhạc kho (C4).
- Kiểm file tồn tại **NGAY lúc khai** — path sai báo lỗi luôn, không để tới assemble
  mới lộ (Δ vẫn dựng, chỉ mất bài editor = loại lỗi "hỏng-mà-vẫn-chạy").
- Không `--music` → Δ dùng nhạc chương như cũ, **M2 nguyên vẹn**.
- Khai lại cùng beat = SỬA (kể cả đổi/bỏ nhạc).

## 3. ★ BẤT BIẾN BỊ PHÁ CÓ CHỦ ĐÍCH: "1 chương = 1 bài"

**Trước M3:** một chương đúng một bài nhạc. Đo thật **14/14 project** trong
`autoedit/projects/` — số bài = số chương, không sót một cái. Khóa cứng ở 3 chỗ:
`select_music` (`select.py:131` "1 bài/chương"), `MusicPlanEntry.chapter_id`
(`project.py:369`), `pick_by_ch` dict khóa chapter_id (`assembler.py:653`).

> ⚠ Dễ nhầm: hệ thống **CHỌN** nhạc theo CẢM XÚC từng đoạn nội dung rất tinh vi
> (`_score` theo mood/music_hint; `_entry_span`/`_start_offset` `select.py:93,165`
> vào thẳng đoạn `drop` cho chương cao trào, `intro` cho chương lắng). Nhưng
> **RANH GIỚI ĐỔI BÀI** thì vẫn trùng ranh giới chương. Hai thứ khác nhau.

**M3 phá bất biến đó ĐÚNG MỘT CHỖ:** Δ có `--music` mở một **span nhạc mới** giữa
chương. Đây là lần đầu tiên 1 chương có thể có 2 bài.

**Hệ quả — chỗ nào giả định "1 chương = 1 bài" thành bẫy:**
`music_selections` là dict khóa `chapter_id` (`assembler.py:702`) → bài editor sẽ
**đè mất** tên bài gốc trong report. Đã xử lý: span Δ ghi key `"<ch>Δ"` (vd `"2Δ"`),
bài gốc giữ key `"2"`.

## 4. Chạy ở đâu

`music/plan.py`:
- `insert_edges(project)` → `{after_beat: (mép_vào, mép_ra)}`. Mép VÀO Δ =
  `segment.timeline_end + breathing_after + micro_pause_after` — **KHÔNG PHẢI**
  `beat.timeline_end` (chỉ beat cuối run mới trùng segment). Khớp đúng công thức
  coverage dựng cửa sổ Δ (`coverage.py:97-101`).
- `music_spans(project, chapters, boundaries, total_end)` → danh sách nhịp nhạc theo
  timeline. Chương không có Δ-nhạc → **đúng 1 span, tọa độ Y HỆT đường cũ**.

`packager/assembler.py::_add_music_by_chapter` lặp trên **span** thay vì chương.

## 5. HAI BẪY TỌA ĐỘ đã xử lý (ổ bug im lặng)

**① Track `music`/`music2` luân phiên theo CHỈ SỐ SPAN, không phải chỉ số chương.**
Span lẻ chèn vào giữa mà vẫn đếm theo chương → 2 đoạn liền nhau rơi **cùng một
track** → crossfade 3s đè nhau → `SegmentOverlap`, mà `_safe_add_segment` thì
**nuốt lỗi im lặng** (§7d.3 bàn giao). Đã kiểm trên RD89 thật: 6 span ra
`music/music2/music/music2/...` xen kẽ, **0 đoạn đè nhau trên cùng track**.

**② Bất biến P KHÔNG áp cho span Δ.** Công thức `P = start_offset + min(XFADE,
timeline_start)` (`plan.py:196`, `assembler.py:656`) giả định segment nhạc bắt đầu
ở **đầu chương**. Span Δ bắt đầu **giữa chương**, và `start_offset` trong
`music_plan` là của **bài CŨ** — áp vào bài editor sẽ nhảy vào một điểm vô nghĩa
giữa bài lạ. Nên span Δ vào từ **đầu bài** (offset 0), không áp P.

## 6. RÀ CHỒNG CHÉO (P5) — các tầng cùng quản vùng nhạc Δ

| Tầng | Đụng không? | Kết luận |
|---|---|---|
| M-CHANGE (`music_boundaries`) | Mép Δ đã nằm trong `edges` từ M2 (cửa sổ Δ là window riêng) → ranh giới chương sau Δ vẫn neo vào mép RA Δ | thuận chiều, không sửa |
| Bất biến P (`timeline_accents`) | Span thường giữ P y cũ; span Δ không áp P (§5.2) | đã xử lý |
| `timeline_accents` / `timeline_beats` | Lặp theo CHƯƠNG, `hi = bounds[i+1]` → accent trong vùng span Δ vẫn tính theo bài CŨ của chương | ⚠ **TỒN ĐỌNG** — xem §8 |
| Ducking F8 | Δ không có voice → nhạc NỞ 0.5 suốt Δ, không phân biệt bài | cộng hưởng, không đụng |
| M-VOL hook | `i == 0` giờ là span đầu = chương đầu (Δ không thể ở đầu video, §7a) | không đổi hành vi |
| `select_music` cấm lặp bài (`used`) | Bài editor ngoài kho → không vào `used` | không xung đột; trùng bài chương khác → xem §8 |
| `usage` (phạt mềm đa dạng giữa video) | Span Δ **KHÔNG** đếm usage — bài editor không thuộc kho, đếm vào sẽ bẩn sổ | đã loại |
| Δ **không** có `--music` | `music_by_beat` rỗng → không chẻ span | M2 nguyên vẹn (có test) |
| Ambient / SFX / slug trong Δ | M3 chỉ đụng track nhạc | không đụng |
| Chuẩn hóa WAV (C4) | Bài editor qua `normalize_audio` y như nhạc kho | không đụng |

**Tầng nào có thể ÂM THẦM LẬT M3?** Chỉ 2 ứng viên, cả hai đã chặn: track alternation
(§5.1) và bất biến P (§5.2). Ngược lại M3 không lật tầng nào — span Δ chỉ tồn tại khi
editor chủ động đưa nhạc.

## 7. File : dòng

| File | Đổi |
|---|---|
| `project.py` | `InsertSpec.music` (project.json M2 load được, mặc định rỗng) |
| `music/plan.py` | +`insert_edges()` +`music_spans()` |
| `packager/assembler.py` | `_add_music_by_chapter` lặp span; track theo chỉ số span; key `selections` |
| `cli.py` | cờ `--music` cho `insert` (kiểm file lúc khai) + liệt kê ♪ |
| `tests/test_music_insert.py` | 9 test (mép Δ/chẻ span/liền mạch/2 Δ/span vụn/schema) |

## 8. Cách kiểm (cổng) + TỒN ĐỌNG

- pytest: **670 passed, 11 skipped** (M2 đóng ở 661 → +9, 0 hồi quy).
- Chạy thật `rd89-oman-10min-20260720`: `insert_edges` ra **188,4185 → 208,4185**,
  khớp **từng chữ số** số đo cổng mắt M2. Chưa `--music` → 5 span = 5 chương (hồi quy
  bằng 0). Có `--music` → span Δ phủ **188,42→208,42 = đúng 20,00s**.
- 🔄 **CỔNG TAI USER — CHƯA CHẠY.** Claude KHÔNG tự báo đạt.

**TỒN ĐỌNG (chưa làm, ghi để không mất):**
1. `timeline_accents`/`timeline_beats` chưa biết span Δ → accent/beat target trong vùng
   bài editor vẫn tính theo bài CŨ của chương. **Chưa hại ở M3** vì mép Δ được MIỄN
   snap (guard M2) và trong Δ chưa có footage thật để cắt. **Sẽ thành thật ở M4/M5**
   khi cắt hình theo nhịp trong Δ — lúc đó phải cho 2 hàm này đọc span.
2. Bài editor **chưa đo nhịp** (`beat_times`/`beat_strength`) vì nằm ngoài kho — M0 chỉ
   đo bài trong kho. M4 cắt hình theo nhịp trong Δ sẽ cần; đo bằng librosa ~0,5s/bài.
3. Bài editor trùng bài đã chọn cho chương khác → nghe lặp. Chưa cảnh báo (editor đưa
   bài là editor quyết) — cân nhắc thêm warning nếu user gặp thật.
