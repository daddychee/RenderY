# C7 — SHOT VARIETY (đa dạng cỡ cảnh & góc máy)

> **Vị trí:** luật giữ mắt khán giả tươi bằng xen kẽ cỡ cảnh + đổi góc. ĐÓNG GÓP vào phễu
> [[c5-loc-xep-hang]] một CHIỀU ĐIỂM (×1.5) — không veto, không tự quyền loại footage.
> Đặc thù: là luật **XÉT THEO CHUỖI** duy nhất hiện nay (cần biết shot #n−1) → là lý do
> phễu chạy tuần tự theo beat (đã ghi ở c5 cạm bẫy "variety phá song song").
> Sự đa dạng tự nó tạo nhịp → liên đới [[d1-pacing]].
> **Trạng thái phần 3: DỰ KIẾN 🔸.**

---

## 1. Là gì

Xen kẽ **toàn cảnh – trung – cận – đặc tả** và đổi góc máy để mắt không chán (nguyên văn
user, `GHI_CHEP_GOC.md §6`):

> Nguyên tắc "đổi cỡ cảnh hoặc đổi góc ≥30°" giữa hai shot liền kề → tránh jump cut và giữ
> tươi mắt. Cứ vài shot trung thì chèn một đặc tả (bàn tay, ánh mắt, chi tiết) để tạo texture.

**Trọng tâm đã chốt (user, 2026-07-02):** *"cỡ cảnh quan trọng hơn"* — **cỡ cảnh là tín hiệu
CHÍNH** của variety; **góc máy là tín hiệu phụ CHỈ-CỘNG**, hạ trọng số hoặc bỏ hẳn nếu tag
góc khó làm tin cậy (tránh loại oan footage hay vì dữ liệu góc thiếu/sai).

Mỗi cỡ cảnh có VAI riêng (ngữ pháp đã nằm trong prompt direct):
- **wide / aerial** — mở bối cảnh, quy mô, "người nhỏ giữa thế giới lớn" → MỞ chương;
- **medium** — kể chuyện mặc định;
- **close_up** — cảm xúc, thân mật, căng thẳng → NHẤN khoảnh khắc đắt;
- **extreme_close_up** — chi tiết biểu tượng (mắt, bàn tay, đồng xu) — hiếm, impact cao.

Ví dụ user (nấu ăn): toàn cảnh bếp → trung thái rau → đặc tả dao chạm thớt + foley "cạch"
→ cận mặt nếm thử. **4 cỡ cảnh trong 8 giây → sống động.**

## 2. Yếu tố ảnh hưởng

| Yếu tố | Ảnh hưởng thế nào |
|---|---|
| **Shot liền trước (#n−1) — THỰC TẾ đã chọn** | Cái mắt khán giả thấy là chuỗi footage ĐÃ CHỌN, không phải chuỗi ý định của director → điểm variety phải so với shot thật vừa chốt, kể cả vắt qua ranh giới chương. |
| **Vai trò beat trong chương** | Mở chương thiên wide/aerial; điểm nhấn thiên close_up; đặc tả là "gia vị" chêm theo nhịp. |
| **Nguồn footage** | Local library ĐÃ có tag cỡ cảnh; stock (Pexels) KHÔNG có tag — phải suy từ mô tả/ảnh preview; footage DNA sẽ có tag từ Phase B. |
| **Nhịp đặc tả của niche** | "Vài shot trung chèn 1 đặc tả" — *vài* là bao nhiêu tùy niche (cooking dày đặc tả, chill travel thưa) → DNA. |
| **Pacing đoạn** | Đoạn cắt nhanh cần variety cao hơn (nhiều shot sát nhau, trùng cỡ là lộ ngay); đoạn hold dài (hình thở) một shot đứng lâu, luật chuỗi nhẹ đi. |

## 3. Cách làm THỰC TẾ ở project này — 🔸 DỰ KIẾN

### Luồng chạy (2 thì — cùng khuôn với [[c2-an-du-veto]]: Ý ĐỊNH lúc direct → KIỂM lúc chọn)

**Thì 1 — direct đặt ý định (ĐÃ CHẠY hôm nay):** mỗi beat được quyết `shot_size` theo ngữ
pháp trên; prompt cấm 3 beat liên tiếp cùng cỡ; chuỗi được truyền qua ranh giới chương
(chương sau biết shot cuối chương trước); validator cảnh báo nếu LLM vẫn vi phạm.

**Thì 2 — chấm variety lúc chọn footage (CHƯA CÓ — là "đầu chấm variety" đã ghi ở 3b của c5):**
1. Phễu chạy đến beat #n thì shot #n−1 ĐÃ chốt → biết cỡ cảnh/góc thật của nó.
2. Mỗi ứng viên của beat #n cần ước lượng cỡ cảnh: local → đọc tag DB; stock → NÃO suy từ
   mô tả/title (rẻ) hoặc frame preview (đắt — theo kỷ luật rẻ-trước-đắt-sau của c5);
   DNA → tag sẵn từ Phase B.
3. **Chấm bằng CỠ CẢNH (tín hiệu chính):** ứng viên đổi cỡ cảnh so shot #n−1 → điểm variety
   cao; trùng cỡ → điểm thấp. Trùng cỡ NHƯNG khớp `shot_size` ý định của director → không
   phạt kép (ý định thắng, vì director đã tính vai beat).
4. **Góc máy = tín hiệu phụ CHỈ-CỘNG (user chốt 2026-07-02):** khi ứng viên CÓ tag góc đáng
   tin và đổi góc ≥30° so shot #n−1 → cộng nhẹ. **Thiếu tag góc hoặc trùng góc → KHÔNG trừ
   điểm** — góc máy không bao giờ là lý do loại/trừ, chỉ là bonus. Nếu Phase B cho thấy tag
   góc không tin cậy → BỎ HẲN tín hiệu này, variety chạy bằng cỡ cảnh.
5. **Không bao giờ veto** — footage đúng nghĩa đúng mood mà trùng cỡ cảnh vẫn phải sống
   (nghĩa > mood > nhịp/variety, thứ tự đã đóng băng ở c5).

### 3b. PHÂN RÃ NĂNG LỰC

> Loại: **(a)** đã có sẵn · **(b)** cần code mới ỐNG · **(c)** NÃO quyết lúc chạy · **(d)** cần dữ liệu DNA (Phase B)

| Luật ngôn-ngữ-editor | Hệ thống chạy thế nào | Loại | Trạng thái |
|---|---|---|---|
| Ý định cỡ cảnh per beat + ngữ pháp vai (wide mở, CU nhấn, ECU hiếm) | `Beat.shot_size` (schema 5 giá trị) + prompt direct pass 2 | (a)+(c) | ✅ đã có |
| Cấm 3 beat liên tiếp cùng cỡ (mức Ý ĐỊNH) | prompt + `validator.check_consecutive_shot_size` (warning) | (a) | ✅ đã có |
| Chuỗi vắt qua chương | `director/runner.py` truyền concept+shot_size beat cuối chương trước vào prompt chương sau | (a) | ✅ đã có |
| Tag cỡ cảnh footage local | `library/vision.py` (Claude vision) → cột `shot_size` trong DB | (a) | ✅ đã có — NHƯNG `sourcer/local.py` ĐÁNH RƠI tag khi gom ứng viên (chỉ giữ path+mô tả) |
| **Đầu chấm variety trong phễu (so shot #n−1 THẬT)** | cắm vào `ranker/` — local đọc lại tag DB (nối tag đã rơi = code nhỏ, tiền đề); stock NÃO suy từ mô tả | **(b)+(c)** | ❌ = dòng "chấm variety theo chuỗi" đã ghi ở 3b của c5, KHÔNG phải mục mới — file này cấp tiêu chí chấm |
| Góc máy ≥30° — CHỈ-CỘNG (user hạ cấp 2026-07-02) | CHƯA AI TAG GÓC (vision.py chỉ tag cỡ cảnh). Schema tag GLM Phase B: cỡ cảnh BẮT BUỘC, góc máy TÙY CHỌN thử nghiệm — đánh giá độ tin cậy tag góc trước, tin mới dùng (bonus-only), không tin → BỎ HẲN | (d) | ❌ Phase B; variety chạy đủ bằng cỡ cảnh, không chờ góc |
| Nhịp đặc tả ("vài shot trung chèn 1 đặc tả" — vài = ?) | tần suất ECU/đặc tả theo niche từ DNA → tinh prompt direct | (d) | ❌ Phase B |

**→ Backlog code rút ra:** không mở mục lớn mới — đầu chấm variety thuộc khung phễu c5;
mục nhỏ tiền đề: **nối tag `shot_size` từ DB vào dict ứng viên local** (sửa `sourcer/local.py`,
vài dòng — làm cùng lúc với khung phễu).

## 4. Cạm bẫy / ranh giới

- **Chấm theo ý định thay vì thực tế.** Director đặt wide nhưng sourcer trả về close_up —
  nếu chỉ validate chuỗi Ý ĐỊNH thì mắt khán giả vẫn thấy 3 close_up liền. Chuỗi THẬT
  (footage đã chọn) mới là thước đo.
- **Variety phá song song** (nhắc lại từ c5): luật cần shot #n−1 → phễu buộc tuần tự theo
  beat. Đừng vì tối ưu tốc độ mà chạy song song rồi làm luật chuỗi mù.
- **Nâng variety thành veto.** Video niche cảnh quan có lúc 2–3 shot aerial liền vẫn đẹp —
  trùng cỡ chỉ trừ điểm, không giết (luật meta c5: không veto thứ 3).
- **Trừ điểm theo góc máy = loại oan footage hay.** Tag góc thiếu/sai phổ biến (stock không
  có, vision đoán góc kém tin hơn đoán cỡ) — vì vậy góc CHỈ được cộng, không bao giờ trừ
  (user chốt: "sợ bị loại đi nhiều footage hay, cỡ cảnh quan trọng hơn").
- **Đoán cỡ cảnh stock bằng vision đại trà** = nổ chi phí — chỉ suy từ mô tả/title ở lớp rẻ;
  vision chỉ cho nhóm dẫn đầu, đúng kỷ luật c5.
- **Quên vai đặc tả.** ECU là gia vị tạo cảm xúc — thiếu nó video phẳng; nhưng ECU dày quá
  mất "hiếm, impact cao". Tần suất là số DNA, đừng fix cứng.

## 5. Học gì từ DNA niche (Phase B)

| Tín hiệu | Dùng để |
|---|---|
| Phân bố cỡ cảnh thật của video viral niche (bao nhiêu % wide/medium/CU/ECU) | tinh ngữ pháp cỡ cảnh trong prompt direct theo niche |
| Nhịp đặc tả (mấy shot trung thì 1 đặc tả) | tần suất ECU theo niche |
| Chuỗi cỡ cảnh điển hình (vd cooking: wide→medium→ECU→CU) | mẫu chuỗi mồi cho director |
| **Tag CỠ CẢNH của từng footage DNA** | đầu vào bắt buộc của đầu chấm variety — schema tag GLM PHẢI có trường này |
| Tag góc máy (TÙY CHỌN thử nghiệm) | tag thử 1 mẻ nhỏ → đo độ tin cậy: tin → bonus-only trong phễu; không tin → bỏ trường, không tag đại trà (đỡ token) |
