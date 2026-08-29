# NHẬT KÝ TỐC ĐỘ PIPELINE — dữ liệu để tối ưu

> Mục đích: ghi thời gian + tốc độ từng bước MỖI video để sau vài video tìm ra nút cổ chai
> và cách tối ưu. Mỗi video 1 section. Cột "scales-with" = đại lượng bước đó tỉ lệ theo
> (dùng để dự đoán + so sánh video khác độ dài). Máy: Windows (CPU 16 luồng), kho ở F:.

## Cách đọc chỉ số chuẩn hoá
- **realtime factor** = thời-lượng-video ÷ thời-gian-bước. >1 = nhanh hơn thời lượng thật; <1 = chậm hơn.
- **s/beat**, **s/phút-video**, **s/cảnh**, **ms/từ** = tốc độ đơn vị, so được giữa video khác cỡ.
- Nút cổ chai xét theo **% tổng thời gian máy**.

---

## VIDEO #1 — SP1-017 "Edge of the Universe" (2026-07-12) — BASELINE

**Kích thước bài:** voice 2097s (34:57 = 34,95′) · 4744 từ · 11 chương · **324 beat** ·
236 segment + 25 hình thở · 344 footage vào draft. Đường đạo diễn = **L2b sâu, fan-out 11 agent**.
REF: 5 video mẫu → **873 cảnh** ingest (viral). Draft: `SP1_017_EDGE_OF_THE_UNIVERSE_20260711_233818`.

### Bảng thời gian + tốc độ từng bước

| # | Bước | Thời gian | % tổng | Tốc độ chuẩn hoá | Scales-with | Ghi chú |
|---|---|---:|---:|---|---|---|
| 1 | Ghép 8 voice → 1 | 1s | 0,0% | 2097s out / 1s (ffmpeg -c copy) | #file voice | không transcode |
| 2 | new (tạo project) | ~0s | 0,0% | — | — | chỉ ghi project.json |
| 3 | **align** | **334s** | 1,5% | realtime **6,28×** · 9,6 s/phút-video · 70 ms/từ | **độ dài audio** | faster-whisper small, CPU 16 luồng, beam 1; nội suy 2,5% |
| 4 | **library-ingest** (5 mẫu) | **1547s** | 7,0% | **1,77 s/cảnh** (873 cảnh) | **#cảnh REF** | GLM vision qua mạng; 2 fail; ĐỘC LẬP độ dài video |
| 5 | direct-context | 1s | 0,0% | — | — | xuất transcript+bảng+kho |
| 6 | **đạo diễn 11 agent** | **222s** (wall) | 1,0% | wall 0,69 s/beat · **compute 1460s** = 4,5 s/beat · ~509k token | **#chương / #beat** | 11 agent SONG SONG; wall = agent lâu nhất (Ch7 222s); nếu chạy tuần tự = 1460s |
| 6b | ghép+sửa lỗi+direct-ingest | ~120s | 0,5% | — | — | 3 lớp lỗi (route/query>4/beat>10s) sửa python 1 lượt; ingest $0 API |
| 7 | **cut** | **25s** | 0,1% | realtime **84×** · 0,077 s/beat · 0,7 s/phút-video | **#segment** | ffmpeg cắt WAV + snap lặng + hình thở |
| 8 | **source --ref** 🔺 | **18556s** | **84,4%** | realtime **0,113×** (chậm 8,85× thời lượng) · **57,3 s/beat** · 531 s/phút-video | **#beat** | NÚT CỔ CHAI. Phễu NÃO chấm 1 call/beat qua Claude Code subprocess + tải footage + normalize |
| 9 | **assemble** | **1297s** | 5,9% | realtime **1,62×** · 4,0 s/beat · 37 s/phút-video | **#beat / #overlay** | pycapcut ráp + render chart/graphic + 41 overlay + 41 SFX + nhạc 11 chương + ambient + drone + Ken Burns 8 ảnh |
| 10 | report | 1s | 0,0% | — | — | chỉ đọc project.json |
| | **TỔNG (compute máy)** | **~21983s ≈ 6h06′** | 100% | ~10,5× thời lượng video | | align+ingest chạy song song thật → tiết kiệm ~334s so bảng |

### Nút cổ chai + hướng tối ưu (giả thuyết, kiểm sau vài video)
1. **source = 84% tổng (57,3 s/beat).** Nguyên nhân: phễu NÃO chấm **1 call Claude Code/beat** (324 call tuần tự).
   Hướng thử: (a) chấm SONG SONG nhiều beat (batch/parallel như đạo diễn) — tiềm năng giảm mạnh nhất;
   (b) `--no-rank` heuristic cho beat "dễ" (kho rõ ràng) chỉ NÃO chấm beat khó; (c) cache/nhóm beat cùng query.
2. **library-ingest 1,77 s/cảnh** — chỉ chạy 1 lần/bộ mẫu, độc lập độ dài video; ít ưu tiên. GLM quốc tế đã nhanh.
3. **assemble 22′** — render chart/graphic + normalize footage. Có thể normalize SONG SONG lúc source (tải xong normalize luôn).
4. **align 6,28× realtime** — ổn; nếu cần nhanh dùng model nhỏ hơn/GPU.
5. **đạo diễn fan-out** đã tối ưu (song song 222s thay vì 1460s tuần tự / thay `direct` claude -p dễ timeout chương dài).

### Sự cố ảnh hưởng thời gian (loại khi so sánh)
- assemble timeout foreground 2′ (mốc tool) → phải chạy nền; 1 file Pexels download đứt (b055) phải normalize lại tay (~5s).
- 3 lớp lỗi ingest phải sửa (agent hay nhầm). Các lần sau nếu siết prompt agent sẽ bớt vòng sửa.

### Công thức dự đoán thô (từ baseline này, kiểm lại ở video #2+)
- align ≈ **0,16 × thời-lượng-audio(s)**
- library-ingest ≈ **1,8 s × #cảnh-REF** (chỉ khi có mẻ mẫu mới)
- source ≈ **57 s × #beat**  ← chi phối tổng
- assemble ≈ **4 s × #beat**
- Tổng (không kể ingest) ≈ **~62 s × #beat** + 0,16×audio. Vd 324 beat → ~5,6h.

### Phụ lục A — library-ingest từng video mẫu (SP1-017)
| Video mẫu | Cảnh (dry-run) | Thời gian | s/cảnh |
|---|---:|---:|---:|
| The-Edge-of-the-Universe-A-Journey (HVb) | 386 | 615s | 1,59 |
| The-Anomaly-at-the-Edge (nCe3) | 205 | 481s | 2,35 |
| What-Is-Beyond-The-Edge (IkaetPoBZM) | 168 | 251s | 1,49 |
| Why-Humans-Will-NEVER-Reach (urp) | 65 | 114s | 1,75 |
| The-Edge-Of-The-Universe-Is-Insane (ZLP1) | 49 | 85s | 1,73 |
| **Tổng** | **873** | **1547s** | **1,77 tb** |

### Phụ lục B — đạo diễn 11 agent (SP1-017): wall song song vs compute tuần tự
| Chương | Beat | Thời gian agent | Token |
|---|---:|---:|---:|
| HOOK | 12 | 54,9s | 37,2k |
| Ch1 | 24 | 111,3s | 42,6k |
| Ch2 | 32 | 136,8s | 46,9k |
| Ch3 | 37 | 201,5s | 52,7k |
| Ch4 | 17 | 56,7s | 38,7k |
| Ch5 | 29 | 120,3s | 45,1k |
| Ch6 | 30 | 151,3s | 48,2k |
| Ch7 | 40 | 221,8s | 56,7k |
| Ch8 | 28 | 126,6s | 46,3k |
| Ch9 | 37 | 134,7s | 47,2k |
| Ch10 | 28 | 144,4s | 47,8k |
| **Tổng** | **314*** | **compute 1460s / wall 222s** | **~509k** |

*314 beat lúc agent trả (sau ghép+tách+gộp <1,5s = 324→ingest chốt 324). Song song tiết kiệm 6,6× (1460→222s).

### Ghi khi chạy VIDEO #2 (checklist thu số)
Mỗi lệnh bọc `start=$(date +%s); <lệnh>; echo $(( $(date +%s)-start ))`. Thu: độ dài audio · #từ ·
#chương · #beat · #cảnh-REF · thời gian 10 bước · #call rank source · token đạo diễn · sự cố phát sinh.
So s/beat của source + assemble với baseline 57,3 / 4,0 để xác nhận công thức.

---

## VIDEO #2 — DS5-083 "Ocean Without Sharks" (2026-07-13) — DEEPSEA, xác nhận công thức

**Kích thước bài:** voice 1660s (27:40 = 27,67′) · 3519 từ · 9 chương · **270 beat** (đạo diễn 274 →
gộp 270) · 43 hình thở · 405 footage đo màu. Đường đạo diễn = **L2b sâu, fan-out 9 agent song song**.
REF: 13 video mẫu DS083 → **~1629 cảnh** ingest (viral, kho deepsea 8989→10.618). Music-sync BẬT.
Draft: `DS5_083_OCEAN_WITHOUT_SHARKS_20260713_030358`.

### Bảng thời gian + tốc độ từng bước

| # | Bước | Thời gian | Tốc độ chuẩn hoá | So baseline SP1-017 |
|---|---|---:|---|---|
| 1 | Ghép 7 voice → 1 | ~1s | ffmpeg -c copy | = |
| 3 | **align** | **243s** | realtime **6,83×** · 8,8 s/phút-video · 69 ms/từ | 69 vs 70 ms/từ ✓ (0,146×audio) |
| 4 | **library-ingest** (13 mẫu) | **4278s** (71′) | **~2,6 s/cảnh** (~1629 cảnh) | chậm hơn 1,77 (nhiều draft nhỏ + zoom 112% + yt-dlp bị chặn retry) |
| 5 | direct-context | 1s | — | = |
| 6 | **đạo diễn 9 agent** | **wall ~426s** (agent ch9 lâu nhất) · **compute ~1980s** | 9 agent SONG SONG; ~713k token | song song tiết kiệm ~4,6× |
| 6b | normalizer + direct-ingest (2 vòng) | ~150s | vòng 1: 125 lỗi (query>4/breath range/beat>10s/entity-route/overlay len/graphic half) sửa python; vòng 2 PASS | nhiều lỗi hơn baseline (agent drift schema ch2-5) |
| 7 | **cut** | **90s** | realtime **18×** · 0,33 s/beat | chậm hơn 0,077 (nhiều segment nhỏ + hình thở) |
| — | music-sync (stage music) | 1s | 9 chương neo mood, 6 accent/downbeat | MỚI (music-sync BẬT) |
| 8 | **source --ref** 🔺 | **7032s** (117′) | realtime **0,236×** · **26,0 s/beat** · 254 s/phút-video | **NHANH GẤP 2,2× baseline** (57,3→26,0 s/beat) |
| 9 | **assemble** | **1206s** (20′) | realtime **1,38×** · 4,5 s/beat | 4,5 vs 4,0 s/beat ✓ (music-sync thêm M-VOL/M-ACCENT/M-CHANGE) |
| 10 | report | 1s | — | = |
| | **WALL-CLOCK align→report** | **~4h00′** | ~8,7× thời lượng video | ingest+align song song |

### Phát hiện tốc độ (xác nhận + cập nhật công thức)
1. **source 26,0 s/beat — NHANH GẤP 2,2× baseline 57,3.** Nguyên nhân đo được: kho deepsea RẤT giàu
   (10.618 asset, kho thắng 104 pick / 227 beat có ứng viên kho) → nhiều beat pick LOCAL, KHÔNG tải Pexels
   + không normalize file mới. **Công thức source phụ thuộc ĐỘ PHỦ KHO, không chỉ #beat.** Kho dày → source rẻ.
2. **assemble 4,5 s/beat ≈ baseline 4,0** — xác nhận công thức; music-sync (M-VOL/M-ACCENT snap 40 mép/M-CHANGE 8) thêm ~0,5 s/beat.
3. **align 69 ms/từ ≈ baseline 70** — công thức align chắc (0,146×audio).
4. **library-ingest 2,6 s/cảnh > baseline 1,77** — 13 draft nhỏ (overhead mở/đọc mỗi draft) + yt-dlp bị YouTube
   chặn bot (retry timeout mỗi video) + zoom 112% nướng. Ingest vẫn độc lập độ dài video, chỉ chạy 1 lần/bộ mẫu.
5. **source vẫn là nút cổ chai wall-clock (49%)** nhưng đã tự giảm mạnh nhờ kho dày — củng cố hướng "kho local càng dày, source càng rẻ".

### Sự cố ảnh hưởng thời gian (loại khi so sánh)
- **Bug stdin heredoc:** subprocess `uv run` nuốt stdin vòng `while read` → draft mẫu chạy lộn thứ tự/ăn mất
  tiền tố tên. Fix: đọc list trên FD3 (`done 3< file`) + `</dev/null` mỗi subprocess. Mất ~2′ dò + chạy lại (resume nên không mất công ingest).
- **Agent drift schema** (ch2,3,4,5 dùng `visual_anchor` string / `visual_level` "broad/establishing" / overlay `type`/`word`):
  normalizer python coerce hết (1 vòng). Ch1,6,7,8,9 (block schema nghiêm ngặt trong prompt) trả ĐÚNG → bài học: prompt agent PHẢI có block "SCHEMA BẮT BUỘC" liệt kê enum/bool/key.
- Beat >10s không có pause thật giữa: normalizer tách tại từ giữa-thời-gian (silence-snap lo mép cắt).

### Cập nhật công thức dự đoán (2 điểm dữ liệu)
- align ≈ **0,145 × audio(s)** (SP1 0,159 · DS 0,146 — dùng ~0,15)
- source ≈ **26–57 s × #beat** — BIÊN ĐỘ RỘNG theo độ phủ kho (kho nghèo→57, kho giàu→26). Không dự đoán bằng #beat đơn thuần.
- assemble ≈ **4–4,5 s × #beat**
- CỔNG TAI CHƯA QUA: music-sync deepsea (M-VOL hook 0.3 tới 154s + M-CHANGE xfade 0.5s) — user nghe draft kiểm.

---

## 2026-07-15 — GÓI TĂNG TỐC TOC-1..4 ĐÃ VÀO CODE (chờ video #3 đo)

Mổ số 3 bài: NÃO **viết output** ≈78% source DS5-083 (43-57 call tuần tự × 10-12k tok out;
50-65% output = echo asset_key path 165 ký tự). Đã code (pytest 526/526, chi tiết
`MO_TA_VAN_HANH_TOC_DO_SOURCE.md`): TOC-1 id ngắn crc32 · TOC-2 3 call song song
(knob `AUTOEDIT_RANK_PARALLEL`) · TOC-3 normalize nền trong source (knob `AUTOEDIT_PRENORM`)
· TOC-4 perf tự ghi vào `project.json::stages.*.started_at/perf` — **HẾT bấm giờ tay.**

**Video #3 trở đi, đọc số tại `stages.source.perf`:** kỳ vọng `rank_call_s` giảm nửa
(token out ~10,3k→4-5k/call) · `rank_wait_s` ≪ `rank_call_s` (lookahead ăn) ·
warning "TOC-3 normalize nền: N asset" · assemble 20′→5-8′.

**TOC-3b tải song song ĐÃ LÀM LUÔN cùng ngày** (user chốt, 10 key Pexels): warm-up
top-pick sau verdict, 4 luồng, khóa theo đích, `dl_reuse` đo tỉ lệ trúng (kỳ vọng
≥60-70%). Dự đoán cộng dồn: source DS5-cỡ 117′→~25-35′ · SP1-cỡ 5h09′→~40-55′.
pytest 529/529.
