# BÀN GIAO — NHIP-M4 ĐANG DỞ: nhịp cắt trong Δ CHƯA ĐẠT CỔNG TAI

> ✅ **ĐÃ GIẢI QUYẾT 2026-07-21 — M4 PHẦN NHỊP ĐÓNG TRỌN (V11 + V12 cổng tai DUYỆT).**
> GT1 đúng (lưới librosa trôi) + GT4 đúng một nửa (tai bám Ô NHỊP). Lời giải: foundation
> `e2-chuyen-footage-theo-phach.md` (user chốt luật phách 1&3 / phách 1) + madmom lo PHA
> / công thức lo LƯỚI + A′ shuffle RUN+HOLD. Chi tiết: NHAT_KY entry NHIP-M4b + memory
> `madmom-downbeat-luoi-cong-thuc`. CÒN NGỎ: footage THẬT trong Δ (§7 dưới vẫn đúng).
> File này giữ làm sử liệu — các bài học §1 (kiểm thứ tự segment, tin CapCut) VẪN ĐỨNG.

> **ĐỌC FILE NÀY TRƯỚC KHI LÀM TIẾP M4.** Viết 2026-07-20 ngay trước khi user clear chat.
> Đọc kèm: `CLAUDE.md` → `BAN_GIAO_NHIP_NHAC.md` (gói tổng) → file này.

---

## 0. TÌNH TRẠNG THẬT — ĐỌC KỸ, ĐỪNG TIN "ĐÃ ĐÚNG"

| Việc | Trạng thái |
|---|---|
| M3 nhạc editor cho Δ (phương án B) | ✅ **CỔNG TAI USER DUYỆT** (draft V4) |
| M4 — Δ vào ĐÚNG VỊ TRÍ 4:12 | ✅ **USER XÁC NHẬN MẮT** (từ draft V9) |
| M4 — **nhịp cắt trong Δ** | ❌ **CHƯA ĐẠT.** User nghe V10: *"chuyển footage vẫn chưa đúng nhịp beat chuyển"* |
| M4 — footage thật trong Δ | ⏸ chưa làm (hiện là slug giữ chỗ) |

**User nói nguyên văn khi dừng:** *"tôi thấy bạn chuyển footage vẫn chưa đúng nhịp beat
chuyển. có lẽ tôi và bạn đã nhầm ở đâu đó."*

⚠️ **Draft V10 CHƯA ĐẠT.** Mọi số đo trong commit `9fa01dc` nói "0,0ms lệch beat" đều
đúng về toạ độ nhưng **tai user vẫn nghe sai** → số đo hiện tại KHÔNG bắt được lỗi thật.

---

## 1. ★ BÀI HỌC ĐẮT NHẤT PHIÊN NÀY (đọc trước khi kiểm bất cứ draft nào)

**Tôi đã 3 lần báo "đã đúng" và 3 lần user phải tự mở CapCut bác lại.** Nguyên nhân:

### 1a. Phép kiểm bằng script BỊ MÙ với bug thứ tự segment
Script đọc `draft_content.json` rồi `sort` theo `start` → **luôn** thấy đúng. Nhưng CapCut
duyệt track **TUẦN TỰ theo thứ tự segment trong file**. Slug được add SAU footage nên nằm
cuối danh sách dù mốc ở giữa → CapCut dồn cả cụm xuống cuối video.

**LUẬT: kiểm draft PHẢI xét THỨ TỰ segment, không chỉ giá trị mốc:**
```python
starts = [s['target_timerange']['start'] for s in track['segments']]  # KHÔNG sort
assert starts == sorted(starts)
```
Đã fix (commit `c1d88f4`) + có regression `test_slug_fill_sorts_track_by_time`.

### 1b. File nói ĐÚNG mà CapCut hiện SAI → **TIN CAPCUT**
Memory `capcut-main-track-nam-cham-va-san-niche` đã ghi luật này; tôi đọc mà không áp dụng,
còn đổ cho "đọc file đang ghi", "CapCut ghi đè", "user mở nhầm draft". Tất cả đều sai.

### 1c. Đừng đọc draft khi assemble đang chạy
Có lúc tôi đọc phải file nửa vời rồi dựng cả một câu chuyện bug từ dữ liệu hỏng. Dựng xong
mới đọc; nghi ngờ thì dựng bản tên mới rồi đọc ngay.

---

## 2. Đã làm gì ở M4 (3 commit)

| Commit | Nội dung |
|---|---|
| `e95b002` | Đo nhịp bài editor lúc khai (`InsertSpec.music_beats/_beat_strength/_bpm/_tier`, librosa) + `coverage.insert_grid_cuts()` + `split_insert_windows()` + nối dây assembler |
| `c1d88f4` | **FIX NAM CHÂM**: sort `video_l1` theo thời gian sau khi lấp slug (§1a) |
| `9fa01dc` | `_meter_k` khóa lưới vào CHU KỲ NHỊP MẠNH + `INSERT_TARGET_SHOT` 3,0→2,0s |

**File đụng:** `project.py` (4 field), `cli.py` (`--music` đo nhịp), `packager/coverage.py`
(`insert_grid_cuts`/`split_insert_windows`/`_meter_k`), `packager/assembler.py` (nối dây +
sort + warning). Test: `tests/test_music_insert.py` (20 test). **pytest 681 passed, 11 skipped.**

---

## 3. Số đo hiện tại của V10 (đúng toạ độ, VẪN SAI TAI)

Δ = 252,18→282,18s (4:12–4:42), bài `Romeo - End of an Era`, 89,15 BPM, tier A, 202 beat.

```
15 hình: 2,3 / 2,0 ×13 / 1,7s     khoảng cách beat: 3,3,3,3,3,3,3,3,3,3,3,3,3
lệch mép so beat: 0,0ms           strength tb mép: 0,465 (trung vị bài 0,289)
mép rơi beat yếu: 2/14            thứ tự segment: tăng dần ✅
```

Lịch sử điều chỉnh (để không thử lại vòng cũ):
| Lần | Cách | Kết quả | Tai user |
|---|---|---|---|
| V6-V9 | k=4 (round(3,0/period)), search ±2 → ±1 → 0 | shot 2,0/4,0s chênh 2,53× rồi đều 2,7s | ❌ "nhiều footage không rơi đúng nhịp" |
| V10 | `_meter_k` khóa chu kỳ 3 + target 2,0s | 15 hình đều 2,00s, strength +28% | ❌ **"vẫn chưa đúng nhịp"** |

---

## 4. ★ GIẢ THUYẾT HÀNG ĐẦU CHO PHIÊN SAU (chưa thử)

### GT1 — Lưới beat librosa KHÔNG ĐỀU, cắt mỗi 3 beat thì SAI SỐ CỘNG DỒN ⭐
Đo thật 20 beat đầu, khoảng cách beat liên tiếp:
```
0.696, 0.674, 0.673, 0.674, 0.650, 0.673, 0.674, 0.673, 0.650, 0.673,
0.674, 0.650, 0.673, 0.674, 0.650, 0.673, 0.674, 0.673, 0.673, 0.651
   -> min 0,650  max 0,696  DAO ĐỘNG 46ms
```
Mẫu `0,674 / 0,674 / 0,650` lặp lại → librosa đang **làm tròn về khung phân tích**
(hop_length), không phải nhịp thật. Cắt mỗi 3 beat = cộng dồn sai số → mép trôi dần khỏi
nhịp tai nghe. **Cách thử:** so mép cắt với **downbeat** (`analyze_rhythm` có trả
`downbeats`) thay vì `beat_times`; hoặc dựng lưới từ BPM ổn định (`b0 + n*period_chuẩn`)
rồi mới hạ cánh — NHƯNG cẩn thận: đó chính là cách đẻ ra bug b08/b09 (bàn giao §5a).

### GT2 — Mép VÀO Δ lệch −302ms kéo lệch cảm nhận cả đoạn
Mép đầu Δ cố định theo chỗ voice dứt (252,184), không rơi beat (beat gần nhất 252,486).
Hình đầu dài 2,3s thay vì 2,0s. Tai có thể lấy mốc từ nhát đầu → nghe cả chuỗi bị lệch.
**Cách thử:** cho hình đầu Δ kéo tới beat thật đầu tiên rồi mới bắt đầu lưới đều.

### GT3 — `SNAP_LEAD` chưa áp cho Δ
Editor thật cắt **TRƯỚC beat 80ms** (`SNAP_LEAD=0.08`, đo từ kênh top, memory
`editor-music-sync-study`: lead 120-175ms). Lưới Δ hiện cắt ĐÚNG beat, không lead.
Cắt đúng beat có thể bị cảm nhận là **trễ**. **Cách thử rẻ nhất, thử trước GT1.**

### GT4 — "beat" tai user nghe ≠ beat librosa
Bài 89 BPM nhịp 3 → tai có thể bám **ô nhịp (bar)** ~2,02s chứ không phải beat lẻ.
Nếu đúng thì phải neo vào downbeat. **Cách thử:** hỏi user gõ nhịp tay theo nhạc, hoặc
xuất click-track (`test_music_rhythm.py::test_click_track_tier_a` có sẵn hàm) cho user nghe
đối chiếu — **cách này dứt điểm nhất, nên làm ĐẦU TIÊN.**

---

## 5. VIỆC ĐẦU TIÊN NÊN LÀM Ở PHIÊN SAU

1. **Hỏi user 1 câu trước khi code:** trong Δ, tai anh bám vào cái gì — tiếng trống/beat lẻ
   hay ô nhịp? Và mép nào cụ thể nghe sai (giây thứ mấy)? Không có thông tin này thì lại
   đoán mò như phiên vừa rồi.
2. **Xuất click-track chồng lên Δ** cho user nghe: nếu click của máy đã lệch tai user thì
   lỗi ở tầng ĐO NHỊP (GT1/GT4), không phải tầng cắt → tiết kiệm cả vòng sửa sai chỗ.
3. Thử **GT3 (lead 80ms)** trước vì rẻ nhất — đổi 1 hằng, dựng lại, nghe.

⚠️ **KHÔNG tự chốt "đã đạt".** Cổng tai là của user (P4).

---

## 6. Lệnh tái lập

```bash
cd "c:/Users/NBPC/Documents/Claude/Projects/tool edit padoma/autoedit"
.venv/Scripts/python.exe -m pytest -q                      # 681 passed, 11 skipped
# Δ đã khai sẵn trong project (beat 36, 30s, nhạc đã đo nhịp) — chỉ cần:
.venv/Scripts/python.exe -m autoedit.cli assemble projects/rd89-oman-10min-20260720
```
Đổi nhịp: `INSERT_TARGET_SHOT` / `INSERT_SEARCH_BEATS` / `_meter_k` ở `packager/coverage.py`.
Δ không đổi độ dài thì **KHÔNG cần chạy lại cut/music/source** (chỉ assemble ~1-2 phút).

**Draft:** V10 = mới nhất (nhịp chưa đạt) · **V4 = M3 sạch, user đã duyệt tai** ·
V5-V9 hỏng (bug nam châm), **nên xóa** — user chưa xác nhận nên tôi giữ nguyên.

Nhạc test: `E:\NHỊP NHANH\ĐÀN DỒN DẬP NHỊP NHANH\Romeo - End of an Era.mp3` (89 BPM, nhịp 3).

---

## 7. Tồn đọng M3 còn nguyên (chưa làm)

1. `timeline_accents`/`timeline_beats` **chưa biết span Δ** — accent/beat trong vùng bài
   editor vẫn tính theo bài CŨ của chương. Chưa hại vì mép Δ miễn snap, nhưng **phải sửa
   khi làm footage thật trong Δ**.
2. Bài editor trùng bài chương khác → nghe lặp, chưa cảnh báo.
3. Footage thật trong Δ (M4 phần b "project editor đưa") — **cần user chỉ nguồn footage**.
