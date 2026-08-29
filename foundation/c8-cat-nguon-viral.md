# C8 — LUẬT CẮT NGUỒN VIRAL (bản quyền — an toàn kênh khi lấy footage video đối thủ)

> **Vị trí:** luật AN TOÀN PHÁP LÝ cấp nguồn — đứng TRƯỚC mọi foundation chất lượng: footage
> vi phạm bản quyền thì đẹp mấy cũng vô nghĩa (kênh ăn gậy). Chi phối 2 điểm của pipeline:
> **ống NẠP kho** (`library-ingest`, PB4) và **phễu CHỌN khi dựng** ([[c5-loc-xep-hang]]).
> Chỉ áp cho footage nguồn **viral/đối thủ** (video kênh khác trên YouTube) — footage từ
> project của CÔNG TY và stock có license (Pexels) KHÔNG bị luật này đụng.
> Nguyên văn lời user: `GHI_CHEP_GOC.md` §BỔ SUNG 2026-07-08. Foundation thứ 19 (danh mục
> 18 file khóa 2026-07-02 +1 theo lệnh user). **Trạng thái phần 3: DỰ KIẾN 🔸 — CHƯA CODE;
> mô tả vận hành riêng phải được duyệt trước mẻ nạp viral đầu tiên.**

---

## 1. Là gì

Khi cắt footage từ video viral của kênh khác để nạp kho + dựng video mình, công ty có
**5 luật cứng** (quy tắc đã dùng cho editor người, nay máy phải giữ y nguyên):

| # | Luật | Bản chất |
|---|---|---|
| 1 | **Mỗi miếng cắt từ nguồn ≤10s — chuẩn an toàn 6s** | Miếng càng ngắn càng khó khớp Content ID; 6s là chuẩn công ty, 10s là trần tuyệt đối |
| 2 | **Tách âm thanh, chỉ lấy hình** | Audio là vùng match bản quyền mạnh nhất — không bao giờ mang theo |
| 3 | **Trong 1 video của mình: KHÔNG dùng 2 cảnh LIỀN KỀ của cùng 1 video nguồn — DÙ ĐẶT XA NHAU trên timeline mình** (user chốt 2026-07-08) | 2 cảnh kề nhau của nguồn cùng lộ diện = lộ vùng trích liền mạch → dễ nhận diện + khó cãi fair-use |
| 4 | **Zoom to để mất logo/chữ** | Watermark/logo góc + chữ lower-third của kênh gốc là bằng chứng nhận diện tức thì |
| 5 | **≤8% thời lượng của 1 video nguồn trong 1 video mình; ưu tiên RẢI nhiều nguồn, mỗi nguồn một ít** | Tổng lượng trích từ 1 nguồn càng thấp càng an toàn; rải nguồn làm loãng dấu vết từng kênh |

Tinh thần chung: **ít — ngắn — rời rạc — biến dạng — không tiếng.** Một miếng 6s zoom
112% không audio, đứng cạnh footage nguồn khác, gần như không thể bị Content ID quét trúng
và rất khó bị kênh gốc nhận ra bằng mắt.

## 2. Yếu tố ảnh hưởng

| Yếu tố | Ảnh hưởng thế nào |
|---|---|
| **Nguồn gốc asset (source class)** | Luật CHỈ áp cho `viral` (video kênh khác). Kho hiện tại 665 asset học từ project công ty = class `own`, miễn toàn bộ. Db phải PHÂN LOẠI được — thiếu nhãn thì mặc định coi là viral (an toàn nghiêng về chặt). |
| **Thời lượng video nguồn** | Mẫu số của luật 5 (8%). Video nguồn 20 phút → trần 96s/1 video mình; nguồn 5 phút → chỉ 24s. Phải đo + lưu lúc nạp. |
| **Vị trí cảnh trong nguồn (scene_index)** | Nền của luật 3 — db PB4 đã lưu `scene_index` + `source_video` sẵn (may). |
| **Editor tách cảnh thế nào** | Editor tách cảnh dài 15-20s thì ống nạp phải TỰ bóp về ≤10s (lấy khúc giữa) — không tin mép tách tay tuân trần. |
| **Content ID vs mắt người** | Content ID quét match hình/tiếng theo đoạn; kênh gốc report tay thì nhìn LOGO + trình tự. Luật 1-2-5 chống máy quét; luật 3-4 chống mắt người. Phải giữ CẢ HAI. |

## 3. Cách làm THỰC TẾ ở project này — 🔸 DỰ KIẾN (CHƯA CODE — chờ mô tả vận hành duyệt)

### Nguyên tắc thực thi: luật NẠP nướng chết vào clip; luật CHỌN gác lúc dựng

**Nhóm A — thực thi 1 lần lúc NẠP (`library-ingest`, sửa ống PB4):**
- **Luật 2 (tách tiếng): ✅ ĐÃ CÓ** — ffmpeg `-an` từ PB4, không làm gì thêm.
- **Luật 1 (≤10s/chuẩn 6s):** cảnh editor tách >10s → ống chỉ cắt **6s khúc GIỮA** cảnh
  (giữa thường là lõi hành động, tránh mép transition); cảnh ≤10s giữ nguyên mép editor.
  Thuận chiều luật GLM 1-frame (<10s = 1 frame) → mọi clip viral tag giá rẻ đồng loạt.
- **Sàn 2s (user chốt 2026-07-08):** CapCut tách cảnh đẻ ra cả cảnh ≤1s — cảnh **<2s bị BỎ
  ngay tại ống nạp, TRƯỚC khi gọi vision** (đỡ tiền tag; clip <2s cũng gần vô dụng với phễu:
  không đủ 1,2× beat, không đủ miếng shot thở ≥1,5s). Áp cho MỌI mẻ nạp về sau, không riêng viral.
- **Luật 4 (zoom mất logo/chữ):** nướng **crop-zoom ~112% tâm khung** vào clip chuẩn hóa
  ngay lúc nạp (mọi clip viral, không chỉ clip có logo — đồng nhất, downstream khỏi nghĩ).
  Mẻ thử: user soi mắt logo/chữ đã mất chưa, chỉnh % nếu cần. Chữ lower-third to giữa khung
  thì zoom không cứu — GLM tag sẵn trường chữ-trong-khung → cảnh đó **loại từ lúc nạp**.
- **Ghi siêu dữ liệu cho luật 3+5:** `source_class='viral'` + `source_duration` (ffprobe
  video nguồn) vào db; `scene_index`/`source_video`/`scene_start` PB4 đã có sẵn.

**Nhóm B — gác lúc CHỌN (phễu [[c5-loc-xep-hang]] / sourcer, 1 video đang dựng):**
- **Luật 3 (không 2 cảnh liền kề):** khi 1 asset viral được pick, mọi asset cùng
  `source_video` có `scene_index` ±1 bị CHẶN cho video này (mở rộng tự nhiên của P7
  `used_in_video` — cùng chỗ code, thêm chiều "hàng xóm theo nguồn").
- **Luật 5 phần cứng (trần 8%):** cộng dồn giây đã pick theo `source_video`; ứng viên nào
  đẩy tổng vượt `8% × source_duration` → CHẶN cho video này.
- **Luật 5 phần mềm (ưu tiên rải):** ĐIỂM TRỪ tăng dần theo % đã dùng của nguồn (dùng càng
  nhiều nguồn đó điểm càng xấu) — đúng khuôn [[filter-overload-guard]]: phần rải là RANK,
  chỉ 2 cái chặn cứng ở trên là gate pháp lý.
- **Fail-safe mặc định:** chừng nào gate luật 3+5 CHƯA code xong, asset `source_class='viral'`
  **không được vào pool phễu** — thà kho nằm chờ còn hơn dựng video phạm luật. (Nạp kho
  và dùng kho tách rời được nhờ cờ class.)

### 3b. PHÂN RÃ NĂNG LỰC

> Loại: **(a)** đã có sẵn · **(b)** cần code mới ỐNG · **(c)** NÃO quyết lúc chạy · **(d)** cần dữ liệu DNA

| Luật ngôn-ngữ-công-ty | Hệ thống chạy thế nào | Loại | Trạng thái |
|---|---|---|---|
| Tách âm thanh chỉ lấy hình | `ingest.py` ffmpeg `-an` (C4 chuẩn hóa) | (a) | ✅ ĐÃ CÓ từ PB4 |
| Miếng cắt ≤10s, chuẩn 6s | ống nạp bóp cảnh >10s về 6s khúc giữa | **(b)** | ❌ sửa `ingest.py` — TRƯỚC mẻ nạp viral |
| Sàn 2s: bỏ cảnh vụn trước vision | ống nạp skip cảnh <2s (đếm + báo số bị bỏ, không bỏ âm thầm) | **(b)** | ❌ sửa `ingest.py` — cùng gói, áp mọi mẻ nạp |
| Zoom ~112% mất logo/chữ | nướng crop-zoom vào bước chuẩn hóa ffmpeg lúc nạp + GLM cờ chữ-trong-khung → loại | **(b)** | ❌ sửa `ingest.py`/`transcode` — TRƯỚC mẻ nạp viral |
| Nhãn nguồn + thời lượng nguồn | db thêm `source_class` + `source_duration` (migrate: 665 asset cũ = `own`) | **(b)** | ❌ sửa `db.py` — TRƯỚC mẻ nạp viral |
| Không 2 cảnh liền kề 1 nguồn/1 video | gate cạnh P7 `used_in_video`, đọc `source_video`+`scene_index` | **(b)** | ❌ sửa sourcer — trước lần DỰNG đầu dùng kho viral |
| Trần 8%/nguồn/video + điểm rải nguồn | gate cộng dồn giây theo nguồn + điểm trừ rank theo % đã dùng | **(b)** | ❌ sửa sourcer/ranker — cùng đợt gate liền kề |
| Fail-safe: viral chưa có gate → không vào pool | lọc `source_class` ở `find_local_candidates` | **(b)** | ❌ 1 dòng — code CÙNG đợt nhãn db |
| Lấy càng ít từ 1 nguồn càng tốt (chọn nguồn nào để nạp) | NÃO/user lúc gom video nguồn — máy chỉ đo và báo % đã dùng trong report | (c) | 🔸 quy trình gom của user |
| Ngưỡng an toàn theo niche (6s có đủ? 8% có lỏng?) | theo dõi kênh thật có bị claim không → chỉnh hằng số | (d) | ❌ kinh nghiệm vận hành, chưa có số |

**→ Backlog code rút ra: 1 gói "ingest viral an toàn bản quyền"** (luật 1+4+nhãn db+fail-safe
— PHẢI xong trước mẻ nạp viral đầu tiên) **+ 1 gói "gate chọn theo nguồn"** (luật 3+5 —
phải xong trước lần dựng đầu tiên dùng asset viral; trong lúc chờ, fail-safe chặn sẵn).
Mỗi gói 1 mô tả vận hành riêng, duyệt rồi code (P4/P5).

## 4. Cạm bẫy / ranh giới

- **Áp luật lên cả kho `own`** — thảm họa ngược: footage của chính công ty bị bóp 6s + cấm
  liền kề thì kho 665 asset hiện tại thành phế. Luật CHỈ theo `source_class='viral'`.
- **"2 frame liên tiếp" — ĐÃ CHỐT (user 2026-07-08):** = 2 CẢNH có `scene_index` kề nhau
  (i và i±1) của cùng video nguồn KHÔNG được cùng xuất hiện trong 1 video mình, **dù đặt xa
  nhau trên timeline**. Gate nằm ở PHỄU lúc pick (chặn hàng xóm theo nguồn), không phải assembler.
- **Zoom sau, hứa "editor sẽ chỉnh"** — zoom phải NƯỚNG lúc nạp; để đến 20% cuối là có ngày
  quên và footage mang logo kênh gốc lên sóng.
- **Trần 10s nhưng phễu ưa clip dài** — phễu chấm bonus clip ≥1.2× beat ([[c5-loc-xep-hang]],
  PB7): clip viral 6-10s tự nhiên chỉ phục vụ beat ≤8s + shot con (F6) + shot thở (miếng
  4,5-10,5s dùng tốt). KHÔNG nới trần để "cứu" beat dài — beat dài đã có kho own + Pexels.
- **Cộng dồn 8% quên shot thở/multi-shot** — mọi ĐƯỜNG dùng asset (beat chính, shot con,
  shot thở, breathing tail) đều phải đi qua cùng một sổ cộng dồn theo nguồn; sót 1 đường là
  thủng trần âm thầm (bài học vùng-ảnh-hưởng P5: bug `int()` luôn có anh em).
- **Coi đây là veto chất lượng thứ 3** — không phải: đây là lớp AN TOÀN cùng loại geo-gate
  PA2, đứng NGOÀI hệ điểm phễu ([[filter-overload-guard]] nguyên vẹn: phần "rải nguồn" là
  điểm rank, chỉ trần 8% + liền kề là gate cứng có lý do pháp lý).

## 5. Học gì từ DNA niche (Phase B)

| Tín hiệu | Dùng để |
|---|---|
| Kênh nào trong niche từng đánh gậy / claim | danh sách nguồn né hẳn (không nạp) |
| % dùng thật mỗi nguồn qua các video đã dựng (report cộng dồn) | biết nguồn nào sắp "nóng" → ưu tiên gom nguồn mới |
| Mật độ footage viral / video mình theo niche | cân tỉ lệ viral vs own vs stock cho tự nhiên |
