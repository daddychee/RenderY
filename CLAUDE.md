# CLAUDE.md — RenderY

**Fork của tool padoma**, phát triển thành tool dựng video riêng cho user.
Mục tiêu: **đưa kịch bản + voice vào → nhận timeline CapCut**. Footage từ nguồn uy tín.

> **ĐỌC CẢ `CLAUDE_PADOMA_GOC.md`** — luật gốc của padoma (5 luật CapCut C1–C5,
> 5 nguyên tắc kiến trúc NT1–NT5, cách chọn provider AI). File này chỉ ghi
> **cái gì RenderY làm KHÁC**, không chép lại.

---

## Fork từ đâu

| | |
|---|---|
| Nguồn | `F:\OutlierY Nas 2\Tool Edit\tool edit padoma` |
| Ngày fork | 29/08/2026 |
| Quyền | User đã được padoma cho phép dùng **toàn bộ** |
| Không copy | `.venv/`, `.git/`, `autoedit/projects/` (2GB output cũ), `AB_TAG_MOON/`, `TOOL CẮT SIÊU DỮ LIỆU/`, `.env`, cache |
| Đã copy | 373 file / 52MB — **137 file .py + 38 file test**, khớp 100% bản gốc |

Tool thứ hai kế thừa: **Auto Editing** (`D:\App\AE\Auto Editing`, repo `daddychee/aespace`)
— sẽ lấy **connector Envato/Vecteezy/Artlist** + **web UI**, hai thứ padoma không có.

---

## LUẬT CỨNG (chốt 29/08/2026)

### 1. Đầu ra là DRAFT CAPCUT, không phải MP4
User chốt: *"thứ tôi muốn là timeline capcut, không phải video Mp4"*.
ffmpeg CHỈ dùng để probe + copy media vào draft. Không encode video hoàn chỉnh.
Mọi cải tiến đo bằng chất lượng TIMELINE, không phải chất lượng video render.

### 2. Trao đổi trước khi code
User nhắc 2 lần: *"chưa được code, chúng ta cần trao đổi trước"*.
Khảo sát → trình bày → đề xuất có đánh đổi → **DỪNG**, đợi duyệt.

### 3. Karpathy + Ponytail (user yêu cầu áp dụng trước khi code)

**Karpathy** — `D:\App\AE\refs\andrej-karpathy-skills\CLAUDE.md`:
1. *Think Before Coding* — nêu giả định; nhiều cách hiểu thì HỎI, không chọn ngầm.
2. *Simplicity First* — code tối thiểu. 200 dòng làm được bằng 50 → viết lại.
3. *Surgical Changes* — **"Don't refactor things that aren't broken"**,
   **"Don't remove pre-existing dead code unless asked"**. Mỗi dòng diff truy về yêu cầu.
4. *Goal-Driven Execution* — mỗi bước có tiêu chí verify chạy được.

**Ponytail** — `D:\App\AE\refs\ponytail\AGENTS.md`. Thang leo TRƯỚC KHI viết code:
1. Có cần xây không? (YAGNI) → 2. Đã có trong codebase chưa? → 3. Stdlib có chưa?
→ 4. Platform có sẵn? → 5. Dependency đã cài giải quyết được? → 6. Một dòng được không?
→ 7. Chỉ khi đó mới viết code tối thiểu.

*"Deletion over addition. Boring over clever. Fewest files possible."*
*Không lười ở*: hiểu vấn đề, validate ở biên tin cậy, error handling chống mất dữ liệu,
bảo mật, và **thứ được yêu cầu rõ ràng**. Logic không tầm thường phải để lại **1 check chạy được**.

### 4. Python đo — LLM hiểu/sinh, không đảo vai
Mọi con số đo bằng code. LLM chỉ chia ý, đặt tên, sinh keyword.
**NT4 của padoma: LLM KHÔNG BAO GIỜ SINH TIMESTAMP.**

### 5. Không tự quyết hộ user
Tool tự chọn clip được, nhưng phải **đánh dấu rõ chỗ không chắc** để user review có trọng điểm.

---

## Luồng: TUYẾN TÍNH THEO CHƯƠNG

User ren voice từng chương; trong lúc tool dựng chương N thì user ren voice chương N+1.

```
User ren voice chương 1 ──► thả vào RenderY ──► tool dựng chương 1 ─┐
User ren voice chương 2 ──► thả vào RenderY ──► tool dựng chương 2 ─┴─► draft tổng
```

**Đầu vào mỗi chương** (user đưa từng file riêng, tool KHÔNG tự chia chương):
`script.txt` + `voice.mp3` + `voice.srt` *(thiếu srt → sinh timestamp)*

---

## NGUỒN FOOTAGE — ràng buộc pháp lý

User: *"kho của họ đều là đi cắt từ nguồn không legal... không biết tỉ trọng và đâu là
đoạn cắt. Rất rủi ro. Mục tiêu rõ ràng là dùng footage từ các trang uy tín."*

**Đã kiểm chứng: kho padoma HOÀN TOÀN TRỐNG** — `Tool Edit\AutoEdit\{library,music,sfx}`
đều 0 file; `F:\THU VIEN NHAC + SFX` không tồn tại. User nhận CODE, không nhận DỮ LIỆU.
→ Kho xây từ đầu, 100% nguồn user kiểm soát.

| Nguồn được phép | Giấy phép | Từ đâu |
|---|---|---|
| Envato Elements · Vecteezy Pro · Artlist | Subscription | connector Auto Editing |
| Pexels · Pixabay | Free, thương mại được | cả 2 tool |
| Kho user tự mua/tự quay | Của user | xây dần |

**Footage cắt YouTube — TÁCH BIỆT RÕ, không loại hẳn** (user chốt): giữ được nhưng phải
đánh dấu trong sổ để phân biệt clip cắt vs clip mua. Padoma có `library/ytpeaks.py` +
`sourcer/viral.py` + gate C8 → **cô lập, không bật mặc định**.
Tool cắt YouTube riêng của user: repo `daddychee/me-metadata-extraction` — KHÔNG nối vào pipeline.

**SỔ NGUỒN GỐC:** mỗi clip ghi **nguồn + ID** (user chốt: chỉ cần vậy).
Padoma đã có `draft_materials` registry — thêm 2 trường.

---

## Dependency — CÔNG CỤ TỐI THIỂU CHO KẾT QUẢ TỐI ĐA

User chốt: *"công cụ tối thiểu cho kết quả tối đa, hạn chế những thứ cồng kềnh mà không có kết quả."*

**CÀI (7):** `pycapcut` · `typer` · `pydantic` · `python-dotenv` · `pyyaml` · `requests` ·
`matplotlib` — cộng **ffmpeg** (binary hệ thống, có sẵn `C:\OutlierY\tools\ffmpeg\bin\`).

**BỎ (5):**

| Gói | Lý do |
|---|---|
| `madmom` | **MSVC C++ Build Tools KHÔNG có trên máy** → không build được. Chỉ phục vụ NHIP-M4 |
| `librosa` | Chỉ cho MUSIC SYNC — nâng cao, chưa yêu cầu |
| `psycopg[binary]` | Dựng song song nhiều máy; user 1 máy → SQLite đủ |
| `faster-whisper` | `.srt` user ĐÃ CÓ timestamp. **Để OPTIONAL**, cài khi gặp chương thiếu |
| `yt-dlp` | Chỉ cho YTREF điểm nhô — đã cô lập |

**KHÔNG gỡ code PostgreSQL / đa máy** (Karpathy #3): không cài `psycopg` thì nhánh đó
không chạy, không cản trở gì. Xoá chỉ tạo diff lớn + rủi ro hỏng test. User chốt:
*"Đúng, đừng gỡ gì cả."*

### ✅ ĐÃ KIỂM CHỨNG THẬT (29/08/2026, venv riêng trong scratchpad)

| Kiểm chứng | Kết quả |
|---|---|
| Python 3.13.14 (padoma cần ≥3.11) | ✅ |
| Cài 7 gói | ✅ sạch |
| `import pycapcut` — 55 symbol, đủ `ScriptFile`/`VideoSegment`/`AudioSegment`/`TrackType` | ✅ |
| Import 6 module cốt lõi (project, matcher, silence, ducking, packager, pause) | ✅ |
| CLI `--help` — **44 lệnh** | ✅ |
| **Test: 721 collected** | ✅ **697 pass / 10 fail / 14 skip** |

**10 fail đều là `test_music_rhythm.py` → `No module named 'librosa'`** — đúng nhóm đã cố ý bỏ.
**KHÔNG có bug code nào.**

**2 điều chỉ biết được khi CHẠY THẬT:**
1. **`PYTHONUTF8=1` BẮT BUỘC** (không chỉ `PYTHONIOENCODING`). Thiếu → 4 test chết
   `UnicodeDecodeError: 'charmap' codec`, `--help` crash giữa chừng. Đặt CẢ HAI trong launcher.
2. **`matplotlib` KHÔNG bỏ được** — không phải để vẽ chart, mà vì
   `assembler._slug_image()` render **ảnh placeholder "EDITOR: ĐẮP FOOTAGE Ở ĐÂY"** cho ô
   `needs_human`. Đây CHÍNH LÀ placeholder câu thiếu clip đã chốt — padoma làm sẵn rồi.

**Lệnh chạy:**
```bash
cd F:/RenderY/autoedit
PYTHONPATH=. PYTHONIOENCODING=utf-8 PYTHONUTF8=1 python -m autoedit.cli --help
```

---

## Quyết định đã chốt

| # | Quyết định | Lý do |
|---|---|---|
| 1 | Đầu ra = draft CapCut | LUẬT CỨNG 1 |
| 2 | Tự chọn clip + **đánh dấu chỗ không chắc** | Cắt 80% thao tác, vẫn tôn trọng LUẬT CỨNG 5 |
| 3 | LLM = **GLM** (z.ai) | Ý định ban đầu; Auto Editing có bug gate nên chạy nhầm Claude |
| 4 | Keyword `[0]` trước, ít kết quả mới thử `[1]`,`[2]` | Đo thật: `[0]` đủ cho 8/8 câu |
| 5 | Câu thiếu clip → **placeholder** giữ đúng chỗ | Bỏ qua mất 65% timeline. **Padoma đã có** (`_slug_image`) |
| 6 | Xuất draft ngay, review/sửa rồi xuất lại | Xem tổng thể sớm |
| 7 | Gộp dần vào **1 draft tổng** | Mở ra là có cả phim đúng thứ tự |
| 8 | Giao diện **web** | User quen tay, xem/chọn clip trực quan |
| 9 | Timeline theo **duration thật từ voice** | Chính xác tuyệt đối |
| 10 | **FORK padoma** (không copy module lẻ) | Giữ 38 file test + 40 tài liệu — thứ đắt nhất |
| 11 | Quy mô **20–100 video/tháng** | Padoma cho ~200/tháng → không cần hạ tầng đa máy |
| 12 | Chỉ nguồn uy tín; YouTube **tách biệt rõ** trong sổ | Xem NGUỒN FOOTAGE |

**Tín hiệu "không chắc"** — đo bằng Python, không hỏi LLM:

| Tín hiệu | Mức |
|---|---|
| 0 clip | 🔴 → placeholder |
| < 3 clip | 🟠 |
| `imageability < 0.5` (L3 sinh sẵn) | 🟠 |
| Phải fallback keyword `[1]`/`[2]` | 🟡 |
| Sạch mọi tín hiệu | 🟢 bỏ qua được |

---

## Bẫy đã biết ngoài CLAUDE_PADOMA_GOC.md

### Môi trường máy này
- Ổ F là **ổ cứng local thật** (16.7TB, volume "MINPICTURE DATA"), không phải NAS
  dù thư mục tên "OutlierY Nas 2".
- **Không có MSVC Build Tools** → mọi gói cần build C++ đều fail.
- CapCut **9.1.0.3879** tại `C:\Users\Administrator\AppData\Local\CapCut`.
  Draft root user dùng thật: `F:\OutlierY Nas 2\Tool Edit\Capcut Draft\CapCut Drafts`.
- Draft mẫu **ĐÃ CHẠY ĐƯỢC** (mở trong CapCut + render ra MP4 375MB):
  `...\CapCut Drafts\SCRIPT1_20260805_072653` — dùng `materials/`, 18 key/video, version 360000.
- Python 3.13.14 · `uv` 0.12.1 · **chưa có Node.js**.
- venv **không di chuyển được** giữa máy/OS. `.bat` phải CRLF.

### Bug kế thừa từ Auto Editing — sửa khi port connector sang
- `main.py:371` + `script_parser.py:353` gate cứng `ANTHROPIC_API_KEY` → **vô hiệu hoá
  multi-provider**. User đặt `LLM_PROVIDER=glm` nhưng vẫn chạy Claude; refine bị bỏ im lặng.
- `main.py:610` sinh 2–4 keyword nhưng **chỉ dùng `[0]`**.
- `_meta.json` ghi **không atomic** → crash mất sạch project.
- `derive_brief` đồng bộ trong async handler → **block event loop** 3–10s.
- Restart server → `l3_status` kẹt `running` vĩnh viễn, FE poll vô hạn.
- Download 50 clip **tuần tự** = ~4 phút giữ 1 request HTTP.
- URL login Envato **khác nhau** giữa `main.py:84` và `login.py:28`.
- `app.js:537` chèn `page_url` vào `innerHTML` không escape.

### Đo thật trên project `video_001` (Rome, 8 câu) — Auto Editing
- L3 sinh keyword: **8/8 câu, 0 lỗi**, 4 keyword/câu.
- Search Pexels+Pixabay với `keywords[0]`: **8/8 câu đều ra 8 clip 16:9**.
  → Scraper KHÔNG hỏng; câu trống trước đó chỉ vì test dở (`search_keywords=None`).
- Bỏ qua câu thiếu clip → timeline còn 14.4s/40.8s: **mất 65%**.

---

## Lộ trình

- [x] R0 Khảo sát Auto Editing + chốt spec
- [x] R1 Khảo sát padoma → chốt padoma làm xương sống
- [x] R2 **Fork sang `F:\RenderY`** + git init + venv + verify test (697 pass, khớp gốc)
- [x] R3 **Align đọc `.srt` có sẵn** — `align/srt_file.py` + `--backend auto|srt|whisper`.
      714 pass. Parse thật IN002 (434 câu/2850 từ) + geo023 (284 câu/1873 từ), tức thì.
      Không sửa runner/matcher — chỉ implement interface `Aligner` có sẵn.
- [ ] R4 Mô hình chương: nhận script+voice+srt từng chương
- [ ] R5 Port connector Envato/Vecteezy/Artlist từ Auto Editing + sổ nguồn gốc
- [ ] R6 Tự chọn clip + chấm 4 tín hiệu không chắc
- [ ] R7 Gộp dần draft tổng
- [ ] R8 Web UI + hàng đợi job bền (restart không mất việc)

**Verify từng bước** (Karpathy #4): R3 nghe mép file segment · R5 tải thật 1 clip Envato ·
R7 mở draft trong CapCut thật · R8 restart server giữa chừng, job vẫn chạy tiếp.
Không tự nhận "xong" khi chưa chạy.
