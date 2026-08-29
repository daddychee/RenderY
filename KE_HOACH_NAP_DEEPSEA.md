# KẾ HOẠCH NẠP NICHE DEEPSEA — sổ theo dõi xuyên phiên

> **Mục đích file này:** Claude Code sau khi /clear đọc file này là chạy tiếp được ngay,
> không cần hỏi lại. Cập nhật bảng trạng thái SAU MỖI draft xong. User nhắc "chạy tiếp
> deepsea" = mở file này → làm mục 🔄 đầu tiên chưa xong.

## Quyết định đã chốt (user, 2026-07-12 + bổ sung 2026-07-13)

4. **Nhạc editor: BỎ cổng tai, máy tự gán mood từ tên** (user chốt 2026-07-13: "editor đã
   lựa chọn kỹ") — 90 bài staging → pool `~/AutoEdit/music/tracks` tên `__mood`
   (script map: `scratchpad/stage_music_deepsea.py`, đã lưu logic vào sổ này); tên
   số/mơ hồ (1-7.mp3, "2 3 được") → mood `mysterious` (prior deepsea).
5. Video kiểm (bước 10) làm SAU khi xong nhạc — user sẽ đưa input.

## Quyết định gốc (user, 2026-07-12)

1. Nguồn: 3 folder editor công ty — `E:\PROJECT NHAN BAN\DEEPSEA 1`, `...\DEEP SEA 5`,
   `...\DEEP SEA 3`. **TẤT CẢ là `own`** (không trần 8%, không gate kề — luật own-vs-viral).
2. **Máy TỰ SINH title + chapter từ voice** (transcribe → Claude) → ghi file
   `topic + chapter video.txt` vào folder draft. User KHÔNG duyệt từng cái — chạy tự động.
3. Chạy theo mẻ, ghi sổ này để resume sau /clear. Draft nguồn CHỈ ĐỌC (trừ việc ghi thêm
   file TCF vào folder — user đồng ý vì đó là spec TCF chuẩn).

## Khảo sát 2026-07-12 (đã xong)

- 27 folder con → **25 draft hợp lệ** đưa vào pipeline:
  - `DS1-042` RỖNG (không draft_content.json) → loại.
  - `DS1_067_v2-Spain` = bản sao MD5 y hệt `DS1_067_v2` → loại.
- Tổng ~902 phút video (~15h). Nghi vấn — TÌNH TRẠNG SAU MẺ TCF 2026-07-12:
  - `DS-53 v2` vs `DS1-053`: CHƯA quyết được — cả 2 fail bẫy placeholder trong mẻ đầu, chạy lại bằng code đã fix rồi so title.
  - `DS1_046` (Sperm Whale) vs `DS1_049` (Anglerfish): topic KHÁC NHAU → GIỮ CẢ HAI. ✅ đóng nghi vấn.
  - `DS1_048`: meta ghi 2,9′ nhưng transcript thật 33:32 (Colossal Squid) — meta sai/stale, video ĐẦY ĐỦ → GIỮ. ✅ đóng nghi vấn. (Bài học: tm_duration meta không tin được, tin transcript.)
  - `DS1_074`: ⛔ HOÃN — draft kiểu "Clip ghép" (compound): timeline chính chỉ 2 clip gộp path rỗng, 0 audio; nội dung thật trong 10 subdraft con. Xử riêng nếu user muốn (~4% dữ liệu, không đáng build compound-support bây giờ). Ingest cũng sẽ dính y bẫy này → bỏ luôn khỏi danh sách ingest.

## Trình tự pipeline (mỗi bước xong → cập nhật bảng + đánh dấu)

| # | Bước | Lệnh / việc | Trạng thái |
|---|---|---|---|
| 0 | Khảo sát folder | (xong, kết quả ở trên) | ✅ 2026-07-12 |
| 1 | `library-init deepsea` + điền `niche_profile.yaml` | xong — profile đã điền (safe_pool/audience_bias deepsea) | ✅ 2026-07-12 |
| 2 | Build lệnh `tcf-gen` | XONG: `autoedit/library/tcf_gen.py` + lệnh CLI `tcf-gen`; 5 pytest mới, full suite 434 pass. Bẫy đã xử: material `name` ≠ file đĩa → resolve theo basename `path`; NÃO chỉ chọn mốc block cho sẵn, lệch >1 block = bỏ (NT4); transcript <200 từ = lỗi rõ không sinh mù | ✅ 2026-07-12 |
| 3 | Chạy tcf-gen 25 draft | XONG: **24 draft có TCF** (21 mẻ chính + DS1-050 + 2 placeholder chạy lại sau fix 60954cf; DS1_074 compound fail). Title chuẩn, user chưa cần duyệt (chốt tự chạy) | ✅ 2026-07-12 |
| 4 | Rà title trùng → chốt danh sách ingest cuối | XONG: **danh sách ingest = 23 draft** (24 TCF − DS1-053 cùng tập DS-53 v2). 3 cặp trùng CHỦ ĐỀ khác kênh (Sperm Whale/Orca/Creepier) = remake, GIỮ CẢ | ✅ 2026-07-12 |
| 5 | Ingest từng draft (nền) | ✅ **ĐÓNG 2026-07-13: kho deepsea 8.981 asset / 23 draft** (8.994 cảnh cắt = 99,85%). Mẻ chính 8.686 + retry vớt 295 sau khi **map 12 mood tài liệu vào `_MOOD_SYNONYMS`** (educational 151 + creepy 105... — tiền lệ PB4). Fix ingest path chết `D:/`→`materials/<basename>`. CÒN NGỎ 13 lỗi lì (0,15%): 2 jpg + 3 combination + 2 Artlist .mov hỏng thật · 4 clip cắt không rút frame (orphan trong nap/, KHÔNG vào db — vô hại) · 1 GLM lì + 1 contentFilter 1301 (tag tay nếu cần, tiền lệ PB9) | ✅ 2026-07-13 |
| 6 | DNA pacing + nhịp nghỉ | ✅ **ĐÓNG 2026-07-13** (cả 23 draft, commit riêng): `dna.json` — 11,9 cut/ph · shot p50 4,63s · hold 45% · close-up 20% (KHÁC HẲN space 9,4/6,2s/67%/2,5% — DNA per-niche trả công); `pause_dna.json` — kết câu 4,2/ph nghe-ra p50 2,41s · chèn +20,3% · hình thở p50 2,76s (167 ô đo được, anchors đủ). Kèm thống nhất resolver voice: `voice_files_of` map theo path đĩa, `make_whisper_words` nhận rel path — pause-dna hết mù draft editor lệch name↔file; cache TCF dùng lại 100% (0 transcribe mới). Whisper-only (không script gốc) — kém chính xác hơn space chút, chấp nhận | ✅ 2026-07-13 |
| 7 | editor-learn từng draft (luật đứng) | ✅ **ĐÓNG 2026-07-13**: 23/23 draft 0 lỗi (vá `mine.py::resolve_media` fallback basename path). Mót: 48 ambient + 27 sfx + 90 nhạc + 323 hold; **import xong: 57 ambient (ocean 27!) + 28 SFX vào kho deepsea** (1 wav hỏng bỏ); rerun DS1-050 = 0-mới ✅; backup D: refresh. DNA âm cộng dồn 23+5 draft, số máy giữ nguyên (báo-cáo-only). **90 nhạc ở staging `F:\AutoEdit\music_editor\<draft>\` CHỜ CỔNG TAI user** — nghe duyệt rồi mới music-import vào pool | ✅ 2026-07-13 |
| 8 | Ambient deepsea | ✅ **GẦN NHƯ TỰ ĐÓNG nhờ bước 7** — editor-learn mót đủ bộ underwater/ocean/rumble/sonar từ chính draft editor (13 kind, ocean 27 file). User CHỈ bổ sung nếu thấy thiếu khi nghe video kiểm | ✅ 2026-07-13 |
| 9 | Nhạc editor vào pool (thay cổng tai — user chốt 2026-07-13) | ✅ **ĐÓNG 2026-07-13**: 90 bài máy gán mood từ tên → **89 vào pool (tổng 128 bài/18 mood**; dark 21 · mysterious 33 · dreamy 31 — đúng phổ deepsea); 1 bài "The Light Within b" bị lọc vocals ĐÚNG THIẾT KẾ (cùng 3 bài cũ trước giờ). Backup D: XONG 0 FAILED (library +10.038 file/54,7GB · ambient +440 · music_editor +90 · AutoEdit_C +151 gồm cả nhạc mới + cache.db — robocopy exit 1 = thành công có copy) | ✅ 2026-07-13 |
| 10 | Bàn routing entity deepsea + 1 video kiểm cổng mắt → mới scale | Đề xuất đã gửi user (facts-niche 3-8 entity; entity ảnh thật dành cho tàu lặn/người/sự kiện, SINH VẬT để kho local vì vision phân biệt loài tốt — bằng chứng db: sperm whale 282 ≠ blue whale 228 ≠ orca 75; colossal 167 ≠ vampire 158 ≠ giant squid 114). User chốt: LÀM SAU — chờ user đưa script+voice | ⏸ CHỜ USER |

## Bảng trạng thái 25 draft

Cột: **TCF** (sinh title+chapter) / **ING** (ingest kho) / **EL** (editor-learn).
Ký hiệu: ✅ xong · ❌ lỗi (ghi chú) · ⏸ chưa · ⛔ loại.

| Draft | Phút | TCF | ING | EL | Ghi chú |
|---|---|---|---|---|---|
| DEEPSEA 1\DS1-050 | 28,9 | ✅ | ⏸ | ⏸ | title "Every Layer of the Ocean Has a Stranger Squid...", 10 ch |
| DEEP SEA 5\DS-53 v2 | 44,2 | ✅ | ⏸ | ⏸ | "The Octopus: Earth's Other Intelligence" 12 ch |
| DEEP SEA 5\DS1-053 | 44,2 | ✅ | ⛔ | ⛔ | CÙNG TẬP DS-53 v2 (cùng 43:40, cùng bài Octopus) → chỉ ingest bản v2 |
| DEEP SEA 5\DS1_046 | 38,6 | ✅ | ⏸ | ⏸ | "The Sperm Whale: Earth's Largest Brain..." 13 ch |
| DEEP SEA 5\DS1_048 | 33,5 thật | ✅ | ⏸ | ⏸ | "The Colossal Squid: 100 Years of Hunting..." 11 ch (meta 2,9′ SAI) |
| DEEP SEA 5\DS1_049 | 38,6 | ✅ | ⏸ | ⏸ | "The Anglerfish: ...Broke Every Rule of Biology" 13 ch |
| DEEP SEA 5\DS1_051 | 42,8 | ✅ | ⏸ | ⏸ | "Why Every Squid Gets Creepier The Deeper You Go" 12 ch |
| DEEP SEA 5\DS1_053 → xem DS1-053 | | | | | |
| DEEP SEA 5\DS1_056_v2 | 43,4 | ✅ | ⏸ | ⏸ | "Why the Mariana Trench Dissolved Every Monster..." 14 ch |
| DEEP SEA 5\DS1_059 | 46,6 | ✅ | ⏸ | ⏸ | "The Blue Whale: The Most Powerful Animal..." 13 ch |
| DEEP SEA 5\DS1_063 | 37,7 | ✅ | ⏸ | ⏸ | "The Challenger Deep: What's Actually Living 7 Miles Down" 12 ch |
| DEEP SEA 5\DS1_067_v2 | 44,5 | ✅ | ⏸ | ⏸ | "The Great White Shark: Everything You Know Is Wrong" 13 ch |
| DEEP SEA 5\DS1_067_v2-Spain | 44,5 | ⛔ | ⛔ | ⛔ | MD5 trùng DS1_067_v2 |
| DEEP SEA 5\DS1_069 | 34,3 | ✅ | ⏸ | ⏸ | "The Orca: The Second Smartest Mind in the Ocean" 12 ch |
| DEEP SEA 5\DS1_074 | 37,3 | ⛔ | ⛔ | ⛔ | Clip ghép/compound — hoãn (xem nghi vấn) |
| DEEP SEA 5\DS5_001 | 60,3 | ✅ | ⏸ | ⏸ | "Inside the Mariana Trench: Creatures, Geology..." 11 ch |
| DEEP SEA 5\DS5_002 | 52,9 | ✅ | ⏸ | ⏸ | "The Octopus: A Mind Built Completely Different..." 12 ch |
| DEEP SEA 5\DS5_005 | 22,2 | ✅ | ⏸ | ⏸ | "Point Nemo: The Most Lifeless Place on Earth..." 8 ch |
| DEEP SEA 3\DS3_003 | 22,8 | ✅ | ⏸ | ⏸ | "The Octopus Has 9 Brains — And Each One Thinks..." 9 ch |
| DEEP SEA 3\DS3_004 | 27,4 | ✅ | ⏸ | ⏸ | "The Deep Sea Giants Science Never Expected to Find" 9 ch |
| DEEP SEA 3\DS3_006 | 48,2 | ✅ | ⏸ | ⏸ | "Mosasaurus vs Blue Whale: Who Would REALLY Rule..." 11 ch |
| DEEP SEA 3\DS3_007 | 30,8 | ✅ | ⏸ | ⏸ | "Orcas: The Most Intelligent Apex Predator..." 8 ch |
| DEEP SEA 3\DS3_008 | 47,0 | ✅ | ⏸ | ⏸ | "Why Deep Sea Animals Get Creepier The Deeper You Go" 12 ch |
| DEEP SEA 3\DS3_010 | 27,7 | ✅ | ⏸ | ⏸ | "The Giant Oarfish: Deep-Sea Giant That Predicts Earthquakes?" 10 ch |
| DEEP SEA 3\DS3_011 | 26,9 | ✅ | ⏸ | ⏸ | "The Real Megalodon: What 2025 Science Reveals..." 9 ch |
| DEEP SEA 3\DS3_017 | 27,0 | ✅ | ⏸ | ⏸ | "The Sperm Whale: Master of the Deep Ocean" 11 ch |
| DEEP SEA 3\DS3_023 | 24,8 | ✅ | ⏸ | ⏸ | "The 19-Meter Ocean Predator That Was Smarter Than Your Dog" 10 ch |

⚠ Trùng chủ đề KHÁC KÊNH (không phải trùng tập — GIỮ CẢ, chỉ ghi nhận): DS1_051 vs DS3_008
("...Creepier The Deeper You Go" bản squid vs bản deep sea animals); DS1_046 vs DS3_017
(Sperm Whale ×2); DS1_069 vs DS3_007 (Orca ×2). Kênh DS1/DS3/DS5 là các kênh khác nhau
làm lại chủ đề — bình thường với hệ nhân bản.
| DEEP SEA 5\DS1-042 | — | ⛔ | ⛔ | ⛔ | folder rỗng |

## Thiết kế lệnh `tcf-gen` (bước 2)

- CLI: `uv run autoedit tcf-gen "<draft_dir>" [--language en] [--force]`
- Luồng: đọc `draft_content.json` → `voice_files_of()` lấy segment voice + map
  file-time↔timeline-time → `make_whisper_words()` transcribe (cache
  `<library>/deepsea/pause_scan_cache/` — pause-dna bước 6 DÙNG LẠI cache này, không tốn 2 lần)
  → ghép transcript theo TIMELINE → 1 call Claude (claude -p, temp 0, structured output):
  title 1 dòng + 4-10 chapter `M:SS Tên` (mốc TIMELINE, chapter đầu 0:00) → ghi
  `topic + chapter video.txt` (format ingest.py đã parse được, spec TCF).
- Có file TCF rồi → skip (trừ --force). KHÔNG đụng gì khác trong draft (P3).
- NT4 giữ nguyên: timestamp chapter lấy từ whisper words (căn theo câu mở đoạn), LLM chỉ
  chọn Ý NGHĨA chia đoạn ở từ nào — không tự bịa số.

## Điểm ngỏ / rà chồng chéo (P5)

- **Bước 6 pause-dna SẼ DÍNH lại 2 bẫy voice** (name≠đĩa + placeholder): `pause_scan.
  make_whisper_words` tìm `materials/<name>` — với draft deepsea phải truyền custom
  WordsFn (`scan_draft` nhận param `get_words`) dựa trên `tcf_gen.make_words_fn` +
  map material_id→rel path kiểu `_resolve_rel`. Cache transcribe ĐÃ CÓ SẴN từ bước 3
  (key basename khớp) — không tốn transcribe lại.
- **Bước 7 editor-learn**: rà xem mine.py resolve path audio kiểu nào trước khi chạy
  (nghi cùng bẫy path chết D:/).

- **Nhạc pool CHUNG mọi niche** — điểm lệch-vị duy nhất đã rà 2026-07-10; editor-learn
  deepsea nạp nhạc vào staging, user nghe duyệt; tai chê mới tách pool.
- **DNA fail-open**: chưa có dna deepsea thì direct-context rơi về không-khối (không lây
  số space) — an toàn, nhưng bước 6 xong mới dựng video kiểm.
- **tcf-gen ghi file vào folder draft nguồn** = ngoại lệ duy nhất của "draft nguồn chỉ đọc",
  đúng spec TCF, user đã đồng ý 2026-07-12.
- Ước lượng chi phí: transcribe GPU ~1-1,5h · GLM tag ~2,3h/~$0.9 · Claude 25 call ngắn.
