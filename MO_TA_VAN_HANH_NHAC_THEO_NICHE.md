# MÔ TẢ VẬN HÀNH — POOL NHẠC THEO NICHE + NẠP LẠI KHO NHẠC/SFX LIFE-IN (2026-07-17)

> User chốt 2026-07-17: **life-in CHỈ dùng nhạc của life-in, không dùng sang niche
> khác; SFX có thể dùng chung giữa niche.** Gói này: (1) luật pool nhạc theo niche,
> (2) xóa + nạp lại toàn bộ nhạc/SFX life-in từ kho editor bàn giao
> `F:\THU VIEN NHAC + SFX\LIFE IN` (5 editor: DAT, Thịnh, NAM, Điền, Tú — 522 file).

---

## 1. Luật pool nhạc theo niche (`music_root_for`)

- `F:\AutoEdit\music\<niche>\tracks\` **TỒN TẠI** → niche đó CHỈ chọn nhạc trong pool
  riêng (index/usage/overrides riêng trong folder đó). KHÔNG rơi về pool chung —
  nhạc không lẫn 2 chiều giữa niche.
- Chưa có folder riêng → pool chung `F:\AutoEdit\music\` như cũ (deepsea/space không đổi).
- Code: `music/library.py::music_root_for(niche)` — 2 nơi gọi:
  - lệnh `music` (M-STAGE): `--niche` → `project.niche` → pool chung. **Stage music chạy
    TRƯỚC source nên `project.niche` thường CHƯA có — dựng life-in PHẢI gọi
    `autoedit music <dir> --niche life-in`** (lệnh `make` đã tự truyền).
  - lệnh `assemble`: tự resolve theo `project.niche` (đã có sau source). `--music`/
    `--music-lib` tay vẫn thắng.
- Pool chung 321 bài GIỮ NGUYÊN (không xóa được "bài của life-in" — không có dấu vết
  niche trong index; deepsea/space đang sống nhờ pool đó). "Xóa nhạc life-in" = life-in
  không đụng pool chung nữa.

## 2. Kho nhạc life-in mới (`F:\AutoEdit\music\life-in\`)

- 117 file DAT + Thịnh (`__mood` trong tên) → **116 bài** (2 file "ANBR - Savage" cùng
  base gộp 1) · 4 typo sửa khi copy (`peachful`→peaceful ×2, `sirious`→serious,
  `misterious`→mysterious) · grid nhịp đủ: **tier A=105 / B=10 / C=1**.
- Tag ngoài bảng bị BỎ theo luật (báo editor): carefree, dramatic, exciting, love,
  powerful, sexy.
- **72 bài NAM KHÔNG có mood** → `staging_cho_mood\` + `DANH_SACH_CHO_MOOD_NAM.txt`
  (NAM đặt tên lại theo bảng 19 mood rồi máy gốc nhập bổ sung). File "Short version"
  tự bị bỏ khi import.
- Mood còn mỏng sau đợt này (đặt hàng tiếp): **determined 0**, suspenseful 1, romantic 2,
  nostalgic 4, inspiring 4.

## 3. Kho SFX life-in mới (`F:\AutoEdit\ambient\life-in\`)

- Kho cũ (165 wav + raw 127 + records) → backup
  `F:\AutoEdit\backup\ambient_life-in_truoc_nap_20260717\` (khôi phục được).
- **GIỮ LẠI 7 file hook cũ (impact ×4, click ×3)** — lệch chủ đích so với "xóa toàn bộ":
  hook SFX life-in đang BẬT mà mẻ mới chỉ có whoosh (5 file mới); impact/click là "ngữ
  pháp cắt", không phải tiếng hiện trường. User muốn xóa nốt thì nói — nhưng hook sẽ câm.
- Nạp mới: **299 entry / 44 kind, 0 lỗi** (tổng kho 306 wav / 47 kind). Loại 21 file có
  lý do + khử 15 file trùng giữa editor. Nguồn thô GIỮ NGUYÊN tại
  `F:\THU VIEN NHAC + SFX\LIFE IN` — niche khác cần (vd whale/seagull/ocean cho deepsea)
  thì nạp thêm từ cùng nguồn = "SFX dùng chung".
- **TÁCH KIND THEO LOÀI (user chốt — đóng điều tra RD-89 lạc-đà-tiếng-chim):** camel 3 ·
  goat 2 · horse 7 · dog 7 · monkey 4 · penguin 1 · whale 12 · eagle 5 · vulture 1 ·
  crow 1 · pigeon 2 · seagull 14 · bird (generic, vét) 5 · animal_wildlife = rổ vét
  RỖNG chủ đích (match mà im + ghi note = thấy lỗ hổng đặt hàng).
- Kind mới đáng chú ý: tách gió 2 khí hậu **wind 17 vs snowstorm 16** (xoay vòng mù —
  trộn là sa mạc dính bão tuyết); market 5 (tách khỏi urban_street); plane 11 /
  plane_cabin 3; subway 11; motorboat 4 / boat 7 / ship 2; volcano 9 (keywords CHỈ cụm
  phun-trào — bài học V8 lava nguội); ice 9 · rumble 9 · snow_walk 9 · splash 10 ·
  stadium 7 · racecar 2 · car_interior 4 · flag 2 · ski 1 · snowmobile 1 · escalator 1.
- `subject_rules.yaml` VIẾT LẠI (bản Oman cũ trong backup): loài đặt TRƯỚC cảnh generic;
  default 2 file lấy từ chính mẻ mới (gió nhẹ trung tính).

### File LOẠI — báo editor (còn nằm nguyên trong folder nguồn)

| Nhóm | Số | Lý do / việc cần |
|---|---|---|
| Flipping (lật trang) + Typewriter | 7 + 3 | chưa có tầng máy dùng — chờ user chốt (backlog chapter-title/overlay?) |
| Freezing Breath (người thở/run) | 4 | không có luật máy an toàn — editor đặt tay trong CapCut |
| Flamingo | 3 | KHÔNG có tiếng hồng hạc thật (chim/sếu trộn gió) — đặt hàng lại |
| Trộn 2 tiếng chính | 2 | gió+ngỗng, tuyết rơi+chó sủa (luật vàng 2.1) |
| Khác | 2 | 1 file VIDEO .mov lạc folder + 1 drone sci-fi không phải dưới nước |

### Lỗ hổng kind sau đợt này (kho cũ xóa mà mẻ mới không có — đặt hàng tiếp)

`food` 0 (đơn cũ +5 chưa về) · `people_activity` 0 · `interior` 0 (plane_cabin/escalator
đã tách riêng) · `mountain_desert`/`sky_cloud`/`urban_landmark`/`nature_forest_field` 0
(ô thở cảnh này rơi về default — chấp nhận, thà im còn hơn sai) · `animal_wildlife` 0
(chủ đích) · penguin/vulture/crow/ski/snowmobile/escalator mới 1 file (nghe lặp nếu dùng dày).

## 4. Rà chồng chéo (P5 — bắt buộc)

- **Tầng cùng quản CHỌN NHẠC:** stage `music` (plan) · assemble fallback (không plan) ·
  `--music`/`--music-lib` tay. Cả 2 đường tự-chọn cùng resolve qua `music_root_for` →
  không ngược chiều. Đường tay thắng như cũ — không đổi.
- **Lệch pool music-stage vs assemble:** chạy `music` KHÔNG truyền `--niche` trên project
  mới (niche chưa set) → plan chọn từ pool CHUNG; assemble sau đó resolve pool RIÊNG →
  file plan không có trong tracks riêng → assembler cảnh báo "thiếu file — bỏ" (mềm,
  không crash, lộ ở cổng tai). Chống bằng: `make` tự truyền + ghi luật vào 2 HUONG_DAN.
  KHÔNG thêm state mới vào project (P2).
- **Usage/đa dạng:** `music_usage.json` per-pool — phạt đa dạng chỉ đếm trong pool riêng,
  pool chung không bị nhiễm số đếm life-in. Đúng chiều luật.
- **SFX các tầng tiêu thụ kind:** C1 ô thở (scene_type → kind cùng tên) · S2 chủ thể
  (subject_rules) · S3 hook (impact/whoosh/click) · S1 drone (life-in không dùng) ·
  editor-learn classify (dùng chung subject_rules — kho học lại SAU này sẽ phân loại
  theo bảng mới, draft đã học không đổi). Kind mới đều khai qua subject_rules.yaml =
  0 code, `niche_kinds()` tự nhận. Không tầng nào âm thầm lật: thiếu kind → im/default
  (fail-open sẵn có).
- **Draft cũ đã dựng:** media đã COPY vào folder draft (portable) → xóa kho không hỏng
  draft cũ. Re-assemble project cũ sẽ ăn kho mới — chủ đích.
- **Cùng pattern bug:** rà OptionInfo khi sửa `make` → phát hiện + sửa kèm bug `credit`
  (make gọi assemble thiếu `credit` → nhận OptionInfo truthy → bật ghi công VD4 ngoài ý
  muốn từ commit VD4). Regression: pytest cũ vẫn xanh; bug này không có test riêng vì
  là call-site typer (khó test đơn vị, đã ghi chú tại chỗ).

## 5. Nghiệm thu

- pytest: 4 test mới `test_music_root_niche.py` + full suite (xem NHAT_KY).
- **Cổng TAI (user, chưa qua):** dựng 1 video life-in mới → nghe nhạc (pool riêng, mood
  đúng chương) + SFX loài (ngựa ra tiếng ngựa, chợ ra tiếng chợ, tuyết ra bão tuyết).
