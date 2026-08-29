# MÔ TẢ VẬN HÀNH — NẠP VIDEO YOUTUBE THAM KHẢO + ĐIỂM NHÔ (ytref)

> Trạng thái: **DUYỆT TRỌN 2026-07-10** — 3 điểm treo §7 chốt (câu 1+2 user đồng ý;
> câu 3 ủy quyền → Claude chốt 0.5) + **GỘP gói TAG BỐI CẢNH §3i** (user: "chất lượng
> đầu ra tốt nhất, chấp nhận tag lại"). Viết 2026-07-10 sau khi user chốt quy trình:
> editor tải video tham khảo → CapCut **tách cảnh tự động** (không tuyển chọn tay)
> → máy nạp như viral + gắn cờ ĐIỂM NHÔ (Most Replayed) để phễu ưu tiên.
> Nguồn tri thức: tool `TOOL CẮT SIÊU DỮ LIỆU\ME OutlierY WIN` (user code trước) —
> bê module `peaks.py`; BỎ mảnh transcript-matching (vision tag + phễu mạnh hơn,
> transcript = lời đọc ≠ nội dung hình — đúng lớp lỗi "chữ nói dối" b60).

---

## 1. Mục tiêu

Quy trình editor thật có bước: tìm 3–6 video YouTube liên quan chủ đề → cắt phân cảnh
phù hợp, **đặc biệt các đoạn ĐIỂM NHÔ** (Most Replayed — đồ thị nhô cao trên timeline
YouTube = khán giả xem lại nhiều). Máy hóa bước này:

- Footage tham khảo vào **kho local** (class `viral`, luật bản quyền c8 nguyên vẹn).
- Cảnh trùng đoạn điểm nhô mang **cờ ưu tiên** → phễu cộng điểm khi nghĩa khớp beat.
- Editor chỉ tốn ~2 phút/video (kéo vào CapCut → bấm tách cảnh). Không tuyển chọn.

## 2. Quy trình vận hành

```
1. Editor tải 3–6 video tham khảo → folder chủ đề (vd F:\SPACE\MOON VIDEO YOUTUBE THAM KHAO)
   — GIỮ NGUYÊN tên file tải (chứa YouTube ID, vd ..._Media_bdygcDw_NM8_001_1080p.mp4)
   — tool tải khác không nhúng ID → thêm urls.txt cạnh video (mỗi dòng: <tên file> = <url>)
2. Editor: CapCut draft NHÁP mới (đặt tên có nghĩa, vd "MOON THAM KHAO 0710")
   → kéo lần lượt từng video vào timeline → chức năng TÁCH CẢNH tự động → lưu. XONG.
   (các video nối tiếp nhau — CapCut tách cảnh tự xếp tuần tự, không trộn xen kẽ)
3. Máy:  autoedit library-ingest "<draft>" --niche space --source-class viral
   → tự nhận diện nguồn YouTube → lấy heatmap → gắn cờ điểm nhô → cắt theo c8 → tag vision
4. Dựng video như bình thường — phễu tự ưu tiên cảnh điểm nhô khi nghĩa khớp.
```

File video gốc giữ nguyên chỗ tới khi nạp xong (draft link path tuyệt đối — C2).

**LUẬT MỚI (user chốt 2026-07-10): MỌI nguồn viral từ nay cũng PHẢI kèm URL/YouTube ID**
(tên file chứa ID hoặc urls.txt) — để mẻ viral nào cũng hưởng trọn tag bối cảnh
(tiêu đề thật + chapters) **và cờ điểm nhô** y hệt ytref. Về pipeline, ytref và viral
là MỘT đường nạp duy nhất; nguồn thiếu ID → vẫn nạp được nhưng warning "thiếu bối
cảnh + điểm nhô" để editor bổ sung.

**✅ SMOKE ĐÃ KIỂM THẬT 2026-07-10 (trước khi code, yt-dlp 2026.07.04 qua uvx) — bộ MOON 3 video:**
- heatmap: **3/3 video có** (100 điểm/video); đỉnh thật vd TY9dnrbQano 13:04 value 1.00
- chapters: **1/3 có** (TY9dnrbQano: Intro/The Moon/The Far Side/The Cube/Lava/Water —
  đúng ca mỗi-chương-một-chủ-đề); 2/3 không có → fail-open chỉ-tiêu-đề là bắt buộc
- tiêu đề thật sạch hơn hẳn stem tên file (file YTDown cụt "…on-the-Fa")
- duration file tải ↔ YouTube lệch <0,5s/21 phút (0,03%) — dưới xa ngưỡng 3% §3d

## 3. Delta trên ống nạp hiện có (`library/ingest.py` + phễu) — 7 điểm

### 3a. Trần cảnh dài mới: `VIRAL_DROP_S = 20.0` (user chốt 2026-07-10)
CapCut tách cảnh có bug đã biết: (a) vài cảnh <2s — **sàn `MIN_SCENE_S=2.0` CÓ SẴN** lo;
(b) cảnh >20s do dò trượt chuyển cảnh (đoạn có transition mềm) — **trong cảnh có mối
nối, không tin được → BỎ**, đếm `too_long` vào stats (không bỏ âm thầm — khuôn C8-NAP).
- Áp cho `source_class='viral'` (mẻ viral nào cũng CapCut tách cảnh cùng kiểu).
- Cảnh 10–20s: giữ luật cũ — bóp 6s khúc giữa.
- **NGOẠI LỆ (user CHỐT 2026-07-10):** cảnh >20s **CÓ ĐIỂM NHÔ** → không bỏ mà cắt
  **6s NEO THEO ĐỈNH** (điểm nhô là footage quý nhất của cả tính năng; 6s sát đỉnh ít
  rủi ro dính mối nối hơn nhiều so với 20s trọn).
- Hồi tố mẻ viral cũ (226 cảnh >10s đã bóp 6s giữa, một phần gốc >20s có thể chứa mối
  nối): **KHÔNG dọn** — đã qua cổng mắt trên video thật; C5 gate + editor soát gánh.
  Ghi còn-ngỏ, chỉ mở nếu mắt thấy clip lỗi mối nối.

### 3b. Nhận diện nguồn YouTube từ tên material
Regex rút ID 11 ký tự: khuôn YTDown `_Media_(?P<id>[A-Za-z0-9_-]{11})_\d+_` trước,
fallback token 11 ký tự hợp lệ đứng riêng trong tên; fallback cuối `urls.txt` cạnh file
nguồn. Không tìm ra ID → nạp như viral thường + 1 dòng warning "không heatmap".

### 3c. Module heatmap `library/ytpeaks.py` (bê từ tool ME `me/peaks.py`)
- `yt-dlp --dump-json` (1 call/video, subprocess y tool ME) → field `heatmap`
  `[{start_time,end_time,value}]` + `duration` + `title`.
- Dò đỉnh giữ NGUYÊN thuật toán đã chạy thật của tool: local maxima CÓ dốc lên
  (chân foot + đỉnh apex), non-max suppression ≥20s, phân loại primary ≥85% /
  secondary 55–84% / minor <55% (mặc định BỎ minor — y tool).
- **Dep mới: `yt-dlp`** (pure-python, pin version trong pyproject). Fail-open toàn tầng:
  lỗi mạng / video ít view chưa có Most Replayed / YouTube đổi format → `[]` + warning,
  mẻ nạp vẫn chạy trọn như viral thường.

### 3d. Đối chiếu duration (chống mốc trượt)
ffprobe duration file tải vs duration YouTube: **lệch >3%** (file bị tool download cắt
đầu/đuôi) → **KHÔNG gắn cờ điểm nhô** video đó (gắn sai còn hại hơn không gắn) + warning.

### 3e. Gắn cờ điểm nhô — 2 cột db mới

> **📌 ĐIỀU CHỈNH 2026-07-11 (cổng mắt M2 — user: "cắt điểm nhô không đúng đỉnh, đặc
> biệt lỗi với video có nhiều điểm nhô"):** cửa sổ gốc `[foot, apex+1s]` bê từ tool ME
> ôm cả DỐC LÊN (đo thật: dốc dài tới 45s+; video 17 đỉnh bị cờ 144/288 = 50% cảnh) —
> tool ME dùng cửa sổ đó để CẮT CLIP MỚI từ chân hướng lên đỉnh, còn ytref GẮN CỜ CẢNH
> CÓ SẴN nên ngữ nghĩa đúng là "cảnh chứa khoảnh khắc đỉnh". **Cửa sổ mới = BIN ĐỈNH
> heatmap nới ±1s** (`[apex_time − 1s, apex_end + 1s]`; heatmap 100 bin ~9-15s/bin,
> value đo trên cả bin). Kết quả đo lại: 144→67 · 4→3 · 8→9 cảnh; 13 clip đối chiếu
> đều nằm đúng đỉnh trên đồ thị. `foot_time` giữ trong `Peak` làm thông tin, không
> dùng gắn cờ nữa.

- Cửa sổ điểm nhô = ~~`[foot_time, apex_time + 1s]` (y tool ME)~~ → **bin đỉnh ±1s
  (điều chỉnh 2026-07-11, xem block trên)**.

> **📌 ĐIỀU CHỈNH 2 — 2026-07-11 (user duyệt "cắt đã đúng đỉnh" rồi chốt thêm):**
> điểm nhô = chuỗi **3 FOOTAGE TỪ ĐỈNH VỀ TRƯỚC** (vd đỉnh 60s → footage đắt ~4x–60s;
> 3 cảnh build-up liên quan trực tiếp nhau, lấy CẢ 3). Máy hóa: trio = cảnh CHỨA đỉnh
> (giữa bin) + 2 cảnh LIỀN TRƯỚC cùng nguồn (`PEAK_RUNUP_N=3`, hở >3s nguồn
> `PEAK_CHAIN_GAP_S` = đứt chuỗi, dừng); cảnh SAU đỉnh KHÔNG cờ. **Ledger c8 luật 3
> (cấm kề ±1) MIỄN cho cảnh mang cờ điểm nhô** — user: "vẫn lấy 3 footage nhưng đặt
> khác vị trí được"; trùng-chính-nó + trần 8% + rải nguồn ÁP NGUYÊN (đổi ở
> `sourcer/viral.py::blocks` + `local.py::_row_to_candidate` mang 2 cột peak — làm
> sớm thay vì chờ M3 vì ledger cần đọc). Điểm theo dõi video kiểm M3: nếu 2 cảnh
> cùng trio rơi vào 2 beat LIỀN KỀ trên timeline dựng (lộ nguồn) → cân nhắc luật
> giãn-beat, chưa siết trước.
- Cảnh nào **giao** cửa sổ → `peak_value` (value đỉnh, 0–1) + `peak_type`
  (primary/secondary). 1 đỉnh trải nhiều cảnh → nhiều cảnh cùng cờ (ledger c8 tự chặn
  lấy cặp cảnh kề trong cùng video mình).
- db migrate thêm 2 cột (khuôn PB2/C8-NAP), asset cũ NULL = không cờ. KHÔNG re-tag.

### 3f. Bóp 6s NEO ĐỈNH cho cảnh điểm nhô
Cảnh điểm nhô 10–20s: bóp 6s **quanh apex** (clamp trong biên cảnh) thay vì khúc giữa —
bóp khúc giữa có thể vứt đúng khoảnh khắc làm nó thành điểm nhô. Cảnh thường: y cũ.

> **📌 ĐIỀU CHỈNH 2026-07-11 (cùng đợt 3e):** mốc neo = **GIỮA BIN ĐỈNH**
> (`(apex_time + apex_end)/2`) thay vì `apex_time` trần — apex_time chỉ là mép TRÁI
> bin ~9-15s, khoảnh khắc xem-lại nằm đâu đó trong bin nên cắt 6s ôm giữa bin trúng
> hơn ôm mép.

### 3g. scene_index đánh theo NGUỒN (gia cố luật c8 số 3)
Hiện index theo thứ tự timeline TOÀN draft; luật 3 check `±1` **trong từng nguồn** →
nếu cảnh 2 nguồn trộn xen kẽ trên timeline, 2 cảnh kề thật trong nguồn có thể mang index
xa nhau = gate trượt. CapCut tách cảnh xếp tuần tự nên thực tế đang tương đương, nhưng
sửa cho đúng nghĩa: **index = thứ tự `source_start` TRONG TỪNG file nguồn**.
- Vùng ảnh hưởng phải rà khi code (P5): consumer `DraftScene.index` — db `scene_index`
  → ViralLedger (fix làm luật ĐÚNG hơn); comment code ghi "d1/c7 cần" → kiểm dna.py
  dùng list order hay `.index`; tên clip deterministic KHÔNG chứa index (an toàn dedup).
- Cảnh bị bỏ (sàn 2s / trần 20s) vẫn làm 2 cảnh hai bên thành kề index → ledger chặn
  RỘNG hơn thật một chút = bảo thủ đúng chiều pháp lý, chấp nhận.

### 3h. Phễu + report
- `PEAK_BONUS = 0.5` 🔸 vào `_diem_may` (`ranker/funnel.py`) khi candidate có
  `peak_value` — spread điểm máy 2.0 → 2.5, **VẪN < NGHIA_W 3.0** → bất biến c5 đóng
  băng "điểm máy không bao giờ lật ứng viên đúng-nghĩa" GIỮ NGUYÊN. Không cửa loại mới
  (filter-overload-guard). **CHỐT 0.5 (Claude, user ủy quyền 2026-07-10):** số lớn nhất
  giữ bất biến theo khuôn bậc 0.5 hiện có; 0.25 chìm dưới dao động ±0.5 của variety
  (tính năng vô hình); tín hiệu "khán giả xem lại" xứng ngang UNUSED_BONUS. PHẲNG cho
  primary + secondary, không chia bậc trước khi có bằng chứng — 🔸 chỉnh sau video kiểm.
- **P5 khi code M3:** bonus phải chảy qua CẢ 2 đường rank — per-beat (`rank_beat`) LẪN
  batch PA-1 (`rank_batch`/`rank_beat_prescored`) — quét cả 2 chỗ gọi `_diem_may`.
- `sourcer/local.py::_row_to_candidate` mang 2 cột mới vào candidate — **chống lặp
  bug PB7** (cột duration từng bị đánh rơi ở đúng chỗ này làm phễu mù).
- Report: dòng nạp "điểm nhô: X cảnh gắn cờ / Y đỉnh / Z video có heatmap" + bảng pick
  đánh dấu ⭐ pick là điểm nhô + đếm "pick điểm nhô: N" cạnh dòng viral c8.

### 3i. TAG CÓ BỐI CẢNH (user duyệt 2026-07-10 — "chất lượng đầu ra tốt nhất, chấp nhận tag lại")
Nền CÓ SẴN từ vá 2a/2b (C đợt 2, sau vụ b60 Pluto→"moon"): `_tag_instruction` đã có
luật không-đoán-tên-riêng + `source_title` (gợi ý chủ đề) + `folder_context` (ground
truth editor xếp folder) — KIEM-V3 chứng minh tác dụng (4 pick sai-nghĩa biến mất sau
tag lại 102 clip). Gói này nối nốt 3 khoảng trống:
1. **`source_title` = tiêu đề THẬT từ yt-dlp** (cùng call heatmap §3c, fallback stem
   như cũ) — hiện đang truyền stem tên file YTDown cụt giữa chừng + lẫn mã, prompt lại
   dặn "tên vô nghĩa thì bỏ qua" → gợi ý chủ đề gần như mất.
2. **`section_hint` MỚI**: map `scene_start` → **YouTube chapter** chứa nó (field
   `chapters` trong cùng dump-json) → 1–2 dòng prompt CÙNG BẬC tin cậy source_title
   ("gợi ý về ĐOẠN, không chắc từng cảnh"). Giải ca video nhiều thực thể theo chương
   (5 hành tinh / 5 quốc gia — mỗi chapter 1 thực thể). Fail-open: không chapters → bỏ.
3. **Flag `--topic` cho `library-ingest`** (mọi mẻ own/viral): editor khai 1 dòng chủ
   đề khi tên file nguồn là mã số ("SP1 - 003") — vào prompt cùng bậc source_title.
   Giải ca video-về-một-hòn-đảo: cảnh thiên nhiên generic trong video mang tên đảo
   (đúng hành vi editor thật — vision thuần không bao giờ biết địa danh từ pixel).

**RANH GIỚI GIỮ NGUYÊN (bài học 2 phía):** luật không-đoán 2b là PHANH (hình mâu thuẫn
bối cảnh → tag theo HÌNH); transcript câu-theo-câu KHÔNG làm nhãn cảnh (b-roll lệch lời
đọc = vết b60); `stock_tags` + C5 gate KHÔNG đổi (gate giữ mắt độc lập để bắt tag kho
nói dối — bài học concept-proxy V5→V6). Chiều đúng về hệ: tag generic = MẤT RECALL vĩnh
viễn (clip không vào pool, không tầng nào cứu); tag có bối cảnh bạo dạn hơn thì precision
đã có veto nghĩa + C5 gate gác cửa pick.

**Đo trong M2 (văn hóa PB6/PB12):** ~40 cảnh bộ MOON tag 2 CÁCH (có/không bối cảnh) →
bảng HTML so mù → user phán → chốt mặc định (~$0,08). **Backlog:** hồi tố re-tag kho cũ
1874 asset có bối cảnh (~$2) — chỉ mở nếu A/B chênh rõ.

**P5 vùng ảnh hưởng khi code:** caller `_tag_instruction` = 2 engine (GLM + Claude
fallback) · `TagJob` thêm field → `indexer.tag_jobs` + ingest + test_library ·
`section_hint` chỉ đường ytref có chapters, mọi đường khác rỗng = prompt y cũ.

## 4. Rà chồng chéo (P5)

| Tầng cùng quản "chọn footage" | Quan hệ với cờ điểm nhô | Kết luận |
|---|---|---|
| NÃO chấm nghĩa/mood (NGHIA_W/MOOD_W) | Bonus máy +0.5 < 1 điểm nghĩa — không lật nghĩa | Không ngược chiều |
| Veto nghĩa (2 cửa veto) | Veto là CỬA, bonus là ĐIỂM — veto vẫn giết được clip điểm nhô sai nghĩa | Đúng thiết kế |
| Điểm máy khác (variety/duration/unused) | Cộng dồn cùng khuôn, trần spread kiểm lại | Giữ bất biến |
| ViralLedger (kề ±1, trần 8%, rải mềm) | Class viral → gate nguyên; clip điểm nhô bị dùng nhiều → nguồn tụt sort rải. **📌 đc 2 (2026-07-11): cảnh CỜ điểm nhô MIỄN luật kề ±1 (trio build-up lấy cả 3); trùng + trần 8% + rải giữ nguyên** | Cùng chiều (miễn-kề là chủ đích user) |
| C5 vision gate (GATE_SOURCES=local) | Clip ytref đi đường sourcer local → **gate SOI luôn pick điểm nhô** | Lưới an toàn miễn phí |
| Shot thở (`videos_for_niche` đóng viral) | Class viral → tự đóng với ytref | Giữ |
| C4 vocab / signature / dna kho | Viral đã được gỡ chặn sau gói CHỌN → clip mới vào từ vựng kho bình thường | Không đổi hành vi |
| has_voice | Draft nháp không track voice → -1; clip cắt `-an` y viral | Không đổi |

Không tầng nào âm thầm lật quyết định của tầng mới; tầng mới không ngược chiều tầng nào.
**Lưu ý bản quyền riêng điểm nhô:** đoạn nhô = đoạn DỄ NHẬN DIỆN nhất của video nguồn →
luật c8 (6s + zoom 112% nướng + trần 8% + cấm kề + rải nguồn) áp NGUYÊN không nới;
nếu sau này muốn siết thêm riêng peak (vd trần N pick điểm nhô/nguồn/video) thì mở khi
có bằng chứng, không siết trước (filter-overload-guard).

## 5. Chi phí / ước lượng (bộ MOON 3 video ~45–50 phút tổng)

- CapCut tách ~300–500 cảnh → sau sàn 2s + trần 20s còn ~250–400 cảnh.
- Vision GLM ~$0,001/cảnh → **~$0,25–0,4/bộ** · cắt+tag ~20–35 phút (đa luồng như PB9).
- Heatmap: 3 call yt-dlp (vài giây/call). Editor: ~5–7 phút/bộ.

## 6. Milestone (P4 — mỗi bước 1 cổng)

| Mốc | Việc | Cổng |
|---|---|---|
| M1 | `ytpeaks.py` (dò đỉnh từ heatmap giả lập + thật; trả kèm **title + chapters** cho §3i) + rút ID tên file + đối chiếu duration + pytest | pytest + smoke 1 URL thật in đúng bảng đỉnh + title/chapters |
| M2 | Delta ingest (3a→3g) + **tag bối cảnh §3i** (source_title thật + section_hint + --topic) + pytest → **A/B mù ~40 cảnh** → **mẻ thử draft MOON thật** (dry-run soi số → chạy thật, tag theo cách thắng A/B) | pytest + **cổng MẮT kép**: (1) user phán bảng A/B tag · (2) đối chiếu vài clip cờ điểm nhô với đồ thị Most Replayed trên YouTube |
| M3 | PEAK_BONUS + `_row_to_candidate` + report → **video kiểm SP012 re-source → draft V12** | **cổng MẮT+TAI**: pick điểm nhô ra trận đúng chỗ, không phá bố cục pick cũ |
| Sau đạt | NHAT_KY + memory + BAN_DO_TRI_THUC (nguồn tool ME) + backup D: + git commit mốc | — |

## 7. Điểm treo — ĐÃ CHỐT TRỌN 2026-07-10

1. ✅ Cảnh >20s CÓ điểm nhô: **cắt 6s neo đỉnh** (user đồng ý đề xuất).
2. ✅ Trần >20s áp **mọi mẻ viral từ nay** (user đồng ý đề xuất); mẻ cũ KHÔNG dọn hồi tố.
3. ✅ `PEAK_BONUS = 0.5` phẳng primary+secondary (user ủy quyền, Claude chốt — lý do §3h);
   🔸 chỉnh sau video kiểm M3 nếu điểm nhô lấn/chìm.
