# MÔ TẢ VẬN HÀNH — SFX THEO LOÀI/HÀNH ĐỘNG per-niche (gói học sheet editor)

> Nguồn: sheet 41 dòng "hành động → SFX" editor deepsea (user 2026-07-13,
> `PHAN_TICH_SFX_EDITOR_DEEPSEA.md`). User duyệt 3 đề xuất A/B/C cùng ngày.
> **Milestone A ĐÃ XONG (2026-07-13, pytest 481/481). Milestone C ĐÃ XONG cùng ngày
> (pytest 482/482)** — user đổi chốt mật độ: KHÔNG trần, match-driven (§5).
> **Sửa C cùng ngày (pytest 485/485): bed KHÔNG loop cả bài — gate theo cảnh underwater (§5b).**

## 1. Cái gì đổi (A + lõi của B)

1. **`subject_rules.yaml` per-niche** (`F:\AutoEdit\ambient\<niche>\subject_rules.yaml`)
   — bảng chủ thể → kind tiếng THAY TRỌN bảng built-in `SUBJECT_RULES` khi file tồn tại
   (không merge — luật space không rơi nhầm vào deepsea). Niche không có file → built-in,
   space **0 thay đổi hành vi**. Schema: `{rules: [{kind, keywords: [...]}]}`; keywords
   EN = tag vision GLM, VN = tên file editor (editor-learn dùng chung bảng). Đây chính là
   đường "học từ editor" lặp lại được: **niche mới = editor điền 1 sheet → mã hóa thành
   1 yaml**, không sửa code.
2. **`subject_kind()` match CỤM TỪ** (word-boundary): "sperm whale" phân biệt "humpback
   whale"; "sunset" vẫn không ăn "sun" (regression giữ). Nhận `rules=` per-niche; luật
   fire-cận-cảnh (tai V7/V8) giữ nguyên cho MỌI bảng.
3. **Kind mới hợp lệ theo niche**: `niche_kinds()` = AMBIENT_KINDS + kind khai trong yaml;
   `ambient-import`/`ambient-list` nhận kind loài.
4. **mine.py (editor-learn)**: `classify()` nhận rules per-niche → lần học draft sau tự
   route tiếng cá voi vào đúng kind (hold không phình lại nhóm này); `_kw` bắt số DÁN
   liền đuôi tên file editor ("cá nhà táng**2**", "Water Whoosh**2**" — \b không ăn số dán).
5. **Kho deepsea nạp 28 file + re-kind 2** (đủ 31/41 dòng sheet có trên máy):
   `whale_sperm` 6 · `whale_humpback` 9 · `whale_blue` 3 · `whale_orca` 1 (kêu thiếu —
   chờ folder editor) · `attack` 4 (vồ + 3 whoosh sinh vật từ sfx staging) · `splash` 5
   (3 nạp + `ocean_14/21` re-kind — tiếng cá voi thở/lao lên KHÔNG phải pad sóng) ·
   `default` +2 ("dưới nước 4/Dưới nước 2" — bị classify NHẠC >40s, rút khỏi staging nhạc).
   Dọn: hold 323→301, sfx staging bỏ 3 whoosh attack + thêm `Water Whoosh.aac` (DS3_008).

## 2. Bảng deepsea (tóm tắt luật đã chốt trong yaml)

- **Thứ tự = ưu tiên: LOÀI trước** (orca đang săn → tiếng orca, không phải whoosh attack),
  hành động (attack/splash) sau, generic (rumble/signal/fire/ocean/water) cuối.
- **CỐ Ý KHÔNG dùng bare** `sea/ocean/whale/predator/underwater` — tag deepsea nào cũng
  dính (predator 1919/10.618 asset) → kêu loạn (bài học filter-overload + tai V7).
  `ocean` chỉ match cụm mặt-biển (seagull/beach/shore/ocean surface/waves crashing...).
- Đo thật 3.000 asset đầu kho: 454 match (sperm 294 · blue 69 · ocean 26 · attack 25...).

## 3. Rà chồng chéo (P5 — bắt buộc)

| Tầng cùng quản | Kết luận |
|---|---|
| C1 ambient ô thở (`choose_files` subject > scene > default) | CÙNG CHIỀU — kind loài tự thắng ở ô thở, không sửa gì thêm |
| S2 volume (SUBJECT_VOL 0.18 / BREATH 0.32) + trần SUBJ_CAP=6 | KHÔNG ĐỔI ở A — trần đổi ở milestone C (mật độ 50%) |
| S1 drone + nhạc + music-sync M-VOL hook 0.30 deepsea | ⚠ hook nhạc to CÓ THỂ ÂM THẦM CHE tiếng loài — user chốt "volume music ở hook tính sau"; kiểm CHUNG 1 cổng tai ở video kiểm |
| editor-learn classify | ĐÃ CẬP NHẬT cùng gói (rules per-niche + số dán) — rerun DS1_046/DS3_017 dry-run = 0-mới ✓ |
| Track sfx UI/overlay, portable/pack, phễu source | KHÔNG ĐỤNG |
| Space/travel | KHÔNG ĐỔI (không có yaml → built-in; pytest 481/481 có regression word-boundary cũ) |

## 5. Milestone C (2026-07-13, cùng ngày — user đổi chốt) — pytest 482/482

**User chốt lại mật độ: "KHÔNG có mật độ — thấy footage phù hợp là để sfx phù hợp với
footage đó"** (thay chốt cũ thân-bài-50%-hook). Kèm 2 việc: folder editor đã copy về
`F:\DEEPSEA\SOUNDEFFECT` (172 file, chia subfolder chủ đề) + điều tra "tiếng ục ục cả bài".

1. **Gỡ trần S2** (`subject_beat_slots`): BỎ SUBJ_CAP=6/video + không-2-beat-kề +
   ≤2-lần/kind → match-driven như editor. GIỮ: ảnh không SFX, beat đồ họa skip, beat
   <AMB_MIN skip, SUBJ_MAX 10s/tiếng, cắt theo shot-1, xoay vòng biến thể. Áp CẢ space
   (user nêu vấn đề chung 2 niche) — tai chê ở cổng kiểm thì thêm knob lại.
2. **"Ục ục cả bài" = bed drone deepsea — ĐO THẬT 23 draft editor:** `dưới nước 4.aac`
   phủ 45–60% bài trong 13 draft (vol 0.32–0.56), `Dưới nước 2` 3 draft, `Dauzkobza
   Underwater Bubbles Scuba Diving` 2 draft (phủ 67%). → re-kind default_5/6 + nạp 1 =
   **kind `drone` deepsea 3 biến thể** (S1 sẵn có tự chạy: 1 bed/video crc32, loop suốt).
   🔸 `DRONE_VOL_BY_NICHE["deepsea"]=0.25` (quy tương quan: bed editor ≈ SFX-voiced 0.5
   của họ ↔ SUBJECT_VOL 0.18 máy; space giữ 0.15) — CHỜ CỔNG TAI.

   > **📌 LỆCH SO VỚI BẢN GỐC (2026-07-13, cùng ngày):** user sửa nhận định — bed
   > KHÔNG loop cả bài; theo sheet editor **CHỈ đặt trên CẢNH DƯỚI NƯỚC**. Đo lại
   > 23 draft xác nhận: 383 đoạn bed, median 40s/đoạn, gap thật 4–630s tại cảnh mặt
   > biển/bản đồ/người (gap 0/âm = nối loop trong 1 chuỗi cảnh dài). → Xem §5b.
3. **Nạp SOUNDEFFECT 37 file** (dedup records): whale_orca +2 (**tiếng orca KÊU đã có**)
   · whale_humpback +5 (Céline mới) · signal +5 (sonar tàu ngầm + tiếng vọng) · ocean +5
   (2 file sheet thiếu: DB studios Beach + OG Big Ocean Wave) · fire +4 · **`underwater`
   13 file** (ÂM THANH HIỆN TRƯỜNG/TIẾNG NƯỚC NGẦM) · nature_water 2 (dual).
4. **Vá 2 lỗ scene fallback C1** (phát hiện khi rà): GLM scene_type deepsea =
   `underwater` 8.498/10.618 asset + `nature_water` 923 — kho trước đó **0 file cả 2
   kind** → mọi ô thở dưới nước rơi về 4 pad default. Giờ ô thở underwater có 13 biến
   thể, nature_water 2.
5. **seabird tách khỏi ocean**: re-kind ocean_17/23 (2 file seagull sheet chỉ định) →
   `seabird` + rule riêng — footage chim biển không còn rơi vào rotation 28 file sóng.

**Trạng thái sheet sau C: 39/41 dòng có tiếng trong kho** (2 còn thiếu: `Phun nước.aac`,
`Water Whoosh2.aac` — vẫn ở máy editor, ĐÃ có bản tương đương trong kind).

## 5b. Bed gate theo CẢNH (2026-07-13 tối — user sửa nhận định) — pytest 485/485

**Chốt mới:** bed ục ục CHỈ trên cảnh dưới nước, KHÔNG loop cả bài. Số đo 23 draft
editor: 383 đoạn, dur median 40s, phủ 13–98%/bài (median ~43%); gap thật 4–630s =
cảnh rời mặt nước thì bed TẮT.

- **`bed_intervals(project, scene_lookup, scenes)`** (schedule.py): đơn vị = BEAT trọn
  (voice + thở sau, tới `timeline_start` beat kế — shot thở 3.0 liên tục chủ thể nên
  cảnh ô thở ≈ cảnh pick); pick có `scene_type ∈ scenes` → vào run; beat liền nhau gộp;
  run < `BED_MIN=6.0s` bỏ (editor hiếm đặt đoạn <7s); beat mù tag/graphic = gap.
- **`DRONE_SCENE_BY_NICHE = {"deepsea": ("underwater",)}`** — space/travel không gate
  → loop cả bài y cũ (regression giữ). `nature_water` CỐ Ý không vào gate: cảnh mặt
  nước không có ục ục ngầm.
- **`_add_drone`**: niche gate → loop file trong TỪNG run (fade vào 2s/ra 3s mỗi run,
  seam 0.3s trong run); **mù cache.db → tầng TẮT** (bed đè cảnh mặt biển tệ hơn không
  bed — khác fail-open C1 vốn rơi về default); 0 run → tắt + warning. `drone_log` thêm
  `covered_s/runs/gate`; report hiển thị "phủ X/Ys (N run cảnh)".
- **Smoke DS5-083 thật:** 33 run, phủ 1260/1876s = **67%**, run median 25.8s — đúng dải
  editor; 63 beat cảnh mặt biển/rừng/người hết bị bed đè.

### Rà chồng chéo bổ sung (C)

- Gỡ trần S2 → số tiếng/video tăng mạnh (video loài đặc trưng có thể hàng chục) — volume
  0.18/-15dB dưới voice giữ nguyên; loạn hay không do CỔNG TAI video kiểm quyết.
- Bed drone 0.25 + nhạc + M-VOL hook 0.30 + tiếng loài: 4 lớp cùng kêu ở hook — kiểm
  CHUNG 1 cổng tai (user: volume music hook tính sau).
- `underwater`/`nature_water`/`drone` KHÔNG vào subject_rules (bare "underwater" sẽ spam
  S2 trong voice) — chỉ đi đường C1 scene fallback + S1 bed.
- **Bed gate (§5b) vs C1 ô thở cảnh underwater:** trong ô thở cảnh dưới nước giờ CHỒNG
  2 lớp — pad `underwater` C1 (0dB) + bed drone (0.25). Editor cũng chồng (bed + hiện
  trường); dày hay không do cổng tai. Bed gate đọc scene từ PICK, C1 đọc từ miếng shot
  thở — có thể lệch ở ô thở đổi cảnh (hiếm: shot thở 3.0 liên tục chủ thể); chấp nhận.
- Space: gỡ trần ÁP CHUNG nhưng bảng match space hẹp (rocket/explosion...) → tăng ít;
  drone space vẫn 0.15. Regression pytest giữ.

## 5c. Gói nước-động (2026-07-13 tối — từ 4 vấn đề user nêu trên DS5-083 V3)

> Chẩn đoán 4 vấn đề: memory `ds5-083-4-van-de-sfx-lap`. User duyệt gói này + gói hook
> (đo trước); seabird b85 (máy ĐÃ đặt, vol 0.18) user tự nghe lại; lặp footage GIỮ NGUYÊN.

1. **Kind `water_churn`** — 10 file bubble/gurgle foley từ folder editor "Nước động"
   (file gốc giữ nguyên chỗ). Keywords: churning/turbulent/whirlpool/vortex/bubbles/
   bubbling/gurgling + cụm swirling 2 CHIỀU (swirling sand / sediment swirling...).
   **KHÔNG bare `swirl/swirling`** — đo thật DS5-083: b220 "green smoke swirling" ăn
   nhầm bubble foley. Đo kho 10.618 asset trước khi thêm: bubbles 67 là lớn nhất.
2. **`ocean` +8 cụm mặt-biển-động**: choppy · rough sea(s) · stormy sea/ocean · surf ·
   foam(y). "surf" word-boundary KHÔNG dính "surface" (đã đo).
3. **Bài học b43**: kho có 28 file ocean + keyword "waves crashing" CÓ SẴN mà beat vẫn
   im — vì pick Pexels **fail vision M3b → mù tag** (fail-open). Chạy `tag-stock
   <project>` vá được; DS5-083 còn b75/b142 fail kiểu khác (mood ngoài vocabulary,
   xem Còn ngỏ). Quét lại 270 pick: **+6 beat có tiếng mới** (b43 ocean + 5 water_churn).
4. Rà chồng chéo: mine classify dùng chung yaml (file "Bubbling/Gurgling" tương lai tự
   route water_churn); thứ tự ocean > water_churn (mặt biển thắng); space/travel 0 đổi;
   0 code — pytest 485/485 nguyên.

## 6. Còn ngỏ

- Cổng TAI video kiểm deepsea: bed 0.25 🔸 + mật độ không trần + tiếng loài + music hook
  + water_churn/ocean mở rộng (§5c).
- **Lỗ mood-vocab tag stock:** GLM trả mood ngoài vocabulary → validator loại CẢ asset
  sau 4-retry → mù tag vĩnh viễn (DS5-083: b75, b142). Cần quyết: lọc mood lạ giữ tag
  còn lại, hay giữ như cũ? (CHỜ USER)
- SOUNDEFFECT chưa nạp (ngoài scope ambient): CÔNG NGHỆ/NHIỄU/Highlight TEXT (UI-sfx)
  · GIỚI THIỆU/Trống/NĂNG ĐỘNG (nhạc) · KINH DỊ (riser) · KINH DỊ 2 (19 drone
  cinematic — nạp thêm nếu tai muốn đổi vị bed) · NHỊP TIM CÁ 4.
  (~~Nước động~~ ĐÃ NẠP §5c · ~~Tiếng BOOM/WHOSH/Underwater Whoosh/CLICK/CAMERA~~
  ĐÃ NẠP gói S3-HOOK 2026-07-13 — `MO_TA_VAN_HANH_HOOK_SFX.md`: kind impact 7 ·
  whoosh 6 · click 5, per-niche deepsea.)
- Whoosh attack TƯƠNG LAI vẫn route sfx staging (hint whoosh xét trước rules) — người sort.
- `_KIND_NAME_PAT` (mine `_out_name`) chưa biết kind per-niche — vô hại (`_copy` không đè).
- Hold còn 301 file chưa phân loại (ngoài phần sheet phủ).
