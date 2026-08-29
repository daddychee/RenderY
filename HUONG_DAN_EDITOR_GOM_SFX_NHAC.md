# HƯỚNG DẪN EDITOR — GOM NHẠC NỀN + SFX NẠP KHO (đợt 2026-07)

> **Đưa file này cho editor.** Editor chỉ cần LỌC FILE + ĐẶT TÊN đúng quy ước rồi bàn giao
> folder — việc nhập vào tool do máy gốc làm sau (KHÔNG phải việc của editor).
>
> Vì sao tên file quan trọng: tool ĐỌC TÊN FILE để biết mood của nhạc (tag tự động bằng
> máy đã thử và thất bại). Tên đặt sai/chung chung = tool chọn nhạc sai cảm xúc, SFX sai
> loài (bài học thật 2026-07-16: footage LẠC ĐÀ bị ghép tiếng CHIM vì file chỉ ghi chung
> chung là "động vật").
>
> Tài liệu anh em: `HUONG_DAN_NAP_NICHE_MOI.md` (checklist cho máy khi mở niche mới) —
> file này là danh sách ĐẶT HÀNG + quy ước đặt tên cho NGƯỜI gom file.

---

## PHẦN 1 — NHẠC NỀN

### 1.1 Quy ước đặt tên (BẮT BUỘC — tool parse đúng khuôn này)

```
Tên ca sĩ - Tên bài __mood1 __mood2.mp3
```

- Ngăn cách mood bằng **HAI dấu gạch dưới `__`** (không phải 1 gạch, không phải gạch ngang).
- Mỗi bài gắn **1–3 mood**, chọn ĐÚNG CHỮ trong bảng 1.2 — **tự chế từ khác
  ("chill", "emotional", "vibe"...) tool sẽ BỎ QUA im lặng**, coi như bài không có mood.
- Ví dụ ĐÚNG:
  - `Ian Post - Desert Caravan __playful __happy.mp3`
  - `AGST - Night Market __nostalgic __peaceful __hopeful.mp3`
- Ví dụ SAI:
  - `nhac vui 1.mp3` (không mood — tool mù)
  - `Ian Post - Desert Caravan _playful.mp3` (1 gạch dưới — không parse được)
  - `Ian Post - Desert Caravan __vui.mp3` (mood tiếng Việt / ngoài bảng — bị bỏ)

### 1.2 Bảng 19 mood hợp lệ (CHỈ dùng đúng các chữ này)

| Mood | Nghĩa | Thường dùng cho |
|---|---|---|
| `epic` | hùng tráng, hoành tráng | mở/kết chương lớn, cảnh choáng ngợp |
| `uplifting` | phấn chấn | đoạn tích cực, thành tựu |
| `inspiring` | truyền cảm hứng | câu chuyện vươn lên |
| `hopeful` | hy vọng, ấm áp | kết mở, đoạn ấm |
| `happy` | vui tươi | đời sống, đồ ăn, lễ hội |
| `playful` | tinh nghịch, dí dỏm | facts vui, đoạn hài |
| `peaceful` | bình yên | thiên nhiên, sinh hoạt chậm |
| `dreamy` | mơ màng | cảnh đẹp lơ lửng, dưới nước |
| `romantic` | lãng mạn | cảnh đôi, hoàng hôn |
| `nostalgic` | hoài niệm | lịch sử, truyền thống, văn hóa |
| `mysterious` | bí ẩn | mở màn câu hỏi, biển sâu, vũ trụ |
| `suspenseful` | hồi hộp chờ đợi | dẫn tới cao trào |
| `tense` | căng thẳng | cao trào, nguy hiểm |
| `dark` | u tối | đoạn nặng, đe dọa |
| `sad` | buồn | mất mát, bi kịch |
| `angry` | dữ dội, giận dữ | xung đột, thảm họa |
| `scary` | rùng rợn | săn mồi, kinh dị nhẹ |
| `serious` | nghiêm túc, tài liệu | số liệu, giải thích |
| `determined` | quyết tâm, dồn bước | hành trình, xây dựng |

Một bài có thể vừa `playful` vừa `happy` — cứ gắn cả hai nếu tai nghe thấy cả hai.

### 1.3 Điều kiện chọn bài (lọc TRƯỚC khi cho vào folder)

1. **KHÔNG LỜI (instrumental) — quan trọng nhất.** Tool KHÔNG tự phát hiện giọng hát;
   bài có lời lọt vào sẽ bị dùng như nhạc nền và đè lên voice. Bài có ngân nga
   "ooh/aah" thoáng qua thì được, có hát từ ngữ thì loại.
2. **Dài ≥ 2 phút 30** (chương video dài 2–4 phút). Bài ngắn hơn dễ bị loại khi chọn.
3. **KHÔNG lấy bản "Short Version"** của Artlist (tool tự bỏ các file có chữ này).
4. Ưu tiên bài có CẤU TRÚC (intro → dồn dần → đoạn cao trào) hơn bài phẳng đều một
   màu từ đầu đến cuối — tool biết canh vào đúng đoạn cao trào.
5. **Tốc độ/BPM: KHÔNG cần ghi vào tên** — tool tự đo. Việc của editor là gom ĐA DẠNG
   NHỊP: trong mỗi mood cố gắng ~1/3 số bài là nhịp nhanh, dồn dập rõ (kho hiện đang
   thiếu bài nhanh: chỉ 27/241 bài fast). Bài nào tai nghe thấy nhịp RÕ RỆT nhanh hoặc
   chậm khác thường → ghi 1 dòng vào `GHI_CHU.txt` (xem Phần 3), máy gốc sẽ sửa tay.
6. Nguồn: Artlist (đã có license công ty). Có link bài thì dán vào `GHI_CHU.txt` (không bắt buộc).

### 1.4 ĐẶT HÀNG — mood đang thiếu (đã kiểm kho 241 bài ngày 2026-07-16)

Ưu tiên theo thứ tự bảng. Một bài gắn 2–3 mood được tính cho cả 2–3 dòng, nên thực tế
**chỉ cần gom ~50–60 file là phủ đủ**.

| Ưu tiên | Mood | Kho đang có | Cần thêm | Ghi chú |
|---|---|---|---|---|
| 🔴 1 | `angry` | 0 | +8 | trống hoàn toàn |
| 🔴 1 | `playful` | 11 | +14 | trụ cột niche đời sống (life-in) |
| 🔴 1 | `happy` | 7 | +13 | trụ cột life-in |
| 🔴 1 | `uplifting` | 13 | +12 | trụ cột life-in |
| 🔴 1 | `scary` | 5 | +10 | deepsea săn mồi đang phải mượn dark |
| 🟡 2 | `inspiring` | 18 | +7 | |
| 🟡 2 | `romantic` | 3 | +7 | |
| 🟡 2 | `sad` | 8 | +7 | |
| 🟡 2 | `serious` | 8 | +7 | đoạn số liệu/tài liệu mọi niche |
| 🟢 3 | `nostalgic` | 19 | +6 | văn hóa/truyền thống life-in |
| 🟢 3 | `hopeful` | 22 | +3 | |
| 🟢 3 | `suspenseful` | 17 | +3 | |

Các mood sau kho ĐÃ DÀY, **không cần gom thêm**: mysterious (46), dreamy (37),
tense (34), peaceful (30), epic (26), dark (26), determined (24).

---

## PHẦN 2 — SFX / TIẾNG HIỆN TRƯỜNG (theo niche)

### 2.1 Quy ước đặt tên (khác nhạc: KHÔNG cần `__`, chỉ cần MÔ TẢ THẬT CỤ THỂ)

Tên tiếng Anh, nói rõ **con gì / tiếng gì + đang làm gì + bối cảnh**:

- ĐÚNG: `Camel grunting close up.mp3` · `Goat herd at livestock market.mp3` ·
  `Coffee pouring into cup.mp3` · `Mosque interior reverb ambience.mp3`
- SAI: `Animal.mp3` (loài gì?) · `Desert vibes.mp3` (gió? lạc đà? nhạc?) ·
  `SFX 01.mp3`

**3 luật vàng:**
1. **MỖI FILE MỘT LOẠI TIẾNG.** File trộn nhiều tiếng (vd "river water wild birds" —
   vừa nước vừa chim) không phân loại được, chính là nguồn gốc vụ lạc-đà-kêu-tiếng-chim.
   Nghe thấy 2 tiếng chính trong 1 file → loại, tìm file khác.
2. **KHÔNG dính nhạc, KHÔNG lời bình** trong file SFX.
3. **Động vật phải ghi RÕ LOÀI** trong tên (camel/goat/horse/bird...), tuyệt đối không
   ghi chung "animal".

**Độ dài:** tiếng chủ thể/cảnh 10–30 giây là đẹp (tool chỉ dùng tối đa ~10s mỗi lần,
file dài hơn không sao). Riêng tiếng NỀN đánh dấu (bed/drone) cần 2–5 phút, loop mượt.
Định dạng mp3/wav/aac đều được — tool tự chuẩn hóa.

### 2.2 ĐẶT HÀNG NICHE `life-in` (ưu tiên cao nhất — đang chạy video)

| Nhóm tiếng | Kho có | Cần thêm | Gợi ý cụ thể |
|---|---|---|---|
| 🔴 Lạc đà | 0 | 4–6 | grunt/kêu, bước chân trên cát, gần–xa |
| 🔴 Dê / cừu | 0 | 3–4 | kêu lẻ + cả đàn, chợ gia súc |
| 🔴 Ngựa / lừa | 0 | 3–4 | hí, bước chân, thồ hàng |
| 🔴 Bò / chợ gia súc | 0 | 3 | tiếng chợ buôn gia súc tổng thể |
| 🔴 Đồ ăn / nấu nướng | 1 | +5 | xèo xèo chảo, nướng than, rót trà/cà phê, chợ đồ ăn |
| 🟡 Trong nhà (interior) | 2 | +3 | quán cà phê, sảnh vọng âm (đền/nhà thờ), phòng yên |
| 🟡 Nền trung tính (default) | 2 | +3 | ngoài trời chung chung không đặc điểm |
| 🟡 Suối / kênh nước | 3 | +2 | nước chảy nhỏ, kênh tưới |
| 🟡 Địa danh đô thị | 3 | +2 | quảng trường vắng, khuôn viên di tích |
| 🟡 Núi / sa mạc (không gió) | 3 | +2 | không gian rộng tĩnh |
| 🟢 Người sinh hoạt | 7 | +3 | cầu nguyện xa xa, sân chơi, quán đông |
| 🟢 Hook: impact / whoosh / click | 4/4/3 | +2 mỗi loại | tiếng nhấn tại cut đầu video |

Chim (6 file) và gió (12 file) life-in ĐÃ ĐỦ — không gom thêm.

### 2.3 ĐẶT HÀNG NICHE `deepsea`

| Nhóm tiếng | Kho có | Cần thêm | Gợi ý cụ thể |
|---|---|---|---|
| 🔴 Cá voi xanh (blue whale) | 3 | +2 | tiếng gọi tần số thấp |
| 🔴 Cá voi sát thủ (orca) | 3 | +2 | click/kêu bầy |
| 🟡 Chim biển | 2 | +2 | mòng biển ven bờ |
| 🟡 Drone nền dưới nước | 3 | +2 | ù trầm loop được, 2–5 phút |
| 🟢 Đất liền (phố/người/nước ngọt) | 1/1/1 | +2 mỗi loại | hiếm dùng, ưu tiên thấp |

### 2.4 ĐẶT HÀNG NICHE `space`

| Nhóm tiếng | Kho có | Cần thêm | Gợi ý cụ thể |
|---|---|---|---|
| 🔴 Tín hiệu (signal) | 2 | +3 | beep radio, sonar ping, telemetry |
| 🟡 Người sinh hoạt | 1 | +2 | phòng điều khiển, đám đông xem phóng tàu |
| 🟢 Phố / nước | 2/3 | +1 mỗi loại | ưu tiên thấp |

**Tổng SFX cả 3 niche: ~60–70 file.** Gom được một phần cứ bàn giao trước phần đó,
không cần chờ đủ.

---

## PHẦN 3 — CÁCH BÀN GIAO

Tạo folder theo khuôn (trên ổ F chung, hoặc zip gửi về nếu máy không thấy F):

```
F:\NAP_KHO\<ten_editor>_<YYYYMMDD>\
├── nhac\                 ← file nhạc ĐÃ đặt tên  Artist - Title __mood
├── sfx\
│   ├── life-in\          ← SFX đặt tên mô tả cụ thể (Phần 2.1)
│   ├── deepsea\
│   └── space\
└── GHI_CHU.txt           ← (tùy chọn) mỗi dòng 1 ghi chú:
                             - tên file | nhịp nhanh/chậm khác thường
                             - tên file | link Artlist
```

Checklist tự soát trước khi bàn giao (5 phút):
- [ ] Nhạc: không bài nào CÓ LỜI, không bài nào < 2:30, không "Short Version"
- [ ] Nhạc: mọi file có ít nhất 1 `__mood` đúng chữ trong bảng 1.2
- [ ] SFX: không file nào tên chung chung ("animal", "nature", "sfx1")
- [ ] SFX: không file nào trộn 2 loại tiếng hoặc dính nhạc
- [ ] File nằm đúng folder niche

---

## PHẦN 4 — DÀNH CHO MÁY GỐC (Claude Code) KHI NHẬP — editor không cần đọc

> 📌 CẬP NHẬT 2026-07-17 (mẻ nạp life-in đợt 2): (a) nhạc **life-in vào POOL RIÊNG**
> `F:\AutoEdit\music\life-in\tracks\` — life-in CHỈ dùng pool này, các niche khác vẫn
> pool chung `F:\AutoEdit\music\tracks\` (luật `music_root_for`, memory
> `music-pool-theo-niche`); (b) user ĐÃ CHỐT **tách kind SFX theo loài** — hết staging.

1. **Nhạc:** copy `nhac\*` vào pool ĐÚNG NICHE (life-in → `F:\AutoEdit\music\life-in\tracks\`;
   niche khác → `F:\AutoEdit\music\tracks\` chung) → `music-import --lib <pool>`. Đọc
   `unknown_tags` trong kết quả → tag lạ báo lại editor sửa tên, KHÔNG tự đoán (typo
   hiển nhiên kiểu `peachful` thì sửa + báo). `GHI_CHU.txt` có dòng tempo → ghi
   `overrides.yaml` (bpm/tempo_class, overrides luôn thắng). Xong chạy `library_status`
   xác nhận bảng 1.4 đã đầy.
2. **SFX:** nghe/soi tên từng file → tự viết `ambient_manifest.yaml` ({file, kind, title})
   vào folder niche `F:\AutoEdit\ambient\<niche>\` → `import_from_manifest`. Giữ nguyên
   tên gốc trong `source_file` (truy vết loài — bài học animal_wildlife). File loài
   mới (camel/goat/eagle...): **kind riêng theo loài** — thêm kind + keywords vào
   `subject_rules.yaml` của niche (user chốt 2026-07-17; khuôn = subject_rules.yaml
   life-in). File trộn 2 tiếng chính → LOẠI + ghi danh sách báo lại (luật vàng 2.1).
3. Nhớ luật 2 máy: tránh 2 mẻ NẠP kho cùng niche cùng lúc (HUONG_DAN A4.3).
