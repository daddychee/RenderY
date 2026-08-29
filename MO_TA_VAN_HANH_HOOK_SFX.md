# MÔ TẢ VẬN HÀNH — S3-HOOK: hit/whoosh/click tại CUT trong hook (deepsea)

> Nguồn số: `PHAN_TICH_HOOK_SFX_EDITOR_DEEPSEA.md` (23 draft editor, 2026-07-13).
> User duyệt thiết kế + "làm gói hook trước sau đó dựng lại v4" (2026-07-13 tối).
> Bối cảnh 4 vấn đề: memory `ds5-083-4-van-de-sfx-lap`.

> 📌 **LỆCH SO VỚI BẢN GỐC (2026-07-14, user chốt):** **space BẬT S3-HOOK, MƯỢN nguyên
> số đo deepsea 🔸** (user: "2 niche gần giống nhau; sau này space có số liệu rồi sẽ áp
> dụng số liệu của space") — bản gốc ghi "chỉ niche có số đo mới bật". Kho
> `F:\AutoEdit\ambient\space` đã nạp đúng 18 file cùng nguồn editor
> (impact 7 · whoosh 6 · click 5). Đo lại space theo
> `QUY_TRINH_LAY_MAU_SFX_NICHE_MOI.md` → thay số, gỡ 🔸. Rà chồng chéo riêng space: §3b.

> 📌 **CỔNG TAI V4 DS5-083 (2026-07-14): MẬT ĐỘ RỚT.** User nghe hook V4: "chỉ có tiếng
> whoosh với impact xuất hiện dày đặc làm khó chịu" → **`HOOK_SFX_PM` CÒN 30% số đo
> editor: 4,8 → 1,44/phút, áp CẢ 2 niche** (user chốt). Số đo editor 4,8 GIỮ NGUYÊN
> trong `PHAN_TICH_HOOK_SFX_EDITOR_DEEPSEA.md` — đo đúng, nhưng tai user quyết mức máy
> (bài học: số editor là điểm XUẤT PHÁT, không phải đích). Click không đổi (luật riêng
> bám ảnh, trần 4 — hook V4 không có click nên không dính khiếu nại). Vol 0,2 🔸 giữ —
> chưa có phán quyết riêng. Dựng lại DS5-083 → **_V5** chờ tai.

## 1. Luật

Tầng **S3-HOOK** — CHỈ chạy khi `project.niche ∈ HOOK_SFX_NICHES` (mở màn: `deepsea`
— niche duy nhất có số đo; space/travel TẮT tới khi đo):

1. **Phạm vi**: chương 1 (hook) = 0 → `timeline_start` chương 2 (`_chapters_with_time`).
   Không có dữ liệu chương (≤1 chương) → tầng tắt.
2. **Mốc đặt = CUT video** (mọi mép miếng L1, kể cả miếng shot thở; bỏ mốc <0,5s đầu
   video) — theo đo: 48% SFX hook editor nằm ±0,25s quanh cut, text chỉ 3%.
3. **3 loại tiếng** (kind kho ambient niche — xem §2):
   - `click` — TẠI cut **vào ẢNH** (photo/entity, khoảnh khắc "chụp" Ken Burns), trần
     `HOOK_CLICK_CAP=4`/video, đặt cả khi mật độ đã đủ (hành vi editor: click đi với ảnh).
   - `impact` — TẠI cut **trùng accent nhạc** (±0,35s quanh target M-SNAP; music-sync
     tắt → không có loại này) — "hit trên nhịp".
   - `whoosh` — cut thường, đặt **TRƯỚC cut `HOOK_WHOOSH_LEAD=0,08s`** (đo: 13% tiếng
     editor lead 0–200ms "whoosh-vào-hit"; cùng triết lý SNAP_LEAD 80ms của M-SNAP).
4. **Mật độ đích** `HOOK_SFX_PM=1,44` tiếng/phút hook (📌 cổng tai V4 2026-07-14: còn
   30% median editor 4,8 — xem block đầu file) — S3 chỉ **BÙ**:
   deficit = round(1,44 × phút hook) − (tiếng S2/C1/sfx-track đã có trong hook) − click
   vừa đặt. Deficit ≤0 → chỉ còn click. Khoảng cách tối thiểu giữa 2 tiếng bất kỳ
   `HOOK_SFX_GAP=3s` (chống dồn cục).
5. **Volume `HOOK_SFX_VOL=0,2`** 🔸 — quy tương quan lớp PB10 (editor 0,56 × 0,18/0,5
   ≈ 0,20), KHÔNG copy số editor. Chốt thật ở cổng tai V4.
6. **Đặt track `sfx`** (vai UI/hiệu ứng — ambient giữ vai môi trường), chạy **SAU
   overlay/chart SFX** (UI-SFX thắng chỗ; S3 né bằng gap + `_safe_add_segment`).
   One-shot: KHÔNG fade-in (giữ attack), trần `HOOK_SFX_MAX_S=4s`, cắt thì fade-out 0,3s.
   Xoay vòng biến thể trong kind, seed crc32(project_id) — dựng lại ra đúng bản cũ.
7. **Fail-open mọi nấc** (y C1/S1/S2): niche ngoài gate / kho thiếu cả 3 kind / không
   chương / 0 cut trong hook → tầng tắt, draft y như cũ. Kind thiếu lẻ → bỏ loại đó.
8. Log `project.hook_sfx_log` (t/kind/file/note) + 1 dòng warnings (report tự hiện).

## 2. Kho tiếng — per-niche, KHÔNG vào kho SFX toàn cục

18 file từ `F:\DEEPSEA\SOUNDEFFECT` nạp vào **`F:\AutoEdit\ambient\deepsea`** (tiền lệ
kind `drone`): `impact` 7 (Tiếng BOOM) · `whoosh` 6 (WHOSH 2 + Underwater Whoosh 4) ·
`click` 5 (CLICK 4 + CAMERA 1). Lý do KHÔNG nạp `~/AutoEdit/sfx` toàn cục: kho đó là
rotation của overlay-SFX MỌI niche — BOOM/whoosh vị deepsea sẽ lọt vào video space.
`AMBIENT_KINDS` thêm `("impact", "whoosh", "click")` để ambient-import nhận.

## 3. Rà chồng chéo (P5 — bắt buộc)

| Tầng cùng quản | Kết luận |
|---|---|
| **PB12 (bỏ whoosh auto bám ô thở/text)** | KHÔNG lật: PB12 đo space = whoosh bám TEXT; deepsea đo ra bám CUT. S3-HOOK bám CUT + per-niche gate (space vẫn 0 whoosh auto). Ghi 📌 lệch theo niche ngay tại đây. |
| S2 loài/hiện trường (không trần) + C1 ô thở | CÙNG CHIỀU — S3 đếm chúng vào mật độ (chỉ bù thiếu) + gap 3s né chồng mốc; S2/C1 nằm track ambient, S3 track sfx — không tranh chỗ. |
| S1 bed 0.25 + nhạc M-VOL hook 0.30 | Hook giờ 5 lớp âm (voice·nhạc·bed·S2/C1·S3) — kiểm CHUNG 1 CỔNG TAI trên V4 (user chốt từ trước: volume music hook tính sau). |
| M-SNAP accent (cov.snap_to_accents) | CÙNG CHIỀU — cut đã snap về accent−80ms; S3 đặt impact tại đúng các cut đó (đọc targets từ `timeline_accents`, truyền qua assemble). Music-sync tắt → S3 vẫn chạy, chỉ không có impact-accent. |
| Overlay-SFX (pop/kinetic) + chart-SFX track `sfx` | S3 chạy SAU → UI-SFX giữ chỗ; S3 tính chúng vào busy (gap 3s) + `_safe_add_segment` chặn đè. |
| Kho sfx toàn cục / mine.py editor-learn | KHÔNG ĐỤNG kho toàn cục. mine `_KIND_NAME_PAT` ăn theo AMBIENT_KINDS mới — vô hại (nhận diện tên file kho). Editor-learn tương lai file whoosh vẫn route sfx staging (người sort) — không tự vào kind. |
| subject_rules.yaml | impact/whoosh/click KHÔNG khai trong yaml (không phải tiếng chủ thể — tránh S2 spam); vào qua AMBIENT_KINDS. |
| Space/travel | ~~0 đổi hành vi (gate niche)~~ 📌 2026-07-14: space BẬT mượn số (xem đầu file + §3b); travel vẫn tắt chờ đo. |

## 3b. Rà chồng chéo RIÊNG SPACE (📌 2026-07-14 — bật mượn số deepsea)

| Tầng cùng quản | Kết luận |
|---|---|
| **PB12 (đo space: whoosh editor bám TEXT, không bám cut)** | ⚠️ ĐIỂM CĂNG DUY NHẤT — S3 đặt tiếng bám CUT tức là làm khác hành vi ĐO ĐƯỢC của editor space. User biết và chốt mượn (2 niche gần giống); **cổng tai video space kế tiếp là trọng tài** — chê thì gỡ space khỏi gate, 1 dòng. PB12 bản thân không lật: overlay-SFX bám text vẫn chạy y cũ. |
| Overlay-SFX space (pop/kinetic bám text) — track `sfx` | CÙNG CHIỀU — S3 chạy SAU, đếm chúng vào busy (gap 3s) + `_safe_add_segment` chặn đè. Space overlay dày hơn deepsea → deficit S3 tự nhỏ đi (chỉ bù thiếu). |
| **Ảnh Ken Burns (space NHIỀU ảnh entity ≠ deepsea)** | `click` bám cut-vào-ẢNH sẽ NỔ THẬT ở space (V4 deepsea = 0 click vì hook không ảnh) — trần 4/video giữ nguyên. ĐIỂM NGHE CHÍNH ở cổng tai. |
| Nhạc M-VOL hook space + drone space 0.15 | Lớp mới chồng lên mix hook space hiện có (đã qua cổng tai V13/V14 KHÔNG có S3) — vol S3 0.2 🔸 nghe chung, chê chỉnh 1 hằng. |
| Kho whoosh mượn: 4/6 file là "Underwater Whoosh" | Vị nước trong video vũ trụ — nghe thử ở cổng tai; chê thì lọc file whoosh vị nước khỏi kho space (xóa `whoosh_*.wav` tương ứng, records còn truy được nguồn). |

## 4. Verify

- pytest: unit `hook_sfx_slots` (mật độ/bù, gap, click-ảnh + trần, impact-accent,
  whoosh-lead, ngoài hook bỏ) + wire `_add_hook_sfx` (đặt thật + fail-open) + FULL suite.
- Dựng lại DS5-083 → `_V4`: kiểm hook_sfx_log (số tiếng, loại, mốc) — **cổng TAI user**
  nghe chung 5 lớp (bed + loài + water_churn + nhạc hook + S3). Máy không tự phán.
