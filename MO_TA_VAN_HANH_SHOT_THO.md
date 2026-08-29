# MÔ TẢ VẬN HÀNH — SHOT THỞ (footage riêng cho ô thở hết ý / cuối chương)

> Trạng thái: v1 (§1–5) CODE XONG 2026-07-08, Jupiter V6 — **cổng MẮT user: CHƯA ĐẠT
> nghĩa "thở"** (footage chỉ ~2s, 100% ô 1 footage). **SHOT THỞ 2.0 (§6) — user chốt
> 2026-07-08: footage 4–10s, 1–3 footage/ô, đa dạng, số theo niche; cách làm user giao
> Claude quyết → CODE XONG cùng ngày, pytest 278/278, Jupiter draft V7, cổng số §6.4
> ĐẠT + ✅ cổng MẮT user DUYỆT V7 (2026-07-08) — TÍNH NĂNG ĐÓNG, backlog §6.5.**
> Nguồn: user xem V5/V6 + DNA 3 project.
>
> **SHOT THỞ 3.0 (§7) — user chốt 2026-07-13 sau DS5-083: LUẬT CHỌN ĐỔI HẲN sang
> LIÊN TỤC CHỦ THỂ** (tiếp tục chủ thể clip liền trước, đổi cỡ cảnh; bỏ "đắt"/mood-chủ-đạo).
> Bảng điểm §2c hết hiệu lực — đọc §7. Timing/k miếng của 2.0 GIỮ NGUYÊN.

---

## 1. Vấn đề + bằng chứng DNA

User (2026-07-08, sau khi xem draft V5): *"Khi hết các ý trong 1 đoạn, editor làm hình
thở sẽ để một footage khác tiếp theo (không có voice), cùng mood với footage liền kề
trước đó nhưng khác cỡ cảnh (không có thì chấp nhận trùng)… hiện tại bạn vẫn chỉ để
footage trước đó chạy tiếp."*

Đo 51 ô thở sạch (≥1,5s, đã lọc nhiễu ≥8s) của SP1-001/003/004 — editor có **3 cách
phủ hình**, không phải 1:

| Cách | Tần suất | Khi nào |
|---|---|---|
| Giữ hình cũ suốt ô + shot kế vào sớm 0,15–0,6s (J-cut muộn) | ~55% | ô nông giữa chương (style chủ đạo SP1-003) |
| Phủ thụ động (không cắt trong ô) | ~20% | ô nông, hình cũ còn đẹp |
| **Giữ hình cũ 0,4–0,9s → CẮT sang footage khác chạy im lặng 1–5s → voice vào trên footage đó** | ~25% | **ô sâu, nhất là hết ý / cuối chương** |

Bằng chứng cách 3 (offset cắt tính từ lúc hết voice):
- SP1-004 ô cuối chương: 5,3s (giữ 0,43 → shot mới im lặng **4,87s**) · 4,0s (0,57 →
  **3,46s**) · 3,9s (0,63 → **3,30s**).
- SP1-001: ô 6,1s (giữ 0,87 → **5,2s**) · ô 6,9s (giữ 4,8 → 2,1s).
- SP1-003 ô chương 2,4s (giữ 0,67 → 1,73s); ô 2,9s cắt ngay tại 0,0.

⚠ **Đính chính tri thức cũ**: kết luận đợt 1 "ô sâu = giữ hình, không footage riêng"
chỉ đúng cho STYLE SP1-003. Đã sửa memory `sp1-003-breathing-pattern`.

V5 hiện tại chỉ có cách 1 với lead cố định 0,3s (9 frame) — mắt đọc là "không chuyển
footage". Tính năng này cũng chính là chuyện user nêu từ trước: hình thở dài = editor
**đắt thêm 1 footage**.

## 2. Thiết kế

### 2a. Ô nào nhận shot thở (chốt 1: 100% ô đạt ngưỡng)

```
BREATH_SHOT_MIN         = 2.5   # ô thở >= 2,5s ở bất kỳ đâu
BREATH_SHOT_MIN_CHAPTER = 1.5   # ô cuối chương (beat kế thuộc chương khác)
BREATH_SHOT_HOLD        = 0.5   # giữ hình cũ trước khi cắt (DNA: 0,4-0,9s)
```

- Ngưỡng suy từ DNA: các ô nhận cách-3 của editor nằm 2,4–6,9s; riêng cuối chương
  editor làm cả ô 1,5s.
- **Beat cuối video KHÔNG nhận** (không có voice vào sau — outro giữ hình như cũ; backlog).
- Ô không đạt ngưỡng: giữ nguyên hành vi V5 (giữ hình + J-cut 0,3s / phủ thụ động).

### 2b. Timing trong ô

```
hết voice ──0,5s giữ hình cũ──┤CẮT├── shot thở chạy hết ô ──┤voice chương/ý sau vào TRÊN shot thở
```

- **Bỏ J-cut 0,3s tại ô có shot thở** — shot thở đã làm đúng vai "hình mới vào trước
  voice"; thêm J-cut nữa = 2 nhát cắt vụn trong 1 ô (editor đa số 1 nhát/ô).
- Shot thở kết thúc đúng mép voice kế → beat sau vào hình của nó đúng lúc nói.

### 2c. Chọn footage shot thở (chốt 2: máy thuần, 0 call NÃO)

> 📌 **LỆCH SO VỚI BẢN GỐC (2026-07-13):** bảng điểm dưới đây (mood chủ đạo 2,0/tag +
> bonus wide/aerial "đắt") HẾT HIỆU LỰC — user xác nhận nhặt sai chủ thể ở cả space lẫn
> deepsea. Luật mới: **liên tục chủ thể + đổi cỡ cảnh** — xem §7. Giữ nguyên văn để đối chiếu.

Pool = **kho local của niche** (video, geo-gate PA2 như phễu; local-first theo
`footage-source-local-first`). Điểm — theo đúng triết lý filter-overload-guard:
**chỉ CỘNG ĐIỂM, không đẻ cửa loại mới**; loại duy nhất = P7 đã-dùng-trong-video
(luật cứng có sẵn):

| Tiêu chí | Điểm | Ghi chú |
|---|---|---|
| Mood trùng clip liền trước | +2,0/tag (max 4,0) | luật 1 của user — chủ đạo |
| Cỡ cảnh KHÁC clip liền trước | +1,0 | luật 2; trùng/thiếu tag = 0, vẫn chọn được |
| Đủ dài (dur ≥ ô − 0,5) | +1,5 | thiếu → slow-mo fallback có sẵn của assembler |
| Chưa dùng trên kênh (P7 mềm) | +0,5 | |
| wide / aerial | +0,5 | proxy "đắt" của máy (thoáng, ăn tiền ở cảnh nghỉ) |

- "Clip liền trước" = clip CUỐI của cửa sổ beat mang ô (extra_shots[-1] nếu multi-shot,
  không thì clip chính). Mood/cỡ cảnh của nó: tra db nếu là local; clip stock không
  tag → dùng `beat.mood`/`beat.shot_size` (LLM điền sẵn, dịch qua vocab 19 từ bằng
  `_MOOD_SYNONYMS`).
- Mỗi shot thở chọn xong vào `used_in_video` → 2 ô không trùng clip, và tự động không
  trùng clip beat nào (kể cả beat kế — tránh "cắt sang chính nó").
- **Fallback khi không chọn được** (pool rỗng/niche trống): KHÔNG ghi shot thở → ô đó
  giữ nguyên hành vi V5. Không bao giờ hở hình.

### 2d. Chỗ đứng trong pipeline + dữ liệu

- **SOURCE** (sourcer/breath.py mới): sau khi mọi beat có clip → chọn shot thở cho từng
  ô đạt ngưỡng, copy vào `assets/b{bid}_breath_*.mp4`, ghi usage. Ghi
  `project.breath_shots: list[BreathShot{beat_id, asset_path, asset_key, source, note}]`
  (NT1/NT5 — editor + report kiểm được).
- **ASSEMBLE**: `breath_ids` lấy từ `project.breath_shots` THẬT (không tính lại predicate
  — pick hụt ô nào thì ô đó tự về hành vi cũ, 2 tầng không bao giờ lệch nhau).
  `coverage.split_breath_shots()` chẻ cửa sổ cuối segment thành [thoại+0,5s giữ] +
  [cửa sổ shot thở] rồi mới `apply_j_cuts` (cửa sổ giữ còn breathing 0,5 < 1,2 → tự
  thoát J-cut, không cần if riêng).

## 3. RÀ CHỒNG CHÉO (P5 — bắt buộc)

| Tầng cùng quản | Ngược chiều? | Ai lật ai? |
|---|---|---|
| **Luật d2 "ô thở = 1 hình giữ, nhát cắt không rơi giữa im lặng"** (rà 2026-07-04 #1, đang nằm ở `split_window` tail + comment coverage.py) | **CÓ — LUẬT LẬT CÓ CHỦ ĐÍCH** tại ô đạt ngưỡng, bằng chứng DNA 3 project + mắt user. Ô dưới ngưỡng luật cũ VẪN GIỮ. Cắt của shot thở rơi tại hết-voice+0,5s (có chủ đích), KHÔNG phải máy chia đều vô thức như bug cũ. | Ghi rõ ở đây + comment code |
| `apply_j_cuts` (hình thở 2.0) | Không — ô có shot thở tự thoát (breathing tail còn 0,5 < 1,2); ô khác giữ nguyên J-cut | Không ai lật ai |
| `split_window` multi-shot (tail không chia) | Không — cửa sổ giữ mang tail 0,5 nên nhát chia multi-shot vẫn nằm trong thoại; cửa sổ shot thở luôn 1 clip | — |
| Phễu `_need_dur` (hình thở 3.0 vừa thêm) | **Đổi có chủ đích**: breathing ≥ 2,5 → clip beat chỉ cần phủ thoại + 0,5 (shot thở gánh phần còn lại) → bớt giết oan clip ngắn, bớt slow-mo. Ô cuối-chương 1,5–2,5s: phễu KHÔNG biết hàng xóm → giữ conservative (tính đủ tail) — chỉ thiệt nhẹ (đòi clip dài hơn cần), không sai | need_dur giảm nhưng fallback (pick hụt) = clip beat giãn slow-mo phủ ô — hành vi degrade có sẵn, có warning |
| Ducking nhạc (MIN_BREATH 1,5) | Không đụng — ducking đọc `segments.breathing_after`, voice không đổi. Nhạc vẫn nở suốt ô kể cả khi hình cắt | Đo nhạc editor tại ô = backlog |
| Pacing DNA validator (Mảnh B) | placed_shots đếm THÊM 6–10 shot thở → cuts/min tăng nhẹ. DNA đo từ draft editor VỐN CÓ shot thở của họ → ta GIỐNG mẫu hơn, không lệch | — |
| SFX/overlay/text/chart | Không — anchor theo word/beat timeline, không theo cửa sổ video | — |
| Report | `breath_shots` nằm trong project.json (kiểm được); hiện chưa vẽ lên report.html = backlog | — |
| P7 chống lặp + usage kênh | Shot thở đi qua CÙNG used_in_video + log_usage như clip beat | — |

Anh em cùng pattern đã quét: `_need_dur` có 2 điểm gọi (technical_gate + finish_scoring)
— cùng 1 hàm, sửa 1 chỗ; `total_end` (4 chỗ assembler) không đổi vì timeline không đổi.

## 4. Cổng kiểm

1. **pytest**: predicate ngưỡng (2,5 mọi nơi / 1,5 cuối chương / beat cuối video không) ·
   split cửa sổ (liền khít, invariants, thoát J-cut) · chọn máy (mood thắng, khác cỡ
   cảnh ưu tiên, trùng vẫn chấp nhận, P7 loại, pool ngắn → vẫn chọn) · need_dur mới
   (regression: clip 4s từng bị giết oan ở ô thở 5s giờ sống) · assemble tích hợp
   (3 segment video, mép 4,5/7,0 đúng chỗ, không J-cut tại ô shot thở). FULL suite.
2. **Cổng số V6** (Jupiter): số shot thở = số ô đạt ngưỡng có pick; mỗi shot thở =
   material KHÁC clip liền trước; mép cắt = hết voice + 0,5 (±1 frame); các ô không
   ngưỡng giữ J-cut 0,3 như V5; mối nối vẫn khít plan+0,1.
3. **Cổng MẮT user**: mở V6 xem các ô hết ý/cuối chương — có "footage nghỉ" thật chưa,
   mood có nối không, cỡ cảnh có đổi không. **Claude KHÔNG tự phán đạt.**

**KẾT QUẢ 2026-07-08 (draft `SCRIPT_VOICE_20260707_132450_V6`):**
- pytest FULL **270/270** (12 mới, gồm regression "clip 4s từng bị giết oan ở ô thở 5s").
- Jupiter: **7/7 ô đạt ngưỡng có shot thở** (5 ô ≥2,5s giữa chương + 2 ô cuối chương;
  beat 111 cuối video đúng thiết kế không nhận; 9 ô nông giữ hành vi cũ).
- Cổng số: 7/7 mép cắt = hết voice + 0,5 (±1 frame — lệch 33µs do coverage round 4 chữ
  số, vô hại) · 7/7 phủ tới ĐÚNG mép voice kế, KHÔNG J-cut · 7/7 material khác clip
  liền trước · 8/8 ô không ngưỡng giữ J-cut 0,3 y cũ · 127 segment video 0 hở/đè.
- Mood: 6/7 khớp (vd b029 epic+mysterious, cỡ wide→aerial). **b105 mood `sad` kho space
  không có clip sad** → máy rơi về cỡ cảnh/độ dài, chọn clip trạm điện — điểm đáng soi
  nhất ở cổng mắt; nếu nhạt/lệch → kích hoạt backlog "NÃO chấm shortlist" (§5).

## 5. Backlog (không tự làm)

- Ô thở cuối video (outro) — hiện giữ hình cũ.
- ~~Ô rất sâu >6s: editor có khi 2–3 nhát~~ → làm ở 2.0 (§6).
- NÃO chấm "đắt" trong shortlist (phương án b) nếu cổng mắt thấy máy chọn nhạt.
- Report.html vẽ hàng shot thở.
- Nhạc tại ô thở (ducking DNA riêng).

---

# SHOT THỞ 2.0 — kéo sâu ô 4–10s + đa dạng 1–3 footage (2026-07-08)

## 6.1 Vấn đề (cổng mắt V6) + gốc rễ + đính chính DNA

User xem V6: footage thở *"chỉ chạy auto để 2 giây, chưa đúng nghĩa thở"* (editor nói
1 footage thở thường **4–10s**), và *"100% chỉ dùng thêm 1 footage"* — cần đa dạng
**1–3 footage/ô**, 3 footage thì mỗi cái ngắn hơn; thời lượng cũng đa dạng; **số liệu
theo niche** (đây là space).

**Gốc rễ — không phải lỗi chọn footage:** NÃO director cho `breathing_after` toàn số
tròn bậc 0,5s, thực tế trần 3,0s (Jupiter 7 ô = 5×2,5 + 2×3,0) → footage = ô − 0,5
giữ = 2,0–2,5s đều tăm tắp. Ô sâu thật của editor chạy **liên tục 2,4 → 12,3s**.

**Đính chính DNA (user chỉ ra):** bảng độ sâu ô ở lần bàn đầu TRỘN cả ô voice-nghỉ
(giữ hình/J-cut) lẫn ô hình thở thật → **TÁCH 2 LỚP RIÊNG**:

| Lớp | Là gì | Số liệu (đo lại từ `holes` 3 project) | Ai xử |
|---|---|---|---|
| **Giãn nghỉ voice** | ngắt câu/mệnh đề, hình giữ nguyên | nghe-ra 0,7–2,7s (bảng hình thở 3.0) | `plan_micro_pauses` — KHÔNG ĐỔI |
| **Ô hình thở** | hết ý/cuối chương, CÓ footage riêng | footage đo được 1,7–12,1s; **4 ô 8,4–12,3s từng bị bộ lọc "nhiễu ≥8s" che nhầm** (có ô 9,8s ngay trước "Chapter 4") — khớp lời editor 4–10s | lớp mới §6.2 |

Số footage/ô đo được: **đa số 1** (kể cả footage đơn 7,7s và 12,1s); ô rất sâu mới
2–3 nhát (6,77s → 1,73+1,5; 7,57s → 3,7; 9,03s → 7,7); đoạn 57,7s = montage, khác
loài, loại. → luật k dưới đây cho phép cả "1 footage dài" lẫn "nhiều footage ngắn".

## 6.2 Thiết kế — 3 phần (Claude quyết thay user, có căn cứ)

### A. Kéo sâu ô bằng MÁY tại stage CUT (quantile-map, giống hình thở 3.0)

NÃO vẫn quyết **chỗ nào** thở + rank thô (quyết định nghĩa — NT4 giữ nguyên); máy map
**độ sâu cuối cùng** lên phân bố DNA lớp-hình-thở của niche. Không dạy NÃO cho số sâu
vì: NÃO vốn trả số tròn lặp (bằng chứng 5/7 ô cùng 2,5) + phải re-direct cả video.

```
# pause.py — lớp DNA mới (space, fail-open khi niche thiếu block):
BREATH_POOLED = {
    "footage_anchors": [4.0, 4.5, 5.3, 6.8, 8.5],  # p10-p90 GIÂY footage (sàn 4 = user chốt;
    "footage_cap": 10.0,                            #  p50/p90 từ đo 4,87/5,2/7,7/12,1 + interview)
    "hold": 0.5,                # giữ hình cũ trước nhát cắt (DNA 0,4–0,9)
    "k_thresholds": [5.5, 8.5], # footage < 5,5 -> k=1; < 8,5 -> k∈{1,2}; còn lại k∈{1,2,3}
    "k_fractions": {2: [0.58, 0.42], 3: [0.42, 0.33, 0.25]},  # chia KHÔNG đều, cái đầu dài nhất
    "min_piece": 1.5,           # sàn 1 miếng footage khi chia
}
```

- `plan_breath_depth(beats, dna)`: ô đạt ngưỡng (predicate `breath_shot_beat_ids` —
  y v1, tính trên số NÃO) → rank theo (breathing NÃO, cuối chương, vị trí) → nội suy
  `_target()` sẵn có trên `footage_anchors` → `breathing_after mới = hold + footage`.
  Jupiter 7 ô: footage ≈ 4,0/4,2/4,3/4,5/4,8/7,2/8,5 — đa dạng liên tục, video dài
  thêm ~23s (+3,3%).
- **Bẫy idempotent (phát hiện khi rà):** chạy lại cut mà kéo ô rồi lại kéo tiếp/budget
  micro trừ theo số ĐÃ KÉO → co micro oan. Fix: `Beat.breathing_base` (số NÃO gốc,
  backfill lần cut đầu cho project cũ); mỗi lần cut **reset breathing về base** → plan
  micro (budget theo base — đúng vì editor đo 8–13% chèn giãn KHÔNG tính ô thở, rows
  và holes là 2 list riêng) → plan depth ghi số mới. Chạy lại N lần ra đúng 1 kết quả.

### B. Đa dạng 1–3 footage (quyết ở SOURCE — cần biết pool)

- footage R = breathing mới − hold. k: R<5,5 → 1 · 5,5–8,5 → chọn trong {1,2} ·
  ≥8,5 → chọn trong {1,2,3}. Chọn bằng **seed định trước** `crc32(project_id:beat_id)`
  (KHÔNG dùng `hash()` builtin — bị salt mỗi lần chạy Python; crc32 ổn định NT1).
- Guard thực dụng: k=1 mà pool không có clip nào ≥ R−0,5 → nâng k (né slow-mo 0,4x xấu).
- Chia R theo `k_fractions` (miếng đầu dài nhất — đúng mẫu editor 3,7+0,64 / 7,7+0,2).
- Chọn clip: miếng 1 chấm điểm với clip cuối cửa sổ beat (y v1); miếng 2/3 chấm với
  **miếng liền trước nó** (chuỗi mood nối); P7 dùng chung → không trùng nhau.
- `BreathShot.dur` mới (giây miếng); nhiều record cùng beat_id, thứ tự list = thứ tự
  đặt. dur=0 (record v1 cũ) = 1 miếng phủ trọn ô — backward compatible.

### C. Số theo niche (câu hỏi user về DNA niche)

- Toàn bộ số §A đọc từ block **`pooled.breath`** trong `pause_dna.json` của niche
  (`~\AutoEdit\library\<niche>\pause_dna.json`) — cùng loader/fail-open như
  `load_pause_dna`. Space: ghi block vào file niche + artifact gốc project root.
- **Bài học cho niche mới** (lý do DNA bị hiểu sai lần đầu): scan DNA niche mới phải
  (1) KHÔNG lọc phăng ô ≥8s — thay bằng nhận diện montage (≥4 nhát cắt hoặc >20s);
  (2) TÁCH lớp ô theo cách phủ (hold ≤1,2s + footage ≥1,5s = lớp hình thở);
  (3) xuất block `pooled.breath`. Ghi vào memory + đây; thiếu block → hằng space.

### Cắt trong ô — timing k miếng

```
hết voice ─0,5s giữ─┤CẮT├─ miếng 1 (dài nhất) ─┤CẮT├─ miếng 2 … ─┤ voice kế vào TRÊN miếng cuối
```
Miếng cuối luôn kết thúc ĐÚNG mép voice kế (nuốt sai số làm tròn + pick hụt giữa chừng
→ miếng đã pick cuối tự phủ dài ra, không bao giờ hở). Không J-cut (y v1).

## 6.3 RÀ CHỒNG CHÉO 2.0 (P5)

| Tầng | Kết luận |
|---|---|
| `plan_micro_pauses` budget 15% | Chạy TRƯỚC depth, budget theo `breathing_base` — micro không đổi so V5/V6. Căn cứ: editor 8–13% chèn giãn đo từ `rows` KHÔNG gồm `holes` — 2 lớp cộng riêng như editor thật |
| Validator NÃO 1,5–6s | Không đổi — trần 6s là trần số NÃO (rank thô); số cuối do máy map (có thể >6, trần 10,5) — ghi rõ tại đây |
| `breath_shot_beat_ids` | Predicate chạy ở cut trên số NÃO (base) → tập ô = y V6; funnel/coverage phía sau thấy số ĐÃ KÉO (≥4,5 đều ≥2,5) → nhánh "cuối chương 1,5–2,5 conservative" của funnel tự biến mất — clip beat bớt bị đòi dài oan |
| `split_breath_shots` | Đổi signature: nhận `{beat_id: [dur từng miếng]}` từ picks THẬT; k cửa sổ liền khít, cửa sổ cuối luôn chạm mép voice kế |
| `apply_j_cuts` | Không đổi — cửa sổ giữ còn breathing 0,5 <1,2 tự thoát; ô nông giữ J-cut y cũ |
| Ducking nhạc | Đọc `segments.breathing_after` (đã kéo) → nhạc nở dài hơn TỰ NHIÊN; RAMP 2,5s < ô min 4,5s — không sửa |
| Nhạc chương / SFX / overlay / text | Anchor theo word/beat timeline — re-cut xong assemble tự tính lại; không sửa |
| Pacing DNA (Mảnh B) | cuts/min tăng nhẹ (7 ô × k miếng) — DNA đo từ draft editor VỐN CÓ các nhát này → giống mẫu hơn |
| Voice re-cut | `run_cut` pure function (đè sạch segments); mép cắt speech KHÔNG đổi (chỉ gap đổi) — cổng số so lại |
| Tên draft | Fix luôn bẫy điền-lỗ-trống (V4 2 lần): next version = **max hiện có + 1**, kèm regression test |
| Usage kênh khi re-pick | Jupiter chạy không channel → không double-log; nếu có channel, re-pick log thêm lần 2 (chấp nhận — usage là đếm mềm) |

## 6.4 Cổng kiểm 2.0

1. **pytest**: depth-map (đúng khoảng [4,5–10,5], rank, beat cuối loại, non-qualifying
   giữ nguyên, idempotent qua base-reset) · k + fractions + seed ổn định + guard clip
   dài · split multi-miếng (liền khít, miếng cuối chạm mép, dur=0 legacy, pick hụt giữa
   chừng) · chuỗi mood miếng 2 · tên draft max+1 · FULL suite.
2. **Cổng số V7** (Jupiter): 7 ô có breathing mới 4,5–9,0s đa dạng; tổng miếng đúng
   plan; mép giữ = hết voice+0,5 ±1 frame; miếng cuối = mép voice kế; material các miếng
   khác nhau + khác clip trước; ô nông giữ J-cut; 0 hở; video dài thêm ≈ tổng kéo.
3. **Cổng MẮT user**: xem V7 — đã ra nghĩa "thở" chưa (4–10s), số footage đa dạng chưa.
   **Claude KHÔNG tự phán.**

**KẾT QUẢ 2026-07-08 (draft `SCRIPT_VOICE_20260707_132450_V7`):**
- FULL pytest **278/278** (8 mới; test cut end-to-end cũ assert gap=3,0 NÃO sửa CÓ CHỦ
  ĐÍCH theo luật mới: base=3,0 + breathing=5,8).
- Jupiter re-cut: 7 ô → **4,5–9,0s** (+25,9s video, timeline 701,2s); giãn micro 62 điểm
  y V5/V6 (base-reset đúng thiết kế, không co oan).
- Re-pick: **9 miếng / 7 ô** — b008 cuối ch1 2 miếng (4,2+3,0) · b029 4,0 · b042 4,4 ·
  b059 4,8 · b063 cuối ch2 ĐƠN 8,5s · b073 5,3 · b105 2 miếng (3,6+2,6). Footage
  3,0–8,5s, hết cảnh 2s đều.
- Cổng số: 7/7 ô đúng số miếng/dur/file/thứ tự (mép giữ = hết voice+0,5 ±1 frame, miếng
  cuối chạm đúng mép voice kế) · 8/8 ô nông giữ J-cut 0,3 · 129 segment video 0 hở/đè ·
  tên draft đúng V7 (fix max+1 hoạt động dù lỗ V4 còn đó).
- Điểm đáng soi cổng mắt: **b105 miếng 1 vẫn clip trạm điện** (kho space không có mood
  `sad` — máy rơi về cỡ cảnh); miếng 2 Parker Solar Probe. Nếu nhạt → backlog NÃO chấm.

## 6.5 Backlog 2.0

- Đo phân bố k thật khi có thêm project editor (hiện 3 điểm dữ liệu k≥2 — luật k
  đang nửa DNA nửa interview).
- Scan DNA niche mới theo bài học §6.2C (tool scan chưa đóng gói thành lệnh).

---

# SHOT THỞ 3.0 — LIÊN TỤC CHỦ THỂ (user chốt 2026-07-13)

## 7.1 Vấn đề — user xác nhận SAI LOGIC TỪ ĐẦU (cả space lẫn deepsea)

User xem DS5-083 (deepsea) gặp lại đúng lỗi từng thấy ở space → kết luận sai từ thiết
kế, không phải sai kho: *"tài liệu cũ nói nhặt những footage đắt hoặc điểm nhô vào hình
thở, nhưng tool rất khó lựa chọn nên nhặt sai. tôi muốn đổi logic là nhặt các footage
liên quan footage trước đó, thay đổi cỡ cảnh cho đỡ nhàm chán. ví dụ cảnh trước hình
thở đang trình chiếu cá mập thì các footage tiếp theo hình thở nên tiếp tục là cá mập."*

Bằng chứng DS5-083 (31 miếng / 27 ô): thuyền cá neo bến → **orca aerial** (b040); sói
Yellowstone → **asteroid flyover** (b045); domino đổ → **thằn lằn bay** (b048); phố mất
điện → **mực khổng lồ** (b092); rừng nắng → **hàm megalodon** (b100); nước tối nghẹt
thở → **bãi biển nắng** (b126).

**3 gốc rễ đo được (không chỉ 1):**
1. **Điểm chọn cũ KHÔNG có tiêu chí chủ thể** — "liên quan" chỉ đo bằng mood (2,0/tag).
2. **Mood câm toàn video (bug):** director trả mood ghép `awe_urgent_cautionary`;
   `_mood_set` chỉ split dấu phẩy → cả chuỗi không dịch được vocab → 29/31 miếng note
   ghi `mood —`. Máy chỉ còn "đủ dài + khác cỡ + wide/aerial" → bonus wide/aerial
   (proxy "đắt") thành tiêu chí DẪN DẮT = nguồn nhặt sai trực tiếp (asteroid/orca đều
   wide/aerial dài).
3. **Pool đói (bug):** `videos_for_niche` trần 500 clip mới-index-nhất; kho deepsea
   7.940 video own → pool chỉ thấy 6%, chủ thể nạp sớm không bao giờ được cân.

## 7.2 Luật mới + bảng điểm (vẫn máy thuần, 0 call NÃO)

**Shot thở TIẾP TỤC CHỦ THỂ của clip liền trước ô; ĐỔI CỠ CẢNH cho đỡ nhàm. Bỏ hẳn
luật "đắt" (wide/aerial) và mood-chủ-đạo.** Chỉ CỘNG ĐIỂM (filter-overload-guard);
loại duy nhất vẫn là P7 đã-dùng-trong-video.

| Tiêu chí | Điểm | Ghi chú |
|---|---|---|
| **Chủ thể trùng clip liền trước** | **+3,0/token (trần 3 = 9,0)** | luật 1 MỚI — chủ đạo tuyệt đối |
| Cỡ cảnh KHÁC miếng liền trước | +2,0 | luật 2 (nâng từ 1,0 — cơ chế đổi vị chính trong cùng chủ thể); trùng/thiếu tag = 0, vẫn chọn được |
| Đủ dài (dur ≥ miếng) | +1,5 | thiếu → slow-mo fallback sẵn của assembler |
| Mood trùng | +0,5/tag (max 1,0) | HẠ từ 2,0 xuống phụ trợ; `_mood_set` fix split cả `_`/`/` (mood ghép hết câm) |
| Chưa dùng trên kênh (P7 mềm) | +0,5 | giữ nguyên |
| ~~wide/aerial "đắt"~~ | **BỎ** | proxy "đắt" cũ = chính nguồn nhặt sai |

**Chủ thể đo thế nào (máy thuần):** token hóa `subject` + `tags` của kho (thường hóa,
bỏ stopword + từ <3 ký tự; tag cụm "sperm whale" tách từng từ). **Token NỀN NICHE
không được tính** = token có mặt >25% pool (deepsea: underwater 72% / marine life 71% /
ocean 64%) — đo từ pool thật lúc chạy nên tự thích nghi mọi niche, không hardcode danh
sách; pool <40 clip không demote (thống kê vô nghĩa).

**Neo chủ thể của ô** = clip cuối cửa sổ beat mang ô (extra_shots[-1] nếu multi-shot):
- clip local → tra db theo path lấy subject+tags+mood+cỡ (KỂ CẢ ảnh/viral — cái đang
  chiếu là cái cần nối, không giới hạn trong pool như cũ);
- clip stock/entity/gen chưa tag → `beat.visual_concept` (mô tả cái NÃO đặt lên màn
  hình — proxy chủ thể sát nhất; DS5-083 prev toàn stock/gen nên đây là đường chính)
  + `beat.mood`/`beat.shot_size` như cũ.

**Neo CỐ ĐỊNH cho MỌI miếng trong ô** ("tiếp tục là cá mập") — bỏ chuỗi-mood-nối 2.0
(miếng 2/3 chấm với miếng trước làm chủ thể TRÔI dần); riêng cỡ cảnh vẫn so với miếng
liền trước để các miếng đổi cỡ nhau. Kho không có clip cùng chủ thể (vd beat sói
Yellowstone giữa niche deepsea) → tiêu chí chủ thể im lặng, mood/cỡ/độ dài gánh —
fail-open y triết lý cũ, chấp nhận rơi về "cùng không khí", KHÔNG đẻ cửa loại.

Note của BreathShot thêm trường đầu: `chủ thể shark+reef · mood … · cỡ wide→close_up`
— editor + cổng số kiểm được máy khớp bằng token nào.

## 7.3 RÀ CHỒNG CHÉO 3.0 (P5)

| Tầng cùng quản | Kết luận |
|---|---|
| **Luật user 2026-07-08** ("cùng mood clip liền trước, ưu tiên footage đắt" — §1, memory `sp1-003-breathing-pattern`) | **LẬT CÓ CHỦ ĐÍCH bởi chính user 2026-07-13** — mood/"đắt" xuống phụ trợ/bỏ, chủ thể lên chủ đạo. Ghi 📌 tại §2c + foundation d2 |
| Chuỗi-mood-nối miếng 2/3 (2.0 §6.2B) | **LẬT CÓ CHỦ ĐÍCH**: neo cố định theo ô — chuỗi nối cũ làm chủ thể trôi (b092: miếng 1 mực → miếng 2 chấm theo mực, không theo phố) |
| Phễu beat thường + PEAK_BONUS ytref | KHÔNG ĐỤNG — cờ điểm nhô chỉ chảy trong `_finish_scoring` phễu thoại; breath là đường chọn riêng, trước nay chưa từng đọc peak |
| filter-overload-guard | GIỮ — generic-demote KHÔNG phải cửa loại (chỉ không cộng điểm); loại duy nhất vẫn P7 |
| `videos_for_niche` 500→50k | caller DUY NHẤT là breath (grep); chặn viral GIỮ NGUYÊN (test c8 pass); is_file ~8k row ≈ vài giây/build — chấp nhận |
| `_mood_set` split thêm `_`/`/` | hàm nội bộ breath.py (grep: không ai khác gọi); music `_chapter_moods` ĐÃ split `_` sẵn; vision validator nhận list + raise to tiếng — không anh em cùng pattern còn sót |
| stock_tags (M3b) | KHÔNG đọc (nguyên tắc không-2-tầng-cùng-quản + lúc source chưa chắc đã tag xong) — fallback visual_concept; nếu mắt chê thì mở backlog đọc stock_tags |
| Assembler / coverage / ducking / music / report | KHÔNG ĐỤNG — chỉ ĐIỂM chọn clip đổi; timing hold 0,5/k miếng/mép voice kế y 2.0; BreathShot schema không đổi (note đổi format — report không parse note) |
| Usage kênh / P7 | đi qua CÙNG used_in_video + log_usage y cũ |

Vùng ảnh hưởng đã rà: `_score`/`_anchor_tags`(cũ `_prev_clip_tags`)/`_mood_set` chỉ có
caller trong breath.py + test_breath.py; `videos_for_niche` 1 caller; test viral-exception
(`test_viral_pool_open_except_breath`) giữ nguyên nghĩa.

## 7.4 Cổng kiểm 3.0

1. **pytest FULL 474/474** (2026-07-13; 6 test mới trong test_breath.py, gồm 3 hồi quy
   tái hiện bug trước-fix: mood ghép câm · sói-tuyết-thua-asteroid · neo trôi miếng 2).
2. **Cổng số (khi dựng lại DS5-083):** so bảng 31 miếng cũ↔mới — tỷ lệ miếng có token
   chủ thể khớp neo (note `chủ thể ≠ —`); các ô kho không có chủ thể (sói/phố/domino)
   được phép rơi về mood/cỡ; mood `—` phải biến mất ở beat có mood dịch được; timing
   mép giữ 0,5/mép voice kế KHÔNG đổi so bản cũ.
3. **Cổng MẮT user** — xem draft dựng lại: hình thở có "tiếp tục chủ thể" thật chưa,
   cỡ cảnh có đổi không. **Claude KHÔNG tự phán đạt.**

## 7.5 Backlog 3.0 (không tự làm)

- Đọc `stock_tags` làm neo khi clip liền trước là stock ĐÃ tag vision (thay proxy
  visual_concept) — chỉ mở nếu cổng mắt thấy neo lệch.
- Trần token generic 25% + sàn pool 40 là số khởi điểm — chỉnh khi có bằng chứng
  niche mới (travel địa danh có thể cần demote khác).
