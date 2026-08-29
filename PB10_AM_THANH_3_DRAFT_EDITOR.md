# PB10 — GIẢI PHẪU ÂM THANH 3 DRAFT EDITOR THẬT (SP1-001/003/004)

> Quét 2026-07-10 phục vụ C đợt 3 (C1 ambient ô thở): parse `draft_content.json` của
> 3 draft ở `E:\PROJECT NHAN BAN\SPACE 1\` (26–30 phút/video), gom audio segment theo
> tên file, tách voice, đọc volume/fade/số lần dùng. Script: scratchpad `audio_scan.py`.
> Con số volume ở đây là THAM CHIẾU CHUẨN khi chỉnh mọi tham số âm lượng của máy.

## 1. Kiến trúc 6 lớp của editor (xếp theo thời lượng chiếm)

| # | Lớp | Ví dụ file thật | Volume | Cách dùng |
|---|---|---|---|---|
| 1 | **Nhạc nền cảm xúc** | `lắng đọng` `căng dần` `hy vọng` `nhẹ nhàng vô tận` `êm` `khoa học + bao la` `cảnh đẹp, êm ái` | **0.02–0.17** (điển hình 0.05–0.10) | File 2–4 phút đặt CẢ BÀI, **chồng 2–4 lớp cùng lúc** trên nhiều track; đổi theo mạch nội dung |
| 2 | **Drone/ambient NỀN chạy dài** | `ù ù điện ảnh` (199s) `ù ù vũ trụ` `amvien` `sâu lắng ambient` `deep space` `Dark Space` `Opening up Space` | **0.05–0.17** (khúc nhấn 0.2–0.5) | Gần như SUỐT video, không chỉ ô thở — chính là "room tone" e1 đang để sau |
| 3 | **Ambient KHỚP CẢNH cục bộ** (5–35s/khúc) | gió bão `Wind sound/storm` `wind roaring` · lửa/sôi cho cảnh MẶT TRỜI `lửa` `sôi sục mặt trời` `boiling water` · phố `Tel Aviv Ambiences` `Crowd Wall Street` `traffic + birds` · tuyết `Snow Storm` ×7 | **0.1–0.6** (điển hình **0.2–0.4**; gió bão 0.55–0.69) | Bám cảnh đặc biệt đang chiếu, có fade; ĐÚNG mô hình C1 v1 nhưng editor không giới hạn ở ô thở |
| 4 | **Whoosh chuyển động — RẤT DÀY** | `Swoosh` 1.1s **×16** · `vụtt` ×13 · `wind noise_whoosh` **×15** · `vụt phải qua trái` ×7 · `Buon (Whoosh movie)` | 0.1–0.6 | ~**20–30 lần/video** cho chuyển cảnh/camera vụt — máy hiện CHỈ có whoosh khi overlay |
| 5 | **SFX UI/data bám đồ họa** | `Data analysis` 1s ×5–6 · `UI提示` · `Pop-up tap` ×7 · typing/keyboard · camera click | 0.1–0.45 | Giống kỷ luật máy hiện có (bám overlay/chart) ✅ |
| 6 | **Impact/explosion/rumble bám SỰ KIỆN** | `Rocket ignition` `Rumble slow impact earth` `Earth rumbling` `爆炸` `explosion` | 0.03–0.64 (đa số ≤0.25) | Thưa, chỉ tại cú phóng tàu/va chạm/reveal |

**Phát hiện thêm:** video **GIỮ TIẾNG GỐC ~100%** (130/130 · 236/238 · 255/256 clip,
volume 1.0) — tiếng gốc footage là ambient tự nhiên miễn phí. Máy hiện VÔ TÌNH giống:
pycapcut `VideoSegment` default volume 1.0 + transcode giữ stream audio (aac 192k).
GIỮ NGUYÊN; nếu sau này clip viral lẫn tiếng thoại/nhạc bẩn thì mới cân nhắc.

## 2. Đối chiếu máy hiện tại vs editor

| Thứ | Máy | Editor | Nhận xét |
|---|---|---|---|
| Nhạc nền | 0.2 phẳng, 1 lớp (+nở 0.5 ô thở) | 0.05–0.10, **nhiều lớp chồng** | Máy 1 lớp nên 0.2 nghe tương đương; KHÔNG đổi đợt này |
| Ambient cảnh | chưa có → C1 | 0.2–0.4 điển hình | `AMBIENT_VOL=0.4` v1 nằm mép trên dải — hợp lý, tai anh chỉnh xuống nếu dày |
| Drone nền suốt video | chưa có (e1 để sau) | dùng RẤT đậm (lớp 2) | Ứng viên backlog mới sau C đợt 3 |
| Whoosh chuyển cảnh | chỉ khi có overlay | 20–30 lần/video tự do | Ứng viên backlog mới (cần luật vị trí — d3) |
| SFX UI/data | bám overlay/chart | y vậy | ✅ khớp |
| Tiếng gốc video | bật 1.0 (default) | bật 1.0 | ✅ khớp (vô tình) |

## 3. Rút ra cho C1 (mua gì — đã cập nhật COWORK_BRIEF)

- 2 loại ĐẮT NHẤT với niche space theo editor: **space drone/hum** (deep space, ù ù vũ
  trụ, cinematic low rumble) và **gió/bão** (storm wind, wind roaring low) → mỗi loại
  2–3 biến thể.
- Editor dùng tiếng **lửa/sôi cho cảnh mặt trời** — `scene_type` không phân biệt được
  (mặt trời tag = `space`): ambient theo SUBJECT là nâng cấp hướng C5 vision, KHÔNG cố
  nhét vào v1.
- Thư viện ambient đặt `F:\AutoEdit\ambient\<niche>\` (user chốt 2026-07-10 — cấu trúc
  theo niche "dễ nhớ khi có nhiều niche", tránh mất khi cài lại Win; suy từ
  `machine.json::library_root` cha + `project.niche`). Kho space: 29 file đã gom xong
  cùng ngày, manifest máy sinh sẵn.

## 4. Backlog gợi mở từ PB10 → ĐÃ THÀNH C đợt 3b (user duyệt 2026-07-10)

1. Drone nền toàn video → **S1**. 2. Whoosh standalone → **S3** (PB11 dưới đây cho luật
vị trí). 3. Ambient theo subject → **S2** (không chờ C5: kho local ĐÃ có vision tag
subject/tags/description; stock dùng visual_concept làm proxy). Xem
`MO_TA_VAN_HANH_SFX_HOAN_THIEN.md`.

## 5. PB11 — đo VỊ TRÍ whoosh 3 draft editor (2026-07-10, phục vụ S3/M4)

| Draft | Whoosh | Mật độ | Dài (median) | Volume (median) | Đầu-whoosh sát cut ≤0,5s | Cut nằm TRONG whoosh |
|---|---|---|---|---|---|---|
| SP1-001 (26,8', 120 cut) | 40 | 1,5/phút | 1,70s (1,1–9,5) | **0,32** (0,09–0,67) | 25% | 17/40 |
| SP1-003 (29,4', 232 cut) | 25 | 0,9/phút | 3,47s (0,8–15,1) | **0,18** (0,05–0,55) | 20% | 12/25 |
| SP1-004 (26,2', 263 cut) | 23 | 0,9/phút | 2,13s (0,4–10,2) | **0,20** (0,09–1,0) | 30% | 4/23 |

**KẾT LUẬN LẬT GIẢ THUYẾT "whoosh bám cut":** median |offset| tới cut gần nhất 1,2–3,0s
— editor KHÔNG rắc whoosh theo cut (video có 120–263 cut mà chỉ 23–40 whoosh). Mẫu thật:
**~1 whoosh/phút, volume thấp 0,2–0,3, whoosh DÀI trải qua KHÚC CHUYỂN LỚN** (chuyển ý/
chuyển chương/ camera move mạnh), khoảng nửa ôm cut bên trong. → Luật S3 v1: đặt whoosh ở
**chuyển CHƯƠNG + vào/ra ô thở** (những khúc chuyển lớn máy biết chắc), KHÔNG đặt theo cut
thường; mật độ tự nhiên ~1/phút; volume theo số đo (chi tiết chốt ở M4).
File editor hay dùng: Swoosh ×16, vụtt ×13, wind noise_whoosh ×20, Buon Whoosh movie ×10.

## 6. PB12 — whoosh CÓ bám mốc vào ô thở không? (2026-07-10, sau tai V8)

User nghi whoosh-auto-ô-thở sai → đo lại: mốc VÀO Ô THỞ = đầu khoảng nghỉ voice ≥1,5s
trên track voice thật của editor; đối chiếu cả mốc TEXT hiện lên (giả thuyết user).

| Draft | Ô thở voice | Whoosh | Whoosh quanh mốc vào ô thở ±1,5s | Whoosh quanh TEXT ±1s |
|---|---|---|---|---|
| SP1-001 | 18 | 40 | **0 (0%)** | 16 (40%) |
| SP1-003 | 18 | 25 | **0 (0%)** | 12 (48%) |
| SP1-004 | 21 | 23 | **0 (0%)** | 16 (70%) |

**KẾT LUẬN: editor KHÔNG BAO GIỜ đặt whoosh khi vào hình thở (0/88)** — luật S3 v1
"vào ô thở" của PB11 là suy diễn SAI từ "khúc chuyển lớn". Whoosh thật của editor bám
**TEXT hiện lên** (40–70%, đúng lời user: "chapter 2: the moon" lên hình → whoosh theo)
+ camera move/chuyển ý (phần còn lại — máy chưa đo được). → **S3 auto BỎ TRỌN**; máy đã
có overlay-SFX (text overlay nào hiện cũng có tiếng kèm) = một nửa mẫu editor; phần thiếu
= **chapter-title card + whoosh/swell** (backlog, kho swell ×8 + whoosh ×15 chờ sẵn).
(Ghi chú đo: SP1-004 track "voice" chọn theo nhiều-segment-nhất có thể lẫn track SFX —
không đổi kết luận vì 001/003 sạch và đều 0%.)

## 7. PB13 — volume SFX editor theo ngữ cảnh CÓ VOICE vs KHÔNG VOICE (2026-07-10)

User đề xuất SFX -15dB khi có voice / -10dB khi không voice (ô thở) và yêu cầu "học
project editor thật". Đo: SFX = đoạn audio ≤40s không phải voice/nhạc (nhạc+drone đặt
cả bài, đoạn dài); ngữ cảnh xét theo % trùng khoảng voice (≥60% = đè voice, ≤15% =
không voice). Script: `autoedit/scripts_phan_tich_pb13_sfx_vol_voice.py` (giữ trong
repo — M5 editor-learn dùng lại phép đo này cho mỗi project editor mới).

| Draft | Nhạc (median) | SFX ĐÈ VOICE (median, bỏ whoosh) | SFX KHÔNG VOICE (median, bỏ whoosh) |
|---|---|---|---|
| SP1-001 | 0.10 (−20dB) | n=45 · 0.25 (**−11.9dB**) | n=1 · 1.00 (outlier "clip ghép") |
| SP1-003 | 0.09 (−21dB) | n=33 · 0.28 (**−10.9dB**) | n=1 · 0.26 (−11.6dB) |
| SP1-004 | 0.06 (−25dB) | n=33 · 0.17 (**−15.6dB**) | n=12 · 0.32 (**−9.9dB**) |

**KẾT LUẬN: trực giác user KHỚP số editor.** SFX đè voice −11…−15.6dB (user đề xuất
−15dB — trong dải); SFX không voice −10…−11.6dB (user đề xuất −10dB — trúng); chênh
2 ngữ cảnh ~3–5dB đúng chiều "không voice to hơn". → CHỐT `SUBJECT_VOL=0.18` (−15dB
trong voice) + `SUBJECT_BREATH_VOL=0.32` (−10dB thắng ô thở). **Ambient LOẠI CẢNH giữ
0dB** (verdict V4 riêng: pad dài cùng phổ với nhạc, từng chìm ở 0.4 dưới nhạc-nở 0.5;
tiếng chủ thể giàu transient xuyên nền tốt hơn). ⚠️ Ghi chú tương quan: nhạc editor chỉ
0.06–0.10 (−20…−25dB) trong khi nhạc máy 0.2 thường / nở 0.5 ô thở — SFX −15dB của máy
sẽ ngồi NGANG mức nhạc thay vì trên nhạc như mix editor; nếu tai nghe chìm thì tầng
đáng chỉnh là NHẠC (hạ về hướng editor), không phải nâng SFX lại.
