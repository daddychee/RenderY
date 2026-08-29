# C4 — TỪ KHÓA TÌM (query: dịch Ý ĐỒ HÌNH sang ngôn ngữ của KHO)

> **Vị trí:** chạy NGAY SAU phân tuyến [[c1-phan-tuyen-nguon]] — route quyết "hút từ vòi
> nào", c4 quyết "nước gì chảy vào phễu": query tốt thì pool ứng viên giàu và đúng nghĩa,
> query hỏng thì phễu [[c5-loc-xep-hang]] chỉ còn lọc rác. Nguyên lý gốc: **query là BẢN
> DỊCH của visual_concept sang ngôn ngữ của từng kho** — và chỉ là PHỎNG ĐOÁN, không phải
> bảo chứng: phễu chấm ứng viên THẬT, không bao giờ tin query mù.
> Nội dung chưng cất từ luật đã chạy trong code (`_QUERY_RULES`, `pexels.py`, `local.py`)
> + fact nền local-first (GHI_CHEP_GOC §8). **Trạng thái phần 3: DỰ KIẾN 🔸** (riêng
> Thì 1 + Thì 2 phần stock/local đã chạy thật hôm nay).

---

## 1. Là gì

Cùng một `visual_concept` ("phi hành gia lơ lửng ngoài trạm ISS"), muốn ra footage phải
dịch thành từ khóa — nhưng **hai kho nói hai NGÔN NGỮ khác nhau**:

| Kho | Ngôn ngữ của kho | Query phải viết thế nào |
|---|---|---|
| **local_library** (tuyến CHÍNH — kho học từ ~100 project, tag vision Phase B) | **vocabulary của schema tag GLM**: subject / description / tags / category / đường dẫn thư mục | Từ khóa phải TRÚNG từ vựng tag — kho không "hiểu" đồng nghĩa. Tag ghi "spacewalk" mà query "astronaut floating" = trượt dù cùng một cảnh. |
| **stock Pexels** (BỔ TRỢ — lấp chỗ kho chưa phủ) | **keyword matcher**, KHÔNG phải semantic search | Tối đa 4 từ, công thức `chủ thể + hành động/bối cảnh (+ cỡ cảnh nếu còn chỗ)`. Query dài kiểu văn xuôi → trả rác hoặc rỗng. |

**3 tầng query = thang NỚI NGHĨA có kiểm soát** (đã chạy trong code, tầng sau chỉ mở khi
tầng trước nghèo):

| Tầng | Dạng | Ví dụ (niche space) | Vai trò |
|---|---|---|---|
| **specific** | 2–3 query, 3–4 từ, mang thực thể/địa danh cụ thể | "astronaut spacewalk iss" | Đúng nghĩa nhất — tầng DUY NHẤT được match kho local (xem cạm bẫy geo) |
| **broad** | 1–2 query, 2 từ, cố ý GENERIC | "space station" | Lưới vớt cho Pexels khi specific cạn |
| **thematic** | 1–2 query gọi tên chủ đề niche | "outer space" | Phao cuối trước khi `needs_human`; cũng là nguồn nền lót cho graphic |

Cái thang này chính là hiện thân của bất đối xứng WRONG-vs-BLAND ([[c2-an-du-veto]]):
càng tụt tầng, hình càng NHẠT đi chứ không được SAI đi — nhạt-mà-đúng ăn điểm thấp,
sai nghĩa mới chết.

## 2. Yếu tố ảnh hưởng

| Yếu tố | Ảnh hưởng thế nào |
|---|---|
| **Route của beat ([[c1-phan-tuyen-nguon]])** | Route quyết TRƯỚC, query viết SAU và viết CHO route đó: entity → `entity_queries` (tên riêng, đủ dài để google); stock/local → `search_queries` 3 tầng; graphic → không cần query chính (chỉ tầng thematic làm nền lót). |
| **Kho nào đang tìm** | Cùng concept, hai bản dịch: local cần trúng vocabulary tag; Pexels cần công thức 4-từ. Hiện code dùng CHUNG một bộ query cho cả hai — chạy được vì tag hiện tại cũng là tiếng Anh mô tả, nhưng khi schema tag Phase B chốt thì đây là chỗ phải bàn lại (xem 3b). |
| **Địa danh/thực thể trong script** | Query tầng specific PHẢI chở địa danh khi beat có địa danh — đó là lý do local chỉ được match tầng specific: AND-match tự lọc đúng nơi. Geo-gate PA2 chặn thêm tầng dưới (clip sai quốc gia so với script bị loại). |
| **Độ giàu của kho local** | Kho phủ concept → query local ăn ngay (rẻ, đúng chữ ký); kho chưa phủ → rơi xuống Pexels. Kho càng dày (Phase B tag xong ~100 project) thì tỉ lệ local-hit càng cao — đo được, thành DNA. |
| **`visual_concept` có quay được không** | Query chỉ tốt khi concept là cảnh camera THẬT quay được (chủ thể cụ thể + hành động cụ thể + nơi chốn cụ thể). Concept trừu tượng ("sự cô đơn của vũ trụ") → không dịch nổi thành 4 từ → luật trong prompt bắt concept phải filmable TRƯỚC khi viết query. |
| **Hạn mức API** | Pexels 200 query/giờ/key — code đã xoay nhiều key + cache query trong SQLite (query trùng không tốn mạng). Ảnh hưởng thiết kế: đừng sinh query thừa "cho chắc"; tầng sau chỉ chạy khi tầng trước nghèo. |

## 3. Cách làm THỰC TẾ ở project này — 🔸 DỰ KIẾN

### Luồng chạy (2 thì — cùng khuôn c1/c2/c7)

**Thì 1 — direct viết query (ĐÃ CHẠY hôm nay):** prompt pass 2 (`_QUERY_RULES`) bắt LLM,
SAU khi đã chốt route + cấp độ + concept: viết `search_queries` 3 tầng theo đúng khuôn
phần 1 (max 4 từ, công thức chủ thể + hành động, specific mang địa danh). Số lượng
query mỗi tầng (2–3 / 1–2 / 1–2) là số ĐANG CHẠY — coi là ví dụ khởi điểm, không phải luật.

**Thì 2 — source thực thi (ĐÃ CHẠY, phễu c5 sẽ bọc lại):** với route stock/local:
1. **Local trước** (`find_local_candidates`): CHỈ lấy tầng specific → AND-match từng từ
   trên subject/description/tags/category/folder (LIKE) → bỏ file đã xóa → geo-gate PA2
   → tối đa 5 ứng viên.
2. **Pexels bù** (`search_tiered`): chạy tầng specific → broad → thematic, tầng sau chỉ
   mở khi tổng ứng viên < 5; mỗi query cache SQLite; 429 thì xoay key; lọc landscape,
   chọn bản ~1080p.
3. Pool gộp → khử trùng lặp → (hiện tại: heuristic Phase 0 chọn; tương lai: đổ vào phễu
   c5). **Cạn cả thang → `needs_human`** — không "sáng tác" thêm query để cứu.

**Hướng padoma (local-first) — ✅ ĐÃ CODE (C4, 2026-07-08, `MO_TA_VAN_HANH_C4_TU_VUNG.md`):**
cả 2 câu hỏi treo đã chốt: (1) query local viết theo **controlled vocabulary** — máy in
từ vựng THẬT của kho (khối TỪ VỰNG KHO trong `direct_context.md`, sinh từ `db.vocab_for_niche`)
cho NÃO khi đạo diễn; (2) **TÁCH `queries.local`** riêng (tier thứ 4 trong SearchQueries,
optional — rỗng = hành vi cũ). Local match tier local TRƯỚC rồi specific; broad/thematic
vẫn cấm; geo-gate giữ nguyên. Mỗi run source tự báo "local-first (C4): X/Y beat có ứng
viên kho · kho thắng Z pick" vào report.

### 3b. PHÂN RÃ NĂNG LỰC

> Loại: **(a)** đã có sẵn · **(b)** cần code mới ỐNG · **(c)** NÃO quyết lúc chạy · **(d)** cần dữ liệu DNA (Phase B)

| Luật ngôn-ngữ-editor | Hệ thống chạy thế nào | Loại | Trạng thái |
|---|---|---|---|
| Query ≤4 từ + công thức + 3 tầng + concept phải filmable | `_QUERY_RULES` trong `director/prompts.py` (pass 2) | (a)+(c) | ✅ đã có |
| Thang nới tầng "rẻ trước đắt sau, tầng sau khi tầng trước nghèo" | `pexels.py::search_tiered` (ngưỡng 5 ứng viên/tầng — số ví dụ) + cache SQLite + xoay key 429 | (a) | ✅ đã có |
| Local chỉ match tầng specific + geo-gate | `local.py::find_local_candidates` + `passes_geo` (bug 20/06 đã trả giá) | (a) | ✅ đã có |
| Match kho local theo từ khóa | `library/db.py::search_assets` — LIKE AND-match mọi từ trên 5 trường | (a) | ✅ đã có (đủ cho kho nhỏ hiện tại) |
| Dịch concept → query đúng ngôn ngữ từng kho | LLM lúc direct — chất lượng dịch là việc của NÃO, không có code nào cứu được query tồi | (c) | ✅ chạy; sẽ giàu lên khi có vocabulary tag |
| **Query local theo controlled vocabulary của schema tag** | `db.vocab_for_niche` in từ vựng kho vào direct_context.md → NÃO điền `search_queries.local` (tier 4 mới, optional) → `local.py` match tier local trước specific | **(b)+(c)** | ✅ ĐÃ CODE — C4 2026-07-08 (`MO_TA_VAN_HANH_C4_TU_VUNG.md`) |
| Match local "thông minh" hơn LIKE khi kho phình to (~100 project) | nếu LIKE trượt nhiều (đo bằng kill-log/tỉ lệ local-hit) mới nâng cấp — đừng xây trước | (b) | ⏸ CHƯA làm — chờ số liệu thật sau Phase B |
| Từ nào hay cạn / hay trả rác trên Pexels theo niche | đo từ log query các lần dựng | (d) | ❌ Phase B |

**→ Backlog code còn lại: KHÔNG.** Việc dạng (b) — query theo vocabulary tag — đã đóng
ở gói C4 (2026-07-08). Còn ngỏ dạng (d): bảng đồng nghĩa concept↔tag + từ hay cạn trên
Pexels — chờ log nhiều run thật (đo bằng dòng "local-first (C4)" trong report).

## 4. Cạm bẫy / ranh giới

- **Tin query mù.** Query khớp chữ ≠ đúng nghĩa ("gold card" ra thẻ tín dụng; "apple"
  ra quả táo). Query chỉ là bước THU — phễu c5 (veto nghĩa c2 + chấm điểm) mới là người
  kiểm ứng viên thật. Đừng bao giờ thiết kế bước nào "vì query đã specific nên khỏi kiểm".
- **Query dài kiểu văn xuôi cho Pexels.** "luxury gold card velvet surface spotlight" →
  rác hoặc rỗng. Đã thành luật trong prompt (max 4 từ) — đừng nới khi viết lại prompt.
- **Cho local match tầng broad/thematic.** Bug THẬT 20/06: tầng dưới cố ý generic, local
  match vào là footage SAI ĐỊA DANH đè footage đúng (video Hà Nội ra cảnh Hà Giang). Khi
  đảo local-first ở padoma, cám dỗ sẽ là "nới cho local match nhiều hơn để tăng local-hit"
  — CHỈ được nới qua vocabulary tag có kiểm soát, không qua LIKE generic. Khán giả > tái dùng.
- **Viết query local bằng ngôn ngữ Pexels (và ngược lại).** Hai kho hai ngôn ngữ; khi có
  schema tag mà vẫn để NÃO "dịch tự do" thì local-hit sẽ thấp một cách oan uổng và mọi người
  tưởng kho nghèo — thực ra là dịch trượt vocabulary.
- **Sinh thêm query để "cứu" beat cạn.** Cạn cả thang → `needs_human`. Query sáng tác thêm
  lúc tuyệt vọng gần như chắc chắn sai nghĩa — thà thiếu hình còn hơn hình sai.
- **Coi số trong file này là luật.** 4 từ, 5 ứng viên/tầng, 2–3 query/tầng đều là số ĐANG
  CHẠY của project cũ = ví dụ khởi điểm. Số thật theo niche chờ DNA + log chạy thật.

## 5. Học gì từ DNA niche (Phase B)

| Tín hiệu | Dùng để |
|---|---|
| **Vocabulary tag thực tế của kho** (tag xong ~100 project mới biết kho "nói" những từ gì) | phát danh sách từ vựng cho NÃO khi viết query local — nền của nguyên tắc controlled vocabulary |
| Tỉ lệ local-hit vs rơi xuống stock, theo concept/niche | đo kho phủ tới đâu → biết cần nạp thêm project loại nào; đồng thời là thước đo "đã local-first thật chưa" |
| Query nào hay trả rỗng/rác trên Pexels theo niche | tinh luật viết query trong prompt (từ cấm, từ nên dùng) thay vì học lại mỗi lần dựng |
| Cặp đồng nghĩa hay trượt (concept nói A, tag ghi B) | bảng map từ đồng nghĩa cho bước dịch — rẻ hơn nâng cấp engine match |
