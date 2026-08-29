# BÀN GIAO — GÓI CẮT THEO NHỊP NHẠC (mini-hook · hình thở · đoạn chèn)

> **ĐỌC FILE NÀY TRƯỚC KHI LÀM M1.** Viết 2026-07-19 ngay trước khi user clear chat.
> Mọi số trong đây là ĐO THẬT, không phải ước lượng. Đường dẫn file:dòng đã kiểm.
> Đọc kèm: `CLAUDE.md` (nguyên tắc) → file này → `NHAT_KY_BUILD.md` (tiến độ).

---

## 0. Gói này là gì

User muốn tool cắt footage theo nhịp nhạc **giống editor thật**. Chia làm 3 vùng dùng:

| Vùng | Có voice? | Trạng thái |
|---|---|---|
| **Mini-hook** đầu bài | Không | ✅ Lưới beat XONG, user DUYỆT 4 project 2026-07-19 |
| **Hình thở** giữa bài | Không | ✅ **M1 ĐÓNG TRỌN — CỔNG TAI USER DUYỆT 2026-07-20** (draft RD89_OMAN_10MIN, mép beat 65 lệch 0,2ms; `MO_TA_VAN_HANH_NHIP_O_THO.md`) |
| **Đoạn chèn** giữa bài (editor khai) | Không | ✅ **M2 ĐÓNG TRỌN — CỔNG MẮT DUYỆT 2026-07-20** (`MO_TA_VAN_HANH_DOAN_CHEN.md`) + ✅ **M3 nhạc editor CODE ĐÓNG 🔄 chờ cổng TAI** (`MO_TA_VAN_HANH_NHAC_DOAN_CHEN.md`); M4-M5 ⏸ |
| Vùng CÓ voice | Có | ❌ **KHÔNG ĐỤNG** — xem §1 |

---

## 1. LUẬT ĐỨNG: hai hệ cắt KHÔNG trộn

| | Vùng CÓ voice | Vùng KHÔNG voice |
|---|---|---|
| Ai quyết mép cắt | **nghĩa** của lời | **nhịp** nhạc |
| Nhạc đóng vai | nền, snap ≤15% mép | **chủ đạo, 100% mép** |

**Bằng chứng KHÔNG được quên:** nghiên cứu ~11.000 cut của 26 draft editor thật kết luận
video **CÓ LỜI** thì editor **KHÔNG** cắt theo lưới nhịp (lift đo 0,86 < 1,6 cần thiết).
Xem memory `editor-music-sync-study`. Project mẫu `0719` không mâu thuẫn — nó là video
**KHÔNG LỜI**. Hai bằng chứng nói về hai loại video khác nhau.

⚠️ Nếu ai đó (kể cả user) đề xuất cắt theo nhịp ở vùng có voice → nhắc lại số đo này trước.

---

## 2. QUYẾT ĐỊNH USER ĐÃ CHỐT (2026-07-19)

1. **Mini-hook 4 project ĐẠT** — "tôi kiểm tra 4 project đã ổn".
2. **Nhạc đoạn chèn = phương án B** — bài editor đưa **THAY LUÔN** nhạc chương đó từ điểm
   chèn về sau (không quay lại nhạc cũ). Lý do: hệ thống vốn đổi nhạc theo chương, B đi
   cùng chiều thiết kế; A gây 2 lần chuyển nhạc trong vài chục giây, rối tai.
3. **Độ dài đoạn chèn: EDITOR quyết** từng đoạn, không cứng 20s.
4. **Nhịp cắt theo nhạc** — không dùng mẫu beat cứng, xem §4.
5. **BỎ TRẦN 3 MIẾNG ở ô hình thở** — "đoạn này cho phép sáng tạo theo beat nhạc".
6. **Đo lại 433 bài nhạc: ĐỒNG Ý** — đã làm xong ở M0.
7. Footage đoạn chèn: 2 cách — (a) editor khai bằng lời ("thiên nhiên hùng vĩ", "phụ nữ
   xinh đẹp"); (b) editor đưa project đã tách cảnh. **Làm (b) trước** (M4), (a) sau (M5).

---

## 3. LỘ TRÌNH

| Mốc | Nội dung | Rủi ro | Trạng thái |
|---|---|---|---|
| M0 | Lưu độ mạnh beat/accent vào thư viện nhạc + đo lại 433 bài | Thấp | ✅ **XONG 2026-07-19**, pytest 640 |
| **M1** | **Cắt nhịp ở HÌNH THỞ** (không chèn gì) | Thấp | ✅ **ĐÓNG TRỌN — CỔNG TAI DUYỆT 2026-07-20** ("tôi nghe đạt", draft RD89_OMAN_10MIN_20260720; target 3,0s; pytest 651 gồm fix trần đuôi c04def1; xem `MO_TA_VAN_HANH_NHIP_O_THO.md`) → **TIẾP THEO: M2 đoạn chèn (§7 đã rà sẵn, rủi ro CAO)** |
| M2 | Đoạn chèn: chèn Δ vào timeline, mọi tầng dịch đúng | **CAO** | ✅ **ĐÓNG TRỌN — CỔNG MẮT DUYỆT 2026-07-20** (draft `RD89_OMAN_10MIN_20260720_V2`: Δ 188,42→208,42s đúng 20,00s, phủ kín, voice khớp từng chữ số; lệnh `autoedit insert`, Δ chèn tại cutter/timeline.py theo §7b; pytest 661; `MO_TA_VAN_HANH_DOAN_CHEN.md`) → **TIẾP THEO M3** |
| M3 | Đoạn chèn: nhạc editor đưa (phương án B) + độ dài tuỳ editor | TB | ✅ **ĐÓNG TRỌN — CỔNG TAI USER DUYỆT 2026-07-20** (draft `RD89_..._V4`; cờ `insert --music <file>`, bài editor thay nhạc chương từ mép vào Δ tới HẾT CHƯƠNG; `music_spans()`; `MO_TA_VAN_HANH_NHAC_DOAN_CHEN.md`) |
| **M4** | Δ: lưới beat + footage editor đưa | TB | 🔄 **ĐANG DỞ — ĐỌC `BAN_GIAO_M4_NHIP_DANG_DO.md`**. ✅ Δ vào ĐÚNG vị trí 4:12 (user duyệt mắt, sau khi fix bug NAM CHÂM biến thể thứ-tự-segment `c1d88f4`) · ❌ **NHỊP CẮT CHƯA ĐẠT TAI** (V10, user: *"vẫn chưa đúng nhịp beat chuyển"*) · ⏸ footage thật trong Δ chưa làm (còn slug). 4 giả thuyết đã ghi sẵn; việc đầu tiên = xuất click-track cho user đối chiếu. pytest 681 |
| M5 | Footage đoạn chèn: khai bằng lời | TB | ⏸ |
| M6 | Video thật trọn gói | — | ⏸ **cổng mắt+tai USER** |

**Vì sao M1 trước M2:** hình thở đã có sẵn trong mọi video → KHÔNG phải chèn gì → không
đụng bug NAM CHÂM, không dịch toạ độ, không làm ôi thiu kế hoạch nhạc. Nó là **phép thử
rẻ** cho lưới beat trong bài thật. Tai user duyệt ở đây rồi mới đem sang đoạn chèn.

> P4: một mốc một lần. Xong → test → báo cáo → **CHỜ USER XÁC NHẬN** → mới sang mốc sau.
> Cổng TAI/MẮT là của USER. Claude **KHÔNG TỰ BÁO ĐẠT**.

---

## 4. SỐ ĐO THẬT (dùng ngay, đừng đo lại)

### 4a. Nhịp cắt theo BPM — mẫu beat CỨNG là SAI HƯỚNG

Mẫu `HOOK_PATTERN = (3,5,5,3,4,4,5,4)` rồi khoá 8 beat (copy từ project tay `0719`) cho ra:

| Bài (E:\NHỊP NHANH\ĐÀN DỒN DẬP NHỊP NHANH) | BPM | Shot đầu | **Khoá 8 beat** |
|---|---|---|---|
| Adrián Berenguer - Class Act | 152,0 | 1,2–2,0s | **3,2s** |
| Adrián Berenguer - Premiere | 172,3 | 1,0–1,7s | **2,8s** |
| Romeo - End of an Era | 89,1 | 2,0–3,4s | **5,4s** ⚠ |
| Ziv Moran - Looking Further | 136,0 | 1,3–2,2s | **3,5s** |

**Kết luận:** đếm theo số beat thì co giãn theo BPM **QUÁ TAY** — chênh gần 2× giữa bài
nhanh và chậm. Tai người cảm nhận shot theo **GIÂY**, không theo số beat.

**Hướng sửa (chưa code):** nhắm khoảng THỜI GIAN shot, quy ngược ra số beat — nhạc chậm
dùng ÍT beat hơn (89 BPM: 8 beat 5,4s → 4 beat 2,7s). Mọi cut vẫn hạ cánh trên beat thật.
**Khoảng nhắm cụ thể CHƯA CHỐT** — phải đo từ project `0719` + draft editor trong kho ở M1.

### 4b. Phân bố ô thở thật — 367 ô / 15 project

| Độ dài | Số ô | % |
|---|---|---|
| 1,5–2,5s | 143 | 39% |
| 2,5–4s | 37 | 10% |
| 4–6s | 103 | 28% |
| **6–8s** | 53 | 14% |
| **≥8s** | 31 | 8% |

Trung vị **4,0s**, max **9,0s** (trần: `footage_anchors[-1]=8.5` + `hold 0.5`).
**22% ô dài ≥6s** → mỗi video ~5-6 chỗ đủ dài để cắt nhịp mà không thành vụn.

### 4c. Độ mạnh beat sau M0

Trải **0,17 → 1,00** (chuẩn hoá trong bài), trung vị ~0,29. Khoảng **20% số beat** mạnh
≥1,5× trung vị → cứ 5 beat có 1 beat "nặng": đủ thưa làm mốc, đủ dày để luôn có cái gần chỗ cần.

---

## 5. CODE ĐÃ CÓ

### 5a. `autoedit/autoedit/music/minihook.py` — lưới beat (ĐÃ DUYỆT)

- `beat_grid(duration, beat_times, *, pattern, lock, min_shot, beat_strength, search)`
- `grid_windows(...)` → [(start,end)] liền khít, mép dùng CHUNG float
- `HOOK_PATTERN=(3,5,5,3,4,4,5,4)`, `HOOK_LOCK=8`, `MIN_HOOK_SHOT=0.7`, `SEARCH_BEATS=2`
- **CHƯA ĐƯỢC GỌI TỪ PIPELINE** — mới chỉ dùng bởi `autoedit/scripts_thu_mini_hook.py`.

**🐛 Bug đã sửa (user bắt, cut b08/b09):** bản đầu tính mốc SỐ HỌC `b0+n*period` → rơi vào
beat YẾU ngay sau beat MẠNH → tai nghe cao trào 13,421s nhưng hình đổi 13,785s = **TRỄ ĐÚNG
MỘT BEAT**. Nay: đi pattern ra mốc dự kiến → **hạ cánh xuống beat THẬT** trong ±2 beat, chọn
beat MẠNH NHẤT, rồi `idx = pick` neo lại (không trôi). `SEARCH_BEATS=2` là số ĐO: ±1 → 4/33
cut rơi beat yếu; ±2 → 1/33.

Test: `autoedit/tests/test_minihook.py` (11 test, có 2 test hồi quy bug trên).

### 5b. M0 đã sửa gì (2026-07-19)

| File:dòng | Đổi |
|---|---|
| `music/analyze.py` `_rhythm_from_signal` | +`beat_strength` (env[idx] vốn tính rồi VỨT) |
| `music/analyze.py` `_pick_accents` | trả `(accents, accent_strength)`; **sort lại theo THỜI GIAN** |
| `music/library.py:24` `RHYTHM_KEYS` | +`beat_strength`, +`accent_strength` |
| `music/library.py` `_import_entries` | điều kiện nâng cấp: `or "beat_strength" not in obj` |

Đã đo lại: `F:\AutoEdit\music` (317 bài, 151s) + `F:\AutoEdit\music\life-in` (116 bài, 54s).
Backup: `music_index.pre_strength_20260719.json` ở cả 2 folder.
Kiểm chứng: 0 field cũ đổi giá trị · accents đổi THỨ TỰ nhưng KHÔNG đổi tập hợp · 0 bài lệch độ dài.

---

## 6. VÙNG ẢNH HƯỞNG M1 — file:dòng đã rà (P5)

### 6a. Ô thở hiện chia hình thế nào

| Việc | File:dòng |
|---|---|
| **Ô nào ĐỦ ĐIỀU KIỆN** nhận shot thở | `packager/coverage.py:107-116` `breath_shot_beat_ids` — ngưỡng `BREATH_SHOT_MIN=2.5`, hoặc `BREATH_SHOT_MIN_CHAPTER=1.5` nếu beat kế khác chương |
| **CHIA bao nhiêu miếng** (nơi thật sự quyết) | `sourcer/breath.py:107-128` `_pieces` — **stage SOURCE**, không phải assemble |
| **THI HÀNH chẻ cửa sổ** | `packager/coverage.py:119-148` `split_breath_shots` — chỉ đọc `durs` do caller đưa |
| Lắp `durs` cho coverage | `packager/assembler.py:73-76` (`breath_specs`) và `:209-212` (`breath_q`) — **trùng logic, dựng từ cùng vòng lặp** |
| Đặt clip lên track | `packager/assembler.py:214-227` — `breath_q[w.beat_id].pop(0)`, KHÔNG có Ken Burns |
| Ghi `project.breath_shots` | `sourcer/runner.py:448` — chỗ GHI DUY NHẤT |

**⚠ TRẦN 3 MIẾNG (user chốt BỎ):** hardcode ở `sourcer/breath.py:119` (`allowed=[1,2,3]`)
+ ràng buộc chéo với key của `k_fractions` (`cutter/pause.py:85`, chỉ có key 2 và 3 → `k=4`
sẽ **KeyError**). Muốn bỏ trần phải sửa **CẢ HAI CHỖ, 2 FILE**.

**Tham số DNA ô thở:** `cutter/pause.py:80-87` `BREATH_POOLED`:
`footage_anchors=[4.0,4.5,5.3,6.8,8.5]`, `footage_cap=10.0`, `hold=0.5`,
`k_thresholds=[5.5,8.5]`, `k_fractions={2:[0.58,0.42], 3:[0.42,0.33,0.25]}`,
`min_piece=1.5` ← **HẰNG CHẾT, KHÔNG AI ĐỌC** (grep xác nhận). Bỏ trần miếng thì phải
tự dựng sàn miếng, đừng trông vào hằng này.

### 6b. Ba cái BẪY đã biết trước cho M1

**① Số miếng phải quyết ở stage SOURCE, không phải assemble.** Vì chỉ stage source mới
biết kho còn bao nhiêu clip. Chốt số miếng ở assemble mà không đủ clip → **hở timeline**
→ bug NAM CHÂM CapCut (lịch sử trôi −187s, xem memory `capcut-main-track-nam-cham-va-san-niche`).

**② Luật GIỮ HÌNH CŨ 0,5 giây.** `BREATH_SHOT_HOLD=0.5` (`coverage.py:104`), thi hành ở
`coverage.py:138` `cut_at = w.end - w.breathing_dur + HOLD`. Đo từ draft editor thật (DNA
đo 0,4-0,9s). **Lưới beat phải bắt đầu SAU mốc này**, không đè lên.

**③ CHỒNG CHÉO: mép giữa các miếng thở hiện BỊ LOẠI khỏi snap accent.**
`coverage.py:201-202`: `if w.breath_shot and nxt.breath_shot: continue`.
Tính năng M1 **ĐẢO NGƯỢC ĐÚNG LUẬT NÀY**. Phải khai rõ trong mô tả vận hành, không lặng lẽ sửa.
(Mép VÀO ô thở thì KHÔNG bị loại — `breath_entry`, ưu tiên hạng 1, ràng buộc `coverage.py:218-219`.)

### 6c. Chỗ CỘNG HƯỞNG (tin tốt)

Ô thở đã có sẵn cơ chế **nhạc NỞ TO** khi voice ngừng: `ducking.py:15` `BREATH_VOL=0.5`
(~+8dB so mức nép 0.2), `MIN_BREATH=1.5`, `RAMP=2.5`. Nghĩa là đúng lúc muốn cắt theo nhịp
thì nhạc VỐN ĐÃ TO SẴN → hai thứ cộng hưởng, không cãi nhau.

### 6d. Cần cho M1: biết "tại giây T nhạc mạnh hay yếu"

Sau M0 đã đủ dữ liệu. Công thức chiếu **hệ TIMELINE → hệ FILE NHẠC** (bất biến P, giữ đúng
ở cả `music/plan.py:196` và `packager/assembler.py:656`):

```
P_i           = start_offset_i + min(MUSIC_XFADE, timeline_start_i)     # MUSIC_XFADE=3.0
pos_in_track(T) = P_i + (T - boundary_i)
```
Rồi tra `beat_times`/`beat_strength` của bài đó. **Lưu ý:** không mô hình hoá LOOP — nếu
`pos_in_track > duration_sec` thì bài đã quay vòng (`music/plan.py:176-177`).

**Ranh giới chương** = `chapters_with_time(project)` (`music/plan.py:41-63`), suy từ
`beat.timeline_start`. Ranh giới N→N+1 = `chs[i+1]["timeline_start"]`, **KHÔNG PHẢI**
`chs[i]["timeline_end"]` (hai giá trị lệch nhau đúng bằng ô thở cuối chương).
⚠ `boundaries` đã neo M-CHANGE chỉ tồn tại trong RAM lúc assemble (`assembler.py:91`),
**KHÔNG lưu vào project.json**.

---

## 7. VÙNG ẢNH HƯỞNG M2 (đoạn chèn) — rà sẵn, đọc khi tới M2

### 7a. Cổng CHẶN CỨNG — không chèn được ở ĐẦU bài

`packager/coverage.py:247-248`: `if abs(windows[0].start) > 1e-3` → lỗi "cửa sổ đầu phải là 0",
raise ở `assembler.py:113-115`. Cửa sổ đầu lấy `seg.timeline_start` của segment đầu.
→ **KHÔNG THỂ đẩy voice xuống rồi nhét đoạn chèn vào đầu.** Đây là cổng TỐT (canh bug nam châm).

### 7b. Đường chèn khuyến nghị: phình `breathing_after`, KHÔNG dịch tay ở assembler

Timeline sinh ở ĐÚNG MỘT CHỖ: `cutter/timeline.py:67-72` (`cursor = 0.0`; `cursor =
timeline_end + breathing_after + micro_pause_after`). Chèn Δ **tại đó** → **10/14 chỗ trong
assembler TỰ ĐÚNG**. Dịch tay 14 chỗ là chắc chắn sót.

### 7c. Bốn chỗ vẫn phải xử lý tay

1. **Hình trong Δ** — dùng lưới beat thay chia đều.
2. **Kế hoạch nhạc ÔI THIU** — `p.start_offset` neo accent theo timeline CŨ
   (`music/plan.py:123-124`). Phải gọi `mark_music_stale()` (`music/plan.py:206-215`).
   Không gọi → accent lệch → `snap_to_accents` **trượt mép cắt video về chỗ KHÔNG có accent**.
   Hỏng-mà-vẫn-chạy, tệ hơn crash.
3. **Mẫu số pacing** — `assembler.py:169` dùng `total_end/60`; Δ làm méo `cpm` + `pstdev`
   → báo động giả. Loại Δ khỏi mẫu số (tiền lệ: slug, `assembler.py:255-256`).
4. **Ambient nuốt trọn Δ** — `schedule.py:233-244` `breath_slots` coi cả Δ là MỘT ô,
   đặt 1 clip KHÔNG loop → file ngắn hơn Δ thì im lặng phần còn lại (`assembler.py:820-825`).

### 7d. Ba bẫy IM LẶNG của M2

1. **`layer2`/`kinetic*` KHÔNG đi qua CoverWindow** — chart PiP (`assembler.py:526`),
   info-card (`assembler.py:1150`) đọc THẲNG `beat.timeline_start`. Dịch ở tầng window mà
   quên tầng beat → chart/card lệch Δ, **không invariant nào bắt**.
2. **KHÔNG có invariant nào cho track AUDIO.** Hình có cổng phủ kín + slug lấp lỗ; nhạc/
   drone/ambient hụt Δ ở cuối → **không exception, không warning rõ** (chỉ số trong
   `record.warnings`, `assembler.py:288`, `:927-931`).
3. **`_safe_add_segment` nuốt SegmentOverlap** (`assembler.py:1165-1177`) → trả False, bỏ
   qua segment. Δ dịch sai có thể mất hàng loạt SFX hoàn toàn im lặng.

### 7e. Chỗ ĐÃ SẴN SÀNG cho M2

Nhạc trải **THEO CHƯƠNG** và chương i kéo tới `bounds[i+1]` (`assembler.py:624-632`) →
đoạn Δ giữa 2 chương **TỰ ĐỘNG được nhạc chương đó phủ kín**, không phải làm gì.
Voice cũng dễ: `assembler.py:196-204` chỉ đọc `seg.timeline_start`, không cộng dồn cursor.

---

## 8. FOOTAGE (M4/M5) — rà sẵn

### 8a. `--ref` KHÔNG tự đọc draft CapCut

Là **HAI BƯỚC TÁCH RỜI**:
1. `library-ingest <niche> <folder draft>` (`cli.py:1169-1200` → `library/ingest.py:460`)
   — đọc `draft_content.json`, cắt theo mép editor, tag GLM, ghi kho.
2. `--ref <path>` (`cli.py:693-697`) — chỉ là **prefix lọc trên kho đã nạp**.

**⚠ BẪY ĐÃ CẮN (bug DS3-084):** mẻ chưa `library-ingest` thì `--ref` chạy **RỖNG, KHÔNG
BÁO LỖI**. Luật rào: memory `tu-nap-video-mau` (mọi máy TỰ nạp mẻ mẫu trước direct-context).

3 tác dụng của `--ref`: chèn pool ≤6/beat (`sourcer/local.py:183-243`) · `REF_BONUS=1.0`
(`ranker/funnel.py:38`) · trần 15% thay 8% (`sourcer/viral.py:42-46`).

### 8b. `--boost "X@scope"` — có sẵn nhưng YẾU ở chữ "NHIỀU"

5 tầng: chèn pool ≤6 (`local.py:298-333`) · `BOOST_BONUS=1.0` (`funnel.py:41`) · sàn vét
(`runner.py:836-839`) · tầng ĐO (`runner.py:493-497`) · khối NÃO (`director/live.py:245-279`).
Merge tại chokepoint DUY NHẤT `sourcer/runner.py:315`. Scope: `all|hook|ch<N>`.

**4 lỗ hổng thật:**
1. `search_assets` (`library/db.py:388-389`) **KHÔNG match `scene_type`/`mood`** — gõ
   `mountain_desert` ra **0 dòng** dù kho có nghìn cảnh núi. Dễ vá nhất, giá trị lớn nhất.
2. AND-match 1 term, **không có OR/khái niệm** — "thiên nhiên hùng vĩ" là hợp của nhiều tag.
3. **KHÔNG có cơ chế MẬT ĐỘ.** `BOOST_BONUS=1.0 < NGHIA_W=3.0` (cố ý) → chương toàn beat
   nghĩa mạnh thì gõ boost **gần như không đổi gì** → editor kết luận "tính năng hỏng".
4. Không có "cường độ" — boost editor và `audience_bias` niche dùng chung 1 hằng.

**★ NHƯNG đoạn chèn KHÔNG CÓ VOICE → KHÔNG có điểm nghĩa cạnh tranh → vấn đề mật độ BIẾN MẤT.**
Nên M5 (khai bằng lời TRONG đoạn chèn) dễ; "khai bằng lời trong vùng có voice" mới là bài
toán khó — **ghi TỒN ĐỌNG, user chưa yêu cầu**.

### 8c. Field kho mô tả nội dung hình

`library/db.py:24-58`: `subject`, `description`, `tags` (5-10 keyword EN), `scene_type`
(**enum ĐÓNG 14 loại**: `nature_water`, `nature_forest_field`, `mountain_desert`, `sky_cloud`,
`urban_street`, `urban_landmark`, `interior`, `people_activity`, `food`, `animal_wildlife`,
`underwater`, `space`, `abstract_texture`, `other`), `mood` (vocab đóng 19 từ), `shot_size`
(`wide/medium/close_up/extreme_close_up/aerial`), `has_people`.

**Chưa có** embedding/semantic search ở đâu cả — chỉ AND-match LIKE trên chuỗi.

### 8d. ⚠ CẢNH BÁO KIẾN TRÚC — `filter-overload-guard`

Nguyên tắc lặp ở `ranker/funnel.py:4-5`, `sourcer/viral.py:8`, `ranker/visiongate.py:6-7`:
**tính năng mới phải là CHÈN hoặc ĐIỂM, KHÔNG được đẻ thêm cửa loại.** Hiện chỉ có ĐÚNG 2
cửa loại (kỹ thuật + veto nghĩa nghiêm trọng). Phương án "cứng" cho REF-theo-chương đã từng
bị bác vì lý do này. Mật độ nếu làm → **bonus ĐỘNG**, không phải quota cứng.

---

## 9. LỆNH HỮU ÍCH

```bash
cd "c:/Users/NBPC/Documents/Claude/Projects/tool edit padoma/autoedit"
.venv/Scripts/python.exe -m pytest -q                    # cổng: 640 passed, 11 skipped
.venv/Scripts/python.exe scripts_thu_mini_hook.py --music "<mp3>" --footage <dir> --dur 20 --name X
```
⚠ **PHẢI dùng `.venv/Scripts/python.exe`** — python toàn cục KHÔNG có librosa.

Nhạc test: `E:\NHỊP NHANH\ĐÀN DỒN DẬP NHỊP NHANH` (4 bài, §4a).
Project mẫu user dựng tay: `E:\CapCut Drafts\0719` (13 cut, 152 BPM, đều trên beat).
4 draft mini-hook user đã duyệt: `E:\CapCut Drafts\MINIHOOK_{1_CLASSACT,2_PREMIERE,3_ENDOFERA,4_LOOKINGFURTHER}`.

---

## 10. TỒN ĐỌNG (chưa làm, user chưa yêu cầu)

- Cắt theo nhịp ở vùng **CÓ VOICE** — §1 nói KHÔNG, cần số đo mới mới được mở lại.
- `search_assets` không match `scene_type`/`mood` (§8b lỗ hổng 1) — vá rẻ, giá trị cao.
- Điều khiển **MẬT ĐỘ** footage trong vùng có voice (§8b lỗ hổng 3).
- `min_piece=1.5` là hằng chết (`cutter/pause.py:86`).
- `breath_specs`/`breath_q` trùng logic (`assembler.py:73-76` vs `:209-212`) — nên gộp.
- Track voice dùng `int()` thay `round()` (`assembler.py:198,202`) — trái bài học
  `assembler.py:374-376`; chưa lộ vì các segment cách nhau.
- Loop nhạc không được mô hình hoá (`music/plan.py:176-177`) — chương dài hơn phần nhạc
  còn lại thì hết accent target.
- **(M3)** `timeline_accents`/`timeline_beats` chưa biết span Δ — accent/beat trong vùng
  bài editor vẫn tính theo bài CŨ của chương. Chưa hại (mép Δ miễn snap + Δ chưa có
  footage) nhưng **BẮT BUỘC sửa ở M4/M5** khi cắt hình theo nhịp trong Δ.
- **(M3)** Bài editor đưa **chưa đo nhịp** (`beat_times`/`beat_strength`) vì nằm ngoài kho
  — M0 chỉ đo bài trong kho. M4 cần; đo bằng librosa ~0,5s/bài.
- **(M3)** Bài editor trùng bài đã chọn cho chương khác → nghe lặp, chưa cảnh báo.
