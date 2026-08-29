# MÔ TẢ VẬN HÀNH — FOOTAGE THẬT TRONG ĐOẠN CHÈN Δ (M4c + M4d)

> User chốt 2026-07-21: nguồn **LAI** — clip folder editor đưa dùng TRƯỚC, thiếu thì
> **KHO đắp bù theo PROMPT editor khai** (không tự suy từ chương); cỡ cảnh do GLM tag.
> Thay slug giữ chỗ của M2/M4b bằng clip thật, lưới nhịp V12 đã duyệt GIỮ NGUYÊN 100%.
> Sửa kèm tồn đọng M3 #1 (`timeline_accents`/`timeline_beats` chưa biết span Δ).
> **M4d cùng ngày (user chốt sau cổng V13):** ① CỔNG LOCATION cho kho đắp bù (V13 dính
> clip Vietnam/Bosnia/Djibouti trong bài Oman) ② folder **`HINH THO`** trong mẻ video
> mẫu = footage editor dành riêng cho Δ/mini-hook.

## 1. Editor dùng thế nào

```
autoedit insert <project> --after-beat N --dur S --music <file>
    --footage <folder>     # clip editor cho Δ (video/ảnh, không cần quy ước tên)
    --prompt "chọn các footage thiên nhiên hùng vĩ liên quan Oman và hình ảnh phụ nữ"
```

### 1b. Folder video mẫu có `HINH THO` (M4d — cách chuẩn từ nay)

```
F:\LIFE IN\VIDEO MAU\RD89\          ← khai qua `source --ref` như mọi mẻ mẫu
├── CHAPTER 1\ CHAPTER 2\ ...       ← REF theo chương (VD2, như cũ)
└── HINH THO\                       ← DÀNH RIÊNG Δ + mini-hook (M4d)
    ├── chapter 1\  chapter 5\      ← footage cho Δ sau chương 1 / chương 5
    ├── Mini Hook\                  ← để dành tính năng mini-hook đầu video (chưa tiêu thụ)
    └── <file ở gốc / folder khác>  ← "chung": mọi Δ dùng được
```

- Video nguồn **xếp vào folder TRƯỚC khi làm draft tách cảnh** (sổ khớp theo
  `source_video` — bẫy cũ của REF theo chương, vẫn áp nguyên).
- Nạp mẻ như thường (`library-ingest <niche> <draft> --source-class viral`) — LUẬT TỰ NẠP.
- Cảnh HINH THO bị **tước chèn REF + bonus ở mọi beat thường** (`ledger.ref_excludes`,
  mềm: search thường vẫn chấm được, trần 15% giữ cả mẻ — không đẻ cửa loại).
- `ref_chapter_scan` đếm cảnh HINH THO vào key riêng `hinh_tho` (không phồng số "chung").

- **Lúc khai** (fail fast, cùng triết lý nhạc M3): folder copy vào `media/insert/`
  (prefix crc8 chống đè trùng tên — họ bug F6) + GLM tag cỡ cảnh từng file;
  prompt được NÃO dịch thành 2-6 query tiếng Anh khớp vocab tag kho (C4), in ra ngay.
  NÃO lỗi → kho đắp bù TẮT (ô thiếu giữ slug), khai lại để thử lại.
- **Khai lại cùng beat = SỬA toàn bộ** — phải khai lại cả `--footage`/`--prompt`.
- Chạy lại chuỗi như cũ: cut → music → source → assemble.

## 2. Máy làm gì (3 tầng)

1. **Lưới** — `cov.insert_grids(project)`: dời logic mốc+seed từ assembler về MỘT chỗ,
   source và assemble cùng gọi → số ô/mốc hai tầng tự khớp. Lưới V12 không đổi 1 ms.
2. **SOURCE** — `sourcer/insert_fill.py::pick_insert_footage` (chạy SAU pick beat/thở,
   `used_in_video` đầy đủ): tính ô + cờ HOLD (`insert_hold_flags`, luật A′ dur ≥1,5×
   trung vị — cùng hàm với ảnh slug hold). **Ưu tiên 4 tầng:**
   ① clip `--footage` (editor đưa tay cho đúng Δ này) → ② **HINH THO** của mẻ --ref
   (đúng-chương-Δ xếp trước "chung"; KHÔNG đụng chương khác/Mini Hook; trong pool xếp
   scene CHẴN trước LẺ — 2 pick liên tiếp không kề nhau trong video nguồn, giảm rủi ro
   "kề" bản quyền) → ③ kho theo query prompt **qua CỔNG LOCATION** → ④ slug.
   Mỗi tầng cùng bậc gán cỡ cảnh: HOLD←wide/aerial, RUN←close/medium, 4 nấc + quét vét.
   Tầng ①② editor tự chọn nên **miễn cổng location**; pick từ sổ (②③) log usage P7.
   Ghi `InsertSpec.footage_picks` theo **INDEX Ô** (không lưu mốc tuyệt đối — cut chạy
   lại timeline dịch nhưng index ổn định).

### CỔNG LOCATION (M4d) — `foreign_location` + `passes_geo`

Kho đắp bù theo prompt match CHỮ nên V13 kéo clip **Vietnam/Bosnia/Djibouti** vào bài
Oman (geo-gate PA2 chỉ gác cây "Khu Vực...", mẻ nạp `nap\EXxxx` là phi-địa-lý nên lọt).
Luật mới cho pool Δ: ứng viên mà siêu dữ liệu (source_video/folder/subject/description/
tags) nhắc **tên một QUỐC GIA script không nhắc** → loại; match theo TOKEN có đệm
("oman" ⊄ "romance", "viet nam" ⊄ "soviet name"); clip không nhãn nước → QUA (fail-open,
chỉ chặn ca chắc chắn — triết lý phễu c5). Kèm `passes_geo` cũ cho cây địa lý. Warning
in rõ số clip bị chặn + 3 tên đầu.
3. **ASSEMBLE** — cửa sổ Δ đọc pick theo index: có path → `_place_video_l1` như footage
   thường (norm C4, Ken Burns nếu ảnh); hỏng/hụt → rơi về slug. Số ô ≠ số pick (spec
   đổi sau source) → warning "chạy lại source", ô lệch giữ slug.

## 3. Sửa kèm tồn đọng M3 #1 — accent/beat biết span Δ

`timeline_accents`/`timeline_beats` (music/plan.py) trước coi chương liền mạch 1 bài;
chương mang Δ-nhạc-editor thì từ mép Δ tới hết chương bài THẬT là bài editor → accent
bài kế hoạch trong vùng đó là mốc SAI (M4c có footage + vùng sau Δ vẫn snap nên thành
hại thật). Nay hai hàm đi theo `music_spans()`: span Δ dùng **downbeat madmom /
beat+strength đo lúc khai** của bài editor (vào từ đầu bài tại mép span, P=0);
span thường giữ bất biến P y cũ. Project không Δ-nhạc → tọa độ Y HỆT (hồi quy 0, có test).

## 4. Rà chồng chéo (P5)

| Tầng cùng quản | Kết luận |
|---|---|
| Lưới Δ M4b (V11/V12 đã duyệt tai) | KHÔNG đụng — chỉ thay nội dung ô, mốc giữ nguyên từng ms (kiểm V13: 13/13 ô lệch 0,0ms) |
| Slug + sort nam châm (fix c1d88f4) | Clip thật đi cùng đường sort theo start; kiểm THỨ TỰ segment trong draft V13 tăng dần; cổng CapCut vẫn là chuẩn cuối |
| Mép Δ miễn snap/J-cut (M2) | Giữ nguyên — pick chỉ lấp nội dung, không sinh mép mới |
| Hai hệ cắt không trộn | Δ vẫn vùng không-voice = NHỊP quyết mép; prompt chỉ chọn HÌNH |
| Pacing/cuts_log/credit (loại trừ M2) | Δ vẫn NGOÀI cả ba — không đổi |
| Phễu source + P7 | Pick Δ chạy sau cùng, `used_in_video` đầy đủ nên không giành clip của beat; pick từ sổ log usage, clip editor KHÔNG log (y luật nhạc editor M3) |
| Ambient cắt trước Δ (M2) | Không đụng — Δ có nhạc chủ đạo, ambient vẫn dừng mép vào |
| REF chèn/bonus (VD2) | M4d: cảnh HINH THO bị tước chèn+bonus ở MỌI beat (`ref_excludes`) — không giành đất với REF chương; search thường vẫn chấm (mềm) |
| ViralLedger trần/kề (c8) | ⚠ Δ fill KHÔNG qua ledger — giảm nhẹ bằng xếp scene chẵn/lẻ (2 pick liên tiếp không kề trong nguồn); trần 15% chưa đếm phần Δ. CÒN NGỎ nếu Δ dài/mẻ mỏng |
| Cổng location vs phễu beat | Cổng location CHỈ áp pool Δ — phễu beat thường giữ nguyên (đã có geo-gate + NÃO chấm nghĩa), không ai lật ai |
| ⚠ CÒN NGỎ khác | Mini Hook: folder đã nhận diện + giữ riêng, tính năng chèn mini-hook đầu video CHƯA làm (user chốt để dành 2026-07-21) · 2 Δ dùng CÙNG bài nhạc editor → nghe lặp, chưa cảnh báo (tồn đọng M3 #3) |

## 5. Số đo V13 → V15 (RD89 Oman)

**V13 (M4c, trước cổng location):** Δ beat 36, 30s, 13 ô (2 HOLD): kho 13/13, 0 slug;
2 HOLD nhận aerial+wide; mốc 0,0ms. Query NÃO: oman landscape/desert/nature/mountains/
outdoor + women traditional. ❌ Cổng mắt user bác: dính clip Vietnam/Bosnia/Djibouti
→ đẻ ra M4d.

**V15 (M4d):** mẻ `F:\LIFE IN\VIDEO MAU\RD89` nạp 132 cảnh Oman documentary vào
`HINH THO\chapter 1` (video 2GB move từ Downloads + sửa path draft tách cảnh 133 chỗ
— không đụng id, luật C1). Hai Δ:
- **Δ sau beat 8 (cuối chương 1, 20s — đúng ví dụ prompt user): 9 ô (1 HOLD) =
  HINH THO 9/9**, 0 slug, mốc 0,0ms.
- **Δ sau beat 36 (chương 3, 30s): kho 13/13 qua CỔNG LOCATION — chặn 55 ứng viên**
  (Vietnam...), 0 tên nước lạ trong draft; KHÔNG rò cảnh HINH THO ch1 (fix vùng đặt
  chỗ — V14 lần đầu bị rò qua search chữ, vá + hồi quy ngay).
pytest 710/710 (+21 test_insert_footage). Giới hạn đã biết: cổng chỉ bắt TÊN NƯỚC —
địa danh không mang tên nước (Everest, vịnh Hạ Long) không bắt được; nội dung lệch văn
hóa (clip bikini match query "women") do cổng MẮT phán — chê thì nâng cấp danh sách
địa danh hoặc vision gate cho Δ.
