# MÔ TẢ VẬN HÀNH — DUCKING KEYFRAME (F8)

> **✅ ĐÃ CODE + ĐẠT cổng mắt+tai V7 (2026-07-04).** Code: `packager/ducking.py` +
> `_duck_music` trong assembler. Lưu ý sống còn khi sửa sau này: `time_offset` keyframe
> tính theo thời gian trong FILE NGUỒN, không phải từ đầu clip (memory
> [[capcut-volume-keyframe]] — bài học V6).
>
> CỔNG DUYỆT VẬN HÀNH cho backlog số 1 của [[e1-sound-design-nhac]]. Đọc → duyệt →
> mới code. Nguyên văn user (GHI_CHEP_GOC §3): *"khi voice bắt đầu nói thì nhạc nền bé
> lại. khi voice không nói (đoạn hình thở) thì nhạc nền to lên. mức hạ db bao nhiêu
> chúng ta sẽ học dna niche hoặc quyết định sau."*

---

## 1. Bài toán

Hiện tại nhạc nền **phẳng 0.2 suốt video** (`MUSIC_VOLUME=0.2`, comment code ghi sẵn
"ducking keyframe là Phase 1"). Hệ quả: khoảng hình thở chỉ "thở" được một nửa — hình
nghỉ nhưng nhạc vẫn nép như lúc có voice, khoảng thở nghe trống thay vì nở.

Ducking v1 = **nhạc nở ra ở khoảng thở, nép xuống khi voice nói**, chuyển mượt bằng ramp.

## 2. Nguyên liệu đã khảo sát (không phải đoán)

| Thứ | Ở đâu | Kết luận |
|---|---|---|
| Lúc nào voice nói / nghỉ | `project.segments`: `timeline_start`/`timeline_end` từng đoạn voice + `breathing_after` | Biết CHÍNH XÁC từ cấu trúc timeline — **không cần dò waveform** |
| Keyframe volume | pycapcut `AudioSegment.add_keyframe(offset_µs, volume)` → `KFTypeVolume`, nội suy tuyến tính | Đường ống CÓ SẴN trong thư viện — pipeline chưa từng dùng keyframe nào |
| Nhạc đang đặt thế nào | `_lay_music`/`_add_music_by_chapter`: theo chương, 2 track `music`/`music2` luân phiên, crossfade 3s, fade in/out mép bài | Ducking chèn keyframe **sau khi** nhạc đặt xong — không sửa logic chọn/đặt nhạc |

## 3. Cách vận hành (4 bước, chạy trong assemble)

1. **Lập lịch voice/thở** từ `project.segments`: khoảng có voice = `[timeline_start,
   timeline_end]`. Khoảng nghỉ **ngắn hơn NGƯỠNG_THỞ (1.0s)** được nuốt vào voice liền
   mạch — chống **pumping** (nhạc nhấp nhô theo từng hơi lấy giọng — cạm bẫy "giật cục"
   e1 đã ghi). Phần còn lại = khoảng thở thật (kể cả khoảng thở kết video).
2. **Quét mọi segment nhạc** trên `music` + `music2` (chạy chung cho cả 2 nhánh
   `--music` tay và thư viện tự chọn) → giao lịch voice/thở với khoảng thời gian của
   từng segment.
3. **Chèn keyframe volume** cho từng segment:
   - đang voice → `DUCK_VOL`; đang thở → `BREATH_VOL`;
   - thở→voice: ramp XUỐNG **kết thúc đúng lúc voice bắt đầu** (xuống sớm — chữ đầu
     tiên phải rõ); voice→thở: ramp LÊN bắt đầu tại lúc voice dứt;
   - độ DỐC ramp cố định (đi hết DUCK→BREATH trong RAMP giây): khoảng thở dài → nở
     trọn có mặt bằng; khoảng thở ngắn hơn 2×RAMP → chỉ phồng nhẹ một phần rồi hạ —
     KHÔNG dốc gắt hơn để nhét cho đủ mức;
   - neo keyframe ở 2 mép segment để mức đúng ngay từ đầu;
   - giây→µs dùng `round()` + clamp trong segment (bài học SegmentOverlap 1µs).
4. **Fade in/out + crossfade chương GIỮ NGUYÊN** (fade là material riêng chồng lên
   keyframe — kiểm ở draft test, mục 6).

## 4. Tham số — hằng số đầu file, 🔸 điểm treo tai anh chốt

| Tham số | v1 | Vì sao |
|---|---|---|
| `DUCK_VOL` | **0.20** | GIỮ NGUYÊN mức hôm nay — lúc voice nói video nghe y hệt V5 đã qua tai anh; ducking chỉ THÊM phần nở |
| `BREATH_VOL` | **0.50** | nhạc nở ~+8dB lúc thở — khởi điểm nhẹ; tham chiếu -12…-18dB chốt sau bằng tai + DNA (điểm treo e1) |
| `RAMP` | **2.5s** | user chỉnh 2026-07-04 (bản đầu 0.4s → "muốn dài hơn 2 giây"); dốc CỐ ĐỊNH — khoảng thở ngắn thì nhạc chỉ nở một phần (phồng nhẹ), không dốc gắt |
| `NGƯỠNG_THỞ` | **1.0s** | nghỉ ngắn hơn → nhạc giữ mức thấp, không nhấp nhô |

## 5. KHÔNG làm đợt này

- **Không ambient** (backlog 2 của e1 — chờ Phase B: tag loại-cảnh + kho ambient).
- **Không đo LUFS/loudness thật** — chỉ nhân volume; mở khi nghe thật có vấn đề (e1 đã treo).
- **Không đụng** voice, SFX, logic chọn nhạc; **không thêm gì vào phễu c5**.

## 6. Rủi ro & cách kiểm (P1 — không suy đoán một mình)

Hai behavior CapCut chưa chắc 100%: (i) `time_offset` keyframe tính từ **đầu segment
hay đầu bài nhạc**; (ii) keyframe + volume tĩnh + fade **chồng nhau thế nào**.

→ **M1 = draft test nhỏ trước khi wire:** 1 bài nhạc + 1 đoạn voice giả + vài keyframe,
anh mở CapCut nhìn đường volume trên clip nhạc (thấy hình bậc thang đúng chỗ = đạt).
Mỗi draft test đổi đúng 1 biến (bisect).

## 7. Cổng theo P4

| Milestone | Nội dung | Cổng |
|---|---|---|
| **M1** | Draft test keyframe (kiểm 2 behavior mục 6) | 👁 anh mở CapCut xem |
| **M2** | Hàm lập lịch thuần + wire vào assemble + pytest (merge nghỉ ngắn, ramp clamp mép, ngưỡng thở, JSON có `KFTypeVolume`) | pytest |
| **M3** | Chạy lại project thật → **V6** | 👂 tai anh — chốt/chỉnh 4 tham số |
