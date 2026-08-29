# C2 — ẨN DỤ HÌNH ẢNH & VETO SAI NGHĨA

> **📌 LỆCH SO VỚI BẢN GỐC (user chốt 2026-07-13 — lỗi "bán thuốc", DS5-083 Jenga/domino
> lặp lại đúng lỗi từng thấy ở space):** cấp 3 "metaphorical" ở §1 đọc lại theo luật
> **"VOICE kể ẩn dụ — HÌNH kể câu chuyện"**: (1) ẩn dụ thị giác chỉ dành cho câu THƯỜNG
> cần nâng tầm, và phải diễn **TRONG thế giới của video_subject/central_subject** khi thế
> giới đó quay được ("sụp đổ" trong video cá mập → rạn trống dần, KHÔNG domino đổ);
> (2) khi CHÍNH SCRIPT đã mượn ẩn dụ từ domain ngoài (Jenga, domino, "imagine…") hoặc
> nói trực tiếp với người xem → **KHÔNG minh họa cỗ xe chở nghĩa** — hình tiếp tục kể
> câu chuyện của chương; (3) hình chỉ rời thế giới chủ đề khi content nói thực thể/sự
> kiện THẬT (ăn khớp "ngoại lệ thực thể thật" §1). Ví dụ "lâu đài cát bị sóng cuốn /
> domino đổ = đẳng cấp" ở §1 vì thế chỉ còn đúng khi video KHÔNG có thế giới chủ đề quay
> được. Thực thi: prompts.py (pass 1 cấm central_subject chứa thủ pháp tu từ + pass 2
> SCRIPT-SIDE METAPHOR RULE) · khối luật trong direct_context.md (đường sâu) · skill
> dung-video · warning máy "nghi bán thuốc" ở direct-ingest (warning-only). Chi tiết:
> `MO_TA_VAN_HANH_BAN_THUOC.md`. Nguyên văn gốc dưới đây GIỮ để tham chiếu.

> **Vị trí:** kỹ năng "chọn hình gì cho câu thoại này" — trái tim của việc chọn footage.
> Foundation này ĐÓNG GÓP cho phễu [[c5-loc-xep-hang]] hai thứ: **(1) veto cứng #1 — sai
> nghĩa nghiêm trọng** (1 trong đúng 2 veto của toàn hệ thống, đã đóng băng) và **(2) chiều
> điểm nặng nhất — khớp nghĩa/concept (×3.0)**. C2 định nghĩa TIÊU CHÍ; cơ chế thực thi
> (chạy ở bước nào, sàn, log) thuộc c5 — file này không tự quyền loại footage.
> **C2b (veto mood) KHÔNG ở đây** — nội dung ở [[b1-mood-tone]]; theo c5 đã đóng băng, mood
> là điểm trừ rất nặng, không phải veto cứng.
> **Trạng thái phần 3: DỰ KIẾN 🔸** — chốt dần khi chạy Level 2.

---

## 1. Là gì

Một câu thoại có thể minh họa ở **3 cấp độ** (ví dụ thoại *"Anh ta mất tất cả chỉ sau một đêm"*):

1. **Literal (nghĩa đen):** người đàn ông buồn — *đúng nhưng nhàm*.
2. **Associative (liên tưởng):** căn phòng trống, két sắt mở toang — *khá hơn*.
3. **Metaphorical (ẩn dụ):** lâu đài cát bị sóng cuốn, domino đổ, nến tắt — *đẳng cấp*.

Editor giỏi không minh họa nghĩa đen — minh họa nghĩa bóng. NHƯNG toàn bộ sự sáng tạo đứng
trên một luật nền:

> **Quy tắc bất đối xứng:** footage **sai nghĩa là lỗi chí mạng** (khán giả thoát ngay);
> footage **nhạt-mà-đúng chấp nhận được**. Sáng tạo (associative/metaphorical) chỉ được
> phép trong vùng chắc chắn không sai.

Chính quy tắc này đẻ ra **veto sai nghĩa** — cửa loại tuyệt đối duy nhất về nội dung.

**Ngoại lệ thực thể thật:** thoại nhắc thực thể khán giả biết mặt (Trump, một chính sách có
tên, sự kiện thời sự) → KHÔNG dùng cả 3 cấp trên — phải cho xem **ảnh/footage thật của đúng
thực thể đó** (ảnh báo chí + Ken Burns là chuẩn commentary). Ẩn dụ hóa thực thể thật = khán
giả thấy bị lừa.

## 2. Yếu tố ảnh hưởng

| Yếu tố | Ảnh hưởng thế nào |
|---|---|
| **Chủ đề thật của beat (central_subject)** | Nhiều câu script MƯỢN ẩn dụ ngôn ngữ từ domain khác ("lò phản ứng của tự nhiên" nói về MẶT TRỜI) — minh họa bề mặt chữ = sai nghĩa. Phải neo hình vào chủ đề thật của chương, không phải chữ trên bề mặt. |
| **Hiệu ứng Kuleshov (ngữ cảnh chuỗi)** | Nghĩa của 1 shot do shot đứng cạnh quyết định → không chọn footage từng câu độc lập; chi tiết chuỗi ở [[c3-ngu-canh-chuoi]]. |
| **Loại nội dung beat** | Số liệu → graphic/infocard, KHÔNG bịa ẩn dụ stock; thực thể thật → route entity; cảnh generic → stock; đã có phân tuyến [[c1-phan-tuyen-nguon]]. |
| **Trần cụ thể (specificity ceiling)** | Footage không được CỤ THỂ hơn mức xác minh được: script nói "đường tàu Hà Nội" mà không chắc clip quay ở Hà Nội → dùng cận cảnh giấu bối cảnh hoặc cảnh generic. |
| **Mức sáng tạo niche chịu được** | Tỉ lệ literal/associative/metaphorical là VÍ DỤ khởi điểm (~60/30/10) — niche commentary thời sự literal nhiều hơn, niche chiêm nghiệm ẩn dụ nhiều hơn → số thật học từ DNA. |

## 3. Cách làm THỰC TẾ ở project này — 🔸 DỰ KIẾN

### Luồng chạy (2 thì: QUYẾT Ý ĐỊNH lúc direct → KIỂM KẾT QUẢ lúc chọn)

**Thì 1 — direct (đã chạy hôm nay):** với mỗi beat, NÃO quyết theo thứ tự:
1. `sourcing_route` — entity | stock | local_library | graphic (phân tuyến trước, cấp độ sau);
2. `visual_level` — literal | associative | metaphorical (mix toàn chương, ẩn dụ để dành
   chỗ đắt nhất: stakes, cảm xúc, kết luận);
3. `visual_concept` — MỘT CẢNH máy quay thật quay được, neo vào central_subject của chương;
4. `search_queries` — tiếng Anh ≤4 từ/query (stock site là keyword matcher, không semantic).

**Thì 2 — kiểm lúc chọn (CHƯA CÓ — chính là "đầu chấm nghĩa" backlog #2 của [[c5-loc-xep-hang]]):**
hiện pipeline **"tin query mù"** — query tốt nhưng Pexels trả gì lấy nấy, không ai kiểm.
Đầu chấm nghĩa sẽ xét mô tả/title/tag của TỪNG ứng viên vs `visual_concept` + central_subject:

- **VETO (cửa 2 của phễu)** khi **sai nghĩa NGHIÊM TRỌNG** — định nghĩa hẹp, chỉ 3 dạng:
  (i) chủ đề khác hẳn (concept "mặt trời/plasma" nhưng clip về lò nướng bánh);
  (ii) thực thể SAI (cần Trump nhưng ảnh người khác; cần Hạ Long nhưng cảnh vịnh Thái Lan
  nhận diện được); (iii) vi phạm trần cụ thể theo hướng NGƯỢC (clip khẳng định bối cảnh cụ
  thể SAI với script).
- **KHÔNG veto** khi chỉ nhạt/chung chung/kém đẹp — cái đó là ĐIỂM THẤP ở chiều khớp nghĩa
  (×3.0), để phễu cân với mood/variety. Nhạt-mà-đúng phải sống sót tới vòng chấm.
- Khi phân vân giữa concept đắt-nhưng-rủi-ro và concept nhạt-nhưng-chắc → **chọn chắc**
  (bất đối xứng). Phân vân veto hay không → KHÔNG veto, chấm điểm thấp + ghi log (sàn 3
  của c5 được giữ).

### 3b. PHÂN RÃ NĂNG LỰC

> Loại: **(a)** đã có sẵn · **(b)** cần code mới ỐNG · **(c)** NÃO quyết lúc chạy · **(d)** cần dữ liệu DNA (Phase B)

| Luật ngôn-ngữ-editor | Hệ thống chạy thế nào | Loại | Trạng thái |
|---|---|---|---|
| 3 cấp độ + mix ~60/30/10 + "ẩn dụ để chỗ đắt nhất" | prompt direct pass 2 (`director/prompts.py`) | (a)+(c) | ✅ đã có trong prompt |
| Neo central_subject — chống bẫy bề-mặt-chữ | pass 1 chốt central_subject/chương → pass 2 neo mọi beat kể cả câu ẩn dụ/setup | (a) | ✅ đã có |
| Bất đối xứng + trần cụ thể | luật trong prompt pass 2 ("SPECIFICITY CEILING", "boring but correct is acceptable") | (a) | ✅ đã có |
| Schema chở quyết định | `Beat.sourcing_route/visual_level/visual_concept/search_queries/visual_anchor` (`project.py:218-223`) + Pydantic validate (NT4) | (a) | ✅ đã có |
| Ngoại lệ thực thể thật | route entity: Serper/GoogleCSE tìm ảnh thật, cache `library/<niche>/entity/<slug>/`, cấm hãng watermark (`sourcer/entity.py`) | (a) | ✅ đã có |
| **Veto sai nghĩa + chấm khớp nghĩa lúc chọn** | đầu chấm nghĩa trong phễu `ranker/` — NÃO xét ứng viên vs concept | **(b)+(c)** | ❌ **= backlog #2 của c5, KHÔNG phải mục mới** — tiêu chí veto/điểm lấy từ file này |
| Mix cấp độ theo niche (60/30/10 chỉ là ví dụ) | đo tỉ lệ thật từ video viral niche → đè số prompt (số cứng trong prompt GỠ khi L2b sâu, cùng đợt với số pacing/hình thở) | (d) | ❌ Phase B |
| Từ điển ẩn dụ theo niche | học cặp "khái niệm ↔ footage ẩn dụ" từ DNA (từ điển generic đã có trong prompt làm mồi) | (d) | ❌ Phase B |

**→ Backlog code rút ra:** KHÔNG thêm mục mới — veto sai nghĩa + chấm khớp nghĩa chính là
**backlog #2 "đầu chấm nghĩa (NÃO)" đã ghi ở [[c5-loc-xep-hang]]**; file này cấp tiêu chí
(3 dạng veto hẹp, nhạt-mà-đúng không chết, phân vân → không veto).

## 4. Cạm bẫy / ranh giới

- **Bẫy bề-mặt-chữ (lỗi sai nghĩa tệ nhất):** script mượn ẩn dụ ngôn ngữ ("cỗ máy in tiền",
  "lò phản ứng của tự nhiên") → minh họa nghĩa đen bề mặt là SAI dù match từng chữ. Luôn hỏi:
  beat này THẬT RA nói về cái gì trong chương?
- **Ẩn dụ hóa thực thể thật = lừa khán giả.** "Trump's gold card" → ảnh Trump thật, không
  phải stock thẻ tín dụng vàng.
- **Bịa ẩn dụ stock cho beat số liệu.** Số liệu → graphic/infocard route, đừng tìm "ba đồng
  xu xếp chồng" cho "GDP tăng 3%".
- **Veto phình to.** Định nghĩa "nghiêm trọng" phải giữ HẸP (3 dạng ở phần 3) — nếu đầu chấm
  nghĩa bắt đầu veto cả footage "hơi lệch/nhạt" thì phễu c5 sập sàn; kill-log sẽ lộ ngay
  ("% chết vì veto nghĩa" cao bất thường → siết lại định nghĩa, không siết footage).
- **Sáng tạo ngoài vùng an toàn.** Metaphorical chỉ khi chắc chắn không gây hiểu sai; mọi
  phân vân → tụt xuống associative/literal.

## 5. Học gì từ DNA niche (Phase B)

| Tín hiệu | Dùng để |
|---|---|
| Tỉ lệ literal/associative/metaphorical thật của video viral niche | đè mix ví dụ 60/30/10 |
| Cặp "khái niệm ↔ hình ẩn dụ" niche hay dùng | từ điển ẩn dụ theo niche (mồi cho visual_concept) |
| Thực thể xuất hiện lặp lại trong niche | làm dày cache entity trước (`library/<niche>/entity/`) |
| Niche có khoan dung sai nghĩa thấp/cao (commentary thời sự vs chill ambient) | tinh ngưỡng chấm nghĩa + độ hẹp veto theo niche |
