# M-LEVEL — kiểm soát mức nhạc nền theo LOUDNESS ĐO THẬT (thay hằng số mù)

> Tên gọi chính thức: **M-LEVEL** (cùng họ M-VOL / M-GRID / M-CHANGE của MUSIC SYNC).
> 2 vấn đề con: **M-LEVEL-THỞ** và **M-LEVEL-VOICE**. User nêu 2026-07-14.
> Trạng thái: ⏸ **TẠM ĐÓNG (user chốt 2026-07-14: "khó làm, cần thì làm sau")** —
> dừng NGAY TRƯỚC cổng tai vòng 2. Đã xong: user chọn phương án A (band-clamp), thước
> đo LUFS + band hiệu chuẩn bằng 6 mốc tai, preview 4 wav đã render. Mở lại = user
> nghe 4 file §4 → duyệt → wiring theo §5. CHƯA đụng một dòng pipeline nào.

## 1. Vấn đề

Volume nhạc hiện đặt theo **hằng số** (nép 0.2 khi voice / nở 0.5 ở hình thở / hook
0.30-0.35) — mù hoàn toàn với độ to thật của khúc nhạc đang phát → hình thở lúc quá to
lúc quá nhỏ (**M-LEVEL-THỞ**), nhạc dưới voice thi thoảng vọt to / chìm mất
(**M-LEVEL-VOICE**). Đo trên DS3-084 _V5: 25/33 ô thở ngoài band tai, đa số QUÁ NHỎ.

## 2. Thước đo — bài học hiệu chuẩn QUAN TRỌNG (2026-07-14)

User cho 6 mốc tai trên _V5: BÉ = 1:48, 2:18, 4:03 · VỪA = 4:21, 4:34, 6:53. Kết quả đo:

| thước | BÉ (3 mốc) | VỪA (3 mốc) | tách được? |
|---|---|---|---|
| peak dBFS 400ms (≈ đồng hồ CapCut) | -16.3 / -13.5 / -17.8 | -12.0 / -14.1 / -9.1 | ❌ chồng lấn |
| RMS 400ms | -22.7 / -24.6 / -24.1 | -21.7 / **-24.9** / -19.7 | ❌ VỪA còn nhỏ hơn BÉ |
| **LUFS momentary (K-weighting BS.1770)** | -24.8 / -26.9 / -25.9 | -22.1 / -22.2 / -18.3 | ✅ **khoảng trống sạch** |

→ **Chuẩn M-LEVEL = LUFS momentary (cửa sổ 400ms) của LỚP NHẠC**, không phải peak.
Lý do: 2 bài nhạc khác phổ tần — bài sáng (nhiều trung-cao) tai nghe to hơn dù đỉnh
thấp hơn; K-weighting mô phỏng đúng độ nhạy tai. ⚠️ Band -10..-5 user đọc từ đồng hồ
CapCut ban đầu KHÔNG khớp tai chính user (nếu áp sẽ đẩy nhạc to hơn mốc "vừa" ~6dB) —
**mốc tai là chân lý, số đọc đồng hồ chỉ là gợi ý**.

## 3. Band chốt (LUFS momentary, lớp nhạc riêng)

- **THỞ: -22.5 … -17.5** (center -20) — ôm trọn 3 mốc VỪA của user.
- **VOICE: -34 … -24** (center -29) — median phân bố _V5 (draft đã duyệt tai) là -29.1,
  band = median ±5dB: chỉ bắt outlier "thi thoảng vọt/chìm", giữ swell tự nhiên.

Phương án user chọn: **A — band-clamp** (giữ dynamics của bài, chỉ kéo về biên khi vượt).
Công thức: `volume(t) = vol_cũ(t) × 10^(delta/20)`, delta = lượng vượt band (mượt 2s,
trần ±12dB, multiplier ≤2.0, nhạc lặng <-50 LUFS không kéo). **Zone hook**: M-VOL voice
giữ nguyên (đã qua cổng tai M2), CHỈ bù ô thở — 3 mốc BÉ của user đều nằm trong hook.

Kết quả dự đoán trên _V5: mọi ô thở về band (BÉ -24.7/-26.1/-25.8 → ~-21.7/-22.1/-21.7;
VỪA gần như đứng yên); voice ngoài band 28.1% → 18.6%.

## 4. Bản nghe thử vòng 2 (CHỜ user)

`autoedit\projects\ds3-084-womb-cannibalism-20260713-224919\m_level_preview\`:
`95s-285s_{OLD,A}.wav` (phủ 5/6 mốc tai, cả 3 mốc BÉ) + `395s-545s_{OLD,A}.wav`
(mốc VỪA 6:53 + cụm ô thở chìm 461/494/544s). Trộn offline đủ voice+nhạc+ambient+
drone+SFX đúng gain/fade/keyframe draft. Script: `autoedit\scripts_phan_tich_m_level_preview.py`.

## 5. Kế hoạch nối vào pipeline (SAU cổng tai vòng 2)

Sửa **duy nhất tầng ducking** (`packager/ducking.py` + `_duck_music` assembler):
envelope đổi từ hệ số tuyệt đối sang target-LUFS → hệ số tính từ loudness nguồn
(K-weighting đo bằng scipy lfilter — dependency đã có qua librosa). Giữ nguyên: ramp
2.5s, MIN_BREATH 1.5, keyframe theo giờ-file-nguồn, fade/crossfade. Keyframe bù thêm
mỗi ~2s chỉ chỗ lệch >1.5dB (đỡ rác). Cổng: pytest regression → cổng TAI trên draft thật.

## 6. Rà chồng chéo (P5 — các tầng CÙNG QUẢN volume nhạc)

| Tầng | Đụng? | Kết luận |
|---|---|---|
| `MUSIC_VOLUME 0.2` tĩnh + ducking F8 (0.5 thở, ramp) | **CÓ — chính chỗ sửa** | M-LEVEL thay cách TÍNH mức, sống trong ducking; chỉ MỘT tầng ghi keyframe volume nhạc |
| M-VOL hook (0.30/0.35, đã qua cổng tai M2) | một phần | voice hook GIỮ; ô thở hook ĐƯỢC bù (3 mốc BÉ user nằm ở đây) |
| Fade/crossfade (MUSIC_XFADE 3s, M-CHANGE 0.5s deepsea) | không ngược chiều | fade nhân CHỒNG lên keyframe; dip crossfade là chủ đích, silence-floor chặn không bù |
| Ambient/drone/SFX (track riêng) | không | M-LEVEL chỉ đo + chỉnh lớp nhạc |
| Foundation e1-sound-design (0.2/0.5 chốt tai V6/V10) | **CÓ** | khi wiring: thêm block "📌 LỆCH SO VỚI BẢN GỐC" vào e1 (luật foundation-deviation) |

## 7. Còn ngỏ

- Cổng tai vòng 2: user nghe 4 file, xác nhận band LUFS mới.
- Mốc 794.7s vẫn -25.8 sau bù (trần +12dB chạm nóc vì khúc nhạc quá lặng) — chấp nhận
  hay nới trần, chờ tai.
- Video khác niche/bài nhạc khác: band THỞ hiệu chuẩn trên deepsea _V5 — niche mới nên
  kiểm lại 1 lần bằng tai trước khi tin.
