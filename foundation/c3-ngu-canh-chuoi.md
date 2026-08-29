# C3 — NGỮ CẢNH CHUỖI (hiệu ứng Kuleshov: nghĩa của shot do HÀNG XÓM quyết)

> **Vị trí:** bổ đề của [[c2-an-du-veto]] — c2 chấm nghĩa TỪNG beat độc lập; c3 nói thêm
> rằng **nghĩa một shot còn do shot đứng cạnh quyết định**, nên tiêu chí "đúng nghĩa" của
> đầu chấm nghĩa (backlog #2 của [[c5-loc-xep-hang]]) phải nhìn CỬA SỔ vài beat, không chấm
> câu trong chân không. c3 **KHÔNG thêm veto** (luật meta c5: chỉ 2 veto) — nó tinh chiều
> điểm **khớp nghĩa (×3.0)** và **variety (×1.5)** bằng ngữ cảnh chuỗi. Cũng KHÔNG lấn c7:
> [[c7-shot-variety]] lo LẶP CỠ CẢNH; c3 lo LẶP/LỆCH NGHĨA theo mạch.
> Nội dung chưng cất từ luật đã chạy (`_DIRECTOR_ROLE` Kuleshov, `_CONTEXT_COHERENCE`
> central_subject, P7 dedup) + các mảnh đã chốt c2/c5. **Trạng thái phần 3: DỰ KIẾN 🔸**
> (Thì 1 phần neo central_subject đã chạy; phần chấm theo chuỗi lúc chọn CHƯA có).

---

## 1. Là gì

Hiệu ứng Kuleshov: **cùng một khuôn hình, ghép cạnh cảnh khác nhau thì mang nghĩa khác
nhau.** Một gương mặt trung tính đặt sau bát súp = "đói"; sau quan tài = "buồn"; sau đứa
trẻ = "trìu mến" — bản thân khuôn hình không đổi, HÀNG XÓM tạo nghĩa. Hệ quả cho việc chọn
footage: **không bao giờ chấm một câu thoại trong chân không.**

Ba dạng ngữ cảnh chuỗi mà việc chọn hình phải để ý:

| Dạng | Ý nghĩa | Ví dụ (niche space) |
|---|---|---|
| **Neo chủ đề (coherence)** | Cả chương phải xoay quanh `central_subject` thật, kể cả câu MƯỢN ẩn dụ ngôn ngữ | Chương nói về Mặt Trời, câu mở "hãy nghĩ về đống lửa trại" → hình phải là Mặt Trời/plasma NGAY, không phải lửa trại (bẫy bề-mặt-chữ của c2) |
| **Bồi nghĩa xuôi chuỗi (Kuleshov thật)** | Shot trung tính đặt cạnh shot mang cảm xúc thì "lây" nghĩa — dùng có chủ đích, hoặc coi chừng lây nhầm | Cảnh Trái Đất bình yên → cắt sang cảnh thiên thạch lao tới: Trái Đất "bình yên" thành "mong manh". Đúng ý thì tốt; nếu beat sau vô tình là cảnh nổ thì beat trước bị đổi nghĩa oan |
| **Mạch lặp / khựng (continuity)** | Hai beat liền nhau dùng hình quá giống nhau → khán giả tưởng lỗi tua lại; mạch nghĩa khựng | Beat 4 và beat 5 cùng ra một cảnh phi hành gia lơ lửng gần như trùng → như bị lag |

Luật nền của c3 (đứng trên bất đối xứng c2): **liền mạch với chủ đề > khớp từng chữ.**
Một hình "nhạt nhưng nối mạch" luôn hơn hình "khớp chữ nhưng gãy mạch".

## 2. Yếu tố ảnh hưởng

| Yếu tố | Ảnh hưởng thế nào |
|---|---|
| **`central_subject` của chương** | Cột neo của cả chuỗi. Mọi beat (kể cả ẩn dụ/setup) phải nối về đây → giữ mạch nghĩa xuyên chương. Đã chạy ở direct (pass 1 chốt central_subject, pass 2 neo từng beat). |
| **Beat đứng TRƯỚC (đã chọn xong)** | Ngữ cảnh RẺ và ĐÁNG TIN nhất lúc chọn: beat N−1 đã có footage → chấm beat N có thể nhìn lùi (giống quá → phạt variety; nối nghĩa tốt → cộng). |
| **Beat đứng SAU (chưa chọn)** | Ngữ cảnh ĐẮT: lúc chấm beat N thì N+1 chưa chọn xong (phễu chạy tuần tự từng beat — c5 đã đóng băng). Nên context xuôi chủ yếu phải lo ở DIRECT (nơi thấy cả script), không phải lúc chọn. |
| **`visual_anchor`** | Beat neo chở nghĩa → mạch phải chuẩn, đáng trả giá để nối; beat chêm → chỉ cần đúng mood, không cần gánh mạch. |
| **Ranh giới chương** | Đổi chương = được phép (và nên) đổi mood/cảnh mạnh — "khựng" ở đây là CHỦ ĐÍCH (nhịp thở), không phải lỗi mạch. Đừng phạt variety xuyên ranh giới chương như trong lòng chương. |
| **Loại mạch của niche** | Commentary thời sự: mạch theo dòng sự kiện (ai-làm-gì); chiêm nghiệm/space: mạch theo cảm xúc/quy mô (nhỏ→lớn). Kiểu mạch là chữ ký niche → DNA. |

## 3. Cách làm THỰC TẾ ở project này — 🔸 DỰ KIẾN

### Luồng chạy (2 thì — cùng khuôn c2)

**Thì 1 — direct, ngữ cảnh XUÔI lo ở đây (ĐÃ CHẠY phần lớn):** đây là nơi DUY NHẤT thấy
trọn script nên gánh phần lớn việc chuỗi:
- `_DIRECTOR_ROLE` đã dặn LLM "nghĩa đến từ chuỗi (Kuleshov) — luôn xét cái trước và sau,
  không đọc một câu cô lập."
- Pass 1 chốt `central_subject` mỗi chương; pass 2 neo mọi beat (kể cả ẩn dụ/setup) vào đó
  (`_CONTEXT_COHERENCE`) → mạch coherence được dựng ngay từ direct.
- Motif lặp có chủ đích (1–3 motif/video) cũng chốt ở pass 1 → mạch hình xuyên video.

**Thì 2 — lúc chọn, ngữ cảnh LÙI là phần rẻ (CHƯA CÓ — nằm trong đầu chấm nghĩa backlog #2):**
hiện phễu chọn từng beat ĐỘC LẬP; ngữ cảnh chuỗi lúc chọn mới có đúng MỘT mảnh chạy thật:
**P7 dedup** (`used_in_video`) — cấm cứng tái dùng đúng một clip, phạt mềm clip gần giống.
Khi đầu chấm nghĩa ra đời, nó nên nhìn **cửa sổ LÙI 1 beat** (beat N−1 đã chốt) để:
- **cộng điểm khớp nghĩa** khi ứng viên nối mạch với hình vừa chọn (cùng chủ thể/địa danh/mood);
- **phạt variety** khi ứng viên gần trùng hình vừa chọn (mở rộng P7 từ "trùng file" sang
  "trùng cảnh") — đây là điểm trừ, KHÔNG phải veto.
- Ngữ cảnh XUÔI (beat N+1) **không** cố nhét vào phễu tuần tự — để direct lo. Nếu sau này
  cần, đó là nâng cấp riêng có mô tả vận hành + user duyệt, không làm lẻ.

**Vì sao không phá thế tuần tự của phễu:** c5 đóng băng "phễu chạy tuần tự từng beat". Cho
phễu chờ cả chuỗi chọn xong rồi mới tối ưu toàn cục = bài toán khác hẳn (đắt, khó resume).
c3 chọn giải pháp RẺ: xuôi-lo-ở-direct + lùi-1-beat-lúc-chọn. Đủ bắt phần lớn lỗi mạch.

### 3b. PHÂN RÃ NĂNG LỰC

> Loại: **(a)** đã có sẵn · **(b)** cần code mới ỐNG · **(c)** NÃO quyết lúc chạy · **(d)** cần dữ liệu DNA (Phase B)

| Luật ngôn-ngữ-editor | Hệ thống chạy thế nào | Loại | Trạng thái |
|---|---|---|---|
| "Nghĩa đến từ chuỗi, xét trước-và-sau" | `_DIRECTOR_ROLE` trong prompt direct | (a)+(c) | ✅ đã có |
| Neo mọi beat vào central_subject (mạch coherence) | pass 1 chốt central_subject → pass 2 `_CONTEXT_COHERENCE` neo từng beat | (a) | ✅ đã có |
| Motif lặp có chủ đích xuyên video | pass 1 chọn 1–3 motif | (a) | ✅ đã có |
| Cấm tái dùng clip + phạt clip gần giống (mạch không khựng vì trùng) | P7 `used_in_video` cứng + `usage.soft_penalty_sort` mềm (`sourcer/`) | (a) | ✅ đã có (mức "trùng file") |
| **Đầu chấm nghĩa nhìn cửa sổ LÙI 1 beat (cộng nối-mạch / phạt gần-trùng-cảnh)** | phần của đầu chấm nghĩa trong `ranker/`: truyền footage beat N−1 đã chốt vào lúc chấm beat N | **(b)+(c)** | ❌ **= mở rộng backlog #2 của c5 (đầu chấm nghĩa), KHÔNG mục mới** — c3 cấp tiêu chí "lùi 1 beat" |
| Không phạt variety xuyên ranh giới chương | đầu chấm nghĩa đọc `chapter_id`/`visual_anchor` của beat để tắt phạt khi đổi chương | (b)+(c) | ❌ cùng gói đầu chấm nghĩa — chi tiết nhỏ, không mục riêng |
| Kiểu mạch theo niche (dòng sự kiện vs cảm xúc/quy mô) | học từ video viral niche → gợi ý direct sắp mạch | (d) | ❌ Phase B |

**→ Backlog code rút ra: KHÔNG mở mục mới.** Toàn bộ phần (b) của c3 là **thuộc tính của
đầu chấm nghĩa** (backlog #2 c5): khi xây đầu đó, cho nó thêm đầu vào "footage beat N−1" +
cờ ranh-giới-chương. c3 chốt tiêu chí; c2 chốt phần chấm-từng-beat; hai file cùng nuôi MỘT
đầu chấm nghĩa.

## 4. Cạm bẫy / ranh giới

- **Chấm câu trong chân không.** Lỗi gốc c3 chống: chọn hình đúng-nghĩa-đen từng câu nhưng
  ghép lại thành chuỗi rời rạc/đổi nghĩa oan. Luôn hỏi: hình này đứng CẠNH hình trước có
  đọc đúng ý không?
- **Biến ngữ cảnh chuỗi thành veto thứ 3.** CẤM (luật meta c5). "Gãy mạch" là điểm trừ nặng
  ở khớp nghĩa/variety, không phải cửa loại. Chỉ 2 veto: sai nghĩa nghiêm trọng (c2) +
  hỏng kỹ thuật/watermark.
- **Bắt phễu tối ưu toàn chuỗi.** Chờ chọn xong cả video rồi mới xếp lại = phá thế tuần tự
  + khó resume ([[assemble-segment-overlap-rounding]] nhắc resume là ràng buộc thật). Giữ
  rẻ: xuôi-ở-direct, lùi-1-beat-lúc-chọn.
- **Lấn sân c7.** Lặp CỠ CẢNH (3 medium liền) là việc [[c7-shot-variety]]; c3 chỉ lo lặp/lệch
  NGHĨA (cùng chủ thể, cùng cảnh, đổi nghĩa). Đừng chấm cỡ cảnh trong đầu nghĩa.
- **Phạt "khựng" ở ranh giới chương.** Đổi chương ĐƯỢC phép đổi cảnh mạnh (nhịp thở
  [[d1-pacing]]/[[d2-hinh-tho]]). Phạt gần-giống chỉ áp TRONG lòng chương.
- **Gánh ngữ cảnh XUÔI vào phễu tuần tự.** Beat N+1 chưa chọn lúc chấm beat N — đừng cố đoán.
  Xuôi là việc của direct (thấy cả script). Nhét vào phễu = vừa đắt vừa sai.

## 5. Học gì từ DNA niche (Phase B)

| Tín hiệu | Dùng để |
|---|---|
| Kiểu mạch chủ đạo của niche (dòng sự kiện / cảm xúc / quy mô nhỏ→lớn) | gợi ý direct cách sắp chuỗi + trọng số nối-mạch theo niche |
| Motif hình lặp mà video viral niche hay dùng | mồi cho danh sách motif pass 1 (thay vì bịa mỗi lần) |
| Khoảng cách "an toàn" trước khi tái xuất một cảnh/chủ thể | tinh ngưỡng phạt gần-trùng-cảnh (P7 mềm) theo niche thay vì số cứng |
| Chỗ chuyển chương video viral hay đổi cảnh mạnh cỡ nào | canh biên độ "khựng có chủ đích" ở ranh giới chương |
