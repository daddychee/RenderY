# C1 — PHÂN TUYẾN NGUỒN (sourcing route: hình này lấy từ ĐÂU)

> **Vị trí:** quyết định ĐẦU TIÊN cho mỗi beat, trước cả việc nghĩ hình gì — "beat này lấy
> hình từ tuyến nào: entity / stock / local_library / graphic". Với phễu [[c5-loc-xep-hang]],
> c1 chính là **bước THU**: tuyến nào được chọn thì ứng viên đổ vào phễu từ tuyến đó.
> Phân tuyến KHÔNG phải veto — nó khoanh vùng tìm; footage sai nghĩa lọt vào vẫn bị cửa
> veto của [[c2-an-du-veto]] bắt. Nội dung chưng cất từ luật đã chạy trong code + các mảnh
> đã chốt ở c2/c5, CỘNG chỉnh sửa quan trọng của user khi duyệt (2026-07-02, nguyên văn ở
> GHI_CHEP_GOC §8): **kho local học từ project là tuyến CHÍNH, stock chỉ bổ trợ.**
> **Trạng thái phần 3: DỰ KIẾN 🔸** (riêng Thì 1 đã chạy thật hôm nay).

---

## 1. Là gì

Cùng một câu thoại, hình minh họa có thể đến từ **4 tuyến** rất khác nhau về bản chất:

| Tuyến | Khi nào | Bản chất |
|---|---|---|
| **entity** — ảnh/footage THẬT của đúng thực thể | Beat nhắc thứ THẬT kiểm chứng được: người, tổ chức, chính sách có tên, sự kiện có ngày; **V2 (user duyệt 2026-07-09) thêm 3 nhóm:** máy móc/phương tiện ĐƯỢC ĐẶT TÊN (tàu vũ trụ, tên lửa, kính thiên văn, rover, vệ tinh, trạm — Orion, Saturn V, JWST...) · sự kiện thật của chương trình có tên (phóng, đổ bộ, spacewalk, crew walkout) · thiên thể/địa hình vũ trụ NÊU ĐÍCH DANH khi ảnh thật tồn tại (far side, hố Tycho) | "Khán giả google được thì PHẢI cho xem đồ thật" — mô phỏng/diễn viên generic thay đồ thật có tên = lừa (WRONG-vs-BLAND). Ảnh báo chí/NASA + Ken Burns ([[f2-ken-burns]] — đã chạy, ảnh không còn đứng yên). KHÔNG ẩn dụ hóa (ngoại lệ thực thể thật của [[c2-an-du-veto]]). **Ngân sách theo niche: đời sống/travel 0-1 beat/video; facts (space, science, history) ~3-8.** Địa danh TRÊN TRÁI ĐẤT (thành phố, landmark) vẫn CẤM entity — đi stock video (thiên thể đích danh là ngoại lệ). |
| **local_library** — kho footage HỌC từ project | Beat khớp footage trong kho — kho xây từ RẤT NHIỀU project tải về (ban đầu có thể ~100) + video viral: hệ thống học, cắt footage ra, tag vision (Phase B) | **Tuyến CHÍNH của project này** (user chốt 2026-07-02 — KHÁC project cũ nơi stock là mặc định). Footage "của mình": đã tag, đã lọc, mang chữ ký ([[c6-footage-chu-ky]]). Đa niche: space, deepsea, travel,... |
| **stock** — kho stock (Pexels) | Cảnh generic mà kho local CHƯA phủ, không gắn thực thể cụ thể | Tuyến BỔ TRỢ — lấp lỗ hổng kho. Chất lượng sống chết theo query ([[c4-tu-khoa-tim]]). |
| **graphic** — biểu đồ/thẻ chữ tự render | Số liệu/so sánh là NGÔI SAO của beat | Chart động (bar/line/pie) hoặc placeholder cho editor; số phải là số THẬT từ script. |

Luật vàng của tuyến: **thứ tự quyết định là route TRƯỚC → rồi mới cấp độ sáng tạo →
concept → query** ([[c2-an-du-veto]] Thì 1). Chọn nhầm tuyến thì mọi bước sau đều sai
theo — ví dụ kinh điển (đã nằm trong prompt): *"Trump's gold card costs $1 million"* mà
đi tuyến stock tìm "thẻ tín dụng vàng" = lỗi chí mạng, dù query rất "khớp chữ".

**Graphic có 2 tầng quyết định con** (đã chạy trong code):
- **Chart hay không:** so sánh ≥2 số / xu hướng theo thời gian → chart thật (`graphic_spec`);
  MỘT con số lẻ → KHÔNG chart, chỉ text overlay đè lên footage thường (route vẫn là stock).
- **Full hay half:** số liệu là toàn bộ câu chuyện → chart đầy màn (route=graphic);
  có bối cảnh đáng giữ trên hình → chart nửa phải + footage nửa trái (route=stock/entity/local,
  KHÔNG phải graphic — nếu đặt graphic sẽ thành 2 chart đè nhau, bug đã dính 15/06).

## 2. Yếu tố ảnh hưởng

| Yếu tố | Ảnh hưởng thế nào |
|---|---|
| **Beat có thực thể google-được không** | Có → BẮT BUỘC entity, cấm mọi tuyến khác. Đây là ranh giới cứng nhất của phân tuyến (nối thẳng veto dạng ii của c2: thực thể SAI). |
| **Số liệu là sao chính hay nhắc qua** | Sao chính + so sánh được → graphic; nhắc qua → stock + overlay chữ rẻ; so sánh neo vào vật quen (ly cà phê, bình xăng) → LUÔN stock quay vật đó, không chart. |
| **Kho local phủ tới đâu** | Kho học từ ~100 project là NGUỒN CHÍNH — beat nào kho phủ thì đi local_library (rẻ, đúng chữ ký, đã tag); stock chỉ lấp chỗ kho chưa phủ. Code hiện đã ưu tiên local khi trùng ứng viên (P6) — đúng chiều, nhưng luật route trong prompt còn coi local là "khi có niche profile" (logic cũ) → phải đảo lại khi L2b sâu. |
| **`visual_anchor` của beat** | Beat neo (anchor=true) hình phải CHỞ nghĩa → phân tuyến phải chuẩn; beat chêm (anchor=false) chỉ cần đúng chủ đề + đúng mood → thường rơi về local/stock thoáng hơn. |
| **Ngân sách graphic** | Chart/infocard là pattern interrupt — dày quá thành PowerPoint. Prompt hiện giới hạn ~1 graphic beat/60s thoại + tối đa 2 chart & 2 info-card/chương (số = VÍ DỤ khởi điểm, tinh theo DNA). |
| **Niche** | Commentary thời sự nặng entity; chill travel nặng local/stock đẹp; tài chính nặng graphic. Tỉ lệ tuyến là chữ ký niche → DNA. |

## 3. Cách làm THỰC TẾ ở project này — 🔸 DỰ KIẾN

### Luồng chạy (2 thì — cùng khuôn c2/c7: Ý ĐỊNH lúc direct → THỰC THI lúc source)

**Thì 1 — direct quyết tuyến (ĐÃ CHẠY hôm nay):** prompt pass 2 bắt LLM quyết
`sourcing_route` ĐẦU TIÊN cho từng beat theo đúng luật phần 1 (kèm luật chart/layout,
ngân sách, ví dụ Trump). Kết quả chở trong `Beat.sourcing_route` + `entity_queries`
(tuyến entity) / `search_queries` 3 tầng (tuyến stock/local) / `graphic_spec` (chart).

**Thì 2 — source thực thi theo tuyến (ĐÃ CHẠY, sẽ được phễu c5 bọc lại):**
`sourcer/runner.py` dispatch 3 nhánh:
1. **entity** → `_source_entity`: cache theo slug thực thể (tải 1 lần dùng mãi) → Serper/CSE
   tìm ảnh thật, cấm domain watermark, bỏ SVG/ảnh hỏng, gắn `licensing_flag` → hết sạch
   thì `needs_human` (TUYỆT ĐỐI không tự rơi về stock ẩn dụ — thà để người chọn).
2. **graphic** → `_source_graphic`: có `graphic_spec` → render chart động; không có →
   placeholder cho editor + tự tải nền lót theo tầng thematic. Chart half + info-card
   render thêm làm PiP sau khi đã có footage chính.
3. **stock | local_library** → `_source_stock` (chung nhánh): gom ứng viên local TRƯỚC
   (P6, kèm geo-gate PA2 lọc clip sai quốc gia) + Pexels 3 tầng specific→broad→thematic
   → loại trùng trong video (P7 cứng) → ưu tiên clip dài ≥1.2× beat → phạt mềm P7
   → tải; hỏng thì thử ứng viên kế; cạn thang → `needs_human`.

**Khi phễu c5 vào (tương lai):** bước THU của phễu chính là bước "gom ứng viên" ở trên —
c1 không đổi gì về kiến trúc, chỉ đổi chỗ đứng: thay vì heuristic chọn ngay (Phase 0),
ứng viên thu theo tuyến sẽ đi qua veto 2 cửa → chấm điểm → sàn 3. **Phân tuyến vẫn quyết
TRƯỚC phễu và không phải là một luật chấm** — nó quyết "phễu hút từ vòi nào".

### 3b. PHÂN RÃ NĂNG LỰC

> Loại: **(a)** đã có sẵn · **(b)** cần code mới ỐNG · **(c)** NÃO quyết lúc chạy · **(d)** cần dữ liệu DNA (Phase B)

| Luật ngôn-ngữ-editor | Hệ thống chạy thế nào | Loại | Trạng thái |
|---|---|---|---|
| 4 tuyến + "route là quyết định đầu tiên" + ví dụ Trump | `_SOURCING_RULES` trong `director/prompts.py` (pass 2) | (a)+(c) | ✅ đã có |
| Schema chở quyết định tuyến | `Beat.sourcing_route/entity_queries/search_queries/graphic_spec` (`project.py`) + Pydantic (NT4) | (a) | ✅ đã có |
| Thực thi 3 nhánh theo tuyến | `sourcer/runner.py::run_source` dispatch | (a) | ✅ đã có |
| Entity: cache + cấm watermark + không rơi về stock | `sourcer/entity.py` + `_source_entity` (needs_human khi cạn) | (a) | ✅ đã có |
| Graphic: chart bar/line/pie + full/half + info-card + nền lót | `packager/charts.py`, `packager/infocard.py`, `_source_graphic` | (a) | ✅ đã có |
| Local ưu tiên + geo-gate + thang fallback 3 tầng + P7 | `_source_stock` (P6, PA2, specific→broad→thematic→needs_human) | (a) | ✅ đã có |
| Ngân sách graphic (~1/60s, ≤2 chart & ≤2 card/chương) | luật trong prompt — số là VÍ DỤ, chưa ai đo đúng/sai theo niche | (a)→(d) | ✅ chạy bằng số ví dụ; số thật chờ DNA |
| **Bước THU của phễu (gom ứng viên theo tuyến, giữ pool thay vì chọn ngay)** | tái dùng chính phần gom ứng viên hiện có, chuyển đầu ra cho `ranker/` | **(b)** | ❌ **= một phần của backlog #1 "khung phễu" ở c5, KHÔNG phải mục mới** |
| **Local là tuyến CHÍNH, stock bổ trợ (user chốt 2026-07-02)** | (1) KHO: học từ ~100 project tải về + video viral — cắt footage, tag vision = chính là Phase B; (2) PROMPT: luật route hiện viết theo logic cũ ("local khi có niche profile", stock mặc định) → ĐẢO mặc định khi L2b sâu (local trước, stock lấp lỗ) | (d)+(b) | ❌ kho chờ Phase B; sửa prompt thuộc gói L2b sâu (gỡ số cứng), KHÔNG mở mục mới |
| Tỉ lệ tuyến theo niche (bao nhiêu % entity/stock/local/graphic) — đa niche: space, deepsea, travel | đo từ video viral niche → tinh luật route + ngân sách graphic trong prompt | (d) | ❌ Phase B |

**→ Backlog code rút ra: KHÔNG mở mục mới.** Bước THU thuộc backlog #1 "khung phễu"
đã ghi ở [[c5-loc-xep-hang]]; file này chốt tiêu chí phân tuyến mà bước THU phải tôn trọng.

## 4. Cạm bẫy / ranh giới

- **Bê logic "stock mặc định" của project cũ.** Ở đây kho local học từ project là tuyến
  chính — nếu prompt/route vẫn dồn beat về stock thì kho đã tag thành vô dụng, video mất
  chữ ký, tốn query Pexels vô ích. (Chính bản nháp đầu của file này dính lỗi đó — user sửa
  2026-07-02, nguyên văn ở GHI_CHEP_GOC §8.)
- **Ẩn dụ hóa thực thể thật** — lỗi phân tuyến chí mạng nhất (Trump gold card → stock thẻ
  vàng). Đã có luật trong prompt; đầu chấm nghĩa (c5 backlog #2) sẽ bắt thêm ở Thì 2 nếu lọt.
- **Entity cạn → tự đổi sang stock.** CẤM. Tuyến entity cạn thì `needs_human` — một ảnh
  "gần giống" người/sự kiện thật còn tệ hơn thiếu hình (veto dạng ii của c2 chờ sẵn).
- **Nhồi graphic.** Mỗi con số thành một chart → video thành slide PowerPoint, mất footage
  kể chuyện. Số nhắc qua → stock + overlay; so sánh neo vật quen → stock quay vật đó.
- **Chart half mà đặt route=graphic** → 2 chart đè nhau (bug 15/06, đã fix bằng luật trong
  prompt + guard trong runner — đừng nới lỏng khi viết lại).
- **Phân tuyến thành veto thứ 3.** Route chỉ khoanh vùng THU; nếu sau này thêm kiểm tra
  "footage lệch tuyến" thì đó là ĐIỂM TRỪ trong phễu, không phải cửa loại (luật meta c5).
- **Quên rằng route hiện là quyết định MỘT CHIỀU.** Tuyến chính cạn là needs_human luôn,
  không thử tuyến khác. Với entity đó là chủ đích (xem trên); với stock↔local đó là điều
  phễu tương lai có thể nới (pool trộn sẵn 2 nguồn rồi) — đừng "sửa lỗi" này ngoài khung phễu.

## 5. Học gì từ DNA niche (Phase B)

| Tín hiệu | Dùng để |
|---|---|
| Tỉ lệ tuyến thật của video viral niche (% entity/stock/local/graphic) | tinh luật route + ngân sách graphic theo niche (thay số ví dụ 1/60s) |
| Thực thể lặp lại trong niche | làm dày cache entity TRƯỚC khi dựng (`library/<niche>/entity/`) — trùng dòng đã ghi ở c2 §5 |
| Kho footage cắt từ ~100 project + video viral (tag vision) phủ concept gì | nền của tuyến CHÍNH local_library — kho càng dày, route local càng nhiều, stock càng teo lại thành lấp lỗ |
| Loại số liệu niche hay trình bày kiểu gì (chart full / half / chỉ overlay) | tinh luật chọn layout graphic theo niche |
