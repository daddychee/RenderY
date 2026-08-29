# E1 — SOUND DESIGN & NHẠC (bị coi nhẹ nhất, quan trọng nhất)

> **Vị trí:** foundation TRÙM cả nhóm E — nhạc nền + ambient + SFX nhấn + ducking (lớp con).
> "Âm thanh làm 50% cảm xúc mà người xem không ý thức được" — và là 60% của mood
> ([[b1-mood-tone]]). Ăn khớp: hình thở sống nhờ ambient ([[d2-hinh-tho]]), chuyển chương
> cảm được nhờ đổi nhạc ([[d3-loai-cat-transition]]), SFX là vũ khí interrupt
> ([[b3-pattern-interrupt]]). Nguyên văn user: `GHI_CHEP_GOC.md §5 + §3 (ducking)`.
> **Trạng thái phần 3: DỰ KIẾN 🔸. Điểm treo: mức dB ducking (user dặn note).**

---

## 1. Là gì

Ba lớp âm thanh xếp chồng, voice luôn trên cùng (nguyên văn user §5):

> Xây theo lớp — voice ở trên cùng (rõ nhất), nhạc nền dưới (ducking: tự hạ khi có voice),
> ambient để lấp "khoảng trống chân không". Dùng riser trước một cú reveal, impact/boom
> ngay điểm cắt mạnh, whoosh cho chuyển cảnh nhanh. **Ambient là thứ khiến hình thở không
> bị "chết".**

- **Nhạc nền** — chọn theo mood/energy chương, ĐỔI BÀI khi đổi chương, cấu trúc nhạc
  (build/drop) khớp cấu trúc nội dung.
- **Ambient/foley** — tiếng môi trường theo footage (sóng, gió, phố xá); user: *"khán giả
  thích nghe âm thanh dễ chịu... niche deepsea: khán giả thích nghe tiếng âm thanh dưới
  biển sâu"* — ambient theo niche là chuyện DNA.
- **SFX nhấn** — whoosh/riser/impact/pop đúng ĐIỂM (kèm overlay, chart, cú reveal).
- **Ducking (lớp con)** — nguyên văn §3: *"khi voice bắt đầu nói thì nhạc nền bé lại.
  khi voice không nói (đoạn hình thở) thì nhạc nền to lên. mức hạ db bao nhiêu chúng ta
  sẽ học dna niche hoặc quyết định sau."*
- **Im lặng** — cũng là công cụ: ngắt nhạc đột ngột trước câu quan trọng = cú nhấn mạnh
  nhất; nhưng không bao giờ im lặng TUYỆT ĐỐI (*"tai người nghe khoảng lặng tuyệt đối
  như lỗi — luôn có một lớp ambient/room tone rất nhỏ"*).

## 2. Yếu tố ảnh hưởng

| Yếu tố | Ảnh hưởng thế nào |
|---|---|
| **Mood/energy chương** | Quyết bài nhạc + điểm vào bài (drop cho energy cao, build cho vừa). Nhạc phục vụ tone, "không phải bài mình thích". |
| **Voice đang nói hay nghỉ** | Trục của ducking: có voice → nhạc nép xuống; hình thở → nhạc/ambient nở ra chiếm chỗ. |
| **Footage đang chiếu** | Ambient phải KHỚP HÌNH: cảnh biển tiếng sóng, cảnh phố tiếng phố — ambient lệch hình còn tệ hơn không có. |
| **Điểm nhấn nội dung** | Riser TRƯỚC reveal, impact TẠI điểm cắt mạnh/overlay keyword — SFX bám sự kiện, không rắc đều. |
| **Niche (DNA)** | Loại ambient khán giả niche thích + mức dB ducking + gu nhạc — cả ba là số DNA. |

## 3. Cách làm THỰC TẾ ở project này — 🔸 DỰ KIẾN

### Hiện trạng code — lớp NHẠC + SFX nhấn đã chạy khá đủ, ambient + ducking CHƯA có

- **Nhạc:** `music/select.py` chọn bài theo chương — lọc cứng (instrumental, đủ dài, chưa
  dùng) → chấm 0.6 mood + 0.25 energy + 0.15 tempo; vào bài tại drop/build theo energy;
  đổi bài theo chương, crossfade 3s, fade in/out (`assembler._add_music_by_chapter`).
- **SFX nhấn:** thư viện kinds (cash/impact/pop/whoosh/riser/ding/keyboard) tự đặt theo
  overlay kind + chart (`overlay/style.py` map kind→sfx, `_add_overlays`, `_add_chart_sfx`).
- **Im lặng chiến lược:** chính là hình thở (voice ngắt) — ĐÃ có; nhưng hiện nhạc giữ
  nguyên volume phẳng qua khoảng thở (chưa nở ra).
- **CHƯA có:** ducking (volume nhạc cố định `MUSIC_VOLUME=0.2` cả video — comment sẵn
  "ducking keyframe là Phase 1"); ambient layer (chưa có track, chưa có thư viện).

### Hướng dự kiến 🔸

1. **Ducking v1 (đáng làm sớm nhất — nghe thấy ngay):** không cần bám waveform từng chữ —
   dùng cấu trúc ĐÃ BIẾT của timeline: trong `segments` voice → nhạc mức thấp; trong
   khoảng thở/lead-silence → nhạc nâng lên, có ramp ngắn ở mép. Keyframe volume qua
   pycapcut. **Mức dB = điểm treo** — khởi điểm 🔸 lấy tham chiếu -12…-18dB khi có voice,
   chốt bằng tai user + DNA sau. Chạm assembler → qua CỔNG DUYỆT VẬN HÀNH trước khi code.
2. **Ambient v1 cho HÌNH THỞ trước tiên** (chỗ ambient ăn tiền nhất — cứu "chết hình"):
   thư viện ambient gắn tag loại-cảnh (biển/rừng/phố/vũ trụ/dưới nước) → khoảng thở chọn
   ambient khớp tag footage đang chiếu. Phụ thuộc tag footage (Phase B) + thư viện ambient
   (user gom, như MusicLibrary). Toàn video rải room-tone rất nhỏ: để sau.
3. **SFX giữ nguyên kỷ luật bám-sự-kiện** — không rắc thêm.

### 3b. PHÂN RÃ NĂNG LỰC

> Loại: **(a)** đã có sẵn · **(b)** cần code mới ỐNG · **(c)** NÃO quyết lúc chạy · **(d)** cần dữ liệu DNA (Phase B)

| Luật ngôn-ngữ-editor | Hệ thống chạy thế nào | Loại | Trạng thái |
|---|---|---|---|
| Nhạc theo mood/energy chương, đổi theo chương, vào tại drop/build | `music/select.py` + `_add_music_by_chapter` (crossfade 3s) | (a) | ✅ đã có |
| SFX nhấn bám sự kiện (overlay/chart) | `overlay/style.py` + `_add_overlays`/`_add_chart_sfx` + thư viện `sfx/` | (a) | ✅ đã có |
| Im lặng chiến lược sau ý đắt | hình thở (d2) | (a) | ✅ đã có |
| **Ducking: voice → nhạc nép; thở → nhạc nở** | keyframe volume theo segments/breathing đã biết trên timeline; ramp mép | **(b)** | ❌ MỞ MỤC MỚI — ứng viên code sớm nhất của E; cần mô tả vận hành duyệt trước |
| Mức dB ducking | khởi điểm 🔸 -12…-18dB; chốt bằng tai user + DNA | (d)+🔸 | ⏸ điểm treo (user dặn note) |
| **Ambient cho hình thở khớp footage** | thư viện ambient tag loại-cảnh + track mới + chọn theo tag footage | **(b)+(d)** | ❌ mở mục — SAU Phase B (cần tag footage + kho ambient) |
| Ambient theo gu niche (deepsea nghe tiếng biển sâu…) | spec tag GLM thêm "loại cảnh cho ambient"? → gom vào spec schema tag Phase B | (d) | ❌ Phase B |
| Nhạc không át voice / chuẩn loudness | transcode/volume hiện cố định; đo LUFS để sau | (b treo) | ⏸ chưa mở — chờ nghe thật có vấn đề |

**→ Backlog code rút ra: 2 mục mới** — (1) **ducking keyframe** (làm trước, có cổng duyệt
vận hành riêng); (2) **ambient-cho-hình-thở** (sau Phase B). Mọi thứ khác đã có hoặc treo.

## 4. Cạm bẫy / ranh giới

- **Im lặng tuyệt đối = "lỗi"** trong tai khán giả — khi làm ducking/thở, kiểm không có
  khoảng nào cả nhạc lẫn ambient đều = 0.
- **Nhạc át voice** — lỗi phổ biến nhất; ducking sinh ra để trị nó, nhưng mức nâng lúc
  thở cũng không được giật cục (ramp ở mép).
- **Ambient lệch hình** (cảnh sa mạc + tiếng sóng) — ambient chọn theo TAG footage thật
  đang chiếu, không theo mood chung chung.
- **Rắc SFX đều như gia vị** — SFX không bám sự kiện là tiếng ồn; kỷ luật hiện tại
  (SFX chỉ đi kèm overlay/chart) là ĐÚNG, đừng nới.
- **Đổi nhạc giữa chương** — nhạc đổi TẠI ranh giới chương (đã là luật code); đổi giữa
  chừng phá mood.
- **Chọn nhạc theo gu cá nhân** thay vì tone video — "nhạc phải phục vụ tone".

## 5. Học gì từ DNA niche (Phase B)

| Tín hiệu | Dùng để |
|---|---|
| Mức chênh nhạc lúc voice/lúc thở trong video viral niche | chốt số dB ducking (điểm treo) |
| Loại ambient theo loại cảnh + theo niche (travel: nước chảy; deepsea: âm biển sâu) | xây thư viện ambient + luật chọn |
| Gu nhạc niche (BPM, mood phổ biến, có drop không) | tinh chấm điểm `music/select.py` |
| Mật độ SFX video viral | kiểm kỷ luật SFX hiện tại đã đúng gu niche chưa |
