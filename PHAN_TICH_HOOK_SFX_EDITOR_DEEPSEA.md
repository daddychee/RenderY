# PHÂN TÍCH — SFX ở HOOK của editor deepsea (23 draft own, đo 2026-07-13)

> Gói HOOK SFX bước 1 (user duyệt 2026-07-13 sau khi nêu "hook chỉ 1 layer ục ục" trên
> DS5-083 V3 — memory `ds5-083-4-van-de-sfx-lap`). ĐO TRƯỚC, luật sau — thiết kế ở §4
> CHỜ USER DUYỆT rồi mới code.

## 1. Cách đo

- 23 draft own `E:\PROJECT NHAN BAN\{DEEPSEA 1, DEEP SEA 3, DEEP SEA 5}` (loại 4 bẫy
  cũ: Spain-dup, DS1_074 compound, DS1-053 trùng tập, DS1-042 rỗng). READ-ONLY.
- **Hook = 0 → mốc chương 2 trong TCF** `topic + chapter video.txt` (23/23 có TCF).
- Phân loại audio TÁI DÙNG `editor_learn.mine.classify` (rules deepsea per-niche);
  đếm "SFX điểm" = segment dest sfx/ambient/hold, **loại segment >45s** (bed/pad — đã
  có tầng S1) và **loại file ElevenLabs lọt lưới** (voice không nằm voice-track, 24 seg).
- Script: scratchpad `do_hook_editor.py` (chạy lại được).

## 2. Số đo chính

| Chỉ số | Giá trị |
|---|---|
| SFX điểm/phút ở HOOK | **median 4,77** (min 1,5 – max 13,5) |
| SFX điểm/phút ở THÂN BÀI | median 1,63 → **hook ≈ 3× thân bài** |
| Draft có hook KHÔNG SFX điểm | **0/23** — hook nhiều tiếng là chuẩn editor, không phải cá biệt |
| Volume segment SFX hook | median **0,56** (n=556) — KHÔNG copy thẳng, phải quy tương quan lớp như PB10 (editor 0,5 ↔ máy 0,18) |
| Cut video ở hook | 12–15 cut/phút (dày hơn DNA toàn bài 11,9) |

**SFX bám vào đâu (556 tiếng hook):**

| Mốc | ≤0,10s | ≤0,25s |
|---|---|---|
| CUT video | 36% | **48%** |
| TEXT overlay | 2% | 3% |

- **13% tiếng vào TRƯỚC cut 0–200ms** ("whoosh-vào-hit" — khớp khóa pha yếu đo ở 30
  video viral space, `editor-music-sync-study`).
- ⚠ NGƯỢC với PB12 (space: whoosh 40–70% đi cùng TEXT, 0% mốc ô thở): **deepsea bám
  CUT, không bám text.** Luật hook vì thế phải per-niche, và KHÔNG mâu thuẫn PB12 (PB12
  bỏ whoosh-bám-Ô-THỞ; đây là bám-CUT-trong-hook).

## 3. Editor dùng LOẠI tiếng gì ở hook (top, cộng dồn 23 draft)

1. **Hiện trường nước** (nhiều nhất): Underwater Bubbles ×63 · Waves Crashing+Seagulls
   ×22+10 · dưới nước 4/ù ù ×30 · whale blowing ×11 · splash ×7 → nhóm này máy ĐÃ CÓ
   ĐƯỜNG (S2 loài/water_churn/ocean + C1 + bed S1) — sau gói nước-động sẽ tự dày thêm.
2. **Camera shutter/click ×~30** — đi với ảnh tĩnh/khoảnh khắc "chụp" (Ken Burns!).
   Kho: folder `CLICK`/`CAMERA` trong SOUNDEFFECT **chưa nạp**.
3. **Impact/boom**: ES Designed Boom Big Hit ×8 — folder `Tiếng BOOM` chưa nạp.
4. **Spooky ambience riser** ×22 (Asak SFX Sci Fi Cinematics) — dạng KINH DỊ/KINH DỊ 2.
5. **Nhạc stinger ngắn** (<45s: Fire and Ice, Synthetic Network, Signals of Distress
   ×~25) — editor cắt nhạc làm hiệu ứng đoạn; ghi nhận, chưa bàn tầng này.

## 4. Thiết kế đề xuất (CHỜ USER DUYỆT — chưa code)

Tầng mới **S3-HOOK** (chỉ chương 1, chỉ niche có số đo — deepsea trước):

1. **Nạp 3 nhóm SOUNDEFFECT**: `Tiếng BOOM` (impact) · `WHOSH` + `Underwater Whoosh`
   (whoosh) · `CLICK`/`CAMERA` (shutter) — vào sfx library (không phải ambient).
2. **Luật đặt**: tại CUT video trong hook — ưu tiên cut đã snap accent music-sync
   (đã có M-SNAP); whoosh có knob lead 0–120ms TRƯỚC cut; camera click CHỈ tại cut
   vào ẢNH/graphic (địa chỉ rõ, khớp hành vi editor).
3. **Mật độ đích**: tổng SFX hook (S2 hiện trường + S3 mới) hướng tới dải median editor
   ~4–5 tiếng/phút — S3 chỉ BÙ phần thiếu, không đặt cạnh tiếng S2 đã có (chống dồn).
4. **Volume**: KHÔNG lấy 0,56 thẳng — quy tương quan lớp (PB10) rồi chốt ở CỔNG TAI.
5. **Rà chồng chéo (sơ bộ, làm đủ khi viết mô tả vận hành)**: hook sẽ có 5 lớp âm
   (voice · nhạc M-VOL 0.30 · bed 0.25 · S2 loài/hiện trường · S3 hit/whoosh) — kiểm
   CHUNG 1 cổng tai; PB12 không bị lật (xem §2); music-sync M-SNAP là bạn (cùng mốc cut).

## 5. Caveat

- Phân loại theo tên file editor — nhạc stinger ngắn lẫn trong đếm (~25/556, không đổi
  median); 1 file voice đã loại tay.
- DS3_007 body 5,8/ph > hook 3,0/ph (video orca — tiếng loài dày toàn bài): mật độ hook
  cao là MẪU CHUNG (18/23 draft hook > body) nhưng không tuyệt đối.
