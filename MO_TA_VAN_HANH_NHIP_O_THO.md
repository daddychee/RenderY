# MÔ TẢ VẬN HÀNH — LƯỚI BEAT Ở Ô HÌNH THỞ (NHIP-M1)

> Gói CẮT THEO NHỊP NHẠC, mốc M1 (`BAN_GIAO_NHIP_NHAC.md` §3). Viết 2026-07-19.
> Trạng thái: ✅ **ĐÓNG TRỌN — CỔNG TAI USER DUYỆT 2026-07-20** (draft
> `RD89_OMAN_10MIN_20260720`, mép giữa miếng beat 65 lệch 0,2ms so beat nhạc thật;
> kèm fix trần đuôi commit c04def1, pytest 651).

---

## 1. Làm gì

Ô hình thở (voice ngừng, footage riêng chạy) — trước đây chia 1-3 miếng theo tỷ lệ DNA
(`k_fractions`), mép cắt rơi chỗ bất kỳ so với nhạc. Nay khi **music-sync bật**: mép cắt
giữa các miếng **hạ cánh trên BEAT THẬT** của bài nhạc đang phát (ưu tiên beat MẠNH,
đúng thuật toán mini-hook đã duyệt), số miếng do lưới beat quyết — **trần 3 miếng BỎ**
(user chốt 2026-07-19).

Vùng CÓ voice: **KHÔNG ĐỤNG** (luật đứng hai-hệ-cắt, `BAN_GIAO_NHIP_NHAC.md` §1).

## 2. Số đo chốt "khoảng nhắm" (đo 2026-07-19)

Bài học §4a bàn giao: đếm theo SỐ BEAT cứng thì co giãn theo BPM quá tay (89 BPM ra shot
5,4s). Tai người cảm shot theo GIÂY → **nhắm THỜI GIAN, quy ngược ra số beat**:

| Nguồn đo | Kết quả |
|---|---|
| Draft `0719` (user dựng tay), đoạn khoá | 5 shot **3,13–3,23s** (= 8 beat @152 BPM) |
| 246 miếng thở thật editor (deepsea+life-in, ô k≥2, ≥1s) | p25 2,23 · **p50 2,86** · p75 3,00 · p90 4,07s |

→ `BREATH_TARGET_SHOT = 3.0s` · số beat/miếng `k = max(2, round(3.0/period))` (89 BPM → 4
beat = 2,7s; 152 → 8 = 3,2s; 172 → 9 ≈ 3,1s) · sàn miếng = `min_piece` DNA niche (1,5s —
khớp p10 editor; hằng-chết cũ nay ĐƯỢC dùng thật ở đường beat).

Hạ cánh: mốc dự kiến → beat THẬT mạnh nhất trong ±2 beat — **tái dùng `beat_grid` nguyên
vẹn** (đã duyệt 4 project mini-hook, 2 test hồi quy bug b08/b09 canh sẵn).

## 3. Chạy ở đâu — HAI TẦNG (vì sao phải hai)

**Tầng 1 — stage SOURCE** (`sourcer/breath.py`): tính lưới beat trên hệ timeline
(chiếu nhạc→timeline qua `timeline_beats`, boundary DỰ ĐOÁN = `timeline_start` chương)
→ ra **số miếng + độ dài** → pick clip như cũ (neo chủ thể/cỡ cảnh 3.0 nguyên vẹn).
Số miếng chốt Ở ĐÂY vì chỉ source biết kho còn clip (bẫy ① — hở timeline = bug NAM CHÂM).
Record đánh dấu `BreathShot.beat_cut=True`.

**Tầng 2 — stage ASSEMBLE** (`retime_breath_grid`, coverage.py): sau khi M-CHANGE chốt
boundary thật + snap accent xong → **tính LẠI vị trí mép giữa các miếng** trên boundary
thật, dời mép về beat, **số miếng GIỮ NGUYÊN** (đúng số clip đã pick). Vì sao phải tính
lại: M-CHANGE có thể dời điểm đổi nhạc chương tới ±2s so dự đoán → beat tính ở source
lệch theo → cắt trật nhịp cả giây (bug b08/b09 dạy: lệch 1 beat là tai nghe ra).
Retime xong ghi `dur` mới ngược vào `project.breath_shots` (project.json = sự thật;
`first_piece_end` của SFX chủ thể đọc đúng số mới).

**Điều kiện bật per-ô (tự động):** có `music_plan` (music-sync bật) · bài chương đó tier
≠ C · ≥2 beat trong vùng footage của ô. Thiếu bất kỳ → **đường DNA cũ nguyên vẹn**
(fail-open, kể cả lỗi đọc index nhạc). Lưới thiếu mốc lúc retime (m < n−1, hiếm) → giữ
mép cũ của ô đó (off-beat nhưng lành), đếm vào warning.

## 4. Bỏ trần 3 miếng — phạm vi

- **Đường BEAT: trần bỏ** — số miếng = lưới quyết (ô 10s @109 BPM ra 4 miếng ~2,75s).
- **Đường DNA (không music-sync): trần 1-3 GIỮ** — `k_fractions` chỉ có mẫu editor cho
  k=2,3; bỏ trần ở đây phải sửa 2 file + không có số đo đỡ lưng. User chốt bỏ trần trong
  ngữ cảnh "sáng tạo theo beat nhạc" → hiểu là đường beat. Muốn bỏ cả đường DNA → hỏi lại.

## 5. RÀ CHỒNG CHÉO (P5) — các tầng cùng quản mép cắt trong ô thở

| Tầng | Đụng không? | Kết luận |
|---|---|---|
| `split_breath_shots` | Vẫn chẻ theo durs từ source; retime chỉ DỜI mép giữa miếng | không ngược chiều |
| `apply_j_cuts` | Ô có shot thở: hold 0,5 < 1,2 → không J-cut (như cũ) | không đụng |
| `snap_to_accents` — mép GIỮA miếng | Luật loại `w.breath_shot and nxt.breath_shot` **GIỮ NGUYÊN** nhưng ý nghĩa ĐẢO: trước là "ngoài gói", nay là "đã nằm trên beat — snap accent−80ms sẽ kéo LỆCH beat". Khai báo tại đây + comment code (bẫy ③ bàn giao: không lặng lẽ) | cố ý giữ |
| `snap_to_accents` — mép VÀO/RA ô | Vẫn được snap như cũ (ưu tiên 1/body); retime chạy SAU snap nên lưới tôn trọng mép đã snap | thuận chiều |
| M-CHANGE boundary | Neo vào mép gần `timeline_start` chương nhất: mép chương thật cách ≤~0,3s, mép giữa-miếng gần nhất ≥1,2s → boundary không bao giờ neo vào mép sẽ-bị-retime | không lật nhau |
| Hook SFX S3 (`cuts_log`) | Ô thở trong hook có nhiều mép hơn → thêm ứng viên slot; mật độ do `hook_sfx_slots` trần per-minute + busy điều tiết | warning-only, theo dõi cổng tai |
| Pacing DNA (`_warn_pacing_dna`) | Miếng ngắn hơn → cpm nhích ở video nhiều ô | validator warning-only |
| Ducking `BREATH_VOL` | Nhạc NỞ TO đúng ô đang cắt nhịp | cộng hưởng, không đụng code |
| Ambient/subject-SFX | Đọc ô theo `breath_slots` (cả ô, không theo miếng); `first_piece_end` đọc `dur` — đã sync số retimed | khớp |
| `mark_music_stale` | Cut lại → plan xóa → source lại tự về đường DNA (đúng thiết kế) | an toàn |

**Giả định tọa độ ở source:** vùng footage = `[beat.timeline_end + HOLD, beat.timeline_end
+ breathing_after]`; beat mang ô luôn cuối segment và `plan_micro_pauses` không bao giờ
chọn beat có breathing → micro = 0. Sai số nếu có → tầng 2 retime sửa trên tọa độ window thật.

## 6. File : dòng

| File | Đổi |
|---|---|
| `music/minihook.py` | +`BREATH_TARGET_SHOT`/`BREATH_MIN_PIECE` + `breath_cuts()`/`breath_pieces()` (bọc `beat_grid` pattern đều k) |
| `music/plan.py` | +`timeline_beats()` — beat_times+beat_strength chiếu lên timeline (song song `timeline_accents`; record thiếu strength → mảng 0, vẫn cắt được) |
| `project.py` | `BreathShot.beat_cut: bool = False` (project cũ load bình thường) |
| `sourcer/breath.py` | `_beat_map()` (fail-open) + nhánh lưới beat trong `pick_breath_shots` |
| `packager/coverage.py` | +`retime_breath_grid()` + comment đảo-ý-nghĩa tại luật loại snap |
| `packager/assembler.py` | gọi retime sau snap (trong block music-sync) + sync `dur` + warning `NHIP-M1` |

## 7. Cách kiểm (cổng)

- pytest: `.venv/Scripts/python.exe -m pytest -q` — cổng 640+.
- Cổng TAI/MẮT user: dựng video thật music-sync (deepsea/space/life-in) → mở draft, soi
  các ô thở dài (report/warning `NHIP-M1: retime X/Y ô`): hình đổi đúng cú nhạc, không
  vụn (<1,5s), không trễ-một-nhịp. **Claude KHÔNG tự báo đạt.**
