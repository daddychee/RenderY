# MÔ TẢ VẬN HÀNH — SFX EPIDEMIC SOUND (`epidemic-sfx`)

> Ngày đóng code: 2026-07-18. Trạng thái: 🔄 CHỜ CỔNG TAI (đã nạp 18 file thật vào life-in).

---

## 1. Vấn đề & cách giải

Kho SFX local mỏng: nhiều kind chỉ **1 biến thể** (`penguin`, `vulture`, `crow`,
`snowmobile`, `ski`, `escalator`) — dùng lại trong 1 video là nghe lặp lộ ngay.
Epidemic Sound có ~250k SFX tag chuẩn theo LOÀI/vật thể, và công ty đã mua tài khoản.

Giải: lệnh `epidemic-sfx` tìm + tải + nạp thẳng vào kho ambient per-niche.

## 2. Dùng thế nào

```bash
# xem trước, KHÔNG tải
autoedit epidemic-sfx --niche life-in --want "camel" --dry-run

# kind=term:số_file — term khác kind khi cần tả rõ hơn
autoedit epidemic-sfx --niche life-in --want "escalator=escalator:4" --want "ski=skiing:4"

# chạy lại không tải trùng: kind đã đủ 4 biến thể thì bỏ qua
autoedit epidemic-sfx --niche life-in --target 4 --want "crow=crow:4"
```

| Cờ | Mặc định | Ý nghĩa |
|---|---|---|
| `--want` | (bắt buộc) | `kind` \| `kind=term` \| `kind=term:n`. Lặp nhiều lần. |
| `--filetype` | `MP3` | `WAV` lấy bản gốc 24bit/96k (nặng ~13MB/file). |
| `--target` | không | Kind đã có ≥ n biến thể thì bỏ qua — chạy lại an toàn. |
| `--min-s` / `--max-s` | 1 / 30 | Lọc độ dài. |
| `--loose` | tắt | TẮT lưới loài (xem §4). Chỉ dùng khi cố ý gom rộng. |
| `--dry-run` | tắt | Xem sẽ lấy gì, không tải. **Luôn chạy trước mẻ lớn.** |

## 3. Đường đi kỹ thuật

```
SearchSoundEffects (MCP)
  → LƯỚI LOÀI title_matches()        ← loại kết quả lệch loài TRƯỚC khi tốn băng thông
  → DownloadSoundEffect → tải ngay   ← link hết hạn ~60s
  → folder tạm + sinh ambient_manifest.yaml
  → ambient.library.import_from_manifest()   ← TÁI DÙNG NGUYÊN, không viết lại
       ↳ normalize_audio() → WAV PCM 48k (luật C4)
       ↳ _next_name() → <kind>.wav, <kind>_2.wav…
       ↳ ghi ambient_library.yaml (artlist_url = link Epidemic, truy license)
```

File: `autoedit/ambient/epidemic.py` (client MCP thuần) + `epidemic_fetch.py` (nghiệp
vụ nạp kho) + `cli.py::epidemic_sfx_cmd`.

## 4. LƯỚI LOÀI — vì sao phải có

**Đo thật 2026-07-18:** search Epidemic ngữ nghĩa lỏng, cố lấy đủ `limit` nên vét sang
loài họ hàng. Tìm `penguin` → ra NGỖNG, HẢI ÂU, **vịt đồ chơi**; `vulture` → currawong,
mallard, **chim tiền sử**. Nạp mù thì `penguin.wav` kêu tiếng vịt = tái lập đúng RD-89
(lạc đà nghe tiếng chim) mà vừa sửa xong.

`title_matches()` giữ kết quả chỉ khi **kind (hoặc từ riêng của term) có mặt trong
title**. Từ chung chung (`call`, `bird`, `engine`, `movement`…) bị loại khỏi phép khớp —
nếu không `"penguin call"` sẽ khớp `"Goose, Call"` (pytest bắt được lỗi này lúc code).

Kind chuyên biệt (`snowmobile`, `escalator`, `ski`) vốn đã đúng 4/4, lưới không đụng tới.

## 4b. BẬT/TẮT MỖI LẦN DỰNG — `--epidemic` (MẶC ĐỊNH TẮT)

User chốt 2026-07-18: editor bật/tắt **theo lần dựng** (không theo máy, không theo niche).
**ĐẢO MẶC ĐỊNH cùng ngày:** ban đầu mặc định BẬT (cờ `--no-epidemic` để tắt) → user chốt
lại **mặc định TẮT**, chỉ bật khi yêu cầu → cờ đổi thành `--epidemic`. Hai cờ SFX giờ
cùng chiều "gõ vào là bật", không còn phủ định kép.

```bash
autoedit assemble <project>              # mặc định KHÔNG dùng SFX Epidemic
autoedit assemble <project> --epidemic   # bật cho lần dựng này
autoedit run <project> --epidemic        # cả pipeline
```

Cơ chế: `project.use_epidemic_sfx` (mặc định `False`) → `assembler._epidemic_skip()` đọc
`ambient_library.yaml` lấy tên file có `artlist_url` chứa `epidemicsound.com` → truyền
`exclude_files` xuống `list_variants()`. **Kho VẪN GIỮ nguyên file** — tắt chỉ là không
chọn tới, bỏ cờ là dùng lại ngay (khác hẳn xóa hay đổi folder).

Chokepoint đúng 1 chỗ: mọi tầng SFX (ambient `choose_files`, chủ thể `choose_subject_files`,
drone `choose_drone`, hook `_add_hook_sfx`) đều đi qua `list_variants` — sửa 1 nơi, cả 4
tầng theo. Bật (mặc định) → trả `None`, không đọc yaml, 0 chi phí.

📌 **Chốt chặn thật nằm ở `assembler._epidemic_skip` — `getattr(project, "use_epidemic_sfx", False)`.**
project.json CŨ (dựng trước 2026-07-18) KHÔNG có field này; sửa mỗi `project.py` là VÔ ÍCH,
draft cũ dựng lại vẫn bật qua nhánh getattr. Có pytest chốt cả 2 đường (field=False và
object thiếu field hẳn). Đo thật RD-89: mặc định **0/100 lượt**, `--epidemic` → **16/100**.

## 5. BẪY đã cắn (giữ lại kẻo quên)

1. **`term` phải LỒNG trong `query`** — để phẳng ở cấp trên cùng thì server *lặng lẽ*
   bỏ qua, trả list mặc định. Mọi term ra **cùng một kết quả**, không lỗi, không cảnh
   báo. Mất 3 lần thử mới nhận ra. → có test hồi quy.
2. **Key tài khoản FREE search được nhưng KHÔNG tải được** (`FORBIDDEN`). Key phải tạo
   từ tài khoản **trả phí**. Thông điệp lỗi đã chỉ thẳng nguyên nhân này.
3. **`assetUrl` hết hạn ~60 giây** — lấy link xong phải tải ngay, không cache lại được.
4. **Key hết hạn 30 NGÀY** → 401. Bắt riêng, báo `account/api-keys`, không chết câm.
5. File gốc là **24bit/96kHz** — bắt buộc qua `normalize_audio()`, thả thẳng vào draft
   thì CapCut đòi relink (C4).
6. **Title dài trùng 60 ký tự đầu → file ĐÈ nhau.** Epidemic đặt title rất dài, 2 SFX
   khác nhau có thể trùng hệt phần đầu (*"…Farmers Market, Vendors Shouting, People
   T|alking 01/02"*). Cắt 60 ký tự làm tên file thô → file sau đè file trước trong folder
   tạm → kho nhận **2 bản y hệt** (md5 trùng). Dính thật `market_8/9` + `boat_9/10`
   2026-07-18; đã vá bằng cách gắn đuôi `id[:8]` vào slug, có test hồi quy.
   *Cũng lưu ý:* một SFX khớp 2 term khác nhau sẽ vào kho 2 lần dưới 2 kind (đã thấy
   `urban_street_16` = `market_6`) — đó là **trùng chéo kind**, không phải bug slug;
   muốn tránh thì đừng chạy 2 term chồng nghĩa trong cùng mẻ.

## 6. RÀ CHỒNG CHÉO (P5)

**Các tầng CÙNG QUẢN kho SFX:**

| Tầng | Có bị đụng không |
|---|---|
| `ambient/library.py` — đặt tên, biến thể, records | **KHÔNG** — tái dùng nguyên `import_from_manifest`, không đẻ đường ghi thứ hai. Đây là lý do chọn kiến trúc này. |
| `subject_rules.yaml` — bảng chủ thể→kind | **KHÔNG** — lệnh chỉ *đọc* qua `niche_kinds()` để validate. Kind lạ bị từ chối, không tự khai thêm. |
| `schedule.py` — picker chọn file lúc assemble | **KHÔNG** — chỉ thấy thêm biến thể mới, `list_variants()` regex chặt `^kind(_\d+)?\.wav$` vẫn đúng. |
| `sfx/library.py` (SFX overlay toàn cục) | **KHÔNG** — kho khác, `KINDS` khác. Lệnh này chỉ ghi vào ambient per-niche. |
| Luật pool nhạc theo niche | **KHÔNG** — đây là SFX, luật đó chỉ quản nhạc. Memory `music-pool-theo-niche` ghi rõ *"SFX dùng chung giữa niche ĐƯỢC"*. |

**Luật mới có ngược chiều tầng cũ không?** Không. Lưới loài CÙNG CHIỀU với quyết định
"tách kind theo loài" (memory `sfx-animal-wildlife-do-phan-giai-loai`) — cả hai đều
chống một rổ trộn nhiều loài.

**Tầng nào có thể ÂM THẦM LẬT quyết định của tầng mới?** Một chỗ đáng lưu ý:
`sfx/library.py::list_variants()` dùng **glob lỏng** `{kind}*.wav` nên kind có tiền tố
trùng sẽ nuốt nhau. Nhưng `ambient/library.py` (kho mà lệnh này ghi vào) dùng **regex
chặt**, nên không dính. Chỉ cần nhớ nếu sau này làm bản cho SFX overlay toàn cục.

## 7. TEST THẬT — RD-89 "Oman" (life-in, 291 beat)

Project `content-english-20260715-063548`. Dựng 2 bản để so cổng TAI:

| Draft | Cờ | SFX Epidemic |
|---|---|---|
| `..._V4` | (mặc định, BẬT) | **23 / 115 lượt (20%)** — 6 kind |
| `..._V5` | `--no-epidemic` | **0 / 115** — chỉ kho cũ |

**BÀI HỌC chọn kind:** mẻ đầu tôi nạp theo *"kho mỏng nhất"* (penguin/vulture/crow/
snowmobile/ski/escalator) → **0/115 lượt dùng**, vì bài Oman không có cảnh nào cần
chúng. Phải xem `subject_sfx_log` của project xem bài THỰC SỰ dùng kind gì rồi mới nạp:
`urban_street` (51), `wind` (26), `boat` (11), `camel` (6), `market` (5), `flag` (4).
→ **Luật: nạp theo NHU CẦU BÀI, không theo độ mỏng của kho.**

Kind Trung Đông tìm được rất khớp bối cảnh: *"Ambience, Urban, City, Middle East,
Traffic, Car Horns, Walla"*, *"Ambience, Market, Middle East, Auctioning"*, *"Wind,
General, Desert, Swells With Sand"*.

## 8. CÒN NGỎ

- **Cổng TAI chưa qua** — user cần nghe V4 vs V5, xác nhận chất lượng MP3→WAV và độ hợp
  bối cảnh trước khi nạp mẻ lớn.
- **Nhạc chưa làm** — mới chỉ SFX. Tool `SearchRecordings`/`DownloadRecording` đã có sẵn
  trong cùng MCP server; nhạc vướng license nặng hơn (phát nền trên YouTube), nên chờ.
- **RD-89 mất nhạc 16/16 chương** — KHÔNG liên quan Epidemic: `music_plan` trỏ tới file
  nhạc không còn trong pool (kho nhạc life-in đã nạp lại đợt 2 ngày 2026-07-17, xem
  `music-pool-theo-niche`). Cần chạy lại `autoedit music <project> --niche life-in`.
  **Còn ngỏ, chưa sửa.**
- Chưa có cache search (Pexels có `search_cache`); mỗi lần chạy đều gọi API. Chưa cần
  vì mẻ SFX nhỏ, nhưng nếu nạp hàng nghìn file thì nên thêm.
